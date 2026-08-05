#!/usr/bin/env python3
"""Phase 2 robustness check: sweep the breakeven P(high-demand) across a grid
spanning below/above the real 25% base rate, holding c_drill fixed at its
derived value and varying v_drill_gross. Same pattern as the other four
VoI labs' own `cost_ratio_sweep_dispatch.py`.

Usage: python3 cost_ratio_sweep_dispatch.py --n-seeds 200
Writes results/cost_ratio_sweep_dispatch.json.
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from decision import ACTIONS, build_payoff_matrix_voi, oracle_value_2action, realized_value_with_probe  # noqa: E402
from voi import bayes_action_voi  # noqa: E402

import stress_classifier as sc
from run_dispatch_voi import C_PROBE_DEFAULT, SIGMA_PROBE2_LOCAL, derive_dispatch_constants

CONDITIONS = ("svm", "gpc_mean", "gpc_full")
# 0.0495 is this lab's own derived breakeven under the corrected payoff (M3);
# 0.3738 was the derived value under the old mining-shaped total-loss payoff and is
# kept on the grid so the two regimes can be compared directly.
BREAKEVEN_P_GRID = [0.0495, 0.10, 0.15, 0.20, 0.25, 0.30, 0.3738, 0.45,
                    0.55, 0.65, 0.75, 0.90]


def run_one_seed(seed, X, y_raw, c_drill, v_drill_residual, breakeven_grid, c_probe, sigma_probe2):
    gpc, svm, X_train, y_train, X_test, y_test, ell, val_ap = sc.fit_classifier(X, y_raw, seed=seed)
    conditions = sc.all_conditions(gpc, svm, X_test)
    y_test_int = y_test.astype(np.int64)

    per_sweep = []
    # The breakeven probability is set by the NET cost of a wasted pre-charge
    # (c_drill minus the value retained when the day turns out normal), not by the
    # gross charging cost -- see CODE_REVIEW.md M3. Inverting on the net cost keeps
    # each grid point's label ("breakeven_p") the probability it actually is.
    net_drill_cost = c_drill - v_drill_residual
    for breakeven_p in breakeven_grid:
        # Invert p* = net / (net + v_gross - c_drill) for v_gross. Using the
        # residual=0 shortcut (net/p*) here made drilling negative-EV in BOTH states
        # for every p* >= 0.10, collapsing the whole sweep to a never-drill $0.
        v_drill_gross = c_drill + net_drill_cost * (1.0 - breakeven_p) / breakeven_p
        V = build_payoff_matrix_voi(c_drill=c_drill, v_drill_gross=v_drill_gross,
                                    v_drill_residual=v_drill_residual)
        oracle = oracle_value_2action(y_test_int, V)
        row = {"breakeven_p": breakeven_p, "oracle_total": float(oracle.sum())}
        for name, (p_now, mean, var) in conditions.items():
            actions, ev = bayes_action_voi(p_now, mean, var, V, sigma_probe2=sigma_probe2, c_probe=c_probe)
            realized = realized_value_with_probe(actions, y_test_int, V, c_probe)
            row[name] = {
                "realized_total": float(realized.sum()),
                "action_distribution": {a: int((actions == i).sum()) for i, a in enumerate(ACTIONS)},
            }
        per_sweep.append(row)
    return {"seed": seed, "n_high_demand_test": int(y_test.sum()), "sweep": per_sweep}


def paired_bootstrap_ci(diffs, n_boot=10000, seed=0):
    rng = np.random.default_rng(seed)
    diffs = np.asarray(diffs)
    n = len(diffs)
    boots = np.array([diffs[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=200)
    ap.add_argument("--c-probe", type=float, default=C_PROBE_DEFAULT)
    ap.add_argument("--sigma-probe2", type=float, default=SIGMA_PROBE2_LOCAL)
    ap.add_argument("--out", type=str, default="results/cost_ratio_sweep_dispatch.json")
    args = ap.parse_args()

    X, y_raw, dates, thresh_full = sc.build_dataset()
    delta_kwh, c_drill, v_drill_gross_derived, v_drill_residual = derive_dispatch_constants()
    print(f"n_days={len(y_raw)}  c_drill=${c_drill:.4f}  residual=${v_drill_residual:.4f}  "
          f"net cost of a wasted pre-charge=${c_drill - v_drill_residual:.4f} (fixed across sweep)")

    results = []
    t_start = time.time()
    for i in range(args.n_seeds):
        t0 = time.time()
        r = run_one_seed(i, X, y_raw, c_drill, v_drill_residual, BREAKEVEN_P_GRID,
                         args.c_probe, args.sigma_probe2)
        dt = time.time() - t0
        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (args.n_seeds - i - 1)
        mid = r["sweep"][len(BREAKEVEN_P_GRID) // 2]
        print(f"[{i+1}/{args.n_seeds}] seed={i}  "
              f"(breakeven_p={mid['breakeven_p']}: svm=${mid['svm']['realized_total']:.2f} "
              f"gpc_full=${mid['gpc_full']['realized_total']:.2f})  "
              f"({dt:.2f}s, elapsed={elapsed:.0f}s, eta={eta:.0f}s)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "c_probe": args.c_probe, "sigma_probe2": args.sigma_probe2,
        "c_drill": c_drill, "delta_kwh": delta_kwh, "breakeven_p_grid": BREAKEVEN_P_GRID,
        "actions": list(ACTIONS), "wall_time_s": time.time() - t_start,
        "runs": results,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f)
    print(f"wrote {args.out} ({time.time()-t_start:.0f}s total)")

    print(f"\n=== Breakeven-probability sweep, {args.n_seeds} seeds ===")
    print(f"{'breakeven_p':>12}  {'svm':>10}  {'mean':>10}  {'full':>10}  "
          f"{'full-svm':>22}  {'full-mean':>22}")
    for gi, breakeven_p in enumerate(BREAKEVEN_P_GRID):
        totals = {c: np.array([r["sweep"][gi][c]["realized_total"] for r in results]) for c in CONDITIONS}
        d1 = totals["gpc_full"] - totals["svm"]
        d2 = totals["gpc_full"] - totals["gpc_mean"]
        p1, l1, h1 = paired_bootstrap_ci(d1)
        p2, l2, h2 = paired_bootstrap_ci(d2)
        print(f"{breakeven_p:12.4f}  ${totals['svm'].mean():8.3f}  ${totals['gpc_mean'].mean():8.3f}  "
              f"${totals['gpc_full'].mean():8.3f}  ${p1:6.3f} [{l1:6.3f},{h1:6.3f}]  "
              f"${p2:6.3f} [{l2:6.3f},{h2:6.3f}]")


if __name__ == "__main__":
    main()
