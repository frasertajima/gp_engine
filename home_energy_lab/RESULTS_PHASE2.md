# Phase 2 — sequential-VoI skip/probe/drill dispatch layer

**Status: DONE (2026-08-04).** Fifth application of the same sequential-VoI mechanism this codebase
has now built five times (`grid_reserve_lab`'s Phase 4, `shm_lab`'s Phase 2, `hydro_reserve_lab`'s
Phase 2, `climate_cat_lab`'s Phase 3, now this lab).

**Headline: GPC's calibrated mean robustly beats SVM — posterior variance adds nothing on top,
across the entire cost-ratio range tested.** A clean, unambiguous null result for the
variance-specific mechanism, closest in shape to `shm_lab`'s own finding, on a genuinely different
kind of problem (a personal-scale, real-data dispatch decision, not a classification-only lab).

## Method

**State**: a real, data-derived label — is today a "high-demand day" (net load in the top 25% of
the real 2017-2025 record, the same real-quantile-threshold convention `hydro_reserve_lab`'s
drought label used). **Actions**: skip = rely on Phase 1's own winning Method 2 (plain GP forecast)
target only; probe = pay a small cost for an updated short-horizon read before committing; drill =
commit immediately to a full protective pre-charge.

**The new modeling piece** (the sixth lab in this family to need one): neither Phase 1's GP1D
forecast nor its GaussianMixture regime layer produce a native `(mean, var, prob)` triple.
`stress_classifier.py` builds a real `LaplaceBinaryGPC` fit (unchanged) on two already-computed,
real, day-ahead-available features — yesterday's net load and yesterday's mean temperature —
against the real high-demand label. Checked empirically before trusting anything downstream: **val
AP≈0.798, test AP≈0.82, genuine posterior variance range 0.014-0.66** — neither `shm_lab`'s
near-total separability nor an unworkably hard problem, a healthy middle case.

**Economics — the best-sourced of any VoI lab in this family, needing zero new research**:
`delta_kwh` (13.5, capped at the real battery capacity) is this lab's own real mean net-load gap
between high-demand and normal days; `c_drill`/`v_drill_gross` follow directly from BC Hydro's real
off-peak/peak effective rates (`rate_model.py`, already used and self-test-verified in Phase 1 to
the cent against a real bill). Only `c_probe` ($0.15, illustrative cost of an updated forecast read)
is unsourced — the one constant every VoI lab in this family has needed to flag this way.

**Bootstrap convention**: one fixed real dataset (3,286 days, 2017-2025) — 200 seeds each redraw a
fresh stratified train/val/test split, mirroring `shm_lab`/`hydro_reserve_lab`'s convention.

## Result: 200 seeds, derived economics (breakeven P(high-demand)=0.3738)

| condition | realized $ | vs. SVM |
|---|---|---|
| SVM | $162.44 ± $9.35 | — |
| GPC-mean-only | $168.40 ± $8.78 | +$5.96 [$4.98, $6.92] |
| **GPC-full-posterior** | **$168.39 ± $8.77** | **+$5.94 [$4.96, $6.90]** |

GPC-full − GPC-mean: **−$0.018 [−$0.087, $0.052]** — statistically indistinguishable from zero.
Probe niche fraction (gpc_full): **0.0000 across all 200 seeds** — Probe is essentially never worth
considering at this breakeven, mirroring Phase 1's own real-data-driven finding that the regime/
variance-aware layer doesn't earn its keep here.

## Result: breakeven-probability sweep (200 seeds)

| breakeven P(high-demand) | SVM | GPC-mean | GPC-full | full−SVM | full−mean |
|---|---|---|---|---|---|
| 0.050 | $2,586.82 | $2,925.64 | $2,925.19 | +$338.38 [331.35,345.39] | −$0.44 [−1.27,0.43] |
| 0.100 | $1,261.85 | $1,304.67 | $1,304.39 | +$42.54 [38.71,46.35] | −$0.28 [−0.60,0.06] |
| 0.150 | $745.99 | $770.51 | $770.08 | +$24.09 [21.70,26.48] | **−$0.43 [−0.66,−0.20]** |
| 0.200 | $496.62 | $510.91 | $510.83 | +$14.20 [12.15,16.26] | −$0.08 [−0.25,0.10] |
| 0.250 (real base rate) | $351.12 | $361.77 | $361.70 | +$10.57 [8.79,12.34] | −$0.07 [−0.20,0.06] |
| 0.300 | $254.68 | $264.22 | $264.27 | +$9.59 [8.21,10.98] | +$0.05 [−0.07,0.17] |
| 0.374 (derived value) | $162.48 | $168.42 | $168.41 | +$5.93 [4.94,6.89] | −$0.02 [−0.09,0.06] |
| 0.450 | $104.43 | $106.40 | $106.41 | +$1.97 [1.32,2.64] | +$0.00 [−0.03,0.03] |
| 0.550 | $56.20 | $53.82 | $53.83 | **−$2.36 [−2.85,−1.89]** | +$0.01 [−0.02,0.04] |
| 0.650 | $25.37 | $23.38 | $23.42 | **−$1.95 [−2.37,−1.55]** | +$0.04 [−0.01,0.08] |
| 0.750 | $6.22 | $7.77 | $7.76 | +$1.53 [1.11,1.94] | −$0.02 [−0.07,0.04] |
| 0.900 | −$0.19 | $0.13 | $0.13 | +$0.32 [0.20,0.45] | −$0.01 [−0.03,0.02] |

**GPC-full vs. GPC-mean stays at essentially zero across the entire grid** — the largest deviation
(breakeven=0.15) is −$0.43, tiny in absolute terms and not economically meaningful even where the
CI technically excludes zero. **GPC-mean vs. SVM is real and mostly positive, but not
uniform**: it flips negative at breakeven 0.55-0.65 before returning positive at the extremes — a
real, non-monotonic pattern, reported as observed rather than smoothed into a single story.

## Mechanism, checked directly, not guessed

**Why variance adds nothing here**: the classifier's own posterior variance is real (0.014-0.66,
confirmed above) and yet the niche fraction is essentially zero — the Skip/Drill economics at this
lab's derived breakeven are decisive enough from the mean alone that resolving the residual
uncertainty via Probe rarely changes the optimal action. This differs from `shm_lab`'s reason for
the same null outcome (there, the classifier was too separable to leave any ambiguity at all); here,
real ambiguity exists (AP≈0.82) but the payoff structure doesn't reward resolving it — the same
"check separability AND the decision structure separately" lesson `VOI_DISPATCH_PATTERN.md`'s point
6 already flagged, now confirmed as a *second*, distinct route to the same null result.

**Why GPC-mean beats SVM broadly, but not uniformly**: consistent with the pattern already
established across this family (MacKay moment-matching calibration differences between GPC and
SVM), but the sign flip at moderate-high breakeven (0.55-0.65) is a real, unexplained wrinkle in
this specific dataset — flagged honestly rather than forced into a single clean narrative.

## Answering "does the sequential-VoI mechanism earn its keep here"

**No — a clean null result for posterior variance specifically**, the sixth and clearest
confirmation that this mechanism is genuinely niche: it requires *both* real classification
ambiguity *and* a decision structure where resolving that ambiguity changes the optimal action, and
this lab's real economics (however well-sourced) don't create the second condition. The calibrated
mean *is* a real, usable win over SVM — consistent with Phase 1's own finding that the plain GP
already does the job well, and Method 3's regime-mixture margin didn't help there either. Two
independent layers of this lab (Phase 1's regime-mixture, Phase 2's VoI variance) now agree: for
*this* real dispatch problem, the plain forecast is doing essentially all of the useful work.

## Risks / honest unknowns

- **`c_probe` ($0.15) is illustrative, unsourced** — the qualitative finding (near-zero variance
  contribution) is unlikely to flip under a different value, given the niche fraction is exactly
  zero, but not swept here.
- **The high-demand label and the delta_kwh/rate economics inherit `rate_model.py`'s own documented
  simplifications** (the same-day 0-6 off-peak proxy, the unresolved 60-day tier-proration
  discrepancy noted in `research/04_vancouver_real_calibration_case.md`).
- **The GPC-mean-vs-SVM sign flip at breakeven 0.55-0.65 is reported, not explained** — a real
  pattern in this specific real dataset, not chased further this phase.
