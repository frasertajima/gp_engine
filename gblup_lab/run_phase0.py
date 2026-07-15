#!/usr/bin/env python3
"""Phase 0 -- parity, no new science (see LAB_PLAN.md).

Reproduces MPDOK's own linear-GRM CV-lambda-sweep result through gp_engine's
exact Cholesky+IR solver instead of MPDOK's numpy/cupy backends, using the
*same* GRM (`A`, already published with the dataset) and the *same* 5-fold
split MPDOK/gblup/grm.py uses. Two comparisons per trait:

  1. gp_engine's alpha vs a plain numpy reference alpha at the same lambda
     (proves the PrecomputedKernel + IR plumbing reproduces a known-correct
     linear solve, not just "some number").
  2. gp_engine's best-lambda CV r vs MPDOK's README-reported range
     (wheat 0.45-0.55 across environments; mice BMI CV r=0.280).

Run inside conda py314 (needs cupy):
    /var/home/fraser/miniconda3/envs/py314/bin/python run_phase0.py
"""

import sys
import time

import cupy as cp
import numpy as np

sys.path.insert(0, "..")
from gp_core import PrecomputedKernel, gp_fit, gp_predict  # noqa: E402

import datasets  # noqa: E402

LAMBDAS = np.logspace(-4, 1, 20)


def numpy_baseline(G_train, y_train, G_cross, lam):
    """Direct numpy solve -- the thing gp_engine's IR result must agree with."""
    n = G_train.shape[0]
    alpha = np.linalg.solve(G_train + lam * np.eye(n), y_train)
    return G_cross @ alpha, alpha


def gp_engine_fit_predict(G_train, y_train, G_cross, lam):
    """Same (G_train + lam I) alpha = y_train system, solved via gp_engine's
    FP32-factor + FP64-IR path instead of numpy dgesv."""
    kern = PrecomputedKernel(cp.asarray(G_train), sigma_f2=1.0, sigma_n2=lam,
                             A_cross=cp.asarray(G_cross))
    dummy_X = cp.zeros((G_train.shape[0], 1))  # unused by PrecomputedKernel
    fit = gp_fit(kern, dummy_X, cp.asarray(y_train), tol=1e-10, max_ir=15)
    dummy_Xs = cp.zeros((G_cross.shape[0], 1))
    mean, _var = gp_predict(fit, kern, dummy_X, dummy_Xs,
                            batch=max(4096, G_cross.shape[0]))
    return cp.asnumpy(mean), cp.asnumpy(fit.alpha), fit.relres, fit.n_ir, fit.converged


def cv_sweep(G, y, k=5, seed=42, label=""):
    splits = datasets.kfold_indices(len(y), k=k, seed=seed)

    # --- 1. parity check at a single mid-range lambda: does gp_engine's IR
    #     alpha match numpy's dgesv alpha? (first fold only, cheap sanity gate)
    train, val = splits[0]
    G_tt = G[np.ix_(train, train)]
    G_vt = G[np.ix_(val, train)]
    lam_check = 0.1
    y_np, alpha_np = numpy_baseline(G_tt, y[train], G_vt, lam_check)
    y_gp, alpha_gp, relres, n_ir, ok = gp_engine_fit_predict(
        G_tt, y[train], G_vt, lam_check)
    alpha_err = np.max(np.abs(alpha_np - alpha_gp)) / (np.max(np.abs(alpha_np)) + 1e-30)
    pred_err = np.max(np.abs(y_np - y_gp)) / (np.max(np.abs(y_np)) + 1e-30)
    print(f"[{label}] parity @ lam={lam_check}: "
         f"alpha rel-err={alpha_err:.2e}  pred rel-err={pred_err:.2e}  "
         f"relres={relres:.2e}  n_ir={n_ir}  converged={ok}")

    # --- 2. full lambda sweep via gp_engine, mirroring MPDOK's cv_lambda_sweep
    mean_rs = []
    t0 = time.time()
    for lam in LAMBDAS:
        fold_rs = []
        for train, val in splits:
            G_tt = G[np.ix_(train, train)]
            G_vt = G[np.ix_(val, train)]
            y_hat, _, _, _, ok = gp_engine_fit_predict(G_tt, y[train], G_vt, lam)
            if not ok:
                fold_rs.append(0.0)
                continue
            r = np.corrcoef(y[val], y_hat)[0, 1]
            fold_rs.append(r if np.isfinite(r) else 0.0)
        mean_rs.append(np.mean(fold_rs))
    dt = time.time() - t0
    best_idx = int(np.argmax(mean_rs))
    print(f"[{label}] gp_engine best: lam={LAMBDAS[best_idx]:.4g}  "
         f"r={mean_rs[best_idx]:.4f}  ({dt:.1f}s, {k}x{len(LAMBDAS)} solves)")
    return LAMBDAS[best_idx], mean_rs[best_idx]


def main():
    print("=== wheat (Crossa et al. 2010) -- published GBLUP r ~ 0.45-0.55 per env ===")
    w = datasets.load_wheat()
    for i, trait in enumerate(w["trait_names"]):
        cv_sweep(w["A"], w["Y"][:, i], label=f"wheat/{trait}")

    print()
    print("=== mice (Valdar et al. 2006) -- MPDOK README: CV r=0.280 for BMI ===")
    m = datasets.load_mice()
    cv_sweep(m["A"], m["y_bmi"], label="mice/bmi")
    cv_sweep(m["A"], m["y_blen"], label="mice/blen")


if __name__ == "__main__":
    main()
