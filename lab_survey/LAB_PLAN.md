# shm_lab — does GP soft-EM catch a real structural change that a classical EOV correction misses?

> ## ⚠️ DISCLAIMER — READ BEFORE USING ANYTHING IN THIS LAB FOR ANY PURPOSE ⚠️
>
> **This lab is theoretical, educational, and exploratory only. Nothing here is certified,
> validated, or fit for use in any real engineering decision.**
>
> - **No one may rely on this lab's findings, code, methodology, or output to make any decision or
>   take any action regarding a real structure — bridge, building, pipeline, or otherwise.** Not
>   for design, inspection scheduling, retrofit prioritization, risk assessment, public
>   communication, or anything else with real-world consequences.
> - **This is not a substitute for, and must never be treated as equivalent to, certified
>   structural-engineering practice.** Any real structure must be evaluated exclusively by
>   qualified, licensed engineers using established, validated, code-compliant methods.
> - **The GP soft-EM math used here has not been validated against certified structural-engineering
>   methodology by any qualified engineer.** Where this lab's approach differs from standard
>   practice, that difference is a hypothesis to be scrutinized — not a claim that this lab's
>   method is better, safer, or more accurate. A qualified engineer must review and independently
>   assess any such difference before it is given any weight whatsoever.
> - **The sole legitimate use of this lab is as a starting point for evaluating standard-practice
>   assumptions in a research/educational context** — e.g., "does a classical EOV correction miss
>   something a regime-aware model would catch, and if so, is that worth a qualified engineer's
>   attention" — never as an answer in itself.
> - All datasets used are public benchmark datasets (e.g., KW51), not live monitoring of any
>   structure currently in service that this lab's authors have any responsibility for or authority
>   over. Nothing here monitors, or should be construed as monitoring, any real structure's actual
>   current safety status.
>
> This disclaimer applies to every file, result, notebook, and any application built in this lab,
> and must be preserved (not diluted or removed) in any derivative, summary, or presentation of
> this work, including the FastAPI app described below.

**Status: Research pass DONE (2026-07-28, `research/RESEARCH.md`), Phase 0 DONE (2026-07-28,
`RESULTS_PHASE0.md`), Phase 1 DONE (2026-07-28, `RESULTS_PHASE1.md`), Phase 1b/1c DONE (2026-07-28,
`RESULTS_PHASE1B.md`), same rigor as `climate_cat_lab/research/` and `grid_reserve_lab/research/`.
Phase 2-original (the FastAPI app) not pursued — see Phase 2 (2026-08-02) below instead, a
different, later addition: the sequential-VoI inspect/wait/remediate layer, `RESULTS_PHASE2.md`.**
**Phase 1's per-mode result was a genuine mixed/negative
finding — no clear soft-EM advantage over classical regression or vanilla GP.** Fraser's own
structural hypothesis (this lab lacked the recurring-regime and cross-sectional-pooling ingredients
that made soft-EM win in `climate_cat_lab`/`cvar_gp_lab`/`grid_reserve_lab`) led to Phase 1b: a
**joint** model sharing one regime-responsibility trajectory across all 5 modes (restoring
cross-sectional pooling, since a single retrofit event can't be made recurring) — false-alarm rate
dropped to 5.8% with detection just 6 days after the true retrofit start, a dramatic improvement
over any single mode. **But Phase 1c's honest control (a naive joint chi-squared statistic, no
soft-EM at all, summing the same five per-mode z-scores) matched that same detection speed and
flag rate exactly**, at an 11.5% false-alarm rate — meaning **pooling across modes, not the
soft-EM mechanism, did almost all of the work**; soft-EM's own isolated contribution is real but
modest (roughly half the false-alarm rate at matched detection speed), and on a small enough
sample (3 vs. 6 flagged days) to be suggestive rather than decisive. See `RESULTS_PHASE1B.md` for
the full reasoning and the sharpened, transferable rule of thumb this leaves for the rest of the
codebase: check whether plain pooling already gets most of the benefit before reaching for
soft-EM's added complexity. A real data-leakage bug (regime B's EM fit was seeing the same
held-out points later used to score its false-alarm rate) was also found and fixed along the way —
see `RESULTS_PHASE1.md`. Dataset chosen, access confirmed downloadable today (no request/approval
step), license
terms read. **The research pass forced one real, load-bearing correction to this lab's own
premise, not just a footnote**: GP regression for EOV removal in bridge SHM — including
heteroscedastic GP — is already an established, actively-published technique (Teimouri et al. 2017;
a dedicated heteroscedastic-GP EOV-removal paper; ongoing 2025 work), and a **regime-switching
cointegration** method already targets the identical "single relationship isn't enough" gap this
lab's soft-EM layer was meant to address. This lab's honestly-narrowed contribution is no longer
"does GP/regime-awareness help SHM" (already answered: yes, by others) but **"does the specific
soft-EM regime-mixture mechanism already validated three times in this codebase transfer
competitively to this domain and this real event, on this real dataset"** — see the corrected
hypothesis below. A second correction: the KW51 retrofit was necessitated by **a real construction
error found on inspection**, not routine planned work — strengthens, rather than weakens, this
lab's real-world relevance.

## One line

Bridge structural-health monitoring (SHM) has a well-known confound: a structure's measured modal
frequencies (its vibration "fingerprint") drift with **temperature and other environmental/
operational variability (EOV)**, and that drift is routinely larger than the frequency shift caused
by real damage — so a naive damage-detection rule either fires constantly on cold mornings (false
alarm → wasted inspection cost) or gets desensitized until it misses a real change (false negative
→ safety risk). This is the same shape of problem as every prior lab in this family
(`climate_cat_lab`, `cvar_gp_lab`, `grid_reserve_lab`): a classical method aggregates away
structure that a spatial/regime-aware GP can resolve, and the cost of getting it wrong is
asymmetric and real. This lab is the fourth port of the same soft-EM regime-mixture mechanism,
this time onto sensor-network time series instead of asset returns or fleet output — **and it is
the first lab in the family with a genuine, non-synthetic ground-truth event**: the KW51 railway
bridge (Leuven, Belgium) was physically retrofitted (strengthened) partway through its 15-month
monitoring campaign, so "did the method correctly flag that the structure's true state changed, and
when" is answerable against a real intervention date, not an oracle DGP.

## Why this lab, and why now

1. **Fourth port of the same mechanism, first with real (not synthetic) ground truth.** Every
   prior lab had to build an oracle because the true systemic-event process isn't observable in
   real data (a real catastrophe year, a real drought regime). Here the "regime change" is a
   scheduled retrofit with a known date — real damage-detection literature and real engineering
   records, not a simulation. If GP soft-EM's advantage shows up here too, that is the strongest
   evidence yet that the pattern is structural, not an artifact of any one lab's synthetic design.
2. **Public-good framing, explicitly requested.** Unlike the prior labs' economic-value framing
   (dollars saved), this one's headline metric is **earlier/more reliable detection of a real
   safety-relevant structural change, with fewer false alarms** — a demonstrable, non-proprietary
   public-safety story, deliverable as an app anyone can point at a bridge's sensor data and try.
3. **Real, open, zero-friction public data — confirmed, not assumed, after a real dead end.**
   BCSIMS (BC's own bridge-monitoring network, including the Ironworkers Memorial Second Narrows
   Crossing and Port Mann Bridge) turned out to gate actual SHM sensor data behind an "authorized"
   (scientist/engineer) account tier — public registrants only get earthquake shake-maps (confirmed
   directly from the BCSIMS design paper, Kaya/Ventura/Huffman/Turek, *Can. J. Civ. Eng.*, draft
   cjce-2016-0577.R2, p.9). Decision (Fraser, 2026-07-28): **use a genuinely open benchmark now,
   revisit BC-specific access only after the lab is complete, if warranted by time/benefit.**
4. **The soft-EM machinery itself needs no new work.** Same shared mechanism as `climate_cat_lab`
   (storm regime) → `cvar_gp_lab` (return regime) → `grid_reserve_lab` (drought regime), now ported
   to an environmental/operational regime (temperature/loading state) confounding a sensor
   network's spatial-kernel GP. `gblup_lab/marker_kernel.py`'s kernel builder generalizes again —
   this time over **sensor position on the structure** (accelerometer/strain-gauge location on
   deck/arches) instead of geographic lat/lon.
5. **The application layer is the point of this lab, not a stretch phase.** Every prior lab
   treated a live app as an optional Phase 3+. Here Fraser's explicit ask is the deliverable itself:
   a FastAPI app that ingests a chosen public dataset, runs both the classical and GP-soft-EM
   calculation, and presents them side by side clearly enough that a non-specialist can see exactly
   where the classical method's warning light fails to come on.

## The dataset (confirmed access, license read, retrofit reason/dates corrected by research pass; content NOT yet downloaded/verified)

**KW51 railway bridge monitoring dataset** — Maes, K. & Lombaert, G., *"Monitoring railway bridge
KW51 before, during, and after retrofitting,"* submitted to ASCE J. Bridge Engineering. Hosted on
Zenodo, DOI [10.5281/zenodo.3745914](https://zenodo.org/records/3745914) — **direct download, no
request/approval step**, unlike Z-24 (KU Leuven's own benchmark, which requires requesting access
under non-commercial/no-third-party-transfer terms) or BCSIMS (gated behind an authorized account).

- **Structure:** steel bowstring railway bridge, Leuven, Belgium, 115 m span, two curved
  electrified tracks.
- **Campaign:** 15 months, 2018-10-02 to 2020-01-15 (a slice of a longer real monitoring campaign —
  confirmed from the KU Leuven Structural Mechanics Section's own benchmark page that the physical
  system actually ran from Sept. 2018 through Sept. 2024, roughly six years; this lab uses the
  15-month Zenodo-published slice, which already spans the full before/during/after retrofit
  structure it needs). **Retrofit took place 2019-05-15 to 2019-09-27, necessitated by a real
  construction error found on inspection** — strengthening the connections of the diagonals to the
  arches and the bridge deck (confirmed directly from the dataset owner's own page, correcting this
  plan's earlier, vaguer "strengthening intervention" framing) — this is the lab's real "did we
  detect a genuine state change" ground-truth event, and a defect correction, not a simulated
  damage case or routine scheduled upgrade.
- **Sensors:** acceleration (deck + arches), strain (deck + diagonals connecting deck to arches),
  strain (rails), displacement (bearings), temperature and relative humidity. Six ambient-vibration
  measurement windows and two train-passage recordings per day.
- **File organization** (per Zenodo + `readme.txt`): `ambient_yyyymm.zip` (raw ambient-vibration
  time series, monthly, roughly 1.4-4.3 GB/month per an initial fetch — **size figures unverified,
  need confirming on actual download, not trusted from a page-summary alone**), `traindata_yyyymm.zip`
  (train-passage recordings, ~187-466 MB/month, same caveat), `trackedmodes.zip` (12.9 MB — **the
  likely Phase 0 starting point**: pre-extracted identified modal characteristics, i.e. the
  processed natural-frequency/mode-shape time series over the full campaign, small enough to work
  with immediately and exactly the object the EOV-confound literature is about), `matlab-functions.zip`
  (6.9 kB, plotting helpers, not needed — this lab is Python/Fortran/Rust).
- **License: CC-BY-NC-SA 4.0** — non-commercial, share-alike, attribution required. Fine for a
  public-good demo/research app; would need a different arrangement before any commercial use.
- **Not yet done:** actually downloading and inspecting `trackedmodes.zip`'s real column layout
  (which modes, what temperature covariate, sampling rate) is Phase 0's first task, not assumed
  here.

## Domain background (research pass DONE, 2026-07-28 — see `research/RESEARCH.md`)

1. **EOV/temperature confound — VERIFIED as a general SHM phenomenon.** Sohn (2007)'s canonical
   review and Peeters & De Roeck (2001)'s direct empirical demonstration on the Z-24 bridge (a
   bilinear frequency-vs-temperature relationship, opposite trends above/below 0°C) both confirm
   temperature effects are large enough to be a first-order confound requiring dedicated
   correction, not a second-order nuisance. **Not yet confirmed specifically for KW51** — checking
   whether this bridge shows a comparable relationship is Phase 0's first task, not assumed here.
   (`research/01_environmental_operational_variability.md`)
2. **A real classical EOV-correction baseline exists — PARTIALLY VERIFIED, with an important
   complication.** Three real, published methods found: plain linear/polynomial regression
   (the literature's standard starting point), PCA-based removal (documented to struggle on
   nonstationary data — its own literature already flags this), and cointegration (Cross et al.).
   **A regime-switching cointegration method already exists**, targeting the same "a single fixed
   relationship isn't enough" gap this lab's soft-EM layer was meant to address — so
   regime-awareness itself is not this lab's novel contribution. Which method is the actual
   most-common real-world default (vs. most-published-about) was not established.
   (`research/02_classical_eov_correction_methods.md`)
3. **GP regression for SHM/EOV removal is NOT a novel idea — CORRECTED, the most important finding
   of this pass.** GP regression, including heteroscedastic GP variants, is an established,
   actively-published technique for exactly this problem (Teimouri et al. 2017; a dedicated
   heteroscedastic-GP EOV-removal paper; population-based GP-SHM work; ongoing 2025 research).
   Combined with point 2's regime-switching-cointegration finding, **this lab's honest
   contribution is narrower than first drafted**: not "does GP or regime-awareness help SHM"
   (already answered elsewhere: yes), but **does the specific soft-EM regime-mixture mechanism
   already validated three times in this codebase transfer competitively to this domain, on this
   real dataset and this real intervention event.** (`research/03_gp_already_used_in_shm.md`)
4. **The retrofit was a construction-defect correction, not routine planned work — VERIFIED,
   correcting this plan's earlier vaguer framing.** Confirmed directly from the dataset owner
   (KU Leuven): "a construction error that was noticed during inspection" necessitated
   strengthening the diagonal-to-arch and diagonal-to-deck connections. This strengthens, rather
   than weakens, this lab's real-world relevance — it is closer to "a real structural problem was
   found and fixed" than to a routine upgrade with no prior concern. Kept honestly distinct from
   a *fault/damage-detection* framing all the same: this is one real, singular, human-identified-
   and-corrected event, not a population of naturally-occurring damage cases.
   (`research/04_kw51_dataset_specifics.md`)
5. **Real-world SHM adoption status and cost figures — PARTIALLY VERIFIED.** US bridge inspection
   practice is confirmed still visual-inspection-default (NBIS, 24-month max interval) with
   full-scale permanent SHM "sparingly used" (Agdas et al., QUT/UF/FDOT) — confirming this lab's
   litmus-test condition that a real (not strawman) classical incumbent exists. Real Florida SHM
   system costs found: ~$29,000 for a scour-monitoring system, ~$11,900/pier for cathodic-
   protection corrosion monitoring. **No sourced figure found yet for the false-negative
   (missed-damage) cost side** — the economic-layer stretch goal stays explicitly unconfirmed, not
   filled with an invented placeholder. The same source independently raises the liability
   question this lab's disclaimer exists to foreclose: "Should a structural change leading to
   bridge failure be missed, which party, if any, holds the responsibility?"
   (`research/05_shm_practice_and_cost.md`)

## Precedent already in this codebase

| shm_lab | reused from |
|---|---|
| Spatial kernel, repointed a fourth time — sensor position on the structure instead of geographic lat/lon | `gblup_lab/marker_kernel.py` → `cvar_gp_lab/asset_kernel.py` → `climate_cat_lab/spatial_kernel.py` → `grid_reserve_lab/spatial_kernel.py` |
| Soft-EM regime-mixture (now over a latent environmental/operational regime instead of a systemic-event regime) | `climate_cat_lab/regime_mixture.py` → `cvar_gp_lab/regime_gp.py` → `grid_reserve_lab/regime_mixture.py` — fourth port of the identical mechanism |
| Dense GP solve | `gp_core.py` (in-core); `gp_ooc_fortran.py` if the raw acceleration/strain files (not just `trackedmodes`) end up needed at scale — open question, see Phases |
| Economic/decision layer for the asymmetric false-alarm/false-negative cost, if pursued | `gp_engine/decision.py` / `voi.py`, already reused three times (`bayesian_decision_lab`, `porphyry_cu_gpc_lab`, flagged-not-yet-used in `grid_reserve_lab`) |
| Live-app precedent | `portfolio_studio` (daily-refreshed signal board) — the closest existing shape for what the FastAPI app below should look like, though this lab's app ingests a *chosen dataset* rather than a live feed |

## The core hypothesis, stated precisely (narrowed by the research pass — see point 3 above)

> **Not** "GP regression helps SHM EOV correction" (already established by others) or "regime
> awareness beats a single fixed relationship" (regime-switching cointegration already exists) —
> the actual, narrower, honest claim this lab tests:
>
> The **specific soft-EM regime-mixture mechanism** already validated three times in this codebase
> (`climate_cat_lab` → `cvar_gp_lab` → `grid_reserve_lab`), ported to sensor-network time series
> with a latent environmental/operational regime, will either (a) raise a materially lower
> false-alarm rate during normal temperature swings than a plain classical EOV-correction baseline
> at matched detection sensitivity, or (b) detect the real 2019 retrofit-driven structural-state
> change (a genuine construction-defect correction, not simulated damage) earlier or more clearly
> than that baseline does — and any advantage over a vanilla (non-mixture) spatial GP specifically
> comes from resolving a latent regime that a single smooth temperature relationship cannot
> represent, the same split every prior lab in this family had to isolate honestly.

Ways this can come back false, to be reported plainly either way (same discipline as every prior
lab in this family):
- The classical regression baseline may already handle this specific bridge's temperature
  relationship well if it's simple/monotonic — the real advantage may only show up in a
  multi-regime scenario (e.g., seasonal freeze/thaw, or the KW51 bridge may not have one at all).
- Vanilla spatial GP (no regime-mixture) might already close most of the gap, exactly as
  `climate_cat_lab` and `grid_reserve_lab` both found for their vanilla-GP rung — if so, the
  writeup must credit vanilla GP, not the regime-mixture layer, honestly.
- **This lab may simply replicate what heteroscedastic GP or regime-switching cointegration
  already achieve, with no material advantage** — a real, reportable possible outcome (parity, not
  improvement), not assumed away. If pursued, a literature-comparison stretch (Phase 3+) would be
  the honest way to check this rather than asserting it either way from this lab's own results
  alone.
- A retrofit is a real, singular, human-identified-and-corrected event — not necessarily
  statistically similar to the kind of gradual damage accumulation SHM literature usually targets.
  The lab should report detection performance for *this specific kind of event* and not overclaim
  it generalizes to slow fatigue-crack growth without saying so.

## Method (draft — will firm up once `trackedmodes.zip` is actually inspected in Phase 0)

Three-rung ladder (fewer rungs than `grid_reserve_lab`'s five, since there is no deterministic-
heuristic rung analogous to ERCOT's fixed rules here — to be revisited once the real classical
baseline is sourced):

0. **Classical EOV correction** — regression of tracked natural frequency(ies) on temperature (and
   possibly humidity/track-loading proxies), residual-based control-chart alarm (e.g. a fixed
   sigma-multiple threshold on regression residuals) — the real incumbent practice, once sourced.
1. **Vanilla spatial GP** — GP regression of frequency (and/or multi-sensor joint state) over
   sensor position + temperature covariate, tests whether a spatially-resolved but still elliptical
   model already closes most of the gap.
2. **GP + soft-EM regime-mixture** — layers a latent regime (seasonal, loading-state, or
   pre/post-retrofit structural state, tunable) on top of rung 1, the same mechanism ported a
   fourth time.

**Scoring, against the real retrofit date (2019-05-15 to 2019-09-27), not a synthetic oracle:**
- Detection lag/clarity — how cleanly and how promptly does each method's residual/regime signal
  shift across the retrofit window, at matched pre-retrofit false-alarm rate?
- False-alarm rate during clearly "nothing structurally changed" periods (e.g., comparing two
  different winters pre-retrofit) — the safety-relevant asymmetric-cost side of the story.
- If the economic framing (point 5 above) gets sourced, a dollar/cost translation analogous to
  `mining_gpc_lab`'s ranked-campaign economic layer — inspection-callout cost vs. missed-change
  risk — kept as a stretch, not assumed necessary for the core finding.

## The application (the point of this lab, not a stretch phase)

A FastAPI app (same posture as `backup_service`/`portfolio_studio`'s FastAPI precedent) that:
1. **Ingests a user-selected public SHM dataset** — KW51 first, structured so a second open
   dataset (e.g. Z-24 if access is pursued later, or the Norwegian open bridge SHM datasets
   surfaced during this session's research, not yet vetted) can be added without a rewrite.
2. **Runs both the classical calculation and the GP soft-EM calculation** on the same ingested
   data and presents them **side by side**, so a user can see concretely where the classical
   method's alarm stays quiet while the GP soft-EM model's doesn't (or vice versa, reported
   honestly either way).
3. **Documents the math and process inline** — the goal stated explicitly by Fraser is that any
   user can verify the work, not just trust a chart. This means the app itself carries (not just
   a separate README) plain explanations of what EOV correction is, what the GP kernel is doing,
   and what the regime-mixture layer adds, next to the actual numbers it computed.
4. **Presents results strikingly** — this is the one lab in the family where the visual
   presentation is a first-class deliverable, not an afterthought; worth a real design pass (the
   `dataviz` skill's conventions), not a default matplotlib dump.
5. **Carries the disclaimer above as a permanent, non-dismissible-past-a-checkbox UI element** —
   not a footer line. Every page that shows a calculation, chart, or "classical missed this, GP
   soft-EM caught it"-style comparison must visibly restate that this is theoretical/educational
   only and not to be relied on for any real structure. This is a hard requirement on the app's
   design, not a nice-to-have.

## Phases

**Phase 0 — DONE (2026-07-28, `RESULTS_PHASE0.md`).** Downloaded and inspected `trackedmodes.zip`
directly (`data_kw51.py`): 11,328 hourly samples, Oct 2018-Jan 2020, 14 tracked modes (frequency,
damping, complex mode shape across 12 sensor channels) + 11 environmental covariates
(temperature/humidity on-deck and at a weather station, plus radiation/wind/rain — richer than
first drafted). **Both sanity checks pass, on real data, not a synthetic oracle**: (1) the
EOV/temperature confound is real and present specifically in KW51 (not just generically in the
literature) — correlation between tracked frequency and deck temperature among the five
well-identified modes ranges from -0.103 to **-0.738**; (2) a real retrofit-window signal exists —
mode 5 (weakest temperature confound) shows a clean **+2.07%** frequency increase post-retrofit,
physically consistent with the strengthening work, while mode 8 (strongest temperature confound,
-0.738) shows an ambiguous small shift that could be retrofit or could be the pre/post windows'
different seasonal temperature mix — **the exact confound this lab's hypothesis targets, now
observed directly rather than only argued from citations.** Raw `ambient_yyyymm.zip` months not
needed for Phase 1 — `trackedmodes.zip` alone is sufficient.

**Phase 1 — DONE (2026-07-28, `RESULTS_PHASE1.md`).** Fit all three methods on daily-aggregated
data for the five well-identified modes, scored against the real retrofit window with a fair
train/held-out/during/post split. **Did not reuse `gblup_lab/marker_kernel.py`'s spatial kernel as
originally planned** — frequency is a scalar per-mode structural property, not a per-sensor
spatial field, so Phase 1 used a direct 1D GP over temperature (`gp1d.py`) instead; a
mode-similarity kernel (treating modes as the "sites") remains a real, un-tried Phase 2 idea if a
joint multi-mode model is pursued. **Headline finding**: no clear advantage for the soft-EM
regime-mixture over classical regression or vanilla GP in this implementation — see the Status
line above and `RESULTS_PHASE1.md` for the full mode-by-mode table, the real data-leakage bug
found and fixed, and the honest caveats on what this specific implementation does and doesn't
prove.

**Phase 2-original — the FastAPI application. Not pursued.** Wrap Phase 1's pipeline into the
ingest → dual-calculation → striking-presentation app described above. Fraser's call: soft-EM's
modest, precisely-characterized Phase 1c contribution didn't warrant it — lab declared
feature-complete at Phase 1c instead (see Notebook section below).

**Phase 2 (2026-08-02) — sequential-VoI inspect/wait/remediate layer. DONE, see
`RESULTS_PHASE2.md`.** A later, different addition — not a resumption of Phase 2-original above.
Second application of `gp_engine/VOI_DISPATCH_PATTERN.md` (after `grid_reserve_lab`'s Phase 4),
per Fraser's direction to try this lab next with the same template, anticipating that sourcing
real $ constants might be "a separate problem" (confirmed true, `research/
06_inspection_and_failure_cost.md`). Reframes Skip/Probe/Drill as inspect/wait/remediate: state =
the real `retrofit_mask`-derived label (0 = held-out-normal pre-retrofit day, 1 = during+post);
skip = default 24-month NBIS inspection cadence; probe = an out-of-cycle manual inspection; drill =
escalate directly to remediation. **New modeling piece required** (`damage_classifier.py`): every
existing model here is GP *regression*, not classification, so a genuine `LaplaceBinaryGPC` fit was
built on top of the five modes' existing frozen-regime-A z-scores (features) against the real
retrofit label — the same honest gap `grid_reserve_lab`'s Phase 4 hit with its own retrospective-
only regime-mixture model. **Bootstrap convention differs from `grid_reserve_lab`** (one fixed real
dataset here, not a resimulable oracle) — 200 seeds each redraw a fresh split of the same 296 real
days, mirroring `bayesian_decision_lab`/`porphyry_cu_gpc_lab`'s own convention more closely than
`grid_reserve_lab`'s did. **Three genuinely new findings for this lab family**: (1) the real KW51
transition is detected almost perfectly (AP≈0.999–1.000, checked not engineered — even single-mode
or 8-day-training-set variants stayed ≥0.97); (2) as a direct consequence, GPC's posterior
*variance* adds nothing measurable anywhere on a 13-point breakeven sweep (GPC-full and GPC-mean
bit-identical in all 200 seeds at every breakeven tried) — the mirror image of `grid_reserve_lab`'s
modest-but-real variance benefit; (3) whether GPC's mean beats SVM is itself cost-ratio-dependent
and, unlike every prior VoI lab, can reverse: SVM wins by a real, robust margin at moderate-to-high
breakeven probabilities (this dataset's positive class is the *majority*, 82.4% — a first for this
family). Mechanism traced to the same MacKay moment-matching shrinkage-toward-0.5 effect
`bayesian_decision_lab`'s own Phase 1 found, here miscalibrating in the opposite direction since the
true base rate sits far above 50% rather than far below it.

**Phase 3 (stretch) — additional open datasets, and the BC access decision.** Add a second open
dataset (Z-24, if its access terms are acceptable once actually requested; the Norwegian open SHM
datasets found in this session's search, unvetted; a public pipeline SHM dataset, if one is ever
found — flagged by Fraser as worth checking, not confirmed to exist). Only after the lab is
complete: revisit requesting BCSIMS "scientist"/"engineer" tier access for a local BC bridge
(Ironworkers Memorial or Port Mann), if the time/benefit case still looks good then.

## Files

- `data/trackedmodes/trackedmodes.mat` — **DONE.** Downloaded from Zenodo (DOI
  10.5281/zenodo.3745914), not committed to version control (large binary; re-downloadable from
  the DOI).
- `data_kw51.py` — **DONE.** Loader: dates, 14-mode frequency/damping/complex-mode-shape arrays,
  11 environmental covariates, and a real pre/during/post-retrofit split from the sourced dates.
- `phase0_run.py` / `results_phase0.json` / `RESULTS_PHASE0.md` — **DONE.** Confirms the
  EOV/temperature confound and a real retrofit-window signal are both present in KW51's actual
  data, and identifies mode 5 (clean signal) and mode 8 (strongest confound) as the two most useful
  test cases for Phase 1.
- `research/` — **DONE.** Five sourced verification notes + `RESEARCH.md` index, same convention as
  `climate_cat_lab/research/`/`grid_reserve_lab/research/`.
- `daily_agg.py` — **DONE.** Daily aggregation + random (not chronological — see file's own comment
  on the temperature-extrapolation bug this fixed) train/held-out/during/post split.
- `gp1d.py` — **DONE.** Minimal exact 1D GP regression (RBF + noise), supports per-point sample
  weights for the regime-mixture's weighted M-step. No GPU/OOC engine needed at this domain's
  scale (~100-400 points/mode) — an honest scoping note, same posture as `grid_reserve_lab`'s own
  Finding 4.
- `classical_baseline.py` — **DONE.** Method 0: OLS regression + residual control chart.
- `vanilla_gp.py` — **DONE.** Method 1: single global GP over temperature, no regime structure.
- `regime_mixture.py` — **DONE.** Method 2: GP + soft-EM regime-mixture (regime A frozen on train,
  regime B iteratively refit via EM on during+post only — a real data-leakage bug in an earlier
  version is documented and fixed directly in this file's docstring).
- `phase1_run.py` / `results_phase1.json` / `RESULTS_PHASE1.md` — **DONE.** The three-method
  ladder, fair-fight calibration, and the honest mixed/negative headline finding.
- `joint_daily_agg.py` / `joint_regime_mixture.py` / `phase1b_run.py` / `results_phase1b.json` —
  **DONE.** The joint multi-mode soft-EM model (one shared responsibility trajectory across all 5
  modes) that restored fast, well-calibrated detection.
- `phase1c_run.py` / `results_phase1c.json` — **DONE.** The honest control that isolated *why*:
  a naive joint chi-squared statistic (no soft-EM) matched Phase 1b's detection speed and flag
  rate exactly, at roughly double the false-alarm rate — pooling did most of the work; soft-EM's
  own contribution is real but modest. See `RESULTS_PHASE1B.md` for the full picture.
- `damage_classifier.py` — **DONE (Phase 2).** New `LaplaceBinaryGPC`/`SVC` fit on the five modes'
  frozen-regime-A z-scores against the real retrofit label — the genuine `(mean,var,prob)` triple
  this lab's regression-only models never produced.
- `run_dispatch_voi.py` / `bootstrap_dispatch_voi.py` / `cost_ratio_sweep_dispatch.py` — **DONE
  (Phase 2).** Single-seed, 200-seed, and breakeven-sweep drivers for the sequential-VoI decision
  layer, reusing `gp_engine/decision.py`/`voi.py` unchanged.
- `research/06_inspection_and_failure_cost.md` — **DONE (Phase 2).** Inspection-cost and I-35W
  bridge-failure-cost research, both honestly caveated (see `RESULTS_PHASE2.md`).
- `RESULTS_PHASE2.md` — **DONE.** Full Phase 2 write-up: near-perfect separability, the
  variance-adds-nothing finding, and the SVM-beats-GPC-at-high-breakeven reversal.

## Notebook

`SHM_LAB.ipynb` (built by `build_notebook.py`, executed via `jupyter nbconvert --execute`, 0
errors, 13 cells, 4 charts) — the disclaimer restated at the top, the full math (EOV correction,
GP regression, the per-mode and joint soft-EM regime-mixture, the honest chi-squared control),
Phase 0's confound/retrofit-signal charts, Phase 1's per-mode false-alarm-rate chart, and Phase
1b/1c's pooling-vs-soft-EM comparison plus the full responsibility-trajectory chart across the
real timeline. Single reference point for this lab as of Phase 1c, per Fraser's request to stop there and
consolidate. Phase 2-original (the FastAPI app) not pursued, per Fraser's call that soft-EM's
modest, precisely-characterized contribution here didn't warrant it. **Phase 2 (2026-08-02)** later
added the sequential-VoI decision layer instead (`RESULTS_PHASE2.md`) — not yet folded into
`SHM_LAB.ipynb`, which still reflects the lab as of Phase 1c only.

## Risks / honest unknowns (stated up front, before any code is written)

- **This lab's contribution is narrower than first drafted, and the plan now says so plainly.**
  The research pass found GP-for-SHM-EOV-removal and regime-switching cointegration already exist
  and are published — this lab tests whether *this specific mechanism*, already validated three
  times elsewhere in this codebase, transfers here, not whether GP or regime-awareness are good
  ideas in the abstract (already answered, by others). Report a parity/no-advantage result as
  plainly as an advantage, if that is what Phase 1 finds.
- **Dataset content is not yet directly inspected.** File names, sensor list, and retrofit dates
  are now confirmed from the dataset owner's own page (KU Leuven, `research/04_kw51_dataset_specifics.md`),
  but the specific per-file size figures were only ever pulled from an automated page summary and
  still could not be cross-checked — treat as approximate until Phase 0 actually downloads
  something.
- **CC-BY-NC-SA 4.0 is non-commercial** — fine for this lab's stated public-good/research framing,
  but would block any future commercial packaging of the app without separately re-licensing or
  swapping the underlying dataset.
- **The retrofit is a single construction-defect correction, not a population of damage cases** —
  confirmed real (not simulated), but this lab can honestly report "did we detect this one real
  event cleanly," not "this generalizes to arbitrary fatigue/damage scenarios," and should say so
  plainly in any write-up.
- **No real economic/asymmetric-cost figures sourced yet for the false-negative side.** Real
  Florida SHM system costs were found (~$29,000 scour system; ~$11,900/pier cathodic protection,
  `research/05_shm_practice_and_cost.md`), but no sourced figure exists yet for the cost of a
  missed real structural change — the economic-layer stretch goal stays explicitly unconfirmed,
  not filled with an invented placeholder.
- **BC-specific data remains inaccessible for now** — BCSIMS's public tier does not expose SHM
  sensor data (confirmed directly from its own design paper); this lab's "close to Vancouver"
  framing is deferred, not abandoned, per Fraser's explicit call to revisit only after completion.
- **This entire lab is theoretical/educational only, per the disclaimer at the top of this
  document** — restated here because it is the single most important risk-management fact about
  this lab, not a formality: nothing produced here is validated for use on any real structure, and
  the liability question independently raised in `research/05_shm_practice_and_cost.md` ("should a
  structural change leading to bridge failure be missed, which party holds responsibility?") is
  exactly why.
