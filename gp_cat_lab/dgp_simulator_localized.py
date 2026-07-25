"""Localized-footprint variant of dgp_simulator.py -- a robustness check on
RESULTS_PHASE1.md/RESULTS_PHASE2.md's soft-classifier finding.

dgp_simulator.py's systemic regime elevates and spatially-correlates EVERY
property in the book simultaneously -- which means the classifier's feature
(the book's TOTAL log loss, log(sum_i L_i,t)) is close to a sufficient
statistic for the regime by construction: of course summing catches a
shock that hits the whole book. A real catastrophic event (a wildfire, a
storm's landfall track) typically affects only a geographic SUBSET of a
region-wide book -- diluting the total-loss signal with the majority of
unaffected properties, exactly the failure mode a global-sum classifier is
vulnerable to.

This module keeps dgp_simulator.py's mechanism (regime -> shared spatial
field + severity multiplier) but restricts it to a random circular
"footprint" each systemic year (random epicenter property + a radius
calibrated so `footprint_frac` of the book falls inside it), instead of the
whole region. Properties outside the footprint behave exactly as in a
normal year, even in a "systemic" year -- so at small footprint_frac, the
book's total loss is dominated by the unaffected majority, and a
classifier that only looks at the total should degrade.

footprint_frac=1.0 (the whole book affected, same radius as the book's own
spatial extent) is NOT identical to dgp_simulator.py's original mechanism
(which has no radius cutoff at all, just a smoothly-decaying kernel every
year) -- it's a deliberately close approximation used here as this module's
own "global" baseline, so the footprint_frac sweep is apples-to-apples
within this module rather than exactly reproducing the original numbers.
"""

import numpy as np

DEFAULT_PARAMS = dict(
    p_systemic=1.0 / 15.0,
    regime_severity_mult=6.0,
    idio_sigma=0.5,
    spatial_length_scale_deg=0.5,
    spatial_field_sigma=0.9,
)


def _rbf_kernel(lat, lon, length_scale_deg, variance):
    coords = np.stack([lat, lon], axis=1)
    d2 = ((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1)
    return variance * np.exp(-0.5 * d2 / length_scale_deg ** 2), d2


def sample_true_losses_localized(book, n_years, footprint_frac=1.0, params=None,
                                  seed=0, jitter=1e-9):
    """Same mechanism as dgp_simulator.sample_true_losses, but each
    systemic year's regime shock (severity multiplier + spatial field) is
    restricted to a random circular footprint covering `footprint_frac` of
    the book (a random property as epicenter, radius calibrated from the
    book's own pairwise-distance distribution) instead of the whole book.
    footprint_frac=1.0 -- unrestricted, radius = the book's max pairwise
    distance, every property affected every systemic year.

    Returns dict(losses, regime, affected: (n_years, n) bool -- which
    properties were actually inside the footprint each year, book, params,
    seed, footprint_frac, radius_deg)."""
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    rng = np.random.default_rng(seed)
    n = book["n"]
    mu = book["mu"]
    V = book["insured_value"]

    K_spatial, D2 = _rbf_kernel(book["lat"], book["lon"], p["spatial_length_scale_deg"],
                                 p["spatial_field_sigma"] ** 2)
    L_spatial = np.linalg.cholesky(K_spatial + jitter * np.eye(n))

    # Radius calibration: the footprint_frac-quantile of the book's own
    # pairwise distance distribution -- by definition of a quantile over
    # ALL pairs, a random point has, ON AVERAGE, footprint_frac of the
    # book within that radius.
    dists = np.sqrt(D2[np.triu_indices(n, k=1)])
    radius = float(np.quantile(dists, min(footprint_frac, 1.0))) if footprint_frac < 1.0 \
        else float(dists.max()) + 1e-6

    regime = rng.random(n_years) < p["p_systemic"]
    idio = rng.normal(0.0, p["idio_sigma"], size=(n_years, n))

    n_systemic = int(regime.sum())
    z_field = np.zeros((n_years, n))
    affected = np.zeros((n_years, n), dtype=bool)
    if n_systemic > 0:
        z_raw = rng.standard_normal((n_systemic, n))
        z_field[regime] = z_raw @ L_spatial.T
        epicenters = rng.integers(0, n, size=n_systemic)
        affected[regime] = D2[epicenters, :] <= radius ** 2

    log_ratio = idio - 0.5 * p["idio_sigma"] ** 2
    severity_mult = np.where(affected, p["regime_severity_mult"], 1.0)
    z_applied = np.where(affected, z_field, 0.0)
    loss_ratio = mu[None, :] * severity_mult * np.exp(log_ratio + z_applied)

    losses = loss_ratio * V[None, :]
    return dict(losses=losses, regime=regime, affected=affected, book=book, params=p,
                seed=seed, footprint_frac=footprint_frac, radius_deg=radius)
