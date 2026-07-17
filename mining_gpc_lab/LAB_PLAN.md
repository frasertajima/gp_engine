# mining_gpc_lab — Laplace GPC vs. SVM on ore/waste classification, Carlin Trend Au

**Status:** Phase 0 DONE (2026-07-17) — `datasets.py` loads and filters the raw NURE-HSSR CSV,
reproducing `01_data.ipynb`'s Carlin Trend filter exactly (n=4,106; Au p95 cutoff = 0.0109 ppm,
matches the notebook's 0.011); produces `spatial` (d=2, local-km-projected so the ARD lengthscale
is comparable to the fitted 34.4 km variogram range) and `spatial_pathfinder` (d=8) feature sets,
stratified train/val/test split holding the ~5.1% ore rate steady in every split (209 ore / 3,897
waste total). **Phase 1 DONE (2026-07-17)** — see "Phase 1 result" below: replicates, and sharpens,
the confident-wrong pattern from `mnist_gpc_lab`/`place_gpc_lab`, plus a real mid-implementation
finding about the P95 class imbalance that changed the evaluation metric (see below). **Phase 2
DONE (2026-07-17)** — see "Phase 2 result" below: GPC's better ranking is worth real money in
`mining_mpdok`'s own drilling-campaign economic model ($423M/campaign advantage over SVM at k=50,
paired bootstrap CI excludes zero by a wide margin). **Phase 3 DONE (2026-07-17)** — see "Phase 3
result" below: the *only* genuinely open question in the lab, answered **no** — the nugget-masking
effect that widened MPDOK's regression advantage over FRK (fig19) does not widen GPC's calibration
advantage over SVM; if anything the confident-wrong gap narrows slightly on cleaner (lower-nugget)
data (47.0pp → 40.4pp), a negative result that sharpens rather than undermines the Phase 1/2
finding (see below). **`MINING_GPC_LAB.ipynb` built and executed (2026-07-17)** — all four result
files load live, no hand-transcribed numbers, 0 execution errors. **Phase 4 DONE (2026-07-17)** —
see "Phase 4 result" below: extended `gp_classifier.py`'s `LaplaceBinaryGPC` to support ARD (a
reusable engine fix, verified bit-identical to the isotropic path when `ell` has length 1), fit
per-pathfinder-element lengthscales via LML-maximizing Nelder-Mead. Aggregate result matches Carlin
pathfinder theory (As/Sb/Tl shorter than Ag/Cu/Zn on average) but the individual ranking is more
nuanced (Cu is actually the single shortest lengthscale) — reported honestly, not rounded to a
clean story. Adding pathfinders roughly doubles AP for both models and narrows but does not close
the confident-wrong gap (47.0pp → 38.5pp). **Follow-up (2026-07-17)**: reran Phase 2's dollar
economics on the pathfinder-ARD-ranked candidates — the economic gap narrows far more (7.5x) than
AP or confident-wrong would suggest ($423M → $56M [$47M,$66M] at k=50), evidence that ranking
quality at the top of a candidate list converges faster than calibration quality does; see Phase 4
result below. Phase 5 (stretch, optional) not started.

## Phase 1 result (2026-07-17)

**Mid-implementation finding, not a bug:** at ~5.1% ore prevalence, `P(ore)` never crosses 0.5 for
either model at any `ell` tried — recall/precision/balanced-accuracy at the default threshold are
all degenerate (0.000 / undefined / 0.500). This makes sense (base rate is 1-in-20) but meant the
original plan's headline metrics (accuracy, confidence>0.9 on a positive prediction) couldn't
discriminate between the two models at all. Fixed by adding **average precision** (threshold-free
ranking metric) as the model-selection criterion and a secondary headline number — the same metric
`mining_mpdok/05_thesis.ipynb` already used for its own exploration-targeting comparison (fig17),
so this stays comparable across the two labs by construction. The confident-wrong methodology
survives unchanged, just reframed as "of the misses (false negatives), how many carried >90%
confidence in the wrong call" rather than "of the (positive-predicted) errors."

`run_lab.py --seed 0`: `ell=70.99` km selected on validation AP (Matérn-3/2, matching the fitted
variogram's kernel family). Test set: **GPC AP=0.225 vs. SVM AP=0.061** — GPC's ranking of ore
likelihood is real, not noise (SVM's AP is barely above the 0.051 chance floor at this prevalence).

`confidence_study.py --n-seeds 200`: **average precision, mean over 200 seeds: GPC 0.240 ± 0.053
vs. SVM 0.082 ± 0.035** — non-overlapping. **Confidently-wrong-on-a-miss rate (pooled, 95%
bootstrap CI): GPC 52.8% [51.7%, 53.9%] vs. SVM 99.8% [99.7%, 99.9%]** (4,434/8,400 vs. 8,385/8,400
missed-ore points carried >90% confidence in the "waste" call) — a *sharper* separation than either
prior GPC lab found, and with CIs tight enough (200 seeds × 42 test-set ore points) that they don't
need the wide margin `place_gpc_lab`'s n=219 result did. Read carefully: SVM's Platt-scaled
`P(ore)` barely moves off the ~5% base rate for true ore points (mean AP 0.082, near the 0.051
chance floor), so it is "confidently" wrong on nearly every miss almost by construction — this is
the imbalance manifesting as a calibration failure, not evidence SVM never even tries to separate
the classes (its AP is still ~1.6x chance). GPC's Laplace posterior assigns meaningfully more
probability mass to true ore points (seed-0 max P(ore)=0.33 vs. SVM's 0.12, see run_lab.py's
docstring) without ever crossing 0.5 either — its calibration advantage is in *how much* it moves
off the prior for genuinely likely points, not in ever making a positive call outright at this
threshold.

**One line:** the same "confidently wrong" question `mnist_gpc_lab` and `place_gpc_lab` asked of
digits and loop-closure — is Laplace GPC's confidence more trustworthy than an SVM's? — asked here
of a genuinely high-stakes economic decision: is a sample point *ore* (above cutoff grade) or
*waste*, using the real Carlin Trend gold geochemistry `mining_mpdok` already collected, cleaned,
and variogram-fit.

## Why this lab, and why now

`mining_mpdok`'s masking-effect study already proved a *regression* story: Fixed-Rank Kriging
structurally misses short-range high-grade Au anomalies, and that failure has a dollar figure
attached (fig18: $200M more NPV under MPDOK than FRK m=20 on a 50-target campaign). What it didn't
ask is the *classification* framing of the same decision a mining company actually makes at the
drill-permitting stage: not "what's the predicted grade at this point" but "do we call this ore or
waste" — a binary decision under uncertainty, exactly the shape `mnist_gpc_lab`/`place_gpc_lab`
built calibrated-classifier machinery for.

The hypothesis this lab tests: if SVM systematically overstates confidence on marginal evidence (as
found twice now — MNIST pixels, RANSAC place-recognition features), the same failure mode on ore/
waste calls is not academic. `mining_mpdok`'s own README already names the two costs precisely —
**Revenue loss** (a real high-grade zone confidently called waste) and **milling waste** (barren
rock confidently called ore, $10–30/tonne for zero yield) — but that lab never asked whether the
*confidence* attached to FRK/MPDOK's predictions was itself trustworthy, only whether the point
prediction was accurate. This lab asks the calibration question directly, and — because
`mining_mpdok` already built the $/target and $/tonne economic model in `05_thesis.ipynb` — can
convert "confidently wrong" from a percentage into a dollar figure the same way fig18 did.

## Data (all reused, nothing new to collect)

- **`mining_mpdok/nevada_nure_raw.csv`** — 13,828 USGS NURE-HSSR Nevada stream-sediment samples;
  4,106 within the Carlin Trend bounding box (39.5–42.0°N, 117.5–114.5°W). Columns used: lat/lon,
  Au/As/Sb/Ag/Cu/Zn/Tl (ppm).
- **Fitted variogram parameters** (`02_variogram.ipynb`, reused not refit): Matérn-3/2, nugget =
  0.4536, partial sill C0 = 0.3604, ℓ = 34.4 km, nugget fraction 55.7%.
- **Cutoff grade / label**: start with the P95 threshold already computed (Au = 0.011 ppm) as the
  ore/waste boundary — same threshold `01_data.ipynb`'s HG-signal analysis used, so results are
  directly comparable to the existing eigenspectrum/masking figures. Flag clearly that a real mine's
  economic cutoff grade depends on strip ratio, metal price, and processing cost, not a population
  percentile — P95 is a defensible stand-in, not a claim about any specific deposit's true cutoff.
- **`mining_phase1–5.npz`** — existing FRK/MPDOK regression results (predictions, spatial holdout
  arrays, economic parameters from fig18/fig19). Reused as a third baseline (Phase 4) and as the
  source of the $/target, $/tonne constants for the economic layer (Phase 2), not recomputed.
- **Synthetic nested-Matérn generator** (`03_mpdok.ipynb`'s `y = y_long + y_short + ε` at the real
  NURE-HSSR sample locations, 6% nugget) — reused unchanged in Phase 3 to strip the nugget mask,
  same role it played for the original regression masking-effect result.

No new field data, no new engine capability beyond what `gp_classifier.py`'s `LaplaceBinaryGPC`
(built for `mnist_gpc_lab`, already reused unchanged by `place_gpc_lab`) already provides. This is
a "cheap bridge" lab in the same sense `place_gpc_lab` was.

## Method

**Phase 0 — setup.** Load `nevada_nure_raw.csv`, reproduce the Carlin Trend filter and P95 cutoff
label from `01_data.ipynb`. Two feature sets to compare, both already within engine limits:
  1. **Spatial-only** (lat/lon, d=2) — Matérn-3/2 ARD kernel, directly comparable to the variogram
     already fit.
  2. **Spatial + pathfinder** (lat/lon + As/Sb/Ag/Cu/Zn/Tl, d=8) — well inside gp_engine's
     ARD envelope (validated bit-identical to d=26, MAX_D=32).
  Stratified 60/20/20 split preserving ore/waste class balance (P95 cutoff → ~5% positive class,
  imbalanced — note this up front, it's more skewed than MNIST-vs-rest or place's 73/146).

**Phase 1 — confident-wrong replication. DONE (2026-07-17), see "Phase 1 result" above.** Fit
`LaplaceBinaryGPC` (Matérn-3/2, not the other labs' default RBF -- matches the already-fitted
variogram kernel family) vs `SVC(kernel="rbf", probability=True)` on spatial-only features,
median-heuristic `ell` grid selected on **validation average precision**, not accuracy -- found
during implementation that `P(ore)` never crosses 0.5 for either model at ~5.1% ore prevalence, so
accuracy/recall/balanced-accuracy at the default threshold are all degenerate and can't
discriminate between candidate `ell` values or between models. Headline metrics: average precision
(GPC 0.240±0.053 vs SVM 0.082±0.035, 200 seeds) and fraction of misses (false negatives) with
confidence>0.9, pooled over a 200-seed bootstrap (GPC 52.8% [51.7,53.9] vs SVM 99.8% [99.7,99.9]).

**Phase 2 — economic quantification. DONE (2026-07-17), see "Phase 2 result" below.** Originally
planned as a confusion-matrix $ layer, but Phase 1 found a fixed 0.5 threshold is degenerate for
both models (see above), so a confusion-matrix cost model would have needed an arbitrarily chosen
threshold. Used `mining_mpdok/05_thesis.ipynb`'s own economic model instead, unchanged: a **ranked
top-k drilling campaign** (drill the k highest-`P(ore)`-ranked targets, pay $1M/target regardless
of outcome, collect $50M NPV per confirmed high-grade discovery, same `k_econ` grid and k=50
headline campaign size as fig17/fig18) -- this needs no threshold at all, only an ordering, so it
sidesteps Phase 1's finding entirely rather than working around it. Applied to GPC-ranked vs.
SVM-ranked test-set candidates, pooled over 200 fresh seeds with a **paired** bootstrap CI on the
net-value gap (paired per seed since both models rank the same test set each seed, removing
seed-to-seed variance in which points happen to be test-set ore).

## Phase 2 result (2026-07-17)

`economic_layer.py --n-seeds 200`, k=50 headline campaign (matching fig18's own headline size),
$1M/target, $50M/HG discovery (both constants unchanged from `05_thesis.ipynb`):

| | HG found (of ~13 in top-50 candidates) | Net value | 
|---|---|---|
| GPC | 12.3 ± 2.4 | $565M ± $122M |
| SVM | 3.8 ± 2.8 | $142M ± $138M |
| Random targeting | — | $65M ± $75M |

**GPC − SVM net advantage @ k=50: $423M [$396M, $450M] (95% paired bootstrap CI)** — larger in
absolute terms than `mining_mpdok` fig18's own headline FRK-vs-MPDOK gap ($200M at k=50, same test
set size order of magnitude), though this is a different claim (classifier ranking quality, not
regression-then-rank) so the two numbers aren't directly additive. The advantage holds and grows
across the whole campaign-size grid tested (k=5 to k=200: $121M to $562M), and SVM barely beats
random targeting at small k (k=5: SVM $18M vs. random $8M) while GPC is already well ahead of both
($140M) — consistent with Phase 1's finding that SVM's `P(ore)` barely moves off the base rate.

**Phase 3 — masking crossover. DONE (2026-07-17), see "Phase 3 result" below.** Refit both
classifiers on a P95-cutoff label computed from `mining_mpdok/03_mpdok.ipynb`'s synthetic nested
Matern field (6% nugget) instead of raw Au (55.7% nugget), same locations (generated at the full
4,106-point Carlin Trend set rather than the notebook's 800-point eigenspectrum subsample -- see
`masking_crossover.py`'s docstring for why). Tested whether the GPC-vs-SVM confident-wrong gap
**widens** as the nugget drops, mirroring MPDOK's regression advantage over FRK (fig19: 13pp at
55.7% nugget → 42pp at 6% nugget). This was the one genuinely open empirical question in the lab
— unlike Phases 1-2, which extended patterns already seen twice. **Answer: no, it doesn't widen —
if anything it narrows slightly (47.0pp → 40.4pp).**

## Phase 3 result (2026-07-17)

`masking_crossover.py --n-seeds 200`: field generated with `mining_mpdok`'s exact nested-kernel
parameters (C_L=0.30, ell_L=80km; C_S=0.50, ell_S=10km; noise=0.05), measured nugget fraction 5.9%
(matches the notebook's stated 6.0%); P95-cutoff label overlaps 57.8% with the field's true
short-range peaks (sanity check that the label is meaningfully tied to the short-range signal, not
an artifact of the long-range component alone). `ell` re-selected on this field's own validation AP
(106.79 km, vs. 70.99 km for real Au — makes sense, this field's dominant correlation length
(ell_L=80km) is longer than the fitted Au variogram's 34.4km).

| | Average precision | Confidently-wrong-on-a-miss (95% CI) |
|---|---|---|
| **Real Au (55.7% nugget)** | GPC 0.240±0.053 / SVM 0.082±0.035 | GPC 52.8% [51.7,53.9] / SVM 99.8% [99.7,99.9] — **gap 47.0pp** |
| **Synthetic (5.9% nugget)** | GPC 0.318±0.053 / SVM 0.153±0.064 | GPC 37.5% [36.6,38.5] / SVM 77.9% [75.2,80.6] — **gap 40.4pp** |

**The masking-effect prediction from the regression lab does not transfer to classification
calibration.** In the regression case, dropping the nugget from 55.7% to 6% *widened* the
MPDOK-vs-FRK gap (13pp→42pp) because the nugget compresses both methods' RMSE toward the same
noise floor, hiding FRK's structural blindness to short-range signal. Here, both models get
*better* on the cleaner synthetic field (AP roughly +30-90% for both; SVM's confident-wrong rate
drops from 99.8% to 77.9%), but GPC improves too (52.8%→37.5%), so the *gap between them* narrows
rather than widens. Read: the two labs' "advantage" quantities aren't measuring the same underlying
mechanism. MPDOK-vs-FRK's regression gap is architectural (FRK's inducing-point spacing physically
cannot represent short-range structure, a geometry problem the nugget masks); GPC-vs-SVM's
calibration gap is about how each model's probability estimate responds to genuinely ambiguous
evidence (Laplace posterior variance vs. Platt-sigmoid extrapolation, per `place_gpc_lab`'s
retrain-with-cross-weather-negatives finding) — a lower-noise field gives *both* models more
learnable signal, which narrows a calibration gap even while a capacity/geometry gap would widen
under the same conditions. **This is a negative result worth keeping, not a failure to replicate**:
it sharpens what the Phase 1/2 finding actually is (an intrinsic Laplace-vs-Platt calibration
property, consistent with `place_gpc_lab`'s own conclusion) rather than a masking artifact that
would inflate under cleaner conditions the way MPDOK's regression advantage does.

**Phase 4 — pathfinder ARD. DONE (2026-07-17), see "Phase 4 result" below.** **Engine gap found
while writing Phase 1 (2026-07-17), fixed here:** `gp_classifier.py`'s `LaplaceBinaryGPC` took a
*scalar* `ell` (isotropic kernel only) -- `gp_core.py`'s regression path has per-dimension ARD
lengthscales, but that was never ported to the classifier. **Fixed via option (a) from the original
plan**: `LaplaceBinaryGPC` now accepts a scalar (isotropic, bit-identical to the pre-ARD code) or a
length-d vector `ell` (ARD) -- pre-scales each feature column by `1/ell_k` before the existing
isotropic distance-then-kernel path, same identity `gp_core.py`'s ARD kernel already uses, so
there's no separate ARD code path to keep in sync with the isotropic one. Verified: ARD with
`ell` of length 1 is bit-identical to the isotropic path (existing `mnist_gpc_lab`/`place_gpc_lab`/
this lab's Phases 1-3 callers are all unaffected); a synthetic 2D toy (one informative dimension,
one pure-noise dimension) confirms per-dimension scaling actually reaches the kernel (short ell on
the noise dim tanks accuracy to 0.535, short ell on the signal dim gets 1.000) -- both checks now
live in `gp_classifier.py`'s own `if __name__ == "__main__":` self-test.

Lengthscales fit via Nelder-Mead maximizing `LaplaceBinaryGPC`'s Laplace-approximate log marginal
likelihood (same optimizer/convention `gp_hyperopt.py`/`gblup_hyperopt.py` already use for GP
regression ARD), on `spatial_pathfinder_features` (d=8: x_km, y_km, log As/Sb/Ag/Cu/Zn/Tl).

## Phase 4 result (2026-07-17)

`pathfinder_ard.py`: Nelder-Mead over 9 log-parameters (8 lengthscales + sigma_f), 360 evaluations,
215s, converged to LML=-328.0 (up from a much worse starting-heuristic LML). Fitted lengthscales,
raw units and normalized by each dimension's own training-fold std (the only way to compare across
km-scale spatial dims and log-ppm-scale geochemical dims):

| dim | ell (raw) | ell / std(dim) |
|---|---|---|
| x_km | 317.4 | 4.26 |
| y_km | 1575.4 | **19.01** (effectively pruned) |
| As_ppm | 2.31 | 3.77 |
| Sb_ppm | 2.51 | 4.19 |
| Ag_ppm | 2.34 | 3.77 |
| Cu_ppm | 1.55 | **3.32** (shortest of all 6 pathfinder dims) |
| Zn_ppm | 5.01 | **12.32** (effectively pruned) |
| Tl_ppm | 1.08 | 4.26 |

**Aggregate result matches Carlin pathfinder theory, but the individual ranking is more nuanced
than a clean confirmation.** Mean ell/std: Carlin pathfinders (As/Sb/Tl) 4.08 vs. base metals
(Ag/Cu/Zn) 6.47 — pathfinders shorter (more informative), as `mining_mpdok`'s README predicts. But
that aggregate is driven almost entirely by Zn's outlier long lengthscale (12.32, effectively
pruned) dragging the base-metal mean up — individually, Cu (3.32) is actually the *shortest*
lengthscale of all six pathfinder dimensions, shorter than every one of As/Sb/Tl, and Ag (3.77)
ties with As. Reported plainly rather than rounded to a clean story: **Cu > As ≈ Ag > Sb ≈ Tl >> Zn**
by informativeness, not a clean "arsenian-pyrite trio beats base metals" split. One plausible read
(not verified further): Cu is a common byproduct/associated element in many Nevada-region deposit
types beyond Carlin-style gold specifically, so its informativeness here may reflect broader
mineralization signal rather than being wrong about Carlin pathfinder theory specifically — flagged
as a hypothesis, not confirmed.

**Also found, unprompted**: `y_km` (roughly north-south) got pruned far harder than `x_km`
(roughly east-west) — 19.0 vs. 4.3 in std-normalized units. Plausibly consistent with the Carlin
Trend's own geometry (`mining_mpdok`'s README/maps describe it as a NNW-SSE corridor — gold
anomalies would vary sharply *across* the corridor but more smoothly *along* its strike), but this
wasn't independently checked against the trend's actual azimuth and is reported as a suggestive
pattern, not a verified geological finding.

**Adding pathfinders roughly doubles average precision for both models** (50-seed comparison, fixed
ARD lengthscales / SVM gamma): GPC-ARD AP 0.493±0.063 (vs. Phase 1's spatial-only 0.240±0.053),
SVM AP 0.439±0.068 (vs. 0.082±0.035) — both models benefit substantially from the geochemistry, as
expected. **The confident-wrong gap narrows but does not close**: GPC-ARD 39.0% [36.9,41.1] vs.
SVM 77.5% [75.8,79.2] — a 38.5pp gap, smaller than Phase 1's spatial-only 47.0pp but still large and
non-overlapping. Consistent with `place_gpc_lab`'s own finding that more/better features narrow but
don't eliminate SVM's overconfidence — supports the Phase 3 conclusion that the calibration gap is
substantially intrinsic to the Laplace-vs-Platt mechanism, not purely a signal-starvation artifact.

**Follow-up (2026-07-17, `economic_layer_pathfinder.py`) — does Phase 4 move the Phase 2 dollar
result?** Reran Phase 2's exact ranked top-k campaign economics (unchanged $1M/target, $50M/HG
discovery, same k_econ grid) on spatial+pathfinder-ARD-ranked candidates, using the lengthscales
already fit above (no refit). 200 seeds, k=50 headline:

| | HG found @ k=50 | Net value @ k=50 |
|---|---|---|
| Spatial-only (Phase 2) | GPC 12.3 / SVM 3.8 | GPC $565M / SVM $142M / Random $65M — **gap $423M [$396M,$450M]** |
| Spatial+pathfinder ARD | GPC-ARD 23.6 / SVM 22.5 | GPC-ARD $1,132M / SVM $1,076M / Random $65M — **gap $56M [$47M,$66M]** |

**The economic gap narrows far more (7.5x) than either AP or the confident-wrong rate would
suggest.** Both models' absolute net value roughly doubles-to-triples with pathfinders (consistent
with AP roughly doubling for both), but the *gap between them* nearly closes — still real (paired
CI excludes zero cleanly) but small relative to Phase 2's headline number. Read: **ranking quality
at the very top of a candidate list converges faster than calibration quality does.** With richer
features, the "obviously anomalous" points near the top of a 50-target campaign become easy for
either model to rank correctly — that's what the top-k economic model measures, and it doesn't
penalize a miss any differently based on how confident the wrong call was. The confident-wrong rate
(39.0% vs. 77.5%, unchanged by this follow-up) is a genuinely different, still-large signal that
the ranked-campaign dollar figure doesn't capture: SVM is still far more likely to be badly
miscalibrated on whichever points it does miss, even once both models are similarly good at the
top of the list. The two metrics tell different parts of the story; pathfinders close one much
faster than the other.

**Phase 5 (stretch, optional) — three-way baseline vs. FRK.** `mining_phase2.npz`/`mining_phase3.npz`
already hold FRK's continuous grade predictions on this data. Threshold them at the same P95 cutoff
to get an (imperfect, not-actually-a-classifier) FRK ore/waste call, and add it to the Phase 1/2
tables as a third column. Flag clearly that this is a repurposed regression output, not a
calibrated classifier — no confidence score exists for it beyond the raw predicted grade's distance
from cutoff, so it can only join the accuracy comparison, not the confident-wrong one.

## Risks / honest unknowns (stating up front, not discovering later)

- **P95 is a proxy cutoff, not a real mine's economic cutoff grade.** Every dollar figure in Phase 2
  inherits this — report it as "under a P95-cutoff assumption," not as a claim about the actual
  Carlin Trend's economics.
- **Severe class imbalance** (~5% positive at P95) means per-seed test-set positive counts will be
  small; Phase 1's bootstrap needs pooling across seeds even more than `place_gpc_lab`'s did, and
  stratified splitting is not optional here. **Confirmed and resolved in Phase 1**: it's worse than
  "small counts" -- `P(ore)` never crosses 0.5 for either model, making threshold-0.5 metrics
  (accuracy, recall, precision) fully degenerate. Average precision (threshold-free) is now the
  primary metric; **Phase 2 sidestepped the threshold problem entirely** by reusing `mining_mpdok`'s
  own ranked top-k campaign economic model, which needs no threshold at all (see Phase 2 result).
- **Stream-sediment Au is a weak, indirect proxy for actual ore grade** (drainage geochemistry, not
  drillhole assay) — `mining_mpdok`'s own spatial-holdout result already found even MPDOK gets only
  6.5% improvement at HG sites over 26–55km gaps. A classifier built on this data inherits that
  ceiling; Phase 2's dollar figures are illustrative of the *methodology*, not a real go/no-drill
  recommendation.
- **Phase 3's masking-effect prediction did NOT replicate for classification calibration**
  (resolved, see Phase 3 result) — the confident-wrong gap narrowed, not widened, as the nugget
  dropped from 55.7% to 5.9%. Read as evidence the Phase 1/2 finding is an intrinsic Laplace-vs-Platt
  calibration property rather than a masking artifact, not as a contradiction of Phase 1/2.

## Structure

```
mining_gpc_lab/
  LAB_PLAN.md              this file
  datasets.py               DONE -- loads nevada_nure_raw.csv, reproduces Carlin Trend filter + P95
                             label, stratified splits (spatial / spatial_pathfinder variants)
  run_lab.py                DONE -- ell grid (selected on validation AP) -> GPC + SVM fit ->
                             results/mining_gpc_seed<n>_<feature_set>.json (Phase 1)
  confidence_study.py       DONE -- 200-seed pooled bootstrap, spatial-only ->
                             results/confidence_study_spatial.json (Phase 1)
  economic_layer.py         DONE -- ranked top-k drilling campaign (mining_mpdok's own economic
                             model, $1M/target, $50M/HG discovery, k_econ grid) -> GPC vs SVM vs
                             random net value, paired bootstrap CI ->
                             results/economic_layer_spatial.json (Phase 2)
  masking_crossover.py      DONE -- regenerates 03_mpdok.ipynb's nested-Matern field (unchanged
                             kernel params/seed) at the full 4,106-point Carlin Trend set, refits
                             both classifiers, compares confident-wrong gap real-Au vs synthetic ->
                             results/masking_crossover.json (Phase 3)
  pathfinder_ard.py         DONE -- LML-maximizing Nelder-Mead over 8 ARD lengthscales + sigma_f
                             (../gp_hyperopt.py's convention, now applied to LaplaceBinaryGPC),
                             GPC-ARD vs SVM 50-seed comparison ->
                             results/pathfinder_ard.json (Phase 4)
  economic_layer_pathfinder.py  DONE -- reruns Phase 2's exact top-k campaign economics on
                             spatial+pathfinder-ARD-ranked candidates (loads the fitted ell/gamma
                             from pathfinder_ard.json, no refit) -> GPC-ARD vs SVM vs random net
                             value, paired bootstrap CI -> results/economic_layer_pathfinder.json
                             (Phase 4 follow-up)
  frk_baseline.py            thresholds mining_phase2/3.npz FRK predictions at P95 (Phase 5,
                             stretch) -- not started
  build_notebook.py         DONE -- results/*.json -> MINING_GPC_LAB.ipynb (Phases 1-4 + economic
                             pathfinder follow-up)
  MINING_GPC_LAB.ipynb      DONE -- executed, 0 errors, 8 charts render (Phases 1-4 + follow-up)
  results/
    mining_gpc_seed0_spatial.json
    confidence_study_spatial.json
    economic_layer_spatial.json
    masking_crossover.json
    pathfinder_ard.json
```

Engine dependency: `../gp_classifier.py`'s `LaplaceBinaryGPC` -- **now ARD-capable (2026-07-17,
this lab's Phase 4)**: `ell` accepts a scalar (isotropic, bit-identical to the pre-ARD code, still
what `mnist_gpc_lab`/`place_gpc_lab`/this lab's Phases 1-3 use) or a length-d vector (ARD, new).
This is a real, reusable engine change, not a lab-local workaround -- any future classification lab
needing per-dimension lengthscales can use it unchanged. Data dependency:
`.../MPDOK/mining_mpdok/nevada_nure_raw.csv` + `mining_phase{1,2,3,5}.npz` (read-only, no changes to
`mining_mpdok` itself). No new Rust/CUDA work — pure Python, in-core (n=4,106 Carlin Trend samples,
nowhere near OOC territory).
