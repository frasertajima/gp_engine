"""Large-N oracle generator for Phase 2 -- the SAME generative process as
dgp_simulator.py (regime + spatial-shock lognormal loss model), scaled to
n=45,000 using rff_sampler.py's approximate spatial field instead of
dgp_simulator.py's exact dense Cholesky (infeasible at this n: a dense n x
n covariance is >16GB and its factorization is O(n^3) -- see
RESULTS_PHASE2.md for the measured cost). VALIDATED against
dgp_simulator.py's exact version at Phase 0's n=500 scale
(phase2_rff_validation.py) before being trusted here.

Two entry points, because the two things this lab needs from the oracle
have very different memory profiles:
- `sample_true_losses_full`: full (n_years, n) per-property detail, for the
  HISTORICAL sample every fitted method sees. n_years stays small here
  (~25), so the full matrix is tiny (25*45,000*8 bytes ~9MB) regardless.
- `sample_true_totals`: TOTAL BOOK LOSS PER YEAR only, streamed and reduced
  batch-by-batch, never materializing the full (n_years, n) matrix -- at
  n=45,000 and the ~100,000 years needed for a stable 99.5% quantile
  estimate, that matrix would be 45,000*100,000*8 bytes = 36GB, far more
  than anything in this lab actually uses (every capital/survival
  calculation here operates on the aggregate total, per capital_calc.py).
"""

import numpy as np

from dgp_simulator import DEFAULT_PARAMS
from rff_sampler import rff_features


def _draw_batch(rng, phi, mu, V, regime_batch, p, n_features):
    bsize = len(regime_batch)
    n = mu.shape[0]
    idio = rng.normal(0.0, p["idio_sigma"], size=(bsize, n))
    log_ratio = idio - 0.5 * p["idio_sigma"] ** 2

    n_sys = int(regime_batch.sum())
    z_field = np.zeros((bsize, n))
    if n_sys > 0:
        z_m = rng.standard_normal((n_sys, n_features))
        z_field[regime_batch] = np.sqrt(p["spatial_field_sigma"] ** 2) * (z_m @ phi.T)

    severity_mult = np.where(regime_batch[:, None], p["regime_severity_mult"], 1.0)
    loss_ratio = mu[None, :] * severity_mult * np.exp(log_ratio + z_field)
    return loss_ratio * V[None, :]


def sample_true_losses_full(book, n_years, params=None, seed=0, n_features=800):
    """Same return shape as dgp_simulator.sample_true_losses (losses,
    regime, book, params, seed), for a small n_years -- the historical
    sample every fitted method is allowed to see."""
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    rng = np.random.default_rng(seed)
    coords = np.stack([book["lat"], book["lon"]], axis=1)
    phi = rff_features(coords, p["spatial_length_scale_deg"], n_features, seed=0)

    regime = rng.random(n_years) < p["p_systemic"]
    losses = _draw_batch(rng, phi, book["mu"], book["insured_value"], regime, p, n_features)
    return dict(losses=losses, regime=regime, book=book, params=p, seed=seed)


def sample_true_totals(book, n_years, params=None, seed=0, n_features=800,
                        batch_years=2000):
    """TOTAL book loss per year only (n_years,) plus the regime flags --
    the oracle ground truth used for scoring, at a scale where storing
    every property's every year is neither needed nor feasible."""
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    rng = np.random.default_rng(seed)
    coords = np.stack([book["lat"], book["lon"]], axis=1)
    phi = rff_features(coords, p["spatial_length_scale_deg"], n_features, seed=0)

    regime = rng.random(n_years) < p["p_systemic"]
    totals = np.empty(n_years)
    for start in range(0, n_years, batch_years):
        end = min(start + batch_years, n_years)
        batch = _draw_batch(rng, phi, book["mu"], book["insured_value"],
                             regime[start:end], p, n_features)
        totals[start:end] = batch.sum(axis=1)

    return dict(totals=totals, regime=regime, book=book, params=p, seed=seed)
