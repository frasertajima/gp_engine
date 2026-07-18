#!/usr/bin/env python3
"""Phase 2: 200-seed pooled comparison of the sequential value-of-information
framework, porphyry Cu. See run_voi.py and `../voi.py`'s docstrings.

Usage: python3 bootstrap_voi.py --n-seeds 200
Writes results/bootstrap_voi.json.
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # decision.py, voi.py, gp_classifier.py live in gp_engine/

from decision import (ACTIONS, build_payoff_matrix_voi, no_probe_counterfactual,
                     oracle_value_2action, realized_value_with_probe)
from models import all_conditions, fit_models
from run_voi import (C_DRILL_DEFAULT, C_PROBE_DEFAULT, V_DRILL_GROSS_DEFAULT,
                     V_PROBE_GROSS_DEFAULT)
from voi import SIGMA_PROBE2_DEFAULT, bayes_action_voi

CONDITIONS = ("svm", "gpc_mean", "gpc_full")


def run_one_seed(seed, V, c_probe, sigma_probe2):
    gpc, svm, X_train, y_train, X_test, y_test = fit_models(seed=seed)
    conditions = all_conditions(gpc, svm, X_test)
    oracle = oracle_value_2action(y_test, V)
    skip_idx, probe_idx, drill_idx = (ACTIONS.index("skip"), ACTIONS.index("probe"),
                                       ACTIONS.index("drill"))

    out = {"seed": seed, "n_test": len(y_test), "n_ore_test": int(y_test.sum()),
           "oracle_total": float(oracle.sum())}
    for name, (p_now, mean, var) in conditions.items():
        actions, ev = bayes_action_voi(p_now, mean, var, V, sigma_probe2=sigma_probe2, c_probe=c_probe)
        realized = realized_value_with_probe(actions, y_test, V, c_probe)
        out[name] = {
            "realized_total": float(realized.sum()),
            "regret_total": float((oracle - realized).sum()),
            "action_distribution": {a: int((actions == i).sum()) for i, a in enumerate(ACTIONS)},
        }
        if name == "gpc_full":
            # Cost/benefit accounting for the Probe option -- same
            # convention bayesian_decision_lab established.
            cf_actions, cf_ev = no_probe_counterfactual(p_now, V)
            cf_realized = np.where(cf_actions == drill_idx, V[drill_idx, y_test], V[skip_idx, y_test])

            probed = actions == probe_idx
            n_probed_ore = int((probed & (y_test == 1)).sum())
            n_probed_waste = int((probed & (y_test == 0)).sum())
            drilled_directly_value = float(V[drill_idx, y_test[probed]].sum())
            actual_probe_value = float(realized[probed].sum())

            out[name]["counterfactual_no_probe_total"] = float(cf_realized.sum())
            out[name]["probe_value_added"] = float(realized.sum() - cf_realized.sum())
            out[name]["n_probed_ore"] = n_probed_ore
            out[name]["n_probed_waste"] = n_probed_waste
            out[name]["probe_cost_total"] = float(probed.sum()) * c_probe
            out[name]["probed_actual_value"] = actual_probe_value
            out[name]["probed_if_drilled_directly"] = drilled_directly_value
            out[name]["probed_if_skipped_directly"] = 0.0
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
    ap.add_argument("--v-probe-gross", type=float, default=V_PROBE_GROSS_DEFAULT)
    ap.add_argument("--c-drill", type=float, default=C_DRILL_DEFAULT)
    ap.add_argument("--v-drill-gross", type=float, default=V_DRILL_GROSS_DEFAULT)
    ap.add_argument("--sigma-probe2", type=float, default=SIGMA_PROBE2_DEFAULT)
    ap.add_argument("--out", type=str, default="results/bootstrap_voi.json")
    args = ap.parse_args()

    V = build_payoff_matrix_voi(c_drill=args.c_drill, v_drill_gross=args.v_drill_gross)
    results = []
    t_start = time.time()
    for i in range(args.n_seeds):
        t0 = time.time()
        r = run_one_seed(i, V, args.c_probe, args.sigma_probe2)
        dt = time.time() - t0
        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (args.n_seeds - i - 1)
        print(f"[{i+1}/{args.n_seeds}] seed={i}  "
              f"svm=${r['svm']['realized_total']:.0f}M  "
              f"gpc_mean=${r['gpc_mean']['realized_total']:.0f}M  "
              f"gpc_full=${r['gpc_full']['realized_total']:.0f}M  "
              f"(probes: {r['gpc_full']['action_distribution']['probe']})  "
              f"({dt:.2f}s, elapsed={elapsed:.0f}s, eta={eta:.0f}s)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "c_probe": args.c_probe, "v_probe_gross": args.v_probe_gross,
        "c_drill": args.c_drill, "v_drill_gross": args.v_drill_gross, "sigma_probe2": args.sigma_probe2,
        "payoff_matrix": V.tolist(), "actions": list(ACTIONS),
        "wall_time_s": time.time() - t_start,
        "runs": results,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f)
    print(f"wrote {args.out} ({time.time()-t_start:.0f}s total)")

    totals = {c: np.array([r[c]["realized_total"] for r in results]) for c in CONDITIONS}
    print(f"\n=== {args.n_seeds}-seed comparison (sequential VoI, porphyry Cu) ===")
    for c in CONDITIONS:
        print(f"{c:9s}: mean=${totals[c].mean():.1f}M  std=${totals[c].std():.1f}M")

    for a, b in [("gpc_full", "svm"), ("gpc_full", "gpc_mean"), ("gpc_mean", "svm")]:
        diff = totals[a] - totals[b]
        point, lo, hi = paired_bootstrap_ci(diff)
        print(f"{a} - {b}: ${point:.1f}M [${lo:.1f}M, ${hi:.1f}M] (95% paired bootstrap CI)")

    print("\nMean action distribution per seed:")
    for c in CONDITIONS:
        counts = {a: np.mean([r[c]["action_distribution"][a] for r in results]) for a in ACTIONS}
        print(f"  {c:9s}: " + "  ".join(f"{a}={v:.1f}" for a, v in counts.items()))

    print(f"\n=== Probe cost/benefit accounting, GPC-full-posterior only ({args.n_seeds} seeds) ===")
    added = np.array([r["gpc_full"]["probe_value_added"] for r in results])
    point, lo, hi = paired_bootstrap_ci(added)
    print(f"$ value added by having the Probe option (vs. same p_now, Skip/Drill only): "
          f"${point:.1f}M/seed [${lo:.1f}M, ${hi:.1f}M]")
    print(f"probe cost paid:            mean=${np.mean([r['gpc_full']['probe_cost_total'] for r in results]):.2f}M/seed")
    print(f"probed sites, true ore:     mean={np.mean([r['gpc_full']['n_probed_ore'] for r in results]):.1f}/seed")
    print(f"probed sites, true waste:   mean={np.mean([r['gpc_full']['n_probed_waste'] for r in results]):.1f}/seed")
    print(f"probed sites' actual value (probe-then-decide): "
          f"mean=${np.mean([r['gpc_full']['probed_actual_value'] for r in results]):.1f}M/seed")
    print(f"same sites if drilled directly (no confirmation): "
          f"mean=${np.mean([r['gpc_full']['probed_if_drilled_directly'] for r in results]):.1f}M/seed")
    print(f"same sites if skipped directly (no drilling at all): "
          f"mean=${np.mean([r['gpc_full']['probed_if_skipped_directly'] for r in results]):.1f}M/seed")


if __name__ == "__main__":
    main()
