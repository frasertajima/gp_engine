# A real correction: BC/Canadian rebates and costs, not the US federal credit (2026-08-04)

**A real error caught before it propagated into Phase 3's economics, not after.** `research/
03_solar_battery_economics.md` sourced real 2026 figures for solar/battery costs and incentives —
but those were **US sources, in USD, including the US federal Residential Clean Energy Credit
(30% through 2032)**. Fraser's real household is in Vancouver, BC, Canada — the US federal credit
does not apply, and the cost figures should be in CAD, not USD. Caught while scoping Phase 3
(the capacity-sizing solver, which directly uses these figures), not left in.

## Real BC Hydro rebate structure (verified directly from bchydro.com, not a search summary)

**Solar panel rebate**: $1,000 CAD per kW of installed DC capacity, **capped at $5,000 CAD per
home**, and capped at 50% of total installed cost (labour + materials).

**Battery storage rebate**: $500 CAD per kWh of installed storage capacity, **capped at $1,500 CAD**
(or up to $5,000 CAD if the battery is enrolled in BC Hydro's Peak Saver demand-response program —
a real, larger incentive, not modeled here since Peak Saver enrollment is a separate commitment
this lab doesn't model), also capped at 50% of installed cost. **Battery storage is only eligible
for a rebate if installed together with a solar system** — not available standalone.

**Contractor requirement**: installations must use a Home Performance Contractor Network (HPCN)
member (a real requirement as of mid-2026). No income-tested supplement is documented on BC Hydro's
own rebate page (a secondary source claimed one; not corroborated by the primary source, so not
used here).

**No federal/national incentive is claimed here** — not independently verified this pass, and not
needed given the real BC Hydro rebate above is already a genuine, sourced, primary-source figure.

## Real Canadian/BC installed costs (CAD, not USD)

- **Solar**: ~$2.50-$3.30/W CAD installed in BC (regional variation noted, e.g. BC Interior
  slightly higher at $2.95-$3.40/W) — numerically close to the earlier USD figure, but now correctly
  denominated; a $2.90/W CAD midpoint is used as the representative default.
- **Battery**: $12,000-$22,000 CAD installed for a full home battery system; a Tesla Powerwall
  specifically ~$14,000-$18,000 CAD installed (vs. the $11,500-$16,500 USD figure `research/
  03...md` cited) — real battery installs carry a substantial fixed cost (hybrid inverter, subpanel,
  labour) beyond a pure per-kWh rate, "adding $12,000-$18,000 rather than a smaller increment" per
  the sourced discussion. This lab's model folds that fixed cost into an average $/kWh rate derived
  from the Powerwall reference point (~$16,000 CAD midpoint / 13.5 kWh ≈ $1,185/kWh CAD) — a
  documented simplification (a real fixed-cost component exists and isn't modeled separately), not
  a claim of a truly linear cost structure.

## Net effect on Phase 3's design

`capacity_sizing.py` uses these real CAD figures and the real BC Hydro rebate structure (not the US
federal credit) for its capital-cost side. `research/03_solar_battery_economics.md` is superseded
by this file for the specific $ figures used in Phase 3 — kept in place, not deleted, per this
codebase's own correction convention (`grid_reserve_lab`/`hydro_reserve_lab` did the same).
