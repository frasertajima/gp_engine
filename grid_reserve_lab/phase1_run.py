"""Phase 1: the five-method ladder, small scale, both languages.

Fits methods 0-4 on ONE historical-style sample (illustrative: 730 days,
~2 years -- a plausible amount of daily fleet-output history a real
operator might have), scores every method's chosen reserve requirement
against a much larger oracle resample (achieved reliability + dollar gap,
both directions, per reserve_calc.py). Also benchmarks the Rust
`reserve_baseline` crate against a vectorized NumPy reference for methods
1-2, per LAB_PLAN.md's "Rust component" fairness requirement.

Mirrors climate_cat_lab/phase1_run.py's structure and honesty conventions:
report the achieved-reliability table and dollar-gap table plainly, and
report explicitly whether method 3 (vanilla GP) or only method 4
(soft-EM regime-mixture) closes most of the gap between method 2 (real ISO
practice) and the truth -- LAB_PLAN.md's central open question.
"""

import json
import time

import numpy as np

from fleet import build_fleet
from dgp_simulator import sample_true_output
import naive_baselines
import gp_shortfall_model
import regime_mixture
import reserve_calc

N_SITES = 100
N_HISTORICAL_DAYS = 730       # ~2 years -- a plausible real historical sample size
N_ORACLE_DAYS = 500_000       # large resample for scoring (achieved reliability, dollar gap)
N_METHOD_SCENARIOS = 500_000  # scenarios each method's own reserve-quantile calc draws
SEED_FLEET = 0
SEED_HISTORICAL = 1
SEED_ORACLE = 2

RESULTS = {}


def main():
    fleet = build_fleet(N_SITES, seed=SEED_FLEET)
    print(f"fleet: {N_SITES} sites, mean nameplate {fleet['nameplate_mw'].mean():,.0f} MW, "
          f"total nameplate {fleet['nameplate_mw'].sum():,.0f} MW")

    hist_sim = sample_true_output(fleet, N_HISTORICAL_DAYS, seed=SEED_HISTORICAL)
    hist_shortfall = hist_sim["shortfall_mw"]
    print(f"historical sample: {N_HISTORICAL_DAYS} days, "
          f"{int(hist_sim['regime'].sum())} drought days")

    oracle_sim = sample_true_output(fleet, N_ORACLE_DAYS, seed=SEED_ORACLE)
    oracle_total_shortfall = oracle_sim["shortfall_mw"].sum(axis=1)
    true_required_reserve_mw = reserve_calc.required_reserve_mw(oracle_total_shortfall)
    print(f"oracle: {N_ORACLE_DAYS} days, true required reserve "
          f"(target reliability {reserve_calc.TARGET_RELIABILITY_DAILY:.6f}) = "
          f"{true_required_reserve_mw:,.1f} MW")
    RESULTS["true_required_reserve_mw"] = true_required_reserve_mw
    RESULTS["target_reliability"] = reserve_calc.TARGET_RELIABILITY_DAILY

    # --- Fit methods 1-2 (Python, cheap) ---
    independence_fit = naive_baselines.fit_independence(hist_shortfall)
    aggregate_fit = naive_baselines.fit_aggregate_correlation(hist_shortfall)
    print(f"method 2 fitted fleet-wide rho = {aggregate_fit['rho']:.3f}")

    # --- Methods 0-2 via Rust (the real timed run) ---
    rust_result = naive_baselines.run_rust_baselines(
        fleet, independence_fit, aggregate_fit, N_METHOD_SCENARIOS,
        reserve_calc.TARGET_RELIABILITY_DAILY, seed=SEED_HISTORICAL)
    print(f"[rust] method0 N-1={rust_result['method0_ercot_n1_reserve_mw']:.1f}MW "
          f"5%wind={rust_result['method0_wecc_generic_reserve_mw']:.1f}MW "
          f"method1={rust_result['method1_independence']['reserve_mw']:.1f}MW "
          f"({rust_result['method1_independence']['wall_s']*1000:.2f}ms) "
          f"method2={rust_result['method2_aggregate_correlation']['reserve_mw']:.1f}MW "
          f"({rust_result['method2_aggregate_correlation']['wall_s']*1000:.2f}ms)")

    # --- Same methods 1-2 via plain vectorized NumPy, for the fairness benchmark ---
    py_result = naive_baselines.python_reference_baselines(
        independence_fit, aggregate_fit, N_METHOD_SCENARIOS,
        reserve_calc.TARGET_RELIABILITY_DAILY, seed=SEED_HISTORICAL)
    print(f"[numpy] method1={py_result['method1_independence']['reserve_mw']:.1f}MW "
          f"({py_result['method1_independence']['wall_s']*1000:.2f}ms) "
          f"method2={py_result['method2_aggregate_correlation']['reserve_mw']:.1f}MW "
          f"({py_result['method2_aggregate_correlation']['wall_s']*1000:.2f}ms)")

    RESULTS["rust_vs_numpy_benchmark"] = dict(
        n_scenarios=N_METHOD_SCENARIOS,
        rust_method1_wall_s=rust_result["method1_independence"]["wall_s"],
        rust_method2_wall_s=rust_result["method2_aggregate_correlation"]["wall_s"],
        rust_subprocess_call_wall_s=rust_result["subprocess_call_wall_s"],
        numpy_method1_wall_s=py_result["method1_independence"]["wall_s"],
        numpy_method2_wall_s=py_result["method2_aggregate_correlation"]["wall_s"],
        rust_speedup_method1=py_result["method1_independence"]["wall_s"]
        / max(rust_result["method1_independence"]["wall_s"], 1e-9),
        rust_speedup_method2=py_result["method2_aggregate_correlation"]["wall_s"]
        / max(rust_result["method2_aggregate_correlation"]["wall_s"], 1e-9),
    )

    # --- Method 3: vanilla spatial GP ---
    t0 = time.perf_counter()
    gp_fit = gp_shortfall_model.fit_gp_shortfall_model(hist_shortfall, fleet)
    gp_fit_wall = time.perf_counter() - t0
    print(f"method 3 GP fit: ell={gp_fit['mle']['ell']:.3f} sigma_f2={gp_fit['sigma_f2']:.3f} "
          f"sigma_n2={gp_fit['sigma_n2']:.3f} lml={gp_fit['mle']['lml']:.1f} "
          f"({gp_fit_wall:.1f}s)")
    gp_scenarios = gp_shortfall_model.sample_gp_scenarios(
        gp_fit, N_METHOD_SCENARIOS, seed=SEED_HISTORICAL)
    gp_total = gp_scenarios.sum(axis=1)
    method3_reserve_mw = reserve_calc.required_reserve_mw(gp_total)

    # --- Method 4: GP + soft-EM regime-mixture ---
    t0 = time.perf_counter()
    mix_fit = regime_mixture.fit_regime_mixture_soft(
        hist_shortfall, fleet, signed_shortfall=hist_sim["signed_shortfall_mw"], seed=SEED_HISTORICAL)
    mix_fit_wall = time.perf_counter() - t0
    print(f"method 4 soft-EM fit: p_hat={mix_fit['p_hat']:.3f} "
          f"(raw {mix_fit['p_hat_raw']:.3f}), mean responsibility "
          f"{mix_fit['mean_responsibility']:.3f} ({mix_fit_wall:.1f}s)")
    mix_scenarios = regime_mixture.sample_regime_mixture_scenarios(
        mix_fit, N_METHOD_SCENARIOS, seed=SEED_HISTORICAL)
    mix_total = mix_scenarios.sum(axis=1)
    method4_reserve_mw = reserve_calc.required_reserve_mw(mix_total)

    # --- Score every method against the oracle ---
    scores = [
        reserve_calc.score_method("0_ercot_n1", rust_result["method0_ercot_n1_reserve_mw"],
                                   oracle_total_shortfall, true_required_reserve_mw),
        reserve_calc.score_method("0_wecc_generic", rust_result["method0_wecc_generic_reserve_mw"],
                                   oracle_total_shortfall, true_required_reserve_mw),
        reserve_calc.score_method("1_independence_control",
                                   rust_result["method1_independence"]["reserve_mw"],
                                   oracle_total_shortfall, true_required_reserve_mw),
        reserve_calc.score_method("2_aggregate_correlation",
                                   rust_result["method2_aggregate_correlation"]["reserve_mw"],
                                   oracle_total_shortfall, true_required_reserve_mw),
        reserve_calc.score_method("3_vanilla_spatial_gp", method3_reserve_mw,
                                   oracle_total_shortfall, true_required_reserve_mw),
        reserve_calc.score_method("4_gp_soft_em_regime_mixture", method4_reserve_mw,
                                   oracle_total_shortfall, true_required_reserve_mw),
    ]

    print("\n--- Scorecard (target reliability = "
          f"{reserve_calc.TARGET_RELIABILITY_DAILY:.6f}) ---")
    print(f"{'method':28s} {'reserve_mw':>12s} {'achieved_rel':>13s} "
          f"{'under_$/yr':>15s} {'over_$/yr':>15s} {'net_gap_$/yr':>15s}")
    for s in scores:
        print(f"{s['method']:28s} {s['reserve_mw']:12,.1f} {s['achieved_reliability']:13.6f} "
              f"{s['annual_underprocurement_cost_usd']:15,.0f} "
              f"{s['annual_overprocurement_cost_usd']:15,.0f} "
              f"{s['net_dollar_gap_usd']:15,.0f}")

    RESULTS["scores"] = scores
    RESULTS["gp_fit_summary"] = dict(ell=gp_fit["mle"]["ell"], sigma_f2=gp_fit["sigma_f2"],
                                      sigma_n2=gp_fit["sigma_n2"], lml=gp_fit["mle"]["lml"],
                                      wall_s=gp_fit_wall)
    RESULTS["regime_mixture_summary"] = dict(p_hat=mix_fit["p_hat"], p_hat_raw=mix_fit["p_hat_raw"],
                                              mean_responsibility=mix_fit["mean_responsibility"],
                                              wall_s=mix_fit_wall)

    with open("results_phase1.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    print("\nwrote results_phase1.json")


if __name__ == "__main__":
    main()
