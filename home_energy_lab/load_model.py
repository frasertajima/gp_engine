"""Synthetic household load: a diurnal/weekday-weekend base-load shape plus a
temperature-driven heating term, calibrated against Fraser's own real BC
Hydro bill (`research/04_vancouver_real_calibration_case.md`) rather than
only the aggregate EIA percentages research found.

**The real 2-point calibration** (documented in the research file, repeated
here as the load-bearing calculation this module implements): using the
standard 18C heating-degree-day base temperature (a real, commonly used
utility/HVAC convention, not fit) and the real mean temperature over each of
Fraser's two real billing sub-periods (computed directly from Open-Meteo,
`data_weather.load_range`):

    Mar 20-31, 2026: mean T=5.87C, real usage 35.1 kWh/day
    Apr 1-May 30, 2026: mean T=12.31C, real usage 29.3 kWh/day

Solving `daily_kwh = BASE_KWH_PER_DAY + HEATING_KWH_PER_DEGREE_DAY * max(0, HEAT_BASE_C - T)`
for the two unknowns against those two real points gives BASE_KWH_PER_DAY
~24.2 (non-heating: EV charging + everything else, not separated further --
a real, stated simplification) and HEATING_KWH_PER_DEGREE_DAY ~0.90. Cross-
checked (not fit) against the recalled seasonal anchors: predicts ~25.6
kWh/day for a typical September and ~36.4 kWh/day for a typical January,
close to the recalled ~25/~35 -- a real, working calibration.

The diurnal SHAPE (base load higher in evenings, heating load smoothed
across the day by thermal mass) is EIA-informed but not independently
calibrated at hourly resolution -- flagged in LAB_PLAN.md's Risks, a
real simplification, not claimed as validated at that resolution.
"""

import numpy as np

HEAT_BASE_C = 18.0                    # standard heating-degree-day base temperature
BASE_KWH_PER_DAY = 24.175             # fit from the real 2-point calibration above
HEATING_KWH_PER_DEGREE_DAY = 0.9006   # fit from the real 2-point calibration above

# Diurnal shape (24 hourly weights, summing to 1.0) -- EIA-informed, not independently
# calibrated: a modest overnight trough, a morning bump, an evening peak (the real,
# widely-documented residential shape), applied identically to both the base and the
# heating component (thermal mass would in reality smooth the heating component more
# than this -- a stated simplification, not modeled further this phase).
_DIURNAL_SHAPE = np.array([
    0.030, 0.028, 0.027, 0.027, 0.028, 0.032, 0.040, 0.046,
    0.048, 0.045, 0.042, 0.040, 0.039, 0.038, 0.038, 0.040,
    0.046, 0.055, 0.060, 0.058, 0.052, 0.045, 0.038, 0.033,
])
_DIURNAL_SHAPE = _DIURNAL_SHAPE / _DIURNAL_SHAPE.sum()

WEEKEND_MULT = 1.08  # a modest, real, commonly-documented weekend residential uplift


def hourly_load_kw(temperature_2m_c, timestamps, heat_base_c=HEAT_BASE_C,
                    base_kwh_per_day=BASE_KWH_PER_DAY,
                    heating_kwh_per_degree_day=HEATING_KWH_PER_DEGREE_DAY):
    """temperature_2m_c, timestamps: same-length arrays (hourly). Returns
    hourly household load (kW) -- diurnally-shaped base load plus a
    temperature-driven heating term, both scaled to the real calibration."""
    t = np.asarray(temperature_2m_c, dtype=float)
    hours = timestamps.hour.values
    is_weekend = timestamps.dayofweek.values >= 5

    shape = _DIURNAL_SHAPE[hours]
    weekend_scale = np.where(is_weekend, WEEKEND_MULT, 1.0)

    base_kw = base_kwh_per_day * shape * weekend_scale
    heating_degree = np.maximum(0.0, heat_base_c - t)
    # spread each day's heating kWh across the day using the same diurnal shape
    # (thermal-mass smoothing not modeled -- see module docstring)
    heating_kw = heating_kwh_per_degree_day * heating_degree / 24.0 * (shape * 24.0)

    return base_kw + heating_kw


if __name__ == "__main__":
    from data_weather import load_hourly, load_range

    # --- Real backtest: does this model reproduce Fraser's own two real bill periods? ---
    for start, end, real_daily_kwh, label in [
        ("2026-03-20", "2026-03-31", 35.1, "Mar 20-31, 2026"),
        ("2026-04-01", "2026-05-30", 29.3, "Apr 1-May 30, 2026"),
    ]:
        df = load_range(start, end)
        load_kw = hourly_load_kw(df["temperature_2m"].values, df.index)
        n_days = len(df) / 24.0
        model_daily_kwh = load_kw.sum() / n_days
        print(f"{label}: real={real_daily_kwh:.1f} kWh/day  model={model_daily_kwh:.2f} kWh/day  "
              f"(diff={model_daily_kwh - real_daily_kwh:+.2f})")

    # --- Multi-year seasonal shape check ---
    import pandas as pd

    df = load_hourly(2016, 2025)
    load_kw = hourly_load_kw(df["temperature_2m"].values, df.index)
    monthly = pd.Series(load_kw, index=df.index).groupby(df.index.month).mean()
    print("\nmean hourly load (kW) by calendar month (seasonal shape check):")
    print(monthly.round(2))
    annual_kwh = load_kw.sum() / 10
    print(f"\nimplied annual consumption ~{annual_kwh:,.0f} kWh/yr "
          f"(~{annual_kwh/365:.1f} kWh/day average)")
