#!/usr/bin/env python3
"""Phase 3: does the nugget-masking effect that hid MPDOK's *regression*
advantage (mining_mpdok fig19: 13pp gap at 55.7% nugget vs. 42pp at 6%
nugget) also hide GPC's *calibration* advantage over SVM? This is the one
genuinely open question in the lab -- Phases 1/2 extended patterns already
seen twice (mnist_gpc_lab, place_gpc_lab); this one hasn't been tested
anywhere in the project.

Reuses `mining_mpdok/03_mpdok.ipynb`'s synthetic nested-Matern field
unchanged: y = y_long + y_short + noise, with
  y_long  ~ GP(0, 0.30 * Matern32(ell=80 km))   -- geological-province scale
  y_short ~ GP(0, 0.50 * Matern32(ell=10 km))   -- mineralisation-corridor scale
  noise   ~ N(0, 0.05)                          -- nugget fraction 6.0%
same seed (42) the notebook used, same sill/nugget split -- but generated at
the **full 4,106-point Carlin Trend set** (`datasets.load_carlin_trend`'s
x_km/y_km), not the notebook's 800-point eigenspectrum subsample: that
subsample existed only because notebook 1's `eigh` call is O(n^3) and this
script doesn't need an eigendecomposition, just one Cholesky draw (measured
0.25s at n=4106, not the bottleneck). Using the full set keeps n consistent
with Phases 0-2 so the confident-wrong bootstrap isn't working with a much
smaller, noisier sample than the real-Au comparison it's being held against.

Label (same convention as Phase 0/1, for apples-to-apples comparability):
P95 cutoff on the *observed* field y_true, not on y_short alone -- a real
prospector only ever sees the observed signal, never the decomposed
components, same as the real Au case only ever exposes observed ppm.

Usage: python3 masking_crossover.py --n-seeds 200
Writes results/masking_crossover.json.
"""

import argparse
import json
import os
import sys
import time

import cupy as cp
import numpy as np
from scipy.linalg import cholesky
from sklearn.svm import SVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datasets import load_carlin_trend, _stratified_split
from gp_classifier import LaplaceBinaryGPC
from run_lab import (KERNEL_KIND, average_precision_score, eval_binary,
                      log_loss_binary, median_pairwise_dist)

# Unchanged from mining_mpdok/03_mpdok.ipynb.
C_L, ELL_L = 0.30, 80.0   # long-range: geological province
C_S, ELL_S = 0.50, 10.0   # short-range: mineralisation corridor
SIGMA2_N = 0.05            # noise -- 6.0% of the 0.85 total sill
FIELD_SEED = 42            # same draw mining_mpdok's own notebook used


def nested_kernel(D, C_L=C_L, ell_L=ELL_L, C_S=C_S, ell_S=ELL_S):
    r_L = np.sqrt(3) * D / ell_L
    r_S = np.sqrt(3) * D / ell_S
    return C_L * (1 + r_L) * np.exp(-r_L) + C_S * (1 + r_S) * np.exp(-r_S)


def build_synthetic_field(cutoff_quantile=0.95):
    """Returns (X, y_label, diagnostics). X is (n,2) [x_km, y_km], same
    projection/locations `datasets.spatial_features` uses for the real data.
    """
    data = load_carlin_trend()
    X = np.column_stack([data["x_km"], data["y_km"]])
    n = X.shape[0]
    D2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    D = np.sqrt(D2)

    K_long = nested_kernel(D, C_L, ELL_L, 0.0, 1.0)   # C_S=0 isolates the long component
    K_short = nested_kernel(D, 0.0, 1.0, C_S, ELL_S)  # C_L=0 isolates the short component
    rng = np.random.default_rng(FIELD_SEED)
    L_long = cholesky(K_long + 1e-8 * np.eye(n), lower=True)
    L_short = cholesky(K_short + 1e-8 * np.eye(n), lower=True)
    y_long = L_long @ rng.standard_normal(n)
    y_short = L_short @ rng.standard_normal(n)
    y_noise = np.sqrt(SIGMA2_N) * rng.standard_normal(n)
    y_true = y_long + y_short + y_noise

    cutoff = float(np.percentile(y_true, cutoff_quantile * 100.0))
    label = (y_true >= cutoff).astype(np.int64)

    sill_total = C_L + C_S + SIGMA2_N
    p95_short = np.percentile(y_short, 95)
    is_short_peak = y_short >= p95_short
    diagnostics = {
        "n": n, "sill_total": sill_total,
        "nugget_fraction": SIGMA2_N / sill_total,
        "long_fraction": C_L / sill_total, "short_fraction": C_S / sill_total,
        "cutoff": cutoff, "cutoff_quantile": cutoff_quantile,
        "n_label1": int(label.sum()),
        # how much does the P95-on-observed label overlap with true short-range
        # peaks? -- a diagnostic, not used for fitting.
        "label_short_peak_overlap": float((label & is_short_peak).sum() / max(1, label.sum())),
    }
    return X, label, diagnostics


def load_synthetic_split(X, y, frac_train=0.6, frac_val=0.2, seed=0):
    rng = np.random.default_rng(seed)
    return _stratified_split(X, y, frac_train, frac_val, rng)


def select_ell(X, y, seed=0, frac_train=0.6, frac_val=0.2):
    """Same procedure run_lab.py used for the real Au data: median-heuristic
    grid, selected on validation average precision (not accuracy -- Phase 1
    found accuracy/recall degenerate at this class imbalance, and the
    synthetic field has the same ~5% cutoff-driven imbalance)."""
    rng = np.random.default_rng(seed)
    (X_train, y_train), (X_val, y_val), _ = load_synthetic_split(
        X, y, frac_train, frac_val, seed)
    ell0 = median_pairwise_dist(X_train, rng)
    ell_grid = [ell0 * f for f in (0.5, 0.75, 1.0, 1.5, 2.0)]
    best = None
    for ell in ell_grid:
        clf = LaplaceBinaryGPC(ell=ell, sigma_f=1.0, kind=KERNEL_KIND)
        clf.fit(X_train, y_train)
        _, _, p1 = clf.predict(X_val)
        ap = float(average_precision_score(y_val, cp.asnumpy(p1)))
        print(f"  ell={ell:7.2f}  val_AP={ap:.3f}")
        if best is None or ap > best["ap"]:
            best = {"ell": ell, "ap": ap}
    print(f"selected ell={best['ell']:.2f} km (val_AP={best['ap']:.3f})")
    return best["ell"]


def run_one_seed(X, y, seed, ell, frac_train, frac_val):
    (X_train, y_train), _, (X_test, y_test) = load_synthetic_split(
        X, y, frac_train, frac_val, seed)

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
            "n_wrong": int((correct == 0).sum()),
            "n_confidently_wrong_gt_0.9": int((wrong > 0.9).sum()),
            "frac_confidently_wrong_gt_0.9": float((wrong > 0.9).mean()) if wrong.size else None,
        }

    return {"seed": seed, "gpc": stats(gpc_p1), "svm": stats(svm_p1)}


def pooled_confident_wrong(model, runs):
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
    ap.add_argument("--frac-train", type=float, default=0.6)
    ap.add_argument("--frac-val", type=float, default=0.2)
    ap.add_argument("--cutoff-quantile", type=float, default=0.95)
    ap.add_argument("--out", type=str, default="results/masking_crossover.json")
    args = ap.parse_args()

    print("Building synthetic nested-Matern field (6.0% nugget) at the "
          "4,106-point Carlin Trend set...")
    X, y, diag = build_synthetic_field(args.cutoff_quantile)
    print(f"  n={diag['n']}  nugget_fraction={diag['nugget_fraction']*100:.1f}%  "
          f"n_label1={diag['n_label1']} ({diag['n_label1']/diag['n']*100:.1f}%)  "
          f"label/short-peak overlap={diag['label_short_peak_overlap']*100:.1f}%")

    print("\nSelecting ell on seed-0 validation AP...")
    ell = select_ell(X, y, seed=0, frac_train=args.frac_train, frac_val=args.frac_val)

    results = []
    t_start = time.time()
    for i in range(args.n_seeds):
        t0 = time.time()
        r = run_one_seed(X, y, i, ell, args.frac_train, args.frac_val)
        dt = time.time() - t0
        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (args.n_seeds - i - 1)
        print(f"[{i+1}/{args.n_seeds}] seed={i}  "
              f"gpc_AP={r['gpc']['average_precision']:.3f} gpc_cw%={100*(r['gpc']['frac_confidently_wrong_gt_0.9'] or 0):.1f}  "
              f"svm_AP={r['svm']['average_precision']:.3f} svm_cw%={100*(r['svm']['frac_confidently_wrong_gt_0.9'] or 0):.1f}  "
              f"({dt:.2f}s, elapsed={elapsed:.0f}s, eta={eta:.0f}s)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "ell": ell, "kernel_kind": KERNEL_KIND,
        "frac_train": args.frac_train, "frac_val": args.frac_val,
        "cutoff_quantile": args.cutoff_quantile,
        "field_seed": FIELD_SEED, "C_L": C_L, "ell_L": ELL_L,
        "C_S": C_S, "ell_S": ELL_S, "sigma2_n": SIGMA2_N,
        "diagnostics": diag,
        "wall_time_s": time.time() - t_start,
        "runs": results,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f)
    print(f"wrote {args.out} ({time.time()-t_start:.0f}s total)")

    gpc_ap = np.array([r["gpc"]["average_precision"] for r in results])
    svm_ap = np.array([r["svm"]["average_precision"] for r in results])
    print(f"\n=== Synthetic field (nugget={diag['nugget_fraction']*100:.1f}%), "
          f"{args.n_seeds} seeds ===")
    print(f"Average precision: GPC {gpc_ap.mean():.3f} +/- {gpc_ap.std():.3f}   "
          f"SVM {svm_ap.mean():.3f} +/- {svm_ap.std():.3f}")

    gpc_point, gpc_lo, gpc_hi, gpc_tw, gpc_tcw = pooled_confident_wrong("gpc", results)
    svm_point, svm_lo, svm_hi, svm_tw, svm_tcw = pooled_confident_wrong("svm", results)
    print(f"Confidently-wrong-on-a-miss rate (pooled, 95% bootstrap CI):")
    print(f"  GPC: {100*gpc_point:.1f}% [{100*gpc_lo:.1f}%, {100*gpc_hi:.1f}%]  ({gpc_tcw}/{gpc_tw})")
    print(f"  SVM: {100*svm_point:.1f}% [{100*svm_lo:.1f}%, {100*svm_hi:.1f}%]  ({svm_tcw}/{svm_tw})")
    gap_pp = 100 * (svm_point - gpc_point)
    print(f"\nGPC-vs-SVM confident-wrong gap on synthetic (6.0% nugget): {gap_pp:.1f}pp")
    print("Compare against Phase 1's real-Au gap (55.7% nugget): 47.0pp (99.8% - 52.8%)")
    print("Masking crossover question: does the gap WIDEN as nugget drops? "
          f"{'YES' if gap_pp > 47.0 else 'NO -- gap did not widen'}")


if __name__ == "__main__":
    main()
