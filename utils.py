import gnss_lib_py as glp
import cachier


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
