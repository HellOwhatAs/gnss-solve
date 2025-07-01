import os
import gnss_lib_py as glp
from utils import get_fde_estimate, estimate_distance, distance_category
from skymask_example import get_skymask_estimate
from weighted_example import get_weighted_estimate


def main():
    if not os.path.exists("output"):
        os.makedirs("output")

    gnss_log_file_paths = [f".local/gnss_log_{i}.csv" for i in range(1, 5)]
    for i, gnss_log_file_path in enumerate(gnss_log_file_paths, start=1):
        fix_data = glp.AndroidRawFixes(gnss_log_file_path)
        fde_estimate = get_fde_estimate(gnss_log_file_path)
        skymask_estimate = get_skymask_estimate(gnss_log_file_path)
        weighted_estimate = get_weighted_estimate(gnss_log_file_path)

        glp.plot_map(
            fde_estimate, skymask_estimate, weighted_estimate, fix_data
        ).write_html(f"output/skymask_estimate_map_{i}.html")

        skymask_df = estimate_distance(skymask_estimate, fix_data).pandas_df()
        weighted_df = estimate_distance(weighted_estimate, fix_data).pandas_df()
        skymask_df["category"] = skymask_df["distance_m"].apply(distance_category)
        weighted_df["category"] = weighted_df["distance_m"].apply(distance_category)
        skymask_df.to_excel(f"output/skymask_estimate_{i}.xlsx")
        weighted_df.to_excel(f"output/weighted_estimate_{i}.xlsx")


if __name__ == "__main__":
    main()
