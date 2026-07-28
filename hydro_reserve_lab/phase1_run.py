"""Phase 1 — the four-rung ladder, fit on pre-2000 (71 years), scored against the REAL held-out
2000-2025 megadrought (26 years) Lees Ferry sequence Lees Ferry never saw during fitting.

Gauge column order (fixed throughout this lab): Lees Ferry (target), Green River, Cisco, Gunnison,
San Juan (the four correlated predictor/pooling gauges).

Reservoir: a single lumped system (see reservoir_sim.py's own docstring for why), capacity fixed
at 2x the pre-2000 mean annual Lees Ferry inflow (an illustrative "multi-year carryover"
assumption, not a claim about any specific real reservoir's actual capacity), target reliability
0.98 (Seattle's real, sourced standard, research/05_reliability_standard_firm_yield.md).

Dollar figures (research/04_colorado_river_economics.md, real, sourced, not invented):
- shortfall cost: $2,400/acre-foot (the real "local supply project" replacement-cost figure — the
  real cost of an emergency alternative supply when a shortfall occurs)
- foregone-yield opportunity cost: $417/acre-foot (the real average agricultural-conservation-
  program cost — the real price of the demand headroom a method chose not to use)
These are modeling CHOICES about which real sourced figure maps to which side of the decision,
stated explicitly, not a claim these are the only correct mappings.
"""

import json

import numpy as np
from scipy import stats

from data_usgs import SITES, load_water_year_means
from method0_resampling import HistoricalResampling
from method1_vanilla_mvn import VanillaMVN
from method2_regime_mixture import RegimeMixtureTimeVarying
from method3_trend_control import TrendControl
from reservoir_sim import cfs_mean_to_annual_af, find_firm_yield, simulate

TARGET_RELIABILITY = 0.98
MEGADROUGHT_START = 2000
SHORTFALL_COST_PER_AF = 2400.0
FOREGONE_YIELD_COST_PER_AF = 417.0

GAUGE_ORDER = ["09380000", "09315000", "09180500", "09152500", "09379500"]  # Lees Ferry first


def main():
    df = load_water_year_means()
    log_flow = np.log(df[GAUGE_ORDER].values)
    years = df.index.values

    train_mask = years < MEGADROUGHT_START
    test_mask = ~train_mask
    log_flow_train, years_train = log_flow[train_mask], years[train_mask]
    test_years = years[test_mask]

    lees_ferry_cfs_train = df[GAUGE_ORDER[0]].values[train_mask]
    lees_ferry_cfs_real_test = df[GAUGE_ORDER[0]].values[test_mask]
    real_test_af = cfs_mean_to_annual_af(lees_ferry_cfs_real_test)

    capacity_af = 2.0 * cfs_mean_to_annual_af(lees_ferry_cfs_train.mean())

    # Honest significance check on Method 3's own trend, saved for reproducibility (not just
    # reported ad hoc in RESULTS_PHASE1.md) -- is the trend that scored best actually
    # statistically distinguishable from no trend at all, on the pre-2000 data it was fit to?
    slope, intercept, r, p, se = stats.linregress(years_train, log_flow_train[:, 0])
    trend_significance = {
        "slope_per_year": float(slope), "r_squared": float(r**2), "p_value": float(p),
    }

    # The hindsight-optimal hydro yield, computed directly from the real test-period sequence --
    # what the demand SHOULD have been, known only after the fact.
    true_optimal_demand = find_firm_yield(real_test_af.reshape(1, -1), capacity_af, TARGET_RELIABILITY)

    method2 = RegimeMixtureTimeVarying(horizon=len(test_years)).fit(log_flow_train, years_train)
    method3 = TrendControl(horizon=len(test_years)).fit(log_flow_train, years_train)

    methods = {
        "method0_historical_resampling": HistoricalResampling(horizon=len(test_years)).fit(lees_ferry_cfs_train),
        "method1_vanilla_mvn": VanillaMVN(horizon=len(test_years)).fit(log_flow_train),
        "method2_regime_mixture_time_varying": method2,
        "method3_trend_control": method3,
    }

    # Per-test-year diagnostic series -- what each nonstationarity-aware method actually forecast
    # for the real 2000-2025 years, vs. what really happened (the notebook's key chart).
    pi_drought_by_test_year = method2.pi_drought(test_years)
    method3_implied_mean_cfs = np.array([
        np.exp((method3.mu0 + method3.trend * (yr - method3.year_ref))[0]) for yr in test_years
    ])
    train_mean_cfs = float(lees_ferry_cfs_train.mean())

    results = {
        "n_train_years": int(train_mask.sum()),
        "n_test_years": int(test_mask.sum()),
        "test_year_range": [int(test_years.min()), int(test_years.max())],
        "capacity_af": float(capacity_af),
        "target_reliability": TARGET_RELIABILITY,
        "true_optimal_demand_af_hindsight": float(true_optimal_demand),
        "method3_trend_significance_on_pre2000_data": trend_significance,
        "test_years": [int(y) for y in test_years],
        "real_lees_ferry_cfs_test_years": [float(v) for v in lees_ferry_cfs_real_test],
        "method2_pi_drought_by_test_year": [float(v) for v in pi_drought_by_test_year],
        "method3_implied_mean_cfs_by_test_year": [float(v) for v in method3_implied_mean_cfs],
        "stationary_train_mean_cfs": train_mean_cfs,
        "methods": {},
    }

    for name, model in methods.items():
        traces = model.sample_traces(test_years)
        chosen_demand = find_firm_yield(traces, capacity_af, TARGET_RELIABILITY)

        # Score the method's CHOSEN demand against the REAL historical test-period sequence.
        real_reliability, real_shortfall_per_trace, _ = simulate(
            real_test_af.reshape(1, -1), capacity_af, chosen_demand
        )
        real_shortfall_af = float(real_shortfall_per_trace[0])

        demand_bias_af = float(chosen_demand - true_optimal_demand)
        if demand_bias_af > 0:
            # chose MORE demand than was truly sustainable -> real shortfall risk
            dollar_consequence = real_shortfall_af * SHORTFALL_COST_PER_AF
        else:
            # chose LESS demand than truly sustainable -> foregone-yield opportunity cost, per year
            dollar_consequence = abs(demand_bias_af) * len(test_years) * FOREGONE_YIELD_COST_PER_AF

        results["methods"][name] = {
            "chosen_demand_af": float(chosen_demand),
            "demand_bias_vs_true_optimal_af": demand_bias_af,
            "demand_bias_vs_true_optimal_pct": 100.0 * demand_bias_af / true_optimal_demand,
            "real_achieved_reliability_on_test_years": real_reliability,
            "real_total_shortfall_af": real_shortfall_af,
            "dollar_consequence_usd": float(dollar_consequence),
        }

    with open("results_phase1.json", "w") as fh:
        json.dump(results, fh, indent=2)

    print(f"Train: {results['n_train_years']} years, Test: {results['test_year_range']} "
          f"({results['n_test_years']} years)")
    print(f"Capacity: {capacity_af:,.0f} AF, target reliability {TARGET_RELIABILITY}")
    print(f"True hindsight-optimal demand: {true_optimal_demand:,.0f} AF/yr")
    for name, r in results["methods"].items():
        print(f"\n{name}:")
        print(f"  chosen demand: {r['chosen_demand_af']:,.0f} AF/yr "
              f"(bias {r['demand_bias_vs_true_optimal_pct']:+.1f}% vs. true optimal)")
        print(f"  real achieved reliability on test years: {r['real_achieved_reliability_on_test_years']:.4f}")
        print(f"  real total shortfall: {r['real_total_shortfall_af']:,.0f} AF")
        print(f"  dollar consequence: ${r['dollar_consequence_usd']:,.0f}")


if __name__ == "__main__":
    main()
