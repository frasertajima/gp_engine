# Code review — `home_energy_lab` (+ the `gp_engine` modules it depends on)

**Reviewed 2026-08-05.** Scope: all 18 Python modules in `home_energy_lab/`, both notebooks, the 8
`research/` files, the 4 `RESULTS_PHASE*.md`, `LAB_PLAN.md`, and the shared `gp_engine` modules this
lab reuses (`decision.py`, `voi.py`, `gp_classifier.py`, `shm_lab/gp1d.py`).

Every finding below was **measured, not inferred** — the reproducing command is given with each one.
Three things I initially suspected turned out to be non-issues on measurement; they are recorded in
§5 rather than dropped, because "checked and it holds" is load-bearing information here.

**Overall.** The engineering discipline is high and unusually well documented — simplifications are
stated at the point of use rather than buried, three real bugs were self-caught and recorded during
the build, and `research/07`'s balcony-solar legality check is a genuine model of chasing an
inconvenient answer to a primary source and then propagating it into both notebooks. The problems
below are not sloppiness; they are two structural modeling errors that quietly invalidate two of the
lab's four headline claims, plus one research gap large enough to move a third.

---

> **UPDATE 2026-08-05 — C1 and C2 are FIXED and Phase 1 has been re-run.** See `RESULTS_PHASE1.md`
> for the new eight-rung ladder. Both fixes changed the headline: the cheapest policy now consumes
> no fitted model at all ($613/yr, calendar + fixed peak-window reserve), beating the GP ($624) and
> the corrected regime layer ($638). Notably, with a lever that provably *can* move the number
> (reserve correlation +0.660 with actual net load), regime-awareness still loses to a constant
> reserve of the same mean — so the family's "regime-awareness doesn't automatically help" finding is
> now genuinely earned rather than assumed.
>
> **FURTHER UPDATE — H1, H2, H3 also fixed (2026-08-05).** Crediting export (H1) **changed two of the
> C1/C2 conclusions**, and the write-ups have been corrected: the GP moves from $1 *behind* a
> model-free calendar rule to ~$5 *ahead*, and the regime layer's penalty shrinks from $22/yr to
> $4/yr — a null rather than a negative. The strong "no fitted model needed" claim did not survive
> the economics fix; the weaker and still-useful form (forecasting is worth ~1% of the bill, not the
> 6% originally implied) does.
>
> **FINAL UPDATE — all M and L items fixed and re-run (2026-08-05).** Highlights: **M1** (currency)
> now converts rebates explicitly via a `rebate_currency` key and ships a self-test proving
> FX-invariance — the mixed-currency case was over-crediting by 38% ($1,500 vs $2,070 on one
> battery). **M3** gave `build_payoff_matrix_voi` an optional `v_drill_residual` (default 0.0, so the
> other five VoI labs are bit-identical); the derived breakeven moves 0.3738 → 0.0495. **L4** replaced
> the 7-hour off-peak proxy with BC Hydro's real 8-hour 11pm-7am window. Shared modules
> (`gp1d.py`, `decision.py`, `gp_classifier.py`) were changed **only** in backward-compatible ways,
> since six other labs depend on them. Phases 1, 2 and 3 all re-run; **no conclusion reversed.**
>
> *One error of my own, caught by the work itself:* the first M3 breakeven inversion used
> `net/v_gross`, valid only when the residual is zero. It made drilling negative-EV in both states
> above p=0.10 and collapsed the entire 200-seed sweep to a uniform $0.00. The all-zeros column is
> what exposed it — see `RESULTS_PHASE2.md`.

## 1. Critical — findings that invalidate a published conclusion

### C1. Method 3's regime margin is structurally dead on exactly the days it exists for  — ✅ FIXED 2026-08-05

`gp_forecast_model.predict_targets` sets the target SOC to the *predicted daily net load*, clipped to
battery capacity:

```python
targets[d] = float(np.clip(mean[0], 0.0, capacity_kwh))   # gp_forecast_model.py:52
```

Daily net load averages 14.7 kWh and exceeds the 13.5 kWh capacity on **49.5%** of days. On those
days the target saturates at 13.5. `regime_mixture.predict_targets` then adds its stress margin and
re-clips against the same ceiling (`regime_mixture.py:61`) — so on every saturated day the margin is
mathematically forced to zero.

Measured over the real 2017-2025 test record:

| | value |
|---|---|
| Method 2 targets pinned at capacity | 49.6% of days |
| Method 3 margin nonzero | 50.4% of days |
| Mean **actual** net load on days the margin fires | **3.9 kWh** |
| Mean **actual** net load on days the margin is zero | **25.7 kWh** |

The margin fires **only** on low-demand summer days and is **exactly zero on every high-demand day**.
It is not a weak stress-response; it is an inverted one.

**Consequence.** `RESULTS_PHASE1.md` and `LAB_PLAN.md` report Method 3 as "a small, real negative on
top of Method 2" and count it as *"a third instance of this codebase's 'regime-awareness doesn't
automatically help' finding (after `climate_cat_lab`'s Phase 3 and part of `shm_lab`'s Phase 2)."*
That claim is not supported by this experiment. Phase 1 did not test regime-awareness; it measured
the cost of adding pre-charge margin to summer days. The $8/yr penalty is exactly what you would
predict from that, and says nothing about the mechanism. **The claim should be withdrawn from
`LAB_PLAN.md` and `RESULTS_PHASE1.md` until the layer is re-run against something unsaturated.**

This also propagates: `LAB_PLAN.md`'s Phase 2 summary leans on it — *"Two independent layers of this
lab (Phase 1's regime-mixture margin, Phase 2's VoI variance) now agree."* Only one of those two
layers actually reported on its mechanism. (Phase 2's own null is sound — see §5.)

**Fix.** The decision variable is the problem: target-SOC-clipped-at-capacity is a saturating
function of the forecast, which destroys the forecast's information precisely in the high-demand
tail. The regime layer needs to modulate a quantity with headroom on stress days. Options, cheapest
first:
1. Have the margin control the **discharge reserve floor** (don't let the battery drop below X% on a
   predicted stress day) rather than the charge ceiling — that has headroom at saturation.
2. Have it control **how early off-peak charging starts** / the charge-rate schedule, not the endpoint.
3. Keep the target in net-load space and let the margin change the *number* of off-peak hours served
   directly from grid, which is unbounded above.

Reproduce:
```
python3 -c "import numpy as np,datetime; from daily_agg import build_daily; import gp_forecast_model as gpf, regime_mixture as rm; \
daily=build_daily(); daily.index=daily.index.date; yrs=np.array([d.year for d in daily.index]); \
tr=daily.loc[yrs==2016]; td=daily.index[(yrs>=2017)]; nl=daily['net_load_kwh']; \
gp=gpf.fit(tr); gp3,gmm=rm.fit(tr); \
v2=np.array([gpf.predict_targets(gp,td,nl)[d] for d in td]); v3=np.array([rm.predict_targets(gp3,gmm,td,nl)[d] for d in td]); m=(v3-v2)>1e-9; \
print('saturated %.3f | margin fires on days with mean net load %.1f vs %.1f'%((v2>=13.499).mean(), nl.loc[td][m].mean(), nl.loc[td][~m].mean()))"
```

### C2. Method 2's win is not attributable to the GP — a calendar rule with zero data ties it  — ✅ FIXED 2026-08-05

`RESULTS_PHASE1.md`'s headline is *"Method 2 (plain GP forecast) wins ($624/yr)."* I ran the two
ablations the method ladder is missing, on the identical simulator, rates, and test years:

| Method | $/yr | What it uses |
|---|---|---|
| 0 — naive reactive | 689 | nothing |
| 1 — TOU always-full | 661 | clock only |
| **2 — GP forecast** | **624** | fitted GP1D on lag-1 net load |
| 3 — GP + regime mixture | 632 | + GMM (see C1) |
| **A — persistence, no GP at all** (`target = clip(yesterday's actual net load)`) | **623** | one lookup, no model |
| **B — calendar only** (`full charge Oct–Mar, none Apr–Sep`) | **623** | *no data whatsoever* |

Both ablations **beat** the GP, by $1/yr. The entire $37/yr advantage of Method 2 over Method 1 is
"don't pre-charge in summer" — a two-line seasonal rule. The GP contributes nothing measurable.

This is consistent with the GP's own predictive skill: RMSE 7.04 kWh vs. 7.28 for raw persistence
and 13.77 for a constant — it barely improves on the lag-1 value it is fed.

**Consequence.** The Phase 1 conclusion should be restated as *"proactive off-peak pre-charging beats
reactive control by ~$65/yr, and seasonal on/off captures all of it; day-ahead forecasting adds
nothing"* — which is a **more** interesting finding for this family's thesis than the current framing,
and points the same direction as Phase 2's null. Phase 3 and `scenario_engine` both use Method 2 as
their control policy; that is harmless (a calendar rule gives the same numbers) but should be noted.

**Fix.** Add A and B to `naive_baselines.py` as Methods 0b/1b and re-run `phase1_run.py`. This is
~15 lines and materially strengthens the lab.

Reproduce: the ablation script is inline in the reviewer's session; both targets are one-liners —
`{d: float(np.clip(nl.loc[d-timedelta(1)],0,13.5)) for d in test_dates}` and
`{d: 13.5 if d.month in (10,11,12,1,2,3) else 0.0 for d in test_dates}`, both passed to
`simulate_with_targets(..., tod_aware=True)`.

---

## 2. High — a research gap that moves a headline number

### H1. Grid export is simulated everywhere and monetized nowhere; net metering is absent from `research/`  — ✅ FIXED 2026-08-05

> **Resolved.** `research/08_bc_hydro_export_compensation.md` added from two live bchydro.com primary
> sources. **The lookup mattered more than expected: BC Hydro's program changed on 2026-07-01**, five
> weeks before this check — legacy net metering (RS 1289, annual kWh banking) closed to new
> customers, replaced by the Self-Generation Service Rate (RS 2289): a flat **$0.10/kWh monetary
> credit settled per billing cycle**, capped at the month's energy charge (the basic charge stays
> payable). RS 2289 is the correct rate here specifically because accepting the BC Hydro solar rebate
> that `capacity_sizing.py` already models *forces* the transition to it. Implemented in
> `rate_model.total_cost_with_tod(grid_export_kwh=...)` and `scenario_engine.total_cost`, both
> exactly back-compatible when export is not passed (verified to 9e-13). Phase 3 re-run — see
> `RESULTS_PHASE3.md`.

`battery_sim.py`, `dispatch_sim.py`, and `scenario_engine.py` all compute `grid_export_kwh`.
`rate_model.total_cost_with_tod` takes only `grid_import_kwh`. Export earns **$0** across the entire
lab. The 8kW reference system exports **2,734 kWh/yr**.

I grepped all 8 research files, both notebooks, and all four RESULTS docs: the strings *net metering*,
*net-metering*, *feed-in*, and *buyback* appear **zero times**. This is the one substantive domain
assumption the research pass never examined — notable because BC Hydro's net metering program
(RS 1289) is a real, current, well-documented program, and `research/05` went to bchydro.com for the
rebate structure without picking it up.

**Measured impact on the Phase 3 headline** (same grid, same GP, same test years, export credited at
~9.99¢/kWh):

| System | Total $/yr, export at $0 (published) | Total $/yr, with net metering |
|---|---|---|
| 4 kW / 0 kWh | **1,359 ← published optimum** | 1,254 |
| 6 kW / 0 kWh | 1,466 | **1,218 ← new optimum** |
| 8 kW / 0 kWh | 1,643 | 1,232 |
| 12 kW / 0 kWh | 2,038 | 1,273 |
| 8 kW / 13.5 kWh | 2,560 | 2,287 |

**The "no battery" half of Phase 3's conclusion is robust** — battery loses at every solar size under
both treatments, by a wide margin. **The "4 kW" half is not**: the optimum moves to 6 kW and total
cost falls 10%. And the direction is systematic, not incidental — zero export credit penalises each
additional kW of solar exactly in proportion to how much surplus it creates, so the published grid
is biased toward small systems by construction.

`RESULTS_PHASE3.md:78` even names the mechanism without following it — *"kW mostly produces
exportable summer surplus rather than winter self-consumption"* — that surplus is being valued at
zero, silently.

**Fix.** (a) Add `research/08_bc_hydro_net_metering.md` sourced to BC Hydro RS 1289 — the credit
rate, whether credits are monthly-rolling vs. annually-settled, and the annual-excess treatment
(these differ, and the annual-settlement rule matters a lot for oversized systems). (b) Add
`export_credit_per_kwh` to `rate_model` and to `RATE_PRESETS`. (c) Re-run Phase 3 and the
`SCENARIO_BUILDER` payback figures — payback years for every solar-bearing scenario currently assume
surplus is worthless, so all of them are pessimistic.

### H2. A stated research deferral was never discharged  — ✅ FIXED 2026-08-05

> **Resolved.** `research/09_battery_spec_primary_source.md` added from Tesla's own Powerwall 3
> datasheet, downloaded directly. Three real corrections fell out: (1) **charge power is 5 kW, not
> the 11.5 kW discharge rating** the lab applied to both directions; (2) round-trip efficiency is
> **0.913, derived** as 89%/97.5% — using the 89% headline would double-count the PV inverter loss
> `solar_model.py` already applies, a trap worth recording; (3) amortization moved from 12 years to
> the warranted **10**. Degradation is now modelled as lifetime-mean effective capacity while capital
> is charged on nameplate. **These moved every Phase 1 method by a near-uniform $4-5/yr and reordered
> nothing** — H2 is a robustness fix, not a conclusion change. End-of-life retention remains the one
> unsourced figure (Tesla publishes the term, not the percentage; the warranty PDF 404s), so Phase 3
> now **sweeps** it — the optimum carries no battery at every level from 100% to 60%.

`LAB_PLAN.md:59-60`: *"Battery round-trip-efficiency/degradation spec explicitly **not yet sourced** —
deferred to Phase 0, not invented."* Phase 0 never sourced it. `battery_sim.py:14-15` still carries
`DEFAULT_ROUND_TRIP_EFF = 0.90` with the comment *"research/03 flags this as not yet sourced to a
primary spec sheet."* No research file covers it. Meanwhile `LAB_PLAN.md`'s Files section reports
`research/ — **DONE.**`

Separately, **degradation is not modeled at all**, while `capacity_sizing.py` amortizes the battery
over 12 years. A real pack loses meaningful usable capacity across that window, so year-12 savings
are overstated. The direction favours the existing "no battery" conclusion, so no result flips — but
the deferral should be either discharged or re-flagged as open, not left silently marked done.

### H3. `research/04` asked for two rate structures; only one is ever scored  — ✅ FIXED 2026-08-05

> **Resolved, both halves.** (1) Every Phase 1 method now reports its bill under TOD opt-in *and*
> tiered-only and takes the cheaper, since the TOD layer is genuinely optional. TOD opt-in wins for
> all nine methods, so the earlier always-TOD practice was correct — it had simply never been
> demonstrated. (2) **Method 4**, a tier-threshold-aware policy (suppress off-peak pre-charging once
> the month's running total passes the 675 kWh Step 1 threshold, no lookahead), is now in the ladder
> at **$515/yr, mid-pack**. At this household's ~11,600 kWh/yr the threshold is crossed early enough
> most winter months that gating on it mostly forgoes cheap off-peak energy.

`research/04_vancouver_real_calibration_case.md:64-69` states a *"genuine, real design implication"*:
because the default BC Hydro rate is a **step/tier threshold**, the real optimization question is
partly *"does shifting or reducing consumption keep this month under the Step 1 threshold"* — and
concludes *"Both structures (tiered-threshold and optional TOD) should be modeled as real, named
alternatives in Phase 1/2, not collapsed into one simplified rate."*

Every call site in Phases 1-3 passes `use_tod=True`. The tier-threshold-management question is never
tested — no method in the ladder is aware of the 675 kWh/month step at all. (I did verify TOD opt-in
is the rational choice for all four methods, so there is no comparison bias — see §5.3. The gap is
that a whole class of policy the research explicitly identified is unexamined.)

---

## 3. Medium

**M1 — ✅ FIXED.** Every entry may declare `rebate_currency` (defaults to its own `currency`, the intuitive reading of a self-contained entry); `rebate_per_unit`, `rebate_cap` and `rebate_fixed` are all converted before the `min()`. Rebates are additionally floored at the purchase price, and an unknown currency now raises instead of failing obscurely. A six-part self-test in `__main__` proves FX-invariance, the mixed-currency case, default inheritance, the price floor, and loud failure. \
**M1. `scenario_engine._hardware_capital` silently mixes currencies in the rebate path.** The module
docstring promises *"this module does not silently mix currencies; `to_base_currency` is explicit."*
It isn't, for rebates:

```python
gross  = to_base_currency(quantity * hw["unit_cost"], hw["currency"], fx_rates)   # converted
rebate = min(quantity * hw["rebate_per_unit"], cap, pct_cap)                      # NOT converted
```
(`scenario_engine.py:176-181`)

This happens to be correct today only because `anker_solix_*` deliberately pairs a USD `unit_cost`
with a CAD BC-Hydro `rebate_per_unit`. Any user-supplied non-CAD option with a same-currency rebate —
the exact use case the catalog is built for — is wrong by the FX factor (38% for USD). **Fix:** add
an explicit `rebate_currency` key defaulting to `currency`, and route the rebate through
`to_base_currency` too.

**M2 — ✅ FIXED.** `build_dataset` returns raw net load; the threshold is derived inside `fit_classifier` from the training split alone. The split is consequently unstratified — class balance measured stable within a point of 25% across seeds. Test AP unchanged at ≈0.82. \
**M2. Label-threshold leakage in `stress_classifier.build_dataset`.** The 75th-percentile high-demand
threshold is computed over the whole 2017-2025 pool (`stress_classifier.py:47`) and the train/val/test
split is drawn from it afterward, so the label definition carries a scalar of test-set information.
At n=3,286 the effect is negligible, but it is free to fix: compute the threshold on the training
split inside `fit_classifier`. The same applies to `derive_dispatch_constants`, which computes
`delta_kwh` over the full pool.

**M3 — ✅ FIXED.** See the banner above. \
**M3. The VoI drill payoff overstates drill's downside.** `build_payoff_matrix_voi` sets
`V[drill, waste] = -c_drill` — if the day turns out normal, the pre-charge is scored as a total loss.
Physically the energy is still in the battery and still displaces load; only the *arbitrage premium*
is forfeited. The correct waste payoff is roughly `-delta_kwh * (offpeak_rate - standard_value)`, not
`-delta_kwh * offpeak_rate`. This inflates the breakeven probability (currently 0.374). It does not
change Phase 2's null — the sweep in §5.2 covers breakevens from 0.05 to 0.90 — but the derived
constant is not the right one.

**M4 — ✅ FIXED.** `SIGMA_PROBE2_LOCAL = 0.10` is now set in `run_dispatch_voi.py`. Probe niche remains exactly 0.0000. \
**M4. `voi.SIGMA_PROBE2_DEFAULT` is inherited from a different lab's variance range.** The constant is
documented as *"tuned so Probe has a real (non-degenerate) niche on this dataset's actual variance
range (~0.08-0.38)"* — that is the **mining** lab's range. This lab's is 0.014-0.66. `run_dispatch_voi`
imports the foreign default unchanged. **The conclusion survives** (see §5.2) but the module should
set its own value rather than inherit a constant whose docstring describes someone else's data.

---

## 4. Low — including the `gp_engine` shared modules

**L1 — ✅ FIXED.** `psi_prev` is assigned before the `break`. \
**L1. `gp_classifier.py:239-241` — stale `log_marginal` on convergence.** The Newton loop `break`s on
convergence *before* `psi_prev = psi`, so `log_marginal = psi_prev - 0.5*logdetB` and
`fit_info.psi` are computed from the **previous** iteration's ψ, not the converged one. Bounded by
`tol=1e-9`, so harmless at the default — but silently wrong by one Newton step, and it would bite
anyone using `log_marginal` for model selection with a looser tol. One-line fix: assign `psi_prev = psi`
before the `break`.

**L2 — ✅ FIXED (opt-in).** `fit(center=True)` centres and `predict` adds the offset back. Default stays `False` so `shm_lab`'s published results are bit-identical; demonstrated far-field reversion to 0.000 uncentred vs the data mean centred. \
**L2. `shm_lab/gp1d.py` has no mean function.** Zero-mean GP prior fit against data with mean
14.6 kWh. **Checked, and it does not bite here** — RMSE 7.036 uncentered vs. 7.037 centered — because
the optimizer compensates by inflating `sigma_f2` to 1,580 and `ell` to 68 (vs. 866 and 53 when
centered), effectively fitting a near-linear function. But those hyperparameters are a symptom, and
the model is one dataset away from reverting predictions toward zero in the far field. Since this
module is shared, recommend centering `y` in `fit` and adding the mean back in `predict`.

**L3 — ✅ FIXED.** Docstring rewritten; the phantom `build_voi_payoff` reference is gone. \
**L3. `voi.probe_value`'s docstring is self-contradictory** (`voi.py:99-101`): it says `c_probe`
*"defaults to..."* then *"actually just reads the probe cost baked into V's off-diagonal if not
given; see build_voi_payoff below"*. The code raises `ValueError` if `c_probe is None`, and
`build_voi_payoff` does not exist anywhere in the codebase.

**L4 — ✅ FIXED.** Real 11pm-7am window; `dispatch_sim` credits hour-23 charging to the following day's plan. Everything got ~$10-20/yr cheaper; nothing reordered. \
**L4. `rate_model`'s off-peak window is 7 hours, not the real 8.** Hours 0-6 vs. the real 11pm-7am.
Documented at the top of the module, but worth noting the consequence: hour 23 pays the standard rate
and the pre-charge window is 12.5% shorter than reality, so Methods 1-3 are modeled slightly *worse*
than they would really perform. Conservative direction, but it interacts with C2 — a real 8-hour
window would give the seasonal rule more room, not less.

**L5 — ✅ FIXED.** Marked superseded inline. \
**L5. `LAB_PLAN.md:58` still states the US 30% federal credit** in Domain background with no
superseded marker, while line 201 correctly records the correction. `research/03` is marked
superseded in `RESEARCH.md` but is still cited unqualified in the plan's own summary.

---

## 5. Checked and sound — three suspicions that did not survive measurement

Recorded because these are the load-bearing correctness claims, and they hold.

**5.1 The energy accounting is correct.** `battery_sim.py`'s per-timestep AC-bus balance and
SOC-trace consistency self-tests both pass to floating-point precision, and
`dispatch_sim.simulate_with_targets(targets=0, tod_aware=False)` reproduces `battery_sim.simulate`
exactly. `rate_model`'s self-test reproduces the real Mar 20-31 bill to the cent. The double-discharge
fix recorded in `RESULTS_PHASE1.md` is correctly implemented.

**5.2 Phase 2's null result is robust — this is the strongest-verified finding in the lab.** I was
suspicious of M4 (foreign `sigma_probe2`), so I swept it against `c_probe` on the real fitted
classifier. Probe niche fraction:

| σ²_probe \ c_probe | 0.01 | 0.05 | 0.10 | **0.15** | 0.30 |
|---|---|---|---|---|---|
| 0.001 (near-perfect probe) | 0.0328 | 0.0012 | 0.0000 | **0.0000** | 0.0000 |
| 0.01 | 0.0280 | 0.0012 | 0.0000 | **0.0000** | 0.0000 |
| 0.15 (published) | 0.0097 | 0.0000 | 0.0000 | **0.0000** | 0.0000 |
| 2.0 | 0.0012 | 0.0000 | 0.0000 | **0.0000** | 0.0000 |

Even a *noiseless* probe finds a niche on only 3.3% of days, and only at an implausibly cheap
c_probe. At the published $0.15 it is exactly zero everywhere. The payoff structure genuinely never
rewards resolving the uncertainty — the mechanism `RESULTS_PHASE2.md` claims is the mechanism that is
there. Unaffected by C1/C2.

**5.3 The TOD comparison is fair — no bias against Method 0.** I suspected charging the non-TOD-aware
Method 0 a TOD surcharge it would rationally decline. Measured cost under both elections:

| Method | TOD opt-in | TOD opt-out | rational choice |
|---|---|---|---|
| 0 naive | **689** | 712 | opt in |
| 1 always-full | **661** | 932 | opt in |
| 2 GP | **624** | 853 | opt in |
| 3 GP+regime | **632** | 876 | opt in |

Opt-in is optimal for every method including the naive one, so the published comparison is the
rational-agent comparison. No issue.

**5.4 The heating-degree-day convention is consistent.** `load_model.hourly_load_kw` applies
`max(0, 18 − T)` at *hourly* resolution while the 0.9006 kWh/HDD coefficient was derived from
*daily-mean* temperatures — Jensen's inequality says hourly should run hot. Measured: effective HDD
7.893 hourly vs. 7.909 daily-mean, a **0.2%** difference. Vancouver's diurnal range is small enough
that it doesn't matter. Non-issue.

**5.5 Both notebooks execute clean** — 11 and 18 cells, 0 error outputs. `research/07`'s BC
balcony-solar illegality finding is carried into both, so the 1.2-year payback headline is not
presented as actionable in BC. That is exactly the right handling.

---

## 6. Recommended order of work

1. **C1** — re-target the regime margin so it can act on stress days; re-run Phase 1. Until then,
   withdraw the "third instance of regime-awareness not helping" claim from `LAB_PLAN.md` and
   `RESULTS_PHASE1.md`.
2. **C2** — add the persistence and calendar ablations to the ladder; restate Phase 1's headline.
   (~15 lines, and it strengthens the lab's own thesis.)
3. **H1** — source BC Hydro net metering, add `export_credit_per_kwh`, re-run Phase 3 and the
   `SCENARIO_BUILDER` paybacks. Keep the "no battery" conclusion; re-derive the solar size.
4. **H2/H3** — either discharge the battery-efficiency deferral or re-mark it open; add a
   tier-threshold-aware method or record explicitly why it was dropped.
5. **M1, M2, L1, L3** — small, self-contained correctness fixes.
6. **M3, M4, L2** — engine-level cleanups, none of which change a current result.

Note that C1, C2, and H1 are all failures in the same direction: **a modeling layer silently loses
its ability to affect the outcome, and the flat result is then read as a finding about the
mechanism.** The lab's habit of stating simplifications at the point of use is what makes these
findable at all — the gap is that no ablation was run to confirm each layer could still move the
number before its null was interpreted.
