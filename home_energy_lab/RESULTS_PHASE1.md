# Phase 1 results — the dispatch method ladder

**Re-run twice on 2026-08-05**: first after `CODE_REVIEW.md` C1/C2, then again after H1/H2/H3.
The 2026-08-04 original and the first re-run are both superseded; §5 records what changed at each
step rather than quietly dropping it.

Real 8kW/13.5kWh illustrative system. Fit on one real training year (2016, 366 days), scored on the
real held-out 2017-2025 record (3,287 days, 9 years), BC Hydro's real tiered rate with the optional
TOD layer and the real RS 2289 export credit.

**Headline: every policy that pre-charges off-peak lands in a $485-$521/yr band (a $36 spread,
7.4%), and the top three are within $5/yr of each other — about 1% of the bill, i.e. a tie.** The
one large, robust effect is proactive off-peak pre-charging itself ($649/yr → $485-521/yr, a real
$130-165/yr). Neither the GP forecast nor the soft-EM regime layer produces a difference this model
can resolve.

> **An honest correction to the first re-run.** Earlier on 2026-08-05 this file reported that a
> model-free calendar rule *beat* the fitted GP, and that the regime layer was a clear $22/yr
> negative. Both statements were computed with grid export valued at $0. Once export is credited at
> BC Hydro's real rate (H1), the GP moves from $1 behind the calendar rule to ~$5 ahead, and the
> regime layer's deficit shrinks from $22 to $4. **The strong form of that claim did not survive its
> own economics fix.** What survives is the weaker, still-useful form: the GP's contribution is
> ~1% of the bill, not the $37/yr the original 2026-08-04 framing implied.

---

## 1. The ladder

Nine methods: the original four, four **ablations**, and Method 4 (added for H3). The ablations
exist because the original four-method ladder could not distinguish "the model helps" from "the
model is structurally unable to do anything" (§5) — every fitted layer is now bracketed by a
model-free control using strictly less information.

| Method | $/yr | Grid import kWh/yr | Export kWh/yr | Self-suff. | What it consumes |
|---|---|---|---|---|---|
| 0 — naive reactive | 649 | 5,523 | 1,689 | 52.6% | nothing |
| 1 — TOU always-full | 506 | 7,434 | 3,452 | 36.2% | clock only |
| 0b — persistence *(ablation)* | 516 | 6,718 | 2,742 | 42.4% | yesterday's net load, **no model** |
| 1b — calendar only *(ablation)* | 521 | 6,583 | 2,620 | 43.5% | **no data at all** |
| 2 — GP forecast | 516 | 6,725 | 2,749 | 42.3% | fitted GP1D |
| 4 — tier-threshold aware *(new)* | 515 | 6,742 | 2,834 | 42.2% | monthly running total |
| 3 — GP + regime mixture | 489 | 7,093 | 3,165 | 39.1% | fitted GP1D + soft-EM GMM |
| **3b — GP + constant reserve** | **485** | 6,931 | 2,981 | 40.5% | fitted GP1D |
| 3c — model-free reference *(ablation)* | 490 | 6,781 | 2,839 | 41.8% | **no fitted model of any kind** |

All eight proactive methods span **$485–$521/yr — a $36 (7.4%) band** — and the top three (3b $485,
3 $489, 3c $490) span **$5**. Against a model whose own resolution is at best a few dollars a year,
the top of this ladder is a tie, and this file now reports it as one rather than ranking within the
noise.

**Two things are large enough to be real**, and neither is a forecasting result:
- **Proactive off-peak pre-charging: $649 → $485-521/yr ($130-165).** By far the dominant effect.
- **A peak-window discharge reserve: another ~$25/yr** (compare 2 at $516 with 3b at $485, same
  targets, reserve added).

**A new effect the export credit created**: Method 1 (charge to full every night, no forecast) jumps
from worst-of-the-smart-methods to $506/yr, beating both the GP and the calendar rule. With
off-peak import at 5.97¢ and a flat 10¢ export credit, keeping the battery full and exporting all
solar is a genuine arbitrage — the opposite of what the uncredited-export model implied. This is a
direct, and somewhat uncomfortable, consequence of RS 2289's flat rate; see §6.

---

## 2. Finding 1 — proactive off-peak pre-charging is worth ~$160/yr; forecasting adds ~1%

Method 0 → 3b is $649 → $485/yr ($164). Almost none of that is forecast-driven:

| Comparison | Pre-export-credit | With export credit |
|---|---|---|
| Method 2 (fitted GP) vs 1b (calendar, **zero data**) | 624 vs 623 — calendar wins by $1 | 516 vs 521 — **GP wins by $5** |
| 3b (GP + reserve) vs 3c (calendar + same reserve) | 616 vs 613 — calendar wins by $3 | 485 vs 490 — **GP wins by $5** |

**This is a correction to what this file said earlier today.** With export valued at $0, a calendar
rule genuinely beat the fitted GP and the write-up said so. Crediting export reverses the sign: the
GP now wins both head-to-head comparisons by a consistent ~$5/yr. The consistency across two
independent pairs makes it more credible than a single margin would be — but $5/yr is **~1% of the
bill**, and the same "inside the model's resolution" standard applied to Phase 3's $7/yr margin
applies here too.

The GP's own predictive skill still explains why the effect is so small: RMSE 7.04 kWh vs. 7.28 for
raw persistence and 13.77 for a constant — it barely improves on the lag-1 value it is fed. **The
honest statement is that day-ahead forecasting is worth about 1% here, not the $37/yr (6%) the
original 2026-08-04 framing implied.**

## 3. Finding 2 — a peak-window discharge reserve is worth another ~$25/yr

The genuinely new lever this re-run added. Because BC Hydro's TOD layer is ±5¢, a kWh of battery
energy is worth 10.97¢ spent in a standard-rate hour but 15.97¢ saved for the 4–9pm surcharge
window. Holding SOC back through the standard-rate hours (`dispatch_sim.RESERVE_HOURS`, hours 7–15)
is close to free money. Compare Method 2 ($516) with Method 3b ($485) — identical charge targets,
reserve added.

Swept on the model-free policy (**these figures predate the export credit**, so read the shape, not
the levels — the sweep was not re-run after H1):

| Reserve (kWh) | 0 | 2 | 4 | **6** | 8.82 | 10 | 12 | 13.5 |
|---|---|---|---|---|---|---|---|---|
| $/yr (pre-export-credit) | 623 | 620 | 616 | **612** | 613 | 621 | 636 | 653 |

A real interior optimum near 6 kWh (~44% of capacity). Over-reserving is actively harmful — at a
13.5 kWh floor the battery never discharges before 4pm and the policy is *worse than no reserve at
all* ($653 vs $623). Re-running this sweep under the export credit is the obvious next refinement,
since the reserve interacts with export (holding charge back means less room for solar).

## 4. Finding 3 — regime-awareness genuinely does not help, and this time that is a real test

**This is the finding the original run claimed but did not actually measure.**

Method 3 now sizes the peak-window reserve by yesterday's soft-EM P(stress) × the mixture's
stress-vs-normal mean gap (22.21 kWh). The response is correctly oriented on real data — correlation
**+0.660** with actual net load, mean 19.7 kWh on its top-third days vs. 1.7 kWh on its bottom-third
days. It has real headroom on stress days and it fires on the right ones.

It still does not help:

| | Pre-export-credit | With export credit |
|---|---|---|
| 3 — reserve sized by P(stress) | 638 | 489 |
| 3b — **constant** reserve, same 8.82 kWh mean | **616** | **485** |
| regime layer's cost | **$22/yr worse** | **$4/yr worse** |

Allocating the *same average amount* of reserve by regime probability is worse than spreading it
evenly — but crediting export shrinks that penalty from $22/yr to $4/yr, i.e. from a clear negative
to **within noise**. The directional mechanism still makes sense: on the highest-demand days the
regime-sized reserve saturates at capacity, so the battery does not discharge before 4pm and the
household imports at the standard rate all day, then can only return ~13.5 kWh into a five-hour
window. Those days need battery energy *throughout*, not concentrated.

**The correct claim is now the weaker one: the soft-EM layer does not help, rather than that it
actively hurts.** It is still a legitimate fourth instance of the family's "regime-awareness doesn't
automatically help" finding (after `climate_cat_lab`'s Phase 3 and part of `shm_lab`'s Phase 2) —
and unlike the 2026-08-04 version, it rests on a lever verified capable of moving the number
(correlation +0.660 with actual net load) *before* its null was interpreted. But it is a null, not a
negative, and this file previously overstated it.

---

## 5. What changed from the 2026-08-04 run, and why

Two errors, both found by `CODE_REVIEW.md`, both the same kind: *a layer silently lost its ability to
affect the outcome, and the flat result was read as a finding about the mechanism.*

**C1 — the regime margin was structurally dead.** The original Method 3 added its stress margin to
Method 2's overnight *charge target*. That target is clipped at battery capacity
(`gp_forecast_model.py:52`), and real daily net load exceeds 13.5 kWh on **49.5%** of days — so on
exactly the high-demand days the layer exists for, the target was already saturated and the margin
was clipped to zero. Measured: the old margin fired only on days whose actual net load averaged
**3.9 kWh** (summer) and was **exactly zero** on the days averaging **25.7 kWh**. It was an inverted
stress response. The original "$632/yr, a small real negative" measured the cost of adding pre-charge
to summer days and said nothing about regime-awareness. **Fixed** by moving the stress response to
the peak-window reserve, which is not bounded by the charge target (§4).

**C2 — Method 2's win was never attributed.** The original run reported "Method 2 (plain GP forecast)
wins" with no model-free control in the ladder. Both ablations added here match or beat it (§2). The
headline is now stated as what it is.

**Superseded numbers:** Method 3's $632/yr (now $638/yr under the corrected, live mechanism), and the
claim that Method 2 was the best available policy (now Method 3c, model-free, at $613/yr).

**Still true, and worth keeping:** the original run's counter-intuitive self-sufficiency finding
holds and is if anything sharper. Method 0 still has the **highest** self-sufficiency (52.5%) while
being the **most expensive** ($689/yr); the winning Method 3c sits at 41.5% self-sufficiency and
$613/yr. Self-sufficiency does not capture *when* grid energy is bought — every method that beats
Method 0 buys *more* total kWh (round-trip losses) at a much lower average $/kWh.

`LAB_PLAN.md`'s Phase 2 summary previously leaned on this phase as one of "two independent layers
agreeing" that the plain forecast does all the useful work. That conclusion survives — it is now
stronger, since not even the plain forecast earns its keep — but its supporting argument had to be
rebuilt. Phase 2's own null result is unaffected and was independently re-verified under a
σ²_probe × c_probe sweep (`CODE_REVIEW.md` §5.2).

## 5b. H2 and H3, added 2026-08-05

**H2 — battery specs, sourced at last.** `LAB_PLAN.md` had deferred the round-trip-efficiency and
degradation spec to Phase 0 "not invented"; Phase 0 never did it. Now taken from Tesla's own
Powerwall 3 datasheet (`research/09_battery_spec_primary_source.md`), which forced three corrections:
charge power is **5 kW, not the 11.5 kW discharge rating** the lab was applying to both directions;
round-trip efficiency is **0.913**, *derived* as 89%/97.5% rather than quoted (using the 89% headline
would double-count the PV inverter loss `solar_model.py` already applies); and amortization moves
from 12 years to the warranted **10**.

**These changes moved every method by a near-uniform $4-5/yr and reordered nothing** — verified by
running the ladder under each change separately. That is the useful result: H2 is a robustness and
honesty improvement, not a conclusion change. The one figure still unsourced (end-of-life capacity
retention — Tesla publishes the 10-year term but not the percentage, and the warranty PDF is not
served) is swept in Phase 3 rather than trusted; see `RESULTS_PHASE3.md`.

**H3 — the two things `research/04` asked for and never got.**

1. **Both rate structures are now scored as named alternatives.** Every method reports its bill under
   TOD opt-in *and* under the tiered-only default, and takes the cheaper — since BC Hydro's TOD layer
   is genuinely optional. **TOD opt-in wins for all nine methods** ($485-649 vs $669-703), so the
   earlier practice of always applying TOD was right; it just had never been demonstrated.
2. **Method 4, a tier-threshold-aware policy**, the class `research/04` explicitly named and no
   method addressed: run the calendar rule but suppress off-peak pre-charging once the month's
   running consumption has already passed the 675 kWh Step 1 threshold (using only days strictly
   before the decision day — no lookahead). **Result: $515/yr, mid-pack** — it beats the plain GP by
   $1 and loses to the reserve-based methods by ~$30. Tier-threshold management is a real
   consideration for a household near the threshold, but at this household's consumption (~11,600
   kWh/yr, well above Step 1 every winter month) the threshold is crossed early enough that gating
   on it mostly just forgoes cheap off-peak energy.

## 6. Unchanged caveats

- **The top of the ladder is a statistical tie.** All eight proactive methods sit within $36/yr and
  the top three within $5. Do not read the ordering among them as a finding; the robust results are the $160/yr
  value of off-peak pre-charging and the ~$25/yr value of a peak-window reserve.
- **Method 1's new win is rate-structure-specific and slightly uncomfortable.** "Charge to full every
  night and export all your solar" beats forecasting because RS 2289's flat 10¢ export credit sits
  well above the 5.97¢ off-peak import rate. That arbitrage is real under the current tariff but is
  exactly the kind of behaviour a utility revises tariffs to remove, and it depends on the credit
  cap not binding at 8kW (it does bind above that — see `RESULTS_PHASE3.md`).
- The 6 kWh reserve optimum in §3 was selected on the same held-out record it is scored on — a real
  in-sample selection on one hyperparameter.
- End-of-life battery capacity retention remains **assumed, not sourced** (swept in Phase 3).
- Whether unused RS 2289 export credit rolls forward month-to-month is unresolved
  (`research/08`); this lab takes the conservative reading.
- The 6 kWh reserve optimum in §3 was selected on the same held-out record it is scored on — a real
  in-sample selection on one hyperparameter. Method 3c's headline uses the regime layer's own
  8.82 kWh mean (not the swept 6 kWh optimum) to avoid that, costing $1/yr.
