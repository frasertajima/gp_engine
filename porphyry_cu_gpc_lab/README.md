# porphyry_cu_gpc_lab — Laplace GPC vs. SVM on ore/waste classification, Arizona porphyry Cu(-Mo)

**Status:** Phase 0 DONE (2026-07-18) — `datasets.py` loads the multi-state CSV, filters to Arizona
(whole-state, per the recommendation below), derives the Cu P95 cutoff label (133.50 ppm, 5.0% ore
— 385/7,633), and produces `spatial` (d=2) and `spatial_pathfinder` (d=8: Mo/Re/Au/Ag/Pb/Zn)
feature sets with stratified splits holding the ore rate steady. **Real data-quality finding
handled, not glossed over**: Re_ppm is 91.3% below detection in this dataset (physically sensible —
Re only shows up near real molybdenite mineralization) and Au_sq_ppm is 9.9% below detection; both
floor-imputed (half the column's minimum positive value) before log-transforming rather than
dropped, so a pathfinder's censoring rate doesn't shrink the primary Cu dataset the way dropping
those rows would have. **Phase 1 DONE (2026-07-18)** — see "Phase 1 result" below: the pattern
replicates on a genuinely different commodity/geology/dataset. GPC AP 0.278±0.042 vs. SVM
0.104±0.046 (200 seeds); confidently-wrong-on-a-miss GPC 46.7% [45.9,47.6] vs. SVM 93.3%
[92.1,94.5] — same order of magnitude as gold's 47.0pp gap, just as statistically robust. **Phase 2
DONE (2026-07-18)** — skipped straight to `bayesian_decision_lab`'s sequential value-of-information
framework, per Fraser's direction, rather than rebuilding ranked-campaign economics from scratch.
This required refactoring `decision.py`/`voi.py` out of `bayesian_decision_lab/` into `gp_engine/`
as genuinely shared modules first (verified the refactor changed nothing — both labs reproduce
their exact prior numbers). GPC-full wins again ($8,820.6M vs. SVM $8,751.8M vs. GPC-mean $8,705.8M,
200 seeds) but **the runner-up flips from gold's ranking** (there, mean-only beat SVM; here, SVM
beats mean-only) — reported plainly as a real, dataset-dependent difference, not forced to match
gold's story. Cost/benefit accounting confirms the same "cheap insurance against drilling into
waste" mechanism as gold, at a larger dollar scale. **`PORPHYRY_CU_GPC_LAB.ipynb` built and executed
(2026-07-18)** — 4 charts covering Phase 1 (AP/reliability, confident-wrong bars) and Phase 2
(sequential-VoI realized-value/action-mix, cost/benefit breakdown), 0 errors, one real
transcription-risk caught and fixed along the way (a bootstrap `rng` reuse across GPC/SVM calls
that silently shifted SVM's resample sequence vs. `confidence_study.py`'s own convention — fixed
before finalizing, now matches the script's actual printed output exactly: 92.1%, not 92.2%).
Phases 3-4 not started (lab considered wrapped up at this stage per Fraser's direction). Data
sourcing — the
part Fraser flagged as likely the real effort — was done in
the previous session: see `data/SOURCES.md`. First candidate from
`gp_engine/EXPLORATION_APPLICATIONS_ROADMAP.md`'s ranked list ("do porphyry copper first if the
goal is validating the pattern generalizes cheaply") — that validation now has a real answer: yes.

**One line:** the same confident-wrong / economic-value / cost-ratio-sweep / value-of-information
question `mining_gpc_lab` and `bayesian_decision_lab` already answered for Carlin Trend gold, asked
of a genuinely different commodity, geology, and (crucially) a different, richer pathfinder-element
theory — Arizona porphyry copper-molybdenum, USGS NURE-HSSR reanalysis data, no new data collection.

## Data (found and verified, 2026-07-18 — see `data/SOURCES.md` for the full account)

`data/nure_multistate_az_ca_id_mt_nv_nm_ut_or.csv` — same USGS "NURE-HSSR reanalysis" program
`mining_gpc_lab`'s Nevada file came from, but multi-state (AZ/CA/ID/MT/NV/NM/UT/OR, 54,157 records
total). Same 65-column schema, same 51-element ALS ME-MS61L ICP-MS suite, same QC protocol.

**Arizona subset: 7,633 samples** (comparable scale to Carlin Trend's 4,106) — the classic US
porphyry copper province: Morenci, Bagdad, Ray, Miami-Globe, Safford, Resolution/Superior,
Sierrita/Twin Buttes, Mission, Silver Bell are all Arizona porphyry Cu(-Mo) deposits.

**Already sanity-checked, not just downloaded**: the 20 highest-Cu_ppm AZ samples cluster in the
TUCSON quadrangle (32.4-32.7°N, -111.4 to -111.1°W — Sierrita/Twin Buttes/Mission) and the MESA
quadrangle (33.4°N, -110.8°W — Superior/Resolution/Miami-Globe) — real known districts, the same
kind of built-in geographic validation the Carlin Trend bounding box had. Cu_ppm p95=133.5,
max=19,000 (1.9%, a genuinely huge anomaly); Mo_ppm p95=4.47, max=2,540 ppm; Re_ppm and Au_sq_ppm
both present with real dynamic range (many Arizona porphyries are Cu-Au, not just Cu-Mo).

**A real, not-yet-resolved geographic question, unlike Carlin Trend's clean linear corridor**:
Arizona's porphyry belt is scattered across the state (Morenci in the far east, Bagdad in the
northwest, the Globe-Miami-Superior-Ray-Sierrita cluster in the south-central counties), not one
tight corridor. Two honest options, not yet decided:
1. **Whole-state Arizona** (all 7,633 samples) — simpler, more data, no district-boundary research
   needed, but "ore" anomalies could include non-porphyry Cu sources (skarns, veins, basalt-hosted
   Cu) that happen to share the same stream-sediment signature.
2. **A tighter named cluster** (e.g. Globe-Miami-Superior-Ray-Sierrita-Twin Buttes-Mission, roughly
   32.3-33.5°N / -111.3 to -110.6°W, the same corridor the Cu-anomaly clustering above already
   points to) — closer in spirit to Carlin Trend's own bounded-province framing, but needs real
   district-boundary research before committing to exact coordinates, not just eyeballing the top-20
   table above.
**Recommendation: start with whole-state Arizona for Phase 0/1** (matches this lab's own "cheap
validation first" rationale from the roadmap document) and revisit a tighter district bounding box
only if the whole-state signal turns out too diluted by non-porphyry Cu sources to be useful.

## What's identical to `mining_gpc_lab`, reusable near-verbatim

- `LaplaceBinaryGPC` (now ARD-capable) and `SVC` — same engine, unchanged.
- `datasets.py`'s load/filter/label/split pattern — same NURE-HSSR schema, same negative-value
  (below-detection) cleaning convention, same P95-cutoff labeling approach (though the caveat that
  P95 is a proxy for a real economic cutoff grade, not a sourced one, applies here too — arguably
  more so, since porphyry Cu cutoff grades are a well-documented ~0.15-0.4% Cu in real operations,
  a number this lab could actually compare its P95 threshold against, unlike gold's less
  standardized cutoff).
- The Phase 1-4 structure (confident-wrong replication -> ranked-campaign economics -> masking
  crossover -> ARD pathfinder lengthscales) and the average-precision pivot (expect the same class-
  imbalance-at-P95 finding to recur; not yet confirmed for this dataset specifically).
- `bayesian_decision_lab`'s entire framework (payoff matrix, Bayes action rule, sequential
  value-of-information Probe, cost-ratio sweep) is now a **generalizable, reusable asset** — it
  takes any fitted `LaplaceBinaryGPC`/`SVC` pair and a payoff matrix, not anything Carlin-Trend- or
  gold-specific. This lab could reuse it far sooner than `mining_gpc_lab` built its own decision
  layer from scratch, if the economics are worth modeling here too.

## What's new or needs real work

- **Pathfinder theory is genuinely different, not just relabeled**: porphyry Cu-Mo systems follow
  the classic Lowell & Guilbert (1970) concentric zoning model — a proximal Cu-Mo-bearing potassic
  core surrounded by a distal Pb-Zn-Ag-Au(-Mn-As-Sb) halo. Unlike Carlin Trend (where As/Sb/Tl were
  the pathfinders *for* gold), here **Mo and Re are the paired economic/pathfinder elements for Cu
  itself** (Re strongly partitions into molybdenite, a well-established Mo-deposit pathfinder), and
  Au/Ag are often co-products rather than pure pathfinders (many Arizona porphyries are Cu-Au or
  Cu-Mo-Au). This needs its own literature grounding before an ARD phase claims anything about which
  elements "should" be informative — don't just copy Carlin's As/Sb/Tl framing onto Cu/Mo without
  checking it applies. (Not yet done — flag for Phase 4-equivalent, not Phase 0.)
- **Economic constants need their own derivation, not reused from gold.** `mining_mpdok`'s
  $1M-drill/$50M-discovery constants were for gold prospect drilling; porphyry Cu targets are
  typically larger, deeper, bulk-tonnage systems (bigger holes, bigger footprints) — a real
  cost/value pair for this commodity should be derived (even if still illustrative/order-of-
  magnitude, per this project's established honesty convention), not copy-pasted from the gold lab.
- **State-vs-district bounding-box decision** (above) needs resolving before Phase 1, not deferred
  indefinitely — whole-state is the pragmatic Phase 0/1 default, but should be revisited honestly if
  results look diluted.

## Proposed phases (mirroring `mining_gpc_lab`, not yet started)

- **Phase 0** — `datasets.py`: load the multi-state CSV, filter to Arizona (or the tighter cluster,
  once/if decided), define the Cu P95 (or a jointly Cu+Mo anomaly score — worth trying both) cutoff
  label, stratified splits. Reuse `mining_gpc_lab/datasets.py`'s structure directly.
- **Phase 1 — DONE (2026-07-18), see "Phase 1 result" below.** GPC vs. SVM confident-wrong
  replication + average precision (same methodology, same 200-seed bootstrap convention).
- **Phase 2** — ranked top-k campaign economics, with porphyry-Cu-appropriate cost/value constants
  (to be derived, not reused from gold) — or, given `bayesian_decision_lab` now exists as a
  generalizable asset, consider going straight to a Bayes decision-rule framing (Skip/Probe/Drill)
  instead of re-deriving the simpler ranked-campaign version first. Worth deciding deliberately, not
  defaulting to "redo it exactly like mining_gpc_lab out of habit."
- **Phase 3** — masking crossover (does GPC's advantage survive/change under a synthetic
  lower-nugget control) — only worth doing if it adds new information beyond what `mining_gpc_lab`
  already established about the general mechanism; could be skipped or shortened if it would just
  re-confirm the same intrinsic-calibration-property finding.
- **Phase 4** — pathfinder ARD (Mo/Re/Au/Ag/Pb/Zn lengthscales vs. Cu), grounded in real porphyry
  zoning literature first, not assumed.

## Phase 1 result (2026-07-18)

`run_lab.py --seed 0` (spatial-only, d=2): same degenerate-threshold-at-0.5 pattern found before —
`P(ore)` never crosses 0.5 for either model at this ~5.0% prevalence, confirming Phase 0's
imbalance carries the same consequence as `mining_gpc_lab`'s gold data. `ell=100.27` km selected on
validation AP (Matern-3/2). Seed-0 test: **GPC AP=0.242 vs. SVM AP=0.153**.

`confidence_study.py --n-seeds 200`: **average precision, mean over 200 seeds: GPC 0.278 ± 0.042
vs. SVM 0.104 ± 0.046** (~2.7x, non-overlapping). **Confidently-wrong-on-a-miss rate (pooled, 95%
bootstrap CI): GPC 46.7% [45.9%,47.6%] vs. SVM 93.3% [92.1%,94.5%]** (7,212/15,429 vs.
14,378/15,404 missed-ore points carried >90% confidence in the wrong "waste" call) — a ~46.6pp gap,
slightly narrower than gold's 47.0pp but the same order of magnitude and just as statistically
robust (tight, non-overlapping CIs from 200 seeds × ~77 test-set ore points).

**The pattern replicates on a genuinely different commodity, geology, and dataset** — this is
exactly the question `EXPLORATION_APPLICATIONS_ROADMAP.md` set out to answer cheaply, and the
answer is yes: Laplace GPC's calibration advantage over SVM is not Carlin-Trend- or gold-specific.
SVM's Platt-scaled probability is, once again, essentially always overconfident on the misses it
does make; GPC's Laplace posterior is roughly half as likely to be that overconfident on its own
misses, closely mirroring the gold lab's numbers despite a different commodity, different pathfinder
elements, a different (roughly 1.86x larger) sample size, and no fitted variogram to anchor the
kernel choice this time.

## Phase 2 result (2026-07-18) — skipped straight to `bayesian_decision_lab`'s framework

Per Fraser's direction (2026-07-18): rather than rebuild a ranked-top-k economic layer from
scratch, this phase reused `bayesian_decision_lab`'s sequential value-of-information framework
directly. **This required a real refactor first, done before any porphyry-specific code was
written**: `decision.py` and `voi.py` were dataset-agnostic already (pure functions of `p`/`mean`/
`var`/a payoff matrix, no `mining_gpc_lab`-specific code anywhere in them) but lived inside
`bayesian_decision_lab/`, coupled to that lab's own `models.py` import order. Moved both to
`gp_engine/` as genuinely shared modules — every script that used them needed one `sys.path.insert`
line added (the import order previously relied on `models.py` being imported first as a side
effect, which broke once `decision`/`voi` left the same directory); `decision.py`'s own self-test
was also decoupled from `mining_gpc_lab`'s specific fitted models to a synthetic P(ore)/label pair,
since a shared module's self-test can't depend on any one lab's data. Verified the refactor changed
nothing: `bayesian_decision_lab/run_lab.py --seed 0` and `run_voi.py --seed 0` reproduce their
pre-refactor numbers exactly after the move. This is the foundation for extending the Bayesian
decision framework further (Fraser's stated longer-term goal) — it now has exactly one home, not
one copy per lab.

**Porphyry-specific payoff constants, derived not reused from gold**: `run_voi.py`'s docstring has
the full reasoning — bigger, deeper porphyry drill holes ($2M vs. gold's $1M) and proportionally
larger bulk-tonnage discovery value ($150M vs. $50M gross), same relative Probe:Drill ratios as
gold since neither commodity's absolute numbers were rigorously sourced to begin with. Verified
(not assumed) that Probe still has a genuine P(ore) niche (0.0067-0.0141) under these constants
before running anything.

**Structural prediction confirmed exactly again**: SVM and GPC-mean-only chose Probe zero times
across all 200 seeds — the same mathematical guarantee (paying to learn nothing is never optimal
when a condition's own variance is zero by construction) that held for gold.

**Headline ranking, 200 seeds — GPC-full wins again, but the runner-up flips, and that's worth
reporting plainly rather than forcing it to match gold's story:**

| condition | realized $ (mean ± std) | vs. SVM | vs. GPC-mean |
|---|---|---|---|
| SVM | $8,751.8M ± $126.1M | — | — |
| GPC-mean-only | $8,705.8M ± $163.3M | **−$45.9M** [−$74.1M,−$18.9M] | — |
| GPC-full-posterior | $8,820.6M ± $85.7M | +$68.8M [$48.5M,$89.2M] | +$114.8M [$88.9M,$141.5M] |

In the gold lab, the ranking was GPC-full > GPC-mean > SVM. **Here it's GPC-full > SVM > GPC-mean**
— the naive variance-blind plug-in is robustly *worse* than SVM on this dataset, the opposite of
what it was on gold's. Both CIs are tight and don't cross zero, so this isn't noise. Read plainly:
**the only thing that generalized across both commodities is that the full, correctly-integrated
posterior (GPC-full) comes out ahead — which naive simplification is the "second-best" one is
dataset-dependent, not a general fact about GP calibration.** This is arguably a cleaner, more
defensible version of the lab's core claim than if the full ranking had matched exactly: it isolates
what's actually robust (proper Bayesian treatment) from what was probably a dataset-specific
coincidence in the gold lab (naive-mean-beats-SVM).

**Cost/benefit accounting for GPC-full's Probe option (200 seeds)**: value added by having Probe
available, **$235.8M/seed [$220.1M,$252.2M]** (robust) — larger in absolute terms than gold's
$57.3M/seed, consistent with porphyry's ~3x larger payoff scale and larger test set. **Same
"cheap insurance against drilling into waste" mechanism as gold, even more skewed**: of the sites
probed, ~166.5/seed are true waste and only ~1.0/seed is true ore. Those same sites would have lost
real money if drilled directly (−$189.4M/seed) or scored exactly $0 if skipped; probing them
instead nets +$126.8M/seed at a cost of $16.75M/seed. The mechanism replicates cleanly across both
labs; only the absolute dollar scale differs, as expected.

## Structure (planned)

```
porphyry_cu_gpc_lab/
  LAB_PLAN.md              this file
  data/
    nure_multistate_az_ca_id_mt_nv_nm_ut_or.csv   DONE -- downloaded 2026-07-18, 54,157 records
    SOURCES.md                                     DONE -- full provenance, stats, sanity check
  datasets.py               DONE -- loads nure_multistate CSV, filters to Arizona (whole-state),
                            Cu P95 cutoff label, floor-imputes below-detection pathfinder values
                            (Re 91.3%, Au 9.9% below detection -- handled, not dropped), stratified
                            splits (spatial / spatial_pathfinder variants)
  run_lab.py                DONE -- ell grid (selected on validation AP) -> GPC + SVM fit ->
                            results/porphyry_gpc_seed<n>_<feature_set>.json (Phase 1)
  confidence_study.py       DONE -- 200-seed pooled bootstrap, spatial-only ->
                            results/confidence_study_spatial.json (Phase 1)
  models.py                 DONE -- reproduces this lab's own frozen seed-0 spatial fit (GPC
                            ell=100.27/matern32, SVM gamma=4.97e-05), same convention
                            `bayesian_decision_lab/models.py` established for mining_gpc_lab
  run_voi.py                DONE -- Phase 2: single-seed sequential-VoI 3-condition comparison,
                            porphyry-specific payoff constants ($2M/$150M drill, $0.1M/$15M probe)
                            -> results/voi_seed<n>.json
  bootstrap_voi.py          DONE -- Phase 2: 200-seed pooled comparison + Probe cost/benefit
                            accounting -> results/bootstrap_voi.json
  build_notebook.py         DONE -- results/*.json -> PORPHYRY_CU_GPC_LAB.ipynb (Phase 1:
                            AP/reliability + confident-wrong bars; Phase 2: sequential-VoI
                            realized-value/action-mix bars, cost/benefit breakdown)
  PORPHYRY_CU_GPC_LAB.ipynb  DONE -- executed, 0 errors, 4 charts render (Phases 1-2)
  (further phases as decided above)
  results/
    porphyry_gpc_seed0_spatial.json
    confidence_study_spatial.json
    voi_seed0.json
    bootstrap_voi.json
```

Engine dependency: `../gp_classifier.py`'s `LaplaceBinaryGPC` (unchanged), and — **new as of
2026-07-18** — `../decision.py`/`../voi.py`, moved out of `bayesian_decision_lab/` specifically so
this lab (and any future one) could reuse the sequential value-of-information framework without
copying it. Both are now genuinely shared, dataset-agnostic modules living at the `gp_engine/` level
alongside `gp_classifier.py`/`gp_core.py`, not lab-local files. No new engine code beyond that move
— same pattern as every prior lab in this family, now with one more shared piece.
