"""Daily aggregation shared by Phase 1's method ladder: solar generation,
household load, and their net (load-minus-solar, the real quantity the
battery+grid must cover each day), plus mean temperature -- built from the
real 10-year Vancouver hourly record (`data_weather.py`).
"""

import pandas as pd

from data_weather import load_hourly
from solar_model import pv_output_kw
from load_model import hourly_load_kw

TRAIN_YEARS = (2016, 2016)  # ONE year (366 days) -- `gp1d.py`'s exact O(n^3) GP is fast at this
                            # scale (shm_lab's own ~150-400 point precedent); n=1096 (3 years) was
                            # tried first and measured too slow (single restart ~20-36s even with
                            # BLAS threads pinned to 1, a real timeout hit during testing) --
                            # trained-set size reduced deliberately, not for lack of trying
TEST_YEARS = (2017, 2025)   # remaining 9 years


def build_hourly(nameplate_kw=8.0, start_year=2016, end_year=2025):
    df = load_hourly(start_year, end_year)
    df = df.copy()
    df["solar_kw"] = pv_output_kw(df["shortwave_radiation"].values, nameplate_kw=nameplate_kw)
    df["load_kw"] = hourly_load_kw(df["temperature_2m"].values, df.index)
    return df


def build_daily(nameplate_kw=8.0, start_year=2016, end_year=2025):
    hourly = build_hourly(nameplate_kw, start_year, end_year)
    daily = hourly.resample("D").agg({"solar_kw": "sum", "load_kw": "sum", "temperature_2m": "mean"})
    daily = daily.rename(columns={"solar_kw": "solar_kwh", "load_kw": "load_kwh",
                                  "temperature_2m": "temp"})
    daily["net_load_kwh"] = (daily["load_kwh"] - daily["solar_kwh"]).clip(lower=0.0)
    return daily


if __name__ == "__main__":
    daily = build_daily()
    print(daily.describe())
    train = daily.loc[f"{TRAIN_YEARS[0]}":f"{TRAIN_YEARS[1]}"]
    test = daily.loc[f"{TEST_YEARS[0]}":f"{TEST_YEARS[1]}"]
    print(f"\ntrain: {len(train)} days ({TRAIN_YEARS[0]}-{TRAIN_YEARS[1]})")
    print(f"test: {len(test)} days ({TEST_YEARS[0]}-{TEST_YEARS[1]})")
