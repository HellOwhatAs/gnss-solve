import gnss_lib_py as glp
from gnss_lib_py import loop_time
from tqdm import tqdm
import numpy as np
from gnss_lib_py.utils.coordinates import geodetic_to_ecef
from utils import get_fde_states, name_mapper
import cachier
import dowhen


def __patch_only_bias_position(
    position: np.ndarray,
    receiver_state: glp.NavData,
    timestamp: np.ndarray,
    rx_idxs: dict[str, list[str]],
):
    position = np.vstack(
        (
            receiver_state[
                [rx_idxs["x_rx*_m"][0], rx_idxs["y_rx*_m"][0], rx_idxs["z_rx*_m"][0]],
                np.argmin(np.abs(receiver_state["gps_millis"] - timestamp)),
            ].reshape(-1, 1),
            position[3],
        )
    )
    return {"position": position}


def solve_bias(measurements: glp.NavData, receiver_state: glp.NavData):
    with (
        dowhen.do(__patch_only_bias_position)
        .when(glp.solve_wls, "position = np.vstack((")
        .goto("position = wls(position, pos_sv_m, corr_pr_m, weights,")
    ):
        return glp.solve_wls(
            measurements, only_bias=True, receiver_state=receiver_state
        )


@cachier.cachier()
def get_weighted_states(
    gnss_log_file_path: str, weight_type: str = "true_pr_residual_weights"
):
    fix_data = glp.AndroidRawFixes(gnss_log_file_path)
    fde_states = get_fde_states(gnss_log_file_path)

    xyz_fix = geodetic_to_ecef(fix_data["lat_rx_deg", "lon_rx_deg", "alt_rx_m"])
    fix_data["x_rx_fix_m"] = xyz_fix[0]
    fix_data["y_rx_fix_m"] = xyz_fix[1]
    fix_data["z_rx_fix_m"] = xyz_fix[2]
    bias_fix_estimate = solve_bias(fde_states, fix_data).rename(name_mapper("rx_fix"))

    true_pr_residual_weights: list[float] = []
    for timestamp, _, navdata_subset in tqdm(
        loop_time(fde_states, "gps_millis"),
        total=np.unique(fde_states["gps_millis"]).shape[0],
    ):
        rx_t_idx = np.argmin(np.abs(fix_data["gps_millis"] - timestamp))
        xyz_fix = geodetic_to_ecef(
            fix_data[["lat_rx_deg", "lon_rx_deg", "alt_rx_m"], rx_t_idx][:, np.newaxis]
        )
        xyz_sv: np.ndarray = navdata_subset[["x_sv_m", "y_sv_m", "z_sv_m"]]
        true_r_m: np.ndarray = np.sqrt(np.sum(np.square(xyz_sv - xyz_fix), axis=0))

        bias = bias_fix_estimate.where("gps_millis", timestamp)
        true_pr_residual_m: np.ndarray = np.abs(
            navdata_subset["corr_pr_m"] - true_r_m - bias["b_rx_fix_m"]
        )
        true_pr_residual_weights.extend(true_pr_residual_m.tolist())
    fde_states[weight_type] = true_pr_residual_weights
    return fde_states


@cachier.cachier()
def get_weighted_estimate(
    gnss_log_file_path: str,
    weight_type: str = "true_pr_residual_weights",
) -> glp.NavData:
    weighted_states = get_weighted_states(gnss_log_file_path, weight_type)
    return glp.solve_wls(weighted_states, weight_type=weight_type).rename(
        name_mapper("weighted")
    )
