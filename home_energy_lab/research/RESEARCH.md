# Research pass index — home_energy_lab

Research pass DONE 2026-08-04, before any code written, same discipline as every other lab in this
codebase (`climate_cat_lab/research/`, `grid_reserve_lab/research/`, `shm_lab/research/`,
`hydro_reserve_lab/research/`). Three claims checked, two verified live (not just cited from docs).

| # | Claim | Verdict | File |
|---|---|---|---|
| 1 | A real, free, multi-year, hourly, no-signup weather+solar dataset exists | **CONFIRMED, live-verified** — Open-Meteo Historical Weather API, real `curl` test returned real data | `01_historical_weather_solar_data.md` |
| 2 | A real, sourced typical-home load-shape breakdown exists (HVAC-dominated, real seasonality) | **CONFIRMED** — EIA RECS 2020 figures (HVAC ~42-52% of load, real summer AC peak documented); a real per-building alternative (NREL ResStock) also live-verified as a future cross-check | `02_residential_load_profile.md` |
| 3 | Real, current solar/battery cost figures exist to anchor the capacity-sizing solver's economics | **PARTIALLY SUPERSEDED (see claim 5)** — real 2026 market figures found, but US-sourced (USD, US federal tax credit); TOU rate schedule and battery efficiency/degradation figures explicitly flagged as not yet sourced, deferred to Phase 0/1 | `03_solar_battery_economics.md` |
| 4 | (2026-08-04, Fraser's own real household data) Vancouver, BC real load/rate calibration case | **CONFIRMED, real personal data + real BC Hydro rate structure verified** — a real ~72-day bill (Mar 20-May 30, 2,177 kWh total, tier-split by a rate-year boundary), real tiered+optional-TOD BC Hydro rates; **one real inconsistency found, then resolved with more real data in the same session** (the original "70 kWh/day for March" read was a units error — treating a ~2.4-month bill as one calendar month; the real per-day rates, 35.1 late March tapering to 29.3 Apr-May, need no EV-spike explanation) | `04_vancouver_real_calibration_case.md` |
| 5 | (2026-08-04, caught while scoping Phase 3) Claim 3's figures need correcting for a real Canadian household | **CORRECTED, not just flagged** — the US 30% federal credit does NOT apply in Canada; real BC Hydro rebates verified directly from bchydro.com ($1,000/kW solar capped $5,000; $500/kWh battery capped $1,500, battery-only-with-solar); real CAD installed costs found (~$2.50-$3.30/W solar, ~$14,000-$18,000 CAD for a Powerwall-class battery) | `05_bc_solar_battery_rebates_corrected.md` |
| 6 | (2026-08-04, for the Scenario Builder) Real, current pricing exists for cheaper battery alternatives (Anker SOLIX) and balcony/plug-in solar | **CONFIRMED** — Anker SOLIX real 2026 USD pricing ($700-$1,300/kWh, genuinely cheaper than Powerwall at the low end); real German Balkonkraftwerk figures (800W cap, €400-800 cost, real city subsidies up to €500, 1.5-5yr payback) and US balcony-kit figures ($350-700/800W kit); **BC/Vancouver legality of grid-tied balcony solar not confirmed this pass** — flagged, not assumed | `06_alternative_hardware_options.md` |
| 7 | (2026-08-04, prompted by the Scenario Builder's own balcony-solar payback result) Is balcony/plug-in solar actually legal to install in BC today? | **CHECKED, real primary source** — BC Hydro's own customer-generation application page confirms no exemption/simplified pathway for small or plug-in systems; licensed-installer, permit, and interconnection-application requirements apply identically regardless of system size. **Not currently a legal simple-plug-in path in BC**, unlike Germany's real VDE-AR-N 4105 800W exemption. A real, in-motion BC Green MLA legalization effort noted but not primary-source-verified this pass | `07_bc_balcony_solar_legal_status.md` |

## Net effect on `LAB_PLAN.md`

All four load-bearing data-access claims hold up. The lab can proceed to Phase 0 with: (1) a real
weather/solar time series for the real location (Vancouver, BC, via Open-Meteo, live-verified),
(2) a synthetic load generator anchored to real EIA percentages AND a precise real personal
calibration point (35.1 kWh/day late March tapering to 29.3 kWh/day Apr-May average), (3) real cost
anchors for the capacity-sizing question, (4) a real, more interesting rate structure (BC Hydro's
tiered threshold + optional TOD, including evidence a real bill can straddle a rate-year boundary)
than the flat TOU price first assumed. One item remains open, not invented: battery efficiency/
degradation spec (deferred to Phase 0). The EV-attribution question that was open after the first
data point is now resolved (not needed) after Fraser supplied the real tier breakdown.
