"""Phase 2: scale to where the OOC engine matters, and put a real dollar
figure on it.

Same four-way ladder as Phase 1, but at n=45,000 properties -- past this
session's actual measured in-core VRAM ceiling (~30,000 on this 4GB GPU;
see RESULTS_PHASE2.md), genuinely requiring gp_ooc_fortran.py for the
spatial GP methods' log-marginal-likelihood evaluation. Methods 1
(independence) and 2 (flat correlation) scale trivially -- no n x n matrix
involved at all (method 2 uses the O(n) single-common-factor sampler,
naive_baselines.py). Methods 3/4 reuse Phase 1's fitted spatial length
scale (a geography-driven property, not tied to property count) and do a
small, genuine OOC-based refinement of (sigma_f2, sigma_n2) -- see
gp_loss_model_large.py's docstring for why a full from-scratch search
isn't attempted at this scale.

The oracle DGP and all scenario generation use rff_sampler.py's Random
Fourier Features approximation (validated at Phase 0's exact n=500 scale,
phase2_rff_validation.py) -- exact dense Cholesky sampling is infeasible
at n=45,000 (>16GB, O(n^3)), and neither gp_core.py nor gp_ooc_fortran.py
expose a "multiply by the Cholesky factor" primitive (only solve).
"""

import json
import os

import numpy as np

from exposures import build_book
import naive_baselines as nb
import gp_loss_model as gpl
import regime_mixture as rm
import gp_loss_model_large as gpl_large
import dgp_simulator_large as dgp_large
import capital_calc as cc
import phase1_run as p1

N_PROPERTIES_LARGE = 45_000
BOOK_SEED_LARGE = 0
HISTORICAL_YEARS_LARGE = 25
HISTORICAL_SEED_LARGE = 100
ORACLE_YEARS_LARGE = 100_000
ORACLE_SEED_LARGE = 999
N_SCENARIOS = 20_000
SCENARIO_BATCH = 2_000       # generate/reduce scenarios in chunks -- keeps peak
                             # memory to one batch's (n_properties,) x (batch,)
                             # array (a few hundred MB) instead of the full
                             # (20,000 x 45,000) ~7.2GB array. A prior run on a
                             # 4GB-VRAM laptop locked the machine; this and the
                             # lower OOC_RAM_BUDGET_GB below are the fix.
TARGET_SURVIVAL = 0.995
N_RFF_FEATURES = 800
OOC_RAM_BUDGET_GB = 8.0      # pinned-memory tier budget for gp_ooc_fortran's
                             # panel storage -- was 16.0 (the library default),
                             # cut for headroom alongside everything else
                             # running on the same machine.
OOC_BACKING = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ooc_backing_phase2")


def generate_total_batched(sample_fn, total_n_scenarios, batch_size=SCENARIO_BATCH,
                            base_seed=0):
    """Calls sample_fn(n_scenarios, seed) -> (n_scenarios, n_properties) in
    chunks, immediately reducing each chunk to its per-scenario total and
    discarding the chunk -- peak memory is one batch's array, not the full
    scenario count's. Returns (total_n_scenarios,) totals."""
    totals = np.empty(total_n_scenarios)
    done = 0
    b = 0
    while done < total_n_scenarios:
        n = min(batch_size, total_n_scenarios - done)
        chunk = sample_fn(n, base_seed + b)
        totals[done:done + n] = chunk.sum(axis=1)
        done += n
        b += 1
    return totals


def fit_small_scale_starting_points():
    """Re-derives Phase 1's exact fitted hyperparameters (method 3's
    spatial kernel, method 4's two regime components) at n=500 --
    deterministic given the same seeds phase1_run.py uses -- as Phase 2's
    transfer starting point, rather than hardcoding printed numbers."""
    book = build_book(p1.N_PROPERTIES, seed=p1.BOOK_SEED)
    from dgp_simulator import sample_true_losses
    historical = sample_true_losses(book, p1.HISTORICAL_YEARS, seed=p1.HISTORICAL_SEED)
    losses_hist = historical["losses"]

    fit3 = gpl.fit_gp_loss_model(losses_hist, book)
    fit4 = rm.fit_regime_mixture(losses_hist, book)
    return dict(
        method3=dict(ell=fit3["mle"]["ell"], sigma_f2=fit3["sigma_f2"], sigma_n2=fit3["sigma_n2"]),
        method4_normal=dict(ell=fit4["fit_normal"]["mle"]["ell"],
                             sigma_f2=fit4["fit_normal"]["sigma_f2"],
                             sigma_n2=fit4["fit_normal"]["sigma_n2"]),
        method4_systemic=dict(ell=fit4["fit_systemic"]["mle"]["ell"],
                               sigma_f2=fit4["fit_systemic"]["sigma_f2"],
                               sigma_n2=fit4["fit_systemic"]["sigma_n2"]),
        p_hat=fit4["p_hat"],
    )


def main():
    os.makedirs(OOC_BACKING, exist_ok=True)
    print("=== Phase 2: scale to n=45,000 ===\n", flush=True)

    print("Step 0: re-deriving Phase 1's fitted hyperparameters as transfer starting points...",
          flush=True)
    start = fit_small_scale_starting_points()
    print(f"  method 3 starting point: {start['method3']}")
    print(f"  method 4 normal starting point: {start['method4_normal']}")
    print(f"  method 4 systemic starting point: {start['method4_systemic']}")
    print(f"  method 4 p_hat (transferred as-is, not refit at scale): {start['p_hat']:.4f}\n",
          flush=True)

    book = build_book(N_PROPERTIES_LARGE, seed=BOOK_SEED_LARGE)
    coords = np.stack([book["lat"], book["lon"]], axis=1)
    V = book["insured_value"]
    print(f"book: {N_PROPERTIES_LARGE} properties, mean insured value "
          f"${book['insured_value'].mean():,.0f}\n", flush=True)

    print(f"Step 1: drawing {HISTORICAL_YEARS_LARGE}-year historical sample from the oracle...",
          flush=True)
    historical = dgp_large.sample_true_losses_full(book, HISTORICAL_YEARS_LARGE,
                                                    seed=HISTORICAL_SEED_LARGE,
                                                    n_features=N_RFF_FEATURES)
    losses_hist = historical["losses"]
    print(f"  {int(historical['regime'].sum())} true-systemic years (hidden from every method)\n",
          flush=True)

    print(f"Step 2: drawing {ORACLE_YEARS_LARGE}-year oracle ground truth (totals only)...",
          flush=True)
    oracle = dgp_large.sample_true_totals(book, ORACLE_YEARS_LARGE, seed=ORACLE_SEED_LARGE,
                                          n_features=N_RFF_FEATURES)
    oracle_total = oracle["totals"]
    oracle_true_capital = cc.required_capital(oracle_total, TARGET_SURVIVAL)
    print(f"  oracle true capital @ {TARGET_SURVIVAL:.1%} = ${oracle_true_capital:,.0f}\n",
          flush=True)

    methods = {}

    print("Method 1 (independence)...", flush=True)
    fit1 = nb.fit_independence(losses_hist, book)
    scen1 = nb.sample_independence_scenarios(fit1, V, N_SCENARIOS, seed=1)
    methods["1_independence"] = scen1.sum(axis=1)
    del scen1

    print("Method 2 (flat correlation)...", flush=True)
    fit2 = nb.fit_flat_correlation(losses_hist, book)
    print(f"  fitted rho={fit2['rho']:.3f}", flush=True)
    scen2 = nb.sample_flat_correlation_scenarios(fit2, V, N_SCENARIOS, seed=2)
    methods["2_flat_correlation"] = scen2.sum(axis=1)
    del scen2

    print("Method 3 (vanilla spatial GP)... OOC refinement (3 evals):", flush=True)
    log_ratio3 = np.log(losses_hist / V[None, :])
    mu3 = log_ratio3.mean(axis=0)
    R3 = log_ratio3 - mu3[None, :]
    refined3 = gpl_large.refine_sigma_scale_ooc(
        coords, R3, start["method3"]["ell"], start["method3"]["sigma_f2"],
        start["method3"]["sigma_n2"], backing_dir=os.path.join(OOC_BACKING, "m3"))
    print(f"  refined: sigma_f2={refined3['sigma_f2']:.4f} sigma_n2={refined3['sigma_n2']:.4f} "
          f"(scale={refined3['scale']})", flush=True)
    scen3 = gpl_large.sample_gp_scenarios_rff(
        mu3, coords, start["method3"]["ell"], refined3["sigma_f2"], refined3["sigma_n2"],
        V, N_SCENARIOS, n_features=N_RFF_FEATURES, seed=3, feature_seed=10)
    methods["3_vanilla_gp"] = scen3.sum(axis=1)
    del scen3

    print("Method 4 (GP + regime-mixture)... OOC refinement (3 evals x 2 components):",
          flush=True)
    total_log_hist = np.log(losses_hist.sum(axis=1))
    p_hat = start["p_hat"]
    fit_quantile = float(np.clip(1.5 * p_hat, 8.0 / HISTORICAL_YEARS_LARGE, 0.35))
    cutoff = np.quantile(total_log_hist, 1.0 - fit_quantile)
    is_stress = total_log_hist >= cutoff
    n_stress, n_normal = int(is_stress.sum()), int((~is_stress).sum())
    print(f"  fit split: {n_stress} stress / {n_normal} normal years "
          f"(fit_quantile={fit_quantile:.3f})", flush=True)

    log_ratio_n = np.log(losses_hist[~is_stress] / V[None, :])
    mu_n = log_ratio_n.mean(axis=0)
    R_n = log_ratio_n - mu_n[None, :]
    refined_n = gpl_large.refine_sigma_scale_ooc(
        coords, R_n, start["method4_normal"]["ell"], start["method4_normal"]["sigma_f2"],
        start["method4_normal"]["sigma_n2"], backing_dir=os.path.join(OOC_BACKING, "m4n"))
    print(f"  normal component refined: sigma_f2={refined_n['sigma_f2']:.4f} "
          f"sigma_n2={refined_n['sigma_n2']:.4f}", flush=True)

    log_ratio_s = np.log(losses_hist[is_stress] / V[None, :])
    mu_s = log_ratio_s.mean(axis=0)
    R_s = log_ratio_s - mu_s[None, :]
    refined_s = gpl_large.refine_sigma_scale_ooc(
        coords, R_s, start["method4_systemic"]["ell"], start["method4_systemic"]["sigma_f2"],
        start["method4_systemic"]["sigma_n2"], backing_dir=os.path.join(OOC_BACKING, "m4s"))
    print(f"  systemic component refined: sigma_f2={refined_s['sigma_f2']:.4f} "
          f"sigma_n2={refined_s['sigma_n2']:.4f}", flush=True)

    rng = np.random.default_rng(4)
    is_sys_draw = rng.random(N_SCENARIOS) < p_hat
    n_sys_draw = int(is_sys_draw.sum())
    n_norm_draw = N_SCENARIOS - n_sys_draw
    scen4 = np.empty((N_SCENARIOS, N_PROPERTIES_LARGE))
    scen4[~is_sys_draw] = gpl_large.sample_gp_scenarios_rff(
        mu_n, coords, start["method4_normal"]["ell"], refined_n["sigma_f2"], refined_n["sigma_n2"],
        V, n_norm_draw, n_features=N_RFF_FEATURES, seed=41, feature_seed=11)
    scen4[is_sys_draw] = gpl_large.sample_gp_scenarios_rff(
        mu_s, coords, start["method4_systemic"]["ell"], refined_s["sigma_f2"], refined_s["sigma_n2"],
        V, n_sys_draw, n_features=N_RFF_FEATURES, seed=42, feature_seed=12)
    methods["4_gp_regime_mixture"] = scen4.sum(axis=1)
    del scen4

    print("\n=== Scoring against oracle ===", flush=True)
    table = {}
    for name, scenario_total in methods.items():
        capital = cc.required_capital(scenario_total, TARGET_SURVIVAL)
        achieved_survival = cc.survival_probability(oracle_total, capital)
        dollar_shortfall = cc.expected_shortfall(oracle_total, capital)
        capital_gap = capital - oracle_true_capital
        table[name] = dict(
            required_capital=capital,
            achieved_survival_probability=achieved_survival,
            target_survival_probability=TARGET_SURVIVAL,
            survival_probability_gap=achieved_survival - TARGET_SURVIVAL,
            expected_annual_shortfall_dollars=dollar_shortfall,
            capital_gap_vs_oracle_dollars=capital_gap,
        )
        print(f"[{name}] capital=${capital:,.0f} achieved_survival={achieved_survival:.4f} "
              f"(target {TARGET_SURVIVAL:.4f}) shortfall=${dollar_shortfall:,.0f}/yr "
              f"gap_vs_true=${capital_gap:,.0f}", flush=True)

    output = dict(oracle_true_capital=oracle_true_capital, oracle_years=ORACLE_YEARS_LARGE,
                  methods=table,
                  params=dict(n_properties=N_PROPERTIES_LARGE,
                              historical_years=HISTORICAL_YEARS_LARGE,
                              oracle_years=ORACLE_YEARS_LARGE, n_scenarios=N_SCENARIOS,
                              target_survival=TARGET_SURVIVAL, n_rff_features=N_RFF_FEATURES,
                              transferred_start=start))
    with open("results_phase2.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nwrote results_phase2.json", flush=True)


if __name__ == "__main__":
    main()
