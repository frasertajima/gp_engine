# Research pass index — hydro_reserve_lab

Research pass DONE 2026-07-28. Six claims checked against primary/near-primary sources and, where
possible, direct empirical tests (not just descriptions) — same discipline as `climate_cat_lab/research/`,
`grid_reserve_lab/research/`, and `shm_lab/research/`. **One correction was deliberately made
BEFORE drafting a hypothesis this time** (claim 3) — learning directly from `grid_reserve_lab`'s
own history of having to walk back a strawman premise after the fact.

| # | Claim | Status | File |
|---|---|---|---|
| 1 | The regime genuinely recurs, in a specific chosen real basin | VERIFIED — Colorado River Basin selected: real, dated, escalating shortage-tier events (Tier 1 Aug 2021, Tier 2 Aug 2022) within a documented 23-year "megadrought," the worst in 1,200 years | `01_recurring_hydrological_regime.md` |
| 2 | The regime is rare/imbalanced, with a real sourced figure | VERIFIED, with a real number (5.5% historical extreme-drought likelihood) — **and a real, flagged nonstationarity complication**: nearly all basin watersheds hit extreme drought simultaneously by 2022 | `02_drought_regime_rarity.md` |
| 3 | What does real reservoir-planning practice actually do? | VERIFIED — the Bureau of Reclamation's CRSS model already uses historical/paleo-record ensemble scenario resampling (30-1,000+ traces), NOT a naive independence/flat-correlation strawman. **Hypothesis corrected in advance**: the real gap this lab should target is explicit regime representation vs. resampling resolution, not correlation-awareness itself | `03_real_reservoir_planning_practice.md` |
| 4 | Real dollar figures for the asymmetric-cost decision | VERIFIED — $20.6B/yr total basin value; conservation ~$417/AF (as low as $69.89/AF) vs. new-supply projects >$2,400/AF; municipal ($512/AF) vs. agricultural ($30/AF) price disparity; crop value $814/AF (Lower Basin) vs. $131/AF (Upper Basin). Fragmented by user class/sub-basin, not one blended VOLL-style number — a real, honest difference from `grid_reserve_lab`'s cleaner ERCOT figure | `04_colorado_river_economics.md` |
| 5 | A real reliability-standard convention, and the technical quantity to compute | VERIFIED — "Firm Yield" is the standard technical quantity; Seattle's real, sourced 98%/"1-in-50-year" reliability standard is a usable comparable (not yet confirmed as a Colorado-River-Basin-wide convention specifically); AWWA's M60 manual is the real professional-guidance analogue to NERC | `05_reliability_standard_firm_yield.md` |
| 6 | Real, open, multi-gauge data access | VERIFIED, empirically, twice — both the legacy `waterservices.usgs.gov` API (HTTP 200, no key, direct `curl` test) and its documented 2027 successor `api.waterdata.usgs.gov` (also HTTP 200, no key, direct `curl` test) | `06_usgs_data_access.md` |

## Net read — how this changes the lab's own framing before Phase 0 even starts

Unlike every prior lab in this family, `hydro_reserve_lab`'s hypothesis is written **already
corrected** rather than corrected after a first Phase 1 pass: real Colorado River planning practice
(CRSS) already uses historical/paleo-record scenario resampling, which is correlation-aware by
construction — so this lab is NOT testing "does correlation-aware modeling beat a naive
independence assumption" (already known to be a strawman here, per claim 3). It IS testing whether
an explicit, fitted regime-mixture model adds value over resampling-based practice specifically
where claim 2's nonstationarity complication bites — i.e. whether the drought regime's real,
recent frequency/severity has been shifting faster than a resampled historical/paleo record would
suggest, and whether a regime-mixture model can represent that shift (or a rare regime's tail more
sharply) better than an ensemble of historical scenario draws.

This is also the first lab in this family, per `PLAN.md` §7's litmus test, to be checked against
that specific two-condition + one-bonus-lever bar *before* any Phase 0 code — a genuinely different
discipline than `climate_cat_lab`/`grid_reserve_lab`/`shm_lab`, which each discovered their premise
needed correcting only after building something.
