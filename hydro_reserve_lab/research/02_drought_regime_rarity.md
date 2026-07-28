# Claim 2: is the regime rare/imbalanced, with a real sourced figure (not just return-period vocabulary)?

**Status: VERIFIED, with a real number — and a real, honestly-flagged nonstationarity complication.**

## The real, sourced rarity figure

Per the U.S. Drought Monitor (cited via Earth.org's Colorado River Basin coverage): **extreme
drought was historically rare in the Colorado River Basin's climate — a 5.5% likelihood.** This is
a genuine, sourced figure in the same range as `grid_reserve_lab`'s synthetic ~5-7% drought-regime
assumption and its real ERCOT/CAISO wind-drought event frequencies (`grid_reserve_lab/research/04_dunkelflaute.md`)
— strong, if preliminary, support for condition 2 of `PLAN.md` §7's litmus test.

## The honest complication this pass found — worth stating precisely, not smoothing over

**By 2022, nearly all watersheds in the Colorado River Basin were experiencing extreme drought
simultaneously** — i.e. the same source that gives the 5.5% historical baseline also documents a
year where the "rare" regime became, in that specific year, nearly universal across the basin.
This is a genuine, important complication for this lab's regime-mixture premise:

- If read as "the regime is rare, at 5.5% base rate" — condition 2 is well satisfied, matching the
  imbalanced-minority-class shape that made soft-EM's advantage real in `grid_reserve_lab`'s
  synthetic oracle.
- If read as "the regime's frequency/severity may itself be trending non-stationary" (consistent
  with `01_recurring_hydrological_regime.md`'s 2025 "hydrological whiplash" paper describing
  *increasing*-frequency wet/dry shifts) — a fixed base-rate assumption calibrated on the full
  historical record could understate a real, ongoing shift toward more frequent/severe drought
  years, a genuinely different and harder problem than a stationary rare-regime mixture.

**This must be checked directly against the actual historical/real data in Phase 0**, not assumed
from this generic figure — the same discipline `grid_reserve_lab`'s own real-EIA-930 pass used when
its real fitted regime split (~50/50) turned out different from its synthetic oracle's rare (~5-7%)
assumption. A real possible Phase 0 finding here: the fitted regime frequency, if computed on a
recent sub-window (e.g. the last 20-30 years) rather than the full historical/paleo record, may
come out meaningfully higher than 5.5% — a reportable finding either way, not a foregone one.
