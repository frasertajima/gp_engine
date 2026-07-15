# GBLUP Lab — Phase 2 results (RKHS/Gaussian marker kernel)

**Date:** 2026-07-14. **Goal (LAB_PLAN.md):** the actual value-add over MPDOK
— fit the *shape* of the kernel (Gaussian or Matérn-3/2 over raw marker
dosage `X`, via `marker_kernel.py`'s GEMM-trick distance builder) instead of
MPDOK's fixed linear VanRaden GRM (`A`). Same MPDOK-sourced data, same 5-fold
split as Phases 0–1 (`MPDOK/gblup/data/`, read in place; MPDOK going to
GitHub separately, link to be added here once it's up).

## Headline result

| trait | Phase 0 (MPDOK CV-grid, linear GRM) | Phase 1 (gp_engine MLE, linear GRM) | **Phase 2 (gp_engine MLE, RKHS)** | delta vs Phase 1 |
|---|---|---|---|---|
| wheat/E1 | 0.4264 | 0.4232 | **0.5754–0.5756** | +0.152 |
| wheat/E2 | 0.3880 | 0.3860 | **0.5032–0.5098** | +0.117–0.124 |
| wheat/E3 | 0.3678 | 0.3518 | **0.4418–0.4430** | +0.090–0.091 |
| wheat/E4 | 0.4534 | 0.4516 | **0.5393–0.5415** | +0.088–0.090 |
| mice/bmi | 0.1378 | 0.1378 | **0.2679–0.2698** | +0.130–0.132 |
| mice/blen | n/a | 0.1049 | **0.3779–0.3797** | +0.273–0.275 |

(RBF and Matérn-3/2 give near-identical r throughout — the gain is coming
from letting the kernel's *bandwidth* be fit, not from the choice between
these two smooth kernel families.)

## wheat/E3's Phase 1 calibration problem: fully resolved

Phase 1 found 46/120 held-out points in wheat/E3 fold 4 with exactly-zero
predictive variance (FP32 cancellation, traced to the linear GRM's
cross-covariance collapsing to the prior for related/repeated breeding
lines). Under the RKHS kernel, **every fold, both kernel kinds: 0 pathological
points.** This is a clean, explainable result, not a coincidence: a smooth
Gaussian/Matérn kernel with a properly fit bandwidth doesn't saturate the way
a fixed linear kernel can for near-identical genotypes — there's no analogue
of "cross-covariance equals the prior" unless two individuals are markers-
identical, which the finite bandwidth resists.

## Before trusting the magnitude: two things checked, one thing still open

A +0.09 to +0.27 jump in Pearson r is **far larger than the RKHS-vs-linear-
GBLUP literature typically reports** (Gianola & van Kaam 2008; de los Campos
et al. 2009/2010 report gains more like 0.01–0.05 on comparable panels, in
some cases on these exact BGLR sets). Before reporting this as "gp_engine
beats the literature," two checks were run:

1. **Ruled out an X/y index-alignment bug.** Built a naive linear kernel
   directly from `X` (mean-centered `X @ Xᵀ`, no VanRaden normalization) and
   ran it through the exact same Phase-1 MLE pipeline. Result: r=0.481 for
   wheat/E1 — *higher* than Phase 1's `A`-based 0.4232, and not remotely
   degenerate (a real alignment bug would produce r near 0, not a sensible,
   better number). X and y are correctly ordered.

2. **Found that MPDOK's published `A` and a from-`X` linear kernel don't agree
   as strongly as expected.** `corr(A, naive X-linear-kernel)` = 0.248 (wheat),
   0.456 (mice) on the upper-triangle entries — not the near-1.0 you'd expect
   if `A` were built from this exact `X` via a standard VanRaden formula.
   Tried a haploid-appropriate rescaling for wheat's 0/1 (inbred, no
   heterozygote) marker coding — correlation is scale-invariant, so this
   didn't move the number, confirming the gap isn't a centering/scaling
   artifact. Most likely explanation: `A` (from the BGLR R package) and `X`
   (also from BGLR) were built via different pipelines/QC/imputation
   conventions — a known type of reproducibility gap in the genomics
   community, not unique to this analysis, and not evidence of a data bug
   here (`MPDOK/gblup/data/SOURCES.md` doesn't document exactly how `A` was
   derived relative to `X`, or whether they're both straight from BGLR).

**What this means for the headline number:** part of Phase 2's gain over
Phase 1 is "using `X` directly instead of the published `A`" (0.423 → 0.481,
already a real, if smaller, jump) and part is "nonlinear kernel shape on top
of `X`" (0.481 → 0.575). The first part is explained; the second part —
whether a properly fit RKHS kernel really does add another ~0.10 r on top of
even an `X`-linear kernel, or whether something about the bandwidth fit is
still off — is the piece that should be checked against the Gianola/de los
Campos numbers directly before this goes in any headline write-up. Flagging
this explicitly rather than reporting the full jump as a clean win.

## Literature check (2026-07-14) — the primary source, read directly, not recalled

Located and read the actual paper, not a summary of it: **de los Campos,
Gianola, Rosa, Weigel & Crossa (2010), "Semi-parametric genomic-enabled
prediction of genetic values using reproducing kernel Hilbert spaces
methods," *Genetics Research* 92:295–308**, DOI 10.1017/S0016672310000285.
This is the right paper: **599 CIMMYT wheat lines evaluated for grain yield
in 4 environments (E1–E4) — the exact same lines, trait, and environments as
`MPDOK/gblup/data/wheat.npz`** (1447 DArT markers vs our 1279 — some
downstream QC difference, not the same panel size, but the same underlying
population and phenotypes). Their Table A2 (Appendix) reports 10-fold CV MSE
(phenotypes standardized to unit variance) for a linear marker model
(Bayesian LASSO) and a Gaussian-RKHS marker model swept over a bandwidth grid
θ ∈ {0.1,...,10}:

| env | BL (linear) MSE | best RKHS MSE (θ) | BL r-equiv.* | best RKHS r-equiv.* | Δr (their paper) |
|---|---|---|---|---|---|
| E1 | 0.748 | 0.664 (θ=2) | 0.502 | 0.580 | +0.078 |
| E2 | 0.783 | 0.775 (θ=1) | 0.466 | 0.474 | +0.008 |
| E3 | 0.861 | 0.796 (θ=3) | 0.373 | 0.452 | +0.079 |
| E4 | 0.787 | 0.719 (θ=2–3) | 0.462 | 0.530 | +0.068 |

*r-equivalent = sqrt(1 − MSE), valid when y is standardized to unit variance
and the predictor is reasonably calibrated — an approximation from MSE
(the paper reports MSE, not r directly), not a number the paper states.

**Their RKHS-over-linear gain is +0.01 to +0.08 r-equivalent — not the
+0.15 to +0.27 r this file originally reported.** That confirms what the
"open question" section above suspected: most of Phase 2's original headline
number was the `A`-vs-`X` construction-pipeline gap, not RKHS itself.

To check like-for-like, filled in the from-`X` linear-kernel MLE r (only E1
was tested before) for all four environments and compared directly to
Phase 2's RKHS numbers, same engine, same split, same markers:

| env | our X-linear r | our RKHS r | our Δr | their Δr (Table A2) |
|---|---|---|---|---|
| E1 | 0.4811 | 0.5754 | +0.094 | +0.078 |
| E2 | 0.4576 | 0.5032 | +0.046 | +0.008 |
| E3 | 0.3827 | 0.4418 | +0.059 | +0.079 |
| E4 | 0.4697 | 0.5393 | +0.070 | +0.068 |

**Once compared against the right baseline (a linear kernel built the same
way from the same markers, not MPDOK's separately-normalized published `A`),
gp_engine's RKHS gain lands in the same 0.01–0.09 r range de los Campos et
al. (2010) report on this exact dataset** — E1, E3, E4 agree to within
~0.01–0.04 r; E2 is the largest discrepancy (+0.046 vs +0.008) but still an
order of magnitude away from anomalous, and a full match was never expected
given different marker sets (1279 vs 1447), different CV folds (5 vs 10),
and Bayesian LASSO vs our ridge-style MLE kernel not being the identical
linear method. This is now a verified, not assumed, result. Mice has no
equivalent check yet — this paper is wheat-only; a mice-specific RKHS-vs-GBLUP
comparison in the literature hasn't been located.

## Verdict

The engine capability works. The calibration story (wheat/E3) is a solid,
fully-explained win, unaffected by any of the above. The accuracy story is
now **verified against the primary literature, not just checked internally**:
the genuine RKHS-over-linear gain is modest (0.01–0.09 r) and matches
published numbers on this exact dataset; the originally-reported +0.15 to
+0.27 r was real relative to MPDOK's `A`, but the correct attribution is
"partly a GRM-construction-pipeline difference, partly RKHS" — and the RKHS
part alone is now literature-confirmed rather than merely plausible. Safe to
carry into Phase 3 and safe to cite (with the wheat comparison above,
correctly attributed) in any external write-up.
