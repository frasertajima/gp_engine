"""Methods 1 and 2 of climate_cat_lab's four-method ladder (LAB_PLAN.md's
Method section) -- the two real-world shortcuts this lab targets:
independence (no correlation at all) and flat/block correlation (a single
number, the actuarial-capital-model shortcut confirmed as real, cross-
industry practice at three independent frameworks in
research/01_solvency_ii_correlation.md and research/02_rating_agency_capital_models.md).

Both work in LOG loss-RATIO space (log(loss/insured_value)). The DGP's own
multiplicative structure (dgp_simulator.py) makes residuals homoscedastic
in log space regardless of a property's insured value, so fitting log-
ratios keeps "spatial/regime structure" cleanly separated from "how big is
this property's policy," which lat/lon alone doesn't explain.
"""

import numpy as np


def _log_loss_ratio(losses, book):
    return np.log(losses / book["insured_value"][None, :])


def fit_independence(losses, book):
    """Per-property marginal lognormal fit: mean and std of each property's
    own historical log loss-ratio series. No cross-property structure at
    all -- portfolio total loss has a thin (CLT) tail by construction."""
    log_ratio = _log_loss_ratio(losses, book)
    mu = log_ratio.mean(axis=0)
    sigma = log_ratio.std(axis=0, ddof=1)
    return dict(mu=mu, sigma=sigma, n=book["n"])


def sample_independence_scenarios(fit, insured_value, n_scenarios, seed=0):
    rng = np.random.default_rng(seed)
    n = fit["n"]
    z = rng.standard_normal((n_scenarios, n))
    log_ratio = fit["mu"][None, :] + fit["sigma"][None, :] * z
    return np.exp(log_ratio) * insured_value[None, :]


def fit_flat_correlation(losses, book, n_sample_pairs=2000, seed=0):
    """Same per-property marginals as fit_independence, plus ONE flat
    pairwise correlation number -- the average sample correlation across
    many property pairs, not a full n x n sample covariance (which would be
    hopelessly underdetermined at n_years << n_properties -- exactly the
    reason a real capital model uses a single coarse correlation factor
    instead, per the research citations above)."""
    log_ratio = _log_loss_ratio(losses, book)
    mu = log_ratio.mean(axis=0)
    sigma = log_ratio.std(axis=0, ddof=1)

    n = book["n"]
    rng = np.random.default_rng(seed)
    i_idx, j_idx = np.triu_indices(n, k=1)
    k = min(n_sample_pairs, len(i_idx))
    pick = rng.choice(len(i_idx), size=k, replace=False)
    corrs = [np.corrcoef(log_ratio[:, i], log_ratio[:, j])[0, 1]
             for i, j in zip(i_idx[pick], j_idx[pick])]
    # Clipped to [0, 0.99], not [-0.99, 0.99]: a real flat-correlation capital
    # model always uses a non-negative correlation assumption (the DGP's own
    # comovement is positive, and every real-world example found in
    # research/01-02 -- Solvency II, BCAR, S&P's 100%-correlated Nat Cat --
    # is non-negative by construction; a single-factor model, used below,
    # requires it too).
    rho = float(np.clip(np.nanmean(corrs), 0.0, 0.99))
    return dict(mu=mu, sigma=sigma, rho=rho, n=n)


def sample_flat_correlation_scenarios(fit, insured_value, n_scenarios, seed=0):
    """Single-common-factor sampler: z_i = sqrt(rho)*f + sqrt(1-rho)*e_i,
    f~N(0,1) shared, e_i~N(0,1) idiosyncratic -- gives EXACTLY corr(z_i,z_j)
    = rho for every pair i!=j, var(z_i)=1, no approximation. Mathematically
    equivalent to the dense-Cholesky equicorrelation sample the small-scale
    (Phase 1) version used, but O(n) instead of O(n^2) memory / O(n^3)
    compute -- this is the standard actuarial way a real flat/single-factor
    correlation model is implemented in practice (the same single-systematic-
    factor structure behind CreditMetrics/Vasicek-style capital models), not
    a new approximation introduced for this lab's convenience."""
    rng = np.random.default_rng(seed)
    n = fit["n"]
    rho = fit["rho"]
    f = rng.standard_normal((n_scenarios, 1))
    e = rng.standard_normal((n_scenarios, n))
    z = np.sqrt(rho) * f + np.sqrt(max(1.0 - rho, 0.0)) * e
    log_ratio = fit["mu"][None, :] + fit["sigma"][None, :] * z
    return np.exp(log_ratio) * insured_value[None, :]
