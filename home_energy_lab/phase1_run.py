"""Phase 1 -- the dispatch ladder, real 8kW/13.5kWh illustrative system, fit
on one real training year (2016), scored on the real held-out 2017-2025
record (9 years) using BC Hydro's real tiered+optional-TOD rates.

Central open question, stated in advance per this family's own habit: does
Method 3 (or even Method 2) meaningfully beat naive rule-based control at
all, before any VoI layer (Phase 2) is added.

**Re-run 2026-08-05 after CODE_REVIEW.md's C1 and C2.** The ladder now
carries three ABLATIONS alongside the four original methods, because the
original four could not distinguish "the model helps" from "the model is
structurally unable to do anything":

- **0b (persistence, no model)** and **1b (calendar only, no data at all)**
  bracket Method 2. If a fitted GP cannot beat a two-line seasonal rule, the
  GP is not what is producing the result (C2).
- **3b (constant reserve)** brackets Method 3. Method 3's regime response now
  sizes a peak-window discharge reserve rather than the capacity-clipped
  charge target it used to (C1 -- the old version was provably dead on every
  high-demand day). 3b applies the same reserve with a fixed size, so any
  Method 3 advantage over 3b is attributable to the soft-EM layer itself
  rather than to reserving per se.
"""

import json

import numpy as np
import pandas as pd

from daily_agg import build_daily, build_hourly, TRAIN_YEARS, TEST_YEARS
from dispatch_sim import simulate_with_targets
from rate_model import total_cost_with_tod
import naive_baselines as nb
import gp_forecast_model as gpf
import regime_mixture as rm

NAMEPLATE_KW = 8.0


def main():
    daily = build_daily(nameplate_kw=NAMEPLATE_KW)
    daily.index = daily.index.date
    years = np.array([d.year for d in daily.index])
    train_mask = (years >= TRAIN_YEARS[0]) & (years <= TRAIN_YEARS[1])
    test_mask = (years >= TEST_YEARS[0]) & (years <= TEST_YEARS[1])
    train_daily = daily.loc[train_mask]
    test_dates = daily.index[test_mask]
    print(f"train: {len(train_daily)} days ({TRAIN_YEARS[0]})  "
          f"test: {len(test_dates)} days ({TEST_YEARS[0]}-{TEST_YEARS[1]})")

    net_load_series = daily["net_load_kwh"]  # real, full-record, indexed by date

    print("fitting Method 2 (GP) and Method 3 (GP + regime-mixture)...")
    gp = gpf.fit(train_daily)
    gp3, gmm = rm.fit(train_daily)
    print(f"  GP: ell={gp.ell:.2f} sigma_f2={gp.sigma_f2:.2f} sigma_n2={gp.sigma_n2:.2f}")
    print(f"  GMM: means={gmm.means_.ravel()}  weights={gmm.weights_}")

    gp_targets = gpf.predict_targets(gp, test_dates, net_load_series)
    regime_reserves = rm.predict_reserves(gmm, test_dates, net_load_series)
    # Method 3b's fixed reserve is set to Method 3's own MEAN reserve, so the two
    # differ only in how the reserve is allocated across days, not in how much
    # reserving happens on average -- the cleanest possible isolation of the
    # soft-EM layer's per-day sizing.
    const_reserve_kwh = float(np.mean(list(regime_reserves.values())))
    print(f"  regime reserve: mean={const_reserve_kwh:.2f} kWh "
          f"(Method 3b uses this as its fixed reserve)")

    methods = {
        "0_naive_reactive": dict(
            targets=nb.method0_targets(test_dates), tod_aware=False),
        "0b_persistence_no_model": dict(
            targets=nb.method0b_targets(test_dates, net_load_series), tod_aware=True),
        "1_tou_always_full": dict(
            targets=nb.method1_targets(test_dates), tod_aware=True),
        "1b_calendar_only": dict(
            targets=nb.method1b_targets(test_dates), tod_aware=True),
        "2_gp_forecast": dict(
            targets=gp_targets, tod_aware=True),
        "3_gp_regime_mixture": dict(
            targets=rm.predict_targets(gp3, test_dates, net_load_series), tod_aware=True,
            reserves=regime_reserves),
        "3b_gp_constant_reserve": dict(
            targets=gp_targets, tod_aware=True,
            reserves=rm.constant_reserves(test_dates, const_reserve_kwh)),
        # The full model-free reference: calendar targets + constant reserve. Consumes
        # no fitted model of any kind. If this wins, neither the GP nor the soft-EM
        # layer is earning its complexity anywhere in the ladder.
        "3c_model_free_reference": dict(
            targets=nb.method1b_targets(test_dates), tod_aware=True,
            reserves=rm.constant_reserves(test_dates, const_reserve_kwh)),
        # Method 4: the TIER-THRESHOLD-AWARE policy class research/04 asked for and
        # which no previous method addressed (CODE_REVIEW.md H3). Same reserve as 3c,
        # so the comparison isolates the tier-awareness itself.
        "4_tier_threshold_aware": dict(
            targets=nb.method4_tier_aware_targets(test_dates, net_load_series),
            tod_aware=True,
            reserves=rm.constant_reserves(test_dates, const_reserve_kwh)),
    }

    hourly = build_hourly(nameplate_kw=NAMEPLATE_KW)
    test_hourly = hourly[hourly.index.year.isin(range(TEST_YEARS[0], TEST_YEARS[1] + 1))]
    solar_kw = test_hourly["solar_kw"].values
    load_kw = test_hourly["load_kw"].values
    timestamps = test_hourly.index

    results = {}
    for name, cfg in methods.items():
        out = simulate_with_targets(solar_kw, load_kw, timestamps, cfg["targets"],
                                    tod_aware=cfg["tod_aware"],
                                    daily_reserve_kwh=cfg.get("reserves"))
        # H3: research/04 asked for BOTH real rate structures to be scored as named
        # alternatives rather than collapsed into one. BC Hydro's TOD layer is OPTIONAL
        # -- a household elects it or not -- so the rational bill is the cheaper of the
        # two, and reporting both shows whether opting in is actually the right call for
        # each policy (it is, for all of them, but that was previously asserted untested).
        cost_tod = total_cost_with_tod(out["grid_import_kwh"], timestamps, use_tod=True,
                                       grid_export_kwh=out["grid_export_kwh"])
        cost_tiered_only = total_cost_with_tod(out["grid_import_kwh"], timestamps, use_tod=False,
                                               grid_export_kwh=out["grid_export_kwh"])
        total_cost = min(cost_tod, cost_tiered_only)
        total_load_kwh = float(load_kw.sum())
        total_grid_import_kwh = float(out["grid_import_kwh"].sum())
        total_grid_export_kwh = float(out["grid_export_kwh"].sum())
        self_sufficiency = 1.0 - total_grid_import_kwh / total_load_kwh
        n_years = (TEST_YEARS[1] - TEST_YEARS[0] + 1)

        results[name] = dict(
            total_cost_usd=total_cost, total_cost_usd_per_year=total_cost / n_years,
            cost_tod_optin_usd_per_year=cost_tod / n_years,
            cost_tiered_only_usd_per_year=cost_tiered_only / n_years,
            rate_election="tod_optin" if cost_tod <= cost_tiered_only else "tiered_only",
            total_grid_import_kwh=total_grid_import_kwh,
            total_grid_export_kwh=total_grid_export_kwh,
            self_sufficiency=self_sufficiency,
            proactive_charge_kwh_per_year=float(out["proactive_charge_kwh"].sum()) / n_years,
        )
        print(f"\n[{name}] total cost over {n_years} yrs: ${total_cost:,.0f} "
              f"(${total_cost/n_years:,.0f}/yr)")
        print(f"  rate election: TOD opt-in ${cost_tod/n_years:,.0f}/yr vs "
              f"tiered-only ${cost_tiered_only/n_years:,.0f}/yr -> "
              f"{results[name]['rate_election']}")
        print(f"  grid import: {total_grid_import_kwh:,.0f} kWh, export: {total_grid_export_kwh:,.0f} kWh")
        print(f"  self-sufficiency: {self_sufficiency:.1%}")
        print(f"  proactive charging: {results[name]['proactive_charge_kwh_per_year']:,.0f} kWh/yr")

    with open("results_phase1.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote results_phase1.json")


if __name__ == "__main__":
    main()
