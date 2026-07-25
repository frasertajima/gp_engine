# Phase 1 Results — the four-way ladder (2026-07-23)

**Setup:** `phase1_run.py` (single 60-year historical trial), `phase1_sweep.py` (4
historical-sample sizes x 3 seeds each), `phase1_diagnostic.py` (one oracle-cheat
diagnostic run, not a real method). Same 500-property book as Phase 0 (seed 0). Target:
99.5% 1-year survival probability (the Solvency II SCR convention), scored against a
500,000-year oracle resample (seed 999) no fitted method ever sees. All dollar figures are
this synthetic book's annual total-loss capital, not a real book's.

**Ground truth:** the oracle's own 99.5% 1-year VaR, from 500,000 simulated years, is
**$10,200,242**.

## Headline result (single 60-year historical trial)

| Method | Required capital | Achieved survival | Target | Expected annual shortfall | Capital gap vs. truth |
|---|---|---|---|---|---|
| 1. Independence | $922,390 | 93.29% | 99.5% | $5,110,512/yr | **−$9,277,851** |
| 2. Flat correlation | $2,224,324 | 93.38% | 99.5% | $3,863,111/yr | **−$7,975,917** |
| 3. Vanilla spatial GP | $1,531,634 | 93.30% | 99.5% | $4,506,429/yr | **−$8,668,608** |
| 4. GP + regime-mixture | $2,581,735 | 93.51% | 99.5% | $3,581,714/yr | **−$7,618,507** |

All four methods, fit on one realistic 60-year historical sample, badly under-reserve —
every one holds less than a quarter of the true required capital, and every one's *actual*
survival probability lands around 93%, not the 99.5% each was aiming for. That alone is
this lab's headline finding made concrete: a plausible historical window is not enough to
get this right, for any of the four methods tried.

But the ranking among the four methods is not what Phase 1 set out to test, and the reason
why turned into the most useful part of this phase.

## The surprise: correlation structure alone barely matters here

Method 3 (vanilla spatial GP — a genuinely better-shaped correlation, fit with real
distance decay instead of a flat number) achieves almost exactly the same survival
probability as method 1 (no correlation at all): 93.30% vs. 93.29%. Method 2's flat
correlation does marginally better than both, and method 4 only slightly better than that
— on this one trial, methods 1-3 are barely distinguishable, and method 4's edge is small
enough it could be noise.

This directly contradicts the LAB_PLAN.md hypothesis's more optimistic reading (that a
better-shaped *correlation* alone would recover a real chunk of the gap). A sample-size
sweep was run to find out why, and it ruled out the obvious first guess.

## Ruling out "just not enough data" (`phase1_sweep.py`, first pass)

Re-running the four-way ladder at 60, 120, 250, and 500 historical years (3 seeds each)
showed the mixing-probability estimate converging almost exactly to the truth by
n=500 years (fitted p̂=0.065 vs. true 0.0667) — yet achieved survival for **every**
method, including the regime-aware one, stayed pinned at 93.3–93.5%, barely moving at
all across an 8x increase in historical data:

| Historical years | 1. Independence | 2. Flat corr | 3. Vanilla GP | 4. Regime-mixture (v1) |
|---|---|---|---|---|
| 60 | 93.29% | 93.44% | 93.30% | 93.52% |
| 120 | 93.29% | 93.40% | 93.30% | 93.34% |
| 250 | 93.29% | 93.45% | 93.30% | 93.39% |
| 500 | 93.29% | 93.49% | 93.30% | 93.44% |

More historical data alone was not the fix. That ruled out simple small-sample noise in
the regime-frequency estimate and pointed at something structural in how method 4's
"systemic" component was being fit.

## The actual mechanism, isolated with an oracle-cheat diagnostic

Method 4's first implementation partitioned historical years into "stress" vs. "normal"
using a **fixed top-25%-quantile split** — chosen only so the systemic component's spatial
kernel fit would have enough years to be numerically workable at n≈60. At the DGP's true
systemic frequency (~6.7%), a 25% partition pulls in roughly **3.7 ordinary years for
every genuine systemic year** — diluting the fitted "systemic" component's severity toward
something far milder than the true regime. Critically, that dilution ratio (25% ÷ 6.7%)
doesn't shrink as historical data grows, which is exactly why more data alone didn't help.

`phase1_diagnostic.py` tested this directly: the same GP-mixture machinery, but
partitioned using the historical sample's **true, oracle-only regime labels** (something
no real method is allowed to do) instead of the 25%-quantile proxy:

| | Capital | Achieved survival | Gap vs. truth |
|---|---|---|---|
| Oracle-cheat diagnostic (true regime labels) | $10,393,010 | **99.54%** | **+$192,768** (≈2%) |

Given the *correct* partition, the exact same modeling machinery lands almost exactly on
the 99.5% target — confirming the fixed-quantile dilution, not some deeper flaw in the
DGP, the capital calculation, or the Monte Carlo scenario count, was the actual bottleneck.

## The fix, and the honest result of fixing it

`regime_mixture.py` was revised to size its partition adaptively — `margin x` the model's
**own fitted mixing-probability estimate** (still oracle-free; a safety margin and a
minimum-count floor exist only to keep the fit numerically workable at small n_years, not
to hedge against distrust in the estimate) — instead of a fixed generous quantile. Re-
running the sweep with this fix:

| Historical years | 1. Independence | 2. Flat corr | 3. Vanilla GP | 4. Regime-mixture (v2, adaptive) |
|---|---|---|---|---|
| 60 | 93.29% | 93.44% | 93.30% | **94.79%** (±1.99pp) |
| 120 | 93.29% | 93.40% | 93.30% | **96.59%** (±2.00pp) |
| 250 | 93.29% | 93.45% | 93.30% | **96.89%** (±0.28pp) |
| 500 | 93.29% | 93.49% | 93.30% | **97.29%** (±0.35pp) |

**This is the real, structural result.** Methods 1-3 — none of which can represent a
regime at all — sit on a flat, unmovable ceiling around 93.3% regardless of how much
historical data they get: adding data does not fix a model that cannot express the thing
that matters. Method 4 — the one method built to represent the same mechanism class as the
true DGP — climbs steadily with more data (94.8% → 97.3% across the sweep, closing more
than half the dollar gap: capital gap improves from −$9.3M to −$4.1M by n=500), converging
toward (though not yet reaching) the 99.5% target and the 99.54% the oracle-cheat ceiling
shows is achievable in principle. The remaining gap at n=500 is attributable to
genuine, real-world regime-classification imperfection under unsupervised estimation
(an unavoidable feature of not knowing the true regime, per the oracle-cheat comparison),
not a structural ceiling the way methods 1-3 have one.

## What this revises from LAB_PLAN.md's stated hypothesis

LAB_PLAN.md's Method section framed the open question as: does a better-shaped
correlation (method 3) already close most of the gap, or does the regime-mixture mechanism
(method 4) need to be modeled explicitly? Phase 1's answer is sharper than either original
branch:

- **A better-shaped correlation alone (method 3) closes essentially none of the gap** —
  confirmed directly, not assumed: 93.30% vs. method 1's 93.29%, indistinguishable, and
  flat with more data. Vanilla GP is still elliptical/Gaussian, exactly the limitation
  LAB_PLAN.md's Risks section flagged in advance.
- **Representing the regime mechanism (method 4) is necessary, but not automatically
  sufficient** — the mechanism CLASS matters enormously (it's the only one of the four that
  improves with data at all), but a naive, blind implementation of it (the first fixed-
  quantile classifier) can fail just as badly as having no regime model, for a completely
  different and fixable reason (classification dilution, not model structure). This is a
  genuine methodological lesson worth carrying into Phase 2: "the model class is right"
  and "the model is correctly fit" are two different claims, and Phase 1 caught a real
  failure of the second while the first held up.
- **Even correctly implemented, unsupervised regime classification leaves real headroom**
  — 97.3% vs. the 99.5% target vs. the 99.54% oracle ceiling at n=500 historical years.
  How much of that last gap is fixable with a better classifier (vs. inherent to not
  knowing the true regime) is an open question for Phase 2, not resolved here.

## Follow-up: a SOFT classifier closes almost all of the remaining gap

Answering the open question directly (`phase1_soft_sweep.py`, run after Phase 2's fair-test
rerun raised the same question at scale — see RESULTS_PHASE2.md): `regime_mixture.py`'s
adaptive partition is still a HARD cutoff — a year is either entirely in a component's fit
or entirely out, at a `margin x p_hat`-sized quantile boundary. `fit_regime_mixture_soft`
(same GaussianMixture regime-frequency estimate) replaces that cutoff with each year
contributing to BOTH components' spatial-kernel fits, weighted by its own posterior
P(systemic) — the natural "soft EM M-step" generalization (a hard partition is exactly a
soft fit with weights re-rounded to {0, 1}). `gp_loss_model.py` gained a weighted
repeated-measures MLE (`fit_gp_loss_model_weighted`) to support this.

| Historical years | Hard partition (v2, adaptive) | **Soft (responsibility-weighted)** | Oracle-cheat ceiling |
|---|---|---|---|
| 60 | 94.79% | **98.78%** | 99.54% |
| 120 | 96.59% | **99.47%** | 99.54% |
| 250 | 96.89% | **99.03%** | 99.54% |
| 500 | 97.29% | **99.25%** | 99.54% |

The soft classifier lands within 0.1-0.8pp of the oracle-cheat ceiling at every historical
sample size tested, including the smallest (60 years, where the hard partition was worst).
This resolves Phase 1's open question decisively in favor of **"the hard partition's
cutoff mechanics were costing real accuracy"** over "the gap is inherent to not knowing the
true regime": a year discarded entirely from a fit throws away real information a soft
weight preserves, and removing that discard closes nearly the whole remaining gap at every
data size — not just asymptotically with more years, the way the hard partition needed
(94.8% → 97.3% across a full 60-to-500-year climb). One numerical wrinkle fixed along the
way: when responsibility concentrates almost entirely on one year (common at small
n_years), the weighted-MLE's Nelder-Mead starting-point variance estimate could collapse
toward 0, sending `log()` to `-inf`; `mle_fit_spatial_weighted` now floors it at the
unweighted residual std when this happens (a robustness fix — the one run that hit it
before the fix produced the same result as the fixed rerun, so this didn't change any
reported number, just removed reliance on luck).

## What's next

This result is compelling enough to port to Phase 2's OOC scale (n=45,000) — see
RESULTS_PHASE2.md's "Soft classifier at OOC scale" section for whether it holds up there
too, where the classifier previously showed real headroom (96.11% vs. 99.5% target).
