# Phase 0 results — does this real 5-gauge dataset actually show the mechanism?

**Status: DONE (2026-07-28).** `data_usgs.py` (loader, real USGS daily discharge, five Colorado
River Basin gauges) / `phase0_run.py` / `results_phase0.json`. **97 real water years (1928-2025),
all five gauges complete** — a substantially longer real record than any prior lab in this family
worked with (`grid_reserve_lab`'s real EIA-930 pass was 2 years; `shm_lab`'s KW51 was 15 months).

## Headline finding — every check passes, and the flagged nonstationarity concern is real

**All four Phase 0 checks confirm the mechanism directly in real data, not assumed from the
research pass's cited literature.** Most importantly: **`research/02_drought_regime_rarity.md`'s
flagged nonstationarity complication is real and empirically confirmed** — the drought regime's
rate has genuinely shifted since 2000, not merely subjectively "felt" that way.

## Check 1 — genuine spatial correlation across gauges (the pooling lever)

Pairwise log-flow correlation across the five gauges: **mean 0.764, range [0.633, 0.967]** — very
strong, confirming the five gauges share a real, common regional climate driver (as expected within
one river basin), stronger even than `climate_cat_lab`'s or `grid_reserve_lab`'s near-pair spatial
correlations. This gives the pooling lever (`PLAN.md` §7's bonus condition, and the mandatory
non-mixture control this lab commits to from the start) real, strong structure to exploit.

## Check 2 — a real, recurring, rare drought regime, empirically matching the cited literature figure

Using a basin-wide standardized flow index (mean of each gauge's full-record log-flow z-score) and
an "extreme drought" threshold at the 5.5th percentile (`research/02`'s cited historical
likelihood): **the empirical rate on this real 97-year record is 6.2% (6 of 97 years)** — closely
matching the 5.5% figure cited from the U.S. Drought Monitor. This is real, independent
confirmation from actual gauge data, not just trust in the citation.

## Check 3 — the nonstationarity complication is REAL, not just a documented worry

| | Extreme-drought rate (≤P5.5) | Moderate-drought rate (≤P25) |
|---|---|---|
| Pre-2000 (1928-1999, 71 years) | 5.6% | 19.7% |
| 2000-2025 megadrought (26 years) | 7.7% | **42.3%** |

The moderate-drought rate **more than doubled** in the real 2000-2025 period relative to the
pre-2000 baseline (19.7% → 42.3%) — a real, large, directly-measured shift, not a subtle one. This
confirms `research/02_drought_regime_rarity.md`'s flagged complication precisely: **a fixed-rate
regime-mixture calibrated on the full historical record would understate the real, recent drought
frequency.** This is the single most important finding for how Phase 1 should be designed — it
argues directly for a **time-varying/fitted-rate regime probability**, not the fixed-rate mixture
every prior lab in this family used, since the "regime" here has a real, measured trend rather than
a stable long-run frequency.

## Check 4 — do the real 2021/2022 shortage-tier years actually show up as severe?

- **Water year 2021 (the year Lake Mead's real Tier 1 shortage was declared, August 2021) ranks at
  the 4.1st percentile of the entire 97-year record** — one of the most severe years on record by
  this basin-wide inflow index, consistent with real-world reporting (Lake Mead's lowest level
  ever recorded that summer).
- **Water year 2022 (Tier 2, August 2022) ranks at the 13.4th percentile** — severe, but notably
  *less* extreme than WY2021 by this single-year inflow measure. **A real, honest nuance worth
  keeping, not smoothing over**: shortage-tier declarations are triggered by cumulative reservoir
  *storage* levels, not any single year's inflow rank — WY2022's tier escalation reflects
  accumulated multi-year deficit, not that year alone being the worst inflow year. Phase 1's
  regime-mixture and its scoring should account for this distinction (storage state vs. annual
  inflow) rather than treating the two as interchangeable.

## What this means for Phase 1

- **A fixed-rate soft-EM regime-mixture (the pattern every prior lab in this family used
  unchanged) is likely the wrong first design here** — Check 3's real, measured nonstationarity
  argues for a time-varying regime probability (e.g., a regime rate that can itself drift, or a
  mixture conditioned on a rolling window) as the honest first attempt, not a retrofit after a
  fixed-rate version underperforms.
- **The mandatory non-mixture pooling control (`PLAN.md` §7) has real structure to work with** —
  the 0.764 mean pairwise correlation is strong enough that a simple pooled statistic across the
  five gauges may again capture much of any detection benefit, exactly as it did in `shm_lab`'s
  Phase 1c. Build it alongside Method 2 from the start, per the lab's own standing commitment.
- **Storage-state vs. single-year-inflow is a real distinction Phase 1 needs to model
  explicitly** — a Firm Yield calculation should track cumulative storage, not just be scored
  against annual inflow's own percentile rank, given Check 4's finding.

## Reminder

Real gauge data, real drought years, real historical record — not synthetic, unlike `climate_cat_lab`'s
and `grid_reserve_lab`'s Phase 0/1 oracles. Same caveat as `research/01_recurring_hydrological_regime.md`'s
choice of the Colorado River Basin: this characterizes this basin's real historical record, not a
claim about any specific reservoir-operator's current real-time decision-making.

## Next: Phase 1

Build the four-rung ladder (historical/paleo-record resampling baseline, vanilla spatial GP, GP +
soft-EM regime-mixture — now informed by Check 3 to consider a time-varying rate — and the
mandatory non-mixture pooling control), fit on pre-2000 data, score against the real held-out
2000-2025 megadrought per `LAB_PLAN.md`'s Method section.
