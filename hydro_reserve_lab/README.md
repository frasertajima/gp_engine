# hydro_reserve_lab — does a fitted drought regime-mixture add value over historical-scenario resampling?

> ## ⚠️ DISCLAIMER — READ BEFORE USING ANYTHING IN THIS LAB FOR ANY PURPOSE ⚠️
>
> **This lab is theoretical, educational, and exploratory only. Nothing here is validated or fit
> for use in any real reservoir-operations, water-supply, or policy decision.**
>
> - **No one may rely on this lab's findings, code, methodology, or output to make any decision or
>   take any action regarding a real reservoir, water utility, or river-basin management
>   question.** Not for capacity planning, allocation policy, drought-response triggers, public
>   communication, or anything else with real-world consequences.
> - **This is not a substitute for certified water-resource engineering or hydrologic practice.**
>   Any real reservoir-system decision must be made by qualified professionals using established,
>   validated methods (e.g. the Bureau of Reclamation's own CRSS model and its governing planning
>   processes), not this lab's simplified, illustrative single-lumped-reservoir model.
> - **This lab's own headline finding is a caution about over-trusting any statistical model,
>   including this one**: Phase 1 found that a real, fitted, correctly-implemented regime-mixture
>   still failed to anticipate the real 2000-2025 megadrought's severity from data available only
>   through 1999 — a concrete demonstration that models built on historical-record assumptions can
>   fail exactly when a changing environment renders those assumptions stale, a real
>   garbage-in-garbage-out risk when the "garbage" is simply a training window that ends before a
>   real acceleration begins. This is a reason for humility about this lab's own results, not a
>   claim that its methods are validated for real use.
> - All data used is public USGS gauge data and public domain research figures; nothing here
>   monitors, or should be construed as representing, any specific reservoir operator's actual
>   current planning position.
>
> This disclaimer applies to every file, result, and notebook in this lab, and must be preserved
> (not diluted or removed) in any derivative, summary, or presentation of this work.

**Status: Research pass DONE (2026-07-28, `research/RESEARCH.md`), Phase 0 DONE (2026-07-28,
`RESULTS_PHASE0.md`), Phase 1 DONE (2026-07-28, `RESULTS_PHASE1.md`), same rigor as
`climate_cat_lab/research/`, `grid_reserve_lab/research/`, `shm_lab/research/`.** **Phase 1's
finding is a genuinely humbling one, not a clean method-ranking story**: fit on 71 pre-2000 water
years and scored against the real, held-out 2000-2025 megadrought, **every method over-committed
demand relative to the true hindsight-optimal Firm Yield** — including Method 2, the time-varying
soft-EM regime-mixture this lab exists to test, whose fitted drought probability only rose from
2.8% to 12.1% across the real test years (far short of the real 42.3% rate Phase 0 measured),
because the pre-2000 training data itself never showed a clean "ramping toward drought" pattern to
extrapolate from. **The mandatory non-mixture trend control (Method 3) scored numerically best**
(92.3% real achieved reliability vs. 46.2% for the other three, $7.9B dollar consequence vs.
$34-41B) — **but its own fitted trend is NOT statistically significant on the pre-2000 data
(p=0.645, r²=0.003)**, so this is not evidence that a simple trend reliably beats a regime-mixture
— it is evidence that **detecting a real acceleration after it has happened is a fundamentally
different, easier problem than forecasting one from data that precedes it**, regardless of method
sophistication. See `RESULTS_PHASE1.md` for the full trace-down of why. Litmus-test pre-check
(`LITMUS_CHECK.md`) passed both required conditions of `gp_engine/PLAN.md` §7 before the research
pass began. **This lab's hypothesis is written already corrected, not corrected after a first
pass** — the research found real Colorado River planning practice (CRSS) is NOT a naive
independence/flat-correlation strawman, so this lab does not repeat `grid_reserve_lab`'s own path
of assuming one and having to walk it back. **Phase 0, on 97 real water years (1928-2025) across
five real USGS Colorado River Basin gauges, confirmed every mechanism the research pass flagged**:
strong real spatial correlation (mean pairwise log-flow correlation 0.764) for the pooling lever;
a real extreme-drought rate (6.2%) empirically matching the cited 5.5% literature figure almost
exactly; and — the single most important finding — **the drought regime's nonstationarity is
real, not just a documented worry**: the moderate-drought rate more than doubled from 19.7%
(pre-2000) to 42.3% (the real 2000-2025 megadrought period), arguing directly for a time-varying
regime probability in Phase 1's mixture design, not the fixed-rate pattern every prior lab in this
family used unchanged. See `RESULTS_PHASE0.md` for the full detail, including a real, honest
nuance found in Check 4 (the real 2021/2022 shortage-tier years reflect cumulative storage
deficit, not single-year inflow rank alone — WY2021 ranks more severe than WY2022 by raw inflow
despite Tier 2 being the more severe declared shortage).

## One line

Water utilities and river-basin operators size reservoir storage/withdrawal policy (**Firm
Yield**: the maximum sustainable withdrawal rate during a drought) against a reliability target —
a real, sourced comparable is Seattle's own **98% reliability / "1 shortfall per 50 years"**
standard (`research/05_reliability_standard_firm_yield.md`). The Colorado River Basin has been in a
**documented 23-year "megadrought," the worst in 1,200 years**, with two real, dated shortage-tier
escalations (Tier 1, August 2021; Tier 2, August 2022) on Lake Mead. Real basin-wide planning
(the Bureau of Reclamation's CRSS model) already handles this with an **ensemble of 30-1,000+
resampled historical/paleo-record streamflow scenarios** — genuinely correlation-aware, unlike the
strawman `grid_reserve_lab` first assumed for grid operators. This lab asks a narrower, honestly
corrected question: **does an explicit, fitted drought regime-mixture (soft-EM, the mechanism
already validated in `climate_cat_lab`/`cvar_gp_lab`/`grid_reserve_lab`/`shm_lab`) add value over
resampling-based practice — specifically where the regime's real frequency/severity may be
shifting faster than a resampled historical record reflects (`research/02_drought_regime_rarity.md`'s
nonstationarity finding), or in representing the tail of a rare regime more sharply than a finite
resampled ensemble can?**

## Why this lab, and why now

1. **Fifth port of the same soft-EM mechanism, but the first checked against a cross-lab litmus
   test before Phase 0**, not after. `gp_engine/PLAN.md` §7's two-condition checklist (regime must
   recur; regime must be rare/imbalanced) was itself forced into existence by `shm_lab`'s muted
   per-mode result and its own joint-model/pooling-control finding. This lab passed that check
   directly (`LITMUS_CHECK.md`) before any code was written — the discipline the checklist exists
   to enable.
2. **A real, large, well-documented economic stake** ($20.6B/yr total Colorado River Basin value;
   real, sourced, if fragmented, shortage/conservation-cost figures — `research/04_colorado_river_economics.md`),
   comparable in scale to `grid_reserve_lab`'s grid-reliability stakes.
3. **Real, open, empirically-verified data — twice**, not assumed. Both the legacy
   `waterservices.usgs.gov` API and its documented 2027 successor `api.waterdata.usgs.gov` were
   directly tested with live, unauthenticated `curl` requests and returned real data
   (`research/06_usgs_data_access.md`) — the same first-party-verification standard that caught
   BCSIMS's and KU Leuven's Z-24 access gates before either was trusted for `shm_lab`.
4. **A real, non-synthetic regime-shift event to score against**: the real 2000-2022 megadrought
   (and its two real, dated shortage-tier escalations) gives this lab a genuine train/test split on
   real data with a real regime shift — fit on pre-2000 historical flow data, score whether each
   method's Firm Yield/reliability decision would have held up through the real megadrought years
   it never saw. Mirrors `grid_reserve_lab`'s real 2023-train/2024-test split and `shm_lab`'s
   real-event detection framing at once, but — unlike `shm_lab`'s single one-time retrofit — with a
   genuinely **recurring/escalating** regime to test against, the condition `shm_lab` lacked.

## Domain background (research pass DONE, 2026-07-28 — see `research/RESEARCH.md`)

1. **The regime genuinely recurs — VERIFIED.** Multiple independent real drivers (ENSO, quantified
   at 12-48 month and 128-256 month oscillation cycles; PDO; a 2025 paper documenting increasing-
   frequency Western-US wet/dry "hydrological whiplash"), plus the Colorado River's own real, dated
   shortage-tier escalations (Tier 1 2021, Tier 2 2022) within its documented 1,200-year-worst
   megadrought. (`research/01_recurring_hydrological_regime.md`)
2. **The regime is rare/imbalanced — VERIFIED, with a real number and a real complication.** 5.5%
   historical extreme-drought likelihood (U.S. Drought Monitor) — comparable to `grid_reserve_lab`'s
   synthetic ~5-7% assumption. **Complication, not smoothed over**: by 2022 nearly the entire basin
   was in extreme drought simultaneously, consistent with a possibly-nonstationary (not fixed-rate)
   regime — a real Phase 0 check, not assumed either way. (`research/02_drought_regime_rarity.md`)
3. **Real planning practice (CRSS) already resamples historical/paleo scenarios — VERIFIED,
   correcting the hypothesis before Phase 0 rather than after.** Not a naive independence/flat-
   correlation strawman. This lab's real target is explicit regime representation vs. resampling
   resolution, not correlation-awareness itself. (`research/03_real_reservoir_planning_practice.md`)
4. **Real, sourced, if fragmented, dollar figures — VERIFIED.** $20.6B/yr total value; conservation
   ~$417/AF (as low as $69.89/AF) vs. new-supply projects >$2,400/AF; municipal ($512/AF) vs.
   agricultural ($30/AF) price disparity; crop value $814/AF (Lower Basin) vs. $131/AF (Upper
   Basin) — fragmented by user class/sub-basin, a real and honest difference from `grid_reserve_lab`'s
   cleaner single VOLL figure. (`research/04_colorado_river_economics.md`)
5. **A real reliability standard and technical quantity — VERIFIED.** "Firm Yield" is the standard
   quantity to compute; Seattle's real, sourced 98%/"1-in-50-year" standard is a usable comparable,
   not yet confirmed Colorado-River-Basin-specific. AWWA's M60 manual is the real professional-
   guidance analogue to NERC. (`research/05_reliability_standard_firm_yield.md`)
6. **Real, open, multi-gauge data access — VERIFIED, empirically, twice.** Both the legacy and
   successor USGS APIs directly tested with live `curl` requests, both HTTP 200, no key/login.
   (`research/06_usgs_data_access.md`)

## Precedent already in this codebase

| hydro_reserve_lab | reused from |
|---|---|
| Spatial kernel, repointed a fifth time — over gauge/sub-basin location within the Colorado River Basin | `gblup_lab/marker_kernel.py` → `cvar_gp_lab/asset_kernel.py` → `climate_cat_lab/spatial_kernel.py` → `grid_reserve_lab/spatial_kernel.py` → `shm_lab`'s mode-similarity variant |
| Soft-EM regime-mixture (drought regime, now checked for nonstationary frequency, not assumed stationary) | `climate_cat_lab/regime_mixture.py` → `cvar_gp_lab/regime_gp.py` → `grid_reserve_lab/regime_mixture.py` → `shm_lab/regime_mixture.py` — fifth port of the identical mechanism, and the first checked against `PLAN.md` §7's litmus test before Phase 0 |
| Historical-scenario-resampling baseline (Method 0, the REAL practice — analogous to `grid_reserve_lab`'s aggregate-correlation Method 2, not a strawman) | New — no direct prior-lab module, since no prior lab's "real practice" baseline was itself an ensemble-resampling scheme; closest precedent is `grid_reserve_lab`'s `naive_baselines.py`'s real-ISO-practice rung |
| CVaR/reliability-target solver, reformulated for Firm Yield instead of MW reserve or $ capital | `cvar_gp_lab/cvar_lp.py` → `climate_cat_lab/capital_calc.py` → `grid_reserve_lab/reserve_calc.py` — fourth reformulation of the same Rockafellar-Uryasev machinery |
| Fair-fight non-mixture pooling control (mandatory per `PLAN.md` §7, not optional) | `shm_lab/phase1c_run.py`'s pattern — a joint statistic across multiple correlated gauges/sub-basins, fit with NO regime-mixture, run alongside Method 2 from the start this time, not added only after an initial muted result |
| Rust component, if the resampling Monte Carlo is large enough to warrant it | `grid_reserve_lab/reserve_baseline`'s pattern (rayon-parallel scenario aggregation) — a real candidate, not yet committed to |

## The core hypothesis, stated precisely (corrected in advance — see domain background point 3)

> A historical/paleo-record ensemble-resampling baseline (CRSS's real practice — genuinely
> correlation-aware, not a naive independence strawman) will, when fit on pre-2000 streamflow data
> and evaluated against the real 2000-2022 megadrought it never saw, either (a) understate the true
> Firm Yield shortfall risk if the drought regime's real frequency/severity has shifted
> non-stationarily beyond what the pre-2000 record reflects, or (b) represent the rare drought
> regime's tail less sharply than a model that explicitly fits a regime-mixture and can
> conditionally sample "the drought regime specifically" rather than only whatever mix of regimes
> happened to occur in the resampled historical window. **A mandatory non-mixture pooling control**
> (summing/combining evidence across multiple correlated gauges without any regime-mixture, per
> `shm_lab`'s Phase 1c lesson) runs alongside the regime-mixture from the start, so any advantage
> found is attributed to the mixture mechanism specifically, not to pooling alone.

Ways this can come back false or muted, to be reported plainly either way, per this family's
standing discipline:
- The resampling ensemble may already capture the 2000-2022 regime adequately if the pre-2000
  record happens to include enough severe-drought years/paleo-extension to represent it — a real,
  reportable "practice was already adequate" outcome, not a failure of the lab.
- If claim 2's nonstationarity turns out to be the dominant effect, an explicit regime-mixture with
  a **fitted, time-varying** regime probability might be needed (not a fixed-rate mixture) — a real
  design decision to make in Phase 0/1, not assumed resolved by porting the existing
  `regime_mixture.py` unchanged.
- Per `PLAN.md` §7's mandatory control: if the non-mixture pooling baseline matches the
  regime-mixture's performance (as it did in `shm_lab`), that is the headline finding, not a
  footnote — reported with the same weight as an actual soft-EM win would be.

## Method (draft — will firm up once real USGS data for a chosen set of Colorado River Basin gauges/sub-basins is actually pulled in Phase 0)

Three-plus-one rung ladder:

0. **Historical/paleo-record ensemble resampling** — the real CRSS-style practice: resample
   historical (and, if a public paleo reconstruction dataset is found, paleo-extended) annual/
   seasonal streamflow sequences, propagate through a Firm Yield calculation, report the
   reliability actually achieved.
1. **Vanilla spatial GP** across multiple gauges/sub-basins — smooth but still elliptical, tests
   whether spatial resolution alone (without regime structure) closes any gap.
2. **GP + soft-EM regime-mixture** — a fitted (not oracle-read) drought-regime probability, the
   mechanism ported a fifth time; open design decision (Phase 0/1) on whether the regime
   probability should be fixed-rate or allowed to vary with time, per the nonstationarity finding.
3. **Mandatory non-mixture pooling control** — a joint statistic across the same gauges/sub-basins
   with NO regime-mixture (`shm_lab`'s Phase 1c pattern), run from the start, not added
   after the fact.

**Scoring, against the real 2000-2022 megadrought (fit on pre-2000 data only):**
- Achieved reliability vs. the Firm Yield target each method implies.
- Detection/representation of the real 2021/2022 shortage-tier escalations specifically.
- Dollar consequence using `research/04_colorado_river_economics.md`'s real, fragmented
  (per-user-class) cost figures — not a single invented blended VOLL analogue.

## Phases

**Phase 0 — DONE (2026-07-28, `RESULTS_PHASE0.md`).** Five real USGS gauges pulled (Lees Ferry AZ,
Green River UT, Colorado River near Cisco UT, Gunnison River CO, San Juan River UT — Upper Basin,
for genuine spatial structure and to avoid the Lower Basin's dam-regulated mainstem flows), 97
complete water years (1928-2025) via the verified-open API. All flagged mechanisms confirmed
directly: strong spatial correlation (0.764 mean), a real extreme-drought rate matching the cited
literature figure (6.2% vs. 5.5%), and — the key finding — **real, measured nonstationarity**
(moderate-drought rate 19.7% pre-2000 → 42.3% in the real 2000-2025 megadrought), now a firm design
input for Phase 1's regime-mixture rather than an open question.

**Phase 1 — DONE (2026-07-28, `RESULTS_PHASE1.md`).** All four methods fit on pre-2000 data (71
years), scored against the real 2000-2025 held-out megadrought (26 years) via a lumped-reservoir
Firm Yield simulation. Method 2 used a time-varying regime probability, per Phase 0's finding —
but even so, **every method over-committed demand relative to the real hindsight-optimal Firm
Yield**, and Method 2's fitted drought probability (2.8%→12.1% across the test years) badly
undershot the real 42.3% rate, because the pre-2000 training data itself never showed a clean
ramping pattern to extrapolate from. The mandatory non-mixture trend control (Method 3) scored
numerically best but its trend is not statistically significant on the training data (p=0.645) —
the honest conclusion is about the limits of extrapolating through a genuine acceleration, not a
clean method win. See `RESULTS_PHASE1.md`'s full trace-down, including a new addition to
`gp_engine/PLAN.md` §7's litmus test this finding prompted.

**Phase 2 (stretch) — paleo-record extension, if a public paleo streamflow reconstruction dataset
is found** — real practice (CRSS) uses paleohydrology specifically to extend effective sample size
for rare-event characterization; worth checking whether a public tree-ring-based reconstruction
exists and is usable the same way, before assuming Phase 1's gauged-record-only scope is
sufficient.

## Files

- `data/usgs_<site>_dv.rdb` — **DONE.** Raw USGS daily-discharge pulls (RDB format), five gauges,
  not committed to version control (re-downloadable from the verified-open API).
- `data_usgs.py` — **DONE.** Loader: parses RDB, aggregates to water-year (Oct-Sep) mean discharge,
  restricts to years with all five gauges complete (97 water years, 1928-2025).
- `research/` — **DONE.** Six sourced verification notes + `RESEARCH.md` index, same convention as
  `climate_cat_lab/research/`/`grid_reserve_lab/research/`/`shm_lab/research/`.
- `phase0_run.py` / `results_phase0.json` / `RESULTS_PHASE0.md` — **DONE.** Four real-data checks:
  spatial correlation, empirical drought-rate match to cited literature, the confirmed
  nonstationarity finding, and the real 2021/2022 shortage-tier-years check.

- `reservoir_sim.py` — **DONE.** Lumped single-reservoir storage simulation + Firm Yield bisection
  solver (cfs-to-acre-foot conversion, storage/shortfall accounting).
- `method0_resampling.py` — **DONE.** The real CRSS-style practice: i.i.d. resampling of pre-2000
  annual Lees Ferry flows (a documented simplification vs. full block-bootstrap/paleo-extended
  CRSS).
- `hydro_gaussian.py` — **DONE.** Shared multivariate-Gaussian fitting utilities (plain MVN, a
  linear-trend MVN, and a time-varying-mixing-weight soft-EM mixture) — the "spatial kernel"
  simplification for this lab's fixed, named (not spatially continuous) gauge set is documented in
  this file's own module docstring.
- `method1_vanilla_mvn.py` — **DONE.** Method 1: stationary joint-Gaussian, no trend.
- `method2_regime_mixture.py` — **DONE.** Method 2: soft-EM regime-mixture with a time-varying
  (logistic-trend) mixing weight — the direct response to Phase 0's nonstationarity finding.
- `method3_trend_control.py` — **DONE.** Method 3: the mandatory non-mixture control — a linear
  time trend on the mean, no latent classes at all.
- `phase1_run.py` / `results_phase1.json` / `RESULTS_PHASE1.md` — **DONE.** The four-method
  ladder, real-2000-2025-megadrought scoring, and the honest trend-significance check that
  reframes the whole result.

## Notebook

`HYDRO_RESERVE_LAB.ipynb` (built by `build_notebook.py`, executed via `jupyter nbconvert
--execute`, 0 errors, 13 cells, 4 charts) — the disclaimer restated at the top, the full math
(Firm Yield, historical resampling, the vanilla and time-varying regime-mixture MVN fits, the
mandatory trend control), Phase 0's real-data charts (the 97-year Lees Ferry flow series with the
real megadrought shaded, the spatial-correlation heatmap, the nonstationarity bar chart), and
Phase 1's key chart — what each method actually forecast for the real megadrought years vs. what
happened — plus the honest significance check that reframes the apparent "winner." Single
reference point for this lab, per Fraser's request to consolidate. Lab considered feature-complete
at this stage.

## Risks / honest unknowns (stated up front, before any code is written)

- **The regime's possible nonstationarity (claim 2) is the single most important open question**
  — if real, it changes what "the mechanism" needs to represent (a shifting rate, not a fixed one)
  and should be checked directly in Phase 0, not assumed away in either direction.
- **The economic figures are real but fragmented** (per user class, per sub-basin) rather than one
  clean VOLL-style number — the economic layer needs to reflect that fragmentation honestly, not
  force an artificial single figure for the sake of a tidy chart.
- **Seattle's reliability standard is illustrative, not yet confirmed as this specific basin's own
  convention** — worth a direct check (e.g. does the Bureau of Reclamation or any Colorado River
  Basin state publish its own explicit reliability target) before treating 98%/1-in-50-years as
  this lab's own headline number.
- **The mandatory non-mixture pooling control is not optional** — per `PLAN.md` §7, any apparent
  soft-EM advantage must be checked against it before being reported as a soft-EM finding, learned
  directly from `shm_lab`'s own Phase 1b/1c result.
- **This is one basin, one real historical megadrought** — same standing caveat as every real-event-
  scored lab in this family: a positive or negative finding here characterizes this basin and this
  real event, not a general claim about river-basin planning everywhere.
