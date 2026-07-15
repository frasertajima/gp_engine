# GBLUP Lab — Phase 3 results (G2F hybrid maize yield, stretch goal)

**Date:** 2026-07-14. **Goal (LAB_PLAN.md):** the headline stretch goal —
derive a parental→hybrid GRM and benchmark against the G2F 2024–2025 GxE
Prediction Competition data. New ground for both labs: MPDOK's `gblup/`
never used the real hybrid yield table, only the inbred panel with a
*simulated* phenotype (`README.md`: "Phenotype: Simulated with h²=0.50 ...
hybrid yield data is in a separate G2F repository"). `1_Training_Trait_Data
_2014_2023.csv` (also in `MPDOK/gblup/data/`) has the real thing.

## Checked before running anything: is this actually leaderboard-comparable?

**No — verified directly, not assumed, before building anything.** Read the
competition's own paper (Genomes to Fields 2024 maize genotype-by-environment
prediction competition, PMC12983533): training is 2014–2023 (what we have
locally, 173,960 plot records), but scoring is on a **held-out 2024 season**
— 1,063 hybrids across 23 *new* locations never seen in training, evaluated
by mean Pearson r across environments. `1_Training_Trait_Data_2014_2023.csv`
is exactly what its name says — no 2024 data in it. The paper notes the 2024
observations are "now included to allow post-competition model validation,"
meaning that set exists and could in principle be fetched separately — that's
a new-data-acquisition decision, not made in this pass (flagged for Fraser,
not done silently).

**What this lab does instead:** a random 5-fold CV over unique hybrid
*combinations* (parent1 × parent2 pairs, not full plot records) using only
the 2014–2023 data already on disk. This tests "known parents, unseen
combination" — a materially easier task than the competition's "known
hybrids, unseen year/location." **These numbers are not comparable to any
competition leaderboard entry and are not reported as such anywhere below.**

## Data construction

`g2f_hybrid.py`: filtered `1_Training_Trait_Data_2014_2023.csv` to the
161,534 rows with both parents in the genotyped panel (`g2f.npz`, N=2,193
inbreds, d=48,580 markers) and non-null yield; aggregated to one row per
unique hybrid combination (mean yield across all its plot records, any
year/environment — a real simplification, no environment/year effect
modeled) — **4,979 unique hybrids**, median 22 records averaged per hybrid
(range 1–832). Hybrid marker dosage: standard additive approximation
(Bernardo 1994; the two-kernel GCA form in Technow et al. 2014 is
equivalent) — `X_hybrid = (X_parent1 + X_parent2) / 2`, the expected gamete
dosage under random assortment, no dominance term.

## A real engine-envelope finding, caught before trusting the first result

First run of the from-`X` linear kernel gave **4,979/4,979 pathological
points — every single held-out prediction, every fold, total collapse** (not
subtle — same failure mode as wheat/E3's fold, but complete rather than
partial). Diagnosed directly: the raw, unnormalized `X_hybrid @ X_hybridᵀ`
kernel has diagonal ≈12,000 at d=48,580 markers (vs. wheat's published `A`
or mice's `A`, both diag ≈1–2 — properly VanRaden-normalized). `gp_core.py`'s
FP32 factor path has a documented ~1e-6-**absolute** variance floor
(`gp_predict` docstring) — at kernel magnitude ~12,000, that absolute floor
swamps genuine (small, meaningful) variances for essentially every point.
This isn't a bug in `gp_core.py` or a defect specific to Phase 3 — it's the
same FP32 envelope Phase 1 already documented, just hit far harder because
nothing in `marker_kernel.py`'s from-`X` linear-kernel path normalizes scale
the way MPDOK's `gblup.py`/VanRaden GRM (or `marker_kernel.apply_kernel`'s
bounded-[0,1] RBF/Matérn kernels) already do.

**Fix:** rescale the from-`X` linear kernel to unit mean-diagonal before
fitting (`run_phase3.py::cv_linear`) — the same normalization convention
VanRaden's GRM and the wheat/mice `A` matrices already use. This is a
correction to a missing normalization step, not a numerical cover-up.
Pathological points dropped from 4,979 to **2** (out of 4,979 — negligible,
plausibly near-identical parent pairs). As a side effect, r also improved
substantially (0.658→0.733) — the unnormalized kernel wasn't just violating
the FP32 envelope, it was also giving the Nelder-Mead hyperopt a badly
conditioned search space (the true `sigma_f2` needed to be ~1e-4 with an
`ystd≈1`-based starting heuristic tuned for O(1)-scale kernels).

**Lesson for future gblup_lab / marker-kernel work:** any from-`X`
marker kernel fed through `gp_core.py`'s mixed-precision path needs an
explicit unit-scale normalization step first — RKHS kernels get this for
free (bounded in [0,1] by construction); linear (inner-product) kernels do
not, and the failure mode at large d is silent-until-checked (a clean exit
code, `converged=True`, just a useless model).

## Results (5-fold CV, hybrid-combination holdout, 2014–2023 data only)

| model | r | NLL (median) | pathological pts | ell |
|---|---|---|---|---|
| linear (from-X, normalized) | 0.7330 | 0.711 | 2 | — |
| RBF | 0.7753 | 0.621 | 0 | 109.8 |
| Matérn-3/2 | 0.7773 | 0.619 | 0 | 163.1 |

RKHS gain over linear: **+0.042 to +0.044 r** — squarely inside the
0.01–0.09 r range Phase 2's literature check (de los Campos et al. 2010,
same-style comparison on the wheat panel) found for genuine RKHS-over-linear
gains. Same story as Phase 2, now confirmed at a third, much larger-d
dataset: gp_engine's RKHS capability adds a real, modest, literature-
consistent improvement over a linear kernel — not the inflated
GRM-pipeline-artifact-sized gap Phase 2 originally (and mistakenly) reported
before checking.

## Scale note

d=48,580 markers is ~38× wheat's 1,279 and ~4.7× mice's 10,346 — the first
real stress test of the engine-gap fix (`PrecomputedKernel` +
`marker_kernel.py`'s GEMM-trick distance builder) at meaningful width, and
it worked cleanly once the normalization issue above was fixed. N=4,979
hybrids is modest (well within VRAM, no OOC needed) — the real Phase-3-scale
opportunity (161k+ plot-level records, or the full 2024 competition test)
remains open, per the leaderboard-comparability note above.

## Verdict

Engine capability (precomputed marker kernels at real width) confirmed
working at scale. Found and fixed a genuine, previously-undocumented
numerical-envelope trap (unnormalized high-d linear kernels), consistent
with — not contradicting — `gp_core.py`'s existing FP32-envelope
documentation. RKHS-over-linear result is modest and literature-consistent,
matching Phase 2's now-verified pattern. **Not compared to any competition
leaderboard** — that would require the 2024 held-out season data, which
is not local and has not been fetched.
