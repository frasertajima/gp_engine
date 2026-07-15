#!/usr/bin/env python3
"""Phase 1 -- MLE-fit linear-GRM GBLUP vs MPDOK's CV-grid lambda (LAB_PLAN.md).

MPDOK (`MPDOK/gblup/gblup.py::cv_lambda_sweep`) picks lambda by a 20-point
log-spaced grid search directly against CV Pearson r -- effectively tuning on
the validation folds themselves. gp_engine here instead fits (sigma_f2,
sigma_n2) by Type-II marginal likelihood on the *training* fold only (no
validation peeking), via `gblup_hyperopt.mle_fit`, and only then predicts on
the held-out fold. Same GRM, same data, same 5-fold split as Phase 0 --
compares two philosophies of hyperparameter selection on identical folds.

Also reports held-out NLL (via gp_engine's predictive variance -- MPDOK's
lab has no analogue of this metric; MLE fitting is what makes it well-defined).

Baseline numbers to beat are Phase 0's, i.e. gp_engine == MPDOK's live
`cv_lambda_sweep`, NOT the (stale) MPDOK README table -- see RESULTS_PHASE0.md.

Run inside conda py314 (needs cupy):
    /var/home/fraser/miniconda3/envs/py314/bin/python run_phase1.py
"""

import math
import time

import cupy as cp
import numpy as np

import sys
sys.path.insert(0, "..")
from gp_core import PrecomputedKernel, gp_fit, gp_predict  # noqa: E402

import datasets  # noqa: E402
from gblup_hyperopt import mle_fit  # noqa: E402

LOG2PI = math.log(2.0 * math.pi)

# Phase 0 CV-grid baseline (== MPDOK's live cv_lambda_sweep, RESULTS_PHASE0.md)
PHASE0_R = {
    "wheat/E1": 0.4264, "wheat/E2": 0.3880, "wheat/E3": 0.3678,
    "wheat/E4": 0.4534, "mice/bmi": 0.1378,
}


def predict_r_nll(A_base, y_train, A_cross, y_val, sigma_f2, sigma_n2):
    kern = PrecomputedKernel(cp.asarray(A_base), sigma_f2=sigma_f2, sigma_n2=sigma_n2,
                             A_cross=cp.asarray(A_cross))
    dummy_X = cp.zeros((A_base.shape[0], 1))
    fit = gp_fit(kern, dummy_X, cp.asarray(y_train), tol=1e-10, max_ir=15)
    dummy_Xs = cp.zeros((A_cross.shape[0], 1))
    mean, var = gp_predict(fit, kern, dummy_X, dummy_Xs, include_noise=True,
                           batch=max(4096, A_cross.shape[0]))
    mean, var = cp.asnumpy(mean), cp.asnumpy(var)
    r = np.corrcoef(y_val, mean)[0, 1]
    # No extra variance floor beyond gp_core's own clamp(var, 0) -- same
    # convention as gp_lab/run_benchmark.py: report mean AND median NLL (the
    # median is robust to the rare FP32-cancellation near-zero-variance point
    # near-duplicate genotypes in a GRM can produce), and count how many
    # points blew the envelope (nll_pt > 50) instead of silently flooring.
    nll_pt = 0.5 * np.log(2 * np.pi * np.maximum(var, 1e-300)) + \
        (y_val - mean) ** 2 / (2 * np.maximum(var, 1e-300))
    n_pathological = int(np.sum(nll_pt > 50))
    nll_mean = float(np.mean(nll_pt))
    nll_median = float(np.median(nll_pt))
    return (r if np.isfinite(r) else 0.0), nll_mean, nll_median, n_pathological, fit.converged


def phase1_trait(G, y, label, k=5, seed=42):
    splits = datasets.kfold_indices(len(y), k=k, seed=seed)
    fold_r, fold_nll_mean, fold_nll_med, fold_patho = [], [], [], []
    fold_sf2, fold_sn2 = [], []
    t0 = time.time()
    for train, val in splits:
        G_tt = G[np.ix_(train, train)]
        G_vt = G[np.ix_(val, train)]
        mle = mle_fit(G_tt, y[train])
        r, nll_m, nll_med, n_patho, ok = predict_r_nll(
            G_tt, y[train], G_vt, y[val], mle["sigma_f2"], mle["sigma_n2"])
        fold_r.append(r)
        fold_nll_mean.append(nll_m)
        fold_nll_med.append(nll_med)
        fold_patho.append(n_patho)
        fold_sf2.append(mle["sigma_f2"])
        fold_sn2.append(mle["sigma_n2"])
    dt = time.time() - t0
    mean_r = float(np.mean(fold_r))
    mean_nll_mean = float(np.mean(fold_nll_mean))
    mean_nll_med = float(np.mean(fold_nll_med))
    total_patho = int(np.sum(fold_patho))
    mean_lam = float(np.mean(fold_sn2) / np.mean(fold_sf2))
    p0 = PHASE0_R.get(label)
    delta = f"{mean_r - p0:+.4f}" if p0 is not None else "n/a"
    nll_flag = f"  [!! {total_patho} pathological pts -- mean NLL is meaningless, use median !!]" \
        if total_patho else ""
    print(f"[{label}] MLE r={mean_r:.4f} (Phase0 CV-grid r={p0}, delta={delta})  "
         f"NLL mean={mean_nll_mean:.3e} median={mean_nll_med:.3f}{nll_flag}  "
         f"mean_lam={mean_lam:.4g}  sigma_f2={np.mean(fold_sf2):.4g} "
         f"sigma_n2={np.mean(fold_sn2):.4g}  ({dt:.1f}s)")
    return dict(label=label, mean_r=mean_r, mean_nll_mean=mean_nll_mean,
               mean_nll_med=mean_nll_med, n_pathological=total_patho,
               mean_lam=mean_lam, fold_r=fold_r)


def main():
    print("=== wheat (Crossa et al. 2010) -- MLE-fit sigma_f2/sigma_n2, no CV peeking ===")
    w = datasets.load_wheat()
    results = []
    for i, trait in enumerate(w["trait_names"]):
        results.append(phase1_trait(w["A"], w["Y"][:, i], f"wheat/{trait}"))

    print()
    print("=== mice (Valdar et al. 2006) ===")
    m = datasets.load_mice()
    results.append(phase1_trait(m["A"], m["y_bmi"], "mice/bmi"))
    results.append(phase1_trait(m["A"], m["y_blen"], "mice/blen"))

    print()
    print("=== summary (MLE r minus Phase0 CV-grid r, per trait) ===")
    for r in results:
        p0 = PHASE0_R.get(r["label"])
        if p0 is None:
            continue
        print(f"  {r['label']:12s} {r['mean_r'] - p0:+.4f}")


if __name__ == "__main__":
    main()
