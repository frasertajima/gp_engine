"""Robustness check on the soft-classifier finding: does it survive when
the regime is spatially LOCALIZED (only a subset of the book affected each
systemic year), instead of hitting the whole book at once?

dgp_simulator.py's regime shock affects every property simultaneously, so
method 4's classifier feature (log of the book's TOTAL loss) is close to a
sufficient statistic for the regime BY CONSTRUCTION -- a fair reviewer
critique of RESULTS_PHASE1.md/RESULTS_PHASE2.md's headline result. This
script re-runs the four-method ladder under dgp_simulator_localized.py at
several footprint sizes (1.0 = unrestricted/global, 0.20, 0.05 = only 5% of
the book affected per systemic year) and reports two things per config:

1. Classification quality: mean GMM responsibility for TRUE systemic years
   vs TRUE normal years (using the true regime label ONLY for this
   diagnostic -- no fitted method ever sees it) -- does the classifier
   still separate the two as the footprint shrinks?
2. The usual achieved-survival comparison, hard vs soft, at two historical
   sample sizes (60, 500 years).
"""

import json

import numpy as np

from exposures import build_book
import dgp_simulator_localized as dgpl
import naive_baselines as nb
import gp_loss_model as gpl
import regime_mixture as rm
import capital_calc as cc

N_PROPERTIES = 500
BOOK_SEED = 0
ORACLE_YEARS = 200_000
ORACLE_SEED = 999
N_SCENARIOS = 20_000
TARGET_SURVIVAL = 0.995
FOOTPRINT_FRACS = [1.0, 0.20, 0.05]
HISTORICAL_YEARS_GRID = [60, 500]
SEEDS_PER_SIZE = 3
SEED_BASE = 5000


def classification_diagnostic(losses, true_regime, book):
    """Mean GaussianMixture responsibility for true-systemic vs true-normal
    years -- the true label is used ONLY here, for diagnosis, never passed
    to any fitted method."""
    fit = rm.fit_regime_mixture_soft(losses, book)
    resp = np.asarray(fit["responsibilities"])
    mean_resp_true_sys = float(resp[true_regime].mean()) if true_regime.any() else float("nan")
    mean_resp_true_normal = float(resp[~true_regime].mean())
    return dict(mean_resp_true_systemic=mean_resp_true_sys,
                mean_resp_true_normal=mean_resp_true_normal,
                separation=mean_resp_true_sys - mean_resp_true_normal, fit=fit)


def run_trial(book, oracle_total, oracle_true_capital, n_years, seed, footprint_frac):
    historical = dgpl.sample_true_losses_localized(book, n_years, footprint_frac=footprint_frac,
                                                    seed=seed)
    losses_hist = historical["losses"]
    V = book["insured_value"]

    table = {}

    fit1 = nb.fit_independence(losses_hist, book)
    scen1 = nb.sample_independence_scenarios(fit1, V, N_SCENARIOS, seed=1)
    table["1_independence"] = scen1.sum(axis=1)

    fit2 = nb.fit_flat_correlation(losses_hist, book)
    scen2 = nb.sample_flat_correlation_scenarios(fit2, V, N_SCENARIOS, seed=2)
    table["2_flat_correlation"] = scen2.sum(axis=1)

    fit3 = gpl.fit_gp_loss_model(losses_hist, book)
    scen3 = gpl.sample_gp_scenarios(fit3, V, N_SCENARIOS, seed=3)
    table["3_vanilla_gp"] = scen3.sum(axis=1)

    diag = classification_diagnostic(losses_hist, historical["regime"], book)

    try:
        fit4_hard = rm.fit_regime_mixture(losses_hist, book)
        scen4h = rm.sample_regime_mixture_scenarios(fit4_hard, V, N_SCENARIOS, seed=4)
        table["4_hard"] = scen4h.sum(axis=1)
    except ValueError:
        table["4_hard"] = None

    scen4s = rm.sample_regime_mixture_scenarios(diag["fit"], V, N_SCENARIOS, seed=5)
    table["4_soft"] = scen4s.sum(axis=1)

    scored = {}
    for name, scenario_total in table.items():
        if scenario_total is None:
            continue
        capital = cc.required_capital(scenario_total, TARGET_SURVIVAL)
        achieved = cc.survival_probability(oracle_total, capital)
        gap = capital - oracle_true_capital
        scored[name] = dict(required_capital=capital, achieved_survival_probability=achieved,
                             capital_gap_vs_oracle_dollars=gap)

    return dict(scored=scored, n_true_systemic=int(historical["regime"].sum()),
                classification=dict(mean_resp_true_systemic=diag["mean_resp_true_systemic"],
                                     mean_resp_true_normal=diag["mean_resp_true_normal"],
                                     separation=diag["separation"]))


def main():
    book = build_book(N_PROPERTIES, seed=BOOK_SEED)

    results = {}
    for frac in FOOTPRINT_FRACS:
        print(f"\n=== footprint_frac={frac} ===", flush=True)
        oracle = dgpl.sample_true_losses_localized(book, ORACLE_YEARS, footprint_frac=frac,
                                                    seed=ORACLE_SEED)
        oracle_total = oracle["losses"].sum(axis=1)
        oracle_true_capital = cc.required_capital(oracle_total, TARGET_SURVIVAL)
        print(f"  radius={oracle['radius_deg']:.3f} deg  oracle true capital="
              f"${oracle_true_capital:,.0f}", flush=True)

        frac_summary = {}
        for n_years in HISTORICAL_YEARS_GRID:
            per_method_survival = {}
            per_method_gap = {}
            seps = []
            for s in range(SEEDS_PER_SIZE):
                seed = SEED_BASE + n_years * 100 + s
                trial = run_trial(book, oracle_total, oracle_true_capital, n_years, seed, frac)
                seps.append(trial["classification"]["separation"])
                for name, row in trial["scored"].items():
                    per_method_survival.setdefault(name, []).append(
                        row["achieved_survival_probability"])
                    per_method_gap.setdefault(name, []).append(
                        row["capital_gap_vs_oracle_dollars"])

            summary = dict(
                n_years=n_years,
                mean_classifier_separation=float(np.mean(seps)),
                methods={
                    name: dict(mean_achieved_survival=float(np.mean(vals)),
                               mean_capital_gap_dollars=float(np.mean(per_method_gap[name])))
                    for name, vals in per_method_survival.items()
                },
            )
            frac_summary[n_years] = summary
            print(f"  n_years={n_years:4d}  mean classifier separation="
                  f"{summary['mean_classifier_separation']:.3f}", flush=True)
            for name, m in summary["methods"].items():
                print(f"      {name:14s} achieved_survival={m['mean_achieved_survival']:.4f}  "
                      f"capital_gap=${m['mean_capital_gap_dollars']:>14,.0f}", flush=True)

        results[frac] = dict(oracle_true_capital=oracle_true_capital,
                              radius_deg=oracle["radius_deg"], by_years=frac_summary)

    with open("results_phase1_localized.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote results_phase1_localized.json", flush=True)


if __name__ == "__main__":
    main()
