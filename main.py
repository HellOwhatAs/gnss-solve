import gnss_lib_py as glp
from utils import get_fde_estimate
from skymask_example import get_skymask_estimate
from weighted_example import get_weighted_estimate


def main():
    gnss_log_file_paths = [f".local/gnss_log_{i}.csv" for i in range(1, 5)]
    for i, gnss_log_file_path in enumerate(gnss_log_file_paths, start=1):
        fix_data = glp.AndroidRawFixes(gnss_log_file_path)
        fde_estimate = get_fde_estimate(gnss_log_file_path)
        skymask_estimate = get_skymask_estimate(gnss_log_file_path)
        weighted_estimate = get_weighted_estimate(gnss_log_file_path)
        glp.plot_map(
            fde_estimate, skymask_estimate, weighted_estimate, fix_data
        ).write_html(f"skymask_estimate_map_{i}.html")


if __name__ == "__main__":
    main()
