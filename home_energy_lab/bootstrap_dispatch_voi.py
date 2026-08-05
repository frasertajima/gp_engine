#!/usr/bin/env python3
"""Phase 2: N-seed pooled comparison of the sequential-VoI skip/probe/drill
dispatch layer. See run_dispatch_voi.py's module docstring for the mechanism.

One fixed real dataset (the real 2017-2025 record, 3,286 days) -- 200 seeds
each redraw a fresh train/val/test split, mirroring `shm_lab`/
`hydro_reserve_lab`'s convention, not `grid_reserve_lab`/`climate_cat_lab`'s
synthetic-Monte-Carlo one.

Usage: python3 bootstrap_dispatch_voi.py --n-seeds 200
Writes results/bootstrap_dispatch_voi.json.
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from decision import ACTIONS, build_payoff_matrix_voi, oracle_value_2action, realized_value_with_probe  # noqa: E402
from voi import SIGMA_PROBE2_DEFAULT, bayes_action_voi  # noqa: E402

import stress_classifier as sc
from run_dispatch_voi import C_PROBE_DEFAULT, derive_dispatch_constants, probe_niche_fraction

CONDITIONS = ("svm", "gpc_mean", "gpc_full")


def run_one_seed(seed, X, y, V, c_probe, sigma_probe2):
    gpc, svm, X_train, y_train, X_test, y_test, ell, val_ap = sc.fit_classifier(X, y, seed=seed)
    conditions = sc.all_conditions(gpc, svm, X_test)
    y_test_int = y_test.astype(np.int64)
    oracle = oracle_value_2action(y_test_int, V)

    out = {"seed": seed, "ell": ell, "val_ap": val_ap, "n_test": len(y_test),
           "n_high_demand_test": int(y_test.sum()), "oracle_total_usd": float(oracle.sum())}
    for name, (p_now, mean, var) in conditions.items():
        actions, ev = bayes_action_voi(p_now, mean, var, V, sigma_probe2=sigma_probe2, c_probe=c_probe)
        realized = realized_value_with_probe(actions, y_test_int, V, c_probe)
        niche_frac = probe_niche_fraction(mean, var, V, sigma_probe2, c_probe) if name == "gpc_full" else 0.0
        out[name] = dict(
            realized_total_usd=float(realized.sum()),
            regret_total_usd=float((oracle - realized).sum()),
            action_distribution={a: int((actions == i).sum()) for i, a in enumerate(ACTIONS)},
            probe_niche_fraction=niche_frac,
        )
    return out


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
    ap.add_argument("--sigma-probe2", type=float, default=SIGMA_PROBE2_DEFAULT)
    ap.add_argument("--out", type=str, default="results/bootstrap_dispatch_voi.json")
    args = ap.parse_args()

    X, y, dates, thresh = sc.build_dataset()
    delta_kwh, c_drill, v_drill_gross = derive_dispatch_constants()
    V = build_payoff_matrix_voi(c_drill=c_drill, v_drill_gross=v_drill_gross)
    breakeven_p = c_drill / v_drill_gross
    print(f"n_days={len(y)}  base_rate={y.mean():.4f}  breakeven P(high-demand)={breakeven_p:.4f}")

    results = []
    t_start = time.time()
    for i in range(args.n_seeds):
        t0 = time.time()
        r = run_one_seed(i, X, y, V, args.c_probe, args.sigma_probe2)
        dt = time.time() - t0
        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (args.n_seeds - i - 1)
        print(f"[{i+1}/{args.n_seeds}] seed={i}  "
              f"svm=${r['svm']['realized_total_usd']:.2f}  "
              f"gpc_mean=${r['gpc_mean']['realized_total_usd']:.2f}  "
              f"gpc_full=${r['gpc_full']['realized_total_usd']:.2f}  "
              f"(probes={r['gpc_full']['action_distribution']['probe']})  "
              f"({dt:.2f}s, elapsed={elapsed:.0f}s, eta={eta:.0f}s)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "c_probe": args.c_probe, "sigma_probe2": args.sigma_probe2,
        "delta_kwh": delta_kwh, "c_drill": c_drill, "v_drill_gross": v_drill_gross,
        "breakeven_p_high_demand": breakeven_p,
        "payoff_matrix": V.tolist(), "actions": list(ACTIONS),
        "wall_time_s": time.time() - t_start, "runs": results,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f)
    print(f"wrote {args.out} ({time.time()-t_start:.0f}s total)")

    print(f"\n=== {args.n_seeds}-seed comparison (sequential-VoI skip/probe/drill dispatch) ===")
    totals = {c: np.array([r[c]["realized_total_usd"] for r in results]) for c in CONDITIONS}
    for c in CONDITIONS:
        print(f"{c:9s}: realized=${totals[c].mean():.3f}  std=${totals[c].std():.3f}")

    for a, b in [("gpc_full", "svm"), ("gpc_full", "gpc_mean"), ("gpc_mean", "svm")]:
        diff = totals[a] - totals[b]
        point, lo, hi = paired_bootstrap_ci(diff)
        print(f"{a} - {b}: ${point:.3f} [{lo:.3f},{hi:.3f}] (95% paired bootstrap CI)")

    print("\nMean action distribution per seed:")
    for c in CONDITIONS:
        counts = {a: np.mean([r[c]["action_distribution"][a] for r in results]) for a in ACTIONS}
        print(f"  {c:9s}: " + "  ".join(f"{a}={v:.1f}" for a, v in counts.items()))

    niche = np.array([r["gpc_full"]["probe_niche_fraction"] for r in results])
    print(f"\nProbe niche fraction (gpc_full): mean={niche.mean():.4f}  std={niche.std():.4f}")


if __name__ == "__main__":
    main()
