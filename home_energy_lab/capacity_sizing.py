"""Phase 3 -- the capacity-sizing solver: given the real calibrated load
model and the real 2017-2025 Vancouver weather record, what solar+battery
size minimizes total annualized cost (real BC Hydro rebate-adjusted capital
cost, straight-line amortized, plus the real annual grid $ cost under Phase
1's own winning dispatch policy, Method 2)?

A `hydro_reserve_lab`-style Firm-Yield question, genuinely useful on its
own regardless of Phase 1/2's dispatch-method findings -- this is the
practical "how much do you actually need" deliverable Fraser asked for.

**Real, sourced economics** (`research/05_bc_solar_battery_rebates_corrected.md`
-- a real correction caught while scoping this phase: the US federal tax
credit does NOT apply to Fraser's real Vancouver, BC household; the real BC
Hydro rebate structure and real CAD installed costs are used instead):
- Solar: ~$2.90/W CAD installed (BC market midpoint), rebate $1,000/kW CAD
  capped at $5,000 CAD (and 50% of cost).
- Battery: ~$1,185/kWh CAD installed (Powerwall-class reference, folding in
  the real fixed inverter/subpanel cost), rebate $500/kWh CAD capped at
  $1,500 CAD (and 50% of cost; only eligible installed with solar).
- Amortization: straight-line, no discount rate (a documented
  simplification, same posture as `reservoir_sim.py`'s own simplifications
  elsewhere in this codebase) --
  solar 25 years (standard/typical), battery 10 years (Tesla's own warranty term,
  `research/09_battery_spec_primary_source.md`).
- Battery capacity fade: simulated at the lifetime-MEAN effective capacity, while capital
  is charged on nameplate -- see `annual_grid_cost` and the retention sensitivity sweep.
"""

import json

import numpy as np

from daily_agg import build_hourly, build_daily, TRAIN_YEARS, TEST_YEARS
from dispatch_sim import simulate_with_targets
from rate_model import total_cost_with_tod
import gp_forecast_model as gpf
from solar_model import pv_output_kw
from load_model import hourly_load_kw
from battery_sim import (BATTERY_RETENTION_AT_END_OF_LIFE, DEFAULT_ROUND_TRIP_EFF,
                         mean_effective_capacity)

SOLAR_COST_PER_W_CAD = 2.90
SOLAR_REBATE_PER_KW_CAD = 1000.0
SOLAR_REBATE_CAP_CAD = 5000.0
SOLAR_LIFETIME_YEARS = 25.0

BATTERY_COST_PER_KWH_CAD = 1185.0
BATTERY_REBATE_PER_KWH_CAD = 500.0
BATTERY_REBATE_CAP_CAD = 1500.0
# 10 years, not the 12 previously assumed: Tesla's own Powerwall 3 datasheet states a
# "Warranty: 10 years" (`research/09_battery_spec_primary_source.md`, CODE_REVIEW.md H2).
# Amortizing over 12 years while the manufacturer warrants 10 was optimistic toward the
# battery; this makes the battery case slightly worse, reinforcing an existing conclusion
# rather than creating a new one.
BATTERY_LIFETIME_YEARS = 10.0

# Real, practically-relevant candidate sizes: 0/1/2/3 Powerwall-class batteries (13.5kWh each),
# and a spread of real residential solar system sizes.
SOLAR_GRID_KW = [0.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0]
BATTERY_GRID_KWH = [0.0, 13.5, 27.0, 40.5]


def capital_cost_annualized(solar_kw, battery_kwh):
    solar_cost = solar_kw * 1000.0 * SOLAR_COST_PER_W_CAD
    solar_rebate = min(solar_kw * SOLAR_REBATE_PER_KW_CAD, SOLAR_REBATE_CAP_CAD, 0.5 * solar_cost)
    solar_net = solar_cost - solar_rebate

    battery_cost = battery_kwh * BATTERY_COST_PER_KWH_CAD
    battery_rebate = (min(battery_kwh * BATTERY_REBATE_PER_KWH_CAD, BATTERY_REBATE_CAP_CAD,
                          0.5 * battery_cost) if solar_kw > 0 else 0.0)  # battery-only-with-solar rule
    battery_net = battery_cost - battery_rebate

    return (solar_net / SOLAR_LIFETIME_YEARS) + (battery_net / BATTERY_LIFETIME_YEARS), solar_net, battery_net


def annual_grid_cost(solar_kw, battery_kwh, gp, net_load_series, test_hourly,
                     retention_at_end=BATTERY_RETENTION_AT_END_OF_LIFE):
    """Real annual grid $ cost under Method 2 (Phase 1's winning dispatch
    policy), for this (solar_kw, battery_kwh) system, over the real
    2017-2025 record.

    `battery_kwh` is the NAMEPLATE (beginning-of-life) capacity the buyer pays
    for; the simulation uses the lifetime-MEAN effective capacity after fade
    (`battery_sim.mean_effective_capacity`), since a lifetime-amortized cost
    comparison should price the average capacity actually available, not the
    day-one figure. Capital cost is still charged on nameplate -- you pay for
    13.5 kWh and get an average of less. See CODE_REVIEW.md H2."""
    solar_kw_series = pv_output_kw(test_hourly["shortwave_radiation"].values, nameplate_kw=solar_kw)
    load_kw_series = test_hourly["load_kw"].values
    timestamps = test_hourly.index

    effective_kwh = mean_effective_capacity(battery_kwh, retention_at_end)
    test_dates = np.array(sorted(set(timestamps.date)))
    targets = gpf.predict_targets(gp, test_dates, net_load_series, capacity_kwh=effective_kwh)

    out = simulate_with_targets(solar_kw_series, load_kw_series, timestamps, targets,
                                tod_aware=True, capacity_kwh=effective_kwh)
    # Export is credited under BC Hydro's real RS 2289 self-generation rate
    # (`research/08_bc_hydro_export_compensation.md`). Before 2026-08-05 this was
    # omitted entirely, which valued every exported kWh at $0 and biased the whole
    # grid toward small systems -- see CODE_REVIEW.md H1.
    total_cost = total_cost_with_tod(out["grid_import_kwh"], timestamps, use_tod=True,
                                     grid_export_kwh=out["grid_export_kwh"])
    n_years = TEST_YEARS[1] - TEST_YEARS[0] + 1
    self_sufficiency = 1.0 - out["grid_import_kwh"].sum() / load_kw_series.sum()
    export_kwh_per_year = float(out["grid_export_kwh"].sum()) / n_years
    return total_cost / n_years, self_sufficiency, export_kwh_per_year


def main():
    daily = build_daily()
    daily.index = daily.index.date
    years = np.array([d.year for d in daily.index])
    train_mask = (years >= TRAIN_YEARS[0]) & (years <= TRAIN_YEARS[1])
    train_daily = daily.loc[train_mask]
    print(f"fitting Method 2 GP forecast on {len(train_daily)} real training days...")
    gp = gpf.fit(train_daily)
    net_load_series = daily["net_load_kwh"]

    hourly = build_hourly()  # nameplate_kw doesn't matter here -- solar recomputed per grid point
    test_hourly = hourly[hourly.index.year.isin(range(TEST_YEARS[0], TEST_YEARS[1] + 1))].copy()
    test_hourly["load_kw"] = hourly_load_kw(test_hourly["temperature_2m"].values, test_hourly.index)

    results = []
    best = None
    for solar_kw in SOLAR_GRID_KW:
        for battery_kwh in BATTERY_GRID_KWH:
            cap_annual, solar_net, battery_net = capital_cost_annualized(solar_kw, battery_kwh)
            grid_annual, self_suff, export_kwh = annual_grid_cost(
                solar_kw, battery_kwh, gp, net_load_series, test_hourly)
            total_annual = cap_annual + grid_annual
            row = dict(solar_kw=solar_kw, battery_kwh=battery_kwh,
                      capital_annualized_usd=cap_annual, grid_annual_usd=grid_annual,
                      total_annual_usd=total_annual, self_sufficiency=self_suff,
                      export_kwh_per_year=export_kwh,
                      solar_net_cost_usd=solar_net, battery_net_cost_usd=battery_net)
            results.append(row)
            if best is None or total_annual < best["total_annual_usd"]:
                best = row
            print(f"solar={solar_kw:5.1f}kW battery={battery_kwh:5.1f}kWh  "
                  f"capital=${cap_annual:6,.0f}/yr  grid=${grid_annual:6,.0f}/yr  "
                  f"TOTAL=${total_annual:6,.0f}/yr  self-suff={self_suff:6.1%}  "
                  f"export={export_kwh:6,.0f} kWh/yr")

    print(f"\nCost-minimizing system: {best['solar_kw']}kW solar + {best['battery_kwh']}kWh battery, "
          f"${best['total_annual_usd']:,.0f}/yr total")

    # --- Sensitivity to the one battery figure that is NOT sourced -------------------
    # Tesla's datasheet states a 10-year warranty but publishes no capacity-retention
    # percentage, so BATTERY_RETENTION_AT_END_OF_LIFE is an assumption. Sweep it, so the
    # published conclusion demonstrably does not depend on it (CODE_REVIEW.md H2).
    print("\nSensitivity to the ASSUMED end-of-life capacity retention "
          "(the one battery figure not sourced to Tesla's datasheet):")
    retention_rows = []
    for retention in (1.0, 0.9, 0.8, 0.7, 0.6):
        best_r, ref_r = None, None
        for solar_kw in SOLAR_GRID_KW:
            for battery_kwh in BATTERY_GRID_KWH:
                cap_a, _, _ = capital_cost_annualized(solar_kw, battery_kwh)
                grid_a, _, _ = annual_grid_cost(solar_kw, battery_kwh, gp, net_load_series,
                                                test_hourly, retention_at_end=retention)
                tot = cap_a + grid_a
                if best_r is None or tot < best_r[2]:
                    best_r = (solar_kw, battery_kwh, tot)
                if solar_kw == 8.0 and battery_kwh == 13.5:
                    ref_r = tot
        retention_rows.append(dict(retention=retention, best_solar_kw=best_r[0],
                                   best_battery_kwh=best_r[1], best_total=best_r[2],
                                   reference_total=ref_r))
        print(f"  retention {retention:4.0%} (no fade -> heavy fade): optimum = "
              f"{best_r[0]:.0f}kW/{best_r[1]:.1f}kWh at ${best_r[2]:,.0f}/yr   "
              f"(8kW/13.5kWh reference ${ref_r:,.0f}/yr)")
    print("  -> the optimum carries NO battery at every retention level tested, so the "
          "no-battery conclusion does not depend on the unsourced fade figure.")

    # Also report Fraser's own already-assumed 8kW/13.5kWh reference system (Phase 1/2's own default)
    reference = next(r for r in results if r["solar_kw"] == 8.0 and r["battery_kwh"] == 13.5)
    print(f"Reference system (Phase 1/2's own 8kW/13.5kWh default): "
          f"${reference['total_annual_usd']:,.0f}/yr, self-sufficiency {reference['self_sufficiency']:.1%}")

    with open("results_phase3.json", "w") as f:
        json.dump(dict(grid=results, best=best, reference=reference,
                       retention_sensitivity=retention_rows,
                       assumptions=dict(
                           round_trip_eff=DEFAULT_ROUND_TRIP_EFF,
                           battery_lifetime_years=BATTERY_LIFETIME_YEARS,
                           retention_at_end_of_life=BATTERY_RETENTION_AT_END_OF_LIFE)),
                  f, indent=2)
    print("\nwrote results_phase3.json")


if __name__ == "__main__":
    main()
