import gnss_lib_py as glp
import cachier
from gnss_lib_py.navdata.operations import find_wildcard_indexes
from pygc import great_distance
import numpy as np


def distance_category(x: float) -> str:
    return "A" if x < 10 else ("B" if x < 20 else ("C" if x < 50 else "D"))


def name_mapper(new: str, old: str = "rx_wls"):
    return {
        f"x_{old}_m": f"x_{new}_m",
        f"y_{old}_m": f"y_{new}_m",
        f"z_{old}_m": f"z_{new}_m",
        f"b_{old}_m": f"b_{new}_m",
        f"lat_{old}_deg": f"lat_{new}_deg",
        f"lon_{old}_deg": f"lon_{new}_deg",
        f"alt_{old}_m": f"alt_{new}_m",
    }


@cachier.cachier()
def get_full_states(gnss_log_file_path: str) -> glp.NavData:
    raw_data = glp.AndroidRawGnss(gnss_log_file_path, verbose=True)

    full_states = glp.add_sv_states_rinex(raw_data)
    full_states["corr_pr_m"] = full_states["raw_pr_m"] + full_states["b_sv_m"]

    return full_states


@cachier.cachier()
def get_wls_estimate(gnss_log_file_path: str) -> glp.NavData:
    return glp.solve_wls(get_full_states(gnss_log_file_path))


@cachier.cachier()
def get_fde_states(gnss_log_file_path: str) -> glp.NavData:
    full_states = get_full_states(gnss_log_file_path)
    return glp.solve_fde(full_states, remove_outliers=True)


@cachier.cachier()
def get_fde_estimate(gnss_log_file_path: str) -> glp.NavData:
    return glp.solve_wls(get_fde_states(gnss_log_file_path))


def estimate_distance(estimate1: glp.NavData, estimate2: glp.NavData):
    e1_idxs, e2_idxs = (
        find_wildcard_indexes(est, wildcards=["lat_*_deg", "lon_*_deg"])
        for est in (estimate1, estimate2)
    )
    distance: list[float] = []
    e2_lats_deg: list[float] = []
    e2_lons_deg: list[float] = []
    for timestamp, _, subset in glp.loop_time(estimate1, "gps_millis"):
        pos1 = subset[e1_idxs["lat_*_deg"][0], e1_idxs["lon_*_deg"][0]]
        pos2 = estimate2[
            [e2_idxs["lat_*_deg"][0], e2_idxs["lon_*_deg"][0]],
            np.argmin(np.abs(estimate2["gps_millis"] - timestamp)),
        ]

        e2_lats_deg.append(pos2[0])
        e2_lons_deg.append(pos2[1])
        distance.append(
            great_distance(
                start_latitude=pos1[0],
                start_longitude=pos1[1],
                end_latitude=pos2[0],
                end_longitude=pos2[1],
            )["distance"][0]
        )

    estimate1["distance_m"] = distance
    estimate1[e2_idxs["lat_*_deg"][0]] = e2_lats_deg
    estimate1[e2_idxs["lon_*_deg"][0]] = e2_lons_deg
    return estimate1
