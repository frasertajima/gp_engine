"""BC Hydro's real residential rate structure (`research/
04_vancouver_real_calibration_case.md`): a TIERED threshold, not a flat or
simple time-varying price, with an optional Time-of-Day (TOD) adjustment
layered on top -- both real, current (2026), sourced.

**The TOD window is now the real one (CODE_REVIEW.md L4, fixed 2026-08-05).**
BC Hydro's actual off-peak window is 11pm-7am -- 8 hours, spanning midnight
into the next calendar day. This module previously used hours 0-6 of the
same calendar day (7 hours), a deliberate simplification to avoid
midnight-spanning bookkeeping in the daily dispatch-decision loop. That
made hour 23 pay the standard rate and gave every pre-charging policy 12.5%
less time to charge than reality allows. `dispatch_sim.py` now handles the
midnight crossing directly -- charging during hour 23 is credited to the
FOLLOWING day's target, since the night of day d serves day d+1 -- so the
simplification is no longer needed. Peak (4-9pm) is hours 16-20, matching
the real window directly.
"""

import numpy as np

STEP1_THRESHOLD_KWH_PER_MONTH = 675.0
STEP1_RATE = 0.1097   # $/kWh
STEP2_RATE = 0.1408   # $/kWh
BASIC_CHARGE_PER_MONTH = 6.17  # $

TOD_DISCOUNT = 0.05  # $/kWh, off-peak (11pm-7am -- the real 8-hour window)
TOD_SURCHARGE = 0.05  # $/kWh, peak (4-9pm, hours 16-20)

# Real export compensation under BC Hydro's Self-Generation Service Rate (RS 2289),
# effective 2026-07-01, live-verified from bchydro.com 2026-08-05 --
# `research/08_bc_hydro_export_compensation.md`. A flat monetary credit settled EVERY
# BILLING CYCLE (the legacy RS 1289 annual kWh-banking rate closed to new customers on
# the same date). RS 2289 is the correct rate for this lab specifically because
# `capacity_sizing.py` applies BC Hydro's solar rebate, and accepting that rebate
# forces the transition to RS 2289 -- the two assumptions are consistent only here.
EXPORT_CREDIT_PER_KWH = 0.10

OFFPEAK_HOURS = {23} | set(range(0, 7))   # real 11pm-7am window, see module docstring
PEAK_HOURS = set(range(16, 21))


def tod_rate_period(hour_of_day):
    """(n,) array of hour-of-day -> 'offpeak'/'peak'/'standard'."""
    hour_of_day = np.asarray(hour_of_day)
    period = np.full(hour_of_day.shape, "standard", dtype=object)
    period[np.isin(hour_of_day, list(OFFPEAK_HOURS))] = "offpeak"
    period[np.isin(hour_of_day, list(PEAK_HOURS))] = "peak"
    return period


def monthly_tiered_cost(monthly_kwh, n_days=30.44):
    """Real BC Hydro tiered cost for a period of `n_days` totaling
    `monthly_kwh` -- the threshold is prorated linearly by days-in-period
    (`n_days=30.44` = the real average days/month, used for genuine
    calendar-month bins). **A checked, not fully resolved, real
    discrepancy** (`research/04_vancouver_real_calibration_case.md`): this
    linear proration reproduces Fraser's real Mar 20-31 tier split closely
    (266 observed vs. 270 predicted, 12 days) but NOT the Apr 1-May 30 split
    (1,110 observed vs. 1,350 predicted, 60 days) -- BC Hydro's real
    per-period threshold rule isn't fully reverse-engineered from two data
    points, and this module uses the straightforward published 675 kWh/
    calendar-month rule (linearly prorated for partial periods) as the
    honest, stated modeling choice, not a claim it reproduces every real
    bill exactly."""
    threshold = STEP1_THRESHOLD_KWH_PER_MONTH * (n_days / 30.44)
    step1 = min(monthly_kwh, threshold)
    step2 = max(monthly_kwh - threshold, 0.0)
    return step1 * STEP1_RATE + step2 * STEP2_RATE + BASIC_CHARGE_PER_MONTH * (n_days / 30.44)


def total_cost_with_tod(grid_import_kwh, timestamps, use_tod=True,
                        grid_export_kwh=None, export_credit_per_kwh=EXPORT_CREDIT_PER_KWH):
    """grid_import_kwh, timestamps: (n,) hourly arrays. Returns total $ cost
    over the whole period: monthly tiered cost on TOTAL kWh (tiers respond
    to total consumption regardless of timing) PLUS/MINUS the optional TOD
    adjustment applied to each hour's own import (a real, additive layer on
    top of the tiered rate, per BC Hydro's own real structure).

    `grid_export_kwh`: optional (n,) hourly array of energy exported to the
    grid. When supplied, BC Hydro's real RS 2289 self-generation credit is
    applied (`research/08_bc_hydro_export_compensation.md`): a flat
    `export_credit_per_kwh` monetary credit, settled **per billing cycle**
    (so a high-export summer month cannot subsidise a high-consumption winter
    month), and **capped at that month's energy charge** because BC Hydro
    states the credit covers Energy Charges only -- the $6.17 basic charge
    stays payable no matter how much is exported. Passing `None` (the
    default) reproduces the previous export-is-worthless behaviour exactly,
    which several older results were computed under."""
    grid_import_kwh = np.asarray(grid_import_kwh, dtype=float)
    if grid_export_kwh is not None:
        grid_export_kwh = np.asarray(grid_export_kwh, dtype=float)
    months = timestamps.to_period("M")
    period = tod_rate_period(timestamps.hour.values) if use_tod else None

    total = 0.0
    for m in months.unique():
        mask = (months == m).values if hasattr(months == m, "values") else (months == m)
        kwh = grid_import_kwh[mask].sum()
        n_days_in_bin = mask.sum() / 24.0  # actual hours present for this bin / 24

        # Split the tiered cost into its energy and basic-charge parts: the export
        # credit may offset the former but never the latter.
        basic = BASIC_CHARGE_PER_MONTH * (n_days_in_bin / 30.44)
        energy_charge = monthly_tiered_cost(kwh, n_days=n_days_in_bin) - basic

        if use_tod:
            energy_charge += grid_import_kwh[mask & (period == "offpeak")].sum() * (-TOD_DISCOUNT)
            energy_charge += grid_import_kwh[mask & (period == "peak")].sum() * TOD_SURCHARGE

        if grid_export_kwh is not None:
            credit = min(grid_export_kwh[mask].sum() * export_credit_per_kwh,
                         max(energy_charge, 0.0))
            energy_charge -= credit

        total += energy_charge + basic

    return total


if __name__ == "__main__":
    import pandas as pd

    # Self-test against the real known bill: Mar 20-31, 2026 = 421 kWh over 12 days (266 tier1 + 155 tier2).
    cost = monthly_tiered_cost(421.0, n_days=12)
    real_cost = 266 * STEP1_RATE + 155 * STEP2_RATE + BASIC_CHARGE_PER_MONTH * (12 / 30.44)
    print(f"421 kWh/12 days -> ${cost:.2f} (real observed tier split gives ${real_cost:.2f} -- "
          f"close, the linear-proration model reproduces this real period reasonably well)")

    idx = pd.date_range("2026-01-01", periods=24 * 31, freq="h")
    flat_import = np.full(len(idx), 500.0 / (24 * 31))  # 500 kWh spread evenly
    cost_no_tod = total_cost_with_tod(flat_import, idx, use_tod=False)
    cost_with_tod = total_cost_with_tod(flat_import, idx, use_tod=True)
    print(f"500 kWh flat over a month: no-TOD=${cost_no_tod:.2f}  with-TOD=${cost_with_tod:.2f} "
          f"(should be lower with TOD if evenly split -- roughly equal offpeak/peak/standard hours "
          f"here, so a small net effect expected)")
