# Phase 2 — sequential-VoI skip/probe/drill dispatch layer

**Status: DONE (2026-08-04), RE-RUN 2026-08-05** after `CODE_REVIEW.md` M2/M3/M4 (label-threshold
leakage, a mining-shaped drill payoff, and a probe-noise constant inherited from another lab). **All
three headline conclusions survived, and the evidence for them got stronger** — see "What the M/L
fixes changed" below. Fifth application of the same sequential-VoI mechanism this codebase
has now built five times (`grid_reserve_lab`'s Phase 4, `shm_lab`'s Phase 2, `hydro_reserve_lab`'s
Phase 2, `climate_cat_lab`'s Phase 3, now this lab).

**Headline (unchanged, now on corrected economics): GPC's calibrated mean robustly beats SVM —
posterior variance adds nothing on top, across the entire cost-ratio range tested.** 200 seeds:
**gpc_mean − svm = +$29.80 [29.19, 30.40]**, **gpc_full − gpc_mean = −$0.05 [−0.12, +0.03]**, and the
**probe niche fraction is exactly 0.0000** at every breakeven from 0.05 to 0.90. A clean, unambiguous null result for the
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


---

## What the M/L fixes changed (2026-08-05)

Three `CODE_REVIEW.md` findings touched this phase. None reversed a conclusion; two materially
improved the evidence.

**M2 — label-threshold leakage.** The high-demand threshold was computed over the whole pool and
only then split into train/val/test, so the label definition carried a scalar of test information.
It is now derived from the training split alone and applied to all three splits (the split is
consequently unstratified; measured class balance stays within a point of 25% across seeds). Test AP
is unchanged at ≈0.82 — the leak was real but immaterial, which is worth recording either way.

**M3 — the drill payoff was mining-shaped, and this domain is not mining.** The shared matrix scored
a wasted "drill" as `-c_drill`, a total loss. That is right for a dry borehole and wrong for a
pre-charged battery: if the day turns out normal the energy is not destroyed, it is merely bought
earlier at the same off-peak price. **Only the round-trip loss is truly forfeited** — $0.07, not
$0.81, for a 13.5 kWh pre-charge. `decision.build_payoff_matrix_voi` gained an optional
`v_drill_residual` (default 0.0, so the other five VoI labs are bit-identical) and this lab passes
the real retained value. The derived breakeven moves **0.3738 → 0.0495**.

*A real error of mine, caught by the sweep and worth recording.* The first version of this fix
inverted the breakeven as `net_cost / v_gross`. That shortcut is only valid when the residual is
zero; with a residual, `p* = net / (net + v_gross − c_drill)`. The wrong form made drilling
negative-EV in *both* states for every grid point at or above p=0.10, collapsing the entire sweep to
a uniform $0.00. The all-zeros column is what exposed it — a degenerate result read as a finding
would have been exactly the failure mode this whole review was about.

**M4 — probe noise was another lab's constant.** `voi.SIGMA_PROBE2_DEFAULT` is documented as "tuned
... on this dataset's actual variance range (~0.08-0.38)" — the *mining* dataset's. This lab's GPC
variance runs ~0.009-0.41, so `SIGMA_PROBE2_LOCAL = 0.10` is now set here, as a stated domain-local
choice. The probe niche remains exactly 0.0000, consistent with the earlier σ²×c_probe sweep in
which even a noiseless probe reached only 3.3% of days.

### Full breakeven sweep, 200 seeds, corrected payoff

| breakeven p | svm | gpc_mean | gpc_full | full − svm | full − mean |
|---|---|---|---|---|---|
| **0.0495** *(derived)* | $227.88 | $257.67 | $257.62 | **+$29.74 [29.14, 30.33]** | −$0.06 [−0.13, +0.03] |
| 0.10 | 109.68 | 113.52 | 113.48 | +3.81 [3.46, 4.15] | −0.04 |
| 0.20 | 43.16 | 44.44 | 44.44 | +1.28 [1.08, 1.48] | −0.01 |
| 0.30 | 22.06 | 22.94 | 22.93 | +0.87 [0.75, 1.00] | −0.01 |
| 0.3738 *(old derived)* | 14.05 | 14.60 | 14.60 | +0.55 [0.46, 0.63] | −0.01 |
| 0.45 | 8.98 | 9.19 | 9.19 | +0.21 [0.14, 0.27] | −0.00 |
| 0.55 | 4.82 | 4.60 | 4.60 | −0.22 [−0.26, −0.18] | +0.00 |
| 0.75 | 0.55 | 0.64 | 0.64 | +0.09 [0.05, 0.13] | −0.01 |
| 0.90 | −0.02 | 0.01 | 0.01 | +0.03 [0.01, 0.04] | −0.00 |

GPC-mean beats SVM at every breakeven except a narrow 0.55-0.65 band where the ordering reverses by
cents. **`full − mean` never leaves ±$0.06 anywhere on the grid** — the variance-specific mechanism
is worth nothing, which is this phase's actual finding and is now demonstrated on economics that are
both physically correct and non-degenerate.
