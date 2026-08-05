"""A generalized scenario engine -- the reusable core `capacity_sizing.py`'s
Phase 3 was a single fixed instance of. Every hardware cost, rebate rule,
and electricity rate is a PARAMETER here, not a module constant, so the
`SCENARIO_BUILDER.ipynb` notebook can let a user plug in updated hardware
prices, a different jurisdiction's rebate/rate structure, or a cheaper
battery/balcony-solar option WITHOUT editing this file -- the actual point
Fraser asked for ("generically useful even if only some features are used").

Reuses, unchanged: `gp_forecast_model.py` (Method 2's fitted GP, Phase 1's
own winning dispatch policy), `dispatch_sim.py` (the battery/grid
simulator), `daily_agg.py` (the real 2016-2025 Vancouver weather+load
record). Only the ECONOMICS layer (`rate_model.py`'s BC-Hydro-specific
constants, `capacity_sizing.py`'s hardware constants) is generalized here.

**Real, sourced presets** (not required -- fully overridable): Tesla-
Powerwall-class and generic BC solar (`research/
05_bc_solar_battery_rebates_corrected.md`), Anker SOLIX and balcony/plug-in
solar (`research/06_alternative_hardware_options.md`), BC Hydro's real
tiered+TOD rate structure (`rate_model.py`, self-test-verified against a
real bill). Every preset is tagged with its source currency -- this module
does not silently mix currencies; `to_base_currency` is explicit.
"""

import numpy as np

# ---------------------------------------------------------------------
# Exchange rates -- illustrative, approximate, EDITABLE. Not fetched live.
# ---------------------------------------------------------------------
DEFAULT_FX_TO_CAD = {"CAD": 1.00, "USD": 1.38, "EUR": 1.48}


def to_base_currency(amount, currency, fx_rates=DEFAULT_FX_TO_CAD, base="CAD"):
    """Convert `amount` from `currency` into `base`. Raises on an unknown
    currency rather than silently passing the number through -- a missing FX
    entry is a configuration error, and the failure mode it used to produce
    (a KeyError deep inside a grid search, or worse, an unconverted figure)
    is far harder to diagnose than an explicit message here."""
    for c in (currency, base):
        if c not in fx_rates:
            raise KeyError(
                f"no FX rate for {c!r}; known currencies are {sorted(fx_rates)}. "
                f"Add it to fx_rates (rates are expressed as units of CAD per 1 unit "
                f"of the currency).")
    return amount * fx_rates[currency] / fx_rates[base]


# ---------------------------------------------------------------------
# Hardware catalog -- each entry is a plain dict, fully overridable.
# `unit_cost`/`currency`/`unit` describe a per-kW (solar) or per-kWh
# (battery) continuously-scalable option; `rebate_per_unit`/`rebate_cap`/
# `rebate_pct_cap` describe the rebate rule (set to 0/None to disable);
# `fixed_kw` marks a FIXED-SIZE option (e.g. balcony solar is sold as a
# discrete ~0.8kW kit, not a continuously-sizeable rooftop array) --
# fixed-size options are meant for `run_named_scenario`, not the
# continuous grid optimizer.
# ---------------------------------------------------------------------
SOLAR_OPTIONS = {
    # NOTE: unit_cost is $/kW (not $/W) -- `research/05...md`'s own $2.90/W figure x 1000.
    # Caught and fixed during testing: an earlier draft used $2.90 directly against a kW
    # quantity, undercosting an 8kW system by ~1568x ($11.60 instead of ~$18,200 net).
    "bc_generic_rooftop": dict(
        label="Generic BC rooftop solar", currency="CAD", unit_cost=2900.0,
        rebate_per_unit=1000.0, rebate_cap=5000.0, rebate_pct_cap=0.5, rebate_currency="CAD",
        lifetime_years=25.0, fixed_kw=None,
        source="research/05_bc_solar_battery_rebates_corrected.md",
    ),
    "balcony_solar_de": dict(
        label="German Balkonkraftwerk (800W, Berlin/Munich subsidy)", currency="EUR",
        unit_cost=None, fixed_cost=600.0, fixed_kw=0.8,
        rebate_per_unit=None, rebate_fixed=500.0, rebate_pct_cap=None, rebate_currency="EUR",
        lifetime_years=20.0,
        source="research/06_alternative_hardware_options.md",
        note="Berlin/Munich city subsidy only -- most German cities have no local grant. "
             "BC/Vancouver grid-tie legality not confirmed -- illustrative cost anchor only.",
    ),
    "balcony_solar_us": dict(
        label="US balcony/plug-in solar kit (800W, no dedicated subsidy)", currency="USD",
        unit_cost=None, fixed_cost=525.0, fixed_kw=0.8,
        rebate_per_unit=None, rebate_fixed=0.0, rebate_pct_cap=None,
        lifetime_years=20.0,
        source="research/06_alternative_hardware_options.md",
        note="No dedicated federal/state balcony-solar subsidy confirmed; general 30% US "
             "federal ITC MAY apply depending on install permanency -- not claimed here. "
             "BC/Vancouver legality not confirmed.",
    ),
}

BATTERY_OPTIONS = {
    "tesla_powerwall": dict(
        label="Tesla Powerwall 3-class", currency="CAD", unit_cost=1185.0,
        rebate_per_unit=500.0, rebate_cap=1500.0, rebate_pct_cap=0.5, rebate_currency="CAD",
        lifetime_years=10.0, fixed_kwh=None, requires_solar=True,
        source="research/05_bc_solar_battery_rebates_corrected.md",
    ),
    "anker_solix_low": dict(
        label="Anker SOLIX (low end of real 2026 range)", currency="USD", unit_cost=700.0,
        # Hardware priced in USD; the rebate is BC Hydro's, defined in CAD. This is the
        # exact mixed-currency case CODE_REVIEW.md M1 was about -- `rebate_currency` must
        # be stated, or the CAD rebate would be treated as USD and over-credited by 38%.
        rebate_per_unit=500.0, rebate_cap=1500.0, rebate_pct_cap=0.5, rebate_currency="CAD",
        lifetime_years=10.0, fixed_kwh=None, requires_solar=True,
        source="research/06_alternative_hardware_options.md",
        note="Real 2026 USD range is $700-$1,300/kWh; this preset uses the low end. "
             "BC Hydro's real battery rebate rule (source: research/05) is applied on top "
             "regardless of brand -- not a claim BC Hydro endorses this specific product.",
    ),
    "anker_solix_high": dict(
        label="Anker SOLIX (high end of real 2026 range)", currency="USD", unit_cost=1300.0,
        rebate_per_unit=500.0, rebate_cap=1500.0, rebate_pct_cap=0.5, rebate_currency="CAD",
        lifetime_years=10.0, fixed_kwh=None, requires_solar=True,
        source="research/06_alternative_hardware_options.md",
    ),
    "no_battery": dict(
        label="No battery", currency="CAD", unit_cost=0.0, rebate_per_unit=0.0,
        rebate_cap=0.0, rebate_pct_cap=0.0, lifetime_years=1.0, fixed_kwh=None,
        requires_solar=False,
    ),
}

# ---------------------------------------------------------------------
# Rate presets -- tiers are a list of (upper_bound_kwh_per_month, rate_per_kwh),
# in ascending order, last tier's upper_bound should be float('inf').
# ---------------------------------------------------------------------
RATE_PRESETS = {
    "bc_hydro_2026": dict(
        label="BC Hydro 2026 (real, tiered + optional TOD)",
        tiers=[(675.0, 0.1097), (float("inf"), 0.1408)],
        basic_charge_per_month=6.17,
        tod_discount=0.05, tod_surcharge=0.05,
        offpeak_hours=set(range(0, 7)), peak_hours=set(range(16, 21)),
        # Real RS 2289 self-generation export credit, effective 2026-07-01, flat and
        # settled per billing cycle -- research/08_bc_hydro_export_compensation.md.
        export_credit_per_kwh=0.10,
        source="research/04_vancouver_real_calibration_case.md, "
               "research/08_bc_hydro_export_compensation.md, rate_model.py",
    ),
    "flat_rate_example": dict(
        label="Illustrative flat rate (no tiers, no TOD) -- EDIT ME for your own utility",
        tiers=[(float("inf"), 0.15)],
        basic_charge_per_month=0.0,
        tod_discount=0.0, tod_surcharge=0.0,
        offpeak_hours=set(), peak_hours=set(),
        export_credit_per_kwh=0.0,  # set to your own utility's export/feed-in rate
    ),
}


def tiered_cost(kwh, rate_structure, n_days=30.44):
    """Generalized `rate_model.monthly_tiered_cost` -- any number of tiers,
    linearly prorated for a period of `n_days`."""
    scale = n_days / 30.44
    remaining = kwh
    cost = 0.0
    prev_bound = 0.0
    for upper_bound, rate in rate_structure["tiers"]:
        band = max(0.0, min(remaining, (upper_bound - prev_bound) * scale if upper_bound != float("inf") else remaining))
        cost += band * rate
        remaining -= band
        prev_bound = upper_bound
        if remaining <= 0:
            break
    cost += rate_structure["basic_charge_per_month"] * scale
    return cost


def total_cost(grid_import_kwh, timestamps, rate_structure, use_tod=True, grid_export_kwh=None):
    """Generalized `rate_model.total_cost_with_tod`.

    `grid_export_kwh`: optional hourly export array. When supplied, the rate
    structure's `export_credit_per_kwh` is applied per billing cycle, capped
    at that cycle's energy charge (BC Hydro's real RS 2289 rule -- credits
    cover Energy Charges only, never the basic charge; see
    `research/08_bc_hydro_export_compensation.md`). A rate preset with no
    `export_credit_per_kwh` key credits nothing, preserving old behaviour."""
    grid_import_kwh = np.asarray(grid_import_kwh, dtype=float)
    if grid_export_kwh is not None:
        grid_export_kwh = np.asarray(grid_export_kwh, dtype=float)
    months = timestamps.to_period("M")
    hours = timestamps.hour.values
    offpeak = np.isin(hours, list(rate_structure["offpeak_hours"]))
    peak = np.isin(hours, list(rate_structure["peak_hours"]))
    apply_tod = use_tod and (rate_structure["tod_discount"] or rate_structure["tod_surcharge"])
    credit_rate = rate_structure.get("export_credit_per_kwh", 0.0) or 0.0

    cost = 0.0
    for m in months.unique():
        mask = (months == m).values if hasattr(months == m, "values") else (months == m)
        kwh = grid_import_kwh[mask].sum()
        n_days_in_bin = mask.sum() / 24.0

        basic = rate_structure["basic_charge_per_month"] * (n_days_in_bin / 30.44)
        energy_charge = tiered_cost(kwh, rate_structure, n_days=n_days_in_bin) - basic

        if apply_tod:
            energy_charge += -rate_structure["tod_discount"] * grid_import_kwh[mask & offpeak].sum()
            energy_charge += rate_structure["tod_surcharge"] * grid_import_kwh[mask & peak].sum()

        if grid_export_kwh is not None and credit_rate:
            energy_charge -= min(grid_export_kwh[mask].sum() * credit_rate,
                                 max(energy_charge, 0.0))

        cost += energy_charge + basic
    return cost


def _hardware_capital(quantity, hw, fx_rates):
    """(gross, rebate, net) for one hardware option, ALL in the base currency.
    Handles both continuously-scaled options (`unit_cost` per kW/kWh) and
    fixed-size options (`fixed_cost` for a discrete kit, e.g. balcony solar) --
    `quantity` for a fixed-size option is expected to equal its own
    `fixed_kw`/`fixed_kwh` (a discrete purchase, not a continuous size).

    **Currency handling (CODE_REVIEW.md M1).** An option's PRICE and its
    REBATE are frequently denominated differently -- the common real case is
    exactly the one this catalog already contains: hardware priced in USD
    (an Anker SOLIX unit) qualifying for a rebate defined by a Canadian
    utility in CAD. An earlier version converted `gross` but not the rebate,
    so `rebate_per_unit`, `rebate_cap` and `rebate_fixed` were compared
    against base-currency figures while still carrying their own units --
    silently wrong by the FX factor (38% for USD) for any option whose
    rebate is denominated in its own non-base currency.

    Every hardware entry may therefore declare `rebate_currency`. It
    **defaults to the entry's own `currency`**, which is the intuitive
    reading of a self-contained catalog entry: if you write a price and a
    rebate in one dict without saying otherwise, they are in the same money.
    Entries where that is NOT true (the BC-rebate-on-USD-hardware presets)
    declare `rebate_currency="CAD"` explicitly."""
    if quantity <= 0:
        return 0.0, 0.0, 0.0

    price_ccy = hw["currency"]
    rebate_ccy = hw.get("rebate_currency", price_ccy)

    if hw.get("unit_cost") is not None:
        gross = to_base_currency(quantity * hw["unit_cost"], price_ccy, fx_rates)
        rebate = 0.0
        if hw.get("rebate_per_unit"):
            # Convert the rebate and its own cap out of `rebate_ccy` FIRST, so all
            # three quantities in the min() below are in the base currency.
            raw = to_base_currency(quantity * hw["rebate_per_unit"], rebate_ccy, fx_rates)
            cap = hw.get("rebate_cap")
            cap = to_base_currency(cap, rebate_ccy, fx_rates) if cap else float("inf")
            pct_cap = (hw.get("rebate_pct_cap") or 1.0) * gross  # already base-currency
            rebate = min(raw, cap, pct_cap)
    else:
        gross = to_base_currency(hw.get("fixed_cost", 0.0), price_ccy, fx_rates)
        rebate = to_base_currency(hw.get("rebate_fixed", 0.0), rebate_ccy, fx_rates)
        rebate = min(rebate, (hw.get("rebate_pct_cap") or 1.0) * gross)

    rebate = min(rebate, gross)  # a rebate can never exceed the purchase price
    return gross, rebate, gross - rebate


def capital_cost_annualized(solar_kw, battery_kwh, solar_hw, battery_hw, fx_rates=DEFAULT_FX_TO_CAD):
    """Real net (rebate-adjusted) annualized capital cost, in the base
    currency (CAD by default). Handles both continuously-scaled options
    (rooftop solar, most batteries) and fixed-size options (balcony solar)
    via `_hardware_capital`."""
    _, _, solar_net = _hardware_capital(solar_kw, solar_hw, fx_rates)

    if battery_hw.get("requires_solar") and solar_kw <= 0:
        # Real BC Hydro rule: battery rebate is only available installed with solar --
        # pay full gross cost, no rebate, if there's no solar in this configuration.
        battery_hw_no_rebate = dict(battery_hw, rebate_per_unit=0.0, rebate_fixed=0.0)
        _, _, battery_net = _hardware_capital(battery_kwh, battery_hw_no_rebate, fx_rates)
    else:
        _, _, battery_net = _hardware_capital(battery_kwh, battery_hw, fx_rates)

    solar_lt = solar_hw.get("lifetime_years", 25.0)
    battery_lt = battery_hw.get("lifetime_years", 12.0)
    annualized = (solar_net / solar_lt if solar_kw > 0 else 0.0) + \
                 (battery_net / battery_lt if battery_kwh > 0 else 0.0)
    return annualized, solar_net, battery_net


def run_scenario(solar_kw, battery_kwh, solar_hw, battery_hw, rate_structure,
                 gp, net_load_series, test_hourly, n_years):
    """Full economics for one (solar_kw, battery_kwh, hardware, rate)
    combination, using Method 2's fitted GP forecast (Phase 1's own winning
    dispatch policy) over the real held-out record. Returns a dict with
    capital/grid/total annualized $, self-sufficiency (energy-weighted), and
    a second metric -- fraction of days with ZERO grid import at all
    ("self-sufficient all the time" vs. "most of the time")."""
    import gp_forecast_model as gpf
    from dispatch_sim import simulate_with_targets
    from solar_model import pv_output_kw

    solar_kw_series = pv_output_kw(test_hourly["shortwave_radiation"].values, nameplate_kw=solar_kw)
    load_kw_series = test_hourly["load_kw"].values
    timestamps = test_hourly.index

    test_dates = np.array(sorted(set(timestamps.date)))
    targets = gpf.predict_targets(gp, test_dates, net_load_series, capacity_kwh=battery_kwh)

    out = simulate_with_targets(solar_kw_series, load_kw_series, timestamps, targets,
                                tod_aware=True, capacity_kwh=battery_kwh)
    grid_annual = total_cost(out["grid_import_kwh"], timestamps, rate_structure, use_tod=True,
                             grid_export_kwh=out["grid_export_kwh"]) / n_years
    cap_annual, solar_net, battery_net = capital_cost_annualized(solar_kw, battery_kwh, solar_hw, battery_hw)

    self_sufficiency = 1.0 - out["grid_import_kwh"].sum() / load_kw_series.sum()
    daily_import = _daily_sum(out["grid_import_kwh"], timestamps)
    frac_fully_self_sufficient_days = float((daily_import <= 1e-6).mean())

    return dict(
        solar_kw=solar_kw, battery_kwh=battery_kwh,
        capital_annualized=cap_annual, grid_annual=grid_annual,
        total_annual=cap_annual + grid_annual,
        solar_net_capital=solar_net, battery_net_capital=battery_net,
        self_sufficiency=self_sufficiency,
        frac_fully_self_sufficient_days=frac_fully_self_sufficient_days,
        export_kwh_per_year=float(out["grid_export_kwh"].sum()) / n_years,
    )


def _daily_sum(hourly_values, timestamps):
    import pandas as pd
    s = pd.Series(hourly_values, index=timestamps)
    return s.resample("D").sum().values


def payback_years(net_capital_cost, annual_savings):
    """Simple (non-discounted) payback period -- years to recoup net
    capital cost via cumulative annual savings vs. a baseline. Returns
    float('inf') if savings <= 0 (never pays back)."""
    if annual_savings <= 0:
        return float("inf")
    return net_capital_cost / annual_savings


def cumulative_savings_curve(net_capital_cost, annual_savings, horizon_years=20):
    years = np.arange(0, horizon_years + 1)
    return years, -net_capital_cost + years * annual_savings


def optimize_grid(solar_kw_grid, battery_kwh_grid, solar_hw, battery_hw, rate_structure,
                  gp, net_load_series, test_hourly, n_years, objective="cost",
                  self_sufficiency_target=None):
    """Continuous-hardware grid search. objective="cost": returns the
    cheapest config. objective="self_sufficiency": returns the cheapest
    config achieving >= self_sufficiency_target (energy-weighted, "most of
    the time"), or None if no grid point reaches it."""
    rows = []
    for solar_kw in solar_kw_grid:
        for battery_kwh in battery_kwh_grid:
            if battery_kwh > 0 and battery_hw.get("requires_solar") and solar_kw == 0:
                continue
            r = run_scenario(solar_kw, battery_kwh, solar_hw, battery_hw, rate_structure,
                             gp, net_load_series, test_hourly, n_years)
            rows.append(r)

    if objective == "cost":
        best = min(rows, key=lambda r: r["total_annual"])
    elif objective == "self_sufficiency":
        feasible = [r for r in rows if r["self_sufficiency"] >= self_sufficiency_target]
        best = min(feasible, key=lambda r: r["total_annual"]) if feasible else None
    else:
        raise ValueError(f"unknown objective {objective!r}")
    return best, rows
