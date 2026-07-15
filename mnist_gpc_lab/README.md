# MNIST GPC Lab — Laplace-approximated GP classification vs. SVM

**Status:** M1 done (2026-07-15); M2 done (2026-07-15) — 200-seed robustness
check confirms the confident-error asymmetry is real, not a 3-seed fluke;
M3 done (2026-07-15) — confirmed structural across kernel family and
likelihood, with a real likelihood-dependent effect size; M4 done
(2026-07-15) — MCMC ground truth revises the M3 hypothesis: the logit/probit
confidence gap is a real property of the two response functions, not mostly
an artifact of one Laplace approximation being worse than the other. Week
closes here — visualstash/place bridge and further scale-up deferred to a
future session (see Backlog).
**One line:** replicate the shape of GPML (Rasmussen & Williams 2006) Sec 3.7.3's
MNIST worked example — Laplace-approximated GP classification with a calibrated
predictive probability, benchmarked against an SVM — using this engine's CUDA
Fortran-family linear algebra, extended for the first time from regression to
classification.

## Why this lab, and why now

Every other lab in this project (`gp_lab/`, `gblup_lab/`) exercises the engine's
*regression* solve: `(K + sigma_n^2 I) alpha = y` for continuous `y`. The GPML
book's MNIST chapter is a classification problem — no closed-form posterior,
because the Bernoulli likelihood isn't Gaussian. That's a genuinely new capability
(Laplace's approximation, GPML Algorithm 3.1: Newton-Raphson mode-finding with a
reweighted Cholesky each iteration), not a config change, and "does this engine's
solver machinery generalize past exact-GP regression" is a real question worth a
lab of its own.

## What got built

- **`../gp_classifier.py`** (engine-level, not lab-local — a new capability
  alongside `gp_core.py`): `LaplaceBinaryGPC` (logistic likelihood, chosen over
  the book's probit because `W = diag(pi(1-pi))` is always positive, so
  `I + W^0.5 K W^0.5` is guaranteed SPD and reuses `gp_core.potrf_inplace`/
  `potrs_inplace` unchanged instead of needing a semi-definite-safe path) and
  `OneVsRestLaplaceGPC` (10 independent binary classifiers, shared kernel
  hyperparameters). Self-test in `gp_classifier.py`'s `__main__` confirms Newton
  converges (6 iterations on a toy 2D problem) and that confidence is genuinely
  calibrated — low `|p-0.5|` near the decision boundary, high far from it —
  before ever touching MNIST.
- **Engine note worth flagging on its own:** `gp_core.py`'s direct kernel caps
  `d <= 32` because it's a *register* limit (each CUDA thread keeps one point's
  full coordinate vector in registers so a matvec never materializes an n×n
  intermediate) — not an arbitrary knob. MNIST's raw pixels are d=784, past that
  cap by 24x, so `gp_classifier.py` builds the kernel matrix densely instead, via
  the same one-DGEMM squared-distance identity (`||a-b||^2 = ||a||^2 + ||b||^2 -
  2a.b`) already validated in `gblup_lab/marker_kernel.py` — this is exactly the
  "d>32" path `../PLAN.md` Phase 3 item 6 had deferred until a real workload
  demanded it. See `../PLAN.md` item 6 for the full note.
- **`datasets.py`** — balanced per-digit subsample of the cached MNIST pickle
  (`/var/home/fraser/machine_learning/data/mnist/mnist.pkl.gz`, already on disk,
  no re-download), train/val from MNIST's own 50k training split (no leakage
  between them), test from MNIST's own held-out 10k.
- **`run_lab.py`** — median-heuristic RBF lengthscale grid, selected on
  validation accuracy; final one-vs-rest Laplace GPC fit + eval on a held-out
  test subsample; an `SVC(kernel="rbf", probability=True)` baseline at a
  matching gamma, same protocol. Writes `results/mnist_gpc_seed<seed>.json`.
- **`build_notebook.py`** → `MNIST_GPC_LAB.ipynb` — loads the JSONs, plots
  accuracy/log-loss/reliability, and prints a sample of individual test-digit
  predictions with their full 10-way probability vector (the "confidence"
  payoff the user actually asked for).

## Scope decision: subsample, not full MNIST

Exact GP is O(n^3) per Newton step, times ~10 one-vs-rest classes, times ~6-7
Newton iterations to convergence — the full 60k-image training set was never in
scope for a small lab. Used 150 images/class train (n=1,500), 30/class
validation (n=300), 100/class test (n=1,000) per seed. Fit time ~1.5s, predict
~0.03s on an RTX 4060 — cheap enough that a bigger subsample (or the OOC path,
if it's ever wanted) is a knob-turn, not a rebuild.

## M1 results (3 seeds, 2026-07-15)

| seed | GPC test acc | GPC log-loss | SVM test acc | SVM log-loss |
|---|---|---|---|---|
| 0 | 0.904 | 0.945 | 0.933 | 0.235 |
| 1 | 0.903 | 0.948 | 0.937 | 0.226 |
| 2 | 0.897 | 0.957 | 0.939 | 0.248 |

**Accuracy: close, SVM slightly ahead** (0.901±0.004 vs 0.936±0.003) — consistent
with the book's general finding that GPC and SVM perform similarly on this kind
of problem; SVM's edge here is plausible given the small n and that only 1 shared
lengthscale was tuned for all 10 GPC one-vs-rest models (no per-class ell).

**Log-loss: real finding, not swept under the rug.** GPC's log-loss (~0.95) is
much worse than SVM's Platt-scaled one (~0.24), even though the *binary*
self-test in `gp_classifier.py` showed genuinely calibrated confidence
(low near a boundary, high far from it). The likely cause is the one-vs-rest
combination step: `OneVsRestLaplaceGPC.predict` normalizes 10 independent
binary P(class=c) outputs to sum to 1, which is a well-known weak point of
naive OvR — it has no mechanism to keep 10 separately-calibrated binary
probabilities jointly calibrated as a 10-way distribution. **Not fixed this
session** — the honest options are (a) select the lengthscale on validation
log-loss instead of accuracy (grid already logs both, currently the accuracy
column is used for selection — see `run_lab.py`), or (b) a proper multiclass
Laplace GPC with a softmax likelihood (a materially bigger rebuild: `W` becomes
a structured 10n x 10n block, not 10 independent diagonals) rather than
one-vs-rest at all. Flagged for a follow-up milestone, not hidden in the
notebook's headline numbers.

**The actual headline, found after looking past the summary stats (user
prompted this): GPC is essentially never confidently wrong.** Every test
prediction's confidence and correctness was kept (`confidence_all`/
`correct_all` in the results JSON, not just accuracy/log-loss), and the split
is stark and holds identically across all 3 seeds:

| seed | GPC errors with confidence>0.5 | SVM errors with confidence>0.5 |
|---|---|---|
| 0 | 0.0% (0/96) | 56.7% (38/67) |
| 1 | 0.0% (0/97) | 47.6% (30/63) |
| 2 | 1.0% (1/103) | 55.7% (34/61) |

This *inverts* the log-loss ranking above: log-loss punishes any
miscalibration uniformly (and GPC's OvR-combination miscalibration is real),
but *where* the errors land is arguably the more actionable property for a
deployed classifier. GPC's errors cluster at low confidence — you could gate
on "only trust this above confidence X" and get a real safety margin. The
SVM's Platt-scaled probabilities, despite a much better log-loss on average,
include genuinely confident mistakes (two seed-0 SVM errors carry confidence
>0.9) — exactly the silent-failure case a confidence score is supposed to
catch. Both models' risk-coverage curves reach 100% accuracy at low coverage
(see notebook), so a coverage curve alone doesn't surface this — the
confident-error count does.

## M2 (2026-07-15): 200-seed robustness check — the finding survives

The open question from M1 was whether the confident-error asymmetry was
intrinsic to the Laplace approximation or an artifact of one 3-seed pilot.
`confidence_study.py` reran the same comparison across **200 independent
seeds**, each drawing a *fresh* balanced train/test subsample (not just a
different RNG draw against one fixed split) — checking robustness to which
specific images land in train vs. test, not just prediction noise. Lengthscale
was fixed at 5.1 (the value M1's validation grid selected on all 3 pilot
seeds) rather than re-gridded per seed, since re-running that grid 200x was
the expensive part, not the fit itself; this cut the per-seed cost to ~4.5s,
200 seeds finishing in 15.3 minutes total.

**Statistics were computed per seed, then aggregated by bootstrap-resampling
seeds** (10,000 resamples) rather than pooling all 200,000 test points as if
independent — test points within one seed share a fitted model and are
correlated, so the seed is the correct unit of replication for any
cross-seed CI. Result: **GPC's fraction of errors with confidence>0.5 is
0.57% [95% CI 0.48%, 0.67%]; SVM's is 56.97% [56.06%, 57.89%]** — the two
intervals aren't just non-overlapping, they're separated by roughly 55
percentage points against CI widths of under 0.2 points each. Full notebook:
`MNIST_GPC_ROBUSTNESS.ipynb`.

**Why 200 seeds and not more:** the bootstrap CI half-width scales as
`1/sqrt(n_seeds)` — going to 2,000 seeds (~10x the compute, hours instead of
minutes) would shrink an already-decisive CI by ~3.2x, changing decimal
places, not the conclusion. The honest case for more seeds isn't a tighter
mean here — it's resolving finer bins in the pooled calibration curve, which
needs more raw data density, not more independent replicates of a mean that's
already this far from ambiguous.

**A data-driven cutoff, from the pooled 200-seed calibration curve:** for a
99.5%-reliability target (accuracy among retained predictions), GPC reaches it
at confidence >= 0.436, retaining 48.7% of predictions; SVM needs confidence
>= 0.864 to reach the same bar, retaining 76.4%. So at matched reliability,
SVM currently retains more predictions — GPC's per-point confidence values
run lower overall (a plausible side effect of the same OvR-normalization
miscalibration flagged in M1, not necessarily a deeper problem), even though
its *ordering* of confident-vs-error predictions is the more trustworthy one
of the two. Not yet disentangled: whether recalibrating GPC's normalized
probabilities (e.g. temperature scaling on the OvR output, or the proper
multiclass softmax-likelihood rebuild flagged in M1) would close this
coverage gap while keeping the confident-error property intact — a natural
M3 if this lab continues.

**Still open, not addressed by M2:** whether the near-zero confident-error
rate is intrinsic to the Laplace approximation's predictive variance term
(`predict()`'s `kappa(var)` shrinkage, which reduces confidence whenever a
test point's cross-kernel row has meaningfully overlapping mass with more
than one class's training points) or a property of the RBF-on-raw-pixels
kernel choice specifically — M2 varied the data draw, not the kernel family
or likelihood. A follow-up varying those would be the next real test of how
general this result is.

## M3 (2026-07-15): kernel/likelihood generality sweep — structural, with a real caveat

M2 left open whether the confident-error asymmetry was intrinsic to Laplace's
predictive-variance shrinkage or an artifact of the RBF+logit combination
used throughout M1/M2. `gp_classifier.py` was generalized (`kind=` for
RBF/Matern32/Matern52, `likelihood=` for logit/probit — both keep `W` PSD, so
the same SPD Newton loop applies to either) specifically to test this, and
`generality_sweep.py` ran 3 alternate configs at 50 seeds each (fewer than
M2's 200 since the question here is "does a different config land in a
qualitatively different regime," not "nail the same decimal precision"),
each with its own quick validation-grid lengthscale (Matern doesn't share
RBF's optimal `ell` at the same value — checked empirically before committing
to the sweep). Full notebook: `MNIST_GPC_GENERALITY.ipynb`.

**Result — all four configs land far below the SVM's 56.97%, confirming the
effect is structural, not an RBF+logit artifact:**

| config | frac. of errors with confidence>0.5 (95% CI) |
|---|---|
| RBF + logit (M2 baseline, 200 seeds) | 0.57% [0.48%, 0.67%] |
| Matern 3/2 + logit (50 seeds) | 0.13% [0.05%, 0.23%] |
| Matern 5/2 + logit (50 seeds) | 0.20% [0.10%, 0.32%] |
| RBF + probit (50 seeds) | 3.54% [3.01%, 4.07%] |

Matern behaves like RBF (if anything slightly better); more importantly,
**probit — where the predictive probability is exact (GPML eq 3.25), not
MacKay's (1992) moment-matched approximation for logit — still lands at
3.5%, over an order of magnitude below the SVM.** That rules out "it's just
an artifact of the logit approximation" as the explanation.

**The real, non-swept-under-the-rug caveat: probit's rate is 6-25x higher
than every logit config's.** Working hypothesis, not confirmed: MacKay's
logit approximation is itself conservative (it tends to under-state
predictive confidence relative to the true sigmoid-Gaussian average it's
approximating), so logit's near-zero rate may be "Laplace's structural
variance-shrinkage plus an extra approximation-induced safety margin," while
probit's higher-but-still-small rate is closer to what the variance
shrinkage alone provides. Testing that would need a likelihood-free ground
truth (MCMC or expectation propagation) to separate the two effects — not
attempted here, flagged as the natural M4 if this thread continues.

**Practical read for "is GPC now competitive with SVM":** M2 already showed
GPC at a fixed 0.5 cutoff gives high reliability at ~49% coverage (vs SVM's
76% at matched 99.5% reliability, from the pooled calibration curve). M3
confirms that safety property isn't a fragile artifact of one kernel/
likelihood choice — but it does *not* by itself close M2's remaining
coverage gap. That was explicitly out of scope for M3 (see "which M3 thread"
discussion above) and stays the natural next milestone: recalibrating the
one-vs-rest combination (temperature scaling, or the proper multiclass
softmax-likelihood rebuild) to see whether coverage can rise at matched
reliability while the confident-error property — now confirmed structural —
survives the recalibration.

## M4 (2026-07-15): disentangling Laplace-approximation error from MacKay's
## logit approximation, via MCMC ground truth — revises the M3 hypothesis

M3 found probit's confident-error rate (3.54%) roughly 6-25x higher than
every logit config's, and hypothesized MacKay's (1992) moment-matched
logit-predictive approximation was itself conservative, stacking an extra
safety margin on top of Laplace's structural variance-shrinkage. That
hypothesis conflated two different error sources — Laplace's Gaussian
approximation to the true posterior over f (present for *both* likelihoods)
and MacKay's sigmoid-Gaussian approximation (only in the logit predictive
step; probit's is exact, GPML eq 3.25) — and M3 had no way to separate them.

**Method:** elliptical slice sampling (ESS; Murray, Adams & MacKay 2010) —
tuning-free MCMC purpose-built for exactly this model class (GP prior +
non-Gaussian likelihood) — run as ground truth for both the logit-likelihood
and probit-likelihood models independently, on one binary slice (digit 3 vs
8, echoing the book's own 3-vs-5 example), n_train=200, n_test=100, single
seed (`mcmc_disentangle.py`; this is a diagnostic case study to sharpen
understanding before the week closes, not a robustness sweep — the seed/scale
caveats from M1-M3 apply even more here). For each likelihood: 800 posterior
samples of f_train (after 400 burn-in, thinned by 3), each pushed through the
exact GP conditional to get a Monte Carlo predictive probability at every
test point — directly comparable to Laplace's approximate predictive
probability at the same points, same kernel, same data.

**Result — both Laplace approximations are quite faithful to their own
likelihood's true posterior:**

| likelihood | Laplace vs MCMC mean \|diff\| | mean confidence (Laplace) | mean confidence (MCMC) |
|---|---|---|---|
| logit | 0.0116 | 0.2235 | 0.2251 |
| probit | 0.0200 | 0.2866 | 0.2980 |

Laplace tracks MCMC closely for *both* likelihoods (mean absolute
disagreement 1-2 percentage points, same direction — Laplace slightly less
confident than the true posterior in both cases). **This revises the M3
hypothesis: the logit/probit confidence gap is not mostly "one Laplace
approximation is worse than the other."** It shows up already at the MCMC
(ground-truth) level — probit's true posterior predictive is itself more
confident (mean |p-0.5| 0.298) than logit's true posterior predictive (0.225)
on the *same* underlying data and kernel. The gap is a genuine property of
the two response functions (MacKay's `kappa(var)`-rescaled sigmoid vs the
exact `Phi(mean/sqrt(1+var))`), not primarily an artifact of Laplace fitting
one likelihood's posterior worse than the other's.

**What this means for the production read (M3's takeaway stands, sharpened):**
logit's extra conservatism relative to probit is real and is a property of
the likelihood/response-function choice itself, not a bug or an
approximation error to be corrected — reinforcing that logit is the safer
default for a deployed reject-on-uncertainty system, now for a better-
understood reason than "the approximation happens to be conservative."

**Caveats on M4 specifically:** one seed, one binary slice, small n (200
train / 100 test) — enough to sharpen understanding, not to claim the same
statistical weight as M2/M3's seed-robust numbers. If this distinction ever
matters for a production decision, the natural next step is repeating this
across several seeds/slices before trusting the magnitude (not just the
direction) of the gap.

## Backlog / future directions (not started, logged for a future session)

- **visualstash/place bridge.** `/var/home/fraser/machine_learning/visualstash/place`
  (Rust BoVW + RANSAC-homography place-recognition stack) already produces a
  per-candidate-match score (RANSAC inlier count/ratio) that is structurally
  the same kind of signal as this lab's GPC confidence — a per-decision score
  that should separate real matches from spurious ones. Two possible bridges,
  neither started: (a) cheap — calibrate the existing RANSAC score with the
  same seed/scene-robust bootstrap methodology used in M2, no GP engine
  involved; (b) bigger — train a `gp_classifier.py` Laplace GPC on match-
  descriptor features (inlier count, reprojection error, ratio-test stats) as
  a genuine calibrated match/no-match classifier, inheriting the structural
  safety margin confirmed in M2/M3. Needs labeled match/no-match examples
  from that project first; scope not yet assessed.
- **M4 at proper scale**, if the logit-vs-probit gap's exact magnitude (not
  just direction) ever matters for a decision: repeat across multiple
  seeds/slices with the same bootstrap-CI discipline as M2/M3.
- **M2's coverage gap** (GPC needs confidence>=0.436 for 99.5% reliability at
  48.7% coverage vs SVM's 76.4%) — recalibrating the one-vs-rest combination
  (temperature scaling, or a proper multiclass softmax-likelihood rebuild)
  to see whether coverage can rise while the confident-error property
  survives.

## Structure

```
mnist_gpc_lab/
  LAB_PLAN.md              this file
  datasets.py              balanced MNIST subsample loader (reads the cached pickle)
  run_lab.py               ell grid -> fit -> eval -> results/mnist_gpc_seed<n>.json (M1, 3 seeds)
  build_notebook.py        results/mnist_gpc_seed*.json -> MNIST_GPC_LAB.ipynb
  confidence_study.py      fixed-ell, N-seed confidence/correctness study -> results/confidence_study.json (M2)
  build_robustness_notebook.py  results/confidence_study.json -> MNIST_GPC_ROBUSTNESS.ipynb
  results/                 per-seed JSON (M1) + confidence_study.json (M2)
  MNIST_GPC_LAB.ipynb          rebuild: python3 build_notebook.py && \
                                jupyter nbconvert --to notebook --execute --inplace MNIST_GPC_LAB.ipynb
  MNIST_GPC_ROBUSTNESS.ipynb   rebuild: python3 confidence_study.py --n-seeds 200 && \
                                python3 build_robustness_notebook.py && \
                                jupyter nbconvert --to notebook --execute --inplace MNIST_GPC_ROBUSTNESS.ipynb
  generality_sweep.py      per-config val-grid ell -> N seeds -> results/generality_<kind>_<likelihood>.json (M3)
  build_generality_notebook.py  results/confidence_study.json + results/generality_*.json -> MNIST_GPC_GENERALITY.ipynb
  MNIST_GPC_GENERALITY.ipynb   rebuild: python3 generality_sweep.py --n-seeds 50 && \
                                python3 build_generality_notebook.py && \
                                jupyter nbconvert --to notebook --execute --inplace MNIST_GPC_GENERALITY.ipynb
  mcmc_disentangle.py      ESS MCMC ground truth vs. Laplace, both likelihoods -> results/mcmc_disentangle.json (M4)
```

Engine dependency: `../gp_classifier.py` (new this session for M1, generalized
in M3 with `kind=`/`likelihood=`) — a peer to `../gp_core.py`, not lab-local,
since Laplace GPC is a general engine capability any future classification
lab can reuse.

## Risks / honest unknowns

- **One shared lengthscale across all 10 one-vs-rest models** — a
  simplification; per-class `ell` (some digits are easier to separate than
  others) was not tried.
- **OvR log-loss finding above** — real, not yet fixed.
- **n=1,500 train is small** relative to MNIST's 60k; not claiming this beats
  any published MNIST number, only that it replicates the book's GPC-vs-SVM
  comparison shape at a scale exact GP can handle in a small lab session.
