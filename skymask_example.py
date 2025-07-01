import gnss_lib_py as glp
from gnss_lib_py.utils.coordinates import add_el_az
from gnss_lib_py import loop_time
import numpy as np
import skymask_py
from pyproj import Transformer
from pyproj.crs.crs import CRS
import geopandas as gpd
from utils import get_full_states, get_fde_estimate, name_mapper
import cachier


def WGS84_to_pos(pos: tuple[float, float], target_crs: CRS) -> tuple[float, float]:
    transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
    return transformer.transform(*pos[::-1])


def permute_az(az_sv_deg: np.ndarray) -> np.ndarray:
    theta_prime = (90 - az_sv_deg) % 360
    phi = theta_prime * np.pi / 180.0
    return (phi + np.pi) % (2 * np.pi) - np.pi


@cachier.cachier()
def get_skymask_states(
    gnss_log_file_path: str,
    shp_path: str = ".local/Beijing/Beijing_Buildings_DWG-Polygon.shp",
) -> glp.NavData:
    world = skymask_py.World(shp_path, max_dist=1000)
    original_crs = gpd.read_file(shp_path, encoding="utf-8").crs

    fix_data = glp.AndroidRawFixes(gnss_log_file_path)
    full_states = get_full_states(gnss_log_file_path)
    wls_estimate = get_fde_estimate(gnss_log_file_path)
    full_states = add_el_az(full_states, wls_estimate, inplace=True)

    fault_skymask: list[bool] = []
    for timestamp, _, navdata_subset in loop_time(full_states, "gps_millis"):
        rx_t_idx = np.argmin(np.abs(fix_data["gps_millis"] - timestamp))
        pos = fix_data[["lat_rx_deg", "lon_rx_deg"], rx_t_idx]

        skymask = world.skymask(WGS84_to_pos(pos.tolist(), target_crs=original_crs))
        fault_skymask.extend(
            (
                skymask.samples(permute_az(navdata_subset["az_sv_deg"]))
                >= (navdata_subset["el_sv_deg"] * np.pi / 180.0)
            ).tolist()
        )

    full_states["fault_skymask"] = fault_skymask
    skymask_states: glp.NavData = full_states.where("fault_skymask", False)
    return skymask_states


@cachier.cachier()
def get_skymask_estimate(
    gnss_log_file_path: str,
    shp_path: str = ".local/Beijing/Beijing_Buildings_DWG-Polygon.shp",
) -> glp.NavData:
    skymask_states = get_skymask_states(gnss_log_file_path, shp_path)
    return glp.solve_wls(skymask_states).rename(name_mapper("skymask"))
