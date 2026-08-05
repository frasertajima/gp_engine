# Typical residential electricity load shape — real, sourced figures (2026-08-04)

## Claim
A real, sourced breakdown of what a typical US home's electricity load looks like exists, usable to
parametrize a synthetic (not raw-real-dataset) load generator — the user's own preferred design
("artificial parameters for... load fluctuations," informed by real research on typical shape, not
a raw ingested dataset).

## Sourced figures (EIA Residential Energy Consumption Survey, RECS 2020 — primary federal source)
- **Heating + cooling (HVAC) is the single largest end use**: cited at ~42–52% of total home
  electricity in RECS-2020-derived breakdowns; air conditioning alone (a narrower slice) accounts
  for ~19% of residential electricity consumption, and ~12% of home energy *expenditure* specifically
  (EIA, "Air conditioning accounts for about 12% of U.S. home energy expenditures").
- **Rest of the breakdown**: water heating ~13%, lighting ~9%, refrigeration ~7%, washer/dryer ~6%,
  remainder split across smaller appliances/electronics.
- **Seasonality**: EIA's own "Air conditioning and other appliances increase residential electricity
  use in the summer" piece confirms the real, expected summer AC-driven peak — the mechanism this
  lab's HVAC thermal-load model needs to reproduce from real temperature data, not assume.

## A real, individually-downloadable, per-building alternative (noted, not used as the primary
## driver — see Method)
**NREL ResStock "End-Use Load Profiles for the U.S. Building Stock"** — validated EnergyPlus
building-energy-model simulations for representative homes across every US climate region, 15-minute
resolution, one full year per building, split by end use (HVAC, water heating, etc.). Hosted free on
AWS S3 (OEDI data lake), no signup, direct HTTPS download per building ID. **Verified directly**: a
live `curl -I` against a real example file
(`.../timeseries_individual_buildings/by_state/upgrade=2/state=WA/100025-2.parquet`) returned
`200 OK`, `Content-Length: 2424114` (a real ~2.4MB parquet file).

This is a stronger, more validated source than a single real smart-meter household (which would
carry one household's idiosyncrasies, not a representative shape) — worth revisiting if Phase 1's
synthetic load-shape parametrization needs a real-data cross-check or calibration target, per this
codebase's own "check against something real before trusting a synthetic DGP" norm
(`climate_cat_lab`/`grid_reserve_lab`'s own Phase 0 sanity-check pattern).

## Net effect on this lab's design
Build a synthetic, parametric load generator (diurnal base-load curve + a temperature-driven HVAC
term, per Method) calibrated to the real EIA percentage breakdown and seasonality above — the same
"illustrative but real-anchored" posture `climate_cat_lab/exposures.py` used for insured-value
benchmarks — with ResStock flagged as the real cross-check dataset for a later phase, not required
up front.
