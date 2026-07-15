# GBLUP Lab — Phase 4 results (the real 2024 held-out season)

**Date:** 2026-07-15. **Trigger:** Fraser asked to fetch the G2F competition's
real 2024 test data after Phase 3 was already written, explicitly to get a
genuine (not simulated) held-out-season result, and asked that it be noted
the data was **downloaded after** every earlier phase's results and code were
already committed to `RESULTS_PHASE0.md`–`RESULTS_PHASE3.md`. That's true by
construction here: nothing in this file's data existed on disk, nor was
consulted in any form, when Phases 0–3 were run.

## Where the data came from (found, not guessed)

CyVerse, DOI `10.25739/78mn-4394` → resolved to
`datacommons.cyverse.org/.../GenomesToFields_GenotypeByEnvironment
_PredictionCompetition_2025/`. Confirmed via WebDAV directory listing
(`curl` against `data.cyverse.org/dav-anon/iplant/projects/commons_repo/
curated/.../`), not assumed from the competition website (which had no
working download links). Downloaded, saved to `gblup_lab/data/` (a new
directory — MPDOK's own `gblup/data/` was left untouched, non-goal honored):

- `Testing_data/7_Testing_Observed_Values.csv` — real 2024 yield, 9,486
  plot records, 1,063 unique hybrids, 22 environments. The competition
  paper's own words: released "to allow post-competition model validation."
- `Training_data/5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt` — the
  actual competition-curated hybrid genotype panel: **5,899 hybrids × 2,425
  markers**, additive dosage already coded at the hybrid level ({0, 0.5, 1}
  — 0.5 where the two parents differ, which is exactly the averaged-parent-
  dosage approximation Phase 3's `g2f_hybrid.py` built by hand, confirming
  that approximation was mathematically the right one). Covers **100% of the
  1,063 2024 test hybrids** and 4,940/5,205 (95%) of the 2014–2023 training
  hybrids — much better coverage than Phase 3's 4,979-hybrid subset, which
  was limited to hybrids whose parents were both in the smaller 2,193-inbred
  panel MPDOK had already parsed.
- 3.18% of genotype entries are missing; mean-imputed per marker (flagged,
  not hidden — `g2f_2024_eval.py::load_genotypes`).

## Protocol — the real thing this time

Train: 4,938 hybrids, 2014–2023 (mean yield per hybrid across all its
plot records in that period). Test: 1,063 hybrids, **2024, a genuinely new
season** — 104 hybrids appear in both (repeated checks across years, common
in breeding trials; their 2024 records are never used for training, only
their pre-2024 records are, so there's no leakage). Hyperparameters (linear
and RKHS, same `gblup_hyperopt.py` as every earlier phase) fit by marginal
likelihood on **2014–2023 data only** — no access to 2024 at any point
during fitting, exactly the no-peeking discipline Phase 1 established.
Predict once, on the fixed fitted model, for the 1,063 2024 hybrids.

## Results

| model | r (2024 held-out) | NLL median | pathological pts |
|---|---|---|---|
| linear (from-X, normalized) | 0.2713 | 0.924 | 6/1063 |
| RBF | 0.4084 | 0.979 | 0/1063 |
| Matérn-3/2 | 0.4148 | 0.978 | 0/1063 |

RKHS gain over linear: **+0.137 to +0.144 r** — noticeably larger than
Phase 2/3's literature-anchored 0.01–0.09 range.

## Two honest things about these numbers

**1. This is a much harder, more realistic task than Phase 3, and the drop
in r reflects that, not a regression.** 2024 was a genuinely different
season — its mean yield (10.77 Mg/ha) is a full 0.9 std above the
2014–2023 training mean (9.51 Mg/ha), i.e. real distribution shift from
weather/agronomy/genetic-gain-over-time, none of which a marker-only model
sees. Phase 3's r≈0.73–0.78 was "known parents, unseen combination, same
era"; this is "unseen combination, unseen era" — the actual shape of the
real competition's problem, just scored without the weather/soil/EC
covariates that real competitive entries used. r≈0.27–0.41 is a plausible,
honest number for a genomics-only model under real distribution shift, not
a failure.

**2. The larger RKHS-over-linear gain here is plausible but not
independently verified, and it shouldn't be read as contradicting Phase
2/3's literature check.** de los Campos et al. (2010)'s 0.01–0.09 r figure
was measured on *within-population* interpolation (same wheat trial series,
random CV) — a different regime from *across-season extrapolation*. A
nonlinear kernel plausibly regularizes better under real distribution shift
than a linear one (this is a reasonable mechanism, not a stretch), but that
specific claim — "RKHS extrapolates better than linear GBLUP across novel
seasons, by this much" — hasn't been checked against a primary source the
way Phase 2's number was. Flagging it as an open, interesting, unverified
finding rather than folding it into the literature-consistency story.

## Not compared to the competition leaderboard, on purpose

This is a marker-only model with no weather, soil, or environmental
covariate data — the real competition's genuinely competitive entries used
all of those (that's the entire point of a "genotype-by-**environment**"
prediction competition). Comparing our r≈0.27–0.41 to a leaderboard entry
that had access to weather data would be comparing different problems, not
a fair engine benchmark. What Phase 4 legitimately establishes: gp_engine
can fit and predict genuinely held-out-season genomic-only breeding values,
end to end, on real competition data, without touching the test set during
fitting — the plumbing and the no-peeking MLE discipline both hold up
outside the comfortable random-CV setting every earlier phase used.

## Verdict

Real 2024 competition data, fetched and used correctly (temporal separation
honored, no leakage, coverage verified rather than assumed). A harder,
more honest evaluation than Phase 3's — and it shows: accuracy drops
substantially under real distribution shift, exactly as it should for a
covariate-free model. RKHS still beats linear, by more than the
within-population literature figure would predict; flagged as a real but
not-yet-independently-checked finding, not a headline claim.
