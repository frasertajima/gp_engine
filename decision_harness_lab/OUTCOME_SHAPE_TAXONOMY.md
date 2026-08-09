# Outcome shape taxonomy — what produces each shape, and which shapes are GP soft-EM candidates

**Status (2026-08-06, sharpened 2026-08-09):** built after Phase 2's three toy examples turned out to
have three qualitatively different shapes (multi-lumped, bimodal, right-skewed) — this document asks
*why*, grounds the answer in `shape_diagnostics.py` run against this lab's own real simulated samples
(not asserted from the charts alone), and connects each mechanism to `../PLAN.md` section 7's GP
soft-EM litmus test (regime recurs many times, regime is rare/imbalanced). All numbers below are
copy-pasted from an actual `python3 shape_diagnostics.py` run, seed 0, `n_draws=200,000` —
reproducible, not retyped from memory. **2026-08-09 update**: `../../vol_regime_lab/` ran this
taxonomy's own "GP soft-EM candidate?" call all the way through on a real domain (financial
volatility regimes, real FRED VIX data) and found the table below was asking half the right
question — see "A sharpened rule: 'beats what?' is not one question" below, added after that lab's
real, replicated result forced the distinction into the open.

## The core claim

An outcome distribution's shape is not a free-floating property of "the risk" — it is fully
determined by a small number of **generative ingredients** in the decision model that produced it.
Once you know which ingredients are present, the shape (and whether GP soft-EM is even the right
tool) follows from the math, not from eyeballing a histogram. Five ingredients account for every
shape this lab has produced or that this codebase's other labs have documented:

1. **Number and weight of discrete latent states** — how many regimes exist, and how much prior mass
   each carries.
2. **Between-state separation vs. within-state noise** — whether the states' conditional outcomes
   are far enough apart, relative to their own spread, to show up as visually distinct clusters.
3. **Noise-family skew/kurtosis** — the shape of the randomness *within* a single state, independent
   of how many states there are.
4. **Payoff nonlinearity/censoring** — a cap, floor, or kink imposed by the *decision structure*
   itself (an order quantity, a deductible, an option payoff), reshaping an otherwise-smooth input
   distribution.
5. **Mass vs. height** — a diagnostic pitfall, not a generative ingredient: a rare, diffuse cluster
   can have a *short* density peak (low height) while still holding real probability *mass*, and a
   naive shape check that only looks at peak height will miss it — found directly in this lab's own
   diagnostics (see the table below), not hypothesized.

## The math behind ingredient 2 (worth stating precisely, not just "looks separated")

For a two-component Gaussian mixture with **equal weights and equal variance**, the mixture density
is bimodal if and only if the between-component mean separation exceeds twice the shared standard
deviation: `|μ1 - μ2| > 2σ` (the standard "2-sigma rule" for Gaussian-mixture modality). For unequal
weights or variances — true of every real regime-mixture case in this codebase (`grid_reserve_lab`'s
~5%/~50% regime splits, `climate_cat_lab`'s storm years) — 2 is a rule of thumb, not an exact
threshold; the true boundary shifts with the weight and variance ratio. `shape_diagnostics.py`'s
`separation_ratio_from_samples` computes this ratio directly from simulated draws using a pooled-SD
denominator, so it can be checked against real numbers rather than trusted as a rule of thumb alone.

## Diagnostics used (and a real methodological finding from building them)

- `count_modes_kde` — local maxima of a KDE, kept only if their **density height** clears a 5%
  floor.
- `count_modes_by_mass` — the KDE's density *valleys* split the support into basins; a basin is kept
  only if its **empirical sample mass** (not KDE height) clears a 2% floor.
- `separation_ratio_from_samples` — the pooled-SD ratio above, computed per state pair from real
  simulated draws (using the known state labels `simulate()` already returns).

**Found while building these, not assumed going in**: `count_modes_kde`'s height floor has a real
blind spot for exactly the shape this lab cares about most. `insure_vs_self_insure`'s `self_insure`
has a genuine 8%-probability disaster cluster spread across ~$200k — spread that thin gives the
cluster a *short* KDE peak even though it carries real probability. The height-floored diagnostic
reports **1 mode** for `self_insure` (misses the disaster cluster entirely); the mass-floored one
correctly reports **2** (see table below). A common regime concentrates its mass into a narrow, tall
peak; a rare one is often spread thin (uncertain severity), so a height-only shape check
systematically underweights precisely the regimes GP soft-EM's litmus test says matter most. This is
the practical version of the lesson `PLAN.md` section 7 already states abstractly ("rare/imbalanced
regimes are the ones worth soft-EM's complexity") — a naive shape diagnostic can silently agree with
the wrong half of that lesson unless it's mass-aware, not just height-aware.

## The taxonomy table

| Shape | Generative mechanism | Diagnostic signature (this lab's real numbers) | Real recurring regime? | GP soft-EM candidate? | Right tool if not |
|---|---|---|---|---|---|
| **Multi-lumped, comparable weight** | Several discrete states, each with real prior weight (not rare), well separated from each other | `newsvendor`, all 3 actions: height-modes=3, mass-modes=3/3, separation ratios 25–200 (huge) | Only if the states are a real, recurring classification (e.g. seasonal demand tiers) — not "rare" in the litmus-test sense | **Maybe, weakly** — condition 1 (recurs) can hold, but condition 2 (rare/imbalanced) is the risk: comparable-weight states are closer to `grid_reserve_lab`'s real near-tied EIA-930 result than its ~9% synthetic-oracle win | If states aren't rare: a plain multi-class GP classifier may already capture most of the value; soft-EM's edge shrinks toward a tie |
| **Bimodal, rare/imbalanced (thin, far cluster)** | Exactly 2 discrete states, weight strongly skewed (e.g. 92/8), minority state's mean far from the majority's | `self_insure`: height-modes=**1** (misses it), mass-modes=**2/2** (correct), separation ratio=14.14 | This is the shape `PLAN.md` §7's litmus test is written for — but only if a *real* historical sample shows the regime recurring, not just this toy example's construction | **Yes, if real** — this is the textbook target shape, contingent entirely on Phase 3 picking a real, recurring domain (see checklist below) | N/A — this is the case soft-EM is for, once real data confirms it |
| **Bimodal, tight/small-stakes** | Same 2-discrete-state mechanism as above, but small between-state separation *and* small noise — technically bimodal, economically negligible | `buy_insurance`: height-modes=2, mass-modes=2/3, separation ratio=6.68 (large by the ratio, but only a $1,000 spread) | Same discrete mechanism, different stakes | **No, not worth it** — the ratio alone can't tell you this; the raw dollar separation is what makes it not worth modeling, a reminder that separation_ratio is scale-invariant and must be read alongside the actual $ magnitude | Point estimate is already fine at this stakes level |
| **Borderline/overlapping bimodal** | 2 discrete states, moderate separation relative to noise — right at the ambiguous edge of the 2-sigma rule | `conservative`: separation ratio=3.34 (just above 2), mass-modes=2/3 (a marginal 3rd basin from noise) | Genuinely ambiguous from the shape alone | **Unclear — the dangerous middle case.** Exactly `grid_reserve_lab`'s real EIA-930 near-tie in miniature: don't assume yes or no from the ratio alone, check the real regime's actual recurrence/rarity directly | Fit both a plain GP and a soft-EM version, compare — don't guess from shape alone |
| **Right-skewed, single dominant process** | One continuous process, skewed noise family (here: a zero-mean-shifted lognormal) — no separated discrete state required for the skew itself | `aggressive`: pooled skew=**-0.10** (near zero — misleading, see note below), separation ratio=7.46, mass-modes=2/7 (5 of 7 raw valleys are noise) | Not a regime-recurrence question at all — this is a within-process noise-family question | **No** — mixture modeling would misspecify a genuinely single skewed process; per `bayesian_decision_lab`'s own Jensen's-inequality finding, this is a payoff/likelihood shape question, not a latent-state question | A skewed-likelihood GP regression (lognormal/gamma link), or explicit option-value/convexity-aware payoff modeling |
| **Censored/kinked at a decision-chosen boundary** *(not built in this lab's 3 examples — flagged as a known gap)* | A payoff cap/floor/deductible imposed by the decision itself (e.g. an explicit stop-loss or option payoff `max(x,0)`), reshaping an otherwise-smooth distribution into one with a spike or hard edge at a $ value tied to a *decision parameter*, not a state mean | Would show as a density spike/discontinuity at a value matching a decision constant (order cap, deductible), not at any state's conditional mean — distinguishable from ingredient 1's lumps by checking whether the spike's location tracks a parameter or a state | N/A — not a state-driven shape at all | **No** — this is exactly the mechanism `bayesian_decision_lab`'s Phase 1→3 redesign already proved a linear-in-state payoff can't express (see that lab's Jensen's-inequality section) | Nonlinear/option-value payoff modeling (`bo_engine.py`-style expected-improvement, or the continuous-outcome option-value path that lab's LAB_PLAN.md sketched as its unbuilt alternative) |
| **Heavy-tailed, no clean second mode** *(not built in this lab's 3 examples — flagged as a known gap)* | Single process, genuinely heavy-tailed noise (Pareto-like), not a discrete mixture at all | Would show as height-modes=1, mass-modes=1, but extreme CVaR/mean ratio and high kurtosis | N/A | **No** — imposing a 2-component mixture on a genuinely single heavy-tailed process misspecifies it | A heavy-tailed-likelihood model (Student-t GP) or a direct EVT/CVaR treatment, not a mixture |

**A second real, non-obvious finding worth stating plainly**: `aggressive`'s *pooled* skewness
(-0.10) looks almost symmetric, even though it was explicitly built from a right-skewed lognormal
component in the bull state. This is not a bug — pooling a loss-state cluster (bear, mean -4,000)
with a right-skewed gain-state cluster (bull, mean +9,000) means the *aggregate* skewness statistic
reflects the mixture of a left-shifted cluster and a right-skewed one, which can cancel in the
pooled third moment even though neither component is symmetric on its own. **Aggregate skewness is
not a reliable stand-in for "is there component-level skew" once there's also a between-state mean
shift** — a real trap worth remembering before reading a near-zero pooled skewness as "nothing
interesting happening within components."

## A sharpened rule: "beats what?" is not one question

`vol_regime_lab` (2026-08-09) is the first time this taxonomy's row-2 call ("Bimodal, rare/imbalanced
→ **Yes, if real**") was run all the way through on a real domain with a real, replicated evaluation,
not just a litmus-test shape check. The domain cleared every precondition this document and `PLAN.md`
§7 ask for — a real, live-fetched dataset (FRED VIX, 36 years, no API key needed), 94 recurring
episodes at the practitioner VIX>30 threshold, a 7.95% base rate almost exactly matching
`grid_reserve_lab`'s and `insure_vs_self_insure`'s own two cleanest wins, and a separation ratio of
2.68 — comfortably past the 2-sigma modality floor this document's own math section establishes.
**By this taxonomy's row 2, that should have been enough to expect a real win. It wasn't, and the
reason is a real, previously-uncredited gap in the table above.**

`vol_regime_lab`'s Phase 1/2 used a **3-condition** design (`empirical` / `one_component` /
`soft_em`), not the 2-condition frame this table's "GP soft-EM candidate?" column implicitly assumes.
The result, replicated across 4 real walk-forward windows and a block bootstrap (see that lab's
`LAB_PLAN.md` Phase 2 result for the full numbers):

- **`soft_em` vs. `one_component`** (a misspecified single-Gaussian/single-regime baseline): a real,
  consistent win — matched or beat it in all 4 windows tested, no exceptions.
- **`soft_em` vs. `empirical`** (a plain nonparametric quantile — no model at all): **not
  established** — closest-to-target in only 1 of 4 windows, and even that one split's advantage
  vanished (CI overlapping heavily with the alternatives) once a block bootstrap accounted for
  training-sample uncertainty.

**The sharpened rule this taxonomy's table was missing**: at *moderate* separation (roughly 2.5–3.5σ
— real, past the modality floor, but short of `soft_em_illustration`'s own ≥4–6σ "decisively wins"
zone), a high separation ratio predicts "beats a misspecified parametric baseline" reliably, but does
**NOT** predict "beats a simple nonparametric baseline." Those are two different comparisons with two
different answers, and asking only "is this shape a soft-EM candidate?" — without also asking "compared
to what alternative?" — can hide that distinction entirely, exactly as it did here until a
multi-window/bootstrap replication check forced it into view. **Revise every "Yes, if real" cell in
the table above to implicitly mean**: yes, over a misspecified parametric alternative; not
established over a nonparametric one, unless separation is comfortably in the ≥4–6σ zone
`soft_em_illustration`'s own sweep found decisive, or a real per-domain replication check (below)
says otherwise.

## Phase 3 readiness checklist

This taxonomy sharpens *how fast* a real domain can be triaged — it does not remove the requirement,
already established by `PLAN.md` §7, that a real domain be checked directly against real historical
data before any soft-EM work starts. Before picking a Phase 3 domain:

1. **Run `count_modes_by_mass` (not just `count_modes_kde`) on the domain's real historical outcome
   samples.** If it reports 1 basin, either there's no latent regime, or the regime is currently
   invisible — check condition 2 directly (below) before concluding "no regime."
2. **Compute `separation_ratio_from_samples` if state labels are available** (e.g. a known
   drought/non-drought day), or its proxy from domain knowledge if not. A ratio near 2 is the
   dangerous middle case (row 4 above) — don't guess, fit both a plain GP and a soft-EM version and
   compare, exactly as `grid_reserve_lab` and `shm_lab` already did.
3. **Check `PLAN.md` §7's two conditions directly against real history, not against the shape
   alone**: does the regime genuinely recur many times (not a single change-point, `shm_lab`'s
   counterexample), and is it rare/imbalanced (not ~50/50, the EIA-930 trap)? A shape that looks like
   row 2 above (bimodal, rare) is a *candidate* signal, not proof — the shape can be produced by
   ingredient 4 (a payoff kink) or ingredient 3 (skewed noise) instead of a real recurring state, and
   only real historical recurrence settles which.
4. **If the shape instead looks like row 5 or row 6** (skewed-unimodal or heavy-tailed with no real
   second mode), stop — soft-EM is very likely the wrong tool regardless of how "risky" the
   distribution looks, per `bayesian_decision_lab`'s own Jensen's-inequality lesson. Reach for a
   nonlinear-payoff or heavy-tailed-likelihood model instead.
5. **Even after 1-4 clear, run a 3-condition comparison (`empirical` / `one_component` / `soft_em`),
   not 2** — per "A sharpened rule" above, a real, well-separated, recurring, rare regime still only
   guarantees a win over a *misspecified parametric* baseline, not over the plain empirical quantile.
   Check both, on real held-out data, before trusting either comparison. At moderate separation
   (roughly 2.5–3.5σ), do not accept a single train/test split's result — `vol_regime_lab`'s own
   Phase 1b looked like a clean win and did not replicate across 3 of 4 other real windows tested;
   run a multi-window and/or block-bootstrap check (`vol_regime_lab/research/phase2_multi_window.py`
   and `phase2_block_bootstrap.py` are directly reusable templates for this) before calling it either
   way.

**Answering the direct question**: this taxonomy + its diagnostics put Phase 3 on solid footing for
*triage* — but "solid footing" means "know exactly which shape to look for, how to check for it fast,
and which specific claim (beats what?) actually needs testing," not "a clear shape is enough to
expect a win." `vol_regime_lab` is the concrete proof this distinction matters: a domain that passed
every check in this document still did not show an established advantage over the simplest baseline,
only over a strawman one. The checklist above (now 5 steps, not 4) is the current, sharpened
state of that triage — picking the next Phase 3 domain and running it through step 5 honestly,
not just steps 1-4, is the standing lesson.
