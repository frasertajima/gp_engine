"""Marginal-likelihood hyperparameter fitting for the linear-GRM GBLUP kernel.

Phase 1 of gblup_lab (see LAB_PLAN.md): replaces MPDOK's 20-point CV-lambda
grid search (`MPDOK/gblup/gblup.py::cv_lambda_sweep`) with gp_engine's own
Type-II maximum-likelihood fit -- the same NM-over-log-hyperparameters pattern
`gp_hyperopt.py::fit_hyperparams` uses for the coordinate-kernel path in
`gp_lab/`, adapted here for `PrecomputedKernel` (no X coordinates, no ARD --
the GRM already collapsed the marker dimension via VanRaden's GEMM identity,
same trick MPDOK's `rbf_kernel.py`/`kriging_kernel.py` use).

Two free hyperparameters, both interpretable directly against MPDOK's model:
    sigma_f2 -- genetic-variance scale (MPDOK's model implicitly fixes this at 1)
    sigma_n2 -- residual-noise variance (MPDOK's lambda = sigma_n2 / sigma_f2)
"""

import math
import time

import cupy as cp
import numpy as np
from scipy.optimize import minimize

import sys
sys.path.insert(0, "..")
from gp_core import FactorError, PrecomputedKernel, gp_fit  # noqa: E402
from marker_kernel import apply_kernel, median_dist_scale  # noqa: E402

PENALTY = 1e12
LOG2PI = math.log(2.0 * math.pi)


def lml_precomputed(A_base_dev, y_dev, sigma_f2, sigma_n2, tol=1e-8, max_ir=15):
    """LML for K = sigma_f2 * A_base + sigma_n2 * I via gp_engine's mixed-
    precision path (fused FP32 factor, FP64 IR)."""
    kern = PrecomputedKernel(A_base_dev, sigma_f2=sigma_f2, sigma_n2=sigma_n2)
    dummy_X = cp.zeros((A_base_dev.shape[0], 1))
    fit = gp_fit(kern, dummy_X, y_dev, tol=tol, max_ir=max_ir)
    n = y_dev.shape[0]
    quad = float(y_dev @ fit.alpha)
    lml = -0.5 * quad - 0.5 * fit.logdet - 0.5 * n * LOG2PI
    return lml, fit.relres


def mle_fit(A_base, y, start=None, tol=1e-8, maxfev=80, verbose=False):
    """Nelder-Mead over log(sigma_f, sigma_n) maximizing the LML of the linear
    GRM kernel. Returns dict(sigma_f2, sigma_n2, lam=sigma_n2/sigma_f2, lml,
    nfev, wall_s).
    """
    A_dev = cp.asarray(A_base, dtype=cp.float64)
    y_dev = cp.asarray(y, dtype=cp.float64)
    if start is None:
        ystd = float(cp.std(y_dev))
        start = [ystd, 0.5 * ystd]   # sigma_f, sigma_n
    history = []

    def objective(logp):
        sigf, sign = np.exp(logp)
        try:
            lml, relres = lml_precomputed(A_dev, y_dev, sigf ** 2, sign ** 2, tol=tol)
            if relres > 1e-3:
                lml = -PENALTY
        except FactorError:
            lml = -PENALTY
        history.append((sigf, sign, lml))
        if verbose:
            print(f"    eval {len(history):3d}: sigma_f={sigf:.4f} "
                 f"sigma_n={sign:.5f}  LML={lml: .2f}", flush=True)
        return -lml

    t0 = time.perf_counter()
    res = minimize(objective, np.log(np.asarray(start, dtype=np.float64)),
                   method="Nelder-Mead",
                   options=dict(maxfev=maxfev, xatol=1e-3, fatol=1e-2))
    wall = time.perf_counter() - t0
    sigf, sign = np.exp(res.x)
    return dict(sigma_f2=float(sigf ** 2), sigma_n2=float(sign ** 2),
               lam=float(sign ** 2 / sigf ** 2), lml=float(-res.fun),
               nfev=res.nfev, wall_s=wall, history=history)


def mle_fit_rkhs(D2_train, y, kind="rbf", start=None, tol=1e-8, maxfev=150,
                 verbose=False):
    """Nelder-Mead over log(ell, sigma_f, sigma_n) maximizing the LML of a
    Gaussian/Matern-3/2 marker kernel (Phase 2's value-add over Phase 1's
    fixed linear GRM). D2_train is the squared-distance matrix
    (`marker_kernel.squared_dist_matrix`), built once per fold, reused for
    every eval -- only the cheap elementwise kernel transform changes.
    """
    y_dev = cp.asarray(y, dtype=cp.float64)
    if start is None:
        ell0 = median_dist_scale(D2_train)
        ystd = float(cp.std(y_dev))
        start = [ell0, ystd, 0.5 * ystd]   # ell, sigma_f, sigma_n
    history = []

    def objective(logp):
        ell, sigf, sign = np.exp(logp)
        try:
            A_base = apply_kernel(D2_train, ell, kind=kind)
            lml, relres = lml_precomputed(A_base, y_dev, sigf ** 2, sign ** 2, tol=tol)
            if relres > 1e-3:
                lml = -PENALTY
        except FactorError:
            lml = -PENALTY
        history.append((ell, sigf, sign, lml))
        if verbose:
            print(f"    eval {len(history):3d}: ell={ell:.4f} sigma_f={sigf:.4f} "
                 f"sigma_n={sign:.5f}  LML={lml: .2f}", flush=True)
        return -lml

    t0 = time.perf_counter()
    res = minimize(objective, np.log(np.asarray(start, dtype=np.float64)),
                   method="Nelder-Mead",
                   options=dict(maxfev=maxfev, xatol=1e-3, fatol=1e-2))
    wall = time.perf_counter() - t0
    ell, sigf, sign = np.exp(res.x)
    return dict(ell=float(ell), sigma_f2=float(sigf ** 2), sigma_n2=float(sign ** 2),
               kind=kind, lml=float(-res.fun), nfev=res.nfev, wall_s=wall,
               history=history)
