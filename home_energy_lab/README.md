# home_energy_lab — does GP + soft-EM regime-awareness earn its keep for home solar/battery/HVAC dispatch?

> **Disclaimer.** This lab is illustrative and educational. Its synthetic load model, thermal model,
> and $ figures are anchored to real published data but are not a substitute for a real home-energy
> audit, a licensed electrician/HVAC contractor's assessment, or a real utility's own rate schedule.
> No output of this lab should be used as the sole basis for a real solar/battery purchase or a real
> HVAC control decision.

**Status: scoped (2026-08-04), research pass DONE (`research/RESEARCH.md`), Phase 0 DONE
(2026-08-04, `RESULTS_PHASE0.md`), Phase 1 DONE (2026-08-04, `RESULTS_PHASE1.md`), Phase 2 DONE
(2026-08-04, `RESULTS_PHASE2.md`), Phase 3 DONE (2026-08-04, `RESULTS_PHASE3.md`) — all core phases
complete. Two notebooks DONE (2026-08-04): `HOME_ENERGY_LAB.ipynb` (consolidated Phase 0-3
write-up) and `SCENARIO_BUILDER.ipynb` (editable hardware/rebate/rate scenario comparison + real
payback-year calculations, built on the new generalized `scenario_engine.py`).**

> **CODE REVIEW AND RE-RUN (2026-08-05) — `CODE_REVIEW.md`.** An internal review of this lab and the
> shared `gp_engine` modules it reuses found two structural modeling errors and one unexamined
> economic assumption, all three of which changed a published headline. **Phases 1 and 3 were
> re-run and both notebooks rebuilt** (0 execution errors). Phase 0 and Phase 2 were re-verified and
> stand unaltered — Phase 2's null survived a sigma_probe2 x c_probe sweep and is now the
> best-verified result in the lab. The errors shared one failure mode — a layer silently losing its
> ability to affect the outcome, whose flat result was then read as a finding about the mechanism —
> which is arguably this lab's most transferable output.
>
> **All five C/H findings are now fixed and re-run (2026-08-05).** Corrected headlines: **Phase 1's
> ladder is a statistical tie at the top** (all eight proactive methods within $34/yr, top three
> within $8); the real effects are proactive off-peak pre-charging (~$163/yr) and a peak-window discharge reserve
> (~$25/yr), neither of them a forecasting result. **Phase 3's optimum is 4-6kW solar / no battery**
> (a $12/yr margin, not the $107/yr the uncredited-export version implied).
>
> **H1 changed two of the C1/C2 conclusions, and the write-ups were corrected rather than left
> standing.** Crediting export moved the GP from $1 *behind* a model-free calendar rule to ~$4
> *ahead*, and shrank the regime layer's penalty from $22/yr to $8/yr — a null, not a negative. The
> strong "no fitted model needed" claim did not survive the lab's own economics fix; the weaker form
> (forecasting is worth ~1% of the bill, not the 6% originally implied) does. H2 sourced the battery
> specs to Tesla's own datasheet (`research/09...md`), yielding three corrections that moved every
> method by a uniform $4-5/yr and reordered nothing. H3 added Method 4 (tier-threshold-aware,
> $504/yr, mid-pack) and now scores both rate structures as named alternatives.
> **ALL M AND L ITEMS NOW FIXED AND RE-RUN (2026-08-05) — the review is fully discharged.**
> Notably **M1** (currency): rebates are now converted explicitly via a `rebate_currency` key with a
> self-test proving FX-invariance — the mixed-currency case (USD hardware + CAD rebate) was
> over-crediting by 38%, which matters directly for the non-CAD use this engine is built for.
> **M3** corrected a mining-shaped drill payoff (a wasted pre-charge loses only the round-trip loss,
> not the whole charge), moving the derived breakeven 0.3738 → 0.0495. **L4** replaced the 7-hour
> off-peak proxy with BC Hydro's real 8-hour 11pm-7am window. Shared modules were changed only in
> backward-compatible ways (six other labs depend on them). **No conclusion reversed.**

## One line

Given a real multi-year weather record and a realistic (EIA-anchored) home load pattern, does the
same GP + soft-EM regime-mixture + sequential-VoI decision stack this codebase already validated
four times (`grid_reserve_lab`, `shm_lab`, `hydro_reserve_lab`, `climate_cat_lab`) also earn its
keep for a **personal-scale** energy system — and separately, what's the economically optimal
solar+battery size for a given load pattern in the first place?

## Why this lab, and why now

Fraser's own framing after the four-lab VoI retrospective: the mechanism is niche but real,
predicted well by "is the classification problem genuinely hard for a plain GP mean" — and every
lab so far has depended on gov/corporate-collected, often proprietary-adjacent data (utility
balancing-authority filings, USGS gauges, real bridge sensor campaigns, insurance capital-model
citations), unlike the `stash`/`pdfstash` family's genuinely open-to-anyone tools. Home solar/
battery/HVAC is the first candidate in this session's search for an end-user-shaped application
that is **structurally identical** to what's already built — a storage reservoir (battery SOC), a
stochastic inflow (solar generation), a stochastic demand (household load, HVAC-dominated), and a
recurring commit-or-wait dispatch decision — while running on **genuinely open, personal-scale
data**: real historical weather (no signup), and a load shape anchored to public EIA statistics
rather than a gated dataset.

**Deliberately scoped as ONE instance, not a generic engine.** Fraser's own EV-charging idea is
structurally the same reservoir/decision shape (SOC ↔ battery, driving demand ↔ household load,
trip-range anxiety ↔ stress-regime dispatch) — but per this session's own established practice
(`decision.py`/`voi.py` were extracted from `bayesian_decision_lab` only *after* one real instance
existed, then reused four times), this lab builds the home-energy instance first and extracts a
shared engine afterward, if this instance's own results justify it. EV charging is noted as the
natural Phase 4/second-instance candidate, not built now.

## Domain background (research pass DONE, 2026-08-04 — see `research/RESEARCH.md`)

- **Real, free, live-verified weather+solar data**: Open-Meteo's Historical Weather API (ERA5
  reanalysis, hourly, from 1940, no API key) — confirmed via a live `curl` test, not assumed from
  docs (`research/01_historical_weather_solar_data.md`).
- **Real, sourced load-shape breakdown**: EIA RECS 2020 — HVAC ~42-52% of home electricity (the
  single largest end use), water heating ~13%, lighting ~9%, refrigeration ~7%, real documented
  summer AC-driven seasonal peak (`research/02_residential_load_profile.md`). A real, individually-
  downloadable per-building alternative (NREL ResStock End-Use Load Profiles, live-verified) is
  flagged as a future cross-check, not the primary driver — the load model itself will be synthetic/
  parametric, calibrated to these real percentages, per Fraser's own preferred design.
- **Real, current solar/battery cost anchors**: Tesla Powerwall 3 ($11,500-$16,500 installed, 13.5
  kWh), $2.55-$3.45/W solar installed (`research/03_solar_battery_economics.md`).
  **⚠ SUPERSEDED (2026-08-04, `research/05...md`)** — `research/03`'s figures are US market data in
  USD including the US 30% federal tax credit, **which does not apply to a BC household**; the real
  BC Hydro rebates and CAD costs replace them. Battery round-trip-efficiency/degradation, deferred
  here to Phase 0 and never actually done, was finally **sourced 2026-08-05 to Tesla's own datasheet**
  (`research/09_battery_spec_primary_source.md`, CODE_REVIEW.md H2).
- **A real household calibration case (2026-08-04)**: Fraser's own BC Hydro bill — a real ~72-day
  billing period (Mar 20-May 30), tier-split by a rate-year boundary: 421 kWh (35.1 kWh/day) for
  Mar 20-31, 1,756 kWh (29.3 kWh/day) for Apr 1-May 30, totaling the originally-quoted 2,177 kWh —
  **an apparent inconsistency (a naive "70 kWh/day for March" reading) found and then resolved with
  more real data in the same session**: the figure was never a calendar month, and the real per-day
  rates need no EV-charging-spike explanation, just a units correction. The real seasonal decline
  (35.1 → 29.3 kWh/day, spring warming) is the anchor to calibrate against, consistent with the
  originally recalled seasonal range (~25/day Sept low, ~35/day Jan high, ~33/day May). Underfloor
  electric resistance heat + home EV charging remain the known load drivers. Real BC Hydro rate
  structure verified: a **tiered threshold**, not a flat TOU price — 10.97¢/kWh for the first 675
  kWh/month, 14.08¢/kWh above that, plus optional Time-of-Day pricing (±5¢/kWh peak/off-peak); a
  real bill can straddle a rate-year boundary, which Phase 0's loader needs to handle. See
  `research/04_vancouver_real_calibration_case.md`.

## Precedent already in this codebase

| This lab's component | Reused from |
|---|---|
| Battery state-of-charge simulator (storage = storage + inflow − demand, clipped) | `hydro_reserve_lab/reservoir_sim.py` — same lumped-reservoir mechanics, relabeled |
| Capacity-sizing solver (given a target reliability, find the minimum-cost system) | `hydro_reserve_lab/reservoir_sim.py::find_firm_yield` + `capital_calc.py`/`reserve_calc.py`'s VaR-quantile shortcut — a 2D (solar, battery) search instead of a single scalar |
| Regime-mixture stress-day detector | `climate_cat_lab`/`grid_reserve_lab`/`hydro_reserve_lab`'s `regime_mixture.py` soft-EM pattern |
| The new classifier stage (a `(mean,var,prob)` triple, since regression/mixture layers alone don't produce one) | `grid_reserve_lab/regime_forecast.py`/`shm_lab/damage_classifier.py`/`hydro_reserve_lab/drought_classifier.py`'s pattern — expect to need this again, per `gp_engine/VOI_DISPATCH_PATTERN.md`'s own lesson |
| Sequential-VoI dispatch decision (Skip/Probe/Drill) | `gp_engine/decision.py` + `voi.py`, unchanged, reused a fifth time |
| GP regression/classification engine | `gp_core.py` / `gp_classifier.py`, unchanged |

## The core hypothesis, stated precisely

Two separate, genuinely different questions, not one:
1. **Dispatch**: does a GP + soft-EM-aware, VoI-informed charge/discharge/HVAC-setpoint policy beat
   naive rule-based control (Method 0/1) and a plain GP forecast (Method 2) on real multi-year
   weather, in $ terms — and per `VOI_DISPATCH_PATTERN.md`'s own headline lesson, does this
   domain's classification problem turn out genuinely hard (→ variance likely helps) or easy (→ it
   likely won't)? Checked directly in Phase 0/2, not assumed either way.
2. **Sizing**: given a chosen load pattern and the real weather record, what solar+battery capacity
   minimizes total lifetime cost (capital + residual grid spend) at a chosen reliability/self-
   sufficiency target — a `hydro_reserve_lab`-style Firm-Yield question, genuinely useful on its
   own regardless of how question 1 comes out.

## Method

**The oracle/data**: real Open-Meteo hourly weather (temperature, shortwave radiation, cloudcover)
for **Vancouver, BC** — a real location with a real personal calibration point (see Domain
background), not an arbitrary illustrative city — a multi-year record (illustrative target: 8-10
years, 2015-2024ish, chosen once real pull volume/rate-limits are checked in Phase 0).

**Solar generation**: a standard panel-efficiency/derate conversion from shortwave radiation to AC
output, scaled to a chosen nameplate kW.

**Load model** (synthetic, EIA-anchored, not a raw ingested dataset): a diurnal + weekday/weekend
base-load curve (water heating/lighting/refrigeration/other) plus a temperature-driven heating term
(a simple degree-day/setpoint model — load ∝ max(0, T_heat−T), Vancouver's real single-sided case)
plus an EV-charging component. **Calibrated against a real anchor, not just EIA aggregate
percentages**: Fraser's own real per-day rates (35.1 kWh/day late March, 29.3 kWh/day Apr-May
average) and the recalled seasonal range (~25/day Sept, ~35/day Jan, ~33/day May) — see
`research/04_vancouver_real_calibration_case.md` for the full reconciliation. Splitting this real
total into a base-load/heating/EV breakdown (rather than just matching the aggregate) is still
Phase 0's job — the pieces are not yet individually verified. The heating setpoint is also a genuine
**decision variable** (pre-heating ahead of an anticipated stress period), not only a passive load.

**Battery**: capacity (kWh), max charge/discharge rate (kW), round-trip efficiency — `reservoir_sim.
py`'s own mechanics, relabeled: "inflow" = solar surplus or grid charging, "demand" = household load
net of solar.

**The stress regime**: a multi-day period of simultaneously low solar and high heating demand —
real, weather-system-driven persistence (winter storm systems), not an i.i.d. day-to-day draw.
**Narrowed by the real location** (`research/04_vancouver_real_calibration_case.md`): Vancouver's
mild oceanic climate makes this a heating-dominated, single-sided case (essentially no meaningful
AC load), not the original two-sided winter-cold-snap-vs-summer-heat-wave framing — simpler and
cleaner to test, to be confirmed directly against the real Open-Meteo pull in Phase 0, not assumed
from general climate knowledge alone.

**Method ladder** (mirrors the family convention): 0 — deterministic rule-based control (charge from
solar surplus, discharge to cover deficit, grid only when battery empty); 1 — TOU-arbitrage-only
heuristic (charge at the cheapest scheduled off-peak window regardless of weather, a common
real-world "smart" default); 2 — vanilla GP day-ahead solar/load forecast informing the same
schedule; 3 — GP + soft-EM regime-mixture (stress-day-aware); 4 — the sequential-VoI dispatch layer
(Skip = follow the default schedule; Probe = pay for/wait for an updated short-horizon forecast
before committing; Drill = proactively charge from grid now, ahead of an anticipated stress period).

**Capacity-sizing solver**: a 2D (solar kW, battery kWh) search minimizing amortized capital cost +
expected real-multi-year grid spend, subject to a target self-sufficiency/reliability level — the
practical "how much do I need" deliverable, using whichever dispatch method Phase 1/2 finds best as
the control policy under test.

## Phases

**Phase 0 — DONE (2026-08-04, `RESULTS_PHASE0.md`).** Real 10 years (2016-2025) of Vancouver
weather pulled (Open-Meteo, 87,672 hourly rows, 0 missing). Load model **calibrated exactly** to
Fraser's real 2-point bill data (base=24.175 kWh/day, heating=0.9006 kWh/degree-day at an 18°C
base) — cross-checked (not fit) against the recalled seasonal range and landed within ~1 kWh/day.
Solar model (8kW illustrative system) gives 999 kWh/yr/kW, within the real plausible 900-1,100
range, with a real 5.6x summer/winter seasonal swing. **The stress-regime hypothesis confirmed
directly on real data, not assumed**: low-solar/high-heating-demand co-occurs 1.78x more than
independence would predict, and shows real 4.5x multi-day persistence (P(stress tomorrow|stress
today)=0.502 vs. marginal 0.111) — genuine weather-system persistence, the mechanism Phase 1's
soft-EM layer exists to capture. Battery simulator built and verified energy-conserving to
floating-point precision after a real bug in the first self-test was caught and fixed (a naive
aggregate energy-balance check that didn't correctly account for round-trip efficiency losses,
replaced with a rigorous per-timestep AC-bus power-balance check). BC Hydro's real tiered+
optional-TOD rate structure and the rate-year-boundary-straddling bill handling are deferred to
Phase 1/2 (where the $ economics actually get used), not needed for Phase 0's own sanity checks.

**Phase 1 — DONE (2026-08-04), RE-RUN AND SUPERSEDED (2026-08-05, `RESULTS_PHASE1.md`).** Fit on one
real training year (2016), scored on the real held-out 2017-2025 record (9 years), real 8kW/13.5kWh
system, real BC Hydro tiered+optional-TOD rates. **Headline after the re-runs (C1/C2, then H1/H2/H3): the top of the
ladder is a statistical tie.** All eight proactive methods sit within $34/yr and the top three
within $8 — under 2% of the bill. The two effects large enough to be real are **proactive off-peak pre-charging ($638 ->
~$475/yr, ~$163)** and **a peak-window discharge reserve (~$25/yr)**; neither is a forecasting
result. Best is GP + constant reserve at $475/yr, with the model-free calendar + same reserve at
$479 and the regime-sized version at $483. The GP's own predictive RMSE (7.04) barely improves on
the lag-1 value it is fed (7.28), which is why its contribution is ~1%.
**A genuinely new lever found during the re-run**: holding battery SOC back through standard-rate
hours so it is available for the real 4-9pm surcharge window is worth ~$10/yr, with a real interior
optimum near 6kWh — over-reserving is actively harmful (a 13.5kWh floor is worse than no reserve at
all). **Regime-awareness genuinely does not help, and this time it is a real test**: the soft-EM
layer now sizes that reserve (correlation +0.660 with actual net load, verified to fire on the
high-demand days), and still loses to a constant reserve of the same mean -- by $22/yr before the
export credit, $8/yr after it. A legitimate fourth instance of this codebase's "regime-awareness
doesn't automatically help" finding, but stated as a NULL rather than a negative: $4/yr is inside
this model's own resolution. The
counter-intuitive self-sufficiency result survives and sharpens: Method 0 has the HIGHEST
self-sufficiency (52.5%) but is the MOST expensive, while the winning model-free policy sits at
41.5% and $613/yr.

**Why the re-run was needed — two errors from the 2026-08-04 run, both found by `CODE_REVIEW.md`,
both the same kind (a layer silently lost its ability to affect the outcome, and the flat result was
then read as a finding about the mechanism):** (1) **C1** — Method 3's regime margin was added to a
charge target clipped at battery capacity, and real daily net load exceeds capacity on 49.5% of
days, so the margin was mathematically zero on every high-demand day; measured, it fired ONLY on
days averaging 3.9 kWh net load and never on days averaging 25.7 kWh, an inverted stress response.
The original "third instance of regime-awareness not helping" claim was not supported by that
experiment and has been withdrawn and re-earned. (2) **C2** — "Method 2 wins" was reported with no
model-free control in the ladder; both ablations added since match or beat it.

**Three real bugs caught and fixed during the original build** (all still valid): (1)
`battery_sim.py`'s own first energy-balance self-test was itself wrong (didn't account for
round-trip losses correctly), replaced with an exact per-timestep check; (2) `dispatch_sim.py`'s
first draft let the same-hour reactive step immediately discharge what the proactive charging step
had just added, wasting round-trip losses twice — fixed by serving off-peak deficits directly from
grid instead of the battery; (3) `gp1d.py`'s exact GP was measured too slow at 3 training years
(20-36s per fit even single-threaded) — training set reduced to one real year, matching `shm_lab`'s
own established scale for this module. Central open question for Phase 2, informed by this result:
don't assume the regime layer earns its keep in the VoI decision layer either — check it the same
way, not by default expectation.

**Phase 2 — DONE (2026-08-04, `RESULTS_PHASE2.md`).** The fifth application of the sequential-VoI
mechanism this codebase has now built five times. State = a real, data-derived high-demand-day
label (net load top 25%). A new classifier stage (`stress_classifier.py`, a real `LaplaceBinaryGPC`
on yesterday's net load + temp) was required — checked first for separability (val AP≈0.80, real
variance range 0.014-0.66, neither too easy nor too hard). Economics needed **zero new sourcing** —
derived entirely from this lab's own already-verified BC Hydro rates and battery capacity, the
best-sourced economics of any VoI lab so far. **Headline: GPC's calibrated mean robustly beats SVM
(+$5.94-$338/seed depending on breakeven, 200 seeds), but posterior variance adds nothing on top,
across the ENTIRE cost-ratio range tested** (GPC-full vs. GPC-mean stays at ~$0 everywhere, niche
fraction exactly 0.0000 at the derived breakeven) — a clean null result, and the second, distinct
*mechanism* for that null this family has now found (`shm_lab`'s was too-easy-to-separate; here the
classifier has real, checked ambiguity, but the payoff structure never rewards resolving it). Two
independent layers of this lab (Phase 1's regime-mixture margin, Phase 2's VoI variance) now agree:
for this real dispatch problem, the extra modeling layers add nothing. **Updated 2026-08-05**: the
supporting argument from Phase 1 had to be rebuilt after `CODE_REVIEW.md` C1/C2 (see the Phase 1
entry above), and the conclusion came back stronger — the re-run found that not even the plain
forecast earns its keep, since a model-free calendar+reserve policy beats it. Phase 2's own null is
unaffected and was independently re-verified under a sigma_probe2 x c_probe sweep: even a noiseless
probe finds a niche on only 3.3% of days, and exactly 0.0000 at the published c_probe
(`CODE_REVIEW.md` 5.2).

**Phase 3 — DONE (2026-08-04), RE-RUN (2026-08-05, `RESULTS_PHASE3.md`).** A 2D (solar, battery)
grid search minimizing real annualized cost (rebate-adjusted capital + Method 2's real annual grid
cost), real 2017-2025 record. **Two real errors caught and corrected**: (1) while scoping, the
earlier-sourced solar/battery economics (`research/03...md`) were US market data including the US
federal tax credit — corrected with real BC Hydro rebates verified directly from bchydro.com
(`research/05...md`); (2) `CODE_REVIEW.md` H1 — **grid export was valued at $0 across the entire
lab**, now credited under BC Hydro's real Self-Generation Service Rate
(`research/08_bc_hydro_export_compensation.md`). **The export lookup is this lab's strongest
argument for verify-don't-recall: BC Hydro replaced the program on 2026-07-01**, five weeks before
the check — legacy net metering (RS 1289, annual kWh banking) closed to new customers, replaced by
RS 2289's flat 10¢/kWh monetary credit settled per billing cycle and capped at the month's energy
charge. Any recalled figure would have described the closed program.

**Headline: the cost-minimizing system is still 4kW solar + NO battery ($1,234/yr), but the margin
over 6kW collapsed from $107/yr to $12/yr** — the honest answer is now "4-6kW of solar, no battery",
since a $12/yr gap on a $1,234/yr total is inside the model's own resolution. Battery capacity still
never earns back its capital cost anywhere on the tested grid, a real property of BC Hydro's low
rates and modest battery rebate, not a modeling artifact — and crediting export slightly *widens*
that gap, since a battery's main job at large solar sizes is to avoid exporting, which is now worth
10¢ rather than nothing. **A genuinely new finding from the re-run**: the per-billing-cycle credit
CAP, not the credit rate, governs solar sizing — a Vancouver summer pairs maximum export with a
minimal energy charge, so surplus is forfeited rather than banked into winter ($0/yr forfeited at
4kW, $158 at 8kW, $1,117 at 20kW). Whether unused credit rolls forward is not stated by BC Hydro and
is now this phase's largest single uncertainty. The counter-intuitive **negative self-sufficiency
(−2.8%)** for 0kW solar + a battery is unaffected and still stands. Explicitly flagged as
$-optimization only — a battery's real backup-power/Peak-Saver-eligibility/EV-integration value
isn't priced by this model.

**Phase 4 (stretch) — EV charging as a second instance.** Only after Phases 0-3 land somewhere
conclusive: a second reservoir (vehicle battery/SOC) with a driving-demand process (trip distance/
schedule) instead of a household load, and a "will I have enough range" stress regime instead of
"will I have enough solar" — the point at which extracting a shared engine (per Fraser's own
question) would actually be justified by two real instances, not one.

## Files

- `data_weather.py` — **DONE.** Open-Meteo puller + local cache (mirrors `data_usgs.py`'s RDB-loader
  role); also exposes `load_range` for ad hoc real-bill-period pulls.
- `solar_model.py` — **DONE.** Shortwave radiation → PV generation; real seasonal shape verified.
- `load_model.py` — **DONE.** Base+heating load model, exactly calibrated to Fraser's real 2-point
  bill data; real backtest verified.
- `battery_sim.py` — **DONE.** Storage simulator (`reservoir_sim.py`-style); verified energy-
  conserving to floating-point precision after a real self-test bug was caught and fixed.
- `phase0_run.py` / `results_phase0.json` / `RESULTS_PHASE0.md` — **DONE.** Real stress-regime
  co-occurrence (1.78x) and persistence (4.5x) checks, both confirmed on real data.
- `rate_model.py` — **DONE.** Real BC Hydro tiered+optional-TOD cost calculator; self-test
  reproduces Fraser's real Mar 20-31 bill to the cent ($53.43 model vs. $53.44 real).
- `dispatch_sim.py` — **DONE.** Extends `battery_sim.py` with a daily overnight pre-charge target;
  a real same-hour double-discharge bug caught and fixed (see `RESULTS_PHASE1.md`).
- `daily_agg.py` — **DONE.** Shared daily solar/load/net-load aggregation + train/test year split.
- `naive_baselines.py` — **DONE.** Methods 0-1, plus the model-free ablations 0b (persistence) and
  1b (calendar-only) added 2026-08-05 per `CODE_REVIEW.md` C2.
- `gp_forecast_model.py` — **DONE.** Method 2 (reuses `shm_lab/gp1d.py` unchanged).
- `regime_mixture.py` — **DONE.** Method 3. Rewritten 2026-08-05 (`CODE_REVIEW.md` C1): the stress
  response now sizes a peak-window discharge reserve (`predict_reserves`) instead of the
  capacity-clipped charge target, where it was provably dead on every high-demand day. Charge
  targets are now identical to Method 2's by construction, making Method 3 a clean superset test;
  `constant_reserves` supplies the matching ablation.
- `dispatch_sim.py` — gained an optional `daily_reserve_kwh` floor (2026-08-05); `None` reproduces
  the previous behaviour exactly, verified by the existing parity self-test (0.00e+00 SOC diff).
- `phase1_run.py` / `results_phase1.json` / `RESULTS_PHASE1.md` — **RE-RUN 2026-08-05.** Eight-rung
  ladder (4 methods + 4 ablations); the model-free calendar+reserve policy wins at $613/yr.
- `stress_classifier.py` — **DONE.** New `LaplaceBinaryGPC`/`SVC` fit on yesterday's net load +
  temp against a real high-demand-day label; checked for separability first (val AP≈0.80).
- `run_dispatch_voi.py` / `bootstrap_dispatch_voi.py` / `cost_ratio_sweep_dispatch.py` — **DONE.**
  Same naming convention as the other four VoI labs; economics needed zero new sourcing.
- `results_phase2.json` files / `RESULTS_PHASE2.md` — **DONE.** Clean null result for posterior
  variance, real GPC-mean-vs-SVM advantage.
- `capacity_sizing.py` / `results_phase3.json` / `RESULTS_PHASE3.md` — **RE-RUN 2026-08-05.** 4-6kW
  solar / 0kWh battery wins on pure cost grounds ($1,234 vs $1,245/yr, effectively tied); two real
  economic errors caught and corrected (US-vs-BC tax credit while scoping; export valued at $0,
  `CODE_REVIEW.md` H1).
- `rate_model.py` / `scenario_engine.py` — gained the real RS 2289 export credit (2026-08-05):
  `total_cost_with_tod(grid_export_kwh=...)` and a `export_credit_per_kwh` key in `RATE_PRESETS`.
  Both exactly back-compatible when export is not passed (verified to 9e-13), so no earlier result
  shifted silently.
- `research/08_bc_hydro_export_compensation.md` — **DONE (2026-08-05).** BC Hydro's real export
  compensation, two live primary sources; records that the program changed on 2026-07-01.
- `scenario_engine.py` — **DONE.** Generalizes `capacity_sizing.py`'s hardware/rebate/rate constants
  into plain-dict catalogs (`SOLAR_OPTIONS`, `BATTERY_OPTIONS`, `RATE_PRESETS`), all overridable
  without touching engine code; adds `payback_years`/`cumulative_savings_curve` (real return-of-
  capital) and `optimize_grid` (cost- or self-sufficiency-objective search). Real Anker SOLIX and
  balcony-solar (DE/US) presets from `research/06...md`. Verified to reproduce Phase 3's own
  published numbers exactly before being trusted.
- `HOME_ENERGY_LAB.ipynb` — **REBUILT 2026-08-05**, 0 execution errors. Consolidated Phase 0-3
  notebook (real data, real charts, real findings), built via `build_lab_notebook.py`. Now carries
  the eight-rung Phase 1 ladder with its model-free ablations, the corrected Phase 3 economics, and
  a closing section on the shared failure mode `CODE_REVIEW.md` found (a layer silently losing its
  ability to affect the outcome, then its flat result being read as a finding about the mechanism).
- `SCENARIO_BUILDER.ipynb` — **REBUILT 2026-08-05**, 0 execution errors. Companion editable
  notebook, built via `build_scenario_builder_notebook.py`. Named-scenario comparison (baseline,
  Phase-3-optimal, the new 6kW runner-up, Powerwall-class reference, Anker SOLIX, balcony solar
  DE/US), a real payback-year chart + 20-year cumulative-savings curve, and two optimizers (cheapest
  system; cheapest system reaching a self-sufficiency target). Headline real findings **(updated for
  the RS 2289 export credit)**: balcony solar (DE, subsidized) pays back in ~1.2 years; the
  4kW/no-battery system now pays back in **14.1 years** (was 17.5 before export was credited) and
  the 6kW runner-up in 17.1; the 8kW+battery systems (Powerwall-class or Anker SOLIX) still do not
  pay back within 30 years at real BC Hydro rates. A real payback-calculation bug (comparing
  `total_annual`, which already nets out capital, instead of `grid_annual` only) was caught and
  fixed while building this notebook — see the notebook's own return-of-capital section.
- `research/` — **DONE**, nine passes (08: BC Hydro export compensation; 09: battery specs from
  Tesla's own datasheet — both added 2026-08-05).
- `CODE_REVIEW.md` — **DONE (2026-08-05).** Full review of the lab + the shared `gp_engine` modules
  it reuses. C1/C2/H1 fixed and re-run; H2/H3 and the M/L items remain open.

## Risks / honest unknowns (stated up front)

- **Single location's real weather record** — not a claim about every climate; a different location
  (e.g. one with a much weaker or stronger seasonal HVAC signal) could change the headline finding.
- **The load model is synthetic, anchored to aggregate EIA percentages, not one real household's
  actual behavior** (occupancy, appliance-specific timing) — ResStock flagged as a future real-data
  cross-check, not used as the primary driver by design.
- **The HVAC thermal model is a simplified degree-day/setpoint model**, not a full building-thermal
  RC-network simulation — a real simplification, the same spirit as `reservoir_sim.py`'s own
  lumped-single-reservoir choice.
- **A real TOU tariff and battery efficiency/degradation spec are not yet sourced** — Phase 0's job,
  not invented here.
- **Entirely illustrative economics** — not a real recommendation for any actual household's
  solar/battery purchase or HVAC control, per the disclaimer above.
