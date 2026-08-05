"""Methods 0-1 (plus the two model-free ABLATIONS 0b/1b): the naive dispatch
policies -- no forecast, no regime awareness, just fixed rules. The
"traditional" end of the ladder every prior lab's method comparison starts
from.

**Why 0b/1b exist (CODE_REVIEW.md C2, 2026-08-05).** Phase 1 originally
reported "Method 2 (plain GP forecast) wins" without an ablation showing the
GP itself was responsible. It wasn't: `method1b_targets` -- a two-line
calendar rule using NO data at all -- and `method0b_targets` -- yesterday's
realized net load with no model at all -- both match or beat the fitted GP.
The real advantage of Methods 1-3 over Method 0 is proactive off-peak
pre-charging with a seasonal on/off; day-ahead forecasting adds nothing on
top of that. These two baselines are kept permanently in the ladder so that
finding cannot be lost again.
"""

import numpy as np

DEFAULT_CAPACITY_KWH = 13.5

# Vancouver's real heating season -- the months in which a stress regime can
# occur at all (`phase0_run.py`'s own measured seasonal shape: winter load is
# far above summer, winter solar ~5.6x below summer).
HEATING_MONTHS = (10, 11, 12, 1, 2, 3)


def method0_targets(dates):
    """Method 0 -- fully naive reactive control: no proactive charging, no
    schedule/price awareness at all (paired with `dispatch_sim.py`'s
    `tod_aware=False`, reproducing `battery_sim.simulate` exactly)."""
    return {d: 0.0 for d in dates}


def method1_targets(dates, capacity_kwh=DEFAULT_CAPACITY_KWH):
    """Method 1 -- TOU-arbitrage-only heuristic: always top up to full
    capacity every off-peak window, regardless of weather -- a common real
    "smart" default (charge at the cheapest scheduled hours, no forecast).
    Paired with `tod_aware=True`."""
    return {d: capacity_kwh for d in dates}


def method0b_targets(dates, net_load_series, capacity_kwh=DEFAULT_CAPACITY_KWH):
    """Method 0b (ABLATION) -- persistence, no model: target = YESTERDAY's
    realized net load, clipped to capacity. Uses exactly the same information
    Method 2's GP is fed (the lag-1 net load), with the GP removed entirely.
    Any gap between this and Method 2 is what the fitted GP actually buys.
    Paired with `tod_aware=True`."""
    import datetime
    one_day = datetime.timedelta(days=1)

    targets = {}
    for d in dates:
        prev_day = d - one_day
        if prev_day not in net_load_series.index:
            targets[d] = 0.0
            continue
        targets[d] = float(np.clip(net_load_series.loc[prev_day], 0.0, capacity_kwh))
    return targets


def method4_tier_aware_targets(dates, net_load_series, capacity_kwh=DEFAULT_CAPACITY_KWH,
                               step1_threshold_kwh=675.0, heating_months=HEATING_MONTHS):
    """Method 4 -- TIER-THRESHOLD-AWARE pre-charging, the policy class
    `research/04_vancouver_real_calibration_case.md` explicitly asked Phase 1/2
    to model and which no method in the ladder previously addressed
    (CODE_REVIEW.md H3).

    The real BC Hydro default rate is a STEP THRESHOLD, not a flat or purely
    time-varying price: the first 675 kWh/month costs 10.97c/kWh and every kWh
    above it costs 14.08c/kWh. That makes the marginal value of shifting
    consumption depend on *where this month's running total sits relative to
    the threshold*, which is a genuinely different signal from the time-of-day
    one Methods 1-3 all use.

    The policy: run the calendar rule (which Phase 1 found captures all of the
    achievable seasonal gain), but SUPPRESS off-peak pre-charging once the
    month's cumulative net load has already blown past the Step 1 threshold.
    The reasoning is that round-trip losses on pre-charged energy are paid at
    the Step 2 marginal rate once you are over the line, so the arbitrage that
    is worthwhile early in a month gets more expensive later in it.

    `net_load_series`: realized daily net load indexed by date. Only days
    STRICTLY BEFORE the day being decided are used (a running total through
    yesterday), so there is no lookahead -- the same no-peeking discipline
    every other method in this ladder follows."""
    import collections

    running = collections.defaultdict(float)
    targets = {}
    for d in sorted(dates):
        month_key = (d.year, d.month)
        over_threshold = running[month_key] >= step1_threshold_kwh
        in_season = d.month in heating_months
        targets[d] = capacity_kwh if (in_season and not over_threshold) else 0.0
        # accumulate AFTER deciding, so day d's own load never informs day d
        if d in net_load_series.index:
            running[month_key] += float(net_load_series.loc[d])
    return targets


def method1b_targets(dates, capacity_kwh=DEFAULT_CAPACITY_KWH, heating_months=HEATING_MONTHS):
    """Method 1b (ABLATION) -- calendar only, ZERO data: full overnight charge
    during the heating season, none otherwise. Consumes no weather, no load
    history, and no fitted model of any kind. The floor any forecast-based
    method has to clear to have earned its complexity.
    Paired with `tod_aware=True`."""
    return {d: (capacity_kwh if d.month in heating_months else 0.0) for d in dates}
