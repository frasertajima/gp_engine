#!/usr/bin/env python3
"""M3 generality sweep: is the "GPC is (almost) never confidently wrong"
finding (M1 pilot, M2's 200-seed confirmation) a structural property of
Laplace's predictive-variance shrinkage, or specific to the RBF kernel +
logit likelihood M1/M2 used? Tests three alternate configs against the M2
baseline (RBF+logit, already run at 200 seeds in results/confidence_study.json):

    RBF      + probit    (the book's own default likelihood)
    Matern32 + logit
    Matern52 + logit

Each kernel/likelihood combo gets its own quick 1-seed validation ell-grid
(Matern kernels don't share RBF's optimal lengthscale at the same ell value --
checked empirically, see LAB_PLAN.md M3), then N seeds at that fixed ell,
same per-seed-then-bootstrap statistics as confidence_study.py. SVM is not
refit here -- this sweep is about GPC's own generality across kernel/
likelihood, not another GPC-vs-SVM comparison.

Usage: python3 generality_sweep.py --n-seeds 50
Writes results/generality_<kind>_<likelihood>.json, one per config.
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import cupy as cp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datasets import load_mnist_subset
from gp_classifier import OneVsRestLaplaceGPC


def median_pairwise_dist(X, rng, max_sample=300):
    idx = rng.choice(X.shape[0], size=min(max_sample, X.shape[0]), replace=False)
    sub = X[idx].astype(np.float64)
    D2 = ((sub[:, None, :] - sub[None, :, :]) ** 2).sum(-1)
    d = np.sqrt(D2[D2 > 1e-15])
    return float(np.median(d)) if d.size else 1.0


def select_ell(kind, likelihood, classes, train_per_class, val_per_class, seed=0):
    rng = np.random.default_rng(seed)
    (X_train, y_train), (X_val, y_val), _ = load_mnist_subset(
        n_train_per_class=train_per_class, n_val_per_class=val_per_class,
        n_test_per_class=1, seed=seed)
    ell0 = median_pairwise_dist(X_train, rng)
    grid = [ell0 * f for f in (0.5, 0.75, 1.0, 1.5, 2.0)]

    best = None
    for ell in grid:
        clf = OneVsRestLaplaceGPC(classes=classes, ell=ell, sigma_f=1.0,
                                   kind=kind, likelihood=likelihood)
        clf.fit(X_train, y_train)
        labels, _, _, _ = clf.predict(X_val)
        acc = float(cp.mean((labels == cp.asarray(y_val)).astype(cp.float64)))
        print(f"    ell={ell:7.2f}  val_acc={acc:.3f}")
        if best is None or acc > best["acc"]:
            best = {"ell": ell, "acc": acc}
    return best["ell"], best["acc"]


def run_config(kind, likelihood, ell, n_seeds, train_per_class, test_per_class, classes):
    results = []
    t_start = time.time()
    for i in range(n_seeds):
        (X_train, y_train), _, (X_test, y_test) = load_mnist_subset(
            n_train_per_class=train_per_class, n_val_per_class=1,
            n_test_per_class=test_per_class, seed=i)
        clf = OneVsRestLaplaceGPC(classes=classes, ell=ell, sigma_f=1.0,
                                   kind=kind, likelihood=likelihood)
        clf.fit(X_train, y_train)
        labels, confidence, probs, _ = clf.predict(X_test)
        labels_np, confidence_np = cp.asnumpy(labels), cp.asnumpy(confidence)
        correct = (labels_np == y_test).astype(np.float64)

        wrong = confidence_np[correct == 0]
        results.append({
            "seed": i,
            "accuracy": float(correct.mean()),
            "n_wrong": int((correct == 0).sum()),
            "frac_confidently_wrong": float((wrong > 0.5).mean()) if wrong.size else None,
            "confidence": confidence_np.tolist(),
            "correct": correct.tolist(),
        })
        if (i + 1) % 10 == 0 or i == n_seeds - 1:
            elapsed = time.time() - t_start
            print(f"  [{i+1}/{n_seeds}] acc={results[-1]['accuracy']:.3f} "
                  f"conf_wrong%={100*(results[-1]['frac_confidently_wrong'] or 0):.1f}  "
                  f"(elapsed {elapsed/60:.1f}min)", flush=True)
    return results, time.time() - t_start


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=50)
    ap.add_argument("--train-per-class", type=int, default=150)
    ap.add_argument("--test-per-class", type=int, default=100)
    ap.add_argument("--val-per-class", type=int, default=30)
    args = ap.parse_args()

    classes = list(range(10))
    configs = [("rbf", "probit"), ("matern32", "logit"), ("matern52", "logit")]

    for kind, likelihood in configs:
        print(f"=== {kind} + {likelihood} ===")
        print("  selecting ell (1-seed validation grid)...")
        ell, val_acc = select_ell(kind, likelihood, classes, args.train_per_class,
                                   args.val_per_class)
        print(f"  selected ell={ell:.2f} (val_acc={val_acc:.3f})")

        results, wall_time = run_config(kind, likelihood, ell, args.n_seeds,
                                        args.train_per_class, args.test_per_class, classes)
        out = {
            "kind": kind, "likelihood": likelihood, "ell": ell,
            "n_seeds": args.n_seeds, "train_per_class": args.train_per_class,
            "test_per_class": args.test_per_class, "wall_time_s": wall_time,
            "runs": results,
        }
        path = f"results/generality_{kind}_{likelihood}.json"
        with open(path, "w") as f:
            json.dump(out, f)
        print(f"wrote {path} ({wall_time:.0f}s)\n")


if __name__ == "__main__":
    main()
