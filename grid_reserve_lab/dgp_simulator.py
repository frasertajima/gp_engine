"""The oracle: a synthetic per-day fleet-output generator for
grid_reserve_lab's fleet, with genuine (checkable) regime-driven tail
dependence in SHORTFALL (expected minus actual output) -- unlike a plain
multivariate Gaussian/lognormal model. Structural port of
climate_cat_lab/dgp_simulator.py (replicate unit "day" instead of "year",
"resource-drought" regime instead of "systemic climate-extreme" regime,
output shortfall instead of dollar loss) -- see LAB_PLAN.md's Method section
and research/04_dunkelflaute.md for the domain rationale.

Two-layer process per day:
  1. A latent regime R_t ~ Bernoulli(p_drought) -- "normal" vs "resource
     drought" day (a blocking high-pressure system suppressing wind output,
     optionally correlated with low solar via persistent cloud cover,
     across the region).
  2. Conditional on the regime, each site's output ratio (fraction of
     nameplate actually generated) is a lognormal-ish draw around its own
     climatological cf_i (idiosyncratic in normal days); in drought days, a
     SHARED spatially-correlated field (an RBF-kernel Gaussian process over
     lat/lon) depresses every site's output simultaneously, correlated by
     distance -- nearby sites move together, distant ones don't, and only
     on the days it matters.

Every fitted model in this lab sees only a finite historical-style sample
drawn from `sample_true_output` -- never these parameters or this mechanism.
The oracle is reserved for scoring (resimulating at the chosen reserve
level and reading off the true achieved reliability) and for Phase 0's
sanity check below.

Entirely synthetic and illustrative -- calibration constants (p_drought,
drought severity multiplier, kernel length scale) are tunable knobs checked
for producing a real tail-dependence effect (phase0_run.py), not claims
about any real region's true wind/solar statistics (LAB_PLAN.md Risks
section). Drought frequency here is NOT calibrated to the real ERCOT/CAISO
event counts in research/04_dunkelflaute.md -- that calibration is Phase 2's
job, once real NREL/EIA-930 data is in hand; Phase 0 only needs a
mechanism, not a matched frequency.
"""

import numpy as np

DEFAULT_PARAMS = dict(
    p_drought=1.0 / 15.0,           # ~1-in-15 days is a correlated resource-drought day
    drought_output_mult=0.30,       # drought-day output multiplier over baseline cf_i (i.e. -70%)
    idio_sigma=0.35,                # idiosyncratic lognormal-ish noise (both regimes)
    spatial_length_scale_deg=3.0,   # RBF kernel length scale, degrees lat/lon (wind
                                     # correlation decorrelates over a much larger distance
                                     # than climate_cat_lab's property-hazard length scale)
    spatial_field_sigma=1.6,        # std dev of the drought-day spatial shock field (log-space)
)


def _rbf_kernel(lat, lon, length_scale_deg, variance):
    coords = np.stack([lat, lon], axis=1)
    d2 = ((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1)
    return variance * np.exp(-0.5 * d2 / length_scale_deg ** 2)


def sample_true_output(fleet, n_days, params=None, seed=0, jitter=1e-9):
    """Returns dict(output_mw: (n_days, n) actual MW generated, shortfall_mw:
    (n_days, n) expected-minus-actual MW, regime: (n_days,) bool, fleet=fleet,
    params=params, seed=seed) -- the oracle's ground truth."""
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    rng = np.random.default_rng(seed)
    n = fleet["n"]
    cf = fleet["cf"]
    C = fleet["nameplate_mw"]

    K_spatial = _rbf_kernel(fleet["lat"], fleet["lon"], p["spatial_length_scale_deg"],
                             p["spatial_field_sigma"] ** 2)
    L_spatial = np.linalg.cholesky(K_spatial + jitter * np.eye(n))

    regime = rng.random(n_days) < p["p_drought"]
    idio = rng.normal(0.0, p["idio_sigma"], size=(n_days, n))

    n_drought = int(regime.sum())
    z_field = np.zeros((n_days, n))
    if n_drought > 0:
        z_raw = rng.standard_normal((n_drought, n))
        z_field[regime] = z_raw @ L_spatial.T

    # Mean-preserving idiosyncratic noise (E[exp(idio - idio_sigma^2/2)]=1)
    # so normal days average to cf_i. Drought days multiply by
    # drought_output_mult (<1, a real reduction) AND add the shared spatial
    # field ON TOP -- deliberately not mean-corrected for z_field, since
    # drought days are meant to be both more severe (drought_output_mult)
    # AND more spatially correlated (z_field), not just noisier. z_field can
    # push output ratio above 1.0 in rare cases within a drought day's own
    # noise -- clipped below, same treatment climate_cat_lab gives losses
    # (clipped at zero instead).
    log_ratio = idio - 0.5 * p["idio_sigma"] ** 2
    severity_mult = np.where(regime[:, None], p["drought_output_mult"], 1.0)
    output_ratio = cf[None, :] * severity_mult * np.exp(log_ratio + z_field)
    output_ratio = np.clip(output_ratio, 0.0, 1.0)

    output_mw = output_ratio * C[None, :]
    expected_mw = cf[None, :] * C[None, :]
    # One-sided: reserves respond to underperformance, not overperformance.
    # (Signed expected-minus-actual is ~zero-mean on normal days by
    # construction -- a well-behaved forecast error -- which let the
    # drought-day regime jump swamp the spatial-decay signal entirely in
    # early testing: near- and far-pair unconditional correlation came out
    # statistically indistinguishable, ~0.19 vs ~0.17, because the shared
    # regime dummy dominated total variance regardless of distance. Clipping
    # to the positive part gives normal days a real, nonzero baseline
    # shortfall -- the same structural role climate_cat_lab's mu_i baseline
    # loss ratio plays -- so distance decay is measurable against a
    # comparable-scale noise floor instead of a near-zero one.)
    signed_shortfall_mw = expected_mw - output_mw
    shortfall_mw = np.maximum(signed_shortfall_mw, 0.0)

    return dict(output_mw=output_mw, shortfall_mw=shortfall_mw,
                signed_shortfall_mw=signed_shortfall_mw, regime=regime,
                fleet=fleet, params=p, seed=seed)
