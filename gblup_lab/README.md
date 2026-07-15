# GBLUP Lab

Genomic prediction lab for `gp_engine` — fitted-hyperparameter, nonlinear-kernel
Gaussian process regression applied to real plant-breeding data, benchmarked
against both a sibling hand-built engine (MPDOK) and the published literature.
Full plan and rationale: `LAB_PLAN.md`. Detailed phase-by-phase results:
`RESULTS_PHASE0.md` through `RESULTS_PHASE4.md`. This file is the overview.

## Where this comes from: MPDOK

Everything in this lab starts from **MPDOK** (Mixed-Precision Dense-Operator
Krylov solver — our hand-built CUDA Fortran/CuPy GMRES-IR/LU-IR engine. MPDOK's `gblup/` lab had
already done the hard, genuinely novel part: proving that *exact* genomic
BLUP — a full N×N dense solve — beats the livestock/crop breeding industry's
standard APY approximation (Misztal et al.'s Algorithm for Proven and
Young), on real wheat, mice, and maize genotype data, with a real economic
argument (an 85.6% collapse in selection intensity at the elite tail that
whole-population accuracy metrics hide). That work stands on its own and
this lab doesn't repeat it.

What MPDOK's `gblup/` doesn't do is exactly what `gp_engine` is *for*:
hyperparameters (λ, kernel shape) fit by principled marginal-likelihood
optimization instead of a CV grid search, nonlinear/RKHS kernels instead of
a single fixed linear GRM, and calibrated predictive uncertainty (NLL) as a
first-class output, not just a point prediction. This lab is that missing
half, applied to MPDOK's own datasets, reading them in place — no files in
`MPDOK/gblup/` were touched.

Using two independently-built engines on the same data turned out to be
useful in exactly the way the same pattern was useful for `gp_lab` (Python
vs. CUDA Fortran backends) and for earlier Rust/Python/Fortran duplicate
paths: **Phase 0 caught a real, otherwise invisible bug** — MPDOK's own
`README.md` reports wheat/mice accuracy numbers that don't match what
MPDOK's own current code actually produces. That was only found by
reproducing MPDOK's exact linear solve inside gp_engine and cross-checking
both against a plain numpy reference. Cross-engine reproduction is not just
about GPU performance — it's a code-review process free of charge.

## What's actually new to gp_engine here

- `gp_core.py` gained `PrecomputedKernel`: takes any externally-built dense
  N×N SPD matrix (a GRM, a marker-space RBF/Matérn kernel) and runs it
  through the existing mixed-precision Cholesky+IR solver unchanged. The
  register-resident coordinate kernel (`Kernel`, `d ≤ ~32`) can't touch
  marker data (d = 1,279 to 48,580 across the datasets used here); this can.
- `gblup_hyperopt.py`: Nelder-Mead marginal-likelihood fit over
  (sigma_f, sigma_n) for a linear kernel, and over (ell, sigma_f, sigma_n)
  for RKHS — same NM-over-log-hyperparameters shape as `gp_hyperopt.py`,
  adapted for precomputed matrices.
- `marker_kernel.py`: the GEMM-trick squared-distance builder MPDOK already
  uses in `rbf_kernel.py`/`kriging_kernel.py`, reused here so the distance
  matrix is built once per fold and every hyperopt eval only pays for the
  cheap elementwise kernel transform.

## Results at a glance

| phase | question | headline result |
|---|---|---|
| **0** — parity | Does gp_engine's solver reproduce MPDOK's linear GBLUP? | Yes, to 1e-10–1e-14 relative error, and matches MPDOK's *live* code to float precision. Also found MPDOK's `README.md` numbers are stale vs. its own current code — verified, not assumed (`RESULTS_PHASE0.md`). |
| **1** — MLE vs. CV-grid | Does marginal-likelihood hyperparameter fitting hold up against MPDOK's CV-grid search? | Within 0.002–0.016 r without ever seeing the validation fold — validates the LML objective. First NLL numbers this lab family has had for genomic prediction. Found and explained a real FP32 calibration failure (wheat/E3, 46/120 zero-variance points) (`RESULTS_PHASE1.md`). |
| **2** — RKHS kernel | Does gp_engine's actual value-add (nonlinear kernels) help? | r up +0.09 to +0.27 over the linear GRM; wheat/E3's calibration failure fully resolved. Checked the magnitude against the primary literature (de los Campos et al. 2010, same 599-line wheat panel) rather than trusting it — genuine RKHS gain is +0.05 to +0.09 r once compared to the right baseline, matching the literature to within ~0.01–0.04 (`RESULTS_PHASE2.md`). |
| **3** — G2F hybrids, same-era | Does it scale to real maize breeding data (d=48,580 markers)? | Built a parental→hybrid GRM (4,979 hybrids). Found and fixed a genuine FP32-envelope failure (unnormalized linear kernel → 4,979/4,979 pathological predictions); fixed, r=0.733 linear vs. 0.775–0.777 RKHS, consistent with Phase 2's literature-verified range (`RESULTS_PHASE3.md`). |
| **4** — the real 2024 season | How does it do on a genuinely held-out future season, real competition data? | Fetched the actual G2F 2024 test set from CyVerse (after Phases 0–3 were already written). Linear r=0.271, RBF r=0.408, Matérn r=0.415 — a real accuracy drop from Phase 3, exactly as expected under real distribution shift with no weather/soil covariates. Not leaderboard-compared (marker-only vs. multi-covariate entries isn't a fair fight) (`RESULTS_PHASE4.md`). |

## The throughline

Every phase followed the same discipline, and it paid off every time:
run the comparison, then **check the surprising number before believing
it** — against a second engine (Phase 0), against a primary paper read
directly rather than recalled (Phase 2), against a coverage/overlap check
before claiming a dataset means what it looks like it means (Phase 3's
FP32 collapse, Phase 4's genotype-panel coverage). Two of the five phases
turned up a real bug or a real stale-documentation problem that a clean
exit code would have hidden. That's the actual case for building the same
GP prediction twice, in two different engines, on the same data — not GPU
speed, verification.

## Final thoughts

1. MPDOK wasn't accuracy-wrong — it was documentation-stale. Phase 0's finding (README claims r≈0.45–0.55, live code gives 0.37–0.45) wasn't a bug in MPDOK's computation. The actual cv_lambda_sweep code is correct; someone just never re-ran the README after the code or data changed. gp_engine's solver matched that live code to float precision — it didn't improve on it, it verified it.

2. On MPDOK's own model (linear GRM, same data), gp_engine didn't beat it. Phase 1 showed marginal-likelihood fitting comes within 0.002–0.016 r of MPDOK's CV-grid search — close, sometimes fractionally behind. That's expected: CV-grid tunes directly against the reported metric, so it has a built-in edge. If you only care about "same linear model, whose optimizer is better," the answer is roughly a wash, slightly in MPDOK's favor.

3. The real accuracy gain came from a capability MPDOK never had at all: nonlinear (RKHS) kernels. MPDOK's gblup.py only ever fits a fixed linear VanRaden GRM — there's no kernel-shape option in it. gp_engine's RKHS path added genuine predictive accuracy on top of the best linear model in every single comparison in this lab: +0.05 to +0.09 r on wheat (verified against de los Campos et al. 2010's own numbers on the same panel — not just measured, checked), +0.042–0.044 r on the G2F hybrid panel, and +0.14 r on the real 2024 season. That's not a bug fix or a re-verification — it's new predictive power from a model class MPDOK structurally couldn't express.

One more thread worth naming separately: the Phase 3 FP32 collapse (4,979/4,979 pathological points) wasn't an MPDOK bug either — it was a bug in gp_engine's own new code, introduced while extending into territory MPDOK never went (an unnormalized linear kernel at d=48,580). We found and fixed our own mistake there, not MPDOK's.

So: MPDOK's accuracy was fine as-is; its documentation drifted. gp_engine matched MPDOK on MPDOK's own turf, made a mistake and fixed it while pushing into new territory, and then delivered real, literature-verified accuracy gains specifically where it did something MPDOK never attempted.

## Reproducing

```
cd gblup_lab
/var/home/fraser/miniconda3/envs/py314/bin/python run_phase0.py   # parity
/var/home/fraser/miniconda3/envs/py314/bin/python run_phase1.py   # MLE vs CV-grid
/var/home/fraser/miniconda3/envs/py314/bin/python run_phase2.py   # RKHS kernel
/var/home/fraser/miniconda3/envs/py314/bin/python run_phase3.py   # G2F hybrids, same-era CV
/var/home/fraser/miniconda3/envs/py314/bin/python run_phase4.py   # real 2024 held-out season
```

Phases 0–3 read data from `MPDOK/gblup/data/` in place (no copying). Phase 4
reads from `gblup_lab/data/` (fetched separately from CyVerse, DOI
`10.25739/78mn-4394` — see `RESULTS_PHASE4.md` for exact source URLs).
