# Phase 1 results — the four-rung ladder, scored against the real 2000-2025 megadrought

**Status: DONE (2026-07-28).** `hydro_gaussian.py` / `reservoir_sim.py` / `method0_resampling.py`
/ `method1_vanilla_mvn.py` / `method2_regime_mixture.py` / `method3_trend_control.py` /
`phase1_run.py` / `results_phase1.json`. Fit on 71 pre-2000 water years, scored against the real,
held-out 2000-2025 megadrought (26 years) Lees Ferry never saw during fitting. Lumped single-
reservoir model, capacity 21.26M acre-feet (2x pre-2000 mean annual inflow — an illustrative
"multi-year carryover" assumption, not a claim about any specific real reservoir), target
reliability 98% (Seattle's real, sourced standard).

## Headline finding — a genuinely humbling result, not a clean "soft-EM wins" story

**None of the four methods came close to the real, hindsight-optimal demand — every method
over-committed relative to what the real 2000-2025 megadrought actually sustained — and the
method that scored numerically best (Method 3, the non-mixture trend control) did so via a trend
that is NOT statistically significant (p=0.645) on the pre-2000 data it was fit to.** This is a
different, and arguably more important, kind of finding than any prior lab in this family
produced: **from data available only through 1999, there was no statistically robust signal that
the real acceleration into the 2000-2025 megadrought was coming** — not because any method here
was poorly built, but because the acceleration itself was, in a real sense, not yet present in the
pre-2000 record for any method to detect.

## Full results table

| Method | Chosen demand (AF/yr) | Bias vs. true optimal | Real achieved reliability (test years) | Real total shortfall (AF) | Dollar consequence |
|---|---|---|---|---|---|
| **True hindsight-optimal** | 9,084,156 | — | 98% (by construction) | 0 | — |
| Method 0: historical resampling (real CRSS-style practice) | 9,745,419 | **+7.3%** | 46.2% (12/26 yrs) | 17,192,844 | $41.3B |
| Method 1: vanilla joint-Gaussian (stationary) | 9,636,014 | +6.1% | 46.2% (12/26 yrs) | 14,348,297 | $34.4B |
| Method 2: GP + soft-EM regime-mixture (time-varying) | 9,698,084 | +6.8% | 46.2% (12/26 yrs) | 15,962,123 | $38.3B |
| Method 3: non-mixture trend control (mandatory per `PLAN.md` §7) | 9,210,076 | **+1.4%** | **92.3% (24/26 yrs)** | 3,273,908 | **$7.9B** |

Dollar figures use `research/04_colorado_river_economics.md`'s real, sourced figures: $2,400/AF
(the real "local supply project" replacement-cost) for over-committed demand's real shortfall,
$417/AF (the real average agricultural-conservation-program cost) per AF/yr of foregone yield for
under-committed demand — modeling choices about which real sourced figure maps to which side,
stated explicitly, not the only possible mapping.

## Why Method 3 scored better — traced down, not just reported

- **Method 2's fitted regime probability rose only from 2.8% (test year 2000) to 12.1% (test year
  2025)** — a real, genuine time-varying trend, correctly fit from the pre-2000 data, but far
  short of the 42.3% moderate-drought rate Phase 0 measured in the REAL 2000-2025 period. Why:
  the EM's fitted drought-regime responsibility on the *last 10 pre-2000 training years*
  (1990-1999) was `[0.99, 0.97, 0.999, 0, 0.996, 0, 0, 0, 0, 0]` — scattered, not a clean
  "ramping up right before 2000" pattern the logistic trend could extrapolate aggressively from.
  **The model faithfully fit what was actually there — a real, honest limitation, not a bug.**
- **Method 3's linear trend on raw log-flow (not a bounded regime probability) predicted a mean
  decline from 13,187 cfs (test year 2000) to 12,842 cfs (test year 2025)** — modest, but
  directionally correct and, being unbounded (unlike a probability that saturates), it extrapolated
  further downward than Method 2's mixture did, landing closer to the real test-period mean
  (11,975 cfs).
- **The critical caveat, checked directly, not assumed**: that trend's slope is **-0.00106/year,
  r²=0.0031, p=0.645** on the pre-2000 data — statistically indistinguishable from no trend at
  all. Method 3's better score is real in the sense that it happened, but attributing it to genuine
  predictive skill would be overclaiming what a non-significant regression coefficient can support.
  **The honest read: Method 3 got lucky that a weak, statistically insignificant trend happened to
  point in the direction the real future took** — not evidence that linear-trend extrapolation is
  a reliable tool for this problem.

## What this means — a real, humbling lesson about extrapolating through nonstationarity

Every method in this ladder, including the mechanism this whole lab family exists to test, **failed
to anticipate the real megadrought's severity from pre-2000 data alone.** This is not a failure of
implementation — Phase 0 confirmed the nonstationarity is real and measurable *in hindsight*, but
Phase 1 shows that **detecting an accelerating trend after it has happened is a fundamentally
different, easier problem than forecasting one is about to accelerate from data that precedes it.**
Fraser's own framing going into this lab (climate change undermining the static assumptions of
historical statistics) is exactly what this result demonstrates empirically, not just
conceptually: **a sophisticated, correctly-implemented, time-varying regime-mixture model can still
under-anticipate a real acceleration if the pre-acceleration data doesn't yet contain a strong
enough signal of it** — and a method that happens to extrapolate more aggressively (Method 3) is
not obviously "better" if that aggressiveness isn't statistically grounded.

## A further honest caveat on the true-optimal reference itself

The "true hindsight-optimal" demand (9,084,156 AF/yr) is itself computed from a single real
26-year sequence via bisection — a real but small, noisy reference (each additional/fewer shortfall
year moves achieved reliability by ~3.8 percentage points). Small changes in the exact test window
could shift this reference meaningfully; treat the demand-bias percentages as directionally
informative, not precise to the last decimal.

## A note for `gp_engine/PLAN.md` §7 — a real addition to the cross-lab litmus test

This lab passed both required litmus-test conditions (a recurring, rare/imbalanced regime) at the
pre-check and research-pass stages, and Phase 0 confirmed the mechanism directly in real data. Yet
Phase 1 still found the core mechanism didn't clearly win — for a *different* reason than
`shm_lab`'s pooling-vs-mixture finding. **A new, real caveat worth adding to this codebase's
litmus test**: passing conditions 1 and 2 tells you the regime exists and recurs — it does NOT
tell you whether a **pre-acceleration training window contains enough signal to extrapolate the
acceleration forward**. That is a separate, checkable question (as done here, via a real
significance test on the fitted trend/rate) and should be checked explicitly before trusting any
method's forward-looking scenario generation in a genuinely nonstationary domain.

## Reminder

Real gauge data, a real historical megadrought, real dollar figures — but this remains an
illustrative single-lumped-reservoir model, not a claim about any real utility's actual planning
decision (`LAB_PLAN.md`'s standing caveats apply in full).

## Next

Given this Phase 1 result is itself the lab's most interesting finding — not a clean method
ranking, but a genuine demonstration of extrapolation's limits under real nonstationarity — worth
deciding with Fraser whether to consolidate here (a notebook, per the `shm_lab` pattern) or pursue
a further check (e.g., does the significance-test caveat change if paleo-record data extends the
effective pre-2000 training window, per `LAB_PLAN.md`'s stretch Phase 2).
