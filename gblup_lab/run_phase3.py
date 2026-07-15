#!/usr/bin/env python3
"""Phase 3 (stretch goal, LAB_PLAN.md) -- linear vs RKHS marker kernel on the
G2F hybrid maize yield panel (N~4979, d=48580 markers, averaged-parent
dosage -- see g2f_hybrid.py for the construction and the protocol caveat:
this is a random hybrid-combination holdout on 2014-2023 data, NOT the real
2024-season competition test, so these numbers are NOT comparable to any
competition leaderboard).

Same pipeline as Phase 0-2 (5-fold CV, MLE hyperparameter fit, no CV
peeking), first real test of the engine-gap fix (`PrecomputedKernel` +
`marker_kernel.py`'s GEMM-trick distance builder) at real scale: d=48580 is
~38x wider than wheat's 1279 and ~4.7x wider than mice's 10346.

Run inside conda py314 (needs cupy):
    /var/home/fraser/miniconda3/envs/py314/bin/python run_phase3.py
"""

import time

import cupy as cp
import numpy as np

import datasets
import g2f_hybrid
from gblup_hyperopt import mle_fit, mle_fit_rkhs
from marker_kernel import apply_kernel, cross_squared_dist, squared_dist_matrix
from run_phase1 import predict_r_nll


def cv_linear(X, y, k=5, seed=42, label="g2f-hybrid/linear"):
    splits = datasets.kfold_indices(len(y), k=k, seed=seed)
    fold_r, fold_nll, fold_patho = [], [], []
    t0 = time.time()
    for train, val in splits:
        Xt, Xv = X[train], X[val]
        Xtc = Xt - Xt.mean(0, keepdims=True)
        Kt = Xtc @ Xtc.T
        Xvc = Xv - Xt.mean(0, keepdims=True)
        Kv = Xvc @ Xtc.T
        # Normalize to unit mean-diagonal, same convention VanRaden's GRM scaling
        # and the wheat/mice `A` matrices already use (diag ~1-2). At d=48580
        # markers the raw X@X.T diagonal is O(1e4) -- gp_core's FP32 factor path
        # has a ~1e-6-absolute variance floor (see gp_predict docstring), which
        # at that magnitude swamps genuine small variances for nearly every
        # point (confirmed: unnormalized run gave 4979/4979 pathological points,
        # a total collapse, not a rare edge case). Un-normalized linear kernels
        # in the d>>n regime are outside gp_engine's usable FP32 envelope; this
        # rescaling is the fix, not a cover-up -- see RESULTS_PHASE3.md.
        scale = float(np.mean(np.diag(Kt)))
        Kt, Kv = Kt / scale, Kv / scale
        mle = mle_fit(Kt, y[train])
        r, nll_m, nll_med, npat, ok = predict_r_nll(Kt, y[train], Kv, y[val],
                                                     mle["sigma_f2"], mle["sigma_n2"])
        fold_r.append(r); fold_nll.append(nll_med); fold_patho.append(npat)
    dt = time.time() - t0
    patho = sum(fold_patho)
    flag = f"  [!! {patho} pathological pts !!]" if patho else ""
    print(f"[{label}] r={np.mean(fold_r):.4f}  NLL median={np.mean(fold_nll):.3e}{flag}  ({dt:.1f}s)")
    return dict(label=label, mean_r=float(np.mean(fold_r)), fold_r=fold_r)


def cv_rkhs(X, y, kind="rbf", k=5, seed=42, label=None):
    label = label or f"g2f-hybrid/{kind}"
    splits = datasets.kfold_indices(len(y), k=k, seed=seed)
    fold_r, fold_nll, fold_patho, fold_ell = [], [], [], []
    t0 = time.time()
    for train, val in splits:
        X_tt, X_vt = X[train], X[val]
        D2_train = squared_dist_matrix(X_tt)
        mle = mle_fit_rkhs(D2_train, y[train], kind=kind)
        A_base = cp.asnumpy(apply_kernel(D2_train, mle["ell"], kind=kind))
        D2_cross = cross_squared_dist(X_vt, X_tt)
        A_cross = cp.asnumpy(apply_kernel(D2_cross, mle["ell"], kind=kind))
        r, nll_m, nll_med, npat, ok = predict_r_nll(A_base, y[train], A_cross, y[val],
                                                     mle["sigma_f2"], mle["sigma_n2"])
        fold_r.append(r); fold_nll.append(nll_med); fold_patho.append(npat)
        fold_ell.append(mle["ell"])
    dt = time.time() - t0
    patho = sum(fold_patho)
    flag = f"  [!! {patho} pathological pts !!]" if patho else ""
    print(f"[{label}] r={np.mean(fold_r):.4f}  NLL median={np.mean(fold_nll):.3e}{flag}  "
         f"ell={np.mean(fold_ell):.4g}  ({dt:.1f}s)")
    return dict(label=label, mean_r=float(np.mean(fold_r)), fold_r=fold_r)


def main():
    print("Loading G2F hybrid panel (averaged-parent dosage, see g2f_hybrid.py) ...")
    d = g2f_hybrid.load_hybrid_dataset()
    X, y_raw, n_rec = d["X"], d["y"], d["n_records"]
    print(f"n_hybrids={len(y_raw)}  d_markers={X.shape[1]}  "
         f"records/hybrid: min={n_rec.min()} median={int(np.median(n_rec))} max={n_rec.max()}")
    print(f"yield (Mg/ha): mean={y_raw.mean():.3f} std={y_raw.std():.3f} "
         f"min={y_raw.min():.3f} max={y_raw.max():.3f}")

    y = (y_raw - y_raw.mean()) / y_raw.std()   # standardize, same convention as wheat/mice

    print()
    print("=== linear (from-X, ridge-style MLE) ===")
    lin = cv_linear(X, y)

    print()
    print("=== RKHS ===")
    rbf = cv_rkhs(X, y, kind="rbf")
    mat = cv_rkhs(X, y, kind="matern32")

    print()
    print("=== summary ===")
    print(f"  linear   r={lin['mean_r']:.4f}")
    print(f"  rbf      r={rbf['mean_r']:.4f}  delta vs linear = {rbf['mean_r']-lin['mean_r']:+.4f}")
    print(f"  matern32 r={mat['mean_r']:.4f}  delta vs linear = {mat['mean_r']-lin['mean_r']:+.4f}")
    print()
    print("REMINDER: this is a random hybrid-combination 5-fold CV on 2014-2023 data,")
    print("NOT the G2F competition's held-out-2024-season protocol. Not leaderboard-comparable.")


if __name__ == "__main__":
    main()
