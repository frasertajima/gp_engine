# Phase 1 results — three-method ladder, scored against KW51's real retrofit dates

**Status: DONE (2026-07-28).** `daily_agg.py` / `classical_baseline.py` / `gp1d.py` /
`vanilla_gp.py` / `regime_mixture.py` / `phase1_run.py` / `results_phase1.json`. Five well-identified
modes (2, 4, 5, 8, 12, per `RESULTS_PHASE0.md`), daily-aggregated, fair-fight protocol: every
method fit ONLY on a random 70% of pre-retrofit days (train), threshold calibrated on the
remaining 30% (held-out-normal, never used for fitting) to a matched 10% false-alarm rate, then
applied prospectively to during+post.

## Headline finding — a genuine mixed/negative result, reported plainly, not softened

**In this first implementation, the soft-EM regime-mixture mechanism does not show a clear
advantage over the simpler classical regression or vanilla-GP z-score approach.** Where its
responsibility signal is well-calibrated (modes 5, 12), it detects the real retrofit no earlier
than the simpler methods' z-score approach already does. Where it is poorly calibrated (modes 2,
4, and — worth flagging specifically — mode 8, the mode with the *strongest* temperature confound,
exactly the case this lab most wanted regime-awareness to help with), its own false-alarm rate is
substantially *worse* than the classical/vanilla methods' matched 11.5% rate. This is consistent
with `LAB_PLAN.md`'s and `research/RESEARCH.md`'s stated honest possibility ("this lab may simply
replicate what heteroscedastic GP or regime-switching cointegration already achieve, with no
material advantage") — reported as found, not adjusted to look better.

## A real bug found and fixed along the way (kept here, not hidden)

The first implementation ran the EM fit over held-out-normal + during + post data together, which
meant regime B's GP was directly **fit on the same held-out-normal points later used to measure
its false-alarm rate** — an obvious source of leakage once seen: every mode showed a spurious
~0.97-1.0 "false alarm" responsibility, because a freshly-refit flexible GP will always predict its
own training points well, regardless of whether anything real changed. Fixed by restricting the EM
fit to during+post only (the genuinely unknown period) and scoring held-out-normal days **post-hoc**
against the final, frozen mixture — a real held-out test, not a leaked one. A second, smaller
data-split bug was caught first: the original chronological 70/30 pre-retrofit split put winter in
train (-0.9 to 12.7°C) and spring in held-out (5.4 to 20.6°C), so held-out days were partly
out-of-training-temperature-range — fixed with a random (not chronological) split, so both share
the same temperature distribution, isolating true false-alarm rate from pure extrapolation error.

## Full results table

All values at a matched 10%-target false-alarm rate (empirically 11.5% on the small held-out
sample, ~52 days — `TARGET_FA_RATE=0.10` in `phase1_run.py`). "Flag rate during+post" and "sustained
onset" are for Methods 0/1 and for Method 2's z-score-vs-frozen-regime-A (which is, by
construction, numerically identical to Method 1's — both are literally the same GP fit on the same
train data, only the labeling differs). Method 2's *own* signal is the responsibility-to-regime-B
columns.

| Mode | corr(freq,temp)\* | M0 classical: flag rate / onset | M1 vanilla GP: flag rate / onset | M2 resp-B: FA rate (heldout) / onset | M2 π_B final |
|---|---|---|---|---|---|
| 2  | -0.553 | 0.791 / 2019-05-23 | 0.758 / 2019-05-23 | **0.846** / 2019-05-21 | 0.95 |
| 4  | -0.644 | 0.582 / 2019-05-29 | 0.619 / 2019-05-29 | **0.558** / 2019-05-30 | 0.77 |
| 5  | -0.103 | 0.877 / 2019-06-04 | 0.861 / 2019-05-28 | 0.058 / 2019-06-25 | 0.84 |
| 8  | -0.738 | 0.996 / 2019-05-21 | 0.996 / 2019-05-21 | **0.231** / 2019-05-21 | 0.95 |
| 12 | -0.192 | 0.893 / 2019-06-03 | 0.816 / 2019-06-20 | 0.019 / 2019-06-25 | 0.84 |

\*From `RESULTS_PHASE0.md`. **Bold** = false-alarm rate materially above the 11.5% target the
classical/vanilla methods hit by calibration.

## What this actually shows

- **Classical regression vs. vanilla GP: a wash, mode-dependent, no consistent winner.** Detection
  rates and onset dates trade places mode by mode (vanilla detects 6 days earlier on mode 5,
  17 days later on mode 12; both saturate to ~1.0 flag rate on mode 8's strong confound). Consistent
  with `research/03_gp_already_used_in_shm.md`'s finding that GP alone isn't a novel or
  automatically-superior idea here — at this data scale, with only a single global temperature
  relationship, a GP's flexibility over plain linear regression doesn't materially change anomaly
  scoring.
- **The regime-mixture calibrates well on the two least-confounded modes (5, 12) — but doesn't
  detect any earlier there than the simpler methods already do.** Its onset dates (both 2019-06-25)
  are *later* than classical/vanilla's onset on the same modes. A real, honest non-advantage: being
  well-calibrated is not the same as adding value.
- **The regime-mixture calibrates poorly on the more strongly-confounded modes (2, 4, and
  especially 8).** Mode 8 is the single most informative case: it has the strongest temperature
  confound (r=-0.738, per Phase 0) — exactly the situation this lab hoped regime-awareness would
  help with most — and instead shows a 23.1% false-alarm rate on held-out-normal data, roughly
  double the classical/vanilla methods' matched 11.5%. The likely mechanism: a strong,
  possibly-nonlinear (Peeters & De Roeck found a bilinear, not simple linear, temperature
  relationship on the comparable Z-24 bridge) temperature dependence leaves more residual variance
  for a flexible, freely-refit regime-B GP to "explain" as a distinct regime even when nothing
  structural changed — the single-RBF-kernel GP used here may simply be misspecified for this
  mode's true temperature relationship, a modeling limitation, not evidence against regime-mixture
  methods as a class.

## Honest caveats on this specific implementation (not a final verdict on the mechanism)

- **The asymmetric EM design (regime A frozen, only regime B adaptive) is a real, stated
  simplification** (`regime_mixture.py`'s docstring) — a fully symmetric two-GP mixture, or a
  bilinear/nonlinear mean function per regime (matching Z-24's documented bilinear
  temperature-frequency shape), are both real Phase 2 candidates that might behave differently,
  particularly on mode 8's strong-confound case.
- **Only 122 train days / ~52 held-out days per mode** — small samples for calibrating a 10%
  false-alarm rate (each held-out point is worth ~2 percentage points); the false-alarm rate
  comparisons above are suggestive, not statistically air-tight at this sample size.
- **This result is specific to KW51's real retrofit event and these five modes** — per
  `LAB_PLAN.md`'s stated caveat, this says nothing about how the mechanism would perform on a
  gradual-damage scenario rather than a discrete, real, single intervention.

## Reminder

Per the disclaimer at the top of `LAB_PLAN.md`: none of the above is a claim about KW51's real
structural safety, and none of it should be read as "GP soft-EM is worse than classical methods for
bridge SHM in general" — it is a narrow, honestly-reported result for one specific implementation,
one specific bridge, and five specific modes, exactly the kind of finding meant to be a starting
point for a qualified engineer's own scrutiny, not a conclusion in itself.

## Next: Phase 2 — the FastAPI application

Per `LAB_PLAN.md`, the application layer is the point of this lab, not a stretch phase. It should
present exactly this kind of mixed result honestly — including the negative finding on mode 8 — not
just the cases where the regime-mixture happens to look good. Before building it, worth a brief
Phase 1b consideration (not yet started): whether a fully symmetric regime-mixture or a
bilinear-mean-function variant changes the mode-8 result, since that is the single most
informative open thread this Phase 1 pass leaves behind.
