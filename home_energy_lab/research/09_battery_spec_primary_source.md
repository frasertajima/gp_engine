# Battery specs from the primary source (2026-08-05)

Discharges a deferral this lab had been carrying since Phase 0. `LAB_PLAN.md` said the battery
round-trip-efficiency/degradation spec was *"explicitly **not yet sourced** — deferred to Phase 0,
not invented."* Phase 0 never did it, `battery_sim.py` kept a comment saying the figure was "not yet
sourced to a primary spec sheet", and `LAB_PLAN.md` nevertheless recorded `research/ — DONE`
(`CODE_REVIEW.md` H2).

**Source: Tesla's own Powerwall 3 datasheet (2025, en-us)**, downloaded directly from Tesla's energy
library — not a reseller summary, not a search result:
`https://energylibrary.tesla.com/docs/Public/EnergyStorage/Powerwall/3/Datasheet/en-us/Powerwall-3-Datasheet.pdf`

## What the datasheet actually says

| Datasheet line | Value | Footnote |
|---|---|---|
| Nominal Battery Energy | **13.5 kWh AC** | "Values provided for 25°C (77°F), **at beginning of life**" |
| Nominal Output Power (AC) | 5.8 / 7.6 / 10 / **11.5 kW** | configurable |
| Maximum Continuous Charge Current / Power (Powerwall 3 only) | **20.8 A AC / 5 kW** | 8 kW only with up to 3 expansion units |
| Solar to Battery to Home/Grid Efficiency | **89%** | "Typical solar shifting use case" |
| Solar to Home/Grid Efficiency | **97.5%** | "Tested using CEC weighted efficiency methodology" |
| Warranty | **10 years** | *(no capacity-retention % on the datasheet)* |

## Three real corrections this forced

**1. Charge power is not symmetric with discharge — the lab had it 2.3x too fast.**
`battery_sim.py` applied a single `max_power_kw = 11.5` to *both* directions. The real unit charges
at **5 kW**, less than half its 11.5 kW discharge rating. `DEFAULT_MAX_CHARGE_KW` is now a separate
constant. This binds on a sunny midday with an 8kW array (surplus exceeds 5 kW), pushing more energy
to export instead of the battery.

**2. The 89% headline is the WRONG number to use here, and using it would double-count.**
The datasheet gives no pure battery round-trip figure. It gives two end-to-end paths, and the
difference between them is the battery:

- 97.5% = solar → home/grid (PV inverter only, no battery)
- 89% = solar → battery → home/grid (that same path *plus* the battery detour)
- **0.89 / 0.975 = 0.9128** = the battery's own incremental round-trip contribution

This matters because `solar_model.py` already applies a 0.80 derate covering inverter/wiring/soiling
losses. Feeding 0.89 into `battery_sim` would charge the PV inverter loss twice. The lab's simulated
solar and load series are both already AC-side, so **0.913 is the correct figure** and the old
unsourced 0.90 was closer to right than the "sourced" 0.89 would have been. Recorded because it is a
genuine trap: the most-quoted number on the datasheet is not the one this model needs.

**3. Amortization was one warranty period too generous.** `capacity_sizing.py` amortized the battery
over 12 years against a manufacturer warranty of 10. Now 10.

## The one figure still NOT sourced — and why no conclusion depends on it

**Capacity retention at end of life.** The datasheet states the 10-year warranty term but publishes
no retention percentage; that lives in Tesla's separate limited-warranty document, which is **not
served** at the URL Tesla's own energy library advertises for it (checked 2026-08-05 — returns an
nginx PHP error page, not a PDF). Secondary sources widely report 70%, and some report 80%, which is
exactly the kind of disagreement this lab does not resolve by picking one.

So `BATTERY_RETENTION_AT_END_OF_LIFE = 0.70` is labelled **ASSUMED, not sourced**, and
`capacity_sizing.py` now **sweeps it (100% / 90% / 80% / 70% / 60%)** and prints the resulting
optimum at each level. The cost-minimizing system carries **no battery at every retention level
tested**, including the no-fade 100% case — so the lab's actual conclusion is independent of the
unsourced figure, which is the only honest way to ship an assumption of this kind.

Capacity fade is modelled as the **lifetime-mean** effective capacity (linear fade from nameplate to
`retention × nameplate`), while capital is still charged on **nameplate** — you pay for 13.5 kWh and
get an average of less. Linear fade is a stated simplification; real lithium fade is faster early
then flattens, which moves the lifetime average by a few percent, not enough to matter against the
retention uncertainty above.

## Applicability caveat

These are Powerwall-3 figures. `scenario_engine.py`'s Anker SOLIX presets carry their own costs but
reuse this efficiency/fade model, which is **not** sourced to Anker's spec sheet — flagged there and
here rather than silently generalised.
