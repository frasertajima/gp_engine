"""Phase 1: the four-way ladder, small scale.

Draws ONE historical-style sample from the oracle (the only data every
fitted method sees), fits all four methods (LAB_PLAN.md's Method section),
has each produce a required-capital decision at a fixed target survival
probability, then scores every decision against the TRUE oracle -- a large
fresh resample never seen by any fitted method -- for (a) the achieved
survival probability (does the method's number actually deliver ~99.5%?)
and (b) the dollar gap (expected shortfall if under-reserved, excess
capital if over-reserved).

`run_experiment` is the reusable single-trial engine; `phase1_sweep.py`
calls it repeatedly across historical sample sizes and seeds to separate
two different failure modes this Phase 1 run surfaced (see RESULTS_PHASE1.md):
a small-sample REGIME-FREQUENCY estimation problem (fixable with more
history, for a structurally-correct model) from a persistent STRUCTURAL
ceiling (not fixable with more history, for methods 1-3, which cannot
represent a regime at all).
"""

import json

from exposures import build_book
from dgp_simulator import sample_true_losses
import naive_baselines as nb
import gp_loss_model as gpl
import regime_mixture as rm
import capital_calc as cc

N_PROPERTIES = 500
BOOK_SEED = 0
HISTORICAL_YEARS = 60      # what every fitted method is allowed to see
HISTORICAL_SEED = 100      # distinct from Phase 0's verification seed
ORACLE_YEARS = 500_000     # ground truth, never seen by any fitted method
ORACLE_SEED = 999
N_SCENARIOS = 20_000       # Monte Carlo scenarios per fitted method
TARGET_SURVIVAL = 0.995    # Solvency II SCR convention


def run_experiment(book, oracle_total, oracle_true_capital, historical_years,
                    historical_seed, n_scenarios=N_SCENARIOS,
                    target_survival=TARGET_SURVIVAL, verbose=True,
                    method4_fit_fn=rm.fit_regime_mixture):
    """One trial: draw a historical sample of `historical_years` years
    (seed `historical_seed`), fit all four methods, score each against the
    (already-simulated) oracle. Returns dict(table, meta)."""
    V = book["insured_value"]
    historical = sample_true_losses(book, historical_years, seed=historical_seed)
    losses_hist = historical["losses"]
    n_true_systemic = int(historical["regime"].sum())
    if verbose:
        print(f"historical sample: {historical_years} years, {n_true_systemic} "
              f"true-systemic years (hidden from every fitted method)")

    methods = {}

    fit1 = nb.fit_independence(losses_hist, book)
    scen1 = nb.sample_independence_scenarios(fit1, V, n_scenarios, seed=1)
    methods["1_independence"] = scen1.sum(axis=1)

    fit2 = nb.fit_flat_correlation(losses_hist, book)
    scen2 = nb.sample_flat_correlation_scenarios(fit2, V, n_scenarios, seed=2)
    methods["2_flat_correlation"] = scen2.sum(axis=1)
    if verbose:
        print(f"method 2 (flat correlation): fitted rho={fit2['rho']:.3f}")

    fit3 = gpl.fit_gp_loss_model(losses_hist, book)
    scen3 = gpl.sample_gp_scenarios(fit3, V, n_scenarios, seed=3)
    methods["3_vanilla_gp"] = scen3.sum(axis=1)
    if verbose:
        print(f"method 3 (spatial GP): fitted ell={fit3['mle']['ell']:.3f} deg, "
              f"sigma_f2={fit3['sigma_f2']:.4f}, sigma_n2={fit3['sigma_n2']:.4f}")

    fit4_p_hat = None
    try:
        fit4 = method4_fit_fn(losses_hist, book)
        scen4 = rm.sample_regime_mixture_scenarios(fit4, V, n_scenarios, seed=4)
        methods["4_gp_regime_mixture"] = scen4.sum(axis=1)
        fit4_p_hat = fit4["p_hat"]
        if verbose:
            split_desc = (f"fit split {fit4['n_stress']} stress / {fit4['n_normal']} "
                           f"normal years" if "n_stress" in fit4 else
                           f"mean responsibility={fit4['mean_responsibility']:.3f} "
                           f"(soft, no hard split)")
            print(f"method 4 (GP + regime-mixture): fitted p_hat={fit4['p_hat']:.3f} "
                  f"(true p_systemic={historical['params']['p_systemic']:.3f}, hidden), "
                  f"{split_desc}")
    except ValueError as e:
        if verbose:
            print(f"method 4 (GP + regime-mixture): SKIPPED -- {e}")

    table = {}
    for name, scenario_total in methods.items():
        capital = cc.required_capital(scenario_total, target_survival)
        achieved_survival = cc.survival_probability(oracle_total, capital)
        dollar_shortfall = cc.expected_shortfall(oracle_total, capital)
        capital_gap = capital - oracle_true_capital
        table[name] = dict(
            required_capital=capital,
            achieved_survival_probability=achieved_survival,
            target_survival_probability=target_survival,
            survival_probability_gap=achieved_survival - target_survival,
            expected_annual_shortfall_dollars=dollar_shortfall,
            capital_gap_vs_oracle_dollars=capital_gap,
        )
        if verbose:
            print(f"[{name}] capital=${capital:,.0f} achieved_survival={achieved_survival:.4f} "
                  f"(target {target_survival:.4f}) shortfall=${dollar_shortfall:,.0f}/yr "
                  f"gap_vs_true=${capital_gap:,.0f}")

    return dict(table=table, n_true_systemic=n_true_systemic,
                fit4_p_hat=fit4_p_hat,
                true_p_systemic=historical["params"]["p_systemic"])


def main():
    book = build_book(N_PROPERTIES, seed=BOOK_SEED)

    oracle = sample_true_losses(book, ORACLE_YEARS, seed=ORACLE_SEED)
    oracle_total = oracle["losses"].sum(axis=1)
    oracle_true_capital = cc.required_capital(oracle_total, TARGET_SURVIVAL)
    print(f"oracle ground truth ({ORACLE_YEARS} years): true capital @ "
          f"{TARGET_SURVIVAL:.1%} = ${oracle_true_capital:,.0f}")

    result = run_experiment(book, oracle_total, oracle_true_capital,
                             HISTORICAL_YEARS, HISTORICAL_SEED)

    output = dict(oracle_true_capital=oracle_true_capital, oracle_years=ORACLE_YEARS,
                  methods=result["table"],
                  params=dict(n_properties=N_PROPERTIES, historical_years=HISTORICAL_YEARS,
                              historical_seed=HISTORICAL_SEED, oracle_years=ORACLE_YEARS,
                              n_scenarios=N_SCENARIOS, target_survival=TARGET_SURVIVAL,
                              true_p_systemic=result["true_p_systemic"],
                              n_true_systemic_in_sample=result["n_true_systemic"]))

    with open("results_phase1.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nwrote results_phase1.json")


if __name__ == "__main__":
    main()
