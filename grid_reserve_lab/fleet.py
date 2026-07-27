"""Synthetic wind/solar fleet: n sites with location, nameplate capacity,
and a smooth spatial climatological-capacity-factor surface -- the input to
dgp_simulator.py's oracle output/shortfall generator. Entirely synthetic
(LAB_PLAN.md's Risks section), a direct structural port of
climate_cat_lab/exposures.py's book -- same role (site book -> loss/shortfall
generator), same "illustrative, not fit to any real region" posture. Phase 2
swaps this for real NREL WIND Toolkit/NSRDB site geography and EIA-930
demand data while keeping the shortfall *mechanism* synthetic (LAB_PLAN.md).
"""

import numpy as np

# An illustrative rectangular wind-resource region, degrees lat/lon, roughly
# the footprint of the US Great Plains wind corridor (TX panhandle through
# the Dakotas) -- not tied to any real jurisdiction or real fleet.
LAT_RANGE = (30.0, 45.0)
LON_RANGE = (-105.0, -95.0)

# Nameplate capacity per site: lognormal around a typical utility-scale
# wind-farm size. Illustrative -- real fleets span a much wider range.
MEAN_NAMEPLATE_MW = 150.0
NAMEPLATE_CV = 0.5  # coefficient of variation

# Climatological (long-run average) capacity factor -- illustrative, in the
# real ballpark for US onshore wind (~30-45%), varying smoothly across the
# region (better wind resource toward the region's western edge, a stand-in
# for real terrain/climatology). Not fit to any real WIND Toolkit data --
# Phase 2 does that.
BASE_CAPACITY_FACTOR = 0.32
CAPACITY_FACTOR_RANGE_MULT = 1.4  # up to 1.4x at the highest-resource edge


def build_fleet(n, seed=0, lat_range=LAT_RANGE, lon_range=LON_RANGE):
    """Returns dict(lat, lon, nameplate_mw, cf, n, seed). cf is each site's
    baseline (normal-day) climatological capacity factor, from a smooth
    resource surface increasing toward the region's western edge -- a
    stand-in for real wind-resource geography."""
    rng = np.random.default_rng(seed)
    lat = rng.uniform(lat_range[0], lat_range[1], size=n)
    lon = rng.uniform(lon_range[0], lon_range[1], size=n)

    # western-edge proximity: 1.0 at the western edge, 0.0 at the eastern
    resource_proximity = 1.0 - (lon - lon_range[0]) / (lon_range[1] - lon_range[0])
    cf_mult = 1.0 + (CAPACITY_FACTOR_RANGE_MULT - 1.0) * resource_proximity
    cf = BASE_CAPACITY_FACTOR * cf_mult

    sigma_log = np.sqrt(np.log(1.0 + NAMEPLATE_CV ** 2))
    mu_log = np.log(MEAN_NAMEPLATE_MW) - 0.5 * sigma_log ** 2
    nameplate_mw = rng.lognormal(mu_log, sigma_log, size=n)

    return dict(lat=lat, lon=lon, nameplate_mw=nameplate_mw, cf=cf, n=n, seed=seed)
