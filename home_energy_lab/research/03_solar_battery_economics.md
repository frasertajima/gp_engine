# Solar + battery costs and specs — real, sourced 2026 figures

## Solar (PV array)
- Typical US residential system: **6–10 kW**, installed cost **$2.55–$3.45/W** before incentives —
  a 6kW system ≈ $15,000–$21,000, an 8kW system ≈ $20,000–$28,000, a 10kW system ≈ $25,000–$35,000.
- Federal Residential Clean Energy Credit: **30% through 2032**, stepping to 26% (2033) / 22% (2034)
  — a real, current policy figure, not assumed.

## Battery storage
- **Tesla Powerwall 3** (a real, named, current reference product): **13.5 kWh usable**, **11.5 kW**
  continuous power, **$11,500–$16,500 fully installed** in 2026 (newer homes toward the low end,
  older homes needing panel upgrades toward the high end).
- General market range: **$800–$1,200 per usable kWh installed**, a 10–13.5 kWh system landing
  $9,000–$18,000 before incentives — consistent with the Powerwall figure above, not an outlier.

## Net effect on this lab's design
These give real, sourced illustrative defaults for the capacity-sizing solver's cost side (Method,
Phase 3): $/kW for solar, $/kWh for battery, both with the real federal credit applied — the same
role `climate_cat_lab/exposures.py`'s $300-400k insured-value benchmark or `hydro_reserve_lab`'s
$417/$2,400-per-AF figures play elsewhere in this codebase: real market anchors for a synthetic
system's economics, not a claim about any one specific household's actual installed cost.

## Not yet sourced (flagged, not invented)
- A real time-of-use (TOU) electricity rate schedule — deferred to Phase 0/1, when a specific real
  utility's published TOU tariff (a genuine, checkable primary source, the same standard as every
  other $ figure in this codebase) will be selected and cited, not invented.
- Battery round-trip efficiency, degradation/cycle-life, and inverter losses — standard published
  ranges exist (e.g. round-trip efficiency typically 85-95% for modern lithium systems) but were not
  independently verified against a primary spec sheet this pass; to be sourced at Phase 0 alongside
  the specific reference battery model chosen.
