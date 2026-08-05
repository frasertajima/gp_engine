# Phase 0 — data, models, sanity checks

**Status: DONE (2026-08-04).** Real 10-year Vancouver, BC weather (2016-2025, Open-Meteo Historical
Weather API, live-verified) pulled and cached; solar generation, household load, and battery models
built; all sanity checks passed on real, checkable numbers — nothing assumed from the research
pass's aggregate figures alone, same discipline as every prior lab's Phase 0.

## Data

10 years (2016-01-01 to 2025-12-31), 87,672 hourly rows, 0 missing values, for Vancouver, BC
(49.2827°N, -123.1207°W): temperature (mean 10.4°C, range -14.1°C to 36.4°C), shortwave radiation
(mean 142.4 W/m², max 954 W/m²), cloudcover (mean 63.7% — a real, genuinely cloudy climate).

## The load model: a real 2-point calibration, not just EIA aggregate percentages

Fit against Fraser's own real BC Hydro bill sub-periods (`research/
04_vancouver_real_calibration_case.md`), using real Vancouver temperature pulled for the *exact*
real billing dates:

| Period | Real mean temp | Real usage | Model (calibrated) |
|---|---|---|---|
| Mar 20-31, 2026 | 5.87°C | 35.1 kWh/day | 35.55 kWh/day |
| Apr 1-May 30, 2026 | 12.31°C | 29.3 kWh/day | 29.77 kWh/day |

Fit: `load = 24.175 kWh/day (base) + 0.9006 kWh/degree-day × max(0, 18°C − T)` — an exact 2-point
solve (2 real data points, 2 unknowns; the ~0.45-0.47 kWh/day residual above comes from the diurnal
reweighting, not the fit itself). **Cross-checked, not fit, against the recalled seasonal range**
(~25 kWh/day Sept, ~35 kWh/day Jan): the model predicts ~25.6 kWh/day for a typical September and
~36.4 kWh/day for a typical January — close to the recalled figures despite never seeing them
during fitting, a genuine consistency check passed.

Implied annual consumption: **~11,630 kWh/yr (~31.9 kWh/day average)** — about 3x a typical North
American home, consistent with the real known drivers (large home, underfloor electric resistance
heat, home EV charging).

## The solar model: a real, physically sensible seasonal shape

An 8kW system (a real, representative residential size, `research/03_solar_battery_economics.md`)
produces **~7,989 kWh/yr (999 kWh/yr per installed kW)** — within the real, plausible 900-1,100
kWh/yr/kW range for this climate. Seasonal shape: **summer 38.7 kWh/day vs. winter 6.9 kWh/day
(5.6x)** — a real, strong seasonal swing consistent with Vancouver's ~49°N latitude, peaking in July
(1.75 kW mean hourly) and troughing in December (0.18 kW mean hourly).

## The stress-regime hypothesis: confirmed directly, not assumed

LAB_PLAN.md's central mechanism — winter low-solar/high-heating-demand persistence — checked
directly against the real 10-year record (25th/75th percentile thresholds for "low solar day" /
"high heating-demand day," matching the family's own tail-dependence-check convention,
e.g. `climate_cat_lab`'s λᵤ check):

- **Real co-occurrence excess**: P(both) observed = 0.1114 vs. 0.0626 if the two were independent —
  **a real 1.78x excess**, confirming low-solar and high-heating-demand days genuinely co-occur more
  than chance, not just two marginal seasonal trends that happen to overlap by construction.
- **Real multi-day persistence**: P(stress day tomorrow | stress day today) = 0.502 vs. the marginal
  P(stress) = 0.111 — **a real 4.5x persistence ratio**, confirming this is genuine weather-system-
  driven persistence (real winter storm systems lasting days), not an i.i.d. day-to-day draw. This
  is the mechanism a soft-EM regime-mixture layer (Phase 1/Method 3) exists to capture.

Both numbers are real and directly comparable in spirit to `climate_cat_lab`/`grid_reserve_lab`'s
own Phase 0 tail-dependence findings — a fifth confirmation, in a new domain, that this codebase's
recurring regime-mixture premise (a real, correlated, persistent stress state exists and is worth
modeling explicitly) holds up on real data.

## Load-bearing simplifications, stated plainly

- **The load model's diurnal shape is EIA-informed, not independently calibrated at hourly
  resolution** — only the aggregate daily total is calibrated against real bill data.
- **Base load (24.175 kWh/day) bundles EV charging and everything non-heating** — not separately
  identified; a future phase with sub-metered or time-stamped EV charging data could split this.
- **Battery round-trip efficiency (90%) is a documented mid-range assumption**, not yet sourced to
  a primary spec sheet (`research/03_solar_battery_economics.md`).
- **Solar model uses horizontal GHI directly** (no plane-of-array tilt correction) — a documented
  simplification, not full PVWatts fidelity.

## Files

- `data_weather.py` — Open-Meteo puller + local cache (`data/weather_<year>.json`, not committed).
- `solar_model.py` — GHI → PV generation, real seasonal shape verified.
- `load_model.py` — real 2-point-calibrated base+heating load model, real backtest verified.
- `battery_sim.py` — battery SOC simulator; verified energy-conserving to floating-point precision
  (max per-hour AC-bus power imbalance 8.88e-16 kW, max SOC-trace consistency error 8.88e-16 kWh) —
  a real bug caught and fixed along the way: a first draft's naive aggregate energy-balance
  self-test failed (didn't account for round-trip efficiency losses correctly), replaced with a
  rigorous per-timestep power-balance check.
- `phase0_run.py` / `results_phase0.json` / `RESULTS_PHASE0.md` — this phase.
