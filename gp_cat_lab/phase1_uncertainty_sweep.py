"""Empirical epistemic-uncertainty bands on the capital ESTIMATE itself.

RESULTS_PHASE1.md/RESULTS_PHASE2.md report each method's MEAN achieved
survival across a few seeds, but never show how much a single real-world
insurer's actual point estimate would vary just from WHICH historical
years happened to be observed -- the parameter-uncertainty critique (a
single historical draw's fitted (ell, sigma_f2, sigma_n2, p_hat) has real
sampling variance, especially at small n_years, and every method here
samples scenarios from its POINT ESTIMATE, silently ignoring that
variance).

This script re-draws MANY (default 25) independent historical samples at
each of Phase 1's historical-years grid points, refitting from scratch
each time, and reports the empirical 5th/50th/95th percentile of the
resulting capital ESTIMATE C_hat across those draws -- literally the
sampling distribution of the point estimate, which is exactly what a
lightweight (non-Bayesian) answer to "how much does capital sizing move
around just from which years you happened to observe" looks like. A
narrow band = the point estimate is stable regardless of historical draw;
a wide band = a real insurer fitting on their own one draw could land
anywhere in that range purely from bad luck in which years they have data
for.
"""

import json

import numpy as np

from exposures import build_book
from dgp_simulator import sample_true_losses
import gp_loss_model as gpl
import regime_mixture as rm
import capital_calc as cc

N_PROPERTIES = 500
BOOK_SEED = 0
ORACLE_YEARS = 500_000
ORACLE_SEED = 999
N_SCENARIOS = 20_000
TARGET_SURVIVAL = 0.995
HISTORICAL_YEARS_GRID = [60, 120, 250, 500]
N_DRAWS = 25
SEED_BASE = 9000


def fit_and_capital(losses_hist, book):
    V = book["insured_value"]
    out = {}

    fit3 = gpl.fit_gp_loss_model(losses_hist, book)
    scen3 = gpl.sample_gp_scenarios(fit3, V, N_SCENARIOS, seed=3)
    out["3_vanilla_gp"] = cc.required_capital(scen3.sum(axis=1), TARGET_SURVIVAL)

    try:
        fit4h = rm.fit_regime_mixture(losses_hist, book)
        scen4h = rm.sample_regime_mixture_scenarios(fit4h, V, N_SCENARIOS, seed=4)
        out["4_hard"] = cc.required_capital(scen4h.sum(axis=1), TARGET_SURVIVAL)
    except ValueError:
        out["4_hard"] = None

    fit4s = rm.fit_regime_mixture_soft(losses_hist, book)
    scen4s = rm.sample_regime_mixture_scenarios(fit4s, V, N_SCENARIOS, seed=5)
    out["4_soft"] = cc.required_capital(scen4s.sum(axis=1), TARGET_SURVIVAL)
    return out


def main():
    book = build_book(N_PROPERTIES, seed=BOOK_SEED)
    oracle = sample_true_losses(book, ORACLE_YEARS, seed=ORACLE_SEED)
    oracle_total = oracle["losses"].sum(axis=1)
    oracle_true_capital = cc.required_capital(oracle_total, TARGET_SURVIVAL)
    print(f"oracle true capital @ {TARGET_SURVIVAL:.1%} = ${oracle_true_capital:,.0f}\n",
          flush=True)

    results = {"oracle_true_capital": oracle_true_capital, "by_years": {}}
    for n_years in HISTORICAL_YEARS_GRID:
        draws = {"3_vanilla_gp": [], "4_hard": [], "4_soft": []}
        for d in range(N_DRAWS):
            seed = SEED_BASE + n_years * 1000 + d
            historical = sample_true_losses(book, n_years, seed=seed)
            capitals = fit_and_capital(historical["losses"], book)
            for name, c in capitals.items():
                if c is not None:
                    draws[name].append(c)

        summary = {}
        for name, vals in draws.items():
            vals = np.array(vals)
            summary[name] = dict(
                n_draws=len(vals),
                p5=float(np.percentile(vals, 5)), p50=float(np.percentile(vals, 50)),
                p95=float(np.percentile(vals, 95)),
                mean=float(vals.mean()), std=float(vals.std()),
                cv=float(vals.std() / vals.mean()) if vals.mean() != 0 else None,
            )
        results["by_years"][n_years] = summary
        print(f"n_years={n_years:4d}", flush=True)
        for name, s in summary.items():
            print(f"    {name:14s} p5=${s['p5']:>13,.0f}  p50=${s['p50']:>13,.0f}  "
                  f"p95=${s['p95']:>13,.0f}  CV={s['cv']:.2f}  (n={s['n_draws']})", flush=True)

    with open("results_phase1_uncertainty.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote results_phase1_uncertainty.json", flush=True)


if __name__ == "__main__":
    main()
