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
files load live, no hand-transcribed numbers, 0 execution errors. Phases 4-5 (stretch) not started.

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

**Phase 4 (stretch) — pathfinder ARD.** **Engine gap found while writing Phase 1 (2026-07-17):**
`gp_classifier.py`'s `LaplaceBinaryGPC` takes a *scalar* `ell` (isotropic kernel only) --
`gp_core.py`'s regression path has per-dimension ARD lengthscales, but that was never ported to the
classifier. `spatial_pathfinder_features` (d=8, in `datasets.py` already) can be fit today with an
isotropic kernel over standardized features, but that's not ARD and won't produce the
per-pathfinder-element lengthscale report this phase wants. Two ways to get real ARD: (a) extend
`LaplaceBinaryGPC` to accept a vector `ell` (small, contained change -- `_squared_dist_matrix`
would need per-dimension scaling before the existing distance computation, same identity
`gp_core.py`'s ARD kernel already uses); (b) pre-scale each feature column by a fitted per-dim
lengthscale before calling the existing isotropic kernel, fit via a coordinate-descent-style outer
loop -- cruder, no engine change needed. (a) is the more reusable fix (benefits any future
classification lab needing ARD) and is the preferred option when this phase is picked up. Once
built: check whether the fitted lengthscales rank As/Sb/Tl as more informative than Cu/Zn/Ag (Carlin-
type deposits have known pathfinder theory -- As/Sb/Tl co-occur with invisible gold in arsenian
pyrite, per `mining_mpdok`'s own README), an independent geochemical sanity check on the model, not
just an accuracy number. Also check whether adding pathfinder dims narrows the Phase 1
confident-wrong gap (more informative features could make SVM's overconfidence problem less
visible, or could make no difference if the gap is calibration-method-intrinsic as
`place_gpc_lab`'s retrain experiment suggested).

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
  pathfinder_ard.py          d=8 ARD fit + lengthscale report (Phase 4, stretch) -- blocked on the
                             LaplaceBinaryGPC scalar-ell gap noted above; not started
  frk_baseline.py            thresholds mining_phase2/3.npz FRK predictions at P95 (Phase 5,
                             stretch) -- not started
  build_notebook.py         DONE -- results/*.json -> MINING_GPC_LAB.ipynb
  MINING_GPC_LAB.ipynb      DONE -- executed, 0 errors, all 4 charts render
  results/
    mining_gpc_seed0_spatial.json
    confidence_study_spatial.json
    economic_layer_spatial.json
    masking_crossover.json
```

Engine dependency: `../gp_classifier.py`'s `LaplaceBinaryGPC` (unchanged, third reuse after
`mnist_gpc_lab`/`place_gpc_lab`; scalar-`ell` isotropic kernel only -- see Phase 4 for the ARD gap
found here). Data dependency: `.../MPDOK/mining_mpdok/nevada_nure_raw.csv` +
`mining_phase{1,2,3,5}.npz` (read-only, no changes to `mining_mpdok` itself). No new Rust/CUDA work
— pure Python, in-core (n=4,106 Carlin Trend samples, nowhere near OOC territory).
