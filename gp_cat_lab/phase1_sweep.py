"""Phase 1 follow-up: does more historical data close the gap, and does it
close it EQUALLY for all four methods?

The single-trial run (phase1_run.py, 60 historical years) found all four
methods landing at nearly the same, badly under-reserved achieved survival
probability (~93.3% vs. a 99.5% target) -- surprising, since methods 1-3
have no regime structure at all while method 4 does. The suspected reason:
with only ~4 systemic years expected in 60 (true p_systemic=1/15) and only
2 actually drawn in that one historical sample, EVERY method's fitted
marginal severity is starved of systemic-year examples, and method 4's own
regime-frequency estimate (which literally counts stress-classified years)
inherits that same small-sample noise.

This script separates two different explanations by re-running the whole
four-method ladder across several historical sample sizes (each averaged
over several historical-draw seeds, to average out small-sample noise) and
watching whether the achieved-survival gap: (a) shrinks toward the 99.5%
target as historical years grow, for ALL methods equally (a pure data
problem, not a structural one) -- or (b) shrinks for method 4 but plateaus
for methods 1-3 (a genuine structural ceiling: methods 1-3 cannot represent
a regime at all, so no amount of data fixes them; method 4 can, and more
data should let it).
"""

import json

import numpy as np

from exposures import build_book
from dgp_simulator import sample_true_losses
import capital_calc as cc
from phase1_run import (N_PROPERTIES, BOOK_SEED, ORACLE_YEARS, ORACLE_SEED,
                         TARGET_SURVIVAL, N_SCENARIOS, run_experiment)

HISTORICAL_YEARS_GRID = [60, 120, 250, 500]
SEEDS_PER_SIZE = 3
SEED_BASE = 1000  # offset from phase1_run.py's HISTORICAL_SEED=100, no collision


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
                                     n_years, seed, verbose=False)
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

    with open("results_phase1_sweep.json", "w") as f:
        json.dump(sweep, f, indent=2)
    print("wrote results_phase1_sweep.json")


if __name__ == "__main__":
    main()
