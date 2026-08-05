# BC's real legal status for balcony/plug-in solar (2026-08-04)

Prompted directly by this lab's own `SCENARIO_BUILDER.ipynb` result: given real BC Hydro rates and
real 2026 hardware costs, balcony solar is the only scenario tested with a real, short payback
(~1.2-5.9 years) — every other tested configuration (4kW solar, 8kW+battery) either takes 17.5
years or never pays back within 30. Before treating that as an actionable real-world recommendation,
checked whether it's actually legal to install in BC today — flagged as unconfirmed in
`06_alternative_hardware_options.md` and left open until now.

## The real finding: NOT currently a legal simplified path in BC

**One direct primary source, BC Hydro's own customer-generation application page** (bchydro.com,
fetched live 2026-08-04), confirms there is **no exemption or simplified pathway for small/plug-in
systems**:
- "Your installer must hold all required trade certifications and permits. Electrical permits must
  be obtained where applicable."
- An interconnection application is mandatory — customers must "Apply for self-generation or
  community generation online through your MyHydro account," which goes through a review/approval
  status process before installation can proceed.
- As of June 2026, solar/battery installations must additionally be completed by a Home Performance
  Contractor Network (HPCN) member to qualify for rebates.
- **No carve-out for systems under any size threshold is mentioned anywhere on the page** — a
  700W-1000W balcony kit is treated identically to an 8kW rooftop array for approval purposes.

Corroborating secondary sources (2026, checked but not the primary basis for this finding):
[Plug-In Solar for Canada — British Columbia](https://www.pluginsolarpower.ca/british-columbia) and
[Solar Energies in Canada — Balcony Solar in Canada vs. Germany](https://solarenergies.ca/balcony-solar-canada-vs-germany/)
both independently state that BC requires advance utility approval and licensed-electrician
hardwired installation for any grid-tied PV system, with no legal path (as of their 2026 writing)
for a renter or homeowner to buy a certified ~800W balcony kit and simply plug it into a wall outlet
as compliant. **This is the opposite of Germany's real rule** (`06_alternative_hardware_options.md`):
Germany's VDE-AR-N 4105 framework explicitly permits up to 800W (moving toward 2kW) of plug-in solar
without an electrician, a standard BC has no equivalent of today.

## A real, in-motion policy signal

At least one source reports a sitting BC Green MLA working with the Energy Minister toward
legalizing balcony solar in 2026 — a real, current legislative signal, not a settled outcome. Not
independently verified against a primary legislative source this pass (a Hansard record or a
minister's office statement would be the next real check if this becomes decision-relevant); flagged
here as a real but unconfirmed-at-primary-source data point, same discipline as everywhere else in
this lab.

## What this means for the lab's own economics

`SCENARIO_BUILDER.ipynb`'s balcony-solar payback figures (1.2y Germany-subsidized, 5.9y US) are
**real numbers for a real product category — but not currently a legally installable-as-plug-in
option in BC** under BC Hydro's and (by extension) Technical Safety BC's present interconnection
rules. A BC household today would need to install the same ~800W panel through the standard
licensed-electrician/permit/interconnection-application path used for any other grid-tied system —
which erodes exactly the "no electrician, no professional setup" cost/friction advantage that makes
balcony solar cheap and popular in Germany and increasingly the US. The hardware/payback economics
in this lab remain real and correctly computed; the finding that changes is **feasibility**, not
cost.

## Net effect on the lab

This is itself a genuine, actionable finding this lab's Phase 3 / Scenario Builder work surfaced:
**the balcony-solar payback advantage is real, but currently unrealizable in BC as a simple plug-in
product** — a real, current regulatory gap relative to Germany, not a modeling limitation. If BC
adopts a German-style small-system exemption (consistent with the in-motion MLA effort noted above),
this lab's own payback numbers say that would meaningfully change real households' cost-optimal
hardware choice at the low end of the market.
