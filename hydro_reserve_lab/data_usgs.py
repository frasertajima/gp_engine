"""Loader for real USGS daily-discharge data (RDB format, `data/usgs_<site>_dv.rdb`), five Colorado
River Basin gauges spanning the Upper Basin (spatial spread for the pooling lever):

- 09380000  Colorado River at Lees Ferry, AZ   (the compact-point gauge; record from 1921-10-01,
            NOTE: flow post-1963 is Glen Canyon Dam-regulated, not natural — a real simplification
            flagged in LAB_PLAN.md, not hidden)
- 09315000  Green River at Green River, UT      (record from 1905-03-01)
- 09180500  Colorado River near Cisco, UT        (record from 1913-10-01)
- 09152500  Gunnison River near Grand Junction, CO (record from 1901-10-01)
- 09379500  San Juan River near Bluff, UT         (record from 1914-10-30)

Data pulled 2026-07-28 via the directly-verified-open `waterservices.usgs.gov/nwis/dv` endpoint
(`research/06_usgs_data_access.md`) — real, provisional-flagged USGS discharge (parameter 00060,
mean daily, cfs), not synthetic.
"""

import numpy as np
import pandas as pd

SITES = {
    "09380000": "Colorado River at Lees Ferry, AZ",
    "09315000": "Green River at Green River, UT",
    "09180500": "Colorado River near Cisco, UT",
    "09152500": "Gunnison River near Grand Junction, CO",
    "09379500": "San Juan River near Bluff, UT",
}


def _load_site_daily(site):
    path = f"data/usgs_{site}_dv.rdb"
    rows = []
    with open(path) as fh:
        lines = [ln for ln in fh if not ln.startswith("#")]
    # first two remaining lines are the column-name header and the RDB format-width header
    header = lines[0].rstrip("\n").split("\t")
    for line in lines[2:]:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        date_str, value_str = parts[2], parts[3]
        try:
            value = float(value_str)
        except ValueError:
            continue  # missing/ice-affected/non-numeric daily value, skip
        rows.append((date_str, value))
    df = pd.DataFrame(rows, columns=["date", "discharge_cfs"])
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")["discharge_cfs"]


def _water_year(date):
    # USGS water year: Oct 1 (year-1) through Sep 30 (year) is water year `year`
    return date.year + 1 if date.month >= 10 else date.year


def load_water_year_means():
    """Returns a DataFrame indexed by water year, one column per site (mean daily discharge,
    cfs, over that water year), restricted to years where ALL five sites have a complete or
    near-complete record (>=350 days), and a dict of site metadata."""
    per_site_wy = {}
    for site in SITES:
        s = _load_site_daily(site)
        wy = s.groupby(s.index.map(_water_year))
        wy_mean = wy.mean()
        wy_count = wy.count()
        wy_mean = wy_mean[wy_count >= 350]  # drop partial years (record start/end fragments)
        per_site_wy[site] = wy_mean

    df = pd.DataFrame(per_site_wy)
    df = df.dropna()  # only years where ALL five sites have a complete, valid record
    return df


if __name__ == "__main__":
    df = load_water_year_means()
    print(f"{len(df)} water years with all 5 gauges complete: {df.index.min()}-{df.index.max()}")
    print(df.describe())
