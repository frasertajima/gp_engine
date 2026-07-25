"""The oracle: a synthetic annual-loss generator for climate_cat_lab's book,
with genuine (checkable) regime-driven tail dependence -- unlike a plain
multivariate Gaussian/lognormal model. See LAB_PLAN.md's Method section for
the design rationale; this is that design, implemented.

Two-layer process per year:
  1. A latent regime R_t ~ Bernoulli(p_systemic) -- "normal" vs "systemic
     climate-extreme" year (elevated drought/heat/wildfire-season
     conditions, correlated across the region).
  2. Conditional on the regime, each property's loss ratio is a lognormal
     draw around its own baseline mu_i (idiosyncratic in normal years); in
     systemic years, a SHARED spatially-correlated field (an RBF-kernel
     Gaussian process over lat/lon) multiplies every property's severity
     simultaneously, correlated by distance -- nearby properties move
     together, distant ones don't, and only in the years it matters.

Every fitted model in this lab sees only a finite historical-style sample
drawn from `sample_true_losses` -- never these parameters or this mechanism.
The oracle is reserved for scoring (resimulating at the chosen capital
level and reading off the true survival probability) and for Phase 0's
sanity check below.

Entirely synthetic and illustrative -- calibration constants (p_systemic,
regime severity multiplier, kernel length scale) are tunable knobs checked
for producing a real tail-dependence effect (phase0_run.py), not claims
about any real peril's true statistics (LAB_PLAN.md Risks section).
"""

import numpy as np

DEFAULT_PARAMS = dict(
    p_systemic=1.0 / 15.0,        # ~1-in-15 years is a correlated climate-extreme year
    regime_severity_mult=6.0,     # systemic-year severity multiplier over baseline mu_i
    idio_sigma=0.5,               # idiosyncratic lognormal noise (both regimes)
    spatial_length_scale_deg=0.5, # RBF kernel length scale, degrees lat/lon
    spatial_field_sigma=0.9,      # std dev of the systemic-year spatial shock field
)


def _rbf_kernel(lat, lon, length_scale_deg, variance):
    coords = np.stack([lat, lon], axis=1)
    d2 = ((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1)
    return variance * np.exp(-0.5 * d2 / length_scale_deg ** 2)


def sample_true_losses(book, n_years, params=None, seed=0, jitter=1e-9):
    """Returns dict(losses: (n_years, n) dollar losses, regime: (n_years,)
    bool, book=book, params=params, seed=seed) -- the oracle's ground truth."""
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    rng = np.random.default_rng(seed)
    n = book["n"]
    mu = book["mu"]
    V = book["insured_value"]

    K_spatial = _rbf_kernel(book["lat"], book["lon"], p["spatial_length_scale_deg"],
                             p["spatial_field_sigma"] ** 2)
    L_spatial = np.linalg.cholesky(K_spatial + jitter * np.eye(n))

    regime = rng.random(n_years) < p["p_systemic"]
    idio = rng.normal(0.0, p["idio_sigma"], size=(n_years, n))

    n_systemic = int(regime.sum())
    z_field = np.zeros((n_years, n))
    if n_systemic > 0:
        z_raw = rng.standard_normal((n_systemic, n))
        z_field[regime] = z_raw @ L_spatial.T

    # Mean-preserving idiosyncratic noise (E[exp(idio - idio_sigma^2/2)]=1)
    # so normal years average to mu_i. Systemic years add the shared spatial
    # field ON TOP of the regime severity multiplier -- deliberately not
    # mean-corrected for z_field, since systemic years are meant to be both
    # more severe (regime_severity_mult) AND more spatially correlated
    # (z_field), not just noisier.
    log_ratio = idio - 0.5 * p["idio_sigma"] ** 2
    severity_mult = np.where(regime[:, None], p["regime_severity_mult"], 1.0)
    loss_ratio = mu[None, :] * severity_mult * np.exp(log_ratio + z_field)

    losses = loss_ratio * V[None, :]
    return dict(losses=losses, regime=regime, book=book, params=p, seed=seed)
