# Phase 2 Results — scaling to n=45,000 (2026-07-23)

**Setup:** `phase2_run.py`, single 25-year historical trial, n=45,000-property book (seed
0), past the in-core VRAM ceiling on every GPU tried this session — requires
`gp_ooc_fortran.py`/`gp_ooc_solver.so` for methods 3 and 4's spatial log-marginal-
likelihood evaluation. Target: 99.5% 1-year survival probability, scored against a
100,000-year oracle resample (seed 999) no fitted method ever sees. Oracle DGP and all
scenario generation use `rff_sampler.py`'s Random Fourier Features approximation (800
features; validated against exact Cholesky sampling at Phase 0's n=500 scale in
`phase2_rff_validation.py`) since exact dense Cholesky at n=45,000 is infeasible
(>16GB, O(n³)). All dollar figures are this synthetic book's annual total-loss capital.

**Ground truth:** the oracle's own 99.5% 1-year VaR, from 100,000 simulated years, is
**$893,334,043**.

## A note on how this run got here

This session's first attempt (on a 4GB-VRAM laptop) locked the machine — `phase2_run.py`'s
`SCENARIO_BATCH`/`OOC_RAM_BUDGET_GB` constants exist specifically because of that. This run
is a fresh resume on a desktop with an RTX 4060 (8GB VRAM, 46GB system RAM). Getting it
running here required rebuilding `gp_ooc_solver.so` from source (`make clean && make all`
in `gp_engine/`) — the laptop-compiled binary depended on a CUDA-Fortran library
(`libcufcublas.so`) not present in this machine's toolchain (nvfortran 26.1 / CUDA 13.1).
The rebuild targets `cc86,cc89`, which covers the 4060's Ada (cc 8.9) architecture. The
laptop-compiled `.so` files are kept as `gp_ooc_solver.so.thinkpad.bak` /
`gp_solver.so.thinkpad.bak` in `gp_engine/`.

## OOC solver benchmark (this session, 45,000 x 45,000, 22 panels)

| | Cholesky factor | IR-solve | Total per eval |
|---|---|---|---|
| Method 3 (25 historical years) | ~15.6-16.2s | ~93.4s | ~109s |
| Method 4, normal component (17 years) | ~15.6-15.7s | ~31.7-31.8s | ~47s |
| Method 4, systemic component (8 years) | ~15.6-15.7s | ~29.9s | ~45s |

Solve time scales with the number of historical years being IR-solved against the same
factored panel (method 3's 25 years vs. method 4's 8-17 per component), not with the
3-point sigma-scale sweep itself. All evals converged to `relres` in the 1e-6 to 1e-8
range. Total OOC wall time for the run: 3 evals x ~109s (method 3) + 3 evals x (~47s +
~45s) (method 4's two components) ≈ **~7.5 minutes** of GPU-bound factor+solve time, on
top of scenario generation and book construction. This is the concrete number behind
`gp_loss_model_large.py`'s framing: OOC makes *evaluating* the fitted model tractable at a
scale no in-core method on either GPU tried this session can reach at all, while a full
from-scratch search at this per-eval cost would take hours — hence the 3-point refinement
of a Phase-1-transferred starting point, not a full re-fit.

## Headline result

| Method | Required capital | Achieved survival | Target | Expected annual shortfall | Capital gap vs. truth |
|---|---|---|---|---|---|
| 1. Independence | $74,605,920 | 93.31% | 99.5% | $452,575,424/yr | **−$818,728,123** |
| 2. Flat correlation | $230,357,598 | 93.54% | 99.5% | $308,872,879/yr | **−$662,976,445** |
| 3. Vanilla spatial GP | $136,273,663 | 93.31% | 99.5% | $391,328,958/yr | **−$757,060,380** |
| 4. GP + regime-mixture | $166,259,656 | 93.33% | 99.5% | $362,414,933/yr | **−$727,074,386** |

As a fraction of the oracle's true required capital, every method still holds well under
a third of what's needed: independence 8.3%, flat correlation 25.8%, vanilla GP 15.3%,
regime-mixture 18.6%.

## The Phase 1 ceiling replicates at 90x the property count

The ~93.3% achieved-survival ceiling that Phase 1 found at n=500 (RESULTS_PHASE1.md) shows
up again here, essentially unchanged, at n=45,000: every method lands in a tight
93.3-93.5% band, nowhere near the 99.5% target. Scaling the book up by two orders of
magnitude did not, by itself, close any of the gap Phase 1 identified — consistent with
Phase 1's finding that the shortfall is about which historical years get seen and how the
systemic regime is classified, not about property count or in-core vs. OOC computation.

## Why method 4 doesn't show Phase 1's data-driven improvement here

Phase 1's sweep (RESULTS_PHASE1.md) showed method 4 climbing from 94.8% (60 historical
years) to 97.3% (500 years) as more data let its adaptive regime classifier separate
systemic from normal years more accurately. Phase 2 uses only **25** historical years
(`HISTORICAL_YEARS_LARGE`), and by chance this particular 25-year draw (seed 100) contains
just **1** true-systemic year. `p_hat` (0.0333) is transferred as-is from Phase 1's single
60-year headline trial fit, not re-estimated at this scale or for this sample — per
`phase2_run.py`'s docstring, that's a deliberate scoping decision, not an oversight. With a
`fit_quantile` of 0.320 sized off that transferred `p_hat`, the classifier pulls in 8
"stress" years against that lone true-systemic year — a dilution ratio even worse than the
one Phase 1's diagnostic identified as the root cause of method 4's original failure mode.
Method 4's showing here (18.6% of true capital, best of the GP-based methods but still far
short) is therefore not a fair test of the fixed classifier at this scale — it's a
restatement of Phase 1's classification-dilution finding under an even thinner historical
sample, not new evidence about how method 4 performs with adequate data at n=45,000.

## Refinement results: Phase 1's transferred hyperparameters were already close

The 3-point OOC refinement (0.7x / 1.0x / 1.4x scale sweep around Phase 1's transferred
`sigma_f2`/`sigma_n2`) picked `scale=1.0` (no change) for method 3, and made only small
adjustments for method 4's two components:

| | ell (fixed, transferred) | sigma_f2 | sigma_n2 |
|---|---|---|---|
| Method 3 | 1.0687 | 0.1342 (unchanged) | 0.2487 (unchanged) |
| Method 4, normal | 0.1089 | 0.0000 (unchanged from ~7.9e-7) | 0.2438 |
| Method 4, systemic | 0.6765 | 0.6696 (unchanged) | 0.2211 |

The normal component's `sigma_f2` collapsing to ~0 is not new to this run — Phase 1's own
fit at n=500 already put it at 7.9e-7 (`transferred_start` in `results_phase2.json`), i.e.
the "normal" regime's losses show essentially no spatial correlation once the systemic
component is split out, a fitted result carried forward from Phase 1 rather than an
artifact of scaling or the OOC refinement. Geography-driven `ell` transferred unchanged
throughout, per `gp_loss_model_large.py`'s design (correlation length scale is a property
of the hazard process, not of how many properties are sampled from it).

## Rerun: a fair test of method 4 (`phase2_rerun_more_history.py`)

Following up on the point above: rerun with `HISTORICAL_YEARS_LARGE` raised from 25 to
**200** (≈13 expected true-systemic years at the DGP's ~6.7% frequency, vs. the original's
1) and `p_hat` **re-fit fresh** via `GaussianMixture` on this session's own n=45,000
historical sample (0.0400, vs. the stale 0.0333 transferred from Phase 1's n=500/60-year
fit) instead of transferred as-is. Same book, same oracle, same target. Output:
`results_phase2_more_history.json`.

### A real bug found and fixed along the way

The rerun's Method 4 normal-component eval (188 years, `scale=1.0`) hung for over 6 hours
— pegged CPU, near-idle GPU, no progress. Isolated reproduction (same exact parameters, a
fresh process) completed in ~6 minutes with flat, undegraded per-year timing, ruling out
a numerics problem. The difference: the real run had already been through 4 prior OOC
factor/close cycles (Method 3's 3-eval sweep + this component's own first eval) in the
same long-lived process before the hang. Root cause: `gp_ooc_solver.cuf`'s CUDA Fortran
backend keeps a single **global, module-level** solver state — `py_ooc_init`/`py_ooc_close`
unconditionally deallocate and reallocate the full ~8GB of pinned host panel memory on
*every* call, even though `refine_sigma_scale_ooc`'s 3-point sigma sweep only changes
`(sigma_f2, sigma_n2)`, never the panel geometry (coords/n/b/R/ram_budget). Repeated
multi-GB pinned allocate/deallocate cycles in one process is a known CUDA cost center, and
it compounded across the run's 9 total eval cycles (3 components × 3 scales) until it
stalled.

**Fix**: added `py_ooc_set_sigma(sigf2, sign2)` to `gp_ooc_solver.cuf` — updates only the
module-level sigma scalars, leaving panel allocation untouched (`py_ooc_factor` already
rebuilds every kernel entry from scratch each call, so reusing panel storage across sigma
values is safe). Added a matching `OOCCholeskyF.refactor()` in `gp_ooc_fortran.py` and
rewrote `refine_sigma_scale_ooc` (`gp_loss_model_large.py`) to init **one** factor object
per component and `refactor()` across its 3-point sweep, closing once at the end — cutting
9 total init/close cycles down to 3 for the whole run. Verified against the exact hung
config before relaunching: `refactor()`-based scale=0.7 reproduced the known-good
`lml=-6460438.6` exactly, and scale=1.0 (the eval that had hung) completed in ~351s. Along
the way, also fixed `OOC_RAM_BUDGET_GB` being defined but never passed through to
`refine_sigma_scale_ooc` in the rerun script (a separate, latent, unrelated bug — it had
been silently using the library's default 16GB budget instead of the intended 8GB).

### Rerun result

| Method | Required capital | Achieved survival | Target | Capital gap vs. truth | As % of oracle capital |
|---|---|---|---|---|---|
| 1. Independence | $69,775,076 | 93.31% | 99.5% | **−$823,558,967** | 7.8% |
| 2. Flat correlation | $169,529,831 | 93.33% | 99.5% | **−$723,804,212** | 19.0% |
| 3. Vanilla spatial GP | $132,769,999 | 93.31% | 99.5% | **−$760,564,043** | 14.9% |
| 4. GP + regime-mixture | $439,390,984 | **96.11%** | 99.5% | **−$453,943,058** | 49.2% |

**Methods 1-3 are unchanged from the thin-history run** (93.3% ceiling, same as Phase 1 at
n=500) — exactly as expected, since none of them use the regime classifier at all. **Method
4 jumps from 93.33% to 96.11% achieved survival** (capital gap improves from −$727M to
−$454M) once it has enough true-systemic years and a properly re-fit `p_hat` to work with.
This is the fair test the original run couldn't provide, and it replicates Phase 1's
central finding at 90x the property count: methods that cannot represent a regime sit on a
flat ceiling regardless of data quality, while the regime-aware method climbs toward the
target as its classifier gets a genuine chance to work — the same shape as Phase 1's
60-to-500-year sweep (94.8% → 97.3%), now confirmed at n=45,000 too. A real, unsupervised
regime classifier still leaves meaningful headroom (96.11% vs. 99.5% target), consistent
with Phase 1's own finding that the last gap is attributable to genuine classification
imperfection, not a fixable implementation bug.

## Soft classifier at OOC scale (`phase2_rerun_soft.py`)

RESULTS_PHASE1.md's follow-up found a SOFT (responsibility-weighted) regime classifier
closes nearly all of method 4's remaining gap at small scale (n=500), landing within
0.1-0.8pp of the oracle-cheat ceiling at every historical-years size tested. Given how
compelling that was, it was ported to n=45,000: `gp_loss_model_large.refine_sigma_scale_ooc`
gained an optional `weights` parameter (each historical year's quadratic-form contribution
scaled by its GaussianMixture responsibility, `sum(weights)` replacing `n_years` in the
logdet/normalization terms — the OOC-scale counterpart of `gp_loss_model.py`'s
`_repeated_measures_lml_weighted`, verified to reduce exactly to the unweighted path when
`weights` is all-ones before this ran for real). Unlike the v2 rerun's hard 12/188
stress/normal split, EVERY one of the 200 historical years now contributes to BOTH
components' OOC refinement, weighted by that year's own P(systemic) instead of being
assigned to exactly one.

| Method | Required capital | Achieved survival | Capital gap vs. truth | As % of oracle capital |
|---|---|---|---|---|
| 1. Independence | $69,775,076 | 93.31% | −$823,558,967 | 7.8% |
| 2. Flat correlation | $169,529,831 | 93.33% | −$723,804,212 | 19.0% |
| 3. Vanilla spatial GP | $132,769,999 | 93.31% | −$760,564,043 | 14.9% |
| 4. GP + regime-mixture (soft) | $840,294,529 | **99.36%** | **−$53,039,513** | **94.1%** |

Methods 1-3 are unchanged (they don't touch the classifier). **Method 4 jumps from 96.11%
(hard partition) to 99.36% achieved survival** — right at the 99.5% target, and the capital
gap collapses from −$454M to **−$53M** (94.1% of the oracle's true required capital, up
from 49.2%). This is essentially the same jump the small-scale sweep found (93.3% → 99%+
at every data size), now confirmed at 90x the property count: the hard partition's
discard-or-keep cutoff, not an inherent limit from not knowing the true regime, was the
dominant remaining source of error, at both scales tested so far.

## What's next

The 45,000-property scale, the OOC solver (post-fix), and now the soft classifier all work
as designed and all replicate their small-scale Phase 1 counterparts cleanly. The lab's
running finding across three follow-ups is consistent: methods that cannot represent a
regime sit on a flat ~93.3% ceiling regardless of data or classifier quality; methods that
can, need BOTH enough historical data (v2's fix) AND a classifier that doesn't discard
information (v3's fix) to approach the target. Remaining open threads: (a) close the last
~$53M/0.14pp gap — is it the 3-point sigma-scale sweep's coarseness (vs. a full MLE re-fit,
not yet attempted at OOC scale), RFF scenario-generation approximation error, or genuine
irreducible estimation noise; (b) re-run methods 1-3 at n=45,000 with the same 200-year
history as a formality (unaffected in principle, not yet re-verified at this exact
config); (c) test whether the soft classifier's OOC cost (now ~2x the hard partition's,
since both components solve against all 200 years instead of a 12/188 split) scales
acceptably toward LAB_PLAN.md's original ~100k-300k property target.
