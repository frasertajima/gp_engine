# Phase 3 — the capacity-sizing solver

**Re-run 2026-08-05** after `CODE_REVIEW.md` H1: grid export was previously credited at **$0**, and
the export credit is now sourced and applied (`research/08_bc_hydro_export_compensation.md`). The
2026-08-04 run is superseded; §"What changed" records exactly how.

A 2D (solar kW, battery kWh) grid search over real, practically-relevant system sizes, minimizing
total annualized cost (real BC Hydro rebate-adjusted capital cost + real annual grid $ under Method
2's dispatch policy), scored against the real 2017-2025 Vancouver weather/load record.

**Headline: the cost-minimizing system is still 4kW solar + NO battery ($1,254/yr) — but the margin
over 6kW collapsed from $107/yr to $7/yr, so "4kW" is now effectively a tie with 6kW rather than a
clear winner.** The no-battery half of the conclusion is unchanged and, if anything, more robust.

## Two real corrections this phase has now survived

1. **(2026-08-04)** The earlier-sourced solar/battery economics were **US market data, in USD,
   including the US federal 30% tax credit — none of which applies to a Vancouver, BC household.**
   Corrected in `research/05_bc_solar_battery_rebates_corrected.md` with real BC Hydro rebates
   verified directly from bchydro.com: solar $1,000/kW capped $5,000; battery $500/kWh capped
   $1,500, battery rebate-eligible only when installed with solar.
2. **(2026-08-05)** **Grid export was valued at $0 across the entire lab.** The 8kW reference system
   exports 4,108 kWh/yr with no battery. Fixed, and the lookup mattered more than expected — see
   below.

## The export rate had changed five weeks before it was checked

Worth stating plainly because it is the strongest possible argument for this lab's own
verify-don't-recall discipline. **BC Hydro replaced its net metering program on 2026-07-01**:

- Legacy **RS 1289** (net metering, annual kWh banking) — **closed to new customers**.
- Current **RS 2289** (Self-Generation Service Rate) — flat **$0.10/kWh monetary credit, settled per
  billing cycle**, and credits **cover Energy Charges only** (the $6.17 basic charge stays payable).

Any figure recalled rather than fetched would have described the closed program. RS 2289 is
determinative here for a second reason: accepting the BC Hydro solar rebate this lab already models
*forces* transition to RS 2289, so the two assumptions are only consistent under it.

## Result (full grid, 9-year real annualized $, `results_phase3.json`)

| Solar | Battery | Capital $/yr | Grid $/yr | **Total $/yr** | Self-suff. | Export kWh/yr |
|---|---|---|---|---|---|---|
| 0 kW | 0 kWh | $0 | $1,489 | $1,489 | 0.0% | 0 |
| 0 kW | 13.5 kWh | $1,333 | $1,370 | $2,703 | **−2.8%** | 0 |
| **4 kW** | **0 kWh** | **$304** | **$950** | **$1,254** | 25.4% | 1,051 |
| **6 kW** | **0 kWh** | $496 | $765 | **$1,261** | 30.4% | 2,476 |
| 8 kW | 0 kWh | $728 | $662 | $1,390 | 33.7% | 4,108 |
| 4 kW | 13.5 kWh | $1,512 | $795 | $2,307 | 29.9% | 137 |
| 8 kW | 13.5 kWh *(Phase 1/2's reference)* | $2,323 | $391 | **$2,714** | 42.2% | 2,749 |
| 20 kW | 40.5 kWh | $5,994 | $240 | $6,235 | 59.6% | 12,677 |

(full 32-row grid in `results_phase3.json`)

**4kW/0kWh at $1,254/yr wins, with 6kW/0kWh at $1,261/yr essentially tied** — cheaper than doing
nothing ($1,489/yr) and 49% cheaper than the 8kW/13.5kWh default used throughout Phases 1-2
($2,714/yr). Every battery-inclusive combination still costs more than its solar-only counterpart at
the same solar size, across the entire grid.

**Battery specs were sourced from Tesla's own datasheet on 2026-08-05** (`CODE_REVIEW.md` H2,
`research/09_battery_spec_primary_source.md`): amortization moved from 12 years to the warranted 10,
charge power from 11.5 kW to the real 5 kW, round-trip efficiency to a derived 0.913, and capacity
fade is now modelled. All four make batteries look worse, which is why the reference system rose
from $2,457 to $2,714/yr while the battery-free optimum did not move at all.

## Finding: the per-billing-cycle credit cap, not the credit rate, governs solar sizing

The most interesting result of the re-run, and the reason 6kW did **not** overtake 4kW as a naive
export credit would predict. Because RS 2289 settles monthly and credits cannot exceed the month's
energy charge, a Vancouver summer pairs maximum export with a minimal energy charge — and the
surplus is forfeited, not banked into winter:

| Solar kW | Export kWh/yr | Credit forfeited to the cap |
|---|---|---|
| 4 | 1,051 | **$0/yr** |
| 6 | 2,476 | $43/yr |
| 8 | 4,108 | $158/yr |
| 12 | 7,651 | $448/yr |
| 20 | 15,173 | **$1,117/yr** |

At 4kW the cap never binds; past ~6kW it dominates the export economics. Uncapped, a 20kW array
would run a **negative** annual bill (−$745/yr), which RS 2289 plainly does not permit. **This makes
the monthly-settlement rule — not the 10¢ rate — the binding constraint on how much solar is worth
installing in a heating-dominated climate.** It is also the lab's single largest remaining
uncertainty: whether unused credit rolls forward is not stated on either BC Hydro page
(`research/08`), and this model takes the conservative reading.

## A genuinely counter-intuitive real finding (unchanged)

0kW solar + 13.5kWh battery still shows **self-sufficiency of −2.8%** — the battery, cycling purely
on grid arbitrage, *increases* total grid kWh purchased (round-trip losses on energy that has
nowhere else to come from) while *reducing* the dollar bill ($1,370/yr vs $1,489/yr). Unaffected by
the export fix, since a solar-free system exports nothing. The starkest form of Phase 1's own
finding that self-sufficiency and cost-effectiveness are different axes.

## Mechanism, checked directly

**Why battery capacity never pays for itself here** — unchanged, and now checked under a more
generous rate: BC Hydro's real rates are low (Step 1 10.97¢/kWh), the real battery rebate is small
against real installed cost ($500/kWh vs ~$1,185/kWh, capped at $1,500 regardless of size), and the
real TOD spread (±5¢/kWh) is too thin for a ~$1,185/kWh battery to earn back amortized capital at
any size tested. Crediting export actually *widens* the gap slightly at large solar sizes, because a
battery's main job there is to avoid exporting — which is now worth 10¢ rather than nothing.

**Why solar has a bounded sweet spot** — the $5,000 rebate cap is reached at exactly 5kW, so the
first ~4-5kW carries the largest proportional subsidy. Beyond that, additional capacity is
unsubsidized, falls on Vancouver's weak winter season (Phase 0's real 5.6x seasonal swing), and runs
into the credit cap above. Total cost still rises monotonically past 6kW.

## What changed from the 2026-08-04 run

| System | Old (export = $0) | New (RS 2289 credit) |
|---|---|---|
| 4 kW / 0 kWh | $1,359 *(old optimum)* | **$1,254** *(still optimum)* |
| 6 kW / 0 kWh | $1,466 | $1,261 |
| 8 kW / 0 kWh | $1,643 | $1,390 |
| 8 kW / 13.5 kWh *(reference)* | $2,560 | $2,714 (after H2 battery specs) |

Every solar-only figure fell, larger systems fell furthest, and the 4kW-vs-6kW margin narrowed from
$107/yr to $7/yr. Battery-inclusive figures ROSE, because H2's sourced battery specs (10-year
warranty amortization, 5 kW charge limit, modelled fade) all cut the other way. **The published conclusion survives, but its robustness did not** — the review's H1 estimate
(using an uncapped 9.99¢ credit) predicted 6kW would win at $1,218/yr; the real capped rate is what
keeps 4kW ahead, by an amount smaller than this model's own resolution. The honest statement is now
"4-6kW of solar, no battery," not "4kW."

## Risks / honest unknowns

- **The 4kW-vs-6kW ordering is inside the model's noise.** A $7/yr difference on a $1,254/yr total
  should not be read as a real preference; treat 4-6kW as one answer.
- **Whether unused RS 2289 credit rolls forward is unresolved** and is now the largest single lever
  on this phase's result (see the forfeiture table above).
- **Pure $-optimization only.** A battery provides real value this model doesn't price: backup power
  during an outage, BC Hydro's real Peak Saver program (a larger $5,000 rebate, not modeled), and
  future EV integration.
- **Straight-line amortization, no discount rate, no electricity-price escalation** over the 25/12yr
  horizons. Direction not checked this pass.
- **Solar lifetime (25yr) is standard/typical, not independently re-sourced.** Battery lifetime is
  now the manufacturer's own 10-year warranty term.
- **End-of-life capacity retention is the one battery figure still ASSUMED**, not sourced: Tesla's
  datasheet states the 10-year warranty term but publishes no retention percentage, and the warranty
  PDF is not served at Tesla's own advertised URL (`research/09_battery_spec_primary_source.md`).
  **Swept rather than trusted** — the optimum carries no battery at 100%, 90%, 80%, 70% and 60%
  retention alike (`results_phase3.json`'s `retention_sensitivity`), including the no-fade case, so
  the conclusion does not depend on it.
- **The grid is coarse** (8×4 = 32 points); with 4kW and 6kW now $7 apart, a finer sweep between them
  would be the natural refinement.
- **Dispatch policy is Method 2**, which Phase 1's re-run showed is beaten by ~$31/yr by the
  reserve-based methods. That applies near-uniformly across the grid and does not reorder it, but
  the absolute figures are marginally pessimistic.
- Disclaimer carried forward: illustrative and educational, not a substitute for a real quote from a
  licensed BC solar/battery installer.
