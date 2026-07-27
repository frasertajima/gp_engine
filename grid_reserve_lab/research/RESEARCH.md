# grid_reserve_lab — research index

Six claims checked before Phase 0, same discipline as `climate_cat_lab/research/RESEARCH.md`:
primary/near-primary sources, verbatim quotes, explicit verdicts. Three came back clean, three
forced a real correction to the plan — corrections are folded into `LAB_PLAN.md` directly, not
left only here.

| # | Claim | Verdict | File |
|---|---|---|---|
| 1 | NERC's "1-day-in-10-years" LOLE (0.1 days/yr) is the North American resource-adequacy reliability convention | **PARTIALLY VERIFIED** — the target is real and independently converged on by NPCC/MISO/PJM/SERC/SPP/ERCOT, but the mechanism is regional (BAL-502 series), not one universal NERC standard; original BAL-002 citation was wrong (that's the operating-timescale disturbance-control standard) | `01_nerc_lole_reserve_standard.md` |
| 2 | A simple deterministic reserve-margin heuristic ("3% of load + 5% of wind capacity") is documented, ERCOT-attributed, historical practice | **PARTIALLY VERIFIED** — the "3+5 rule" is real (academic/WECC-study literature), but NOT ERCOT's; ERCOT's own real deterministic rules are a fixed 2300 MW Responsive Reserve requirement, an N-1 "largest single in-service unit" rule for Non-Spin, and a 2.5-sigma statistical rule for Regulation | `02_deterministic_reserve_heuristic.md` |
| 3 | Real resource-adequacy studies aggregate wind/solar site variability under an independence or flat-correlation assumption, understating tail risk | **MIXED — the load-bearing claim, and it needed rephrasing.** Independence is actively contradicted (MISO/E3 use real historical time-synchronous data specifically to preserve correlation); what's real is coarser — one zone/fleet-level historical profile or ELCC number, not a spatially-resolved tail-dependence model. A 2025 Sandia paper directly states current assessments haven't evaluated co-occurrence impact on reliability | `03_correlation_assumption_resource_adequacy.md` |
| 4 | "Dunkelflaute" (correlated multi-day wind+solar shortfall) is a real, studied, quantified phenomenon relevant to reliability | **VERIFIED** — real term in peer-reviewed European literature with real duration/frequency figures; US literature uses "wind/resource drought" instead, with real ERCOT (82 events 2018-2022, worst 146 GWh deficit) and CAISO (167 events, worst 72 GWh deficit) numbers from DOE-lab studies | `04_dunkelflaute.md` |
| 5 | EIA-930 and NREL WIND Toolkit/NSRDB are real, public, sufficiently granular datasets for Phase 2 | **CONFIRMED**, both — EIA-930 has an explicit public-domain statement; NREL data confirmed via AWS/OpenEI mirrors (nrel.gov itself DNS-unreachable in this pass) and a precedent paper that already built the exact "synthetic correlated wind fleet" use case this lab needs | `05_eia930_nrel_data.md` |
| 6 | VOLL (~$9,000-$30,000/MWh) and reserve/capacity cost figures are real and findable | **CONFIRMED, with the VOLL figure corrected upward.** ERCOT VOLL: $9,000/MWh (2015-2021) → $5,000 (2022-2024 interim) → **$35,000/MWh** (adopted Aug 2024, Brattle Group study for PUCT). Capacity/reserve cost: PJM 2026/27 cleared $329.17/MW-day (≈$120,150/MW-yr), ~10x the $28.92/MW-day of 2024/25; MISO PY2025/26 ≈$217/MW-day (≈$79,200/MW-yr) vs ≈$21/MW-day (≈$7,665/MW-yr) the year prior | `06_voll_and_reserve_cost.md` |

## Second research pass (2026-07-27): why isn't GP + soft-EM already adopted?

Four more claims checked, this time verifying a specific "here's why the industry doesn't already
do this" narrative offered mid-session — same rigor, same posture of correcting overstatements
rather than accepting a plausible-sounding argument at face value.

| # | Claim | Verdict | File |
|---|---|---|---|
| 7 | SERVM, MARS, and GE-MAPS are all standard sequential-Monte-Carlo resource-adequacy tools across ISOs | **PARTIALLY VERIFIED** — SERVM (SPP/ERCOT/CPUC) and MARS (NYISO/ISO-NE, called "the industry standard" in one primary source) both confirmed as real multi-adopter sequential Monte Carlo tools; GE-MAPS does NOT belong in this group — it's GE's deterministic production-cost/dispatch model, not a Monte Carlo resource-adequacy tool at all | `07_monte_carlo_tools_servm_mars_geMaps.md` |
| 8 | Long-term planning uses Monte Carlo; real-time/day-ahead reserve sizing uses deterministic heuristics instead, because of a 5-15 minute solve-time constraint | **MIXED** — holds for PJM/MISO (documented deterministic N-1 rules) but is **contradicted** by ERCOT's ORDC, a genuinely probabilistic (LOLP-based) real-time mechanism — not a live Monte Carlo run inside the 5-minute window (it's a curve refreshed ~24x/year), but not the claim's simple "real-time = deterministic" dichotomy either. The 5-minute SCED interval is well-sourced; "15 minutes" was not found anywhere and should be dropped | `08_realtime_vs_planning_reserve_methods.md` |
| 9 | Market participants would oppose a latent-mixture-model reserve requirement as insufficiently transparent | **CONFIRMED (general principle) / UNCONFIRMED (specific application)** — FERC's transparency norm for market-clearing inputs is real and litigated (Order No. 844; 143 FERC ¶ 61,149; PJM's VRR curve explicitly lists "transparency" as a stakeholder design criterion), but no ISO has ever proposed a regime-mixture reserve model, so no documented objection to one exists — the specific claim is a reasonable inference from precedent, not an observed fact | `09_market_transparency_reserve_requirements.md` |
| 10 | Utilities prefer deterministic heuristics because they're legally safer ("standard of care") even when a statistical model is proven more efficient | **MIXED** — the cost-asymmetry-driven conservatism itself is well-documented (NRRI/Brattle/Astrapé 2011, E3-for-El-Paso-Electric 2015, a real $8.3B-tail-vs-$240M-average example; one report names "customers rarely complain" as why the 1-in-10 standard persists — inertia, not proven efficiency) — but the narrower "legally safer as standard of care" causal mechanism isn't directly sourced anywhere; real prudence-review doctrine judges reasonableness given available information, not old-vs-new methodology specifically | `10_regulatory_asymmetry_conservatism.md` |

**What this changes**: the mid-session narrative was directionally reasonable but overstated in
specific, checkable places — exactly the pattern this lab's whole research discipline exists to
catch. GE-MAPS doesn't belong in the tool list. ERCOT's ORDC is real evidence that "real-time reserve
sizing is always deterministic" is false as stated — real-time CAN be probabilistic, just not via a
live Monte Carlo re-run; the actual barrier is closer to "no ISO has built a live regime-mixture
scenario generator," which is a narrower, more accurate claim. The market-transparency and
legal-defensibility arguments are plausible extensions of real, documented norms/doctrine — not
independently confirmed claims about how a regime-mixture model specifically would be received,
since none has ever been tried.

## What this changes in the plan

- **Reliability target**: cite the regional BAL-502 convergence pattern, not a single universal
  NERC standard — still use 0.1 days/yr as the illustrative target, now correctly sourced.
- **Method 0 (deterministic heuristic)**: two real options now, not one guessed number — the
  generic "3+5" WECC/academic rule, or ERCOT's actual documented rules (fixed 2300 MW / N-1
  largest-unit / 2.5-sigma). Plan uses ERCOT's real rules as the headline deterministic baseline
  (more defensible, actually attributed) and keeps "3+5" as a labeled generic alternative.
- **Methods 1-2 (the load-bearing rungs) — rewritten.** Drop "independence" as a claimed real
  industry practice; keep it only as an academic control condition (isolates whether "any
  correlation beats none," same discipline `bayesian_decision_lab` used for its mean-only
  control). Reframe the real-practice baseline as "aggregate historical-correlation" — one
  fleet/zone-level historical time series or ELCC number — not a "flat correlation coefficient."
- **Dunkelflaute → "resource drought"** as the primary term for US-scoped claims and quantitative
  figures, Dunkelflaute kept as the (real, sourced) motivating cross-reference to the European
  literature.
- **VOLL**: use $35,000/MWh (current ERCOT-adopted figure) as the headline, $9,000-$30,000/MWh
  labeled explicitly as the superseded 2015-2021 band, not the current number.
- **Reserve/capacity cost**: use PJM's and MISO's real, current cleared-price figures instead of
  an invented number; note ERCOT has no capacity market (energy-only + ORDC) so no directly
  comparable ERCOT figure exists — flagged, not papered over.
