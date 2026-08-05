#!/usr/bin/env python3
"""Phase 2: single-seed sequential-VoI skip/probe/drill dispatch run.

Reframes `gp_engine/decision.py`/`voi.py`'s Skip/Probe/Drill mining decision
as a day-ahead home-energy dispatch decision: skip = rely on Method 2's
plain GP-forecast target only (Phase 1's own winning method); probe = pay a
small cost for an updated short-horizon read (e.g. a premium forecast
product, or simply waiting a few more hours) before committing; drill =
commit immediately to a full protective pre-charge, anticipating a
high-demand day. State s in {0,1} is whether TODAY is a real, data-derived
high-demand day (net_load in the top 25% of the real 2017-2025 record,
`stress_classifier.py`) -- no engine changes, same
`ACTIONS = ("skip","probe","drill")` tuple every prior VoI lab reuses.

Economics are derived from this lab's OWN already-computed real quantities,
not invented: `delta_kwh` (the real mean net-load gap between high-demand
and normal days, capped at the real 13.5kWh battery capacity) times BC
Hydro's real off-peak/peak effective rates (`rate_model.py`, already used
and self-test-verified in Phase 1) -- because these rates were already
real, sourced, and used, this phase needs no new economic sourcing at all,
closer to `hydro_reserve_lab`'s well-sourced situation than `shm_lab`'s.
Only `c_probe` (cost of the updated forecast read) is illustrative.

Unlike `grid_reserve_lab` (a resimulable synthetic oracle), and like
`shm_lab`/`hydro_reserve_lab`, this lab has ONE fixed real dataset --
bootstrapping means redrawing fresh train/val/test splits of the SAME real
days each seed, not redrawing fresh synthetic scenarios.

Usage: python3 run_dispatch_voi.py [--seed 0] [--c-probe 0.15]
Writes results/dispatch_voi_seed<seed>.json.
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from decision import (ACTIONS, build_payoff_matrix_voi, oracle_value_2action,  # noqa: E402
                      realized_value_with_probe)
from voi import SIGMA_PROBE2_DEFAULT, bayes_action_voi, probe_value  # noqa: E402

import stress_classifier as sc
from rate_model import STEP1_RATE, TOD_DISCOUNT, TOD_SURCHARGE
from battery_sim import DEFAULT_CAPACITY_KWH

C_PROBE_DEFAULT = 0.15  # $, illustrative -- cost of an updated short-horizon forecast read, unsourced


def derive_dispatch_constants():
    """(delta_kwh, c_drill, v_drill_gross) -- delta_kwh is this lab's own
    real mean net-load gap between high-demand and normal days (capped at
    the real battery capacity, the representative full protective
    pre-charge). c_drill/v_drill_gross follow directly from BC Hydro's real
    off-peak/peak effective rates, already used and verified in Phase 1 --
    no new economic sourcing."""
    from daily_agg import build_daily, TEST_YEARS

    X, y, dates, thresh = sc.build_dataset()
    daily = build_daily()
    daily.index = daily.index.date
    years = np.array([d.year for d in daily.index])
    test_mask = (years >= TEST_YEARS[0]) & (years <= TEST_YEARS[1])
    pool = daily.loc[test_mask]
    net_load = pool["net_load_kwh"].values[1:]  # aligned with y
    is_high = y.astype(bool)
    delta_kwh = float(net_load[is_high].mean() - net_load[~is_high].mean())
    delta_kwh = min(max(delta_kwh, 0.0), DEFAULT_CAPACITY_KWH)

    offpeak_eff_rate = STEP1_RATE - TOD_DISCOUNT
    peak_eff_rate = STEP1_RATE + TOD_SURCHARGE
    c_drill = delta_kwh * offpeak_eff_rate
    v_drill_gross = delta_kwh * peak_eff_rate
    return delta_kwh, c_drill, v_drill_gross


def probe_niche_fraction(mean, var, V, sigma_probe2, c_probe):
    skip_idx, drill_idx = ACTIONS.index("skip"), ACTIONS.index("drill")
    p_now = 1.0 / (1.0 + np.exp(-mean))
    ev_skip = V[skip_idx, 0] * (1 - p_now) + V[skip_idx, 1] * p_now
    ev_drill = V[drill_idx, 0] * (1 - p_now) + V[drill_idx, 1] * p_now
    ev_probe = probe_value(mean, var, V, sigma_probe2=sigma_probe2, c_probe=c_probe)
    return float(np.mean(ev_probe > np.maximum(ev_skip, ev_drill)))


def run(seed=0, c_probe=C_PROBE_DEFAULT, sigma_probe2=SIGMA_PROBE2_DEFAULT):
    delta_kwh, c_drill, v_drill_gross = derive_dispatch_constants()
    breakeven_p = c_drill / v_drill_gross
    print(f"delta_kwh={delta_kwh:.2f}  c_drill=${c_drill:.4f}  v_drill_gross=${v_drill_gross:.4f}  "
          f"breakeven P(high-demand)={breakeven_p:.4f}")

    V = build_payoff_matrix_voi(c_drill=c_drill, v_drill_gross=v_drill_gross)
    X, y, dates, thresh = sc.build_dataset()
    print(f"n_days={len(y)}  high-demand-days={int(y.sum())}  base_rate={y.mean():.4f}")

    gpc, svm, X_train, y_train, X_test, y_test, ell, val_ap = sc.fit_classifier(X, y, seed=seed)
    print(f"classifier: ell={ell}  val AP={val_ap:.3f}  n_train={len(y_train)}  n_test={len(y_test)}")

    conditions = sc.all_conditions(gpc, svm, X_test)
    y_test_int = y_test.astype(np.int64)
    oracle = oracle_value_2action(y_test_int, V)

    results = {}
    for name, (p_now, mean, var) in conditions.items():
        actions, ev = bayes_action_voi(p_now, mean, var, V, sigma_probe2=sigma_probe2, c_probe=c_probe)
        realized = realized_value_with_probe(actions, y_test_int, V, c_probe)
        dist = {a: int((actions == i).sum()) for i, a in enumerate(ACTIONS)}
        regret = oracle - realized
        niche_frac = probe_niche_fraction(mean, var, V, sigma_probe2, c_probe) if name == "gpc_full" else 0.0
        results[name] = dict(
            action_distribution=dist, realized_total_usd=float(realized.sum()),
            regret_total_usd=float(regret.sum()), probe_niche_fraction=niche_frac,
        )
        print(f"[{name:9s}] actions={dist}  realized=${realized.sum():.3f}  "
              f"regret=${regret.sum():.3f}  (probe niche frac={niche_frac:.4f})")

    out = dict(
        seed=seed, c_probe=c_probe, delta_kwh=delta_kwh, c_drill=c_drill,
        v_drill_gross=v_drill_gross, sigma_probe2=sigma_probe2, breakeven_p_high_demand=breakeven_p,
        n_train=len(y_train), n_test=len(y_test), n_high_demand_test=int(y_test.sum()),
        ell=ell, val_ap=val_ap, oracle_total_usd=float(oracle.sum()), conditions=results,
    )
    os.makedirs("results", exist_ok=True)
    out_path = f"results/dispatch_voi_seed{seed}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--c-probe", type=float, default=C_PROBE_DEFAULT)
    ap.add_argument("--sigma-probe2", type=float, default=SIGMA_PROBE2_DEFAULT)
    args = ap.parse_args()
    run(args.seed, args.c_probe, args.sigma_probe2)
