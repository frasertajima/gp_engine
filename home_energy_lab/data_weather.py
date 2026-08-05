"""Loader for real hourly Vancouver, BC weather (Open-Meteo Historical Weather
API, ERA5 reanalysis -- `research/01_historical_weather_solar_data.md`, live-
verified: free, no API key, real data confirmed by direct `curl` test before
any code was written).

Pulls year-by-year (the archive API handles arbitrary ranges, but chunking
keeps each request small/fast and lets partial failures retry independently)
and caches to `data/weather_<year>.json` -- not committed to version control,
re-downloadable from the live API, same posture as `data_kw51.py`/
`data_usgs.py`'s raw pulls elsewhere in this codebase.
"""

import json
import os
import time
import urllib.request

import numpy as np
import pandas as pd

LAT, LON = 49.2827, -123.1207  # Vancouver, BC
TIMEZONE = "America/Vancouver"
HOURLY_VARS = "temperature_2m,shortwave_radiation,cloudcover"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _fetch_range(start_date, end_date, retries=3, backoff_s=2.0):
    url = (f"{ARCHIVE_URL}?latitude={LAT}&longitude={LON}"
           f"&start_date={start_date}&end_date={end_date}&hourly={HOURLY_VARS}"
           f"&timezone={TIMEZONE.replace('/', '%2F')}")
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # real network/API hiccups, not silently ignored
            last_err = e
            time.sleep(backoff_s * (attempt + 1))
    raise RuntimeError(f"Open-Meteo fetch failed for {start_date}..{end_date}: {last_err}")


def _fetch_year(year, cache=True):
    os.makedirs(DATA_DIR, exist_ok=True)
    cache_path = os.path.join(DATA_DIR, f"weather_{year}.json")
    if cache and os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    payload = _fetch_range(start, end)
    if cache:
        with open(cache_path, "w") as f:
            json.dump(payload, f)
    return payload


def load_hourly(start_year, end_year, cache=True):
    """Returns a DataFrame indexed by local (America/Vancouver) hourly
    timestamp, columns [temperature_2m (C), shortwave_radiation (W/m^2),
    cloudcover (%)], spanning start_year..end_year inclusive."""
    frames = []
    for year in range(start_year, end_year + 1):
        payload = _fetch_year(year, cache=cache)
        h = payload["hourly"]
        df = pd.DataFrame({
            "time": pd.to_datetime(h["time"]),
            "temperature_2m": h["temperature_2m"],
            "shortwave_radiation": h["shortwave_radiation"],
            "cloudcover": h["cloudcover"],
        }).set_index("time")
        frames.append(df)
    out = pd.concat(frames).sort_index()
    out = out[~out.index.duplicated(keep="first")]
    return out


def load_range(start_date, end_date, cache=False):
    """Direct fetch for an arbitrary [start_date, end_date] range (YYYY-MM-DD),
    e.g. for calibrating against a specific real bill period -- not cached by
    default since these are one-off ad hoc ranges, not the main multi-year pull."""
    payload = _fetch_range(start_date, end_date)
    h = payload["hourly"]
    df = pd.DataFrame({
        "time": pd.to_datetime(h["time"]),
        "temperature_2m": h["temperature_2m"],
        "shortwave_radiation": h["shortwave_radiation"],
        "cloudcover": h["cloudcover"],
    }).set_index("time")
    return df


if __name__ == "__main__":
    df = load_hourly(2016, 2025)
    print(f"{len(df)} hourly rows, {df.index.min()} -> {df.index.max()}")
    print(df.describe())
    n_missing = df.isna().sum()
    print("missing values per column:\n", n_missing)
