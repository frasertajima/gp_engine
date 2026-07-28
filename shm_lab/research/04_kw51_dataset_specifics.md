# Claim 4: KW51 dataset specifics (retrofit reason/dates, sensors, license, monitoring duration)

**Status: VERIFIED**, directly from the KU Leuven Structural Mechanics Section's own benchmark
page (`bwk.kuleuven.be/bwm/kw51`, the dataset owner) and corroborated by independent search results
referencing the Maes & Lombaert (2021) ASCE Journal of Bridge Engineering paper.

## What was previously stated in `LAB_PLAN.md` (from an earlier, less direct source) vs. now confirmed

- **Retrofit reason — a real correction.** `LAB_PLAN.md`'s original draft called this a
  "strengthening intervention" without further context, implicitly framing it as routine/planned
  work. The KU Leuven page states plainly: the bridge underwent retrofitting due to **"a
  construction error that was noticed during inspection"** — specifically, "strengthening the
  connections of the diagonals to the arches and the bridge deck." This is a real defect
  correction, not routine scheduled maintenance. This is actually a **better** fit for this lab's
  framing than first drafted: it means the retrofit event is closer to "a real structural problem
  was found and fixed" than to "planned upgrade with no prior structural concern" — a stronger
  analogy to the safety-relevant detection question this lab asks, and should be stated this way,
  not softened.
- **Exact retrofit dates — confirmed**, consistent across two independent sources (an academic
  functional-data-analysis paper's description and the KU Leuven page itself): retrofit work
  2019-05-15 to 2019-09-27, inside a pre-retrofit monitoring window from 2018-10-02 and a
  post-retrofit window continuing to 2020-01-15 for the specific 15-month dataset published on
  Zenodo (DOI 10.5281/zenodo.3745914).
- **Monitoring duration — a genuine nuance not previously known.** The KU Leuven page states the
  monitoring system actually operated far longer than the 15-month Zenodo-published window —
  **from September 2018 through September 1, 2024** (roughly six years). The Zenodo record this
  lab plans to use is a specific, earlier 15-month slice (Oct 2018-Jan 2020) of a longer-running
  real monitoring campaign, not the campaign's full duration. This is fine for Phase 0/1 (the
  15-month slice already spans the full before/during/after retrofit structure this lab needs) but
  is worth stating accurately rather than implying the dataset covers the structure's entire
  monitored life.
- **Sensors — confirmed, slightly more detail than first drafted**: accelerometers (lateral and
  vertical on the deck, lateral on the arches), strain gauges (deck, braces, and rails), laser-based
  displacement sensors at the abutments, plus temperature and humidity monitoring.
- **License — confirmed directly from the owner**: "Both the data and the model have been
  published under the Creative Commons Attribution Non Commercial Share Alike 4.0 International
  license." Citation of the relevant publications is required. Non-commercial use only.

## Not yet verified (Phase 0 task, not assumed here)

The specific per-file sizes for `ambient_yyyymm.zip`/`traindata_yyyymm.zip` and the exact column
layout of `trackedmodes.zip` were not independently confirmed beyond an automated page-summary
tool's read of the Zenodo listing — `LAB_PLAN.md` already flags this correctly as unverified
pending an actual download.
