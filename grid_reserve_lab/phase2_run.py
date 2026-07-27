"""Phase 2: real data, genuinely held-out scoring.

A real scoping pivot from LAB_PLAN.md's original sketch -- see
data_eia930.py's module docstring and RESULTS_PHASE2.md for the full
reasoning. Two changes from Phase 1, both real:

1. **Fleet and shortfall are real, not synthetic.** 15 real US Balancing
   Authorities (data_eia930.BA_CENTROIDS), real hourly EIA-930
   generation-by-fuel-type data aggregated to daily, real climatology,
   real one-sided shortfall (max(climatology - actual, 0), the same
   definition Phase 0 validated).

2. **Scoring is a genuine train/test split, not an oracle resample.**
   There is no synthetic ground-truth DGP for real data -- unlike Phase 0/1,
   this lab can't resimulate "the truth" at arbitrary N. Instead: every
   method fits on 2023 (365 days), and is scored against the ACTUAL 2024
   test year (366 days) it never saw -- the same discipline gblup_lab and
   mining_gpc_lab used for their synthetic-to-real transitions. Dollar
   scoring is reframed to match: since there's no independent "true
   required reserve" to compare against, each method's total annual cost
   is `reserve_mw x capacity_cost_per_MW_year` (the real stock cost of
   holding that reserve) PLUS the REALIZED under-procurement cost summed
   directly over the 366 real test days it actually violated on -- not a
   probability-times-365 extrapolation the way Phase 1's synthetic oracle
   needed, since the test set IS a real, complete year.

At n=15 real BAs, this fleet is nowhere near the ~40k in-core ceiling
`gp_ooc_fortran.py` exists to push past -- see RESULTS_PHASE2.md for why
that's a real, honest finding about this domain's scale, not a shortfall of
this lab's execution.
"""

import json
import time

import numpy as np

import data_eia930
import naive_baselines
import gp_shortfall_model
import regime_mixture
import reserve_calc

N_METHOD_SCENARIOS = 500_000
SEED = 0

RESULTS = {}


def _annual_holding_cost(reserve_mw, cost_per_mw_year=reserve_calc.RESERVE_COST_PER_MW_YEAR):
    return reserve_mw * cost_per_mw_year


def _annual_realized_underprocurement_cost(test_total_shortfall, reserve_mw,
                                            voll_per_mwh=reserve_calc.VOLL_PER_MWH,
                                            event_hours=reserve_calc.ILLUSTRATIVE_EVENT_HOURS):
    """Sum, directly over the real test year's actual violation days (no
    probability-times-365 extrapolation needed -- the test set already IS
    one real year), of (excess MW) x event_hours x VOLL. Same event_hours
    simplification as Phase 1 (reserve_calc.py's docstring) -- daily
    resolution stands in for an hourly event, pending real hourly data."""
    excess = np.clip(test_total_shortfall - reserve_mw, 0.0, None)
    return float(excess.sum()) * event_hours * voll_per_mwh


def score_real(method_name, reserve_mw, test_total_shortfall):
    achieved = reserve_calc.achieved_reliability(test_total_shortfall, reserve_mw)
    holding_cost = _annual_holding_cost(reserve_mw)
    under_cost = _annual_realized_underprocurement_cost(test_total_shortfall, reserve_mw)
    return dict(method=method_name, reserve_mw=reserve_mw, achieved_reliability_test_year=achieved,
                annual_holding_cost_usd=holding_cost,
                annual_realized_underprocurement_cost_usd=under_cost,
                total_annual_cost_usd=holding_cost + under_cost)


def main():
    fleet, train_shortfall, test_shortfall, train_dates, test_dates, train_signed, test_signed = \
        data_eia930.load_real_fleet_and_shortfall()
    test_total_shortfall = test_shortfall.sum(axis=1)
    print(f"real fleet: {fleet['n']} BAs {fleet['ba_list']}")
    print(f"train: {len(train_dates)} real days ({train_dates.min().date()}"
          f"..{train_dates.max().date()})")
    print(f"test:  {len(test_dates)} real days ({test_dates.min().date()}"
          f"..{test_dates.max().date()}), mean total shortfall "
          f"{test_total_shortfall.mean():,.0f} MW, max {test_total_shortfall.max():,.0f} MW")
    RESULTS["fleet_ba_list"] = fleet["ba_list"]
    RESULTS["nameplate_mw"] = fleet["nameplate_mw"].tolist()

    # --- Fit methods 1-2 (Python, cheap) ---
    independence_fit = naive_baselines.fit_independence(train_shortfall)
    aggregate_fit = naive_baselines.fit_aggregate_correlation(train_shortfall)
    print(f"method 2 fitted (real) fleet-wide rho = {aggregate_fit['rho']:.3f}")

    rust_result = naive_baselines.run_rust_baselines(
        fleet, independence_fit, aggregate_fit, N_METHOD_SCENARIOS,
        reserve_calc.TARGET_RELIABILITY_DAILY, seed=SEED)
    print(f"[rust] method0 N-1={rust_result['method0_ercot_n1_reserve_mw']:.1f}MW "
          f"5%wind={rust_result['method0_wecc_generic_reserve_mw']:.1f}MW "
          f"method1={rust_result['method1_independence']['reserve_mw']:.1f}MW "
          f"method2={rust_result['method2_aggregate_correlation']['reserve_mw']:.1f}MW")

    # --- Method 3: vanilla spatial GP over REAL BA centroids ---
    t0 = time.perf_counter()
    gp_fit = gp_shortfall_model.fit_gp_shortfall_model(train_shortfall, fleet)
    gp_fit_wall = time.perf_counter() - t0
    print(f"method 3 GP fit: ell={gp_fit['mle']['ell']:.3f} (deg) sigma_f2={gp_fit['sigma_f2']:.3f} "
          f"sigma_n2={gp_fit['sigma_n2']:.3f} lml={gp_fit['mle']['lml']:.1f} ({gp_fit_wall:.1f}s)")
    gp_scenarios = gp_shortfall_model.sample_gp_scenarios(gp_fit, N_METHOD_SCENARIOS, seed=SEED)
    method3_reserve_mw = reserve_calc.required_reserve_mw(gp_scenarios.sum(axis=1))

    # --- Method 4: GP + soft-EM regime-mixture over REAL data ---
    t0 = time.perf_counter()
    mix_fit = regime_mixture.fit_regime_mixture_soft(
        train_shortfall, fleet, signed_shortfall=train_signed, seed=SEED)
    mix_fit_wall = time.perf_counter() - t0
    print(f"method 4 soft-EM fit: p_hat={mix_fit['p_hat']:.3f} (raw {mix_fit['p_hat_raw']:.3f}) "
          f"({mix_fit_wall:.1f}s)")
    mix_scenarios = regime_mixture.sample_regime_mixture_scenarios(mix_fit, N_METHOD_SCENARIOS, seed=SEED)
    method4_reserve_mw = reserve_calc.required_reserve_mw(mix_scenarios.sum(axis=1))

    scores = [
        score_real("0_ercot_n1", rust_result["method0_ercot_n1_reserve_mw"], test_total_shortfall),
        score_real("0_wecc_generic", rust_result["method0_wecc_generic_reserve_mw"], test_total_shortfall),
        score_real("1_independence_control", rust_result["method1_independence"]["reserve_mw"],
                   test_total_shortfall),
        score_real("2_aggregate_correlation", rust_result["method2_aggregate_correlation"]["reserve_mw"],
                   test_total_shortfall),
        score_real("3_vanilla_spatial_gp", method3_reserve_mw, test_total_shortfall),
        score_real("4_gp_soft_em_regime_mixture", method4_reserve_mw, test_total_shortfall),
    ]

    print("\n--- Real-data scorecard (fit on 2023, scored on held-out 2024) ---")
    print(f"{'method':28s} {'reserve_mw':>12s} {'achieved_rel':>13s} "
          f"{'holding_$/yr':>15s} {'under_$/yr':>15s} {'total_$/yr':>15s}")
    for s in scores:
        print(f"{s['method']:28s} {s['reserve_mw']:12,.1f} "
              f"{s['achieved_reliability_test_year']:13.4f} "
              f"{s['annual_holding_cost_usd']:15,.0f} "
              f"{s['annual_realized_underprocurement_cost_usd']:15,.0f} "
              f"{s['total_annual_cost_usd']:15,.0f}")

    RESULTS["scores"] = scores
    RESULTS["gp_fit_summary"] = dict(ell_deg=gp_fit["mle"]["ell"], sigma_f2=gp_fit["sigma_f2"],
                                      sigma_n2=gp_fit["sigma_n2"], lml=gp_fit["mle"]["lml"])
    RESULTS["regime_mixture_summary"] = dict(p_hat=mix_fit["p_hat"], p_hat_raw=mix_fit["p_hat_raw"],
                                              mean_responsibility=mix_fit["mean_responsibility"])

    with open("results_phase2.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    print("\nwrote results_phase2.json")


if __name__ == "__main__":
    main()
