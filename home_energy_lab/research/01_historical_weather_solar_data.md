# Historical weather + solar irradiance data — real, open, live-verified (2026-08-04)

## Claim
A real, free, multi-year, hourly, no-signup weather+solar dataset exists and is directly usable
as this lab's DGP driver, the same "real data, synthetic system/economics" posture as
`grid_reserve_lab` (EIA-930), `hydro_reserve_lab` (USGS), and `shm_lab` (KW51).

## Source
**Open-Meteo Historical Weather API** (`https://archive-api.open-meteo.com/v1/archive`) — free,
open-source, no API key. ERA5 reanalysis at 0.25° (~25km) from 1940; ERA5-Land at 0.1° (~9km) from
1950; hourly resolution. Shortwave radiation (the direct solar-generation driver) is available
either from the same ERA5 reanalysis or, for higher fidelity in some regions, from satellite-
derived products (EUMETSAT CM SAF SARAH3 for Europe/Africa/South America from 1983).

## Verified directly (not assumed from docs)
Live `curl` against the archive endpoint for a real location (39.7°N, -104.9°W — Denver, CO area)
returned real hourly `temperature_2m`, `shortwave_radiation`, and `cloudcover` for a test date range,
200 OK, real numeric values, no auth:

```
curl "https://archive-api.open-meteo.com/v1/archive?latitude=39.7&longitude=-104.9&start_date=2023-06-01&end_date=2023-06-02&hourly=temperature_2m,shortwave_radiation,cloudcover"
```

returned a well-formed JSON payload with real hourly series for both dates requested.

## What this gives the lab
- `temperature_2m` (°C, hourly) — drives HVAC thermal load.
- `shortwave_radiation` (W/m², hourly) — drives solar PV generation (via a standard panel
  efficiency/derate conversion, Phase 0's job to implement and sanity-check).
- `cloudcover` (%, hourly) — a secondary solar-variability signal, useful for the regime-detection
  side (extended low-solar spells correlated with cold snaps in winter is the tail-risk mechanism
  this lab's regime-mixture layer would target, the direct analog of `climate_cat_lab`'s systemic-
  year spatial shock and `grid_reserve_lab`'s drought regime).

## Honest caveats
- ERA5 reanalysis is a *modeled* reconstruction, not a ground station measurement — real, but with
  known biases at fine spatial/temporal resolution, particularly for cloud-driven solar variability.
  Adequate for this lab's purpose (a realistic multi-year regime structure to test the decision
  mechanism against), not claimed as bankable production PV-yield forecasting accuracy.
- A single location's multi-year record is what Phase 0 will use (matching every prior lab's
  single-book/single-basin/single-bridge posture) — not a multi-region study.
