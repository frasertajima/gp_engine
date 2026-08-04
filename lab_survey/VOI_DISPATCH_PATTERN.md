# When does a reserve/capital-sizing lab also warrant a VoI dispatch layer?

**Status: template extracted 2026-08-02 after `grid_reserve_lab`'s Phase 4, updated 2026-08-02
after `shm_lab`'s Phase 2, updated 2026-08-03 after `hydro_reserve_lab`'s Phase 2, updated
2026-08-03 after `climate_cat_lab`'s Phase 3 (four worked examples now — all three originally-
parked ideas plus `grid_reserve_lab` itself have been tried).** Written for the same reason
`EXPLORATION_APPLICATIONS_ROADMAP.md` was written after `mining_gpc_lab`: worked examples exist,
this generalizes them by hypothesis so the next lab doesn't have to rediscover the reasoning from
scratch — not a claim that every candidate below will show a real effect. Four labs, **four
genuinely different outcomes**: `grid_reserve_lab` — modest real positive, variance-driven.
`shm_lab` — null (variance adds nothing) and the SVM-vs-GPC-mean ranking itself reverses at some
cost ratios. `hydro_reserve_lab` — the largest, most robust positive, entirely variance-driven.
`climate_cat_lab` — GPC's mean robustly beats SVM, but variance is a small, real *negative* at
most cost ratios tested, neither null nor positive. Folded into the checklist below (points 1, 2,
6, 7, and the new point 8).

## The pattern, stated precisely

Two GP-soft-EM decision idioms have grown up independently in this codebase:

1. **The reserve/capital-sizing family** (`climate_cat_lab` → `cvar_gp_lab` → `grid_reserve_lab` →
   `shm_lab` → `hydro_reserve_lab`): a regime-mixture GP feeding a *static, annual* sizing number
   — how much reserve/capital to hold for the whole year, a one-shot VaR/CVaR-style quantity.
2. **The Bayesian-decision family** (`bayesian_decision_lab` → `porphyry_cu_gpc_lab`): a reusable,
   dataset-agnostic 3-action core (`decision.py` + `voi.py`) — Skip/Probe/Drill, expected-value
   action selection, and a sequential value-of-information layer where "Probe" buys a cheap,
   noisy signal that sharpens a GP posterior (local 1D Gaussian-conjugate update, no refit) before
   a second action is chosen.

`grid_reserve_lab`'s Phase 4 is the first time these two met: reframing an annual reserve-sizing
lab's regime-mixture GP as the input to a *recurring, discrete* dispatch decision on top of (not
instead of) its existing static sizing number.

## Conditions checklist (check all four before starting)

1. **A genuine discrete state** exists — not just a continuous quantity to size for — that a
   short-horizon signal could resolve before a real commitment deadline. This can be **either** a
   recurring regime (`grid_reserve_lab`: `dgp_simulator.py`'s `regime` field, a real per-day
   boolean already in the oracle DGP) **or a one-time real change-point** (`shm_lab`: KW51's actual
   retrofit, a single dated historical transition, not a repeatable generator). A change-point
   still supports the same decision mechanics, but needs a real historical/ground-truth label
   rather than a resimulable oracle, and a bootstrap convention of repeated fresh splits of that
   one fixed dataset (mirroring `bayesian_decision_lab`/`porphyry_cu_gpc_lab`) rather than repeated
   fresh Monte Carlo draws (`grid_reserve_lab`'s own convention, which doesn't apply when there's
   only one real dataset to resample from).
2. **A cheap information-gathering action exists, distinct from the expensive commitment action**
   (a nowcast/inspection/quote vs. procurement/remediation/drilling). Without this, Probe is
   vacuous and the sequential layer degenerates to the single-shot (already-answered) case. Expect
   real new modeling here, not a relabeling of something that already exists — `grid_reserve_lab`'s
   existing regime-mixture GP was retrospective only; `shm_lab`'s existing models were GP
   *regression*, not classification, with no `(mean, var, prob)` triple anywhere. **Check whether
   an obvious "cheap early signal" already exists in the domain's own data structure before
   inventing one** — `grid_reserve_lab` found it in partial early observability of a shared regime
   draw; `shm_lab` found it in already-computed per-mode z-scores repurposed as classifier
   features. Neither required brand-new data collection, just a new model on top of what existed.
   Also check for **spurious ease**: `grid_reserve_lab` had to shrink its early-reporting feature
   from 20 sites to 1 because 20 already gave AP=1.000, leaving nothing for Probe to resolve;
   `shm_lab` tried the same fix (fewer modes, less training data) and found the real signal stayed
   at AP≈0.97-1.00 regardless — a genuine property of that dataset, not an artifact to engineer
   away. Try shrinking the feature set; if separability doesn't budge, that itself is the finding
   (see point 6).
3. **The commitment decision recurs on a real, defensible cycle** — daily is the strongest fit
   (`grid_reserve_lab`), but **annual is a real, workable cycle too**, not just daily/weekly as
   first drafted: both `hydro_reserve_lab` (the Bureau of Reclamation's genuine annual August
   decision) and `climate_cat_lab` (real property-cat reinsurance treaties, ~60-70% of the global
   market renewing annually at January 1, with a real pre-renewal information-gathering window —
   Monte Carlo Rendez-Vous in September, Baden-Baden in October) confirmed this — **the template's
   own original "weakest fit" flag on `climate_cat_lab` was wrong**; the real institutional cadence
   was simply never checked before assuming a multi-year cycle. Lesson: check the real cadence
   directly before assuming a domain doesn't clear this bar, the same discipline this codebase's
   own research passes already apply elsewhere. **A new cost of annual (vs. daily) cadence, found
   in `hydro_reserve_lab`**: far fewer real decision instances (97 years total, ~24 per test split)
   than a daily domain gives you (thousands) — correspondingly wider bootstrap CIs in relative
   terms, even when (as there) they never cross zero. **Separately** (see point 1): whether the
   underlying oracle is resimulable (`grid_reserve_lab`, `climate_cat_lab`) or a single fixed real
   dataset (`shm_lab`, `hydro_reserve_lab`) determines the bootstrap CONVENTION (fresh Monte Carlo
   draws vs. repeated splits) — this is independent of daily-vs-annual cadence, don't conflate the
   two axes.
4. **A believable, sourced $ constant exists for both the cheap and expensive actions** — reuse
   each lab's own already-sourced figures where possible (`grid_reserve_lab` reused
   `reserve_calc.py`'s VOLL/PJM figures unchanged, deriving `delta_mw`/`c_drill`/`v_drill_gross`
   from the oracle's own data rather than inventing new constants). The one constant that's
   genuinely hard to source honestly is usually the cheap Probe action's own cost — every lab in
   this family so far (`bayesian_decision_lab`, `porphyry_cu_gpc_lab`, `grid_reserve_lab`) has had
   to flag this one as illustrative/unsourced. Expect to as well.

## A fifth thing worth checking that condition 4 doesn't cover: the breakeven probability

`grid_reserve_lab`'s Phase 4 surfaced a mechanism worth checking explicitly in any future
application, not just assumed away: **if the ratio of the two $ constants makes the commitment
action's breakeven probability sit far below the state's true base rate, the "smart" dispatch
policy converges to "always commit," and there's very little room for any forecast — however
good — to add value by skipping.** This isn't a flaw in the method; it's a real property of the
economics, and it should be checked (compute the breakeven probability, compare it to the state's
base rate) *before* running a full bootstrap, not discovered after. A cost-ratio sweep across
breakeven probabilities (`grid_reserve_lab/cost_ratio_sweep_dispatch.py`, following
`bayesian_decision_lab/cost_ratio_sweep.py`'s own pattern) is the concrete tool for finding whether
a given domain's actual economics land in the "always commit" regime or somewhere more
decision-relevant.

## A sixth thing: check whether the classification problem is too easy for variance to matter

`shm_lab`'s Phase 2 found a second, distinct way the mechanism can come back null: **if the
underlying classifier is already near-perfectly separable (AP≈0.999-1.000), posterior variance has
nothing left to resolve — Probe's niche fraction stays near zero and GPC-full is statistically
indistinguishable from GPC-mean at every point on a full breakeven sweep, not just the specific
economics first tried.** This is the mirror image of the "always commit" finding above (that one
comes from the economics; this one comes from the classification problem itself) and should be
checked the same way: look at the fitted model's actual AP/separability before trusting a null
variance result as evidence the mechanism doesn't apply — it may just mean this particular
domain's detection problem is easier than expected. A further, sharper consequence found in
`shm_lab`: when the underlying classifier is this easy, whether GPC's *mean* beats SVM's stops
being a safe assumption — it becomes cost-ratio-dependent and can reverse (SVM winning at some
breakeven probabilities), traced to the MacKay moment-matching correction's shrinkage toward 0.5
being a *bigger* miscalibration the further the true base rate sits from 50% in EITHER direction
(a ~5% base rate hurt in `bayesian_decision_lab`; an ~82% base rate hurt in the other direction in
`shm_lab`). **Do not assume "GPC beats SVM" carries over from prior labs — check it at multiple
points on the breakeven grid, not just one.**

## An eighth thing: variance isn't just positive-or-null — it can be a small, real negative

`climate_cat_lab`'s Phase 3 found a third distinct shape for this family, alongside
`grid_reserve_lab`'s positive and `shm_lab`'s null: **GPC's calibrated mean can robustly beat SVM
while GPC's posterior variance simultaneously makes things measurably WORSE than the mean-only
control** — not a ranking reversal (GPC-full still clearly beats SVM throughout), just a small,
statistically robust tax specifically attributable to carrying the variance, present across most
of a 12-point cost-ratio sweep. Same root mechanism as points 6/7 area (MacKay moment-matching
shrinkage toward 0.5, worse the further the true base rate sits from 50%) — but a genuinely
different shape of outcome than either "helps" or "does nothing." **Practical implication**: don't
treat "GPC-full vs. GPC-mean" as a single yes/no question per domain — check the sign AND magnitude
across the whole cost-ratio range, since a domain can land anywhere from clearly-positive through
null to clearly-negative, and `climate_cat_lab` shows the negative case can coexist with GPC still
being the right overall choice (mean alone already beats SVM handily).

## Worked example: `grid_reserve_lab` Phase 4

- State: `dgp_simulator.py`'s per-day `regime` (drought/normal) — condition 1, free.
- Cheap signal: a new 1-site "fast-reporting" nowcast classifier (`regime_forecast.py`) — real new
  work, condition 2 required it.
- Cycle: daily commit/dispatch decision — condition 3, clearly satisfied (the strongest fit of any
  candidate considered so far).
- Constants: `c_drill`/`v_drill_gross` derived from `reserve_calc.py`'s own sourced VOLL/PJM
  figures; `c_probe` illustrative/unsourced — condition 4, mostly satisfied.
- Result: a real, statistically robust $10.44M/yr [$9.67M, $11.31M] (200 seeds) advantage for the
  full posterior over variance-blind controls — small, but genuine, a third independent
  confirmation of this codebase's recurring VoI finding. Separately, the breakeven probability
  (0.0016) sits 40x below the true drought base rate (~0.065) — the "always commit" regime above —
  which is *why* the advantage is modest rather than large, and why the whole dispatch approach
  costs far more than the lab's existing static annual buffer at these economics.

## Worked example: `shm_lab` Phase 2

- State: KW51's real `retrofit_mask` (0=held-out-normal pre-retrofit, 1=during+post) — condition 1,
  a one-time change-point rather than a recurring regime, handled per the updated checklist above.
- Cheap signal: a new `LaplaceBinaryGPC` fit on the five modes' already-computed frozen-regime-A
  z-scores (`damage_classifier.py`) — real new work, condition 2 required it, and repurposed
  existing computed quantities rather than needing new data.
- Cycle: daily monitoring decision — condition 3, satisfied in spirit (a continuous monitoring
  system re-evaluates daily even though the ground-truth transition itself doesn't recur).
- Constants: neither `c_probe` nor `c_drill`/`v_drill_gross` are independently sourced here — a
  harder condition-4 situation than `grid_reserve_lab`'s (which had VOLL/PJM fully sourced on the
  state side). Handled by making the breakeven sweep the primary result instead of a single
  headline number (see the breakeven-probability section above).
- Result: **the null case for point 6 above** — near-perfect separability (AP≈0.999-1.000, checked
  not engineered), so GPC-full and GPC-mean are bit-identical across the entire 13-point breakeven
  sweep (variance adds nothing), and GPC-mean's advantage over SVM itself reverses at
  moderate-to-high breakeven probabilities. A genuinely different, equally honest outcome from
  `grid_reserve_lab`'s modest-but-real positive result — both are correct, for different domains.

## A seventh thing: watch for label circularity when a label is derived from an aggregate index

`hydro_reserve_lab`'s Phase 2 caught a real bug during its own build, worth checking for explicitly
in any future lab: if the domain already has a convenient aggregate index (e.g. a mean z-score
across several correlated sensors/gauges/sites) that's tempting to use as BOTH the classifier's
label AND, via its individual components, its features, check first whether the label is a
near-deterministic function of those same features. The giveaway there was immediate and cheap to
check: SVM's test AP came back at exactly 1.000. **Fix**: predict the actual decision-relevant
target (one specific site/gauge/asset) from the OTHER correlated sources, not from an aggregate that
already includes it. This is often also the more realistic framing anyway (proxy/leading indicators
informing a specific real decision point, not an aggregate informing itself).

## Worked example: `hydro_reserve_lab` Phase 2

- State: whether Lees Ferry (the real Colorado River Basin compact-accounting point) is a
  moderate-drought-or-worse water year, at `phase0_run.py`'s own already-computed 25th-percentile
  threshold — condition 1, resolved via the real data-derived label (not the 2 real Tier 1/2 events,
  far too few to fit or test on).
- Cheap signal: a new `LaplaceBinaryGPC` fit on the OTHER four gauges' z-scores
  (`drought_classifier.py`) — real new work, condition 2 required it; caught and fixed the point-7
  label-circularity bug along the way (see above).
- Cycle: annual (the real August Bureau of Reclamation decision) — condition 3, resolved: annual is
  a real, workable cadence, not just `grid_reserve_lab`'s daily one, though it comes with far fewer
  real decision instances (97 years total).
- Constants: `c_drill`/`v_drill_gross` derived from this lab's own already-sourced $417/AF and
  $2,400/AF figures (already used, unchanged, by `phase1_run.py`) — the best-sourced economics of
  the three labs so far; only `c_probe` illustrative.
- Result: **the largest, most robust positive result of the three** — GPC-full beats both SVM and
  GPC-mean at every point on a 12-point breakeven sweep, with GPC-mean statistically no better than
  SVM — the cleanest isolation yet of "the value is entirely posterior variance." Traced to having
  both genuine per-year classification ambiguity (AP≈0.87-0.93, neither `shm_lab`'s near-certainty
  nor a tuned synthetic case) and economics landing the breakeven probability in a genuinely
  decision-relevant range relative to the true base rate.

## Worked example: `climate_cat_lab` Phase 3

- State: the oracle's own `regime` (systemic/normal year, `dgp_simulator.py`) — condition 1,
  resimulable, mirroring `grid_reserve_lab`'s posture rather than the two real-data labs'.
- Cheap signal: a new `LaplaceBinaryGPC` fit on a 1-property "early-reporting" subset
  (`regime_forecast.py`) — a near-direct structural port of `grid_reserve_lab`'s own module, since
  this lab's DGP has the identical shape; checked empirically (5+ properties already gave
  AP=1.000, same trap `grid_reserve_lab` hit at 20 sites).
- Cycle: annual (real Jan-1 property-cat treaty renewals, ~60-70% of the global market) —
  condition 3, resolved: **the template's own original "weakest fit" flag on this lab was simply
  wrong**, never having checked the real institutional cadence.
- Constants: real cat-XL Rate-on-Line (ROL = premium/limit) makes the breakeven P(systemic)
  *exactly* the ROL value — the cleanest constants-to-breakeven mapping of any lab in this family,
  though the ROL figures themselves are general market data, not this lab's own already-used
  numbers the way `hydro_reserve_lab`'s were.
- Result: **the third distinct shape (see point 8)** — GPC-mean robustly beats SVM at every ROL
  tested, but GPC-full is measurably *worse* than GPC-mean at 9 of 12 ROL points, a small but real
  negative variance effect, not a null one.

## Candidates for the next reuse (four data points now — all three originally-parked ideas plus grid_reserve_lab itself tried)

- All three originally-parked ideas (`climate_cat_lab`, `shm_lab`, `hydro_reserve_lab`) plus
  `grid_reserve_lab` itself are now done. Four genuinely different outcomes on the core "does
  posterior variance help" question (positive / null / large positive / small negative) — the
  honest conclusion is that this is a per-domain empirical question, not one this template can
  predict in advance; its value is in the checklist (what to check, in what order), not in a
  single expected answer.
- A revisit of `shm_lab` itself, if real inspection/failure-cost figures are ever properly sourced
  (a genuine primary-source FHWA fetch, not the search-summary figure flagged in `research/
  06_inspection_and_failure_cost.md`) — the qualitative finding (variance adds nothing) won't
  change, but the single-run headline number currently rests on illustrative constants only.
- A revisit of `climate_cat_lab`'s Phase 3 to check whether a larger `c_probe`/`sigma_probe2`
  combination ever opens a real Probe niche (niche fraction was 0.0000 throughout at the values
  tried) — not attempted this pass.
- Consider whether a genuinely new domain (outside this specific reserve/capital-sizing family) is
  a better next test than further work inside it, now that all four original candidates are done.

## What this doc is not

Not a claim that VoI dispatch will show a large or even positive effect in any of the labs above —
`grid_reserve_lab` itself is exactly one data point, with a real, honestly-reported downside (the
$173M/yr-more-expensive-than-static-buffer finding) alongside the real upside. Check the four
conditions plus the breakeven-probability question before committing to a full build, the same
posture `EXPLORATION_APPLICATIONS_ROADMAP.md` took for the classification-economics pattern.
