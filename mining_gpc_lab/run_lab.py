#!/usr/bin/env python3
"""Ore/waste classification, Carlin Trend Au (P95 cutoff): Laplace GPC vs.
sklearn SVM.

Same "confidently wrong" question as `../mnist_gpc_lab` (MNIST digits) and
`../place_gpc_lab` (loop-closure verification) -- is a Laplace-approximated
GP classifier's confidence more trustworthy than an SVM's -- asked here of a
genuinely high-stakes economic call: is this stream-sediment sample ore or
waste. See LAB_PLAN.md Phase 1/2.

Kernel choice: `kind="matern32"`, not the other two labs' default "rbf" --
`mining_mpdok/02_variogram.ipynb` already fit a Matern-3/2 variogram to this
exact Au field (nugget=0.4536, sill=0.3604, ell=34.4 km), so using the same
kernel family here keeps the fitted `ell` directly comparable to that
geostatistical range instead of introducing an unrelated kernel shape.

No feature standardization for the spatial-only set: x_km/y_km (from
`datasets.spatial_features`) are already the same physical unit and a
similar numeric range (~250-280 km each), unlike place_gpc_lab's mixed
count/ratio features -- standardizing here would make the fitted `ell`
useless for comparing against the 34.4 km variogram range.

**Severe class imbalance** (~5.1% ore at the P95 cutoff): plain accuracy is
close to meaningless (predicting "waste" for everything scores ~94.9%), so
this script always reports precision/recall/F1/balanced-accuracy on the ore
class alongside accuracy -- unlike place_gpc_lab/mnist_gpc_lab, where the
classes were closer to balanced and accuracy alone was informative.

**Found empirically (seed 0):** at this imbalance, neither model's P(ore)
ever crosses 0.5 -- recall_ore is 0.000 for both at the default threshold,
which is uninformative on its own (it says nothing about whether the models
disagree). Two things still work and are reported: (1) average precision
(area under the precision-recall curve), the same threshold-free ranking
metric `mining_mpdok/05_thesis.ipynb` already used for its own exploration-
targeting comparison (fig17: MPDOK 0.41 vs. FRK m=20 0.25) -- comparable
across the two projects by construction; (2) the confident-wrong-on-a-miss
question still applies to false negatives (a "waste" call the model was
>90% sure of, on a point that was actually ore) -- and still separates the
two models sharply (seed 0: GPC 52% of misses were >90% confident vs. SVM
98%), so the original methodology survives, just needs AP alongside it
since raw accuracy/recall at threshold 0.5 do not.

Usage: python3 run_lab.py [--seed 0] [--feature-set spatial]
Writes results/mining_gpc_seed<seed>_<feature_set>.json.
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # gp_classifier.py lives in gp_engine/

from datasets import load_split
from gp_classifier import LaplaceBinaryGPC

KERNEL_KIND = "matern32"


def log_loss_binary(y_true, p1):
    p1 = np.clip(p1, 1e-12, 1.0 - 1e-12)
    return float(-np.mean(y_true * np.log(p1) + (1 - y_true) * np.log(1 - p1)))


def reliability_bins(confidence, correct, n_bins=10):
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


def eval_binary(y_true, p1):
    """(labels, confidence, correct) from a predicted P(class=1) array --
    confidence is the probability mass on whichever label was actually
    predicted, so it ranges [0.5, 1] by construction."""
    labels = (p1 > 0.5).astype(np.int64)
    confidence = np.where(labels == 1, p1, 1.0 - p1)
    correct = (labels == y_true).astype(np.float64)
    return labels, confidence, correct


def imbalance_stats(y_true, labels):
    """Precision/recall/F1/balanced-accuracy on the ore (label=1) class --
    the metrics that actually matter at ~5% positive prevalence, where plain
    accuracy is dominated by the waste class regardless of ore performance."""
    tp = int(((labels == 1) & (y_true == 1)).sum())
    fp = int(((labels == 1) & (y_true == 0)).sum())
    fn = int(((labels == 0) & (y_true == 1)).sum())
    tn = int(((labels == 0) & (y_true == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (2 * precision * recall / (precision + recall)
          if precision and recall and (precision + recall) > 0 else None)
    tnr = tn / (tn + fp) if (tn + fp) > 0 else None
    balanced_acc = 0.5 * (recall + tnr) if recall is not None and tnr is not None else None
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision_ore": precision, "recall_ore": recall, "f1_ore": f1,
            "balanced_accuracy": balanced_acc}


def run(seed=0, feature_set="spatial", frac_train=0.6, frac_val=0.2, cutoff_quantile=0.95):
    rng = np.random.default_rng(seed)
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_split(
        feature_set=feature_set, frac_train=frac_train, frac_val=frac_val,
        seed=seed, cutoff_quantile=cutoff_quantile)

    ell0 = median_pairwise_dist(X_train, rng)
    ell_grid = [ell0 * f for f in (0.5, 0.75, 1.0, 1.5, 2.0)]
    print(f"feature_set={feature_set}  d={X_train.shape[1]}  "
          f"median-heuristic ell0={ell0:.2f} km  grid={[round(e, 2) for e in ell_grid]}")

    best = None
    for ell in ell_grid:
        t0 = time.time()
        clf = LaplaceBinaryGPC(ell=ell, sigma_f=1.0, kind=KERNEL_KIND)
        clf.fit(X_train, y_train)
        _, _, p1 = clf.predict(X_val)
        p1_np = cp.asnumpy(p1)
        labels = (p1_np > 0.5).astype(np.int64)
        acc = float(np.mean(labels == y_val))
        ap = float(average_precision_score(y_val, p1_np))
        ll = log_loss_binary(y_val, p1_np)
        dt = time.time() - t0
        print(f"  ell={ell:7.2f}  val_acc={acc:.3f}  val_AP={ap:.3f}  "
              f"val_logloss={ll:.3f}  ({dt:.2f}s)")
        # Select on average precision, not raw accuracy or balanced accuracy
        # at a 0.5 threshold -- at ~5% ore prevalence P(ore) never actually
        # crosses 0.5 for any ell in this grid (checked directly), so a
        # threshold-based metric can't discriminate between candidate ell
        # values at all here. AP is threshold-free and is the same ranking
        # metric mining_mpdok's own thesis notebook used for this reason.
        if best is None or ap > best["ap"]:
            best = {"ell": ell, "acc": acc, "ap": ap}
    print(f"selected ell={best['ell']:.2f} km (val_acc={best['acc']:.3f}, "
          f"val_AP={best['ap']:.3f})")

    def fit_predict_eval(name, fit_fn, predict_fn, extra=None):
        t0 = time.time()
        model = fit_fn()
        fit_time = time.time() - t0
        t0 = time.time()
        p1 = predict_fn(model)
        predict_time = time.time() - t0

        labels, confidence, correct = eval_binary(y_test, p1)
        wrong_conf = confidence[correct == 0]
        stats = imbalance_stats(y_test, labels)

        result = {
            "model": name,
            "n_train": len(y_train), "n_val": len(y_val), "n_test": len(y_test),
            "n_ore_test": int(y_test.sum()),
            "fit_time_s": fit_time, "predict_time_s": predict_time,
            "accuracy": float(correct.mean()),
            "average_precision": float(average_precision_score(y_test, p1)),
            "log_loss": log_loss_binary(y_test, p1),
            "mean_confidence": float(confidence.mean()),
            "mean_confidence_correct": float(confidence[correct == 1].mean()) if (correct == 1).any() else None,
            "mean_confidence_wrong": float(wrong_conf.mean()) if wrong_conf.size else None,
            "n_wrong": int((correct == 0).sum()),
            "n_confidently_wrong_gt_0.9": int((wrong_conf > 0.9).sum()),
            "frac_confidently_wrong_gt_0.9": float((wrong_conf > 0.9).mean()) if wrong_conf.size else None,
            "reliability": reliability_bins(confidence, correct),
            "risk_coverage": risk_coverage_curve(confidence, correct),
            "confidence_all": confidence.tolist(),
            "correct_all": correct.tolist(),
            "prob_class1_all": p1.tolist(),
            "label_all": y_test.tolist(),
            **stats,
        }
        if extra:
            result.update(extra)

        def fmt(v):
            return f"{v:.3f}" if v is not None else "n/a"

        print(f"{name:16s} test acc={result['accuracy']:.3f}  AP={result['average_precision']:.3f}  "
              f"bal_acc={fmt(stats['balanced_accuracy'])}  "
              f"precision_ore={fmt(stats['precision_ore'])}  recall_ore={fmt(stats['recall_ore'])}  "
              f"logloss={result['log_loss']:.3f}  fit={fit_time:.2f}s  predict={predict_time:.2f}s")
        return result, model

    def gpc_fit():
        m = LaplaceBinaryGPC(ell=best["ell"], sigma_f=1.0, kind=KERNEL_KIND)
        m.fit(X_train, y_train)
        return m

    def gpc_predict(m):
        _, _, p1 = m.predict(X_test)
        return cp.asnumpy(p1)

    gpc_result, gpc_model = fit_predict_eval("laplace_gpc", gpc_fit, gpc_predict,
                                              extra={"ell": best["ell"], "sigma_f": 1.0, "kind": KERNEL_KIND})
    gpc_result["newton_iters"] = gpc_model.fit_info.n_iter
    gpc_result["newton_converged"] = gpc_model.fit_info.converged

    gamma = 1.0 / (2.0 * best["ell"] ** 2)

    def svm_fit():
        m = SVC(kernel="rbf", gamma=gamma, probability=True, random_state=seed)
        m.fit(X_train, y_train)
        return m

    def svm_predict(m):
        probs = m.predict_proba(X_test)
        p1_col = list(m.classes_).index(1)
        return probs[:, p1_col]

    svm_result, _ = fit_predict_eval("svm_rbf_platt", svm_fit, svm_predict, extra={"gamma": gamma})

    out = {
        "seed": seed, "feature_set": feature_set,
        "frac_train": frac_train, "frac_val": frac_val,
        "cutoff_quantile": cutoff_quantile,
        "kernel_kind": KERNEL_KIND,
        "ell_grid": ell_grid,
        "gpc": gpc_result, "svm": svm_result,
    }
    os.makedirs("results", exist_ok=True)
    out_path = f"results/mining_gpc_seed{seed}_{feature_set}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--feature-set", type=str, default="spatial",
                     choices=["spatial", "spatial_pathfinder"])
    ap.add_argument("--frac-train", type=float, default=0.6)
    ap.add_argument("--frac-val", type=float, default=0.2)
    ap.add_argument("--cutoff-quantile", type=float, default=0.95)
    args = ap.parse_args()
    run(args.seed, args.feature_set, args.frac_train, args.frac_val, args.cutoff_quantile)
