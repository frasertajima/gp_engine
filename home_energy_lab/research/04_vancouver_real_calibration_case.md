# A real household calibration case: Vancouver, BC (2026-08-04)

Unlike every prior lab's real data (gov/corporate-collected), this is a genuine personal data point
Fraser supplied from his own BC Hydro bill — the first real, individual-household ground truth
available to any lab in this codebase. Documented here with the same "checked, not assumed"
discipline as every other research file, including a real inconsistency that was found, investigated
with more real data in the same session, and cleanly resolved (see below) — a small live example of
this codebase's own norm of correcting itself rather than being wedded to a first guess.

## The real data point

- **Tier breakdown, real bill detail**: Mar 20-31: 266 kWh tier-1 + 155 kWh tier-2 (421 kWh / 12
  days). Apr 1-May 30: 1,110 kWh tier-1 + 646 kWh tier-2 (1,756 kWh / 60 days). Combined: **2,177
  kWh over a real ~72-day billing period** (see resolution below — this is the same "2,177 kWh"
  figure originally described as "one month," corrected here).
- **Seasonal daily-average anchors**, from the bill's own usage chart (Fraser's recollection, not
  a verbatim quote — treat as approximate): **~25 kWh/day low (September)**, **~35 kWh/day high
  (January)**, **~33 kWh/day (May)** — consistent with, not contradicted by, the precise tier-based
  rates above (~35.1/day late March, ~29.3/day Apr-May average).
- **Known load drivers**: underfloor electric resistance heating (no heat pump) over a large home,
  plus home EV charging.

## A real inconsistency, found — then RESOLVED with more real data (2026-08-04, same session)

**Superseded, kept visible rather than deleted, per this codebase's own correction convention.**
The original framing ("2,177 kWh ÷ 31 days ≈ 70 kWh/day for March") assumed a calendar-month bill.
Fraser then supplied the actual tier breakdown: **266 kWh tier-1 + 155 kWh tier-2 for Mar 20-31**
(421 kWh / 12 days = **35.1 kWh/day**), and **1,110 kWh tier-1 + 646 kWh tier-2 for Apr 1-May 30**
(1,756 kWh / 60 days = **29.3 kWh/day**). **421 + 1,756 = 2,177 kWh exactly** — the original figure
was never a calendar month; it's a single real **~72-day billing period (Mar 20-May 30)**, split
into two priced chunks (almost certainly by a BC Hydro rate-year change effective April 1, which is
why it bills as two separate tier1/tier2 blocks rather than one). **No EV-charging-spike hypothesis
is needed** — the "inconsistency" was a units error (treating a ~2.4-month bill as one month), not
a real anomaly. The real signal that survives: daily use tapering from ~35 kWh/day in late March to
~29.3 kWh/day averaged across April-May — a genuine, usable seasonal decline (spring warming
reducing heating demand), consistent with (not contradicting) the originally recalled seasonal
anchors (~35/day Jan-ish, ~33/day May). EV charging and underfloor resistance heat remain real,
named contributors to the overall high consumption level — just not implicated in an unexplained
spike, since there wasn't one.

**Still open, not yet derived**: the exact proration rule BC Hydro applies to the 675 kWh/month
Step-1 threshold for a non-30-day sub-period (a naive linear proration doesn't cleanly reproduce
both observed tier-1/tier-2 splits from the two available data points) — a real detail to confirm
against BC Hydro's own tariff documentation at Phase 0, not derived by back-solving two bills.

## Vancouver's real climate context (relevant to the stress-regime design)

A mild oceanic (Cfb) climate — long, mild-wet heating season (roughly October-April), rarely cold
enough to require deep resistance-heat draws by US-continental standards, and essentially no
meaningful air-conditioning load. This makes Vancouver a **heating-dominated, single-sided** stress
case, unlike `LAB_PLAN.md`'s original two-sided (winter cold-snap vs. summer heat-wave) framing —
the real stress regime here is winter low-solar-generation + high-heating-demand persistence only,
a simpler, cleaner story to test than originally scoped. To be confirmed directly against the real
Open-Meteo pull in Phase 0, not assumed from general climate knowledge alone.

## BC Hydro's real residential rate structure (closes the "TOU tariff not yet sourced" gap in
## `03_solar_battery_economics.md`)

Verified via search, current (2026): **tiered rate**, not a simple flat/TOU price —
**10.97¢/kWh for the first 675 kWh/month (Step 1), 14.08¢/kWh above that (Step 2)**, plus a
~$6.17/month basic charge. Real **optional Time-of-Day pricing** exists on top of either tier plan:
a 5¢/kWh discount overnight (11pm-7am) and a 5¢/kWh surcharge during 4-9pm.

**A genuine, real design implication, not previously anticipated in `LAB_PLAN.md`**: because the
default rate is a *step/tier threshold* (a nonlinear function of total monthly consumption), not a
simple $/kWh or time-varying price, the real optimization question for a Vancouver household is at
least partly "does shifting/reducing consumption keep this month under the Step 1 threshold," not
only "charge during the cheapest hours." Both structures (tiered-threshold and optional TOD) should
be modeled as real, named alternatives in Phase 1/2, not collapsed into one simplified rate.

**Bill plausibility check, using the real tier splits directly** (not a naive single-threshold
estimate): combined tier-1 across both sub-periods = 266+1,110 = 1,376 kWh; combined tier-2 =
155+646 = 801 kWh. 1,376 kWh × 10.97¢ + 801 kWh × 14.08¢ ≈ **$263.73** in energy charges (plus
basic charge(s) for the ~72-day period, likely ≈$270-285 all-in) — a plausible real bill for a large
home with resistance heat and EV charging.

## Net effect on the lab's design

- Location for Phase 0's real weather pull: **Vancouver, BC** (not an arbitrary illustrative US
  city as originally scoped).
- The stress-regime hypothesis narrows to the real, single-sided winter case for this location.
- The rate/economics model gains a real, sourced, more interesting structure (tiered threshold +
  optional TOD) instead of an assumed flat TOU price, and real evidence (the two sub-periods) that
  a single bill can straddle a rate-year boundary — Phase 0's loader should handle that, not assume
  every bill aligns to one flat-rate period.
- The load model gains a precise real anchor: **~35.1 kWh/day (late March) tapering to ~29.3
  kWh/day (April-May average)** — a real seasonal decline to calibrate against, with the earlier
  EV-spike hypothesis resolved (not needed) rather than left open.
