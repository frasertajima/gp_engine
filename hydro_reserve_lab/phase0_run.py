"""Phase 0 — does this real 5-gauge Colorado River Basin dataset actually show:
(1) genuine spatial correlation across gauges (the pooling lever),
(2) a real, recurring rare/imbalanced drought regime (litmus-test conditions 1 & 2), and
(3) the specific nonstationarity complication research/02_drought_regime_rarity.md flagged
    (is the real 2000-2025 megadrought period's drought rate higher than the pre-2000 baseline)?
Same "does the mechanism actually exist in this specific real data" discipline as every prior
lab's Phase 0 — nothing here is assumed from the research pass's generic literature figures.
"""

import json

import numpy as np

from data_usgs import SITES, load_water_year_means

EXTREME_DROUGHT_PCTL = 5.5  # research/02's cited historical extreme-drought likelihood
MODERATE_DROUGHT_PCTL = 25.0
MEGADROUGHT_START = 2000


def main():
    df = load_water_year_means()
    sites = list(SITES.keys())

    # --- Check 1: spatial correlation across gauges (log flow, standard for streamflow) ---
    log_flow = np.log(df[sites])
    corr = log_flow.corr()
    off_diag = corr.values[np.triu_indices(len(sites), k=1)]

    # --- Basin-wide pooled index: mean of per-site z-scores (standardized on the FULL record) ---
    z = (log_flow - log_flow.mean()) / log_flow.std()
    basin_index = z.mean(axis=1)

    # --- Check 2: real drought-year rate at two thresholds ---
    extreme_thresh = np.percentile(basin_index, EXTREME_DROUGHT_PCTL)
    moderate_thresh = np.percentile(basin_index, MODERATE_DROUGHT_PCTL)
    extreme_years = basin_index[basin_index <= extreme_thresh].index.tolist()
    moderate_years = basin_index[basin_index <= moderate_thresh].index.tolist()

    # --- Check 3: nonstationarity -- pre-2000 vs. the real 2000-2025 megadrought period ---
    pre = basin_index[basin_index.index < MEGADROUGHT_START]
    post = basin_index[basin_index.index >= MEGADROUGHT_START]
    pre_extreme_rate = float((pre <= extreme_thresh).mean())
    post_extreme_rate = float((post <= extreme_thresh).mean())
    pre_moderate_rate = float((pre <= moderate_thresh).mean())
    post_moderate_rate = float((post <= moderate_thresh).mean())

    # --- Check 4: does 2021/2022 (real Tier 1/2 shortage years) show up as genuinely low? ---
    # Water year 2021 = Oct 2020-Sep 2021 (the year Tier 1 was declared, Aug 2021);
    # water year 2022 = Oct 2021-Sep 2022 (the year Tier 2 was declared, Aug 2022).
    rank_2021 = float((basin_index <= basin_index.loc[2021]).mean()) if 2021 in basin_index.index else None
    rank_2022 = float((basin_index <= basin_index.loc[2022]).mean()) if 2022 in basin_index.index else None

    results = {
        "n_water_years": int(len(df)),
        "year_range": [int(df.index.min()), int(df.index.max())],
        "pairwise_log_flow_correlation": {
            "mean": float(off_diag.mean()),
            "min": float(off_diag.min()),
            "max": float(off_diag.max()),
        },
        "extreme_drought_threshold_percentile": EXTREME_DROUGHT_PCTL,
        "extreme_drought_years": extreme_years,
        "extreme_drought_empirical_rate_full_record": float(len(extreme_years) / len(df)),
        "moderate_drought_threshold_percentile": MODERATE_DROUGHT_PCTL,
        "moderate_drought_years_count": len(moderate_years),
        "nonstationarity_check": {
            "pre_2000_extreme_rate": pre_extreme_rate,
            "post_2000_extreme_rate": post_extreme_rate,
            "pre_2000_moderate_rate": pre_moderate_rate,
            "post_2000_moderate_rate": post_moderate_rate,
            "n_pre_2000_years": int(len(pre)),
            "n_post_2000_years": int(len(post)),
        },
        "real_shortage_years_percentile_rank": {
            "water_year_2021_tier1": rank_2021,
            "water_year_2022_tier2": rank_2022,
        },
        "basin_index_by_year": {int(y): float(v) for y, v in basin_index.items()},
        "site_order": sites,
        "pairwise_log_flow_correlation_matrix": corr.values.tolist(),
        "lees_ferry_cfs_by_year": {int(y): float(v) for y, v in df["09380000"].items()},
    }

    with open("results_phase0.json", "w") as fh:
        json.dump(results, fh, indent=2)

    print(f"{results['n_water_years']} water years ({results['year_range'][0]}-{results['year_range'][1]})")
    print(f"Pairwise log-flow correlation: mean={off_diag.mean():.3f}, "
          f"range=[{off_diag.min():.3f}, {off_diag.max():.3f}]")
    print(f"Extreme-drought empirical rate (full record, <= P{EXTREME_DROUGHT_PCTL}): "
          f"{results['extreme_drought_empirical_rate_full_record']*100:.1f}% "
          f"({len(extreme_years)}/{len(df)} years) -- vs. research's cited 5.5%")
    print(f"Extreme-drought rate: pre-2000 = {pre_extreme_rate*100:.1f}%, "
          f"2000-2025 (megadrought) = {post_extreme_rate*100:.1f}%")
    print(f"Moderate-drought rate: pre-2000 = {pre_moderate_rate*100:.1f}%, "
          f"2000-2025 (megadrought) = {post_moderate_rate*100:.1f}%")
    print(f"WY2021 (real Tier 1 shortage year) percentile rank: {rank_2021}")
    print(f"WY2022 (real Tier 2 shortage year) percentile rank: {rank_2022}")


if __name__ == "__main__":
    main()
