"""Answers a direct question, precisely: does GP + soft-EM's advantage come
from "not throwing away data," and how much is that worth in THIS lab
specifically (not by analogy to climate_cat_lab's prior finding)?

Runs the IDENTICAL regime-detection GMM (same p_hat, same responsibilities)
through both fit_regime_mixture_soft (every day weighted into BOTH
components) and fit_regime_mixture_hard (each day rounded to exactly one
component, the other never sees it) on both Phase 1's synthetic oracle and
Phase 2's real held-out year -- isolating the soft-vs-hard GP-fitting
difference from every other difference between the phases.
"""

import json

import numpy as np

import data_eia930
import reserve_calc
import regime_mixture
from fleet import build_fleet
from dgp_simulator import sample_true_output

N_METHOD_SCENARIOS = 500_000
RESULTS = {}


def _score(label, fit_fn, shortfall, signed_shortfall, fleet, eval_fn, seed):
    mix = fit_fn(shortfall, fleet, signed_shortfall=signed_shortfall, seed=seed)
    scenarios = regime_mixture.sample_regime_mixture_scenarios(mix, N_METHOD_SCENARIOS, seed=seed)
    reserve_mw = reserve_calc.required_reserve_mw(scenarios.sum(axis=1))
    result = eval_fn(reserve_mw)
    result.update(label=label, reserve_mw=reserve_mw, p_hat=mix["p_hat"], p_hat_raw=mix["p_hat_raw"])
    if "n_drought" in mix:
        result.update(n_drought_days=mix["n_drought"], n_normal_days=mix["n_normal"])
    else:
        result.update(mean_responsibility=mix["mean_responsibility"])
    print(f"  {label:12s} reserve={reserve_mw:10,.1f} MW  " +
          " ".join(f"{k}={v}" for k, v in result.items()
                   if k not in ("label", "reserve_mw", "p_hat", "p_hat_raw")))
    return result


def synthetic():
    print("=== Phase 1 (synthetic oracle) ===")
    fleet = build_fleet(100, seed=0)
    hist = sample_true_output(fleet, 730, seed=1)
    oracle = sample_true_output(fleet, 500_000, seed=2)
    oracle_total = oracle["shortfall_mw"].sum(axis=1)
    true_reserve = reserve_calc.required_reserve_mw(oracle_total)

    def eval_fn(reserve_mw):
        return dict(achieved_reliability=reserve_calc.achieved_reliability(oracle_total, reserve_mw),
                     net_dollar_gap_usd=reserve_calc.score_method(
                         "x", reserve_mw, oracle_total, true_reserve)["net_dollar_gap_usd"])

    soft = _score("soft", regime_mixture.fit_regime_mixture_soft,
                  hist["shortfall_mw"], hist["signed_shortfall_mw"], fleet, eval_fn, seed=1)
    hard = _score("hard", regime_mixture.fit_regime_mixture_hard,
                  hist["shortfall_mw"], hist["signed_shortfall_mw"], fleet, eval_fn, seed=1)
    return dict(true_required_reserve_mw=true_reserve, soft=soft, hard=hard)


def real():
    print("=== Phase 2 (real EIA-930, held out 2024) ===")
    fleet, train_sf, test_sf, train_d, test_d, train_signed, test_signed = \
        data_eia930.load_real_fleet_and_shortfall()
    test_total = test_sf.sum(axis=1)

    def eval_fn(reserve_mw):
        holding = reserve_mw * reserve_calc.RESERVE_COST_PER_MW_YEAR
        excess = np.clip(test_total - reserve_mw, 0.0, None)
        under = float(excess.sum()) * reserve_calc.ILLUSTRATIVE_EVENT_HOURS * reserve_calc.VOLL_PER_MWH
        return dict(achieved_reliability=reserve_calc.achieved_reliability(test_total, reserve_mw),
                     total_annual_cost_usd=holding + under)

    soft = _score("soft", regime_mixture.fit_regime_mixture_soft,
                  train_sf, train_signed, fleet, eval_fn, seed=0)
    hard = _score("hard", regime_mixture.fit_regime_mixture_hard,
                  train_sf, train_signed, fleet, eval_fn, seed=0)
    return dict(soft=soft, hard=hard)


if __name__ == "__main__":
    RESULTS["synthetic"] = synthetic()
    RESULTS["real"] = real()
    with open("results_hard_vs_soft.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    print("\nwrote results_hard_vs_soft.json")
