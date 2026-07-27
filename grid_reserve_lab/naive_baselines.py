"""Methods 0-2 of grid_reserve_lab's five-method ladder (LAB_PLAN.md's
Method section, corrected post-research-pass) -- the deterministic
heuristic and the two statistical baselines that bracket real ISO practice.
Fitting (per-site mean/std/rho, in Python) is cheap and stays here; the
actual Monte Carlo reserve-quantile computation is delegated to the
`reserve_baseline` Rust crate (rayon-parallel) via subprocess+JSON, so the
traditional-method side of the comparison isn't handicapped by a slow
reference implementation -- see LAB_PLAN.md's "Rust component" section.

Unlike climate_cat_lab/naive_baselines.py, this works in RAW MW shortfall
units, not log-ratio space: dgp_simulator.py's shortfall is one-sided
(clipped at 0, see RESULTS_PHASE0.md's methodology fix) and zero-inflated
on normal days, which breaks a clean lognormal-in-ratio-space treatment the
way climate_cat_lab's always-positive dollar losses supported. Every method
in this ladder (0-4) works in raw MW units for consistency -- including
the GP methods, which is itself part of the point: a plain Gaussian
model, in whatever space it's fit, is still elliptical and still can't
represent the true zero-inflated, tail-dependent shortfall distribution.
"""

import json
import os
import subprocess
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_RUST_BIN = os.path.join(_HERE, "reserve_baseline", "target", "release", "reserve_baseline")

WECC_WIND_PCT = 0.05  # research/02_deterministic_reserve_heuristic.md's generic "5% of wind" rule


def fit_independence(shortfall):
    """Per-site marginal Normal fit: mean and std of each site's own
    historical shortfall series. No cross-site structure at all -- fleet
    total shortfall has a thin (CLT) tail by construction. Kept ONLY as an
    academic control (isolates "does correlation shape matter at all"),
    NOT a claim any real ISO does this -- research/03_correlation_
    assumption_resource_adequacy.md found real practice uses real
    historical correlation, not independence."""
    mu = shortfall.mean(axis=0)
    sigma = shortfall.std(axis=0, ddof=1)
    return dict(mu=mu, sigma=sigma, n=shortfall.shape[1])


def fit_aggregate_correlation(shortfall, n_sample_pairs=2000, seed=0):
    """Same per-site marginals as fit_independence, plus ONE fleet-wide
    correlation number -- the real-practice baseline (LAB_PLAN.md's
    corrected Method 2): a single aggregate profile built from real
    historical time-synchronous data, the way MISO's LOLE Study / E3's
    RECAP actually do it, at fleet resolution rather than per-site-pair
    resolution. Coarse in resolution, not naive by assumption."""
    mu = shortfall.mean(axis=0)
    sigma = shortfall.std(axis=0, ddof=1)

    n = shortfall.shape[1]
    rng = np.random.default_rng(seed)
    i_idx, j_idx = np.triu_indices(n, k=1)
    k = min(n_sample_pairs, len(i_idx))
    pick = rng.choice(len(i_idx), size=k, replace=False)
    corrs = [np.corrcoef(shortfall[:, i], shortfall[:, j])[0, 1]
             for i, j in zip(i_idx[pick], j_idx[pick])]
    rho = float(np.clip(np.nanmean(corrs), 0.0, 0.99))
    return dict(mu=mu, sigma=sigma, rho=rho, n=n)


def run_rust_baselines(fleet, independence_fit, aggregate_fit, n_scenarios,
                        target_reliability, seed=0, wecc_wind_pct=WECC_WIND_PCT):
    """Calls the reserve_baseline Rust binary for methods 0 (both variants),
    1, and 2. Returns dict with reserve_mw for each method plus each Monte
    Carlo method's Rust wall-clock time. Requires `reserve_baseline` built
    (`cd reserve_baseline && cargo build --release`)."""
    if not os.path.exists(_RUST_BIN):
        raise FileNotFoundError(
            f"{_RUST_BIN} not found -- build it first: "
            f"cd {os.path.join(_HERE, 'reserve_baseline')} && cargo build --release")

    payload = dict(
        n=int(fleet["n"]),
        mu=independence_fit["mu"].tolist(),
        sigma=independence_fit["sigma"].tolist(),
        rho=aggregate_fit["rho"],
        nameplate_mw=fleet["nameplate_mw"].tolist(),
        n_scenarios=int(n_scenarios),
        target_reliability=float(target_reliability),
        seed=int(seed),
        wecc_wind_pct=float(wecc_wind_pct),
    )
    in_path = os.path.join(_HERE, "_rust_baseline_in.json")
    out_path = os.path.join(_HERE, "_rust_baseline_out.json")
    with open(in_path, "w") as f:
        json.dump(payload, f)

    t0 = time.perf_counter()
    subprocess.run([_RUST_BIN, in_path, out_path], check=True, capture_output=True)
    call_wall = time.perf_counter() - t0

    with open(out_path) as f:
        result = json.load(f)
    result["subprocess_call_wall_s"] = call_wall  # includes process spawn + JSON I/O overhead
    return result


def python_reference_baselines(independence_fit, aggregate_fit, n_scenarios,
                                target_reliability, seed=0):
    """Plain NumPy equivalent of the Rust crate's methods 1-2, for the
    wall-clock fairness comparison LAB_PLAN.md's Rust section calls for --
    same math (per-site Normal draws, clipped at 0, summed; single-factor
    equicorrelation sampler for method 2), vectorized with NumPy rather
    than a naive per-scenario Python loop (a genuinely slow reference would
    make the traditional method look bad on speed for the wrong reason, not
    a fair comparison)."""
    rng = np.random.default_rng(seed + 1000)
    n = independence_fit["n"]

    t0 = time.perf_counter()
    z = rng.standard_normal((n_scenarios, n))
    draws = independence_fit["mu"][None, :] + independence_fit["sigma"][None, :] * z
    total = np.clip(draws, 0.0, None).sum(axis=1)
    reserve_independence = float(np.quantile(total, target_reliability))
    wall_independence = time.perf_counter() - t0

    t0 = time.perf_counter()
    rho = aggregate_fit["rho"]
    f = rng.standard_normal((n_scenarios, 1))
    e = rng.standard_normal((n_scenarios, n))
    z2 = np.sqrt(rho) * f + np.sqrt(max(1.0 - rho, 0.0)) * e
    draws2 = aggregate_fit["mu"][None, :] + aggregate_fit["sigma"][None, :] * z2
    total2 = np.clip(draws2, 0.0, None).sum(axis=1)
    reserve_aggregate = float(np.quantile(total2, target_reliability))
    wall_aggregate = time.perf_counter() - t0

    return dict(
        method1_independence=dict(reserve_mw=reserve_independence, wall_s=wall_independence),
        method2_aggregate_correlation=dict(reserve_mw=reserve_aggregate, wall_s=wall_aggregate),
    )
