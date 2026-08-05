"""Extends `battery_sim.py`'s reactive storage mechanics with a daily
overnight PRE-CHARGE TARGET -- the actual decision variable the Phase 1
method ladder scores. Each method (naive/TOU/GP/GP+regime) picks a
`target_soc_kwh` for each day; this module applies it during that day's
off-peak hours (`rate_model.py`'s simplified same-day 0-6 proxy for BC
Hydro's real 11pm-7am window), then runs the rest of the day reactively
(solar surplus charges/exports, deficit discharges/imports) exactly as
`battery_sim.simulate` does.

Why this needs its own loop rather than reusing `battery_sim.simulate`
unchanged: that function has no notion of a proactive, price-driven charge
target -- only reactive solar-following behavior. This keeps
`battery_sim.py` itself untouched (Phase 3's capacity-sizing solver can
still use its simpler reactive-only mechanics) and adds the dispatch-
decision behavior as a genuinely separate layer, the same "don't touch a
validated module, extend around it" posture as every other multi-phase lab
in this codebase.
"""

import datetime as _dt

import numpy as np

from battery_sim import (DEFAULT_CAPACITY_KWH, DEFAULT_MAX_POWER_KW, DEFAULT_ROUND_TRIP_EFF,
                         DEFAULT_MAX_CHARGE_KW)
from rate_model import OFFPEAK_HOURS, PEAK_HOURS

# Hours during which a `daily_reserve_kwh` floor is enforced: after the off-peak
# charging window has closed and BEFORE the peak (4-9pm) surcharge window opens.
# Discharging in these standard-rate hours saves STEP1_RATE; saving the same kWh
# for the peak window saves STEP1_RATE + TOD_SURCHARGE. A reserve floor here is
# therefore the one lever a stress-aware layer still has once the overnight
# charge target has saturated at battery capacity -- see CODE_REVIEW.md C1.
RESERVE_HOURS = frozenset(h for h in range(24)
                          if h not in OFFPEAK_HOURS and h < min(PEAK_HOURS))

# The off-peak window spans midnight (11pm-7am). Charging done during the 11pm hour
# belongs to the NEXT calendar day's plan -- the night of day d serves day d+1 -- so
# that hour looks up tomorrow's target/reserve. Avoiding this one-line bookkeeping was
# the stated reason the window used to be truncated to 7 hours (CODE_REVIEW.md L4).
_PRE_MIDNIGHT_OFFPEAK_HOURS = frozenset(h for h in OFFPEAK_HOURS if h >= 12)


def simulate_with_targets(solar_kw, load_kw, timestamps, daily_target_kwh, tod_aware=True,
                          capacity_kwh=DEFAULT_CAPACITY_KWH, max_power_kw=DEFAULT_MAX_POWER_KW,
                          round_trip_eff=DEFAULT_ROUND_TRIP_EFF, initial_soc_frac=0.5, dt_h=1.0,
                          daily_reserve_kwh=None, max_charge_kw=DEFAULT_MAX_CHARGE_KW):
    """solar_kw, load_kw, timestamps: (n,) hourly, aligned. daily_target_kwh:
    dict date -> target SOC (kWh) to reach via off-peak grid charging that
    day, computed by whichever method is under test (see naive_baselines.py/
    gp_forecast_model.py/regime_mixture.py) using only information available
    before that day starts (no lookahead). Returns the same dict shape as
    `battery_sim.simulate`, plus `proactive_charge_kwh` (AC-side grid energy
    drawn specifically for pre-charging, separated out for diagnostics).

    `tod_aware`: if True (Methods 1-3), off-peak-hour deficits are served
    DIRECTLY from grid rather than by discharging the battery -- discharging
    then would pay round-trip losses for no reason when the alternative is
    already the cheapest grid price available (a real bug caught during
    testing: an early draft proactively charged toward the target then
    immediately let the reactive step discharge the same energy straight
    back out to cover that hour's own load). If False (Method 0, the fully
    naive baseline with no schedule/price awareness at all), off-peak hours
    are treated exactly like any other hour -- pass `daily_target_kwh={}`
    (or all-zero targets) together with `tod_aware=False` to reproduce
    `battery_sim.simulate` exactly, verified in this file's own self-test.

    `daily_reserve_kwh`: optional dict date -> SOC floor (kWh) the battery is
    not discharged below during `RESERVE_HOURS` (the standard-rate hours
    between the off-peak window closing and the peak window opening), so that
    energy is still available for the 4-9pm surcharge window. `None` or an
    empty dict reproduces the previous no-reserve behaviour exactly (verified
    in this file's own self-test).

    Why this parameter exists (CODE_REVIEW.md C1): the overnight charge target
    is clipped at battery capacity, and daily net load exceeds capacity on
    ~50% of days -- so on exactly the high-demand days a stress-aware layer
    cares about, the target is already saturated and no forecast-driven margin
    can move it. The reserve floor is not bounded by the charge target, so it
    is a lever that still has headroom on those days."""
    solar_kw = np.asarray(solar_kw, dtype=float)
    load_kw = np.asarray(load_kw, dtype=float)
    n = len(solar_kw)
    one_way_eff = np.sqrt(round_trip_eff)
    hours = timestamps.hour.values
    dates = timestamps.date
    _one_day = _dt.timedelta(days=1)
    if daily_reserve_kwh is None:
        daily_reserve_kwh = {}
    if max_charge_kw is None:
        max_charge_kw = max_power_kw

    soc = np.empty(n)
    grid_import = np.zeros(n)
    grid_export = np.zeros(n)
    proactive_charge_kwh = np.zeros(n)
    level = capacity_kwh * initial_soc_frac

    for t in range(n):
        net_kw = solar_kw[t] - load_kw[t]

        if tod_aware and hours[t] in OFFPEAK_HOURS:
            # Off-peak hour: grid is being bought anyway (cheap), so any deficit is served
            # DIRECTLY from grid, not by discharging the battery -- discharging here would
            # needlessly pay round-trip losses twice (a real bug caught during testing: the
            # first draft charged toward the target, then immediately let the reactive
            # solar-following step discharge the battery again to cover the same hour's load,
            # undoing the proactive charge). Any solar surplus still charges/exports normally.
            if net_kw < 0:
                grid_import[t] += -net_kw * dt_h
            else:
                charge_kw = min(net_kw, max_charge_kw)
                charge_kwh = charge_kw * dt_h * one_way_eff
                room_kwh = capacity_kwh - level
                actual_charge_kwh = min(charge_kwh, room_kwh)
                level += actual_charge_kwh
                ac_side_charge_kwh = actual_charge_kwh / one_way_eff if one_way_eff else 0.0
                grid_export[t] += max(net_kw * dt_h - ac_side_charge_kwh, 0.0)

            # Proactive top-up toward the target for the day this night SERVES, ON TOP of
            # serving this hour's load above. Hours 0-6 serve today; hour 23 serves tomorrow.
            plan_date = dates[t] + _one_day if hours[t] in _PRE_MIDNIGHT_OFFPEAK_HOURS else dates[t]
            target = min(daily_target_kwh.get(plan_date, 0.0), capacity_kwh)
            if level < target:
                room_kwh = target - level
                max_chargeable_kwh = max_charge_kw * dt_h * one_way_eff
                actual_charge_kwh = min(room_kwh, max_chargeable_kwh)
                level += actual_charge_kwh
                drawn = actual_charge_kwh / one_way_eff
                proactive_charge_kwh[t] = drawn
                grid_import[t] += drawn
        else:
            # --- Reactive solar-following dispatch (battery_sim.py's own logic) ---
            if net_kw >= 0:
                charge_kw = min(net_kw, max_charge_kw)
                charge_kwh = charge_kw * dt_h * one_way_eff
                room_kwh = capacity_kwh - level
                actual_charge_kwh = min(charge_kwh, room_kwh)
                level += actual_charge_kwh
                ac_side_charge_kwh = actual_charge_kwh / one_way_eff if one_way_eff else 0.0
                grid_export[t] += max(net_kw * dt_h - ac_side_charge_kwh, 0.0)
            else:
                deficit_kw = -net_kw
                discharge_kw = min(deficit_kw, max_power_kw)
                discharge_kwh_needed = discharge_kw * dt_h / one_way_eff
                # Hold back `reserve` during the standard-rate hours before the peak
                # window, so this energy is still there for the 4-9pm surcharge.
                if hours[t] in RESERVE_HOURS:
                    floor = min(daily_reserve_kwh.get(dates[t], 0.0), capacity_kwh)
                else:
                    floor = 0.0
                available_kwh = max(level - floor, 0.0)
                actual_discharge_from_batt = min(discharge_kwh_needed, available_kwh)
                level -= actual_discharge_from_batt
                delivered_kwh = actual_discharge_from_batt * one_way_eff
                shortfall_kwh = deficit_kw * dt_h - delivered_kwh
                grid_import[t] += max(shortfall_kwh, 0.0)
        soc[t] = level

    return dict(soc_kwh=soc, grid_import_kwh=grid_import, grid_export_kwh=grid_export,
                proactive_charge_kwh=proactive_charge_kwh)


if __name__ == "__main__":
    import pandas as pd

    from data_weather import load_range
    from solar_model import pv_output_kw
    from load_model import hourly_load_kw

    df = load_range("2026-01-01", "2026-01-14")
    solar = pv_output_kw(df["shortwave_radiation"].values, nameplate_kw=8.0)
    load = hourly_load_kw(df["temperature_2m"].values, df.index)

    # target = always top up to full capacity every night (Method-1-style, for a smoke test)
    targets = {d: DEFAULT_CAPACITY_KWH for d in pd.unique(df.index.date)}
    out = simulate_with_targets(solar, load, df.index, targets)
    print(f"2 weeks, always-full-charge policy: grid_import={out['grid_import_kwh'].sum():.1f} kWh, "
          f"grid_export={out['grid_export_kwh'].sum():.1f} kWh, "
          f"proactive_charge={out['proactive_charge_kwh'].sum():.1f} kWh")
    print(f"SOC range: [{out['soc_kwh'].min():.2f}, {out['soc_kwh'].max():.2f}]")

    # target=0, tod_aware=False (Method-0-style, no schedule/price awareness at all)
    # should behave EXACTLY like battery_sim.simulate.
    import battery_sim
    targets0 = {d: 0.0 for d in pd.unique(df.index.date)}
    out0 = simulate_with_targets(solar, load, df.index, targets0, tod_aware=False)
    out_ref = battery_sim.simulate(solar, load)
    max_diff = np.max(np.abs(out0["soc_kwh"] - out_ref["soc_kwh"]))
    print(f"\nzero-target, tod_aware=False vs. battery_sim.simulate max SOC diff: "
          f"{max_diff:.2e} (should be ~0)")
