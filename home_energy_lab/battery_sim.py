"""Home battery state-of-charge simulator -- the same lumped-reservoir
mechanics as `hydro_reserve_lab/reservoir_sim.py`, relabeled: "inflow" =
solar generation, "demand" = household load, "storage" = battery SOC.
Unlike a river reservoir, a home battery also needs an explicit grid-import/
export accounting (a river reservoir's "shortfall" has no symmetric
opposite; a battery's excess solar has to go somewhere -- exported to the
grid, typically at a much lower or zero net-metering credit).
"""

import numpy as np

# All four constants below are now sourced to Tesla's OWN Powerwall 3 datasheet
# (2025, en-us), fetched directly -- `research/09_battery_spec_primary_source.md`.
# Previously these were "documented mid-range assumptions ... not yet sourced to a
# primary spec sheet" (CODE_REVIEW.md H2); LAB_PLAN.md had deferred sourcing them to
# Phase 0, and that deferral was never discharged until 2026-08-05.

DEFAULT_CAPACITY_KWH = 13.5      # datasheet "Nominal Battery Energy: 13.5 kWh AC", with the
                                  # footnote "at 25C, AT BEGINNING OF LIFE" -- see
                                  # `mean_effective_capacity` below for the fade this implies

DEFAULT_MAX_POWER_KW = 11.5      # DISCHARGE only: datasheet "Nominal Output Power (AC)", top
                                  # configurable rating (5.8/7.6/10/11.5 kW)

DEFAULT_MAX_CHARGE_KW = 5.0      # CHARGE is NOT symmetric with discharge -- datasheet
                                  # "Maximum Continuous Charge Current / Power (Powerwall 3
                                  # only): 20.8 A AC / 5 kW" (8 kW only with expansion units).
                                  # This lab previously charged at the 11.5 kW discharge rate,
                                  # a real 2.3x overstatement of how fast a solar surplus or an
                                  # overnight pre-charge can actually fill the pack.

# Round-trip efficiency is DERIVED, not quoted -- the datasheet gives no pure battery
# round-trip figure. It gives two end-to-end paths:
#     "Solar to Battery to Home/Grid Efficiency"  89%    (footnote: typical solar shifting)
#     "Solar to Home/Grid Efficiency"             97.5%  (footnote: CEC weighted methodology)
# The second is the pass-through path (PV -> inverter -> AC) with no battery involved. The
# first is that same path PLUS the battery detour. Their ratio isolates the battery's own
# contribution: 0.89 / 0.975 = 0.9128.
#
# Using the headline 89% directly would be WRONG here and is the trap this note exists to
# flag: `solar_model.py` already applies a 0.80 derate covering inverter/wiring/soiling
# losses, so charging `battery_sim` with 0.89 would count the PV inverter loss twice. The
# derived 0.913 is the correct incremental figure for a simulator whose solar and load
# series are both already AC-side.
DEFAULT_ROUND_TRIP_EFF = 0.89 / 0.975   # = 0.9128, derived as above


# --- Capacity fade ------------------------------------------------------------------
# The datasheet's 13.5 kWh is explicitly "at beginning of life" and states a 10-year
# warranty, but does NOT publish a capacity-retention percentage -- that lives in Tesla's
# separate limited-warranty document, which is not served publicly at the URL its own
# energy library advertises (checked 2026-08-05, returns a server error page, not a PDF).
# So this figure is an ASSUMPTION, clearly marked, not a sourced spec. It is swept in
# `capacity_sizing.py`'s own sensitivity table specifically so that no conclusion in this
# lab depends on it -- see `research/09_battery_spec_primary_source.md`.
BATTERY_RETENTION_AT_END_OF_LIFE = 0.70   # ASSUMED, not sourced. Swept 0.6-1.0.


def mean_effective_capacity(nameplate_kwh, retention_at_end=BATTERY_RETENTION_AT_END_OF_LIFE):
    """Lifetime-average usable capacity under linear fade from nameplate (beginning of
    life) to `retention_at_end * nameplate` at end of life. Linear fade is a documented
    simplification -- real lithium fade is faster early then flattens -- but the average
    is what a lifetime-amortized cost comparison actually needs, and linear vs. a
    square-root-time curve moves that average by only a few percent."""
    return nameplate_kwh * (1.0 + retention_at_end) / 2.0


def simulate(solar_kw, load_kw, capacity_kwh=DEFAULT_CAPACITY_KWH,
             max_power_kw=DEFAULT_MAX_POWER_KW, round_trip_eff=DEFAULT_ROUND_TRIP_EFF,
             initial_soc_frac=0.5, dt_h=1.0, max_charge_kw=DEFAULT_MAX_CHARGE_KW):
    """solar_kw, load_kw: (n,) hourly arrays, same length, kW. Returns dict
    with soc_kwh (n,), grid_import_kwh (n,), grid_export_kwh (n,) -- battery
    charges from solar surplus first, discharges to cover load deficit,
    grid makes up any remaining shortfall or absorbs any remaining surplus.
    One-way efficiency loss (sqrt of round-trip) applied on both charge and
    discharge, the standard convention.

    `max_power_kw` bounds DISCHARGE; `max_charge_kw` bounds CHARGE. These are
    genuinely different on the real hardware (11.5 kW vs 5 kW on a Powerwall 3
    -- see this module's constants), which this lab previously did not model."""
    solar_kw = np.asarray(solar_kw, dtype=float)
    load_kw = np.asarray(load_kw, dtype=float)
    n = len(solar_kw)
    one_way_eff = np.sqrt(round_trip_eff)
    if max_charge_kw is None:
        max_charge_kw = max_power_kw

    soc = np.empty(n)
    grid_import = np.zeros(n)
    grid_export = np.zeros(n)
    charge_drawn_kwh = np.zeros(n)     # AC-side energy drawn from solar to charge (pre-efficiency)
    discharge_from_batt_kwh = np.zeros(n)  # energy actually removed from storage (pre-efficiency)
    level = capacity_kwh * initial_soc_frac

    for t in range(n):
        net_kw = solar_kw[t] - load_kw[t]  # >0 surplus, <0 deficit
        if net_kw >= 0:
            charge_kw = min(net_kw, max_charge_kw)
            charge_kwh = charge_kw * dt_h * one_way_eff
            room_kwh = capacity_kwh - level
            actual_charge_kwh = min(charge_kwh, room_kwh)
            level += actual_charge_kwh
            ac_side_charge_kwh = actual_charge_kwh / one_way_eff if one_way_eff else 0.0
            charge_drawn_kwh[t] = ac_side_charge_kwh
            # surplus beyond what the battery could accept/absorb goes to the grid
            grid_export[t] = max(net_kw * dt_h - ac_side_charge_kwh, 0.0)
        else:
            deficit_kw = -net_kw
            discharge_kw = min(deficit_kw, max_power_kw)
            discharge_kwh_needed = discharge_kw * dt_h / one_way_eff
            available_kwh = level
            actual_discharge_from_batt = min(discharge_kwh_needed, available_kwh)
            level -= actual_discharge_from_batt
            discharge_from_batt_kwh[t] = actual_discharge_from_batt
            delivered_kwh = actual_discharge_from_batt * one_way_eff
            shortfall_kwh = deficit_kw * dt_h - delivered_kwh
            grid_import[t] = max(shortfall_kwh, 0.0)
        soc[t] = level

    return dict(soc_kwh=soc, grid_import_kwh=grid_import, grid_export_kwh=grid_export,
                charge_drawn_kwh=charge_drawn_kwh, discharge_from_batt_kwh=discharge_from_batt_kwh)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n = 24 * 7
    solar = np.clip(np.sin(np.linspace(0, 2 * np.pi * 7, n)) * 3 + 2, 0, None)
    load = np.full(n, 1.5) + rng.normal(0, 0.2, n)
    out = simulate(solar, load, capacity_kwh=13.5, max_power_kw=11.5)
    print(f"round-trip eff (derived from Tesla datasheet): {DEFAULT_ROUND_TRIP_EFF:.4f}  "
          f"max charge {DEFAULT_MAX_CHARGE_KW} kW vs max discharge {DEFAULT_MAX_POWER_KW} kW")
    print(f"SOC range: [{out['soc_kwh'].min():.2f}, {out['soc_kwh'].max():.2f}] kWh")
    print(f"total grid import: {out['grid_import_kwh'].sum():.2f} kWh, "
          f"total grid export: {out['grid_export_kwh'].sum():.2f} kWh")

    # Rigorous per-timestep AC-bus power balance check (not a naive aggregate formula
    # that ignores round-trip efficiency losses): solar + discharge_delivered + import
    # must equal load + charge_drawn + export, every single hour.
    eff = np.sqrt(DEFAULT_ROUND_TRIP_EFF)
    delivered = out["discharge_from_batt_kwh"] * eff
    lhs = solar + delivered + out["grid_import_kwh"]
    rhs = load + out["charge_drawn_kwh"] + out["grid_export_kwh"]
    max_imbalance = np.max(np.abs(lhs - rhs))
    print(f"max per-hour AC-bus power imbalance: {max_imbalance:.2e} kW (should be ~0)")

    # Storage-level self-consistency: soc[t] - soc[t-1] == charge_into_storage - discharge_from_storage
    charge_into_storage = out["charge_drawn_kwh"] * eff
    implied_delta = charge_into_storage - out["discharge_from_batt_kwh"]
    actual_delta = np.diff(out["soc_kwh"], prepend=13.5 * 0.5)
    max_soc_err = np.max(np.abs(implied_delta - actual_delta))
    print(f"max SOC-trace consistency error: {max_soc_err:.2e} kWh (should be ~0)")

    # Charge power must never exceed the real datasheet limit (regression guard for the
    # 11.5 kW discharge rating previously being applied to charging too).
    charge_kw_series = out["charge_drawn_kwh"] / 1.0
    print(f"max charge power drawn: {charge_kw_series.max():.3f} kW "
          f"(datasheet limit {DEFAULT_MAX_CHARGE_KW} kW) -- "
          f"{'ok' if charge_kw_series.max() <= DEFAULT_MAX_CHARGE_KW + 1e-9 else 'FAIL'}")

    for ret in (1.0, 0.8, 0.7, 0.6):
        print(f"  retention {ret:.0%} -> lifetime-mean effective capacity "
              f"{mean_effective_capacity(13.5, ret):.2f} kWh")
