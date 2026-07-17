#!/usr/bin/env python3
"""Does Phase 4's pathfinder ARD move the Phase 2 economic result?

Phase 2's ranked drilling-campaign economics (`economic_layer.py`) only ever
ran on the spatial-only feature set (d=2). Phase 4 fit ARD lengthscales on
the spatial+pathfinder set (d=8) and showed it roughly doubles average
precision for both GPC and SVM -- but AP isn't dollars. This script reuses
`economic_layer.py`'s exact top-k campaign model (unchanged constants:
$1M/target, $50M/HG discovery, same k_econ grid) with GPC-ARD-ranked and
SVM-ranked (standardized, pathfinder_ard.py's fitted gamma) spatial+
pathfinder candidates, using the ARD lengthscales `pathfinder_ard.py` already
fit (loaded from results/pathfinder_ard.json, not refit here -- the
expensive part is the 360-eval Nelder-Mead search, already done).

Usage: python3 economic_layer_pathfinder.py --n-seeds 200
Writes results/economic_layer_pathfinder.json.
"""

import argparse
import json
import os
import sys
import time

import cupy as cp
import numpy as np
from sklearn.svm import SVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datasets import load_split
from economic_layer import C_DRILL, K_ECON, K_HEADLINE, V_DISCOVERY, top_k_campaign
from gp_classifier import LaplaceBinaryGPC
from run_lab import KERNEL_KIND


def run_one_seed(seed, ell_ard, sigma_f, svm_gamma, frac_train, frac_val, cutoff_quantile):
    (X_train, y_train), _, (X_test, y_test) = load_split(
        feature_set="spatial_pathfinder", frac_train=frac_train, frac_val=frac_val,
        seed=seed, cutoff_quantile=cutoff_quantile)

    gpc = LaplaceBinaryGPC(ell=ell_ard, sigma_f=sigma_f, kind=KERNEL_KIND)
    gpc.fit(X_train, y_train)
    _, _, p1 = gpc.predict(X_test)
    gpc_p1 = cp.asnumpy(p1)

    mu, sigma = X_train.mean(axis=0), X_train.std(axis=0)
    sigma[sigma < 1e-12] = 1.0
    Xtr_s, Xte_s = (X_train - mu) / sigma, (X_test - mu) / sigma
    svm = SVC(kernel="rbf", gamma=svm_gamma, probability=True, random_state=seed)
    svm.fit(Xtr_s, y_train)
    svm_probs = svm.predict_proba(Xte_s)
    p1_col = list(svm.classes_).index(1)
    svm_p1 = svm_probs[:, p1_col]

    rng = np.random.default_rng(seed + 1_000_000)
    gpc_found, gpc_net = top_k_campaign(gpc_p1, y_test, K_ECON)
    svm_found, svm_net = top_k_campaign(svm_p1, y_test, K_ECON)
    rand_found, rand_net = top_k_campaign(None, y_test, K_ECON, rng=rng)

    return {
        "seed": seed, "n_test": len(y_test), "n_ore_test": int(y_test.sum()),
        "gpc_ard": {"found": gpc_found.tolist(), "net": gpc_net.tolist()},
        "svm": {"found": svm_found.tolist(), "net": svm_net.tolist()},
        "random": {"found": rand_found.tolist(), "net": rand_net.tolist()},
    }


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
    ap.add_argument("--ard-results", type=str, default="results/pathfinder_ard.json")
    ap.add_argument("--frac-train", type=float, default=0.6)
    ap.add_argument("--frac-val", type=float, default=0.2)
    ap.add_argument("--cutoff-quantile", type=float, default=0.95)
    ap.add_argument("--out", type=str, default="results/economic_layer_pathfinder.json")
    args = ap.parse_args()

    ard = json.load(open(args.ard_results))
    ell_ard = np.array(ard["ell_ard"])
    sigma_f = ard["sigma_f"]
    svm_gamma = ard["svm_gamma"]
    print(f"Loaded ARD fit from {args.ard_results}: ell={np.round(ell_ard, 2).tolist()}  "
          f"sigma_f={sigma_f:.3f}  svm_gamma={svm_gamma:.5f}")

    k_idx = int(np.searchsorted(K_ECON, K_HEADLINE))
    assert K_ECON[k_idx] == K_HEADLINE

    results = []
    t_start = time.time()
    for i in range(args.n_seeds):
        t0 = time.time()
        r = run_one_seed(i, ell_ard, sigma_f, svm_gamma, args.frac_train,
                          args.frac_val, args.cutoff_quantile)
        dt = time.time() - t0
        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (args.n_seeds - i - 1)
        print(f"[{i+1}/{args.n_seeds}] seed={i}  "
              f"gpc_ard_net@50=${r['gpc_ard']['net'][k_idx]:.0f}M  "
              f"svm_net@50=${r['svm']['net'][k_idx]:.0f}M  "
              f"({dt:.2f}s, elapsed={elapsed:.0f}s, eta={eta:.0f}s)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "kernel_kind": KERNEL_KIND,
        "ell_ard": ell_ard.tolist(), "sigma_f": sigma_f, "svm_gamma": svm_gamma,
        "frac_train": args.frac_train, "frac_val": args.frac_val,
        "cutoff_quantile": args.cutoff_quantile,
        "c_drill_musd": C_DRILL, "v_discovery_musd": V_DISCOVERY,
        "k_econ": K_ECON.tolist(), "k_headline": K_HEADLINE,
        "wall_time_s": time.time() - t_start,
        "runs": results,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f)
    print(f"wrote {args.out} ({time.time()-t_start:.0f}s total)")

    gpc_net50 = np.array([r["gpc_ard"]["net"][k_idx] for r in results])
    svm_net50 = np.array([r["svm"]["net"][k_idx] for r in results])
    rand_net50 = np.array([r["random"]["net"][k_idx] for r in results])
    gpc_found50 = np.array([r["gpc_ard"]["found"][k_idx] for r in results])
    svm_found50 = np.array([r["svm"]["found"][k_idx] for r in results])

    print(f"\n=== k={K_HEADLINE} campaign, spatial+pathfinder ARD, {args.n_seeds} seeds ===")
    print(f"HG found:  GPC-ARD {gpc_found50.mean():.1f} +/- {gpc_found50.std():.1f}   "
          f"SVM {svm_found50.mean():.1f} +/- {svm_found50.std():.1f}")
    print(f"Net value: GPC-ARD ${gpc_net50.mean():.0f}M +/- {gpc_net50.std():.0f}M   "
          f"SVM ${svm_net50.mean():.0f}M +/- {svm_net50.std():.0f}M   "
          f"Random ${rand_net50.mean():.0f}M +/- {rand_net50.std():.0f}M")

    diff_point, diff_lo, diff_hi = paired_bootstrap_ci(gpc_net50 - svm_net50)
    print(f"GPC-ARD - SVM net advantage @ k={K_HEADLINE}: "
          f"${diff_point:.0f}M [${diff_lo:.0f}M, ${diff_hi:.0f}M] (95% paired bootstrap CI)")

    print(f"\nCompare against Phase 2's spatial-only result (200 seeds):")
    print(f"  GPC $565M +/- 122M   SVM $142M +/- 138M   Random $65M +/- 75M")
    print(f"  GPC - SVM advantage: $423M [$396M, $450M]")


if __name__ == "__main__":
    main()
