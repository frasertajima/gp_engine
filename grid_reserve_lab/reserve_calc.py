"""Reserve-requirement sizing and dollar-consequence scoring -- the mirror
image of climate_cat_lab/capital_calc.py, reformulated for a single
fleet-wide MW reserve requirement (Rockafellar-Uryasev VaR at the target
reliability has the same closed-form quantile shortcut climate_cat_lab's
capital_calc.py uses: for ONE aggregate quantity with no weights to
optimize, the optimal RU threshold variable IS the VaR, so no LP solver is
needed here either -- see that module's docstring). Uses
research/06_voll_and_reserve_cost.md's sourced figures, not invented ones.
"""

import numpy as np

# 0.1 days/year (the "1 day in 10 years" LOLE convention,
# research/01_nerc_lole_reserve_standard.md), translated to a per-day
# reliability target since this lab's replicate unit is a day, not a year.
TARGET_RELIABILITY_DAILY = 1.0 - 0.1 / 365.0  # 0.999726

# research/06_voll_and_reserve_cost.md: ERCOT's current PUCT-adopted VOLL,
# system-wide average, adopted August 2024 (Brattle Group study). The
# historical 2015-2021 figure was $9,000/MWh -- Phase 1's writeup sweeps
# this band as a sensitivity check, not a single point estimate.
VOLL_PER_MWH = 35_000.0
VOLL_HISTORICAL_LOW = 9_000.0

# research/06_voll_and_reserve_cost.md: PJM's 2026/27 Base Residual Auction
# cleared $329.17/MW-day (=365 x that, /year) -- used as the over-
# procurement cost side; ERCOT has no capacity market to draw a matched
# figure from (energy-only + ORDC), stated explicitly rather than blended.
RESERVE_COST_PER_MW_YEAR = 329.17 * 365.0  # ~$120,150/MW-year, PJM 2026/27 BRA

# Phase 1 simplification, stated plainly: dgp_simulator.py's daily
# shortfall_mw is a single representative daily magnitude, not an hourly
# time series (that granularity is Phase 2's job, once real EIA-930 hourly
# data replaces this synthetic daily oracle). To convert an excess-MW
# violation into a dollar figure, this constant treats a violation day's
# excess as an event of this many hours' duration -- a rough middle-of-
# the-road figure against research/04_dunkelflaute.md's real event
# durations (ERCOT's worst logged wind-drought event was 15 hours; many
# real events are shorter). NOT claimed as a calibrated figure.
ILLUSTRATIVE_EVENT_HOURS = 6.0


def required_reserve_mw(scenario_total_shortfall, target_reliability=TARGET_RELIABILITY_DAILY):
    """VaR at target_reliability -- the reserve level such that
    P(total shortfall <= reserve) = target_reliability under the model's
    own scenario distribution."""
    return float(np.quantile(scenario_total_shortfall, target_reliability))


def achieved_reliability(oracle_total_shortfall, reserve_mw):
    """Fraction of oracle days where total shortfall <= reserve_mw -- the
    ACHIEVED reliability, to compare against a method's target."""
    return float(np.mean(oracle_total_shortfall <= reserve_mw))


def expected_excess_mw(oracle_total_shortfall, reserve_mw):
    """Mean shortfall beyond reserve_mw, on oracle days where it's
    exceeded (zero if none do) -- the physical (MW) violation magnitude,
    before any dollar conversion."""
    excess = oracle_total_shortfall[oracle_total_shortfall > reserve_mw] - reserve_mw
    return float(excess.mean()) if len(excess) else 0.0


def annual_underprocurement_cost(oracle_total_shortfall, reserve_mw, voll_per_mwh=VOLL_PER_MWH,
                                  event_hours=ILLUSTRATIVE_EVENT_HOURS):
    """Expected annual dollar cost of under-procuring reserve: P(violation
    per day) x 365 x expected excess MW x event_hours x VOLL. See module
    docstring for the event_hours simplification."""
    p_violation = float(np.mean(oracle_total_shortfall > reserve_mw))
    excess_mw = expected_excess_mw(oracle_total_shortfall, reserve_mw)
    expected_unserved_mwh_per_day = p_violation * excess_mw * event_hours
    return expected_unserved_mwh_per_day * 365.0 * voll_per_mwh


def annual_overprocurement_cost(reserve_mw, true_required_reserve_mw,
                                 cost_per_mw_year=RESERVE_COST_PER_MW_YEAR):
    """Annual dollar cost of holding reserve capacity beyond the oracle's
    own true required level (zero if this method under- rather than
    over-procures)."""
    excess_mw = max(reserve_mw - true_required_reserve_mw, 0.0)
    return excess_mw * cost_per_mw_year


def score_method(method_name, reserve_mw, oracle_total_shortfall, true_required_reserve_mw,
                  target_reliability=TARGET_RELIABILITY_DAILY, voll_per_mwh=VOLL_PER_MWH,
                  cost_per_mw_year=RESERVE_COST_PER_MW_YEAR):
    """One method's full scorecard against the oracle: chosen reserve,
    achieved reliability, and dollar gap in both directions."""
    achieved = achieved_reliability(oracle_total_shortfall, reserve_mw)
    under_cost = annual_underprocurement_cost(oracle_total_shortfall, reserve_mw, voll_per_mwh)
    over_cost = annual_overprocurement_cost(reserve_mw, true_required_reserve_mw, cost_per_mw_year)
    return dict(
        method=method_name, reserve_mw=reserve_mw, target_reliability=target_reliability,
        achieved_reliability=achieved,
        annual_underprocurement_cost_usd=under_cost,
        annual_overprocurement_cost_usd=over_cost,
        net_dollar_gap_usd=under_cost + over_cost,
    )
