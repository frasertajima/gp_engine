"""Method 3 (vanilla spatial GP) of grid_reserve_lab's five-method ladder.

Fits a spatial kernel over fleet site lat/lon to the historical sample's
per-day shortfall residuals (after removing each site's own historical
mean), treating the n_days historical residual vectors as repeated i.i.d.
draws from one shared spatial covariance N(0, sigma_f2*A_base(ell) +
sigma_n2*I) -- the identical repeated-measures marginal-likelihood idea
climate_cat_lab/gp_loss_model.py built (needed because n_days << n_sites,
same reasoning as that module's docstring). `mle_fit_spatial` /
`mle_fit_spatial_weighted` are reused directly from climate_cat_lab (cross-
lab import, the same move spatial_kernel.py already makes for
gblup_lab/marker_kernel.py) -- they're generic over (coords, R, kind) and
don't know or care whether R is log-loss-ratio residuals or raw-MW
shortfall residuals.

Works in RAW MW units, not log-ratio space (see naive_baselines.py's
docstring for why: dgp_simulator.py's shortfall is one-sided/zero-inflated,
which breaks a clean lognormal treatment climate_cat_lab's always-positive
dollar losses supported). Still jointly Gaussian -- this method's whole
point, per LAB_PLAN.md's core hypothesis, is testing whether a
BETTER-SHAPED (but still elliptical) spatial correlation structure closes
most of the reserve-sizing gap between method 2's real-but-coarse practice
and the truth, before regime_mixture.py's method 4 tests whether genuine
tail dependence needs to be modeled explicitly on top of it.
"""

import os
import sys

import cupy as cp
import numpy as np


# append, not insert(0, ...): climate_cat_lab has its own same-named
# `regime_mixture.py` (and this repo's convention elsewhere uses insert(0,
# ...), which shadowed grid_reserve_lab's OWN regime_mixture.py the first
# time this ran -- appending keeps the local directory's modules
# taking precedence, only falling back to climate_cat_lab for names that
# don't exist locally (mle_fit_spatial/mle_fit_spatial_weighted here).
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "climate_cat_lab"))
from gp_loss_model import mle_fit_spatial, mle_fit_spatial_weighted  # noqa: E402

from spatial_kernel import apply_kernel, squared_dist_matrix  # noqa: E402


def fit_gp_shortfall_model(shortfall, fleet, kind="rbf", mle=None):
    """End-to-end: per-site mean, spatial kernel MLE over the historical
    residuals, and the fitted covariance for scenario sampling. Returns
    dict(mu, mle, A_base, sigma_f2, sigma_n2, n)."""
    mu = shortfall.mean(axis=0)
    R = shortfall - mu[None, :]

    coords = np.stack([fleet["lat"], fleet["lon"]], axis=1)
    if mle is None:
        mle = mle_fit_spatial(coords, R, kind=kind)
    D2 = squared_dist_matrix(coords)
    A_base = cp.asnumpy(apply_kernel(D2, mle["ell"], kind=kind))
    return dict(mu=mu, mle=mle, A_base=A_base, sigma_f2=mle["sigma_f2"],
                sigma_n2=mle["sigma_n2"], n=fleet["n"])


def fit_gp_shortfall_model_weighted(shortfall, fleet, weights, kind="rbf", mle=None):
    """Weighted counterpart, used by regime_mixture.py's soft-EM fit: each
    day contributes to the per-site mean and the spatial-kernel LML
    weighted by `weights` (n_days,) -- a GaussianMixture component's
    posterior responsibility -- instead of a hard stress/normal split."""
    w = np.asarray(weights, dtype=np.float64)
    mu = np.average(shortfall, axis=0, weights=w)
    R = shortfall - mu[None, :]
    # Reference variance for mle_fit_spatial_weighted's numerical safety
    # cap, computed from the UNWEIGHTED mean -- stable regardless of how
    # concentrated `weights` is, same reasoning as climate_cat_lab's
    # fit_gp_loss_model_weighted (RESULTS_ROBUSTNESS.md).
    ref_var = float(np.var(shortfall - shortfall.mean(axis=0)))

    coords = np.stack([fleet["lat"], fleet["lon"]], axis=1)
    if mle is None:
        mle = mle_fit_spatial_weighted(coords, R, w, kind=kind, ref_var=ref_var)
    D2 = squared_dist_matrix(coords)
    A_base = cp.asnumpy(apply_kernel(D2, mle["ell"], kind=kind))
    return dict(mu=mu, mle=mle, A_base=A_base, sigma_f2=mle["sigma_f2"],
                sigma_n2=mle["sigma_n2"], n=fleet["n"])


def sample_gp_scenarios(fit, n_scenarios, seed=0, jitter=1e-9):
    """Plain host-side Cholesky sample from the fitted covariance -- at this
    problem size (n ~ 100) there's no dense-solve cost worth MPDOK's engine,
    same reasoning as cvar_gp_lab/climate_cat_lab's own scenario samplers.
    Clipped at 0 -- shortfall can't be negative, the same domain constraint
    naive_baselines.py's Monte Carlo methods enforce."""
    n = fit["n"]
    cov = fit["sigma_f2"] * fit["A_base"] + fit["sigma_n2"] * np.eye(n)
    cov = 0.5 * (cov + cov.T)
    L = np.linalg.cholesky(cov + jitter * np.eye(n))
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n_scenarios, n)) @ L.T
    draws = fit["mu"][None, :] + z
    return np.clip(draws, 0.0, None)
