# Robustness Follow-ups (2026-07-24)

A structural/mathematical critique of the notebook (`Climate_CAT_Lab_Report.ipynb`) raised
three fair pushbacks on the headline soft-classifier finding (RESULTS_PHASE1.md,
RESULTS_PHASE2.md): (B) the classifier's feature — the book's total log loss — is close
to a sufficient statistic for the regime *by construction*, since the DGP's regime
affects the whole book at once; (C) every method samples from a point estimate, silently
ignoring parameter/epistemic uncertainty; (D) the whole result could be an artifact of
one hand-picked DGP configuration. This document reports three follow-up experiments
(`phase1_localized_sweep.py`, `phase1_param_sweep.py`, `phase1_uncertainty_sweep.py`)
answering each directly, plus a real numerical bug the first of those experiments
surfaced and the fix applied.

## A real bug found while building the localized-regime test, and its fix

`phase1_localized_sweep.py`'s very first run produced a nonsensical result: Method 4
(soft) at `footprint_frac=1.0, n_years=60` reported `capital_gap=+$193,777,189` — a
number ~19x the entire oracle's true capital, for a method whose headline numbers
(RESULTS_PHASE1.md) are all within a few million dollars of the truth.

**Root cause**: at small `n_years`, the GaussianMixture classifier can put ~100%
responsibility on a single year (`eff_n_sys=1.00` was observed directly), leaving the
"systemic" component's weighted spatial-kernel MLE to fit on an effectively singleton
sample — hopelessly underdetermined for a 3-hyperparameter kernel. Nelder-Mead can
(rarely — **not** deterministically; most single-effective-year fits land fine, e.g. one
observed fit converged to a harmless all-zero-variance solution) wander into a degenerate
high-variance basin: one fit landed on `sigma_f2=15.79` against a healthy-fit ceiling of
~0.1-0.7, producing Monte Carlo scenario draws in the hundreds of billions of dollars.

**First fix attempted, and rejected**: flooring each year's GaussianMixture
responsibility (`clip(resp, resp_floor, 1-resp_floor)`, the soft-fit analogue of
`fit_regime_mixture`'s `min_stress_years` floor) does prevent the collapse, but it also
**diluted every already-healthy fit** to guard against a rare event — re-running
`phase1_soft_sweep.py`'s own published seeds with this floor dropped n_years=60's
achieved survival from 98.78% to 94.20%, reintroducing a milder version of the exact
discard-information dilution problem the soft classifier exists to avoid. Rejected.

**Fix kept**: a numerical safety cap on the *fitted result* itself, not the input
weights. `gp_loss_model.py`'s `mle_fit_spatial`/`mle_fit_spatial_weighted` now reject
any `(sigma_f2, sigma_n2)` candidate whose sum exceeds `var_cap_mult=5.0` times a
reference variance — critically, that reference is computed from the **unweighted**-mean
residual (`fit_gp_loss_model_weighted` computes it once, before any component-specific
weighting, and passes it down as `ref_var`), not from the weighted residual matrix R
itself, whose own variance is contaminated by the same degeneracy the cap needs to catch
(a first attempt anchored on `max(weighted, unweighted)` variance of R and didn't bind on
the failure case — R's unweighted variance is itself inflated when the weighted mean it's
centered on is one atypical year's values). Verified directly: the pathological seed
dropped from `sigma_f2=15.79`/capital \$593M to `sigma_f2=0.59`/capital \$23M at
`var_cap_mult=3.0`, and every one of RESULTS_PHASE1.md's originally-published seeds
reproduces its published number almost exactly (98.91% vs. 98.78% at n_years=60, within
seed noise) under the fix — the fix binds only on the pathological case.

**What the cap does NOT do**: eliminate the underlying unreliability of fitting a
sophisticated model on ~1 effective data point — that's not a bug, it's information-
theoretic, and it's exactly what the uncertainty sweep below quantifies honestly rather
than papering over.

## B. Does the soft classifier survive a LOCALIZED regime? (`phase1_localized_sweep.py`)

The DGP's regime multiplies the *whole* book at once, so the classifier's total-loss
feature is close to a sufficient statistic by construction — a fair confound. This
variant (`dgp_simulator_localized.py`) restricts each systemic year's shock to a random
circular footprint covering only `footprint_frac` of the book (radius calibrated from
the book's own pairwise-distance distribution); properties outside it behave as in a
normal year even in a "systemic" year.

| footprint_frac | Classifier separation (mean resp, true-sys vs true-normal) | 4_hard survival | 4_soft survival |
|---|---|---|---|
| 1.0 (global, this module's own baseline) | 1.000 | 95.1% / 97.8% | 98.8% / 99.6% |
| 0.20 | 0.95 / 0.98 | 95.0% / **97.5%** | 97.8% / 97.2% |
| 0.05 | 0.77 / 0.78 | 96.0% / 97.1% | **98.2%** / 97.8% |
(each cell: n_years=60 / n_years=500)

Classifier separation degrades gracefully (1.00 → 0.95-0.98 → 0.77-0.78) as the footprint
shrinks to 5% of the book — genuinely weaker, as the critique predicted — but does not
collapse, and the soft classifier keeps a meaningful edge over hard/baselines at every
footprint level tested, including the most localized. **One honest exception**: at
`footprint_frac=0.20, n_years=500`, hard (97.54%) edged out soft (97.17%) — the only
config in this entire lab where hard beat soft. Reported as observed, not smoothed over.
This does not overturn the headline finding, but it does temper it: the soft classifier's
advantage is real and survives meaningful localization, but is not universal, and a
DGP with a MORE extreme footprint (well under 5%) or a book with less geographic overlap
between the historical sample and future risk might behave differently — untested here.

## D. Is the finding an artifact of one DGP configuration? (`phase1_param_sweep.py`)

One-at-a-time sweep around the baseline DGP (ℓ=0.5°, p_sys=1/15, m_sys=6.0), plus one
non-stationary variant, all at a fixed 120 historical years:

| Config | Oracle true capital | 1_independence | 4_hard | 4_soft |
|---|---|---|---|---|
| baseline | $10,273,977 | 93.29% | 96.25% | **99.41%** |
| ℓ=0.1 (localized field) | $7,197,912 | 93.29% | 93.46% | **98.64%** |
| ℓ=1.5 (regional field) | $13,365,156 | 93.43% | 98.26% | **99.73%** |
| p_sys=1/30 (rarer) | $8,517,583 | 96.71% | 97.03% | **99.58%** |
| p_sys=1/5 (frequent) | $12,997,914 | 80.02% | 96.50% | **99.44%** |
| m_sys=2.0 (weak signal) | $3,424,659 | 93.45% | 97.02% | **99.31%** |
| m_sys=10.0 (strong signal) | $17,123,295 | 93.29% | 96.41% | **99.33%** |
| non-stationary (p_sys drifts 1/30→1/5, oracle at 1/5) | $11,702,649 | 88.36% | 96.39% | **99.37%** |

The soft classifier stays at 98.6-99.7% achieved survival across every configuration
tested — a >6x range in true required capital, a >3x range in regime frequency, a 15x
range in spatial length scale, a 5x range in severity multiplier, and a non-stationary
trend the historical window only partially captures. This is the clearest answer to
critique D: the finding is not a hand-picked artifact of one DGP setting. Two
side-findings worth noting: (1) `ℓ=0.1` is the one config where hard drops close to the
no-regime ceiling (93.46%) while soft stays strong (98.64%) — a very short, hard-to-
resolve length scale seems to hurt the hard partition's coarser data allocation more than
soft's full-information fit; (2) baseline methods' own ceiling is NOT fixed at ~93.3% —
it moves with `p_sys` (96.7% at 1/30, only 80.0% at 1/5) and the non-stationary drift
(88.4%), exactly as expected: a less/more frequent or trending regime changes how much of
the true tail a correlation-blind model misses.

## C. How much does the capital ESTIMATE itself vary by historical draw? (`phase1_uncertainty_sweep.py`)

Every method here samples scenarios from its own fitted point estimate, never propagating
parameter uncertainty. Cheap, non-Bayesian answer: redraw 25 independent historical
samples per grid point, refit from scratch each time, and report the empirical
5th/50th/95th percentile of the resulting capital ESTIMATE — literally the point
estimate's own sampling distribution. Oracle true capital: $10,200,242.

| n_years | Method | p5 | p50 (median) | p95 | CV |
|---|---|---|---|---|---|
| 60 | 3_vanilla_gp | $0.78M | $1.51M | $2.08M | 0.25 |
| 60 | 4_hard | $0.80M | $3.81M | $8.66M | 0.60 |
| 60 | 4_soft | $1.51M | **$9.96M** | $14.20M | 0.45 |
| 120 | 3_vanilla_gp | $1.30M | $1.58M | $2.01M | 0.15 |
| 120 | 4_hard | $3.92M | $6.38M | $8.11M | 0.23 |
| 120 | 4_soft | $6.86M | **$10.70M** | $47.69M | 0.80 |
| 250 | 3_vanilla_gp | $1.37M | $1.50M | $1.82M | 0.10 |
| 250 | 4_hard | $5.11M | $6.10M | $7.82M | 0.13 |
| 250 | 4_soft | $8.10M | **$10.08M** | $12.69M | 0.15 |
| 500 | 3_vanilla_gp | $1.39M | $1.61M | $1.74M | 0.08 |
| 500 | 4_hard | $5.27M | $6.27M | $7.02M | 0.09 |
| 500 | 4_soft | $8.35M | **$10.24M** | $12.02M | 0.11 |

Two findings, both important, in some tension with each other:

1. **The soft classifier's median is remarkably accurate at every data size** — $9.96M
   to $10.24M against a $10.20M truth, essentially unbiased even at 60 years, while
   method 3 (no regime) and hard-partition method 4 are both persistently, substantially
   biased low (method 3 never exceeds $2.1M at ANY historical sample size — a genuine,
   unmovable structural ceiling, not just an achieved-survival statistic).
2. **The soft classifier's SPREAD is not small, and is not even monotonically shrinking**
   — CV actually *rises* from 0.45 (n=60) to 0.80 (n=120, driven by a rare outlier fit
   among the 25 draws — the residual, non-catastrophic version of the numerical
   instability described above, still possible at low but non-negligible probability
   even under the variance cap) before settling to 0.11 by n=500. **A real insurer fitting
   on their own single historical draw, at n_years=60, could land anywhere from $1.5M to
   $14.2M** — the median is excellent, but the point estimate a single fit produces is not
   a reliable substitute for a real uncertainty quantification (full Bayesian or
   bootstrap-ensemble treatment), which this lab does not attempt.

This is the most important qualifier on the whole notebook's headline claim: soft
classification fixes the *systematic* bias (methods 1-3 and hard-partition method 4 are
all persistently biased low, regardless of luck), but does not fix — and this experiment
was never expected to fix — the *sampling* uncertainty inherent in fitting from one finite
historical window. Both are real, and a practitioner should care about both.

## Summary: what changed, what didn't

- **RESULTS_PHASE1.md/RESULTS_PHASE2.md's headline numbers are unaffected** — re-verified
  directly against the exact seeds those results were built from; the numerical fix binds
  only on cases those specific runs never happened to hit.
- **The soft classifier's advantage is real, generalizes across DGP configurations tested
  (critique D: answered), and survives (with one honest exception) meaningful spatial
  localization of the regime (critique B: answered, with nuance) — but does not eliminate
  genuine sampling/epistemic uncertainty in the point estimate itself (critique C:
  answered, and NOT fully resolved — that's an accurate finding, not a gap in this
  follow-up).**
- A real, reusable robustness improvement (the variance-cap fix) is now part of
  `gp_loss_model.py`'s weighted MLE, benefiting any future use of the soft classifier,
  including Phase 2's OOC-scale port (unaffected by the original bug, but now doubly
  protected).
