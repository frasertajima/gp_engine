"""A lumped, single-reservoir storage simulation and Firm Yield solver.

**A documented simplification, stated plainly**: this lab treats the whole Colorado River Basin's
system as one lumped reservoir fed by Lees Ferry's annual flow (converted to acre-feet/year — the
standard USGS cfs-to-acre-foot conversion, 1 cfs-day = 1.983459 acre-feet). Lees Ferry is the real
historical compact-accounting point for the whole basin, so this is a real, if simplified, choice,
not an arbitrary one — but it is not a multi-reservoir Lake-Powell-then-Lake-Mead system the way
the real basin actually operates. The other four gauges (Green River, Cisco, Gunnison, San Juan)
are NOT summed with Lees Ferry (they are partially upstream contributors already integrated into
Lees Ferry's own flow, so summing would double-count real water) — they are used only as
correlated predictor series for the spatial/pooling and regime-detection side of each method.
"""

import numpy as np

CFS_DAY_TO_ACRE_FEET = 1.983459


def cfs_mean_to_annual_af(mean_cfs):
    """Mean daily discharge (cfs) over a ~365.25-day water year -> annual volume (acre-feet)."""
    return mean_cfs * 365.25 * CFS_DAY_TO_ACRE_FEET


def simulate(inflow_traces_af, capacity_af, demand_af, initial_storage_frac=0.5):
    """inflow_traces_af: (n_traces, horizon) array of annual inflow volumes (acre-feet).
    Returns (reliability, shortfall_af_per_trace, shortfall_af_per_trace_year)."""
    inflow_traces_af = np.atleast_2d(inflow_traces_af)
    n_traces, horizon = inflow_traces_af.shape
    storage = np.full(n_traces, capacity_af * initial_storage_frac)
    shortfalls = np.zeros((n_traces, horizon))
    for t in range(horizon):
        storage = storage + inflow_traces_af[:, t] - demand_af
        neg = storage < 0
        shortfalls[:, t] = np.where(neg, -storage, 0.0)
        storage = np.clip(storage, 0.0, capacity_af)
    reliability = float((shortfalls == 0).mean())
    shortfall_per_trace = shortfalls.sum(axis=1)
    return reliability, shortfall_per_trace, shortfalls


def find_firm_yield(inflow_traces_af, capacity_af, target_reliability=0.98,
                     demand_lo=0.0, demand_hi=None, n_iter=40):
    """Bisection search for the max demand (acre-feet/year) achieving >= target_reliability,
    pooled across all trace-years (matching AWWA/Seattle-style "fraction of years served"
    reliability, research/05_reliability_standard_firm_yield.md)."""
    if demand_hi is None:
        demand_hi = float(np.mean(inflow_traces_af)) * 2.5  # generous upper bound, refined by bisection
    lo, hi = demand_lo, demand_hi
    for _ in range(n_iter):
        mid = 0.5 * (lo + hi)
        rel, _, _ = simulate(inflow_traces_af, capacity_af, mid)
        if rel >= target_reliability:
            lo = mid
        else:
            hi = mid
    return lo


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    traces = rng.normal(1_000_000, 200_000, size=(2000, 26))
    fy = find_firm_yield(traces, capacity_af=2_000_000, target_reliability=0.98)
    rel, shortfall, _ = simulate(traces, 2_000_000, fy)
    print(f"Firm yield: {fy:,.0f} AF/yr, achieved reliability on fitting traces: {rel:.4f}")
