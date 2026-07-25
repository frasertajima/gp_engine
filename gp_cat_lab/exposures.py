"""Synthetic exposure book: n insured properties with location, insured
value, and a smooth spatial hazard surface -- the input to dgp_simulator.py's
oracle loss generator. Entirely synthetic (LAB_PLAN.md's Risks section);
values are illustrative, calibrated to real published benchmarks where one
exists (see research/06_book_size_benchmarks.md for the $300-400k average
insured value anchor), not fit to any real book or jurisdiction.
"""

import numpy as np

# An illustrative rectangular coastal-exposure region, degrees lat/lon,
# roughly the footprint of a single US state's coastline. Not tied to any
# real jurisdiction -- Phase 3 (stretch) swaps this for real FEMA NRI
# geography while keeping losses synthetic (LAB_PLAN.md).
LAT_RANGE = (25.0, 27.0)
LON_RANGE = (-82.0, -79.0)

# $300-400k average insured (dwelling) value -- four independent consumer-
# data sources converge here (research/06_book_size_benchmarks.md).
# Lognormal so a few high-value properties exist without a hard cap.
MEAN_INSURED_VALUE = 350_000.0
INSURED_VALUE_CV = 0.4  # coefficient of variation

# Baseline annual expected loss ratio (expected loss / insured value) at the
# region's LEAST hazardous edge -- illustrative, not fit to any real book;
# scaled up toward the coast by COASTAL_LOSS_RATIO_MULT below.
BASE_LOSS_RATIO = 0.0015  # 0.15%/year at the low-hazard edge
COASTAL_LOSS_RATIO_MULT = 4.0  # up to 4x at the high-hazard (coastal) edge


def build_book(n, seed=0, lat_range=LAT_RANGE, lon_range=LON_RANGE):
    """Returns dict(lat, lon, insured_value, mu, n, seed). mu is each
    property's baseline (normal-year) expected annual loss ratio, from a
    smooth hazard surface that increases toward the region's eastern
    (coastal) edge -- a stand-in for real hazard geography."""
    rng = np.random.default_rng(seed)
    lat = rng.uniform(lat_range[0], lat_range[1], size=n)
    lon = rng.uniform(lon_range[0], lon_range[1], size=n)

    coastal_proximity = (lon - lon_range[0]) / (lon_range[1] - lon_range[0])
    hazard_mult = 1.0 + (COASTAL_LOSS_RATIO_MULT - 1.0) * coastal_proximity
    mu = BASE_LOSS_RATIO * hazard_mult

    sigma_log = np.sqrt(np.log(1.0 + INSURED_VALUE_CV ** 2))
    mu_log = np.log(MEAN_INSURED_VALUE) - 0.5 * sigma_log ** 2
    insured_value = rng.lognormal(mu_log, sigma_log, size=n)

    return dict(lat=lat, lon=lon, insured_value=insured_value, mu=mu, n=n, seed=seed)
