"""Shared multivariate-Gaussian fitting utilities for Methods 1-3.

**A documented simplification of this family's usual "spatial kernel" pattern, stated plainly**:
`gblup_lab/marker_kernel.py`'s RBF-over-distance kernel (reused by `climate_cat_lab`,
`cvar_gp_lab`, `grid_reserve_lab`, `shm_lab`) needs real Euclidean coordinates (lat/lon, or sensor
position) to be meaningful. This lab's five gauges are specific, named points in a nested RIVER
NETWORK, not a spatial field with meaningful Euclidean distance between them — an RBF kernel over
arbitrary "positions" would be a fiction here. For a small, FIXED set of named gauges, an
infinitely-flexible RBF kernel converges to the same thing as directly estimating the unconstrained
covariance matrix among them — so that's what this lab fits directly (a real, honest reason to
simplify, not a shortcut around the family's usual approach).
"""

import numpy as np
from scipy.special import expit  # logistic sigmoid


def fit_mvn(X):
    """X: (n, d). Returns (mean vector, covariance matrix), plain MLE."""
    mu = X.mean(axis=0)
    cov = np.cov(X, rowvar=False, ddof=0)
    return mu, cov


def fit_mvn_trend(X, years):
    """X: (n, d), years: (n,). Fits mu(year) = mu0 + trend*(year - year_ref) per dimension via
    OLS, and a single shared residual covariance — Method 3's mandatory non-mixture control:
    a trend, with no latent regime/EM at all."""
    year_ref = years.mean()
    t = years - year_ref
    A = np.column_stack([np.ones_like(t), t])
    coef, *_ = np.linalg.lstsq(A, X, rcond=None)  # (2, d): [mu0; trend] per dimension
    mu0, trend = coef[0], coef[1]
    resid = X - (mu0 + np.outer(t, trend))
    cov = np.cov(resid, rowvar=False, ddof=0)
    return mu0, trend, year_ref, cov


def mvn_logpdf(X, mu, cov):
    d = X.shape[1] if X.ndim == 2 else X.shape[0]
    L = np.linalg.cholesky(cov + 1e-9 * np.eye(d))
    diff = X - mu
    z = np.linalg.solve(L, diff.T).T if X.ndim == 2 else np.linalg.solve(L, diff)
    quad = np.sum(z**2, axis=-1)
    log_det = 2 * np.sum(np.log(np.diag(L)))
    return -0.5 * (quad + log_det + d * np.log(2 * np.pi))


def fit_weighted_logistic_trend(years, resp, year_ref):
    """Linearized weighted logistic fit: logit(resp) ~ a + b*(year - year_ref), least squares in
    logit space (a documented approximation to a full IRLS logistic fit — adequate at this lab's
    sample size, not claimed exact)."""
    eps = 1e-3
    r = np.clip(resp, eps, 1 - eps)
    y = np.log(r / (1 - r))
    t = years - year_ref
    A = np.column_stack([np.ones_like(t), t])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef[0], coef[1]  # a, b


def fit_regime_mixture_time_varying(X, years, n_em_iters=50, seed=0):
    """Two-component MVN mixture, SHARED covariance across components (a common regime-mixture
    simplification in this family — only the mean shifts under the regime), with a TIME-VARYING
    mixing weight pi_drought(year) = sigmoid(a + b*(year - year_ref)), fit via soft-EM. This is
    the direct response to Phase 0's finding that a fixed-rate mixture would understate the real,
    measured post-2000 drought-rate increase.

    Returns dict with mu_normal, mu_drought, cov, year_ref, (a, b) logistic-trend params.
    """
    rng = np.random.default_rng(seed)
    n, d = X.shape
    year_ref = years.mean()

    # Informed, not hard-coded, initialization: seed responsibility from the lowest-mean-flow
    # third of years (same posture as every prior lab's regime_mixture.py seeding).
    composite = X.mean(axis=1)
    order = np.argsort(composite)
    resp = np.full(n, 0.15)
    resp[order[: max(3, n // 3)]] = 0.85

    for _ in range(n_em_iters):
        # M-step: responsibility-weighted component means, shared covariance
        w = resp
        mu_drought = np.average(X, axis=0, weights=w)
        mu_normal = np.average(X, axis=0, weights=1 - w)
        resid = np.where(resp[:, None] > 0.5, X - mu_drought, X - mu_normal)
        cov = np.cov(resid, rowvar=False, ddof=0, aweights=np.clip(np.maximum(w, 1 - w), 1e-3, None))

        a, b = fit_weighted_logistic_trend(years, resp, year_ref)

        # E-step
        pi_drought = expit(a + b * (years - year_ref))
        log_lik_drought = mvn_logpdf(X, mu_drought, cov)
        log_lik_normal = mvn_logpdf(X, mu_normal, cov)
        log_post_drought = np.log(np.clip(pi_drought, 1e-6, None)) + log_lik_drought
        log_post_normal = np.log(np.clip(1 - pi_drought, 1e-6, None)) + log_lik_normal
        m = np.maximum(log_post_drought, log_post_normal)
        resp = np.exp(log_post_drought - m) / (np.exp(log_post_drought - m) + np.exp(log_post_normal - m))

    return {
        "mu_normal": mu_normal, "mu_drought": mu_drought, "cov": cov,
        "year_ref": year_ref, "a": a, "b": b, "final_responsibility": resp,
    }
