"""Method 3 (vanilla spatial GP) of climate_cat_lab's four-method ladder.

Fits a spatial kernel over exposure lat/lon to the historical sample's
per-year LOG loss-ratio residuals (after removing each property's own
historical mean -- the same per-property demeaning naive_baselines.py's
independence fit already computes), treating the n_years historical
residual vectors as repeated i.i.d. draws from one shared spatial
covariance N(0, sigma_f2*A_base(ell) + sigma_n2*I).

This is new work, not present in gp_core.py/gp_hyperopt.py/gblup_hyperopt.py
or cvar_gp_lab's mle_fit_rkhs_mean: those all fit ONE target vector's
marginal likelihood. This is a REPEATED-MEASURES marginal likelihood over
many i.i.d. draws from the same covariance (year 1's residual vector, year
2's, ... all drawn from the same n-property spatial field) -- the standard
way to estimate a spatial random field's covariance parameters from
replicated realizations, needed here because n_years (~60) << n_properties
(500): a full empirical n x n sample covariance would be hopelessly
underdetermined (see naive_baselines.py's flat-correlation module for the
same reason that shortcut uses one number instead), but a 2-3 hyperparameter
kernel is not.

Still jointly Gaussian (a fitted spatial covariance, sampled as a
multivariate normal) -- this method's whole point, per LAB_PLAN.md's core
hypothesis, is testing whether a BETTER-SHAPED correlation structure (real
distance decay, not a flat number) closes most of the capital-sizing gap on
its own, before regime_mixture.py's method 4 tests whether genuine tail
dependence needs to be modeled explicitly on top of it.
"""

import math
import os
import sys
import time

import cupy as cp
import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from gp_core import FactorError, PrecomputedKernel, potrf_inplace, spd_solve_ir  # noqa: E402

from spatial_kernel import apply_kernel, median_dist_scale, squared_dist_matrix  # noqa: E402

PENALTY = 1e12
LOG2PI = math.log(2.0 * math.pi)


def _log_loss_ratio(losses, book):
    return np.log(losses / book["insured_value"][None, :])


def _repeated_measures_lml(A_base_dev, R_dev, sigma_f2, sigma_n2, tol=1e-6, max_ir=8):
    """Sum of per-year LML under a SHARED covariance K = sigma_f2*A_base +
    sigma_n2*I. Factors K ONCE (one potrf), then IR-solves each year's
    residual vector against that same FP32 factor via spd_solve_ir (n_years
    potrs-based solves, not n_years separate factorizations)."""
    n = A_base_dev.shape[0]
    n_years = R_dev.shape[0]
    kern = PrecomputedKernel(A_base_dev, sigma_f2=sigma_f2, sigma_n2=sigma_n2)
    K32 = cp.empty((n, n), dtype=cp.float32, order="F")
    kern.build(None, K32)
    logdet = potrf_inplace(K32)

    dummy_X = cp.zeros((n, 1))
    total_quad = 0.0
    worst_relres = 0.0
    all_ok = True
    for t in range(n_years):
        y_t = R_dev[t]
        alpha, relres, n_ir, ok = spd_solve_ir(K32, kern, dummy_X, y_t, tol=tol, max_ir=max_ir)
        total_quad += float(y_t @ alpha)
        worst_relres = max(worst_relres, relres)
        all_ok = all_ok and ok

    lml = -0.5 * total_quad - 0.5 * n_years * logdet - 0.5 * n_years * n * LOG2PI
    return lml, worst_relres, all_ok


def _repeated_measures_lml_weighted(A_base_dev, R_dev, weights, sigma_f2, sigma_n2,
                                     tol=1e-6, max_ir=8):
    """Same as _repeated_measures_lml, but each year t contributes weight[t]
    to the quadratic-form sum and to the effective year count used in the
    logdet/normalization terms -- the weighted-MLE generalization needed to
    fit a component's covariance under SOFT (responsibility-weighted, not
    hard-partitioned) regime membership. weight[t] in [0, 1]; hard 0/1
    weights reduce this exactly to _repeated_measures_lml on the selected
    subset."""
    n = A_base_dev.shape[0]
    n_years = R_dev.shape[0]
    kern = PrecomputedKernel(A_base_dev, sigma_f2=sigma_f2, sigma_n2=sigma_n2)
    K32 = cp.empty((n, n), dtype=cp.float32, order="F")
    kern.build(None, K32)
    logdet = potrf_inplace(K32)

    dummy_X = cp.zeros((n, 1))
    total_quad = 0.0
    worst_relres = 0.0
    all_ok = True
    for t in range(n_years):
        y_t = R_dev[t]
        alpha, relres, n_ir, ok = spd_solve_ir(K32, kern, dummy_X, y_t, tol=tol, max_ir=max_ir)
        total_quad += float(weights[t]) * float(y_t @ alpha)
        worst_relres = max(worst_relres, relres)
        all_ok = all_ok and ok

    eff_n = float(np.sum(weights))
    lml = -0.5 * total_quad - 0.5 * eff_n * logdet - 0.5 * eff_n * n * LOG2PI
    return lml, worst_relres, all_ok


def mle_fit_spatial_weighted(coords, R, weights, kind="rbf", start=None, tol=1e-6,
                              maxfev=150, verbose=False, var_cap_mult=5.0, ref_var=None):
    """Weighted counterpart of mle_fit_spatial -- see
    _repeated_measures_lml_weighted. `weights` is (n_years,), typically a
    GaussianMixture component's posterior responsibility per year.

    `ref_var`, if given (fit_gp_loss_model_weighted passes it), anchors the
    numerical safety cap below to a stable reference computed from the
    UNWEIGHTED mean, independent of `weights`'/R's own concentration --
    see that function's docstring for why R's own std is NOT a safe anchor
    here. Falls back to std(R) when called standalone without it."""
    D2 = squared_dist_matrix(coords)
    R_dev = cp.asarray(R, dtype=cp.float64)
    weights = np.asarray(weights, dtype=np.float64)

    # Weighted variance, for the Nelder-Mead start point ONLY -- when
    # responsibility concentrates almost entirely on one year (common at
    # small n_years with few true-systemic years), the weighted residual
    # variance collapses toward 0 (that year's own weighted-mean residual
    # is ~0 by construction), sending log(rstd) to -inf. Floor at the
    # UNWEIGHTED residual std, a sane order-of-magnitude reference
    # regardless of weight concentration.
    rstd_weighted = float(np.sqrt(np.average(R ** 2, axis=0, weights=weights).mean()))
    rstd_unweighted = float(np.std(R))
    rstd = rstd_weighted if rstd_weighted > 1e-6 * rstd_unweighted else rstd_unweighted
    # Numerical safety net, not a scientific prior: caps the fitted marginal
    # variance (sigma_f2+sigma_n2) at var_cap_mult x a reference variance
    # -- measured stable (~0.35-0.67) across every seed tried here when
    # anchored on the UNWEIGHTED-mean residual (ref_var). Nelder-Mead can
    # occasionally (rarely -- not deterministically; most thin-effective-
    # sample fits land fine) wander into a degenerate high-variance basin
    # that spuriously improves the weighted LML on a thin effective sample
    # -- observed directly in this lab (sigma_f2=15.8, ~45x the reference
    # variance, vs. every healthy fit tried staying under ~2.5x; see
    # RESULTS_ROBUSTNESS.md).
    var_cap = var_cap_mult * (ref_var if ref_var is not None else rstd_unweighted ** 2)

    if start is None:
        ell0 = median_dist_scale(D2)
        start = np.log(np.asarray([ell0, 0.7 * rstd, 0.7 * rstd], dtype=np.float64))

    history = []

    def objective(p):
        log_ell, log_sigf, log_sign = p
        ell, sigf, sign = np.exp([log_ell, log_sigf, log_sign])
        if sigf ** 2 + sign ** 2 > var_cap:
            lml = -PENALTY
        else:
            try:
                A_base = apply_kernel(D2, ell, kind=kind)
                lml, relres, ok = _repeated_measures_lml_weighted(
                    A_base, R_dev, weights, sigf ** 2, sign ** 2, tol=tol)
                if not ok or relres > 1e-2:
                    lml = -PENALTY
            except FactorError:
                lml = -PENALTY
        history.append((ell, sigf, sign, lml))
        if verbose:
            print(f"    eval {len(history):3d}: ell={ell:.4f} sigma_f={sigf:.5f} "
                  f"sigma_n={sign:.5f}  LML={lml: .2f}", flush=True)
        return -lml

    t0 = time.perf_counter()
    res = minimize(objective, start, method="Nelder-Mead",
                    options=dict(maxfev=maxfev, xatol=1e-3, fatol=1e-1))
    wall = time.perf_counter() - t0
    log_ell, log_sigf, log_sign = res.x
    ell, sigf, sign = np.exp([log_ell, log_sigf, log_sign])
    return dict(ell=float(ell), sigma_f2=float(sigf ** 2), sigma_n2=float(sign ** 2),
                kind=kind, lml=float(-res.fun), nfev=res.nfev, wall_s=wall)


def fit_gp_loss_model_weighted(losses, book, weights, kind="rbf", mle=None):
    """Weighted counterpart of fit_gp_loss_model: per-property mean and
    spatial-kernel MLE both weighted by `weights` (n_years,) instead of
    fit on a hard year subset. Used by regime_mixture.fit_regime_mixture_soft
    so each component's covariance is fit under soft (responsibility-
    weighted) regime membership rather than a hard stress/normal split."""
    log_ratio = _log_loss_ratio(losses, book)
    w = np.asarray(weights, dtype=np.float64)
    mu = np.average(log_ratio, axis=0, weights=w)
    R = log_ratio - mu[None, :]
    # Reference variance for mle_fit_spatial_weighted's numerical safety
    # cap, computed from the UNWEIGHTED mean (stable regardless of how
    # concentrated `weights` is) -- NOT from R above, whose own std is
    # contaminated by the same degeneracy the cap needs to catch when
    # `weights` concentrates on very few years (R's mean is then that thin
    # subset's own atypical mean, inflating R's unweighted variance right
    # when the cap most needs a stable reference; see RESULTS_ROBUSTNESS.md).
    ref_var = float(np.var(log_ratio - log_ratio.mean(axis=0)))

    coords = np.stack([book["lat"], book["lon"]], axis=1)
    if mle is None:
        mle = mle_fit_spatial_weighted(coords, R, w, kind=kind, ref_var=ref_var)
    D2 = squared_dist_matrix(coords)
    A_base = cp.asnumpy(apply_kernel(D2, mle["ell"], kind=kind))
    return dict(mu=mu, mle=mle, A_base=A_base, sigma_f2=mle["sigma_f2"],
                sigma_n2=mle["sigma_n2"], n=book["n"])


def mle_fit_spatial(coords, R, kind="rbf", start=None, tol=1e-6, maxfev=150, verbose=False,
                     var_cap_mult=5.0):
    """Nelder-Mead over (log ell, log sigma_f, log sigma_n) maximizing the
    repeated-measures LML of a spatial kernel over `coords` (n,2) against R
    (n_years,n) i.i.d. residual draws. Returns dict(ell, sigma_f2, sigma_n2,
    kind, lml, nfev, wall_s)."""
    D2 = squared_dist_matrix(coords)
    R_dev = cp.asarray(R, dtype=cp.float64)
    rstd = float(np.std(R))
    # See mle_fit_spatial_weighted's matching comment -- same numerical
    # safety net against a runaway Nelder-Mead variance, applied here for
    # consistency even though it was only observed to bind in the weighted
    # (thin effective sample) case.
    var_cap = var_cap_mult * rstd ** 2

    if start is None:
        ell0 = median_dist_scale(D2)
        start = np.log(np.asarray([ell0, 0.7 * rstd, 0.7 * rstd], dtype=np.float64))

    history = []

    def objective(p):
        log_ell, log_sigf, log_sign = p
        ell, sigf, sign = np.exp([log_ell, log_sigf, log_sign])
        if sigf ** 2 + sign ** 2 > var_cap:
            lml = -PENALTY
        else:
            try:
                A_base = apply_kernel(D2, ell, kind=kind)
                lml, relres, ok = _repeated_measures_lml(A_base, R_dev, sigf ** 2, sign ** 2, tol=tol)
                if not ok or relres > 1e-2:
                    lml = -PENALTY
            except FactorError:
                lml = -PENALTY
        history.append((ell, sigf, sign, lml))
        if verbose:
            print(f"    eval {len(history):3d}: ell={ell:.4f} sigma_f={sigf:.5f} "
                  f"sigma_n={sign:.5f}  LML={lml: .2f}", flush=True)
        return -lml

    t0 = time.perf_counter()
    res = minimize(objective, start, method="Nelder-Mead",
                    options=dict(maxfev=maxfev, xatol=1e-3, fatol=1e-1))
    wall = time.perf_counter() - t0
    log_ell, log_sigf, log_sign = res.x
    ell, sigf, sign = np.exp([log_ell, log_sigf, log_sign])
    return dict(ell=float(ell), sigma_f2=float(sigf ** 2), sigma_n2=float(sign ** 2),
                kind=kind, lml=float(-res.fun), nfev=res.nfev, wall_s=wall)


def fit_gp_loss_model(losses, book, kind="rbf", mle=None):
    """End-to-end: per-property mean (same demeaning as
    naive_baselines.fit_independence), spatial kernel MLE over the
    historical residuals, and the fitted covariance for scenario sampling.
    Returns dict(mu, mle, A_base, sigma_f2, sigma_n2, n)."""
    log_ratio = _log_loss_ratio(losses, book)
    mu = log_ratio.mean(axis=0)
    R = log_ratio - mu[None, :]

    coords = np.stack([book["lat"], book["lon"]], axis=1)
    if mle is None:
        mle = mle_fit_spatial(coords, R, kind=kind)
    D2 = squared_dist_matrix(coords)
    A_base = cp.asnumpy(apply_kernel(D2, mle["ell"], kind=kind))
    return dict(mu=mu, mle=mle, A_base=A_base, sigma_f2=mle["sigma_f2"],
                sigma_n2=mle["sigma_n2"], n=book["n"])


def sample_gp_scenarios(fit, insured_value, n_scenarios, seed=0, jitter=1e-9):
    """Same shape as cvar_gp_lab/scenario_gen_gp.sample_gp_scenarios: a
    plain host-side Cholesky sample from the fitted covariance -- at this
    problem size (n ~ 500) there's no dense-solve cost worth MPDOK's
    engine, same reasoning as that module's own docstring."""
    n = fit["n"]
    cov = fit["sigma_f2"] * fit["A_base"] + fit["sigma_n2"] * np.eye(n)
    cov = 0.5 * (cov + cov.T)
    L = np.linalg.cholesky(cov + jitter * np.eye(n))
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n_scenarios, n)) @ L.T
    log_ratio = fit["mu"][None, :] + z
    return np.exp(log_ratio) * insured_value[None, :]
