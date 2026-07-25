"""Does a SOFT (responsibility-weighted) regime classifier close more of
method 4's remaining gap than the hard-partition classifier?

RESULTS_PHASE1.md's hard-partition method 4 (v2, adaptive) climbs from
94.8% (60 historical years) to 97.3% (500 years) achieved survival, still
short of the oracle-cheat ceiling (99.54%, using TRUE regime labels no real
method may see). RESULTS_PHASE2.md's fair-test rerun found the same shape
at n=45,000 (93.33% -> 96.11%). Two explanations for the remaining gap:
(a) the hard partition itself -- a year is either "in" a component's fit
or entirely "out", discarding real information near the cutoff and
sensitive to margin/min_stress_years/max_fit_quantile tuning -- or (b) the
gap is inherent to not knowing the true regime label at all, and a better
classifier mechanics won't move it much.

regime_mixture.fit_regime_mixture_soft tests this directly: same
GaussianMixture regime-frequency estimate, but each component's spatial
kernel is fit using EVERY year, weighted by that year's own posterior
P(systemic) instead of a hard yes/no split. If soft closes most of the
gap to 99.54%, explanation (a) dominates; if it barely moves, (b) does.

Mirrors phase1_sweep.py's structure exactly (same historical-years grid,
same seeds) so the two are directly comparable side by side.
"""

import json

import numpy as np

from exposures import build_book
from dgp_simulator import sample_true_losses
import capital_calc as cc
import regime_mixture as rm
from phase1_run import (N_PROPERTIES, BOOK_SEED, ORACLE_YEARS, ORACLE_SEED,
                         TARGET_SURVIVAL, N_SCENARIOS, run_experiment)

HISTORICAL_YEARS_GRID = [60, 120, 250, 500]
SEEDS_PER_SIZE = 3
SEED_BASE = 1000  # same as phase1_sweep.py -- identical historical draws,
                   # so the two sweeps are paired, not just averaged


def main():
    book = build_book(N_PROPERTIES, seed=BOOK_SEED)
    oracle = sample_true_losses(book, ORACLE_YEARS, seed=ORACLE_SEED)
    oracle_total = oracle["losses"].sum(axis=1)
    oracle_true_capital = cc.required_capital(oracle_total, TARGET_SURVIVAL)
    print(f"oracle ground truth ({ORACLE_YEARS} years): true capital @ "
          f"{TARGET_SURVIVAL:.1%} = ${oracle_true_capital:,.0f}\n")

    sweep = {}
    for n_years in HISTORICAL_YEARS_GRID:
        per_method_survival = {}
        per_method_gap = {}
        p_hat_vals = []
        n_systemic_vals = []
        for s in range(SEEDS_PER_SIZE):
            seed = SEED_BASE + n_years * 100 + s
            result = run_experiment(book, oracle_total, oracle_true_capital,
                                     n_years, seed, verbose=False,
                                     method4_fit_fn=rm.fit_regime_mixture_soft)
            n_systemic_vals.append(result["n_true_systemic"])
            if result["fit4_p_hat"] is not None:
                p_hat_vals.append(result["fit4_p_hat"])
            for name, row in result["table"].items():
                per_method_survival.setdefault(name, []).append(
                    row["achieved_survival_probability"])
                per_method_gap.setdefault(name, []).append(
                    row["capital_gap_vs_oracle_dollars"])

        summary = dict(
            n_years=n_years,
            mean_true_systemic_in_sample=float(np.mean(n_systemic_vals)),
            expected_true_systemic=n_years / 15.0,
            mean_fitted_p_hat=float(np.mean(p_hat_vals)) if p_hat_vals else None,
            methods={
                name: dict(
                    mean_achieved_survival=float(np.mean(per_method_survival[name])),
                    std_achieved_survival=float(np.std(per_method_survival[name])),
                    mean_capital_gap_dollars=float(np.mean(per_method_gap[name])),
                )
                for name in per_method_survival
            },
        )
        sweep[n_years] = summary

        print(f"n_years={n_years:4d}  mean true-systemic in sample="
              f"{summary['mean_true_systemic_in_sample']:.1f} "
              f"(expected {summary['expected_true_systemic']:.1f})"
              + (f"  mean fitted p_hat={summary['mean_fitted_p_hat']:.3f}"
                 if summary['mean_fitted_p_hat'] is not None else ""))
        for name, m in summary["methods"].items():
            print(f"    {name:24s} achieved_survival={m['mean_achieved_survival']:.4f} "
                  f"(+/-{m['std_achieved_survival']:.4f})  "
                  f"capital_gap=${m['mean_capital_gap_dollars']:>14,.0f}")
        print()

    with open("results_phase1_soft_sweep.json", "w") as f:
        json.dump(sweep, f, indent=2)
    print("wrote results_phase1_soft_sweep.json")


if __name__ == "__main__":
    main()
