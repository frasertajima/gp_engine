#!/usr/bin/env python3
"""Phase 2: dollar-denominated version of the Phase 1 confident-wrong finding.

`mining_mpdok/05_thesis.ipynb` (fig17/fig18) already built an economic model
for this exact question -- FRK vs. MPDOK ranked drilling campaigns -- and it
is a **ranked top-k campaign**, not a fixed-threshold confusion matrix:
drill the k highest-ranked targets, pay $1M/target regardless of outcome,
collect $50M NPV per confirmed high-grade (HG) discovery. This sidesteps
Phase 1's finding that a 0.5 probability threshold is degenerate at ~5.1%
ore prevalence (see run_lab.py's docstring) -- a ranked campaign never needs
a threshold at all, it only needs an ordering, which both GPC's and SVM's
P(ore) provide regardless of where 0.5 falls.

This script applies mining_mpdok's own economic constants unchanged
(C_DRILL=$1M/target, V_DISCOVERY=$50M/HG discovery, same k_econ grid, same
k=50 headline campaign size as fig18) to GPC-ranked vs. SVM-ranked test-set
candidate lists, pooled over many fresh seeds with a paired bootstrap CI on
the net-value gap (paired per seed, since both models rank the *same*
test set each seed -- pairing removes the seed-to-seed variance in which
points happen to be test-set ore, leaving only the ranking-quality
difference).

Usage: python3 economic_layer.py --n-seeds 200 [--ell 70.99]
Writes results/economic_layer_<feature_set>.json.
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
from gp_classifier import LaplaceBinaryGPC
from run_lab import KERNEL_KIND

# Unchanged from mining_mpdok/05_thesis.ipynb -- same $ constants, so this
# lab's numbers are directly comparable to fig17/fig18's FRK-vs-MPDOK ones.
C_DRILL = 1.0        # $M per target drilled, regardless of outcome
V_DISCOVERY = 50.0   # $M NPV per confirmed high-grade (ore) discovery
K_ECON = np.array([5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 125, 150, 200])
K_HEADLINE = 50       # matches 05_thesis.ipynb's own headline campaign size


def top_k_campaign(p1, y_true, k_vals, rng=None):
    """found(k) = true-ore count among the top-k by p1 (descending);
    net(k) = found(k) * V_DISCOVERY - k * C_DRILL. If rng is given, p1 is
    replaced by a random permutation first (random-targeting baseline)."""
    n = len(y_true)
    if rng is not None:
        order = rng.permutation(n)
    else:
        order = np.argsort(-p1)
    y_sorted = y_true[order]
    found = np.array([float(y_sorted[:k].sum()) for k in k_vals])
    net = found * V_DISCOVERY - k_vals * C_DRILL
    return found, net


def run_one_seed(seed, ell, feature_set, frac_train, frac_val, cutoff_quantile):
    (X_train, y_train), _, (X_test, y_test) = load_split(
        feature_set=feature_set, frac_train=frac_train, frac_val=frac_val,
        seed=seed, cutoff_quantile=cutoff_quantile)

    gpc = LaplaceBinaryGPC(ell=ell, sigma_f=1.0, kind=KERNEL_KIND)
    gpc.fit(X_train, y_train)
    _, _, p1 = gpc.predict(X_test)
    gpc_p1 = cp.asnumpy(p1)

    gamma = 1.0 / (2.0 * ell ** 2)
    svm = SVC(kernel="rbf", gamma=gamma, probability=True, random_state=seed)
    svm.fit(X_train, y_train)
    svm_probs = svm.predict_proba(X_test)
    p1_col = list(svm.classes_).index(1)
    svm_p1 = svm_probs[:, p1_col]

    rng = np.random.default_rng(seed + 1_000_000)  # separate stream from split/model seeds
    gpc_found, gpc_net = top_k_campaign(gpc_p1, y_test, K_ECON)
    svm_found, svm_net = top_k_campaign(svm_p1, y_test, K_ECON)
    rand_found, rand_net = top_k_campaign(None, y_test, K_ECON, rng=rng)

    return {
        "seed": seed, "n_test": len(y_test), "n_ore_test": int(y_test.sum()),
        "gpc": {"found": gpc_found.tolist(), "net": gpc_net.tolist()},
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
    ap.add_argument("--ell", type=float, default=70.99)
    ap.add_argument("--feature-set", type=str, default="spatial",
                     choices=["spatial", "spatial_pathfinder"])
    ap.add_argument("--frac-train", type=float, default=0.6)
    ap.add_argument("--frac-val", type=float, default=0.2)
    ap.add_argument("--cutoff-quantile", type=float, default=0.95)
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()
    out_path = args.out or f"results/economic_layer_{args.feature_set}.json"

    k_idx = int(np.searchsorted(K_ECON, K_HEADLINE))
    assert K_ECON[k_idx] == K_HEADLINE

    results = []
    t_start = time.time()
    for i in range(args.n_seeds):
        seed = args.seed_offset + i
        t0 = time.time()
        r = run_one_seed(seed, args.ell, args.feature_set, args.frac_train,
                          args.frac_val, args.cutoff_quantile)
        dt = time.time() - t0
        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (args.n_seeds - i - 1)
        print(f"[{i+1}/{args.n_seeds}] seed={seed}  "
              f"gpc_net@50=${r['gpc']['net'][k_idx]:.0f}M  "
              f"svm_net@50=${r['svm']['net'][k_idx]:.0f}M  "
              f"({dt:.2f}s, elapsed={elapsed:.0f}s, eta={eta:.0f}s)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "ell": args.ell, "feature_set": args.feature_set,
        "kernel_kind": KERNEL_KIND,
        "frac_train": args.frac_train, "frac_val": args.frac_val,
        "cutoff_quantile": args.cutoff_quantile,
        "seed_offset": args.seed_offset,
        "c_drill_musd": C_DRILL, "v_discovery_musd": V_DISCOVERY,
        "k_econ": K_ECON.tolist(), "k_headline": K_HEADLINE,
        "wall_time_s": time.time() - t_start,
        "runs": results,
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f)
    print(f"wrote {out_path} ({time.time()-t_start:.0f}s total)")

    gpc_net50 = np.array([r["gpc"]["net"][k_idx] for r in results])
    svm_net50 = np.array([r["svm"]["net"][k_idx] for r in results])
    rand_net50 = np.array([r["random"]["net"][k_idx] for r in results])
    gpc_found50 = np.array([r["gpc"]["found"][k_idx] for r in results])
    svm_found50 = np.array([r["svm"]["found"][k_idx] for r in results])

    print(f"\n=== k={K_HEADLINE} campaign, {args.n_seeds} seeds, "
          f"${C_DRILL}M/target, ${V_DISCOVERY}M/HG discovery ===")
    print(f"HG found:  GPC {gpc_found50.mean():.1f} +/- {gpc_found50.std():.1f}   "
          f"SVM {svm_found50.mean():.1f} +/- {svm_found50.std():.1f}")
    print(f"Net value: GPC ${gpc_net50.mean():.0f}M +/- {gpc_net50.std():.0f}M   "
          f"SVM ${svm_net50.mean():.0f}M +/- {svm_net50.std():.0f}M   "
          f"Random ${rand_net50.mean():.0f}M +/- {rand_net50.std():.0f}M")

    diff_point, diff_lo, diff_hi = paired_bootstrap_ci(gpc_net50 - svm_net50)
    print(f"GPC - SVM net advantage @ k={K_HEADLINE}: "
          f"${diff_point:.0f}M [${diff_lo:.0f}M, ${diff_hi:.0f}M] (95% paired bootstrap CI)")

    print(f"\nNet value across campaign sizes (mean over {args.n_seeds} seeds):")
    print(f"{'k':>5}  {'GPC $M':>10}  {'SVM $M':>10}  {'Random $M':>10}  {'GPC-SVM $M':>12}")
    for i, k in enumerate(K_ECON):
        gpc_k = np.array([r["gpc"]["net"][i] for r in results])
        svm_k = np.array([r["svm"]["net"][i] for r in results])
        rand_k = np.array([r["random"]["net"][i] for r in results])
        print(f"{k:5d}  {gpc_k.mean():10.0f}  {svm_k.mean():10.0f}  {rand_k.mean():10.0f}  "
              f"{(gpc_k - svm_k).mean():12.0f}")


if __name__ == "__main__":
    main()
