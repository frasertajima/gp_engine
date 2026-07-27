"""Phase 2: real EIA-930 data loader.

**A real scoping pivot from LAB_PLAN.md's original Phase 2 sketch, made
directly in this file rather than silently -- see RESULTS_PHASE2.md for the
full reasoning.** The original plan called for NREL WIND Toolkit/NSRDB
per-turbine-site data (126,000+ raw grid cells) to ground individual-site
geography. That data requires HSDS/S3 access to multi-terabyte time series
for a resolution this lab doesn't actually need: EIA-930's own bulk CSV
download (`https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/`,
confirmed reachable directly with no API key, unlike eia.gov's own
Akamai-fronted pages) already publishes REAL hourly generation-by-fuel-type
(including Wind and Solar, separately) for every US Balancing Authority,
continuously updated. Since a real utility-scale wind/solar FLEET in the US
numbers in the hundreds to low thousands of sites (not tens of thousands),
and EIA-930 gives a genuinely real, physically meaningful aggregate signal
per BA, this lab treats **each Balancing Authority as one "site"** in the
five-method ladder -- a real geographic region with a real fleet of
wind/solar generators behind it, at BA-centroid resolution rather than
individual-turbine resolution. This is coarser than individual-site
geography, but it is REAL data (not synthetic), and BA-to-BA correlation in
renewable output during synoptic-scale weather systems (the actual physical
mechanism behind a multi-state wind lull) is a genuine, measurable spatial
signal at this resolution -- see RESULTS_PHASE2.md for what was found.

BA centroids below are illustrative service-territory centers (common
public knowledge of each BA's footprint), NOT generation-weighted centroids
of each BA's actual wind/solar fleet -- stated as an approximation, not
verified against a real plant-location dataset (that would need EIA-860
generator-level data, not fetched in this pass).

Nameplate capacity is approximated as each BA's own empirical maximum
observed wind+solar output over the full 2-year window -- real generation
can't exceed real installed capacity's realistic peak output, but this is a
proxy, not EIA-860's actual reported nameplate figure (not fetched here).
"""

import glob
import os

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_HERE, "data")

# Illustrative BA-centroid lat/lon -- see module docstring's caveat.
# AZPS/SRP are deliberately kept as neighboring Arizona BAs (not merged or
# dropped) -- a real near-duplicate-pair stress test in the spirit of
# cvar_gp_lab's GOOG/GOOGL finding, not avoided.
BA_CENTROIDS = {
    "ERCO": (31.0, -99.5),    # ERCOT, Texas
    "MISO": (42.0, -93.5),    # Midcontinent ISO, Upper-Midwest wind core
    "SWPP": (38.5, -98.0),    # Southwest Power Pool, KS/OK/NE wind corridor
    "PJM":  (40.0, -78.5),    # PJM Interconnection, mid-Atlantic
    "CISO": (37.0, -119.5),   # California ISO
    "PSCO": (39.5, -104.9),   # Public Service Co of Colorado
    "PACE": (41.5, -109.0),   # PacifiCorp East (UT/WY/ID)
    "BPAT": (46.0, -120.5),   # Bonneville Power, Pacific NW
    "NYIS": (42.9, -75.5),    # New York ISO
    "PNM":  (35.0, -106.5),   # Public Service Co of New Mexico
    "WACM": (40.0, -104.5),   # Western Area Power (CO/NM/MT/WY core)
    "NWMT": (46.5, -111.0),   # NorthWestern Energy, Montana
    "PACW": (44.0, -121.5),   # PacifiCorp West, Oregon
    "AZPS": (33.5, -112.0),   # Arizona Public Service
    "SRP":  (33.4, -111.9),   # Salt River Project, AZ (near-neighbor of AZPS, deliberately)
}

_ID_COLS = ["Balancing Authority", "Data Date"]


def _find_fuel_cols(header, fuel):
    """EIA-930's schema drifted between the 2023 and 2024 six-month files
    (found directly, not assumed): 2023 has one plain 'Net Generation (MW)
    from Wind'/'from Solar' column each; 2024 splits each into 'without
    Integrated Battery Storage' / 'with Integrated Battery Storage'
    sub-columns. Match by substring rather than hardcoding either schema,
    excluding the '(Imputed)'/'(Adjusted)' shadow columns EIA-930 also
    publishes for the same fields."""
    prefix = f"Net Generation (MW) from {fuel}"
    return [c for c in header if c.startswith(prefix)
            and "(Imputed)" not in c and "(Adjusted)" not in c]


def _clip_ba_outliers(df, col="renewable_mw", pct=99.9):
    """A real EIA-930 data-quality bug, found directly (not assumed):
    SWPP reports a single hourly value of 3,589,477 MW on 2023-06-12 --
    physically impossible (larger than the entire US wind+solar fleet;
    SWPP's own real hourly values otherwise top out around 23,000 MW) and
    the kind of isolated reporting glitch EIA's own "known issues" pages
    document. Left unfixed, this one hour inflated SWPP's max-based
    nameplate-capacity proxy 10x (154,987 MW vs. a real ~23,000-25,000 MW
    peak) and would have silently wrecked Method 0's deterministic-rule
    baseline. Fixed with a standard per-BA winsorization: any hourly value
    above that BA's own 99.9th percentile is treated as missing (NaN,
    excluded from the daily mean via pandas' default skipna) rather than
    dropping the whole BA or hand-patching one date -- a general fix, not a
    one-off patch for this one BA/date."""
    out = df.copy()
    caps = out.groupby("Balancing Authority")[col].transform(lambda s: s.quantile(pct / 100.0))
    out.loc[out[col] > caps, col] = np.nan
    return out


def _load_raw(files):
    frames = []
    for path in files:
        header = pd.read_csv(path, nrows=0).columns.tolist()
        wind_cols = _find_fuel_cols(header, "Wind")
        solar_cols = _find_fuel_cols(header, "Solar")
        usecols = _ID_COLS + wind_cols + solar_cols
        df = pd.read_csv(path, usecols=usecols)
        df = df[df["Balancing Authority"].isin(BA_CENTROIDS.keys())].copy()
        renewable = df[wind_cols + solar_cols].fillna(0.0).sum(axis=1).clip(lower=0.0)
        frames.append(df[_ID_COLS].assign(renewable_mw=renewable))
    raw = pd.concat(frames, ignore_index=True)
    return _clip_ba_outliers(raw)


def _daily_renewable_mw(df):
    """Average by (BA, date) to a daily mean MW figure -- comparable units
    to nameplate MW, the same convention dgp_simulator.py's synthetic
    shortfall used. Fuel-column summing already happened in `_load_raw`
    (per-file, since which columns exist depends on that file's schema)."""
    daily = df.groupby(["Balancing Authority", "Data Date"])["renewable_mw"].mean()
    return daily.reset_index()


# Annual + semiannual + ~4-month cycle -- enough to capture a real seasonal
# shape (summer solar peak, winter wind peak, etc.) without enough degrees
# of freedom (7 total: 1 mean + 2 per harmonic) to fit day-to-day weather
# noise the way a rolling window could. A knob, not a claim -- picked to be
# smooth by construction; not cross-validated against alternate orders in
# this pass.
N_HARMONICS = 3
_YEAR_LENGTH = 365.25


def _fit_harmonic_climatology(pivot, n_harmonics=N_HARMONICS):
    """Per-BA least-squares fit of `n_harmonics` sinusoids (+ mean) against
    day-of-year, replacing a 30-day rolling-mean climatology (see
    load_real_fleet_and_shortfall's docstring for why). Fit independently
    per column since different BAs can have different missing-day patterns
    (NaN rows excluded from that column's own fit). Returns
    dict(coefs: (2*n_harmonics+1, n_sites), n_harmonics)."""
    doy = pivot.index.dayofyear.to_numpy(dtype=np.float64)
    design = _harmonic_design(doy, n_harmonics)
    Y = pivot.to_numpy()
    coefs = np.full((design.shape[1], Y.shape[1]), np.nan)
    for j in range(Y.shape[1]):
        y = Y[:, j]
        mask = ~np.isnan(y)
        if mask.sum() <= design.shape[1]:
            raise ValueError(f"column {j}: too few non-missing days to fit "
                              f"{n_harmonics} harmonics")
        coefs[:, j], *_ = np.linalg.lstsq(design[mask], y[mask], rcond=None)
    return dict(coefs=coefs, n_harmonics=n_harmonics)


def _harmonic_design(doy, n_harmonics):
    theta = 2.0 * np.pi * doy / _YEAR_LENGTH
    cols = [np.ones_like(theta)]
    for k in range(1, n_harmonics + 1):
        cols.append(np.cos(k * theta))
        cols.append(np.sin(k * theta))
    return np.stack(cols, axis=1)


def _harmonic_predict(harmonic_fit, doy):
    """Continuous in day-of-year (a Fourier series has no notion of a
    year boundary or a max day-of-year) -- a leap-year day 366 is just a
    slightly larger angle than day 365, no special-casing needed, unlike
    the rolling-mean version this replaced."""
    design = _harmonic_design(np.asarray(doy, dtype=np.float64), harmonic_fit["n_harmonics"])
    return design @ harmonic_fit["coefs"]


def load_real_fleet_and_shortfall(train_files_glob="EIA930_BALANCE_2023_*.csv",
                                   test_files_glob="EIA930_BALANCE_2024_*.csv"):
    """Returns (fleet, train_shortfall, test_shortfall, train_dates, test_dates,
    train_signed_shortfall, test_signed_shortfall).

    fleet: dict(lat, lon, nameplate_mw, n) -- same shape as fleet.py's
    synthetic build_fleet, so every Phase-1 method (naive_baselines.py,
    gp_shortfall_model.py, regime_mixture.py, reserve_calc.py) works
    UNCHANGED on real data.

    train/test_shortfall are the usual one-sided (clipped at 0, per-site)
    arrays every other method uses. train/test_signed_shortfall are the
    UNCLIPPED (climatology - actual) per-site arrays -- summing signed
    values across sites lets an over-performing site offset an
    under-performing one before any clipping happens, unlike summing the
    already-clipped per-site shortfalls (which creates a spurious
    near-zero mass point at the fleet-total level -- see
    RESULTS_PHASE2.md's "Follow-up" section). Only regime_mixture.py's GMM
    regime-detection feature needs the signed version; every reserve-sizing
    calculation still correctly uses the clipped one.

    Climatology (the "expected" output each day is measured against) is a
    per-BA harmonic/Fourier seasonal fit (see `_fit_harmonic_climatology`)
    on TRAINING-year daily output only, applied to both train and test --
    a real out-of-sample climatology, not fit on the test year, so there's
    no leakage into the held-out reliability score. shortfall = max
    (climatology - actual, 0), the same one-sided definition Phase 0
    validated (RESULTS_PHASE0.md).

    NOT a 30-day rolling mean (the first version of this function, see
    RESULTS_PHASE2.md's "Follow-up" section) -- Fraser's diagnosis, checked
    and confirmed: a rolling window is still local enough to track some of
    the same day-to-day/multi-day weather variability the shortfall signal
    is supposed to measure AGAINST, leaking real regime-relevant variance
    into the "expected" baseline itself and flattening the fitted GMM's
    regime split toward an uninformatively-wide ~85%/15% partition. A
    low-order harmonic fit (a handful of annual/semiannual/etc. sinusoids,
    smooth by construction, no per-day degrees of freedom to absorb weather
    noise) is the standard way to separate a true seasonal cycle from
    shorter-timescale anomalies.
    """
    train_paths = sorted(glob.glob(os.path.join(_DATA_DIR, train_files_glob)))
    test_paths = sorted(glob.glob(os.path.join(_DATA_DIR, test_files_glob)))
    if not train_paths or not test_paths:
        raise FileNotFoundError(
            f"expected EIA-930 CSVs under {_DATA_DIR} -- see RESULTS_PHASE2.md "
            f"for the download URLs (eia.gov/electricity/gridmonitor/sixMonthFiles/)")

    raw_train = _load_raw(train_paths)
    raw_test = _load_raw(test_paths)
    daily_train = _daily_renewable_mw(raw_train)
    daily_test = _daily_renewable_mw(raw_test)

    ba_list = sorted(BA_CENTROIDS.keys())
    lat = np.array([BA_CENTROIDS[b][0] for b in ba_list])
    lon = np.array([BA_CENTROIDS[b][1] for b in ba_list])

    def _pivot(daily):
        p = daily.pivot(index="Data Date", columns="Balancing Authority", values="renewable_mw")
        p = p.reindex(columns=ba_list)
        p.index = pd.to_datetime(p.index, format="%m/%d/%Y")
        return p.sort_index()

    train_pivot = _pivot(daily_train)
    test_pivot = _pivot(daily_test)

    # Nameplate proxy: empirical max observed output across BOTH years
    # (see module docstring's caveat -- an approximation, not EIA-860).
    nameplate_mw = pd.concat([train_pivot, test_pivot]).max(axis=0).to_numpy()
    n = len(ba_list)
    fleet = dict(lat=lat, lon=lon, nameplate_mw=nameplate_mw, n=n, ba_list=ba_list)

    # Climatology: low-order harmonic (Fourier) seasonal fit of TRAINING
    # data only -- see _fit_harmonic_climatology's docstring for why this
    # replaced a 30-day rolling mean. A harmonic function is continuous in
    # day-of-year, so a leap-year day 366 (no rolling-mean row existed for
    # it before) is handled naturally -- no clipping/borrowing hack needed.
    harmonic_fit = _fit_harmonic_climatology(train_pivot, n_harmonics=N_HARMONICS)

    def _shortfall(pivot):
        clim = _harmonic_predict(harmonic_fit, pivot.index.dayofyear.to_numpy())
        actual = pivot.to_numpy()
        actual = np.where(np.isnan(actual), clim, actual)  # missing days: assume climatology (no shortfall)
        signed = clim - actual
        return np.clip(signed, 0.0, None), signed

    train_shortfall, train_signed = _shortfall(train_pivot)
    test_shortfall, test_signed = _shortfall(test_pivot)

    return (fleet, train_shortfall, test_shortfall, train_pivot.index, test_pivot.index,
            train_signed, test_signed)


if __name__ == "__main__":
    fleet, train_sf, test_sf, train_dates, test_dates, _, _ = load_real_fleet_and_shortfall()
    print(f"fleet: {fleet['n']} real BAs, nameplate proxy range "
          f"{fleet['nameplate_mw'].min():,.0f}-{fleet['nameplate_mw'].max():,.0f} MW")
    print(f"train: {len(train_dates)} days ({train_dates.min().date()}..{train_dates.max().date()}), "
          f"mean daily fleet shortfall {train_sf.sum(axis=1).mean():,.0f} MW")
    print(f"test:  {len(test_dates)} days ({test_dates.min().date()}..{test_dates.max().date()}), "
          f"mean daily fleet shortfall {test_sf.sum(axis=1).mean():,.0f} MW")
