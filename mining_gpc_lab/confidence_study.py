#!/usr/bin/env python3
"""Multi-seed robustness study for the ore/waste confident-wrong question,
same methodology as `../place_gpc_lab/confidence_study.py` /
`../mnist_gpc_lab`'s M2 -- a single seed's test split has only 42 ore points
(~5.1% of 822), so single-seed confident-wrong counts (0-42 misses) are not
worth reading a percentage off of directly.

Each seed draws a FRESH stratified train/val/test split. The lengthscale is
FIXED (not re-gridded per seed) at the value `run_lab.py`'s seed-0 grid
selected on average precision -- same reasoning as the other two labs:
re-running a 5-point validation grid per seed is the expensive part, not the
fit itself.

Tracks both the confident-wrong-on-a-miss rate (errors with confidence>0.9,
same definition as the other two labs) AND average precision per seed --
see run_lab.py's docstring for why AP is needed here (P(ore) never crosses
0.5 at this class imbalance, so accuracy/recall alone can't discriminate
between models the way they could on the closer-to-balanced MNIST/place
data).

Usage: python3 confidence_study.py --n-seeds 200 [--ell 70.99]
Writes results/confidence_study_<feature_set>.json.
"""

import argparse
import json
import os
import sys
import time

import cupy as cp
import numpy as np
from sklearn.metrics import average_precision_score
from sklearn.svm import SVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datasets import load_split
from gp_classifier import LaplaceBinaryGPC
from run_lab import KERNEL_KIND, eval_binary, log_loss_binary


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

    def stats(p1):
        labels, conf, correct = eval_binary(y_test, p1)
        wrong = conf[correct == 0]
        return {
            "accuracy": float(correct.mean()),
            "average_precision": float(average_precision_score(y_test, p1)),
            "log_loss": log_loss_binary(y_test, p1),
            "n_ore_test": int(y_test.sum()),
            "mean_conf_correct": float(conf[correct == 1].mean()) if (correct == 1).any() else None,
            "mean_conf_wrong": float(wrong.mean()) if wrong.size else None,
            "n_wrong": int((correct == 0).sum()),
            "n_confidently_wrong_gt_0.9": int((wrong > 0.9).sum()),
            "frac_confidently_wrong_gt_0.9": float((wrong > 0.9).mean()) if wrong.size else None,
            "confidence": conf.tolist(),
            "correct": correct.tolist(),
        }

    return {"seed": seed, "gpc": stats(gpc_p1), "svm": stats(svm_p1)}


def pooled_confident_wrong(model, runs):
    """(total confidently-wrong) / (total wrong), pooled across seeds --
    the right unit of replication since test points within one seed share a
    fitted model and are correlated. Bootstrap CI resamples at the seed
    level (10,000 resamples)."""
    n_wrong = np.array([r[model]["n_wrong"] for r in runs])
    n_cw = np.array([r[model]["n_confidently_wrong_gt_0.9"] for r in runs])
    rng = np.random.default_rng(0)
    n = len(runs)
    boots = []
    for _ in range(10000):
        idx = rng.integers(0, n, n)
        num, den = n_cw[idx].sum(), n_wrong[idx].sum()
        if den > 0:
            boots.append(num / den)
    boots = np.array(boots)
    point = n_cw.sum() / n_wrong.sum()
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return point, lo, hi, int(n_wrong.sum()), int(n_cw.sum())


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
    out_path = args.out or f"results/confidence_study_{args.feature_set}.json"

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
              f"gpc_AP={r['gpc']['average_precision']:.3f} gpc_conf_wrong%={100*(r['gpc']['frac_confidently_wrong_gt_0.9'] or 0):.1f}  "
              f"svm_AP={r['svm']['average_precision']:.3f} svm_conf_wrong%={100*(r['svm']['frac_confidently_wrong_gt_0.9'] or 0):.1f}  "
              f"({dt:.2f}s, elapsed={elapsed:.0f}s, eta={eta:.0f}s)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "ell": args.ell, "feature_set": args.feature_set,
        "kernel_kind": KERNEL_KIND,
        "frac_train": args.frac_train, "frac_val": args.frac_val,
        "cutoff_quantile": args.cutoff_quantile,
        "seed_offset": args.seed_offset,
        "wall_time_s": time.time() - t_start,
        "runs": results,
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f)
    print(f"wrote {out_path} ({time.time()-t_start:.0f}s total)")

    gpc_ap = np.array([r["gpc"]["average_precision"] for r in results])
    svm_ap = np.array([r["svm"]["average_precision"] for r in results])
    print(f"\nAverage precision (mean over {args.n_seeds} seeds): "
          f"GPC {gpc_ap.mean():.3f} +/- {gpc_ap.std():.3f}   "
          f"SVM {svm_ap.mean():.3f} +/- {svm_ap.std():.3f}")

    gpc_point, gpc_lo, gpc_hi, gpc_tw, gpc_tcw = pooled_confident_wrong("gpc", results)
    svm_point, svm_lo, svm_hi, svm_tw, svm_tcw = pooled_confident_wrong("svm", results)
    print(f"Confidently-wrong-on-a-miss rate (pooled, 95% bootstrap CI):")
    print(f"  GPC: {100*gpc_point:.1f}% [{100*gpc_lo:.1f}%, {100*gpc_hi:.1f}%]  "
          f"({gpc_tcw}/{gpc_tw} misses were confidence>0.9)")
    print(f"  SVM: {100*svm_point:.1f}% [{100*svm_lo:.1f}%, {100*svm_hi:.1f}%]  "
          f"({svm_tcw}/{svm_tw} misses were confidence>0.9)")


if __name__ == "__main__":
    main()
