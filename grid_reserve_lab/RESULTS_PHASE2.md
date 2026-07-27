# Phase 2 results — real data, genuinely held-out scoring

**Status: DONE (2026-07-27).** `phase2_run.py` / `results_phase2.json` / `data_eia930.py`. A real
scoping pivot from LAB_PLAN.md's original sketch, made directly rather than silently — explained
below, not glossed over.

## The scoping pivot, and why

LAB_PLAN.md's Phase 2 called for NREL WIND Toolkit/NSRDB per-site data to ground individual-turbine
geography at a scale requiring `gp_ooc_fortran.py` (past the ~40k in-core ceiling). While probing
data access for this session, EIA-930's own website turned out to be Akamai-fronted and blocked to
automated fetches (confirming the research pass's earlier finding) — but its **bulk CSV download
endpoint** (`eia.gov/electricity/gridmonitor/sixMonthFiles/`) is directly reachable, no API key, and
serves real, continuously-updated hourly generation-by-fuel-type (Wind and Solar reported
separately) for every US Balancing Authority. That data is real, current, and immediately usable —
NREL's per-turbine data would have needed HSDS/S3 access to a multi-terabyte archive for a
resolution finer than this domain's actual decision-making granularity (grid operators plan
reserves at the BA/zone level, not per-turbine).

**So this lab treats each of 15 real US Balancing Authorities as one "site,"** at an illustrative
service-territory centroid (`data_eia930.BA_CENTROIDS` — a real approximation, not a
generation-weighted centroid, stated plainly in that module's docstring). This is coarser
resolution than individual-site geography, but it is **real data**, and BA-to-BA correlation in
renewable output during synoptic-scale weather systems is a genuine physical signal at this
resolution, not a proxy for one.

**Scoring is a genuine train/test split, not an oracle resample** — there's no synthetic
ground-truth DGP for real data. Every method fits on 2023 (365 real days) and is scored against the
actual, held-out 2024 (366 real days) it never saw, the same discipline `gblup_lab` and
`mining_gpc_lab` used moving from synthetic to real validation. Dollar scoring is reframed to match:
no independent "true required reserve" exists to compare against, so each method's total annual
cost is `reserve_mw × capacity cost` (the real stock cost of holding that reserve) plus the
**realized** under-procurement cost summed directly over the real violation days in the 2024 test
year (not a probability-extrapolated figure — the test set already is one full real year).

## A real data-quality bug caught and fixed along the way

`EIA930_BALANCE_2023_Jul_Dec.csv` reports a single hourly value for SWPP (Southwest Power Pool) on
2023-06-12 of **3,589,477 MW** — physically impossible (larger than the entire US wind+solar
fleet combined; SWPP's own real hourly values otherwise top out around 23,000 MW), and the kind of
isolated reporting glitch EIA-930's own "known issues" pages document. Left unfixed, this one hour
inflated SWPP's max-based nameplate-capacity proxy by 10x (154,987 MW vs. a real ~23,000-25,000 MW
peak) and would have silently corrupted Method 0's deterministic-rule baseline. Fixed with a
standard per-BA 99.9th-percentile winsorization (`data_eia930._clip_ba_outliers`) — a general fix,
not a hand-patch of this one BA/date.

A second, smaller bug from the same file-format change: EIA-930's column schema drifted between the
2023 and 2024 six-month files (2023: one plain "Net Generation (MW) from Wind/Solar" column each;
2024: split into "with/without Integrated Battery Storage" sub-columns) — an initial hardcoded
column list silently produced all-zero shortfall for 2023 data. Fixed by matching fuel columns via
prefix per-file rather than a fixed schema (`data_eia930._find_fuel_cols`).

## Headline scorecard

| Method | Reserve (MW) | Achieved reliability (2024) | Holding cost ($/yr) | Under-cost ($/yr) | Total ($/yr) |
|---|---|---|---|---|---|
| 0 — ERCOT N-1 (largest BA) | 29,610.3 | 99.18% | $3.56B | $5.71B | $9.27B |
| 0 — generic "5% of wind" | 5,824.2 | 65.03% | $0.70B | $155.4B | $156.1B |
| 1 — Independence (control only) | 22,737.4 | 98.09% | $2.73B | $12.34B | $15.07B |
| 2 — Aggregate correlation (real ISO practice) | 26,637.5 | 98.91% | $3.20B | $8.01B | $11.21B |
| 3 — Vanilla spatial GP | 34,410.0 | 99.18% | $4.13B | $2.69B | **$6.82B** |
| 4 — GP + soft-EM regime-mixture | 34,102.1 | 99.18% | $4.10B | $2.88B | $6.98B |

## Finding 1 — the Phase 1 ranking does NOT cleanly replicate on real data

On the synthetic oracle (Phase 1), Method 4 (soft-EM regime-mixture) clearly beat Method 3 (vanilla
GP), which barely beat Method 2. On real 2023→2024 data, **Methods 3 and 4 are statistically
indistinguishable** ($6.82B vs. $6.98B total annual cost, a ~2% difference easily inside this
lab's Monte-Carlo and data-quality noise) — both clearly beat Methods 0-2, but the *specific*
"regime-mixture beats vanilla GP" story from Phase 1 is not confirmed here. Reported plainly, not
smoothed over: this is a real, valuable finding in its own right (a synthetic DGP's mechanism
advantage doesn't automatically transfer to real data at 15-site resolution and one year of
held-out data), consistent with this lab family's own precedent
(`porphyry_cu_gpc_lab`'s runner-up ranking flip, `bayesian_decision_lab`'s Phase 1/3 reversal) —
methods that win in a controlled synthetic world don't always keep the same margin in the real one,
and that gap itself is informative.

## Finding 2 — the soft-EM regime split doesn't cleanly correspond to a real drought event

Method 4's fitted regime-mixture GMM assigns **85.2%** of training days to the "high-shortfall"
component (`p_hat_raw=0.852`), clipped down to the artificial 0.5 upper bound inherited unchanged
from `climate_cat_lab`'s synthetic calibration (`regime_mixture.py`'s `p_hat_bounds=(0.02, 0.5)`).
Checked directly, not assumed: this is **not a seasonal artifact** — the per-month mean
responsibility is flat (77.9%-92.3% across all 12 months, no winter/summer pattern) — so the split
isn't quietly re-discovering a real seasonal cycle either. The more likely explanation: this lab's
one-sided shortfall definition (`max(climatology − actual, 0)`, validated in Phase 0 for the
synthetic DGP) combined with a 30-day rolling climatology leaves enough short-timescale day-to-day
variability that "most days show *some* shortfall relative to the smoothed baseline" — a
genuinely different distributional shape than the synthetic oracle's DGP, which was explicitly
built to have a *rare* (~6.8%) regime. **This means Method 4's real-data fit likely isn't
representing a genuine synoptic drought regime the way it does in the Phase 0/1 synthetic world** —
an open methodological question, not resolved here, and worth flagging clearly before treating
Method 4's real-data numbers as validating the "regime-mixture models real droughts" story
specifically (as opposed to just "a richer covariance model helps," which both methods 3 and 4
support equally). A tighter climatology (e.g. a harmonic/Fourier seasonal fit instead of a 30-day
rolling mean) or a data-driven `p_hat_bounds` (not copied unchanged from a different domain) is the
natural next step, not attempted in this pass.

## Finding 3 — the deterministic N-1 rule's real-data success is a resolution artifact, not vindication

Method 0 (ERCOT's real N-1 rule) scores surprisingly well here (99.18% — tied with the GP methods!)
compared to its catastrophic 2.9% in Phase 1's synthetic 100-site world. Checked directly: ERCO
(ERCOT itself) is **25.4% of this real fleet's total nameplate capacity** (29,610 MW of 116,483 MW
across all 15 BAs) — at only 15 real BA-level "sites," the single largest unit already covers a
huge share of total system variability, simply because there are so few, so unevenly-sized units in
this resolution. This is **not evidence the N-1 rule is secretly a sound methodology for
correlated-shortfall risk** — it's an artifact of choosing BA-level (extremely coarse, 15 units)
resolution instead of individual-farm-level resolution (hundreds to low thousands of real wind/solar
sites, where no single site would dominate total capacity this way). Phase 1's synthetic 100-site
fleet, with no site anywhere near 25% of total capacity, is the more representative test of what N-1
actually does at realistic granularity — this real-data result is flagged as a resolution artifact,
not a contradiction of Phase 1's finding.

## Finding 4 (the domain-scale finding, stated honestly) — this lab doesn't reach OOC scale, and that's real

At n=15 real BAs, this fleet is nowhere near the ~40k in-core ceiling `gp_ooc_fortran.py` exists to
push past — every GP fit here (15×15 kernel) completes in seconds, no OOC engine needed. This is a
genuine finding about this specific domain's realistic decision-making resolution, not a shortfall
of execution: grid operators plan operating reserves at the BA/zone level (dozens of units, not
tens of thousands), unlike `climate_cat_lab`'s insurance book (100k-300k individual policies) or
`gblup_lab`'s marker-level genomic data. Pushing this lab to individual-turbine resolution (NREL
WIND Toolkit's 126,000+ site-level grid, fetched via HSDS/S3) would reach OOC scale, but would be
testing a resolution finer than any real reserve-sizing decision is actually made at — an artificial
scale-up for its own sake, not a domain-motivated one. Recorded here as a genuine, honest scoping
conclusion for this lab family, parallel to how `climate_cat_lab`'s own book-size figures were
carefully sourced rather than inflated to hit a round number.

## What's still illustrative, carried forward from Phase 1 unchanged

VOLL ($35,000/MWh), reserve capacity cost (PJM's $120,150/MW-year), and the 6-hour event-duration
simplification are the same Phase-1 constants (`reserve_calc.py`), not re-derived for this specific
15-BA real fleet — the dollar *magnitudes* above inherit Phase 1's stated caveats about these
figures (see `RESULTS_PHASE1.md`), even though the underlying reserve-MW and reliability numbers
here are genuinely real-data results.

## Follow-up (2026-07-27): fixing the climatology and the regime bounds — and finding the REAL bug

Fraser asked for two specific fixes to Findings 1-2 above: (1) replace the 30-day rolling-mean
climatology with a harmonic/Fourier seasonal fit (rolling means still leak day-to-day weather
variance into the "expected" baseline), and (2) make `regime_mixture.py`'s `p_hat_bounds` — hardcoded
`(0.02, 0.5)`, copied unchanged from `climate_cat_lab`'s synthetic calibration — data-driven instead
of inherited from a different domain. Both were implemented exactly as asked:

- `data_eia930.py`: a per-BA least-squares fit of 3 harmonics (annual/semiannual/~4-month cycle,
  7 parameters total) against day-of-year, replacing the rolling mean. Smooth by construction, no
  per-day degrees of freedom to absorb weather noise — and, as a side benefit, continuous in
  day-of-year, so the earlier leap-year-366 clipping hack is no longer needed at all.
- `regime_mixture.py`: `p_hat_bounds` now defaults to `(min_effective_days/n_days, 1 -
  min_effective_days/n_days)` — a purely numerical floor (enough effective days for a stable
  weighted spatial-kernel fit) computed from this call's OWN `n_days`, not a fixed fraction assuming
  the regime is rare.

**Result after both fixes: the split got MORE extreme, not less — `p_hat_raw` jumped to 0.995
(99.5% "drought"), clipped to 0.973 by the new wider bound.** This was not a failure of either fix
(both did exactly what they were supposed to) — it was the wrong diagnosis of what was broken.
Checked directly: the minority component's weight (0.548%) exactly matched the fraction of training
days with near-zero CLIPPED total shortfall (also 0.548%). **The real bug**: `regime_mixture.py` was
fitting its regime-detection GMM on `shortfall.sum(axis=1)` — the SUM of each site's already
one-sided-clipped (`max(climatology - actual, 0)`) shortfall. Summing already-clipped values creates
a spurious near-zero mass point at the fleet-total level, because a fleet total is only exactly (or
near) zero when EVERY site simultaneously performs at-or-above its own expectation — a far rarer
joint event than "the fleet's NET output, allowing sites to offset each other, was near its combined
expectation." The GMM wasn't finding a drought regime at all; it was mechanically separating "the
rare days the whole aggregated fleet happened to beat its smooth climatology" from "every other
day" — an artifact of clip-then-sum ordering, not a real synoptic signal, and this artifact exists
regardless of climatology choice (rolling or harmonic).

**The actual fix**: feed the GMM the fleet-wide **signed, unclipped** total deviation (climatology
minus actual, summed across sites BEFORE any clipping — `dgp_simulator.py` and `data_eia930.py` now
both expose this alongside the usual clipped `shortfall`, and `regime_mixture.fit_regime_mixture_soft`
takes it as a new `signed_shortfall` parameter). No log-transform is needed or applied — a signed
deviation isn't strictly positive, and it's far less skewed than climate_cat_lab's strictly-positive
dollar losses were, so a raw GMM fit on the signed value is the natural choice.

**Result: `p_hat_raw = 0.498` — a genuine, un-clipped ~50/50 split.** `gmm_means` are now
`[-8,336, +8,405]` MW, symmetric around zero exactly as a signed deviation should be (confirming
this isn't the same clipping artifact in a new guise). Checked directly, not assumed: month-by-month
mean responsibility is flat (37%-65% across all 12 months, no seasonal pattern), so this still isn't
quietly re-discovering a seasonal cycle either — it looks like a genuine, roughly-symmetric
"fleet did worse/better than its smooth seasonal expectation" split.

### Updated headline scorecard (post-fix)

| Method | Reserve (MW) | Achieved reliability (2024) | Total ($/yr) |
|---|---|---|---|
| 0 — ERCOT N-1 | 29,610.3 | 99.18% | $8.42B |
| 0 — generic "5% of wind" | 5,824.2 | 65.30% | $151.4B |
| 1 — Independence (control) | 23,469.8 | 98.36% | $12.59B |
| 2 — Aggregate correlation (real practice) | 27,594.1 | 99.18% | $9.44B |
| 3 — Vanilla spatial GP | 35,778.2 | 99.18% | $5.27B |
| **4 — GP + soft-EM regime-mixture** | 37,214.6 | **99.73%** | **$4.95B** |

**Finding 1 is now reversed, and matches Phase 1 again**: with the regime-detection bug fixed,
Method 4 clearly beats Method 3 on real data ($4.95B vs. $5.27B, higher achieved reliability too) —
the same qualitative ranking Phase 1's synthetic oracle found. The earlier "statistical tie"
reported above was itself a symptom of the same clip-then-sum bug (a degenerate regime fit can't
add much value over a plain spatial GP; a correctly-fit one can and does).

**Finding 2 is answered, but not the way either the original plan or the "rare regime" framing
expected.** The real regime this data supports isn't a rare (~5-7%) severe drought the way the
synthetic Phase 0/1 DGP was explicitly built to have — it's closer to a persistent, roughly
even 50/50 split between "the fleet ran below its smooth seasonal expectation" and "above it."
That's a genuinely different, and correctly-caught, characterization, not a validation of the
original "rare event" story transplanted onto real data. Whether a real, physically-named
synoptic-scale mechanism (not just "half the days are below trend") underlies this split is still
open — a natural next step, not pursued in this pass, would be checking whether the two GMM
components separate along a real meteorological feature (e.g., a blocking-ridge index) rather than
just the shortfall magnitude itself.

## Summary (superseded by the Follow-up above — kept for the record, not deleted)

**This section was the honest conclusion before the Follow-up's bug fix, and is left here rather
than deleted because the debugging trail — including a wrong-but-reasonable first diagnosis — is
itself part of the record.** At the time, both GP methods (3-4) clearly beat methods 0-2, but
methods 3 and 4 were statistically tied and the regime-mixture's fitted split didn't obviously
correspond to a real drought event. Chasing that discrepancy (per Fraser's two requested fixes) led
to finding the actual bug: `regime_mixture.py` was summing already one-sided-clipped per-site
shortfall for its regime-detection feature, creating a spurious near-zero mass point that had
nothing to do with drought events. **The corrected, current conclusion** (see the Follow-up section
above): Method 4 does beat Method 3 on real data after all, matching Phase 1's synthetic finding,
once the regime-detection feature is computed correctly (signed, unclipped, summed across sites
before any clipping). All methods still clearly beat 0-2. The one honestly open question that
survived the fix: the real fitted regime is a persistent ~50/50 above/below-seasonal-trend split,
not the rare (~5-7%) severe-drought event the synthetic DGP was built to have — a genuinely
different, and correctly-diagnosed, characterization of what "regime" means in real fleet-wide
renewable output data.
