# Claim 3: what does real reservoir-system planning practice actually do? (the load-bearing correction, learned in advance this time)

**Status: VERIFIED — and deliberately checked BEFORE drafting a hypothesis, specifically because
`grid_reserve_lab`'s own history shows what happens when this step is skipped**: its first-draft
premise assumed real ISO practice uses a naive independence assumption, and its research pass had
to walk that back after finding real ISO practice (MISO, E3's RECAP) already uses real historical
time-synchronous data to preserve correlation — the actual gap was *resolution* (zone/fleet-level
vs. spatially-resolved), not *assumption* (independence vs. correlation). This note applies that
lesson up front for `hydro_reserve_lab`, rather than discovering it after Phase 1.

## Real practice: the Colorado River Simulation System (CRSS)

The Bureau of Reclamation's own planning model for the Colorado River system, developed in the
1970s and running on the RiverWare platform since the 1990s, is the real tool used for long-term
(5-50 year) planning studies, criteria development, and risk analyses. Its hydrologic inputs are
built from:
- **The historical observed record** (naturalized streamflows),
- **Paleohydrology** (tree-ring-reconstructed streamflow, extending the effective record length
  well beyond the ~100-year gauged record — this is itself notable: real practice already reaches
  for a longer effective history specifically to better characterize rare/extreme events, the same
  motivation this lab has for wanting a longer effective sample of the drought regime), and
- **Climate-model-projected future hydrology.**

CRSS is run in an explicitly **probabilistic mode**: a large set (30-1,000+) of plausible inflow
**scenario traces** — built by resampling the historical/paleo record (preserving its real
statistics, sometimes with an added random component) — are propagated through the system to
generate an ensemble of outcomes.

## The corrected, honest hypothesis this sets up

**Real Colorado River planning practice is NOT a naive independence assumption or a flat/aggregate
correlation strawman** — it already uses historical (and paleo-extended) time-synchronous
scenario resampling, which by construction preserves whatever real cross-site/cross-time
correlation and regime structure occurred in the resampled record. This is structurally similar to
`grid_reserve_lab`'s corrected finding: **the real gap, if one exists, is likely one of
*explicit regime representation*, not of correlation awareness per se** — does resampling
historical scenarios (which mixes drought and non-drought years together in each draw, weighted by
how often they occurred historically) capture the same tail behavior as a model that explicitly
fits a latent regime-mixture and can, e.g., sample from "the drought regime specifically" or
represent a regime whose frequency is *shifting* (per `02_drought_regime_rarity.md`'s nonstationarity
finding) faster than the historical record reflects?

**This lab's hypothesis, stated honestly from the start** (not corrected after the fact this time):
a fitted regime-mixture model may add value over historical-scenario resampling specifically to the
extent that (a) the drought regime's frequency/severity is genuinely nonstationary within the
gauged record (resampling the full historical record understates a recent shift), or (b) an
explicit regime-conditional model generalizes better to plausible-but-unobserved severe scenarios
than resampling a finite historical/paleo record can. Both are real, checkable hypotheses — not
assumed true here, and Phase 1 should be built to test them directly rather than against a
strawman "real practice ignores correlation" premise.
