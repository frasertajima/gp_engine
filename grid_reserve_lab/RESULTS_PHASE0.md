# Phase 0 results — the oracle and the sanity check

**Status: DONE (2026-07-27).** All four checks pass. `phase0_run.py` / `results_phase0.json`.
Fleet: 100 synthetic wind sites (`fleet.py`, illustrative Great Plains-shaped region), 50,000
simulated days, seed 0.

## Headline number

The literature's own upper tail-dependence coefficient (Donnelly & Embrechts 2010, Definition
5.1 — the same citation `climate_cat_lab` used, `research/03_correlation_assumption_resource_adequacy.md`)
at q=0.99 for nearby site pairs is **0.607** — a **61x excess** over the 0.010 independence
baseline. A multivariate Gaussian model fit to the exact same sample mean and full shortfall
covariance (so its ordinary Pearson correlation matches the oracle's *exactly* by construction)
gives only **0.082** — the oracle's genuine tail dependence is **7.4x** what an equally-well-fit
elliptical/Gaussian model can produce. Two models statistically identical in their second-moment
structure disagree by more than 7x on joint catastrophic-shortfall probability — the concrete
numeric version of this lab's whole premise, and a stronger separation than `climate_cat_lab`'s own
Phase 0 result (oracle λᵤ 0.439 vs. Gaussian comparator 0.198, a 2.2x gap).

## All four checks

| # | Check | Result | Passed |
|---|---|---|---|
| 1 | Drought/normal shortfall severity ratio | 4.07x | ✓ |
| 1 | Near-pair shortfall correlation, normal days | 0.001 | ✓ |
| 1 | Near-pair shortfall correlation, drought days | 0.722 | ✓ |
| 2 | Unconditional correlation, near pairs | 0.387 | ✓ |
| 2 | Unconditional correlation, far pairs | 0.243 | ✓ |
| 3 | λᵤ (q=0.99), near pairs | **0.607** | ✓ |
| 3 | λᵤ (q=0.99), far pairs | 0.140 | ✓ |
| 3 | Independence baseline (1−q) | 0.010 | — |
| 4 | λᵤ, Gaussian comparator (same mean+cov as oracle) | **0.082** | ✓ |

Fleet: 3,388 of 50,000 simulated days (6.8%) were drought days — close to the target
`p_drought=1/15` (6.67%), as expected from a large sample.

## What each check confirms

1. **Regime mechanism sanity** — drought days are both far more severe (4.07x the mean fleet-wide
   shortfall of normal days) and far more internally correlated among nearby sites (0.722 vs. 0.001
   near-pair correlation) than normal days. The DGP is doing what it's built to do: a rare, shared
   event that both worsens and correlates outcomes simultaneously.
2. **Distance decay** — nearby site pairs (within one spatial length scale) are unconditionally
   more correlated than distant pairs (0.387 vs. 0.243), confirming genuine spatial structure, not
   just a flat regime effect. This is the reason a single fleet-wide/zone-level correlation number
   is the wrong *resolution*, not just the wrong number — LAB_PLAN.md's corrected Method 2 premise.
3. **The headline tail-dependence check** — 0.607 for near pairs vs. 0.140 for far pairs, both far
   above the 0.010 independence baseline, confirming the tail dependence is both real and
   distance-decaying, not an artifact of the regime dummy alone (which would affect near and far
   pairs equally).
4. **The Gaussian comparator** — fit to the identical mean vector and full covariance matrix as the
   oracle (so ordinary Pearson correlation is unchanged), a Gaussian resample's λᵤ is 0.082 — near
   the independence baseline, nowhere near the oracle's 0.607. This is the numeric proof that
   genuine tail dependence is invisible to a correlation-matrix-only (elliptical) model, exactly
   the property Donnelly & Embrechts (2010)/Sibuya (1960) establish mathematically for the
   Gaussian copula and `climate_cat_lab`'s Phase 0 confirmed empirically in a different domain.

## A real methodology fix made along the way (kept here, not hidden)

The first version of `dgp_simulator.py` defined shortfall as the **signed** deviation
`expected_output − actual_output` (which can be negative, on days a site outperforms its
climatology). This failed check 2 outright (near-pair unconditional correlation 0.190 vs. far-pair
0.171 — indistinguishable) and produced a nonsensical severity ratio of 802x. The root cause: on
normal days, signed shortfall is ~zero-mean noise by construction (a well-behaved, unbiased
forecast error), so the drought-day regime's deterministic jump completely dominates total
variance — and because the drought multiplier applies fleet-wide (every site's output drops
together, not just nearby sites'), that jump correlates *every* pair, near or far, almost equally,
swamping the genuinely distance-decaying spatial-shock signal entirely.

The fix, structurally the same lesson `climate_cat_lab`'s own Phase 0 methodology correction
taught (conditioning statistics on the wrong pooled quantity confounds a regime-driven "everything
moves together" effect with the real spatially-resolved signal): clip shortfall to its **one-sided
positive part**, `max(expected − actual, 0)`. This also happens to be the domain-correct choice —
operating reserves respond to underperformance events, not to a site outperforming forecast — and
gives normal days a real, nonzero baseline shortfall (from the positive tail of the idiosyncratic
noise alone) instead of a near-zero one, so the spatial-decay signal is measurable against a
comparable-scale noise floor. After the fix, severity ratio dropped to a sensible 4.07x and check 2
passed cleanly (0.387 vs. 0.243).

A second, smaller tuning step was needed even after that fix: the first one-sided-shortfall run
passed checks 1, 3, and 4 but still narrowly failed check 2 (0.402 vs. 0.357, a 0.045 gap against
the 0.05 threshold) — the fleet-wide drought regime creates a "flat" baseline correlation between
every pair regardless of distance (every site's output drops together on a drought day), and the
initial spatial-shock-field variance (`spatial_field_sigma=0.6`) wasn't large enough relative to
that flat component to produce a clean distance-decay gap. Increasing it to `1.6` (both values are
tunable knobs, not claims about real wind-fleet statistics — LAB_PLAN.md's Risks section) restored
a clean separation (0.387 vs. 0.243) without needing to touch the drought frequency or severity
parameters that checks 1/3/4 already validated against.

## Not yet calibrated to real drought frequency/duration (deliberately, per LAB_PLAN.md)

`p_drought=1/15` (6.8% observed) is not tied to the real ERCOT (82 events/~5yr ≈ 4.5% of days) or
CAISO (167 events/~5yr ≈ 9.1% of days) frequencies documented in `research/04_dunkelflaute.md` —
Phase 0 only needed a working *mechanism*, not a matched real-world frequency. Phase 2 is where
real NREL WIND Toolkit/EIA-930 data replaces this synthetic fleet's geography and calibrates
drought frequency/severity to the real historical record.

## Next: Phase 1

The oracle now has a confirmed, checkable tail-dependence mechanism with a strong, not marginal,
effect size (7.4x Gaussian-comparator gap, comfortably larger than `climate_cat_lab`'s own 2.2x).
Phase 1 builds the five-method ladder (`reserve_baseline` Rust crate for methods 0-2,
`spatial_kernel.py`/`gp_loss_model.py` for method 3, `regime_mixture.py` for method 4,
`reserve_calc.py`'s CVaR-style reserve-sizing LP) and scores all five against this oracle in
achieved-reliability and dollar terms, per LAB_PLAN.md.
