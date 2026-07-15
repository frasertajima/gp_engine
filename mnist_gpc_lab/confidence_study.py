#!/usr/bin/env python3
"""Multi-seed robustness study for the "is GPC right about being right?"
finding from run_lab.py's 3-seed pilot (see LAB_PLAN.md's headline section).

Design: each seed draws a FRESH balanced train/test subsample (not just a
different RNG on the same data) -- this checks whether the confident-wrong
asymmetry survives across which specific images end up in train vs. test,
not just prediction noise on one fixed split. The lengthscale is FIXED (not
re-gridded per seed, unlike run_lab.py) since re-running a 5-point validation
grid 200x is the expensive part, not the fit itself -- ell=5.1 is the value
run_lab.py's grid selected on all 3 pilot seeds.

Statistics are computed PER SEED and only then aggregated across seeds --
test points within one seed share a common fitted model and are correlated,
so the seed (not the pooled test point) is the correct unit of replication
for a confidence interval on any cross-seed claim. Pooled points are used
only for the calibration-curve *shape* (finer bins need more raw data than
200 seeds' worth of per-seed statistics alone could resolve), with that
caveat stated explicitly wherever pooled data is plotted.

Usage: python3 confidence_study.py --n-seeds 200 [--ell 5.1]
Writes results/confidence_study.json (one file, not one per seed --
200 seeds of full confidence/correct arrays is small, ~3 MB total).
"""

import argparse
import json
import os
import sys
import time

import numpy as np
from sklearn.svm import SVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datasets import load_mnist_subset
from gp_classifier import OneVsRestLaplaceGPC


def run_one_seed(seed, ell, train_per_class, test_per_class, classes):
    (X_train, y_train), _, (X_test, y_test) = load_mnist_subset(
        n_train_per_class=train_per_class, n_val_per_class=1,
        n_test_per_class=test_per_class, seed=seed)

    gpc = OneVsRestLaplaceGPC(classes=classes, ell=ell, sigma_f=1.0)
    gpc.fit(X_train, y_train)
    labels, confidence, probs, _ = gpc.predict(X_test)
    import cupy as cp
    labels_np, confidence_np = cp.asnumpy(labels), cp.asnumpy(confidence)
    gpc_correct = (labels_np == y_test).astype(np.float64)
    gpc_conf = confidence_np

    gamma = 1.0 / (2.0 * ell ** 2)
    svm = SVC(kernel="rbf", gamma=gamma, probability=True, random_state=seed)
    svm.fit(X_train, y_train)
    svm_probs = svm.predict_proba(X_test)
    svm_labels = svm.classes_[np.argmax(svm_probs, axis=1)]
    svm_correct = (svm_labels == y_test).astype(np.float64)
    svm_conf = svm_probs.max(axis=1)

    def stats(conf, correct):
        wrong = conf[correct == 0]
        right = conf[correct == 1]
        return {
            "accuracy": float(correct.mean()),
            "mean_conf_correct": float(right.mean()) if right.size else None,
            "mean_conf_wrong": float(wrong.mean()) if wrong.size else None,
            "n_wrong": int((correct == 0).sum()),
            "n_confidently_wrong_gt_0.5": int((wrong > 0.5).sum()),
            "frac_confidently_wrong": float((wrong > 0.5).mean()) if wrong.size else None,
            "confidence": conf.tolist(),
            "correct": correct.tolist(),
        }

    return {
        "seed": seed,
        "gpc": stats(gpc_conf, gpc_correct),
        "svm": stats(svm_conf, svm_correct),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=200)
    ap.add_argument("--ell", type=float, default=5.1)
    ap.add_argument("--train-per-class", type=int, default=150)
    ap.add_argument("--test-per-class", type=int, default=100)
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--out", type=str, default="results/confidence_study.json")
    args = ap.parse_args()

    classes = list(range(10))
    results = []
    t_start = time.time()
    for i in range(args.n_seeds):
        seed = args.seed_offset + i
        t0 = time.time()
        r = run_one_seed(seed, args.ell, args.train_per_class, args.test_per_class, classes)
        dt = time.time() - t0
        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (args.n_seeds - i - 1)
        print(f"[{i+1}/{args.n_seeds}] seed={seed}  "
              f"gpc_acc={r['gpc']['accuracy']:.3f} gpc_conf_wrong%={100*(r['gpc']['frac_confidently_wrong'] or 0):.1f}  "
              f"svm_acc={r['svm']['accuracy']:.3f} svm_conf_wrong%={100*(r['svm']['frac_confidently_wrong'] or 0):.1f}  "
              f"({dt:.1f}s, elapsed={elapsed/60:.1f}min, eta={eta/60:.1f}min)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "ell": args.ell,
        "train_per_class": args.train_per_class, "test_per_class": args.test_per_class,
        "seed_offset": args.seed_offset,
        "wall_time_s": time.time() - t_start,
        "runs": results,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f)
    print(f"wrote {args.out} ({time.time()-t_start:.0f}s total)")


if __name__ == "__main__":
    main()
