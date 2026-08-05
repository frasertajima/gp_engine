"""Shortwave radiation (GHI, W/m^2) -> PV AC generation (kW), a simplified
single-derate conversion.

**A documented simplification, stated plainly** (same posture as
`reservoir_sim.py`'s lumped-single-reservoir choice elsewhere in this
codebase): a real PVWatts-style model accounts for panel tilt/orientation
(plane-of-array irradiance, not raw horizontal GHI), temperature-dependent
efficiency loss, and separate inverter/wiring/soiling losses. This module
folds all of that into one overall derate factor applied to horizontal GHI
directly -- adequate for testing the regime-mixture/VoI decision mechanism
against a realistic multi-year generation series, not claimed as
bankable production PV-yield forecasting accuracy.
"""

import numpy as np

STC_IRRADIANCE_W_M2 = 1000.0  # standard test condition reference irradiance
DEFAULT_DERATE = 0.80  # bundles temperature/inverter/wiring/soiling losses,
                        # within PVWatts' own typical 0.80-0.86 system-loss range


def pv_output_kw(shortwave_radiation_w_m2, nameplate_kw, derate=DEFAULT_DERATE):
    """AC output (kW) from horizontal shortwave radiation (W/m^2), for a
    system of the given nameplate DC capacity (kW). Vectorized over any
    array-like input."""
    ghi = np.asarray(shortwave_radiation_w_m2, dtype=float)
    return nameplate_kw * derate * (ghi / STC_IRRADIANCE_W_M2)


if __name__ == "__main__":
    from data_weather import load_hourly

    df = load_hourly(2016, 2025)
    gen = pv_output_kw(df["shortwave_radiation"].values, nameplate_kw=8.0)
    annual_kwh = gen.sum() / len(df) * 8760  # hourly kW values sum to kWh directly (1h steps)
    print(f"8kW system, 10-year mean shortwave radiation {df['shortwave_radiation'].mean():.1f} W/m^2")
    print(f"implied annual generation ~{gen.sum() / 10:,.0f} kWh/yr "
          f"({gen.sum() / 10 / 8:,.0f} kWh/yr per installed kW -- a real system "
          f"in this climate typically lands ~900-1100 kWh/yr/kW, a plausible sanity range)")

    by_month = df.copy()
    by_month["gen_kw"] = gen
    monthly = by_month.groupby(by_month.index.month)["gen_kw"].mean()
    print("\nmean hourly generation (kW) by calendar month (seasonal shape check):")
    print(monthly.round(2))
