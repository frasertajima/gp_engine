# soft_em_illustration — a pure, artificial illustration of when GP soft-EM actually beats a vanilla model

**Status (2026-08-06): DONE.** `soft_em_illustration/` fits real models (not just shape charts) to
synthetic data with controllable ingredients, and directly answers "does soft-EM's 2-component
`GaussianMixture` mechanism actually produce a better-calibrated result, and when." Built after
`OUTCOME_SHAPE_TAXONOMY.md` named 5 generative ingredients but only illustrated their effect on
outcome *shape* — no model had been fit anywhere in `decision_harness_lab` yet.

## What "GP soft-EM" means here, concretely

Confirmed by reading `grid_reserve_lab/regime_mixture.py`/`dgp_simulator.py` directly: fit a
2-component `sklearn.mixture.GaussianMixture` on the observed outcome to get soft per-instance
responsibilities, then fit a model per component, weighted by those responsibilities. "Vanilla" is
the 1-component, pooled, regime-blind fit. In `grid_reserve_lab` the per-component model is a
*spatial* GP (multiple correlated sites); stripped of that spatial layer — deliberately, to keep
every file in this lab readable end to end — the core mechanism reduces to a 1-vs-2-component
Gaussian-mixture fit to a scalar outcome, exactly what `shape_diagnostics.py`'s mode-count/
separation-ratio tools already measure.

**The decision task**: reserve/quantile sizing against a reliability target, scored on a fresh
out-of-sample resample — `grid_reserve_lab/reserve_calc.py`'s actual convention
(`required_reserve_mw`, `score_method`), reimplemented locally in a few lines
(`fit_compare.py`) rather than importing that module's fleet-shaped API. This is a distributional
question (characterize the whole outcome distribution), not a per-instance forward-prediction one —
soft-EM's mechanism was never built to predict a new instance's regime from a covariate, so this
lab doesn't force it into that frame.

## A real methodological correction, found while building this, not planned

A first pass compared only two conditions: `empirical` (raw historical quantile) vs. `soft_em`. It
found `soft_em` "winning" even at near-zero separation — where there is no real regime to capture at
all. The reason: **any** parametric fit smooths a noisy order-statistic estimate at a deep quantile,
regardless of whether it's capturing real structure. That's a generic parametric-smoothing effect,
not evidence the 2-component mixture specifically helps.

Fixed by adding a third condition, mirroring `bayesian_decision_lab`'s own isolate-what's-doing-the-
work design (SVM / GPC-mean-only / GPC-full): **`one_component`** — a single Gaussian fit + resample,
parametric but regime-blind. This isolates "does smoothing help" (visible in `empirical` vs.
`one_component`) from "does the mixture help" (visible in `one_component` vs. `soft_em`). Every
result below uses this 3-condition design.

## Sweep 1 — ingredient 2: between-state separation

Fixed rare imbalance (`p_state1=0.05`), separation swept 0.5–8 pooled-SD (same units
`separation_ratio_from_samples` measures), `target_reliability=0.999`, `n_hist=150`, 150 bootstrap
trials per point.

| separation | one_component: rel / cost | soft_em: rel / cost | mixture gap (rel) |
|---|---|---|---|
| 0.5 | 0.9988 / 3.13 | 0.9972 / 2.92 | -0.0015 [-0.0065,+0.0006] |
| 1.0 | 0.9985 / — | 0.9971 / — | -0.0014 [-0.0072,+0.0013] |
| 2.0 | 0.9958 / — | 0.9958 / — | -0.0001 [-0.0052,+0.0044] |
| 3.0 | 0.9892 / — | 0.9953 / — | +0.0062 [-0.0033,+0.0137] |
| 4.0 | 0.9798 / — | 0.9965 / — | +0.0167 [+0.0044,+0.0281] |
| 6.0 | 0.9644 / 6.56 | 0.9975 / 9.97 | +0.0331 [+0.0120,+0.0480] |
| 8.0 | 0.9571 / — | 0.9969 / — | +0.0399 [+0.0188,+0.0498] |

**A clean crossover, exactly the predicted mechanism**: below ~2-sigma separation, `one_component` is
at least as good as `soft_em` (the extra mixture component is pure overfitting risk on genuinely
single-process data) — CI includes 0 or favors `one_component`. Above ~3 sigma, the gap turns
significantly positive and grows monotonically: `one_component` collapses on both reliability
(misspecified — a single Gaussian can't represent two well-separated modes) **and** cost (it
underpays because it doesn't see the far tail as its own thing, which is a real reliability failure,
not a legitimate cost saving).

## Sweep 2 — ingredient 1: regime rarity/imbalance

Fixed well-separated regime (`separation=6.0`), `p_state1` swept 0.5 (balanced) down to 0.02 (rare).

**Reliability alone was actively misleading here — caught by reading it alongside cost, per this
codebase's own discipline.** At `p_state1=0.5`, `one_component` shows *higher* raw reliability
(1.0000 vs. `soft_em`'s 0.9985) — but only by grossly overpaying: cost=12.7 vs. `soft_em`'s cost=8.8,
a 44% overpay for a 0.15-point reliability gain. Fitting one Gaussian to genuinely bimodal, balanced
data inflates its variance estimate and over-covers at high cost — reliability without cost is
exactly the single-number-summary trap `insure_vs_self_insure.py` already warned against.

Read together (cost-adjusted), `soft_em` is the better-calibrated choice across most of the sweep,
collapsing only at the most extreme point tested (`p_state1=0.02`, ~3 expected minority-state points
in `n_hist=150`) — too few for even the mixture to reliably identify a second component at all. This
is not "the rarer the better without limit" — it mirrors `bayesian_decision_lab`'s own Phase 2
finding that GPC's advantage "peaks in a moderate-asymmetry zone and compresses toward both
extremes."

## Sweep 3 — sample size: two distinct reasons soft-EM wins

Fixed at the decisive point above (`separation=6.0`, `p_state1=0.05`), `n_hist` swept 50–3,000.

| n_hist | empirical | one_component | soft_em | gap vs. empirical | gap vs. one_component |
|---|---|---|---|---|---|
| 50 | 0.9798 | 0.9653 | 0.9875 | +0.0077 | +0.0222 |
| 150 | 0.9928 | 0.9644 | 0.9975 | +0.0047 | +0.0331 |
| 600 | 0.9975 | 0.9630 | 0.9987 | +0.0012 | +0.0357 |
| 3000 | 0.9986 | 0.9632 | 0.9989 | +0.0002 | +0.0357 |

**Not the single hypothesis this sweep started with.** The original expectation was "the gap shrinks
as N grows" — true only for the `empirical` comparison (0.0077 → 0.0002, a variance problem more data
straightforwardly fixes). The `one_component` comparison stays flat (~0.033–0.036) across the entire
range: a **bias/misspecification** problem, not a variance one — a single Gaussian never converges to
a 2-component truth no matter how much data it sees. Soft-EM wins for two structurally different
reasons, and only tracking both conditions separately made that visible.

## Negative control — ingredient 3: a single skewed process, no real regime

Reuses `toy_examples/invest_decision.py`'s `_zero_mean_lognormal` skew trick — one continuous,
right-skewed process, no second discrete state.

| condition | reliability | reserve |
|---|---|---|
| empirical | 0.9926 | 3.53 |
| one_component | 0.9812 | 2.35 |
| soft_em | 0.9922 | 3.36 |

**Found, not confirmed as hypothesized.** Per `OUTCOME_SHAPE_TAXONOMY.md`'s row 5, this shape should
not be a soft-EM candidate — but `soft_em` still edges out `one_component` here (+0.0110
[+0.0054,+0.0217]). The honest reason is not "a hidden regime was detected" — `one_component`'s
single *symmetric* Gaussian is itself misspecified for a *skewed* distribution, and a 2-component
mixture is flexible enough to partially approximate skew even with no discrete latent structure at
all. The more informative comparison is `soft_em` vs. `empirical`: they land close together (0.9922
vs. 0.9926), both clearly ahead of `one_component`. **The corrected claim**: soft-EM helps whenever
the truth isn't well-approximated by a single Gaussian — a real discrete regime is the cleanest,
most interpretable case where that's true, but not the only one. "Soft-EM only helps when there's a
real regime" is not quite right as stated.

## Deferred, not rebuilt here

- **Ingredient 4 (payoff nonlinearity/censoring)** already has a definitive answer:
  `bayesian_decision_lab`'s Jensen's-inequality proof that a linear-in-state payoff cannot express
  option-like convexity, regardless of posterior variance. Referenced, not reproduced.
- **Ingredient 5 (mass vs. height)** was already caught directly while building
  `shape_diagnostics.py`'s `count_modes_by_mass` (see that module's docstring). Referenced, not
  reproduced.

## Risks / honest unknowns

- **Still entirely synthetic.** This sharpens intuition with real, swept numbers instead of one-off
  toy examples, but it is not a substitute for `OUTCOME_SHAPE_TAXONOMY.md`'s Phase 3 readiness
  checklist — a real domain still needs its own history checked directly for recurrence and rarity
  before any of this is assumed to transfer.
- **The negative control's result complicates the clean story** (see above) — a 2-component mixture
  is a flexible density estimator, not purely a regime detector, so "does soft-EM show a gain" is not
  by itself proof of a real recurring regime. Combine with `separation_ratio_from_samples` and actual
  domain knowledge, not this comparison alone.
- **All sweeps fix `target_reliability=0.999`, a deep tail.** At shallower targets (e.g. 0.99, tested
  during development), the effect sizes shrink and become noisier — the mechanism is real but its
  practical size depends on how deep into the tail the actual decision cares about, exactly the same
  "the advantage is a property of the economics, not a fixed number to quote out of context" lesson
  `bayesian_decision_lab`'s own Phase 2 cost-ratio sweep already established.
- **`GaussianMixture(n_components=2)` is fixed**, never selected by a model-comparison criterion
  (BIC/AIC) — a real application should let the data indicate 1 vs. 2 components rather than assuming
  2 a priori, which this lab does throughout for clarity.

## Structure

```
decision_harness_lab/soft_em_illustration/
  oracle.py              DONE -- two-state scalar generator, separation/imbalance knobs, self-test
  fit_compare.py          DONE -- empirical/one_component/soft_em reserve + score + bootstrap_compare
  sweep_separation.py     DONE
  sweep_imbalance.py      DONE
  sweep_sample_size.py    DONE
  negative_control.py     DONE
  sweep_viz.py            DONE -- reliability/gap sweep charts, house style (reuses ../viz.py)
  build_notebook.py       DONE -- assembles SOFT_EM_ILLUSTRATION.ipynb via nbformat
  SOFT_EM_ILLUSTRATION.ipynb   DONE -- executed live (real bootstraps, not pre-computed JSON)
```
