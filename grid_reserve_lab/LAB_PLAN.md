# grid_reserve_lab — how wrong is a flat-correlation reserve margin, in dollars

**Status: Research pass, Phase 0, Phase 1, and Phase 2 (+ a real follow-up bug fix) all DONE
(2026-07-27).** Phase 2 (`RESULTS_PHASE2.md`) is a real scoping pivot, made directly rather than
silently: instead of NREL per-turbine data at OOC scale, it uses EIA-930's real bulk-CSV endpoint
(confirmed reachable with no API key, unlike the Akamai-fronted main site) treating 15 real US
Balancing Authorities as "sites," with a genuine 2023-train/2024-test split (no synthetic oracle for
real data). **Follow-up (same day, per Fraser's two requested fixes — harmonic climatology instead
of a 30-day rolling mean, data-driven `p_hat_bounds` instead of copied from `climate_cat_lab`)
found the REAL bug behind Phase 2's first-pass anomaly**: `regime_mixture.py` was summing already
one-sided-CLIPPED per-site shortfall for its regime-detection feature, which creates a spurious
near-zero mass point at the fleet-total level (confirmed by an exact match between the minority
GMM component's weight and the fraction of near-zero-clipped-total days) — not a climatology or
bounds problem at all; both requested fixes were implemented correctly and, applied alone, made the
symptom *worse* (a 99.5%/0.5% split), which is what pinpointed the real mechanism. **The actual
fix**: feed the GMM the fleet-wide SIGNED, unclipped total deviation (summed across sites before
clipping, letting an over-performer offset an under-performer) instead. Result: a genuine ~50/50
split (`gmm_means` symmetric around zero, flat month-by-month responsibility — checked, not a
seasonal leak), and **Method 4 (soft-EM) now clearly beats Method 3 (vanilla GP) on real data
again** ($4.95B vs. $5.27B total annual cost, higher achieved reliability too) — matching Phase 1's
synthetic finding, reversing the earlier "statistical tie." The one thing that stays honestly open:
the real fitted regime is a persistent ~50/50 above/below-seasonal-trend split, not the synthetic
DGP's rare (~5-7%) severe-drought event — a genuinely different characterization of "regime" in
real data, not the same story transplanted. Also found in Phase 2: a real EIA-930 data-quality bug
(SWPP, 3.59M MW on one date) inflating a nameplate proxy 10x until fixed with a per-BA percentile
winsorization; and at only 15 real BA-level sites, this domain never reaches the ~40k OOC-solver
ceiling — a genuine, honest finding about this domain's real decision-making resolution (BA/zone
level, not per-turbine), not a shortfall of execution. Phase 1 (`RESULTS_PHASE1.md`):
the five-method ladder on a 730-day historical sample, scored against a 500,000-day oracle. True
required reserve: 5,059.8 MW. Methods 0 (ERCOT N-1: 571 MW, 2.9% achieved reliability) and 0 (generic
"5% wind": 728.5 MW, 34.5%) both badly under-reserve, as expected for rules designed for a different
risk (single-contingency, not correlated weather-driven shortfall — an honest caveat spelled out in
`RESULTS_PHASE1.md`, not a claim ERCOT is under-reserved in real life). **The central finding, exactly
mirroring `climate_cat_lab`'s own Phase 1 result**: Method 3 (vanilla spatial GP, 2,644 MW, 95.3%)
does NOT beat Method 2 (aggregate historical correlation, the real-ISO-practice baseline, 3,047 MW,
96.3%) — it does slightly worse. Only **Method 4 (GP + soft-EM regime-mixture, 5,925 MW) clears the
target reliability** (≥99.9998% vs. the 99.9726% target), at the cost of ~17% over-procurement
(~$104M/year) — a far cheaper mistake than every other method's multi-billion-dollar under-
procurement gap. The `reserve_baseline` Rust crate (methods 0-2) beat a vectorized NumPy reference by
**34.6x-46.2x** at 500,000 scenarios, confirming the traditional methods' dollar-gap loss isn't an
artifact of them being handicapped on speed. **Status prior to Phase 1**, kept for context:
Oracle DGP (`dgp_simulator.py`/`fleet.py`) confirmed on all 4 sanity checks: near-pair upper
tail-dependence coefficient λᵤ=0.607 at q=0.99 (61x the 0.010 independence baseline), vs. only
0.082 for a Gaussian model fit to the identical mean/covariance — a 7.4x gap, stronger than
`climate_cat_lab`'s own Phase 0 result (2.2x). One real methodology fix made along the way (see
`RESULTS_PHASE0.md`): shortfall had to be one-sided (`max(expected−actual, 0)`), not signed —
signed shortfall is ~zero-mean noise on normal days by construction, which let the fleet-wide
drought regime's jump swamp the spatially-decaying signal entirely (near/far pairs
indistinguishable). Six claims checked against
primary/near-primary sources before any Phase 0 code was written, same discipline as
`climate_cat_lab/research/` — full detail and verbatim quotes in `research/*.md`, indexed in
`research/RESEARCH.md`. Three claims held up close to as drafted; three forced a real correction,
folded into this document below rather than left in a superseded draft:
- The reliability target (0.1 days/yr LOLE) is real, but the citation was wrong (BAL-002 is the
  wrong standard — the real mechanism is the regional BAL-502 series, each NERC region converging
  on the same number independently, not one universal standard).
- The "3%+5%" deterministic reserve heuristic is real but is NOT ERCOT's — it's generic
  WECC/academic-study literature; ERCOT's own actual deterministic rules (fixed 2300 MW Responsive
  Reserve, N-1 largest-unit for Non-Spin, 2.5-sigma for Regulation) are used instead as the
  headline Method 0 baseline, being the more honestly-attributed of the two.
- **The load-bearing claim (Method 1/2's premise) needed the most correction.** Real ISO practice
  does not assume independence — MISO and E3's RECAP tool explicitly use real historical
  time-synchronous data specifically to preserve correlation. What's actually coarse is the
  *resolution*: one fleet/zone-level historical profile or ELCC number, not a spatially-resolved
  model capable of quantifying tail dependence beyond whatever happened to occur in the historical
  sample. The method ladder below is rewritten around this corrected premise.
- VOLL and reserve/capacity-cost figures are real but the original guesses were stale/invented —
  now replaced with current sourced numbers (ERCOT's actual $35,000/MWh VOLL, PJM/MISO's actual
  cleared capacity prices).

## One line

Grid operators size **operating reserves** — spare generating capacity held in reserve to cover the
gap between forecast and actual net load (demand minus wind/solar output) — against a reliability
target. North American resource-adequacy planning converges, region by region, on the same
**0.1 days/year loss-of-load-expectation (LOLE, "1 day in 10 years")** target — confirmed
independently by NERC's own 2019 Long-Term Reliability Assessment data across NPCC, MISO, PJM,
SERC, SPP and ERCOT (`research/01_nerc_lole_reserve_standard.md`), though the enforcement
mechanism is regional (the BAL-502 standard series), not one continent-wide rule. As wind and
solar penetration grows, the dominant source of net-load forecast error shifts from demand noise
toward **renewable output shortfall**, which is spatially correlated by construction — a regional
wind lull or persistent cloud deck depresses output at many sites at once. A real, DOE-national-lab-
documented instance of exactly this: ERCOT logged **82 wind-drought events from 2018-2022, the
worst a 15-hour, ~146 GWh regional deficit**; CAISO logged 167, worst case ~72 GWh
(`research/04_dunkelflaute.md` — the phenomenon is best known in European literature by the German
term "Dunkelflaute," but US DOE-lab studies document the identical mechanism as "wind/resource
drought"). The architecturally-similar failure mode `climate_cat_lab` found in catastrophe-capital
aggregation shows up here too, but in a more precise form than first drafted: real
resource-adequacy practice does **not** assume independence — it uses real historical
time-synchronous data specifically to preserve whatever correlation actually occurred
(`research/03_correlation_assumption_resource_adequacy.md`, correcting this plan's first draft).
What it does do is aggregate to a single fleet- or zone-level historical profile or ELCC number —
coarse in *resolution*, not naive by assumption — which structurally cannot represent tail
dependence beyond whatever happened to occur in the specific historical sample used to fit it. A
2025 Sandia National Labs paper (Gunda et al.) states this plainly: current assessments "have not
evaluated the impact of these co-occurrences on overall reliability of the planned power grid
systems." This lab builds a synthetic-but-realistic fleet-output world where the true joint
distribution is known, ports `climate_cat_lab`'s whole method (oracle DGP → method ladder →
dollar-gap scoring) to reserve-margin sizing instead of catastrophe capital, and — new to this lab
family — implements the traditional-method side in Rust so the comparison is fair on **both axes
that matter**: dollar accuracy of the reserve decision, and wall-clock cost of computing it.

## Why this lab, and why now

1. **It is the most direct port of `climate_cat_lab`'s finding to a second domain** — the
   generalization question `EXPLORATION_APPLICATIONS_ROADMAP.md` and `climate_cat_lab`'s own
   roadmap note raised without answering. Same object (fixed/flat linear-correlation aggregation of
   spatially-distributed loss/shortfall), same failure mode (zero tail dependence, understates a
   correlated systemic event), same fix shape (spatial GP + soft-EM regime-mixture over a fitted,
   not oracle-read, systemic-event probability). If the dollar-gap finding replicates on a second,
   unrelated domain with its own real public data, that is real evidence the pattern is structural
   and not an artifact of one synthetic DGP's design choices.
2. **`gp_cvar_soft`'s soft-EM regime-mixture is now live in `portfolio_studio`**, not just a lab
   result — reusing it a second time (climate_cat_lab → cvar_gp_lab → here) is exactly the kind of
   compounding return the engine-first strategy (`gp_engine`/MPDOK as reusable foundations,
   `CLAUDE.md`) is meant to produce. Nothing new needs proving about *whether* the soft-EM machinery
   works; this lab tests whether it's *valuable on a third dataset shape*.
3. **Real, live, public data exists for this one, unlike climate cat risk — now confirmed, not
   assumed.** EIA-930 (hourly demand/net-generation-by-fuel-type per Balancing Authority, 65 BAs,
   near-real-time, explicit public-domain statement) and NREL's WIND Toolkit (2km grid, 5-minute
   resolution, 126,000+ CONUS sites, 2007-2014, CC-BY 4.0) / NSRDB (2-4km, 5-30 min irradiance,
   1998-present, CC-BY 3.0) are both free, public, and — critically — **updated on an ongoing
   basis**, unlike claims data (`research/05_eia930_nrel_data.md`). A precedent paper found in this
   pass already built the exact use case Phase 2 needs — a synthetic wind-farm fleet with realistic
   distance-correlation structure, built from WIND Toolkit data. That is what makes this the
   strongest candidate of the three parked ideas (grid reserve / fleet structural-health / hydrology
   sizing, see `climate_cat_lab`'s entry in `PROJECTS.md`) for eventually becoming a **live monitored
   application** in the `portfolio_studio` mold (daily-refreshed reserve-requirement board), not just
   a one-shot dollar-gap report — see Phase 3.
4. **A legitimate place to push Rust further than `rbfx`'s current wrapper-only role.** Every prior
   Rust artifact in this codebase (`rbfx`, the `stash` family) either wraps an existing GPU solver
   or does fast local search — none of them are the *baseline being benchmarked against*. This lab's
   traditional-method side (independence/flat-correlation Monte Carlo aggregation over many
   scenarios and many sites) is an embarrassingly-parallel, allocation-light numerical loop with no
   GPU involved — exactly rayon's sweet spot, and a chance to have Rust do double duty: fast enough
   that "the traditional method is slow" can never be an excuse for its answer being wrong, which
   makes the accuracy comparison harder to wave away, not easier.

## Domain background (research pass DONE, 2026-07-27 — see `research/RESEARCH.md`)

- **Reliability target — PARTIALLY VERIFIED, citation corrected.** The 0.1 days/year LOLE target
  is real and independently confirmed across NPCC/MISO/PJM/SERC/SPP/ERCOT (NERC's own 2019
  Long-Term Reliability Assessment, Table 4, cited via a 2020 NYSRC report). It is enforced
  region-by-region via the **BAL-502 standard series** (e.g. BAL-502-RF-03, ReliabilityFirst-
  specific) — NOT via BAL-002, which is NERC's operating-timescale Disturbance Control Standard
  and unrelated to resource adequacy. NERC's own "Probabilistic Adequacy and Measures" report
  could not be fetched directly (403 on both known URLs) — cited here only second-hand via
  documents that quote it; flagged, not hidden. (`research/01_nerc_lole_reserve_standard.md`)
- **Deterministic reserve heuristic — PARTIALLY VERIFIED, re-attributed.** The "3% of load + 5%
  of wind capacity" rule is real (University of Washington dissertation, Papavasiliou/Oren/O'Neill
  2011 IEEE Trans. Power Systems, NREL's 2010 Western Wind and Solar Integration Study) but is
  **generic WECC/academic-study literature, not ERCOT's**. ERCOT's own actual documented rules
  (2004/2005 ancillary-service protocols) are different and more concrete: a **fixed 2300 MW
  Responsive Reserve requirement**, an **N-1 "largest single in-service unit" rule** for
  Non-Spinning Reserve, and a **2.5-sigma statistical rule** for Regulation. Method 0 below uses
  ERCOT's real rules as the headline deterministic baseline; the generic "3+5" rule is kept as a
  labeled alternative. (`research/02_deterministic_reserve_heuristic.md`)
- **The correlation-assumption premise — MIXED, and rewritten below, not just footnoted.** Real
  ISO practice (MISO's PY2025-26 LOLE Study, MISO's Wind/Solar Capacity Credit Report, E3's RECAP
  tool) explicitly builds fleet output from **real historical time-synchronous data specifically
  to preserve whatever correlation actually occurred** — independence is actively contradicted by
  the primary sources, not just unconfirmed, and this plan no longer claims it as real practice.
  What IS real: aggregation down to **one zone-level (e.g. MISO's Local Resource Zone) or
  fleet-wide historical profile / single ELCC percentage** — coarse in resolution, not naive by
  assumption, and structurally unable to represent tail dependence beyond the specific historical
  sample it was built from. Direct support for the "this understates correlated-shortfall risk"
  half of the hypothesis: Gunda et al., *Environ. Res.: Energy* 2, 025009 (2025, Sandia National
  Labs) — "many of the assessments to date have not evaluated the impact of these co-occurrences
  on overall reliability of the planned power grid systems" (their case study is hurricane-driven
  PV outages, not wind/solar drought specifically, but the structural critique is the same one
  this lab targets). (`research/03_correlation_assumption_resource_adequacy.md`)
- **"Dunkelflaute" / resource drought — VERIFIED, term adjusted for US scope.** Real, peer-reviewed
  term in European literature (Kittel & Schill 2024/2025, Biewald et al. 2025, a 2024 IEA Hydro
  Annex IX report co-authored by PNNL/Argonne/Oak Ridge) with real duration/frequency figures
  (multi-week VRE droughts/year in Germany/Spain, extreme tails up to 106 days). The German term
  itself hasn't been naturalized into US literature — DOE-lab studies covering ERCOT/CAISO/MISO/
  PJM/ISO-NE instead say **"wind drought"/"resource drought,"** with the ERCOT (82 events,
  2018-2022, worst 15hr/~146 GWh) and CAISO (167 events, worst 42hr/~72 GWh) figures cited above.
  This plan uses "resource drought" as its primary US-scoped term and keeps Dunkelflaute as a
  sourced cross-reference to the (larger, more quantified) European literature.
  (`research/04_dunkelflaute.md`)
- **EIA-930 and NREL WIND Toolkit/NSRDB — CONFIRMED**, both real, public, sufficiently granular,
  and reusable. See "Why this lab, and why now" point 3 above for the specifics.
  (`research/05_eia930_nrel_data.md`)
- **VOLL and reserve/capacity cost — CONFIRMED, figures corrected.** See "The decision, and its
  dollar consequence" below for the updated numbers. (`research/06_voll_and_reserve_cost.md`)

## Precedent already in this codebase

| grid_reserve_lab | reused from |
|---|---|
| Oracle DGP shape (regime + spatial shock) | `climate_cat_lab/dgp_simulator.py` — same two-layer construction: a latent regime (calm vs. correlated shortfall event) plus a spatial kernel governing which sites move together within an event. |
| Spatial kernel over site lat/lon + weather covariates | `gblup_lab/marker_kernel.py`'s GEMM-trick builder, already repointed twice (`cvar_gp_lab/asset_kernel.py`, `climate_cat_lab/spatial_kernel.py`) — third repointing, same move. |
| Soft-EM regime-mixture (systemic shortfall probability, fitted not oracle-read) | `climate_cat_lab/regime_mixture.py`'s fixed-partition-bug lesson and its fitted-frequency-sized-partition fix, and `cvar_gp_lab/regime_gp.py`'s port of the same idea to daily asset returns — this lab is the third domain for the identical mechanism. |
| CVaR/TVaR-style capital/requirement solver | `cvar_gp_lab/cvar_lp.py` (Rockafellar-Uryasev LP), already reformulated once for capital sizing in `climate_cat_lab/capital_calc.py` — reformulated again here for MW reserve requirement instead of dollar capital. |
| Decision framework (asymmetric-payoff action rule, sequential value-of-information) | `gp_engine/decision.py` / `gp_engine/voi.py`, the shared modules `bayesian_decision_lab` and `porphyry_cu_gpc_lab` both already reuse — candidate fit for a Phase 4 "how much should we pay for a better forecast" question (see Phases). |
| Dense GP solve at scale | `gp_core.py` (Phase 1, in-core) / `gp_ooc_fortran.py` (Phase 2+, past ~40k sites/site-hours) — no engine changes expected; same OOC ceiling `climate_cat_lab` exists to justify also justifies this lab once site-count × historical-hour count is large. |
| Rust FFI pattern for the GPU solver | `rbfx` — if this lab needs predictive **variance**, not just mean, from a Rust-side call (Phase 2's Rust orchestration layer), that is a real `rbfx` engine gap (its README says "mean-only predict (no variance yet)") worth fixing here rather than reverting to the ctypes path — flagged as an open decision, not committed to yet. |

## The core hypothesis, stated precisely (revised post-research-pass)

> A reserve-margin decision computed from a **single aggregate historical-correlation profile**
> (one fleet- or zone-level time series / ELCC number — the real, confirmed practice, per
> `research/03_correlation_assumption_resource_adequacy.md` — not an independence assumption,
> which is not real practice and is dropped from this hypothesis) will, on a synthetic fleet-output
> world with genuine spatially-correlated resource-drought regimes, achieve a materially worse
> *actual* reliability (LOLE-equivalent) than its stated 0.1-days/year target — and a GP fit to the
> same historical sample, feeding the same reserve-sizing calculation, will close a measurable
> fraction of that gap, worth a computable number of dollars (excess-reserve-procurement cost
> avoided, or expected-unserved-energy cost avoided) at a realistic fleet size.

Two ways this can come back false, reported either way (same discipline as `climate_cat_lab`):
- The aggregate-historical-correlation baseline might already be conservative by construction
  (the historical sample happened to include a severe drought event, or utilities pad reserve
  margins beyond their stated target as an informal hedge) — a real, reportable possible outcome
  (over-procurement, not under-), not assumed away.
- Vanilla spatial GP is still jointly Gaussian — same zero-tail-dependence property as a fitted
  flat/aggregate correlation, just better-shaped. If most of the true tail risk is the genuinely
  nonlinear "system enters a drought regime" event rather than misallocated-but-still-elliptical
  spatial correlation, method 3 (vanilla GP) may close only part of the gap, and method 4
  (regime-mixture) is where the rest is expected to come from — Phase 1 measures the split
  explicitly, exactly as `climate_cat_lab` did.
- **New risk surfaced by the research pass, not present in the first draft**: because real
  practice already uses real historical time-synchronous data (not independence), the honest
  "traditional baseline" may be less wrong than climate_cat_lab's flat-correlation strawman was —
  the gap this lab measures could be smaller by construction, since method 2 is no longer being
  compared against a strawman independence assumption but against ISO practice's actual
  (correlation-preserving-but-tail-blind) method. If the gap comes back small, that is itself the
  honest finding, not a failure of the lab.

## Method

**The oracle.** A synthetic fleet of `n` wind/solar sites at `(lat, lon)` with nameplate capacity
`C_i` and a smooth spatial mean-output surface (capacity-factor climatology). Hourly (or daily,
TBD by Phase 0 tractability) net-load forecast error is generated by a two-layer process:
1. A latent regime `R ~ Bernoulli(p_drought)` — "normal conditions" vs. "system-wide low-output
   event" (a blocking high-pressure system suppressing wind across the region, optionally
   correlated with low solar via persistent cloud cover). `p_drought` and the regime's output-
   multiplier are tunable, calibrated in Phase 0 to a plausible drought frequency/duration (a real
   knob, not a claim — same posture as `climate_cat_lab`'s `p_systemic`).
2. Conditional on the regime, each site's output deviates from its climatological mean via its own
   noise, but the regime shifts every site's output multiplier simultaneously, and a spatial kernel
   (distance-decaying, not flat) governs co-movement within an event. This produces genuine tail
   dependence: nearby sites' worst-case-hour output correlation should be measurably higher than
   their all-hours correlation — Phase 0's sanity check, structurally identical to
   `climate_cat_lab/RESULTS_PHASE0.md`'s tail-dependence check.

Every fitted method sees only a finite historical-style sample (illustrative: several years of
hourly/daily fleet output — real magnitude TBD in Phase 0) — never the oracle's true parameters.
The oracle is reserved for scoring: given a method's chosen reserve requirement, resimulate at
large `N` from the true DGP and read off achieved reliability and dollar cost.

**Five methods, a ladder** (one more rung than `climate_cat_lab`, since a genuine deterministic
heuristic — not just a statistical baseline — is real industry practice here, confirmed by the
research pass, and worth including as its own rung). **Methods 1-2 are rewritten from the first
draft** to match what real ISO practice actually does (`research/03_correlation_assumption_resource_adequacy.md`):
0. **Deterministic heuristic** — ERCOT's actual documented rules (fixed 2300 MW Responsive
   Reserve; N-1 "largest single in-service unit" for Non-Spin; 2.5-sigma statistical rule for
   Regulation) as the headline baseline, since these are the real, attributed rules found in this
   pass — the generic "3%+5%"-of-load/wind-capacity rule (real, but WECC/academic literature, not
   ERCOT's) kept as a labeled secondary variant. No correlation model at all in either case.
1. **Independence control (academic, not a real-practice claim)** — each site's forecast-error
   distribution fit marginally; fleet-level error = sum of independent marginals (CLT-thin tail).
   Kept only as a control condition (isolates "does correlation shape matter at all," the same
   discipline `bayesian_decision_lab` used for its variance-blind control) — explicitly labeled as
   NOT a claim that any real ISO does this, since the research pass found the opposite.
2. **Aggregate historical-correlation baseline (the real practice)** — one fleet- or zone-level
   historical time series / single ELCC-style percentage built from real historical
   time-synchronous data, the way MISO's LOLE Study and E3's RECAP tool actually do it: genuine
   historical correlation is baked in, but only whatever correlation happened to occur in the
   specific historical sample, at zone/fleet resolution, not a spatially-resolved model. This is
   the fair fight against the GP methods below — real practice, not a strawman.
3. **Vanilla spatial GP** — full posterior mean + covariance over site lat/lon + weather covariates,
   via `gp_core.py`/`gp_ooc_fortran.py`, scenarios sampled the way `cvar_gp_lab/scenario_gen_gp.py`
   already does. Tests whether a spatially-resolved (but still elliptical) correlation model closes
   the gap between method 2's real-but-coarse practice and the truth.
4. **GP + soft-EM regime-mixture** — layers method 3's spatial covariance inside a two-component
   mixture over a *fitted* resource-drought-regime probability (`regime_mixture.py`/`regime_gp.py`'s
   pattern, ported a third time), the same mechanism class as the true DGP.

**The decision, and its dollar consequence.** Each method (1-4; method 0 is a fixed rule with no
statistical fit) computes a reserve requirement (MW, or MW-hours if multi-hour drought duration
matters) to meet the 0.1-days/year reliability target from its own scenario-implied shortfall
distribution — `cvar_lp.py`'s Rockafellar-Uryasev machinery, reformulated as a reserve-sizing LP
(minimize reserve capacity subject to a CVaR-style shortfall-probability constraint, the mirror
image of `climate_cat_lab/capital_calc.py`). Score every method's decision against the oracle:
- **Achieved reliability** — resimulate at the chosen reserve level; does it actually deliver the
  target LOLE-equivalent, or is true unserved-energy probability materially higher?
- **Dollar gap, both directions, now with real sourced figures** (`research/06_voll_and_reserve_cost.md`):
  under-procurement cost = expected unserved energy in shortfall events × **Value of Lost Load —
  ERCOT's current PUCT-adopted figure is $35,000/MWh (system-wide average, adopted August 2024
  following a Brattle Group study)**, up from $9,000/MWh (2015-2021) and a $5,000/MWh interim
  figure (2022-2024) — customer-class figures range from ~$4,000/MWh (residential) to
  $667,000/MWh (small commercial/industrial). Phase 1's writeup uses $35,000/MWh as the headline
  but sweeps the historical $9,000-$35,000/MWh band as a sensitivity check, since this figure alone
  can swing the answer by 4x. Over-procurement cost = excess reserve capacity held beyond the true
  requirement × its annual capacity cost — **PJM's 2026/27 Base Residual Auction cleared
  $329.17/MW-day (≈$120,150/MW-year), a ~10x jump from $28.92/MW-day (2024/25), driven by
  data-center load growth; MISO's PY2025/26 Planning Resource Auction cleared ≈$217/MW-day
  (≈$79,200/MW-year)** vs ≈$21/MW-day (≈$7,665/MW-year) the prior year. ERCOT itself has no
  capacity market (energy-only, ORDC scarcity pricing instead) — no directly comparable ERCOT
  $/MW-year figure exists, so Phase 1 should use PJM/MISO's cleared prices for the
  over-procurement side even while using ERCOT's VOLL for the under-procurement side, and say so
  explicitly rather than blend markets silently.

## Rust component (new to this lab family — the point, not a decoration)

Two concrete pieces, sized to be genuinely useful rather than a token port:

1. **`reserve_baseline` — a Rust crate (rayon-parallel) implementing methods 0-2** (the
   deterministic heuristic, independence Monte Carlo, and flat-correlation Monte Carlo
   aggregation). This is a legitimate target for Rust on its own merits, independent of the "use
   Rust where we can" instruction: large scenario-count Monte Carlo aggregation over many sites is
   an allocation-light, embarrassingly-parallel numeric loop with no GPU dependency — exactly the
   shape `stash`-family Rust already targets, and a real apples-to-apples fairness move: benchmark
   the GP+soft-EM method against the *fastest reasonable implementation* of the traditional
   methods, not a slow reference Python port that would make the traditional method look bad on
   speed as well as accuracy for the wrong reason. Reports wall-clock **and** feeds the same
   dollar-gap scorer as the GP methods (a thin Python or PyO3 boundary calls into it, output shape
   matched to `capital_calc.py`'s convention).
2. **`rbfx` reuse for the GP side's dense solve**, with an explicit open decision flagged rather
   than resolved here: `rbfx`'s v1 API is mean-only (no predictive variance) per its own README,
   but this lab needs the full posterior (mean **and** covariance) to sample regime-mixture
   scenarios the way `cvar_gp_lab` does. Two options, to be decided in Phase 1 once the shape of
   the fit is known: (a) use `gp_core.py`/`gp_ooc_fortran.py` directly for the GP fit as every prior
   lab has, and reserve Rust for the baseline side only; (b) extend `rbfx-core` with a predictive-
   variance call (a real, reusable engine addition, the same kind of "found an engine gap, fixed
   it" moment `gblup_lab`'s `PrecomputedKernel` and `mining_gpc_lab`'s ARD extension were) so the
   GP side is Rust-callable too. Default to (a) for Phase 1 (lower risk, proven path); revisit (b)
   only if Phase 2's real-data scale-up would benefit from a lighter-weight Rust orchestration
   layer around the existing `.so`.

A stretch, lower priority than either of the above: a small Rust CLI (stash-family style) for fast
ingestion/parsing of EIA-930's hourly per-BA CSV exports and NREL Wind Toolkit/NSRDB site data for
Phase 2 — matches `stash`/`pdfstash`/`mdstash`'s existing pattern (fast local parse/index of a
specific public data shape) rather than inventing a new one.

## Phases

**Phase 0 — the oracle and the sanity check.** `dgp_simulator.py` (regime + spatial-shortfall
generator, ported from `climate_cat_lab`'s), `fleet.py` (synthetic site book: location, nameplate
capacity, climatological mean output). Verify genuine tail dependence exists and is sizeable
(worst-hour correlation vs. all-hour correlation among nearby sites) before anything is fit to it —
identical discipline to `climate_cat_lab/RESULTS_PHASE0.md`. Small fleet (`n` ~ 50-200 sites) for
fast iteration. Also: settle the domain-background verification pass flagged above, at least enough
to know which numbers (LOLE convention, VOLL range, $/MW-year reserve cost) are real vs. still
illustrative going into Phase 1's writeup.

**Phase 1 — the five-method ladder, small scale, both languages.** `reserve_baseline` (Rust: methods
0-2) + `spatial_kernel.py`/`gp_loss_model.py` (method 3, ported naming from `climate_cat_lab`) +
`regime_mixture.py` (method 4) + `reserve_calc.py` (the CVaR-style reserve-sizing LP, adapting
`cvar_lp.py`). Fit all five on one historical-style sample, score against the oracle: achieved-
reliability table, dollar-gap table (both directions), and the same split question
`climate_cat_lab` asked — does vanilla GP (method 3) already close most of the gap, or is the
regime-mixture layer (method 4) carrying the result. **New this lab**: a wall-clock table for
methods 0-2's Rust implementation vs. an equivalent naive Python/NumPy implementation, establishing
that the traditional methods' dollar-gap loss isn't an artifact of them being handicapped on speed.

**Phase 2 — scale to a realistic system size, real geography.** Same five-way comparison at a
fleet size calibrated to a real balancing authority's wind+solar portfolio (illustrative target:
a few hundred to a few thousand sites, i.e. a mid-size ISO's wind/solar interconnection queue —
needs sourcing, same posture as `climate_cat_lab` Phase 2's book-size caveats, not asserted yet).
Real geography and weather covariates from EIA-930 (per-BA hourly demand/net generation) and NREL
Wind Toolkit/NSRDB (site-resolved historical output), losses/shortfall dynamics still synthetic
where real system-wide reliability outcomes aren't public at the needed granularity (mirrors
`climate_cat_lab` Phase 3's "ground the geography, keep the loss process synthetic" move, pulled
forward a phase here since the geographic data is public and strong). Past the in-core ceiling for
a large fleet × long history, requiring `gp_ooc_fortran.py` — report whether the dollar gap grows,
shrinks, or holds with scale (open question, not assumed).

**Phase 3 (stretch) — the application pathway.** If Phase 2's dollar-gap result holds up, this is
the strongest candidate of the three parked ideas for becoming a genuinely live monitored
application rather than a one-shot lab report — daily-refreshed EIA-930 data (already a live feed,
unlike claims/sensor data) feeding a "today's fitted reserve requirement vs. the naive baseline's"
board, in the shape of `portfolio_studio`'s signal board / `daily_monitor.py`. Not committed to
here — a decision point once Phase 2's numbers are in, the same posture `bayesian_decision_lab`'s
Phase 3 redesign took before committing to sequential VoI.

**Phase 4 (stretch, lower priority) — value of a better forecast.** `decision.py`/`voi.py`'s
sequential value-of-information framework, reused a third time (after `bayesian_decision_lab`,
`porphyry_cu_gpc_lab`): how much would a grid operator pay for a better day-ahead wind/solar
forecast, framed as the same "pay to resolve uncertainty before committing capital" structure as
the mining labs' Probe action. Flagged as a real fit for the existing shared module, not yet
scoped in detail.

## Why isn't GP + soft-EM already industry practice? (researched, 2026-07-27)

A mid-session hypothesis proposed a specific "regulatory inertia" narrative for why the industry
hasn't adopted regime-aware Monte Carlo reserve sizing: long-term planning already uses sequential
Monte Carlo (SERVM/MARS/GE-MAPS), but real-time/day-ahead operations reverts to deterministic
heuristics because of a 5-15 minute solve-time constraint, market-transparency requirements, and
regulatory asymmetry favoring conservative, legally-defensible rules. Checked with the same rigor
as the original six-claim pass (`research/RESEARCH.md`'s second pass, claims 7-10) rather than
accepted at face value — directionally reasonable, but overstated in specific, checkable ways:

- **The tool list was wrong in one place.** SERVM and MARS are real, multi-adopter sequential
  Monte Carlo resource-adequacy tools (SPP/ERCOT/CPUC; NYISO/ISO-NE). **GE-MAPS is not** — it's a
  deterministic production-cost/dispatch model, a sibling product to MARS, not a third instance of
  the same methodology.
- **"Real-time reserve sizing is always deterministic" is false as stated.** ERCOT's Operating
  Reserve Demand Curve (ORDC) is a genuinely probabilistic (loss-of-load-probability-based)
  real-time mechanism feeding directly into scarcity prices — contradicting the simple dichotomy.
  It is not a live Monte Carlo simulation re-run every 5 minutes (it's a curve refreshed roughly
  24 times a year, with only curve-*evaluation* happening in real time) — so the more accurate
  framing is **"no ISO has built a live regime-mixture SCENARIO GENERATOR for real-time
  operations,"** not "real-time can't be probabilistic at all." That's a narrower, more precise, and
  more actionable gap than the original claim. The specific "15-minute" solve-window figure was not
  found anywhere and should be dropped; only "5-minute" (the SCED interval) is sourced.
- **The market-transparency concern is a real, litigated norm — but its application here is an
  inference, not an observed fact.** FERC requires market-clearing inputs to be transparent and
  auditable (Order No. 844; the MISO formula-rate-protocols case; PJM's own VRR reserve-requirement
  curve explicitly names "transparency" as a design criterion). But no ISO has ever proposed a
  regime-mixture reserve model, so there is no documented instance of anyone objecting to one on
  these grounds — the claim is a reasonable extension of real precedent, not a confirmed fact about
  how this specific approach would be received.
- **The cost-asymmetry/conservatism mechanism is well-documented; the narrower "legal
  defensibility" causal story is not.** Real regulatory-economics literature (NRRI/Brattle/Astrapé
  2011, E3-for-El-Paso-Electric 2015) explicitly argues utilities should hold reserves above the
  naive economic optimum because rare blackout costs are fat-tailed (one real example: an $8.3B
  tail scenario vs. a $240M average) — and one of those same reports names the actual reason the
  1-in-10 standard persists as **"customers rarely complain,"** i.e. inertia, not proven efficiency
  or legal necessity. The specific claim that deterministic heuristics are preferred *because
  they're more legally defensible as a "standard of care"* isn't directly sourced anywhere found —
  real prudence-review doctrine judges reasonableness given available information at the time, not
  old-vs-new methodology specifically.

**Net read**: the honest version of "why isn't this adopted" is closer to *inertia and an
unbuilt-scenario-generator gap* than a hard regulatory or computational barrier — ERCOT's ORDC
already proves real-time probabilistic reserve mechanisms are operationally viable; nobody has
built the regime-mixture version of one yet. That's a more optimistic, and more precisely-scoped,
conclusion than the original narrative offered.

## Notebook

`GRID_RESERVE_LAB.ipynb` (built by `build_notebook.py`, executed via `jupyter nbconvert
--execute`, 0 errors, 22 cells, 7 charts) — the math (LOLE target, oracle DGP, tail-dependence
coefficient, repeated-measures GP LML, soft-EM weighted LML, the Rust single-factor sampler),
Phase 0's oracle sanity check, Phase 1's and Phase 2's five-method scorecards, the Rust-vs-NumPy
benchmark, a direct soft-vs-hard-partition experiment (`hard_vs_soft_run.py` /
`results_hard_vs_soft.json`) answering "is soft-EM's advantage from not throwing away data?": **yes,
but the effect size is conditional on how imbalanced the regime split is** — a real, meaningful win
on the synthetic oracle's rare (~5%) regime (soft ~9% cheaper), and a statistical tie on real data's
roughly balanced (~50%) regime, where a hard partition isn't data-starved to begin with (confirms
`climate_cat_lab`'s original mechanism from a second, independent domain) — **and (2026-07-27) a
new section on the second research pass's "why isn't this already adopted" findings** (SERVM/MARS
confirmed as real tools, GE-MAPS was miscategorized as one, ERCOT's ORDC contradicts "real-time is
always deterministic," and the market-transparency/legal-defensibility concerns are real norms but
unconfirmed as applied to a regime-mixture model specifically, since none has ever been proposed).

## Files

- `dgp_simulator.py` — **DONE.** The oracle: regime + spatial-shortfall fleet-output generator.
- `fleet.py` — **DONE.** Synthetic site book builder (location, nameplate capacity, climatology).
- `phase0_run.py` / `results_phase0.json` / `RESULTS_PHASE0.md` — **DONE.** Four-check oracle
  sanity pass (regime mechanism, distance decay, headline tail dependence, Gaussian comparator).
- `reserve_baseline/` — **DONE.** Rust crate (rayon + serde_json, subprocess/JSON boundary),
  methods 0 (ERCOT N-1 + generic "5% wind" heuristic, closed-form) / 1 (independence control) / 2
  (aggregate-correlation, single-factor Monte Carlo). 34.6x-46.2x faster than a vectorized NumPy
  reference at 500,000 scenarios (`RESULTS_PHASE1.md`).
- `naive_baselines.py` — **DONE.** Python-side fitting for methods 1-2 (raw MW units, not log-ratio
  — shortfall is one-sided/zero-inflated, see `dgp_simulator.py`'s docstring) + the Rust/NumPy
  calling wrappers.
- `spatial_kernel.py` — **DONE.** Repoints `gblup_lab/marker_kernel.py` at site lat/lon (third
  repointing after `cvar_gp_lab/asset_kernel.py`, `climate_cat_lab/spatial_kernel.py`).
- `gp_shortfall_model.py` — **DONE.** Method 3, vanilla spatial GP over raw-MW shortfall residuals;
  reuses `climate_cat_lab/gp_loss_model.py`'s generic `mle_fit_spatial`/`mle_fit_spatial_weighted`
  (cross-lab import via `sys.path.append` — NOT `insert(0,...)`, which shadowed this lab's own
  `regime_mixture.py` with climate_cat_lab's same-named module the first time this ran; a real bug
  caught and fixed, see `RESULTS_PHASE1.md`-adjacent commit history).
- `regime_mixture.py` — **DONE.** Method 4, soft-EM (responsibility-weighted) drought-regime layer,
  third port of the mechanism `climate_cat_lab` validated and `cvar_gp_lab`/`portfolio_studio`'s
  `gp_cvar_soft` already run live — goes straight to the soft variant, not the hard-partition one
  climate_cat_lab tried first and found buggy.
- `reserve_calc.py` — **DONE.** CVaR-style reserve-requirement solver (closed-form VaR quantile,
  same shortcut as `climate_cat_lab/capital_calc.py`) + dollar-gap scoring using
  `research/06_voll_and_reserve_cost.md`'s sourced VOLL/capacity-cost figures.
- `phase1_run.py` — **DONE.** Fits all five methods, scores against the oracle, runs the Rust vs.
  NumPy benchmark. `results_phase1.json` / `RESULTS_PHASE1.md`.
- `data_eia930.py` — **DONE.** Real EIA-930 loader (15 real BAs as "sites"), handles a real
  cross-schema-version column drift (2023 vs. 2024 files) and a real single-value data-quality bug
  (SWPP's 3.59M MW hour) via per-BA percentile winsorization.
- `phase2_run.py` — **DONE.** Real 2023-train/2024-test scoring for all five methods.
  `results_phase2.json` / `RESULTS_PHASE2.md`. `data_nrel.py` / per-turbine OOC-scale resolution —
  not pursued, per `RESULTS_PHASE2.md`'s Finding 4 (this domain's real decision-making resolution
  doesn't reach OOC scale; would be an artificial scale-up, not a domain-motivated one).
- `research/` — **DONE.** Six sourced verification notes + `RESEARCH.md` index, same convention as
  `climate_cat_lab/research/`, folded into this document's Domain background section.

## Risks / honest unknowns (post-research-pass)

- **This plan's domain claims are now sourced** (`research/RESEARCH.md`, six claims, verbatim
  quotes and citations in `research/*.md`), same rigor as `climate_cat_lab/research/`. Three
  forced real corrections, already folded into the sections above (reliability-standard citation,
  ERCOT reserve-rule attribution, the independence-vs-aggregate-correlation premise, VOLL/reserve-
  cost figures) — this is not a claim that every number in this plan is now beyond dispute, only
  that it went through the same process climate_cat_lab's did before Phase 0 started.
- **The load-bearing premise is now weaker, and more honest, than the first draft's.** Real ISO
  practice already uses real historical correlation (not independence) — the gap this lab measures
  is "spatially-resolved tail-dependence model vs. aggregate zone/fleet-level historical
  correlation," a narrower and more defensible claim than "correlation-aware vs. correlation-blind."
  If Phase 1 finds the gap is small, that is the honest result of a fairer fight, not evidence the
  lab was pointless — report it plainly, the same way `bayesian_decision_lab`'s Phase 1 reported a
  hypothesis-contradicting finding without softening it.
- **Everything here is a controlled synthetic world, on purpose**, same posture as
  `climate_cat_lab`: a positive result demonstrates a mechanism (aggregate historical-correlation
  under-resolves reserves when the truth has regime-driven spatial shortfall, by a dollar amount
  that may scale with fleet size), not a measurement of any real ISO's actual reserve error.
- **Real resource-adequacy studies (MISO's LOLE Study, E3's RECAP, NERC's Probabilistic Adequacy
  work) are more sophisticated than this plan's first-draft strawman** — confirmed directly in
  this pass, not just conceded defensively. This lab's target is specifically the
  *resolution* gap (zone/fleet-level vs. spatially-resolved), not a claim the whole
  resource-adequacy pipeline ignores correlation.
- **Vanilla GP is still elliptical/Gaussian** — if Phase 1 shows method 3 barely beats method 2,
  that is the regime-mixture layer doing the real work, and the writeup must say so rather than
  crediting "the GP" broadly, exactly as flagged for `climate_cat_lab`.
- **VOLL and reserve-cost figures are now sourced but still need a sensitivity sweep, not a single
  point estimate** — $35,000/MWh is ERCOT's current adopted figure, but it moved 4x from
  $9,000/MWh in under a decade, and PJM's capacity price alone moved ~10x in two years
  (data-center load growth, not a grid-reliability signal) — Phase 1's writeup should treat both as
  live, moving inputs and report the dollar gap as a function of them.
- **PJM/MISO capacity prices and ERCOT's VOLL are not the same market design** — ERCOT has no
  capacity market at all (energy-only + ORDC), so the over-procurement-cost side necessarily
  borrows a different ISO's cleared price than the under-procurement side's VOLL. Stated explicitly
  above, not blended silently — a genuine limitation of comparing across market designs, not an
  error to paper over.
- **NERC's own "Probabilistic Adequacy and Measures" reports could not be fetched directly** (403
  on both known URLs) — the LOLE-convention citation rests on corroborating secondary sources
  (IEEE PES paper, NYSRC report quoting NERC's own 2019 data) rather than NERC's primary report
  text itself. Worth a second attempt (different access route) before this lab's own published
  writeup, not blocking for Phase 0.
- **The Rust/Python speed comparison is a secondary finding, not the lab's point** — it exists to
  make the accuracy comparison fair (the traditional method isn't handicapped by a slow reference
  implementation), and should not be allowed to overshadow the dollar-gap result in any summary.
