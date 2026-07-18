#!/usr/bin/env python3
"""Phase 2: single-seed sequential value-of-information run, porphyry Cu.

Skips straight to `bayesian_decision_lab`'s sequential value-of-information
framework rather than rebuilding a ranked-top-k economic layer from
scratch (Fraser's explicit direction, 2026-07-18) -- that framework is now
a genuinely shared, dataset-agnostic asset (`../decision.py`, `../voi.py`,
moved there from `bayesian_decision_lab/` specifically so it could be reused
here without copy-pasting). See `bayesian_decision_lab/LAB_PLAN.md` for the
full mechanism (Probe pays off via a local Gaussian-conjugate posterior
update, not a static side-bet) and its structural guarantee (SVM and
"GPC, mean-only" have var=0 by construction, so Probe is provably never
their Bayes-optimal action).

**Porphyry-specific payoff constants, derived not reused from gold** (per
LAB_PLAN.md's own "What's new" section -- `mining_mpdok`'s $1M/$50M gold
constants were never meant to travel to a different commodity unchanged):
porphyry Cu targets are larger, deeper, bulk-tonnage systems -- bigger holes
(illustratively $2M/target, vs. gold's $1M) and proportionally larger
discovery value (illustratively $150M gross, vs. gold's $50M), keeping the
same *relative* structure (Probe:Drill cost ratio 0.05, Probe:Drill gross-
value ratio 0.1) since neither commodity's absolute numbers were rigorously
sourced to begin with -- only the direction (porphyry systems cost more per
hole and are worth more per confirmed discovery) is a real, defensible
difference from gold. Verified before use: `has_probe_niche` confirms Probe
still has a genuine P(ore) niche (0.0067-0.0141) under these constants, not
assumed.

Usage: python3 run_voi.py [--seed 0] [--c-probe 0.1] [--c-drill 2.0] [--v-drill-gross 150.0]
Writes results/voi_seed<seed>.json.
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # decision.py, voi.py, gp_classifier.py live in gp_engine/

from decision import (ACTIONS, build_payoff_matrix_voi, has_probe_niche,
                     oracle_value_2action, realized_value_with_probe)
from models import all_conditions, fit_models
from voi import SIGMA_PROBE2_DEFAULT, bayes_action_voi

C_PROBE_DEFAULT = 0.1     # $M -- vs. gold's 0.05; a regional porphyry follow-up sample program
V_PROBE_GROSS_DEFAULT = 15.0   # $M -- keeps Probe:Drill gross-value ratio at 0.1, same as gold
C_DRILL_DEFAULT = 2.0     # $M -- deeper/larger-diameter holes than a gold vein target
V_DRILL_GROSS_DEFAULT = 150.0  # $M -- bulk-tonnage porphyry systems are worth proportionally more


def run(seed=0, c_probe=C_PROBE_DEFAULT, v_probe_gross=V_PROBE_GROSS_DEFAULT,
        c_drill=C_DRILL_DEFAULT, v_drill_gross=V_DRILL_GROSS_DEFAULT,
        sigma_probe2=SIGMA_PROBE2_DEFAULT):
    assert has_probe_niche(c_probe, v_probe_gross, c_drill, v_drill_gross), \
        "payoff matrix has no Probe niche -- check the constants above"
    V = build_payoff_matrix_voi(c_drill=c_drill, v_drill_gross=v_drill_gross)

    gpc, svm, X_train, y_train, X_test, y_test = fit_models(seed=seed)
    conditions = all_conditions(gpc, svm, X_test)
    x_km, y_km = X_test[:, 0], X_test[:, 1]
    oracle = oracle_value_2action(y_test, V)

    results = {}
    for name, (p_now, mean, var) in conditions.items():
        actions, ev = bayes_action_voi(p_now, mean, var, V, sigma_probe2=sigma_probe2, c_probe=c_probe)
        realized = realized_value_with_probe(actions, y_test, V, c_probe)
        dist = {a: int((actions == i).sum()) for i, a in enumerate(ACTIONS)}
        regret = oracle - realized
        results[name] = {
            "prob": p_now.tolist(), "mean": mean.tolist(), "var": var.tolist(),
            "action": actions.tolist(), "action_names": [ACTIONS[a] for a in actions],
            "action_distribution": dist,
            "realized_total": float(realized.sum()),
            "regret_total": float(regret.sum()),
            "realized_per_site": realized.tolist(),
        }
        print(f"[{name:9s}] actions={dist}  realized=${realized.sum():.2f}M  "
              f"regret=${regret.sum():.2f}M")

    out = {
        "seed": seed, "c_probe": c_probe, "v_probe_gross": v_probe_gross,
        "c_drill": c_drill, "v_drill_gross": v_drill_gross, "sigma_probe2": sigma_probe2,
        "n_train": len(y_train), "n_test": len(y_test), "n_ore_test": int(y_test.sum()),
        "payoff_matrix": V.tolist(), "actions": list(ACTIONS),
        "x_km": x_km.tolist(), "y_km": y_km.tolist(), "label": y_test.tolist(),
        "oracle_per_site": oracle.tolist(), "oracle_total": float(oracle.sum()),
        "conditions": results,
    }
    os.makedirs("results", exist_ok=True)
    out_path = f"results/voi_seed{seed}.json"
    with open(out_path, "w") as f:
        json.dump(out, f)
    print(f"wrote {out_path}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--c-probe", type=float, default=C_PROBE_DEFAULT)
    ap.add_argument("--v-probe-gross", type=float, default=V_PROBE_GROSS_DEFAULT)
    ap.add_argument("--c-drill", type=float, default=C_DRILL_DEFAULT)
    ap.add_argument("--v-drill-gross", type=float, default=V_DRILL_GROSS_DEFAULT)
    ap.add_argument("--sigma-probe2", type=float, default=SIGMA_PROBE2_DEFAULT)
    args = ap.parse_args()
    run(args.seed, args.c_probe, args.v_probe_gross, args.c_drill, args.v_drill_gross, args.sigma_probe2)
