# Phase 1b/1c results — does pooling across modes restore soft-EM's edge, and is it actually soft-EM?

**Status: DONE (2026-07-28).** `joint_daily_agg.py` / `joint_regime_mixture.py` / `phase1b_run.py`
/ `results_phase1b.json` (the joint soft-EM model); `phase1c_run.py` / `results_phase1c.json` (the
honest control this result needs). Triggered by Fraser's structural hypothesis after Phase 1's
muted result: prior soft-EM wins in this codebase (`climate_cat_lab`, `cvar_gp_lab`,
`grid_reserve_lab`) came from (1) a recurring regime, not a one-time event, and (2)
cross-sectional pooling across many correlated units within a shared regime instance — Phase 1's
per-mode fits had neither. KW51's retrofit is genuinely one-time (ingredient 1 can't be added
back), but ingredient 2 can: all 5 well-identified modes are simultaneous observations of the same
single structure's same single transition, so a **joint** model sharing one regime-responsibility
trajectory across all 5 modes restores the missing cross-sectional leverage.

## Headline finding — pooling helps a lot; soft-EM's specific contribution on top is real but modest

**Phase 1b (joint soft-EM regime-mixture, one shared responsibility across all 5 modes):**
false-alarm rate on held-out-normal days **5.8%** (3/52), detection essentially immediate —
sustained onset **2019-05-21, six days after the true retrofit start (2019-05-15)**, vs. Phase 1's
best single-mode onset of 2019-06-25 (~40 days in). A dramatic improvement over every per-mode
result in `RESULTS_PHASE1.md`.

**Phase 1c (the honest control — a naive joint chi-squared statistic, summing the same five
per-mode z-scores from Phase 1's already-fit classical regression and vanilla GP, no soft-EM at
all):** false-alarm rate **11.5%** (6/52, the calibration target), detection onset **also
2019-05-21** — the identical day — and an identical 99.6% flag rate during+post.

**The honest conclusion, sharpened exactly the way Fraser asked for:** the dramatic detection-speed
and flag-rate improvement from Phase 1 to Phase 1b came almost entirely from **cross-sectional
pooling across modes** — a general multivariate-monitoring principle (combine several correlated
signals about the same shared event) that a plain sum-of-squared-z-scores captures just as well as
a soft-EM mixture does, with no mixture model needed at all. Soft-EM's own, specific contribution,
isolated by this control, is real but modest: **roughly half the false-alarm rate** (5.8% vs.
11.5%) at matched detection speed and completeness — plausibly because a likelihood-ratio-based
responsibility can represent "these five residuals are jointly, habitually elevated together in a
way consistent with a genuinely different state" more precisely than an undifferentiated
sum-of-squares can, but this is a calibration refinement, not a detection-speed or
detection-completeness advantage, and the sample (52 held-out days, a 3-vs-6-flag difference) is
too small to call the false-alarm gap statistically decisive on its own.

## Why this matters — sharpens exactly when to reach for soft-EM in this codebase's own terms

This refines, rather than overturns, the four-lab family's own established pattern:

- **`climate_cat_lab`/`cvar_gp_lab`/`grid_reserve_lab`'s wins came from BOTH a recurring regime AND
  cross-sectional pooling, and this lab could not tell which ingredient did the work because it had
  both at once.** `shm_lab`'s Phase 1/1b/1c sequence is the first place in this codebase's own
  history that **separates the two ingredients** and finds: pooling is necessary and does most of
  the work; a recurring regime was never actually required for soft-EM's calibration edge to show
  up (Phase 1b's regime is a one-time event, and soft-EM still shows a real, if modest, benefit) —
  but a **non-mixture pooling baseline is a real, cheap, competitive alternative** whenever the
  detection question is really "did several correlated signals move together," not "is there a
  genuinely nonlinear or multi-modal residual distribution a simple statistic can't represent."
- **The honest, sharpened rule of thumb this lab now offers the rest of the codebase**: before
  reaching for a soft-EM regime-mixture, check whether a much simpler pooled/combined statistic
  across the same units already gets most of the benefit — `grid_reserve_lab`'s own real-data
  finding (soft-EM was a statistical tie on a ~50%-balanced real regime, a clear win only on a rare
  ~5% regime) was an early, unheeded version of this same caution. Soft-EM is worth its complexity
  when regimes are genuinely rare/imbalanced (giving a simple pooled statistic no natural
  threshold to separate on) or when the within-regime relationship is nonlinear/non-Gaussian enough
  that a likelihood-ratio test meaningfully beats a sum-of-squares — not merely whenever multiple
  correlated signals exist.

## Caveats

- This is one bridge, one real event, five modes, small samples (122 train / 52 held-out / 244
  during+post days) — a single data point on the "pooling vs. soft-EM" question, not a general
  theorem. `LAB_PLAN.md`'s standing caveat about generalizing beyond this one real intervention
  applies here too.
- The false-alarm-rate gap (5.8% vs. 11.5%) should be treated as suggestive, not conclusive, given
  it amounts to 3 vs. 6 flagged days out of 52.
- Reminder, per `LAB_PLAN.md`'s disclaimer: none of this is a claim about KW51's real structural
  safety, and none of it says soft-EM regime-mixture methods are broadly weak for SHM — it is a
  narrow, honestly-reported finding about which ingredient (pooling vs. mixture modeling) did the
  work in this one specific setup.

## Next

Fraser's call: with a real, if modest and now precisely-characterized, soft-EM contribution in
hand — and a sharper, transferable lesson about when the mechanism is and isn't worth its
complexity — is this enough to proceed to Phase 2 (the FastAPI app), presenting the pooling result
as the headline and the soft-EM refinement honestly as a secondary, modest effect? Or is there
further Phase 1 investigation worth doing first (e.g., a bilinear-mean-function regime per Z-24's
documented shape, or testing whether the false-alarm gap holds up with a larger held-out sample)?
