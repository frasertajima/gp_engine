# GBLUP Lab — exact, fitted-hyperparameter genomic prediction

**Status:** Phases 0–3 DONE 2026-07-14, **Phase 4 DONE 2026-07-15** — see
`RESULTS_PHASE0.md` through `RESULTS_PHASE4.md`. Sibling to `../gp_lab/`.
MPDOK data used in Phases 0–3 (`MPDOK/gblup/`) — Fraser is publishing MPDOK
to GitHub separately, link to be added here once it's up. Phase 4's data
(the real 2024 G2F season) is separately sourced from CyVerse, downloaded
2026-07-15 — **after** Phases 0–3 were already written, at Fraser's explicit
request, specifically so the comparison would be genuinely held-out rather
than informed by anything already built.
**One line:** take MPDOK's already-working exact-vs-APY G-BLUP story and add the
one thing it's missing — gp_engine's marginal-likelihood-fit hyperparameters and
nonlinear (RKHS) kernels — then push it to a real, large-N, published-benchmark
dataset (the G2F maize hybrid yield competition) that neither lab has touched yet.

## Why this lab, and why it's not just re-running gp_lab

`MPDOK/gblup/` (see `gblup.py`, `README.md`) already proves the *scale* half of
this story extremely well: exact G-BLUP via GMRES-IR beats the industry-standard
APY approximation, with a genuinely novel finding (APY's ~85% collapse in
selection-tail intensity, hidden by whole-population Pearson r — the "Global
Metric Proxy Fallacy"). That lab is not something to redo.

What it doesn't do, and what gp_engine is *for*:
- **λ (noise/signal ratio) is fit by a 20-point CV grid sweep + a method-of-moments
  h² estimate** (`cv_lambda_sweep`, `estimate_h2_mom` in `gblup.py`), not by proper
  Type-II marginal-likelihood optimization. gp_engine's NM→L-BFGS-B hyperopt
  (`gp_hyperopt.py`) is a strictly more principled fit of the same quantity.
- **The kernel is fixed to the linear VanRaden GRM** (`G = ZZᵀ/scale`). The
  genomic-prediction literature has a whole line of work (Gianola & van Kaam 2008;
  de los Campos et al. 2009, 2010) comparing this to a **Gaussian/RKHS kernel**
  over the same marker data, generally finding a modest but real accuracy gain
  when the trait has non-additive (epistatic/dominance) architecture. gp_engine's
  whole reason to exist is fitted nonlinear kernels — this is the natural target.
- **No NLL / calibrated uncertainty.** Every number in the MPDOK lab is a point
  prediction + Pearson r. gp_engine's predictive variance path gives calibrated
  prediction intervals for free — directly useful for breeding decisions (a
  90%-CI on a breeding value is a different product than a point estimate).

## A real engine gap this lab will surface immediately

`gp_core.py`'s `Kernel._check_X` hard-caps `d <= _MAX_D` (~16–32) because the
fused CUDA kernel keeps each `x_i` row resident in GPU registers. That's fine
for spatial covariates (d=2–26 in gp_lab); it's **not usable as-is** for marker
data: wheat d=1,279, mice d=10,346, G2F d=48,580 SNPs. Trying to run these
through `Kernel.build()` will raise `ValueError` immediately, before any science.

The fix is not to widen the register-resident path further — it's the wrong
approach for d in the thousands. Use the **GEMM-trick distance formula**
(`||a-b||² = ||a||² + ||b||² - 2a·b`, one DGEMM, no N×N×D intermediate) that
MPDOK already has working code for in `kriging_kernel.py` / `rbf_kernel.py`, and
that `gblup.py` already uses for the linear GRM itself. Concretely:

- **New module, `gblup_lab/marker_kernel.py`**: build the N×N base matrix
  (linear GRM *or* squared-distance matrix for RBF/Matérn) via GEMM, for any d,
  reusing MPDOK's already-tested pattern rather than reinventing it.
- **New engine entry point**: a `gp_fit`/marginal-likelihood path that accepts a
  precomputed base matrix (distance² for nonlinear, or the GRM itself for
  linear) instead of raw `X` coordinates, and optimizes only the *scalar*
  hyperparameters (bandwidth for nonlinear, sigma_f², sigma_n²) against it —
  rebuilding the N×N matrix once per optimizer step is cheap (one GEMM), so this
  doesn't need the register-resident kernel at all. This is a small, well-scoped
  addition to `gp_hyperopt.py`/`gp_core.py`, not a rewrite.

This also means the existing OOC Cholesky+IR solver (`gp_ooc_solver.cuf`,
validated bit-identical to n=391,387) applies completely unchanged — it only
ever sees an N×N SPD matrix, it doesn't care how the matrix was built.

## Datasets — all local already, none need `/OWS`

| dataset | N | d (markers) | source | status |
|---|---|---|---|---|
| BGLR wheat | 599 | 1,279 | Crossa et al. 2010, *Genetics* 186(2):713–724 | `MPDOK/gblup/data/wheat.npz` — 4 grain-yield environments, published GRM included |
| BGLR mice | 1,814 | 10,346 | Valdar et al. 2006, *Nat Genet* 38(8):879–887 | `MPDOK/gblup/data/mice.npz` — BMI + body length, published GRM included |
| G2F maize inbreds | 2,193 | 48,580 | Genomes to Fields, CyVerse (PHG-imputed) | `MPDOK/gblup/data/g2f.npz` |
| **G2F hybrid yield** | **up to ~161,534 plot rows / 272 environments** | derived (parental GRM combination) | `MPDOK/gblup/data/1_Training_Trait_Data_2014_2023.csv` — the **2024–2025 G2F GxE Prediction Competition** dataset | not yet used by either lab |

The fourth row is the headline opportunity: it's real, large-N, phenotype data
tied to an actual public prediction competition (Nov 2024–Jan 2025) with a
published leaderboard to benchmark against — the closest thing in this whole
plan to a `3droad`-style "beat the field at real scale" result. It needs one
piece of data engineering neither lab has done yet: deriving a **hybrid** GRM
from the 2,193 genotyped **parents** (standard approach: Technow et al. 2014 /
Bernardo 1994 additive-hybrid GRM from parental marker data) to cover the
161k hybrid phenotype records, most of which are hybrids of two genotyped
parents rather than genotyped individuals themselves.

## Phased plan

**Phase 0 — parity, no new science. DONE, see `RESULTS_PHASE0.md`.** Loaded
wheat + mice via `MPDOK/gblup/data/` (read in place, no copying — `datasets.py`).
Added `PrecomputedKernel` to `gp_core.py` (the engine gap flagged above) and
reproduced MPDOK's linear-GRM CV-λ result through gp_engine's exact solver:
solver parity vs numpy `dgesv` at 1e-10–1e-14 relative error, and CV r matching
MPDOK's own live `cv_lambda_sweep` code to float precision on every trait
tested (wheat E1–E4, mice BMI). **Found MPDOK's README numbers are stale
relative to its own current code** (README claims wheat r≈0.45–0.55, mice
r=0.280; the actual function, run today, gives 0.37–0.45 and 0.138) — verified
this is a doc/code drift, not a gp_engine bug, by running MPDOK's real function
directly and ruling out fold-protocol and centering differences. The real
numbers to beat in Phase 1 are the live-code ones, not the README's.

**Phase 1 — MLE hyperparameter fit, linear kernel. DONE, see `RESULTS_PHASE1.md`.**
`gblup_hyperopt.py` (NM over log(sigma_f, sigma_n), training-fold-only LML,
mirrors `gp_hyperopt.py`'s pattern) + `run_phase1.py`. Verdict: MLE lands within
0.002–0.016 r of MPDOK's CV-grid on every wheat environment and ties mice/bmi
exactly (both methods independently converge to near-zero noise for that
trait) — expected, since CV-grid optimizes directly against the reported
metric and MLE never sees the validation fold; the near-agreement validates
the LML objective rather than "winning." First NLL numbers this lab family has
ever had for genomic prediction. **Found a real calibration issue**, not a bug:
wheat/E3 fold 4 gave 46/120 held-out points exactly zero predictive variance
(FP32 cancellation floor) with residuals up to 1.38 — traced to the wheat
panel's known related/repeated breeding lines pushing cross-covariance to the
prior. Carries into Phase 2 as an open question (does RKHS calibrate better
for the same individuals?), not resolved in Phase 1.

**Phase 2 — nonlinear/RKHS kernel, the actual value-add. DONE, see
`RESULTS_PHASE2.md`.** Added `marker_kernel.py` (GEMM-trick squared-distance
builder, reused across every hyperopt eval since only the elementwise
transform depends on the bandwidth) and `mle_fit_rkhs` in `gblup_hyperopt.py`.
Gaussian and Matérn-3/2 both fit; near-identical r to each other (the gain is
from fitting bandwidth, not kernel-family choice). **Results: r up +0.09 to
+0.27 over Phase 1's linear GRM across every trait tested, and wheat/E3's
Phase-1 calibration failure (46/120 zero-variance points) is fully resolved —
0 pathological points, every fold, both kernel kinds.** Verified this isn't an
X/y alignment bug (a naive from-X linear kernel already beats the published
`A`-based fit, non-degenerately). **Found published `A` and a from-`X` linear
kernel only correlate 0.25–0.46** (different BGLR construction/QC pipelines,
not a bug here — ruled out centering/scaling as the cause). **Literature check DONE (2026-07-14), see `RESULTS_PHASE2.md`.** Located and
read de los Campos, Gianola, Rosa, Weigel & Crossa (2010), *Genetics
Research* 92:295–308, directly — same 599 CIMMYT wheat lines, same 4
environments as our data (their Table A2, 10-fold CV MSE, linear-vs-Gaussian-
RKHS). Their RKHS-over-linear gain converts to +0.01–0.08 r-equivalent, not
the +0.15–0.27 r this lab originally reported. Filled in the from-`X`
linear-kernel comparison for all 4 wheat environments (was only checked for
E1 before): once compared like-for-like (RKHS vs a linear kernel built the
same way from the same markers, not MPDOK's separately-normalized `A`),
gp_engine's own gain is +0.046 to +0.094 r — same 0.01–0.09 order of
magnitude as the literature, agreeing to ~0.01–0.04 r on 3 of 4 environments.
**Verified, not assumed: the RKHS capability is real and its magnitude
matches the published record on this exact dataset.** Safe to cite externally
with correct attribution (part of the original headline number was the
`A`-vs-`X` pipeline gap, not RKHS). Mice has no literature check yet — the
paper found is wheat-only.

**Phase 3 (stretch) — G2F hybrid yield. DONE, see `RESULTS_PHASE3.md`.**
Built `g2f_hybrid.py` (parental→hybrid GRM via averaged-parent marker dosage,
Bernardo 1994-style additive approximation; 4,979 unique hybrid combinations
from the 161k-row yield table, both parents genotyped) and `run_phase3.py`.
**Checked the leaderboard-comparability question before running anything**
(this section's original open question): the real G2F competition scores on
a held-out **2024** season, not present in `1_Training_Trait_Data_2014_2023
.csv` — confirmed by reading the competition paper directly. Ran a random
hybrid-combination 5-fold CV on 2014–2023 data instead (an easier task,
explicitly not leaderboard-comparable, flagged throughout). **Found and fixed
a real engine-envelope issue**: the unnormalized from-X linear kernel at
d=48,580 (diag≈12,000) blew FP32's ~1e-6-absolute variance floor for
*every* held-out point (4,979/4,979 pathological) — fixed by unit-diagonal
normalization (same convention VanRaden's GRM already uses), dropping
pathological points to 2 and improving r 0.658→0.733 as a side effect
(better-conditioned hyperopt search space too). Final: linear r=0.733,
RBF r=0.775, Matérn r=0.777 — RKHS gain +0.042–0.044 r, inside Phase 2's
literature-verified 0.01–0.09 range. Engine capability confirmed at real
scale (d=48,580, ~38x wheat's width). Lab's stated phases are now complete;
literal leaderboard comparison remains open pending a decision to fetch the
2024 held-out season data (confirmed to exist, not fetched here).

**Phase 4 (2026-07-15) — the real 2024 season. DONE, see `RESULTS_PHASE4.md`.**
Fetched from CyVerse (DOI 10.25739/78mn-4394, found via WebDAV listing, not
guessed): the real 2024 ground-truth yield (`7_Testing_Observed_Values.csv`,
1,063 hybrids, 22 environments) and the competition's own hybrid genotype
panel (`5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt`, 5,899 hybrids
× 2,425 markers, additive dosage already at hybrid level — confirms Phase
3's parent-averaging approximation was mathematically correct). Trained on
2014–2023 (4,938 hybrids), predicted the true 2024 held-out season (1,063
hybrids) once, no peeking (MLE hyperparameters fit on 2014–2023 only).
Results: linear r=0.271, RBF r=0.408, Matérn r=0.415 — RKHS gain +0.137 to
+0.144 r, larger than Phase 2/3's literature-anchored range, flagged as
plausible (real distribution shift, a different regime than the
within-population comparison the literature figure covers) but **not
independently verified** — an open finding, not a headline claim. Explicitly
not leaderboard-compared: this is a marker-only model with no weather/soil/
GxE covariates, unlike real competitive entries. Accuracy dropping from
Phase 3's 0.73–0.78 (same-era random CV) to 0.27–0.41 (genuinely new season)
is the expected, honest signature of real distribution shift, not a
regression.

## Open question worth resolving before Phase 3

Is a competition leaderboard number actually comparable to a plain train/test
GBLUP fit, or does the competition score models on a different protocol
(held-out environments/years, ensemble submissions, etc.)? Needs a read of the
competition's own scoring rules before claiming a head-to-head beat — same
diligence as the `protocol="paper"` discovery in `gp_lab` (don't compare apples
to oranges on n or split before publishing a number).

## Non-goals for this lab

- Not touching MPDOK's existing `gblup/` files — new directory, new code, same
  data read in place.
- Not re-deriving the selection-intensity/Breeder's-Equation finding — that's
  already done and correct; if gp_engine's fitted kernels change tail behavior
  at all, that's a Phase 3+ follow-up, not required for this lab to ship value.
