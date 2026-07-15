#!/usr/bin/env python3
"""MNIST one-vs-rest Laplace GPC (CUDA Fortran-engine-family) vs. sklearn SVM.

Reproduces the shape of GPML (Rasmussen & Williams 2006) Sec 3.7.3's MNIST
worked example -- Laplace-approximated GP classification, RBF kernel, with a
calibrated predictive probability, benchmarked against an SVM -- but as
one-vs-rest across all 10 digits rather than the book's binary 3-vs-5 slice,
and on a balanced subsample (exact GP is O(n^3); see LAB_PLAN.md).

Usage: python3 run_lab.py [--train-per-class 150] [--seed 0]
Writes results/mnist_gpc_seed<seed>.json.
"""

import argparse
import json
import os
import sys
import time

import cupy as cp
import numpy as np
from sklearn.svm import SVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # gp_classifier.py lives in gp_engine/

from datasets import load_mnist_subset
from gp_classifier import OneVsRestLaplaceGPC


def log_loss(y_true, probs_by_class, classes):
    """Multiclass log-loss from a (m, num_classes) probability array that is
    not required to be row-normalized (clipped + renormalized here)."""
    idx = {c: i for i, c in enumerate(classes)}
    p = np.clip(probs_by_class, 1e-12, 1.0)
    p = p / p.sum(axis=1, keepdims=True)
    rows = np.array([idx[int(y)] for y in y_true])
    return float(-np.mean(np.log(p[np.arange(len(y_true)), rows])))


def reliability_bins(confidence, correct, n_bins=10):
    """Standard calibration/reliability-diagram bins: for each confidence
    bin, mean predicted confidence vs. empirical accuracy + bin count."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (confidence >= lo) & (confidence < hi if hi < 1.0 else confidence <= hi)
        if mask.sum() == 0:
            continue
        out.append({
            "bin_lo": float(lo), "bin_hi": float(hi),
            "mean_confidence": float(confidence[mask].mean()),
            "accuracy": float(correct[mask].mean()),
            "count": int(mask.sum()),
        })
    return out


def risk_coverage_curve(confidence, correct, n_points=20):
    """Sort predictions by confidence descending; at each coverage level (the
    top-k most-confident fraction), report accuracy on that retained subset.
    This is the standard selective-prediction diagnostic: if confidence tracks
    correctness, accuracy should rise as coverage (the accepted fraction)
    shrinks to just the most-confident predictions."""
    order = np.argsort(-confidence)
    correct_sorted = correct[order]
    n = len(correct)
    out = []
    for frac in np.linspace(0.05, 1.0, n_points):
        k = max(1, int(round(frac * n)))
        out.append({"coverage": float(k / n), "accuracy": float(correct_sorted[:k].mean()), "n": k})
    return out


def median_pairwise_dist(X, rng, max_sample=300):
    idx = rng.choice(X.shape[0], size=min(max_sample, X.shape[0]), replace=False)
    sub = X[idx].astype(np.float64)
    D2 = ((sub[:, None, :] - sub[None, :, :]) ** 2).sum(-1)
    d = np.sqrt(D2[D2 > 1e-15])
    return float(np.median(d)) if d.size else 1.0


def run(train_per_class=150, val_per_class=30, test_per_class=100, seed=0):
    rng = np.random.default_rng(seed)
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_mnist_subset(
        n_train_per_class=train_per_class, n_val_per_class=val_per_class,
        n_test_per_class=test_per_class, seed=seed)

    ell0 = median_pairwise_dist(X_train, rng)
    ell_grid = [ell0 * f for f in (0.5, 0.75, 1.0, 1.5, 2.0)]

    print(f"median-heuristic ell0={ell0:.2f}; grid={[round(e, 1) for e in ell_grid]}")

    classes = list(range(10))
    best = None
    for ell in ell_grid:
        t0 = time.time()
        clf = OneVsRestLaplaceGPC(classes=classes, ell=ell, sigma_f=1.0)
        clf.fit(X_train, y_train)
        labels, _, probs, _ = clf.predict(X_val)
        acc = float(cp.mean((labels == cp.asarray(y_val)).astype(cp.float64)))
        ll = log_loss(y_val, cp.asnumpy(probs), classes)
        dt = time.time() - t0
        print(f"  ell={ell:7.2f}  val_acc={acc:.3f}  val_logloss={ll:.3f}  ({dt:.1f}s)")
        if best is None or acc > best["acc"]:
            best = {"ell": ell, "acc": acc}

    print(f"selected ell={best['ell']:.2f} (val_acc={best['acc']:.3f})")

    # --- final GPC fit on train, scored on the held-out test set -----------
    t0 = time.time()
    gpc = OneVsRestLaplaceGPC(classes=classes, ell=best["ell"], sigma_f=1.0)
    gpc.fit(X_train, y_train)
    fit_time = time.time() - t0
    n_iters = [gpc.models[c].fit_info.n_iter for c in classes]
    converged = all(gpc.models[c].fit_info.converged for c in classes)

    t0 = time.time()
    labels, confidence, probs, norm_probs = gpc.predict(X_test)
    predict_time = time.time() - t0

    labels_np = cp.asnumpy(labels)
    confidence_np = cp.asnumpy(confidence)
    probs_np = cp.asnumpy(probs)
    correct = (labels_np == y_test).astype(np.float64)

    gpc_result = {
        "model": "laplace_gpc_ovr",
        "ell": best["ell"], "sigma_f": 1.0,
        "n_train": len(y_train), "n_test": len(y_test),
        "newton_iters": n_iters, "newton_converged": converged,
        "fit_time_s": fit_time, "predict_time_s": predict_time,
        "accuracy": float(correct.mean()),
        "log_loss": log_loss(y_test, probs_np, classes),
        "mean_confidence": float(confidence_np.mean()),
        "mean_confidence_correct": float(confidence_np[correct == 1].mean()) if (correct == 1).any() else None,
        "mean_confidence_wrong": float(confidence_np[correct == 0].mean()) if (correct == 0).any() else None,
        "reliability": reliability_bins(confidence_np, correct),
        "risk_coverage": risk_coverage_curve(confidence_np, correct),
        "confidence_all": confidence_np.tolist(),
        "correct_all": correct.tolist(),
    }
    print(f"GPC  test acc={gpc_result['accuracy']:.3f}  "
          f"logloss={gpc_result['log_loss']:.3f}  "
          f"fit={fit_time:.1f}s  predict={predict_time:.1f}s  "
          f"newton_iters={n_iters}  converged={converged}")

    # --- SVM baseline (matching kernel family: RBF, same gamma convention) -
    gamma = 1.0 / (2.0 * best["ell"] ** 2)   # so exp(-gamma r^2) == our RBF
    t0 = time.time()
    svm = SVC(kernel="rbf", gamma=gamma, probability=True, random_state=seed)
    svm.fit(X_train, y_train)
    svm_fit_time = time.time() - t0

    t0 = time.time()
    svm_probs = svm.predict_proba(X_test)   # (m, 10), columns in svm.classes_ order
    svm_predict_time = time.time() - t0
    svm_labels = svm.classes_[np.argmax(svm_probs, axis=1)]
    svm_confidence = svm_probs.max(axis=1)
    svm_correct = (svm_labels == y_test).astype(np.float64)

    # reorder svm_probs columns to the 0..9 order our log_loss/classes expect
    order = [list(svm.classes_).index(c) for c in classes]
    svm_probs_ordered = svm_probs[:, order]

    svm_result = {
        "model": "svm_rbf_platt",
        "gamma": gamma,
        "n_train": len(y_train), "n_test": len(y_test),
        "fit_time_s": svm_fit_time, "predict_time_s": svm_predict_time,
        "accuracy": float(svm_correct.mean()),
        "log_loss": log_loss(y_test, svm_probs_ordered, classes),
        "mean_confidence": float(svm_confidence.mean()),
        "mean_confidence_correct": float(svm_confidence[svm_correct == 1].mean()) if (svm_correct == 1).any() else None,
        "mean_confidence_wrong": float(svm_confidence[svm_correct == 0].mean()) if (svm_correct == 0).any() else None,
        "reliability": reliability_bins(svm_confidence, svm_correct),
        "risk_coverage": risk_coverage_curve(svm_confidence, svm_correct),
        "confidence_all": svm_confidence.tolist(),
        "correct_all": svm_correct.tolist(),
    }
    print(f"SVM  test acc={svm_result['accuracy']:.3f}  "
          f"logloss={svm_result['log_loss']:.3f}  "
          f"fit={svm_fit_time:.1f}s  predict={svm_predict_time:.1f}s")

    out = {
        "seed": seed,
        "train_per_class": train_per_class, "val_per_class": val_per_class,
        "test_per_class": test_per_class,
        "ell_grid": ell_grid, "gpc": gpc_result, "svm": svm_result,
        "sample_predictions": [
            {"true": int(y_test[i]), "gpc_pred": int(labels_np[i]),
             "gpc_probs": {str(c): float(probs_np[i, ci]) for ci, c in enumerate(classes)}}
            for i in range(20)
        ],
    }
    with open(f"results/mnist_gpc_seed{seed}.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote results/mnist_gpc_seed{seed}.json")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-per-class", type=int, default=150)
    ap.add_argument("--val-per-class", type=int, default=30)
    ap.add_argument("--test-per-class", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    run(args.train_per_class, args.val_per_class, args.test_per_class, args.seed)
