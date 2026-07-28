# Phase 0 results — does KW51 actually show the EOV confound and a real retrofit signal?

**Status: DONE (2026-07-28).** `data_kw51.py` (loader) / `phase0_run.py` / `results_phase0.json`.
Real data, not a synthetic oracle — this is the first lab in the soft-EM family where Phase 0 is
"does the real dataset show the mechanism," not "does our simulator produce it."

## What's actually in `trackedmodes.mat`

Confirmed by direct download and inspection (Zenodo DOI 10.5281/zenodo.3745914,
`trackedmodes.zip`, 12.9 MB) — not assumed from the page description this time:

- **11,328 hourly samples**, 2018-10-01 00:00 to 2020-01-15 23:00 — matches the dataset's stated
  ~15.5-month campaign.
- **14 tracked modes**: natural frequency (`f`), damping ratio (`xi`), and complex mode shape (`m`,
  12 sensor channels: 6 accelerometers on the bridge deck, 6 on the arches) per mode, per hour.
  Mode identification is not always successful every hour (automated operational modal analysis
  routinely drops out) — NaN fraction per mode ranges from 3.5% (best-identified mode) to 73%
  (worst).
- **11 environmental covariates** (`env`): deck temperature/humidity (`tBD31A`/`rhBD31A`), a
  weather-station temperature/humidity/vapour-pressure/radiation/rain/wind set (`*VL`) — richer
  than `LAB_PLAN.md`'s original draft description ("temperature and relative humidity"), genuinely
  includes solar radiation and wind, which the EOV literature (`research/01_...md`) also treats as
  real confounds, not just temperature.
- **Retrofit split** (using the real dates from `research/04_kw51_dataset_specifics.md`): 5,424
  pre-retrofit hours, 3,240 during-retrofit hours, 2,664 post-retrofit hours.
- **Deck temperature range: -2.98°C to 37.9°C** — comfortably spans the freeze/no-freeze boundary
  Peeters & De Roeck's Z-24 study found produces a bilinear frequency-temperature relationship;
  worth checking for the same bilinearity here in Phase 1, not assumed.

## Check 1 — is the EOV/temperature confound actually present in THIS bridge's data?

**Yes, confirmed directly — this claim was previously only verified generically (`research/01_...md`,
for a different bridge, Z-24). It now holds for KW51 specifically.** Among the five well-identified
modes (≤20% NaN — modes 2, 4, 5, 8, 12), correlation between tracked frequency and deck temperature
ranges from **essentially uncorrelated (mode 5: r=-0.103) to strongly correlated (mode 8:
r=-0.738)** — a real, substantial, mode-dependent confound, not a uniform effect. This mode-to-mode
variation is itself informative: any classical single-relationship correction fit across all modes
at once risks either under-correcting mode 8 or over-correcting mode 5.

| Mode (well-identified only) | NaN frac | corr(freq, temp) | Pre-retrofit mean (Hz) | Post-retrofit mean (Hz) | Shift |
|---|---|---|---|---|---|
| 2 | 5.0% | -0.553 | 1.8931 | 1.8821 | -0.58% |
| 4 | 12.1% | -0.644 | 2.5799 | 2.5712 | -0.34% |
| 5 | 3.5% | -0.103 | 2.9241 | 2.9845 | **+2.07%** |
| 8 | 7.1% | **-0.738** | 4.1088 | 4.0772 | -0.77% |
| 12 | 14.2% | -0.192 | 6.3258 | 6.4179 | +1.46% |

(Full 14-mode table, including the noisier modes, in `results_phase0.json`.)

## Check 2 — is there a real, visible signal across the retrofit window?

**Yes, but genuinely confounded with season — which is precisely this lab's whole point, observed
empirically now, not just argued for.** Mode 5, the mode with the *weakest* temperature
correlation, shows the *largest* clean shift (+2.07%), physically consistent with the retrofit's
stated purpose (strengthening the diagonal-to-arch/deck connections should stiffen the structure
and raise natural frequencies). Several less-well-identified higher modes (9, 10, 11, 13 — 32-57%
NaN, so noisier) also show +2% shifts, echoing the same direction.

**The honest complication**: the pre-retrofit window (Oct 2018-May 2019) spans a full
autumn-through-spring cycle, while the post-retrofit window (Sept 2019-Jan 2020) only covers
autumn-into-winter — the two windows have different temperature *distributions*, not just
different structural states. Mode 8's -0.77% pre/post shift, despite its strong temperature
correlation (-0.738), could plausibly be a seasonal-mix artifact rather than a real structural
change, and a naive "compare the pre/post average" classical check cannot tell these apart. **This
is the exact confound this lab's soft-EM regime-mixture hypothesis exists to address** — not
inferred from the literature this time, but observed directly in this dataset's own pre/post
window composition.

## What this means for Phase 1

- The classical baseline (Method 0, plain regression) and the GP methods must be fit and compared
  on **temperature-conditioned** pre/post comparisons, not raw pre/post means — otherwise the
  season-vs-retrofit confound above will bias any method's apparent detection performance in an
  uninteresting way that has nothing to do with GP vs. classical.
- Modes 2, 4, 5, 8, 12 (the well-identified ones) are the right starting subset for Phase 1's model
  fitting — the noisier modes' high NaN fractions are a data-quality problem orthogonal to this
  lab's EOV-vs-regime question and would need their own missing-data handling (a real, separate
  problem — GP regression for missing-data imputation in bridge SHM is itself a 2025 published
  technique per `research/03_...md`, worth reusing rather than reinventing if the noisier modes are
  needed later).
- Mode 5 is the strongest candidate for a clean "did we detect the real retrofit" test case (large
  real shift, weak temperature confound). Mode 8 is the strongest candidate for testing whether a
  method can correctly *avoid* a false read (strong temperature confound, small/ambiguous shift) —
  useful as a paired test, not just one or the other.

## Reminder

Per the disclaimer at the top of `LAB_PLAN.md`: these are exploratory observations from a public
benchmark dataset for a methodology comparison, not an assessment of KW51's real structural safety
— that bridge's actual condition is Belgian infrastructure authorities' and its own research team's
responsibility, verified by their own certified processes, not this lab's.

## Next: Phase 1

Fit the three-method ladder (classical regression baseline, vanilla spatial GP, GP + soft-EM
regime-mixture) on the well-identified mode subset, score detection performance across the
retrofit window with temperature properly conditioned on, per `LAB_PLAN.md`'s Method section.
