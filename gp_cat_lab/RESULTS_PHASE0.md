# Phase 0 Results — the oracle and the sanity check (2026-07-23)

**Setup:** `phase0_run.py`, pure NumPy (no GPU needed at this scale — same reasoning
`cvar_gp_lab/scenario_gen_gp.py` gives for small-n covariance sampling). 500-property
synthetic book (`exposures.py`), 50,000 simulated years from the oracle DGP
(`dgp_simulator.py`), seed 0. All four checks passed; `results_phase0.json` has the raw
numbers.

## What Phase 0 is checking

The whole lab rests on one premise: a synthetic world where the *true* loss distribution
has genuine tail dependence that a linear-correlation model structurally cannot represent
(LAB_PLAN.md's core hypothesis). Before fitting anything, Phase 0 verifies the oracle DGP
actually has that property — not asymptotically-in-theory, but measurably, in a finite
simulated sample at a realistic tail quantile.

## Results

| Check | Metric | Result | Passed |
|---|---|---|---|
| 1. Regime mechanism | systemic/normal severity ratio | **9.05x** | ✓ |
| 1. Regime mechanism | near-pair corr, normal years | −0.000 | ✓ |
| 1. Regime mechanism | near-pair corr, systemic years | **0.477** | ✓ |
| 2. Distance decay | unconditional corr, near pairs | 0.624 | ✓ |
| 2. Distance decay | unconditional corr, far pairs | 0.277 | ✓ |
| 3. Tail dependence (oracle) | λᵤ, near pairs (q=0.99) | **0.439** | ✓ |
| 3. Tail dependence (oracle) | λᵤ, far pairs (q=0.99) | 0.149 | ✓ |
| 3. Tail dependence (oracle) | independence baseline (1−q) | 0.010 | — |
| 4. Gaussian comparator | λᵤ, same mean+cov as oracle | **0.198** | ✓ |

**1. The regime mechanism works as designed.** Systemic ("correlated climate-extreme")
years are 9x more severe in total book loss than normal years, and nearby properties'
losses go from essentially uncorrelated in normal years (−0.000) to strongly correlated in
systemic years (0.477) — the shared spatial shock field only fires in systemic years, and
it shows.

**2. Real spatial structure, not a flat number.** Nearby property pairs (within one kernel
length-scale) are markedly more correlated (0.624) than distant pairs (0.277), confirming
the DGP has genuine distance-decaying dependence for a spatially-aware model to actually
learn — the reason a flat/block correlation baseline is the wrong *shape*, not just the
wrong number.

**3. The headline number, using the literature's own definition.** λᵤ is the upper
tail-dependence coefficient exactly as defined in Donnelly & Embrechts (2010, Definition
5.1 — `research/03_gaussian_copula_tail_dependence.md`): the probability that property Y
also has an extreme (99th-percentile) loss, given that nearby property X did. Independence
would give λᵤ = 1−q = 0.010 exactly. The oracle gives **0.439** for nearby pairs — a
**44x** excess over what independence predicts — and a smaller-but-still-real 0.149 for
distant pairs, confirming the tail dependence itself decays with distance, same as the
ordinary correlation does.

**4. The demonstration that actually matters for the whole lab.** A Gaussian model was fit
to the exact same simulated sample's mean vector and full covariance matrix — so its
ordinary Pearson correlation matches the oracle's *exactly*, by construction; nothing about
"the wrong average correlation" is in play here. Resampling from that Gaussian and
computing the identical λᵤ gives **0.198** — less than half the oracle's 0.439. Two loss
models with identical second-moment (mean+covariance) statistics disagree by more than 2x
on the probability of a joint catastrophic loss. This is check 3a from
`research/03_gaussian_copula_tail_dependence.md` made concrete and numeric in this lab's
own synthetic world, not just cited from the literature: a correlation-matrix-only
aggregation step *cannot see* this gap, no matter how well its correlation number is
calibrated, because the gap lives entirely in the tail shape, not the correlation.

## A methodology correction worth recording

The first draft of check 3 conditioned on the **worst 1% of years by total book loss**
(rather than each property's own marginal quantile) and compared that subset's *Pearson
correlation* against the unconditional correlation. That version **failed** — the
tail-conditioned correlation came out *lower* than the unconditional correlation
(unconditional 0.605, tail-conditioned 0.429), the opposite of the intended signal.

The reason is a real confound, not a bug in the arithmetic: pooling across the regime
mixture inflates the *unconditional* correlation, because both properties' losses jump
together whenever the regime switches (a shared mean-shift), on top of whatever
correlation exists within each regime. That mean-shift contribution is large and present
in the full sample, but mostly *conditioned away* once you restrict to the very worst
years (which are already almost all systemic) — so the conditional correlation measures
something narrower (correlation among the worst of the systemic years alone) and can
legitimately come out lower than a figure that also includes the marginal boost from
mixing normal and systemic years together.

The fix was to switch to the standard **joint-exceedance-probability** definition of λᵤ
(each property's own marginal quantile, not a book-total-loss cutoff) — the same
definition already cited from the literature in Phase -1's research pass
(`research/03_gaussian_copula_tail_dependence.md`), which doesn't have this confound. This
is worth recording for two reasons: it's a genuine methodological lesson (naive
"conditional correlation" is not the same thing as tail dependence, and can even point the
wrong direction under a regime mixture), and it's a second, independent confirmation — from
inside this lab's own numbers now, not just the literature — that Pearson correlation is
an unreliable stand-in for tail risk exactly the way `research/03` said it would be.

## What's next

Phase 1: the four-method ladder (independence, flat/block correlation, vanilla spatial GP,
GP + regime-mixture), each producing a capital/retention decision, scored against this
oracle's actual achieved survival probability and dollar gap — per `LAB_PLAN.md`'s Method
section.
