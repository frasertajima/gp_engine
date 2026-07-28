# hydro_reserve_lab — litmus-test pre-check (2026-07-28)

**Purpose**: before committing to a full research pass + `LAB_PLAN.md` (the discipline every prior
lab in this family went through), check "hydrology sizing" — the third parked idea from
`grid_reserve_lab/LAB_PLAN.md` ("grid reserve / fleet structural-health / hydrology sizing"),
never previously scoped beyond that one-line mention — against `gp_engine/PLAN.md` §7's soft-EM
litmus test, the checklist this codebase's own history (`climate_cat_lab` → `cvar_gp_lab` →
`grid_reserve_lab` → `shm_lab`) forced into existence. **This is a pre-check, not yet a full
research pass** — claims below are sourced from a first search-and-verify session, not yet at the
six-to-ten-claim depth `climate_cat_lab/research/`, `grid_reserve_lab/research/`, and
`shm_lab/research/` reached before their own Phase 0.

## Condition 1 — does the regime genuinely RECUR? YES, well-evidenced

Multi-year wet/dry hydrological regimes are a real, actively-studied, recurring phenomenon, driven
by known climate oscillations, not a single one-off event the way KW51's retrofit was:

- ENSO (El Niño-La Niña) drives real, recurring streamflow/groundwater-recharge swings — an
  extreme El Niño can reduce streamflow ~60% relative to ENSO-neutral conditions (NOAA
  Climate.gov). The Southwest US sees measurably more dry episodes in La Niña years than El Niño
  years.
- A 2024 hydrology paper (HESS) documents "intra-annual (12-48 month) and inter-decadal (128-256
  month) common oscillation cycles between standardized streamflow index and ENSO" — i.e. the
  recurrence is real and quantified at multiple timescales, not asserted loosely.
- A 2025 *Scientific Reports* paper on "atmospheric teleconnection patterns and hydrological
  whiplashes in the Western U.S." documents **recurring, increasing-frequency shifts between
  extreme wet and dry phases** — directly the "regime recurs many times" shape this litmus test
  requires, and a real, current (2025) research topic, not a settled historical curiosity.
- PDO (Pacific Decadal Oscillation) is independently confirmed as a second, real recurring driver
  at a longer (decadal) timescale.

**This clears condition 1 comfortably** — multiple independent, real, recurring mechanisms, unlike
`shm_lab`'s single permanent retrofit.

## Condition 2 — is the regime RARE/IMBALANCED? Plausibly yes, standard framing supports it

Water-resources engineering's own standard practice already frames drought in return-period terms
that directly imply a minority-class regime:

- "1-in-10-year," "1-in-20-year," "1-in-50-year" drought/return-period framing is the field's
  standard vocabulary (a 10-year return period implies ~10% annual probability; a 20-year period
  ~5% — comparable in magnitude to `grid_reserve_lab`'s synthetic ~5-7% drought-regime assumption,
  and to ERCOT/CAISO's real documented wind-drought event frequencies in that same lab's
  `research/04_dunkelflaute.md`).
- Real water-supply design practice explicitly targets these low-probability tails (e.g. sizing
  against a 20-year cycle while accepting some larger, rarer failure probability) — a real,
  documented engineering norm (frequency-analysis reservoir-storage methods, ranking historical
  years by severity and assigning $m/(n+1)$-style empirical probabilities).

**Honest gap**: this pass did not pin down a specific real drought-year frequency for a specific
real basin the way `grid_reserve_lab` sourced ERCOT's actual 82-events-in-5-years figure — the
return-period vocabulary strongly implies rarity/imbalance as the field's norm, but a real
research pass would need to confirm the actual fitted regime frequency in whatever specific basin
is chosen, the same way `grid_reserve_lab`'s real EIA-930 data turned out to have a genuinely
different (balanced ~50/50) regime than its own synthetic oracle assumed — a real, reportable risk
to carry forward, not papered over.

## Condition 3 (bonus lever) — cross-sectional pooling across multiple correlated basins/gauges? YES, and a real, confirmed-open dataset exists

- USGS operates **8,705+ streamflow-monitoring sites** nationally, with **3,000+ long-term (30+
  years) streamgages** — a real "fleet" of correlated units within any given region/watershed,
  directly analogous to `grid_reserve_lab`'s multi-site wind fleet and `shm_lab`'s multi-mode
  pooling (Phase 1b/1c's own finding: pooling across correlated units is a powerful, largely
  soft-EM-independent lever worth exploiting either way).
- **Directly verified, not just described**: a live, unauthenticated pull against USGS Water
  Services (`waterservices.usgs.gov/nwis/dv`) for a real gauge (01646500, Potomac River) returned
  **HTTP 200 with real daily-values data — no API key, no login, no registration** — confirmed by
  an actual `curl` request in this session, the same standard of proof used to catch BCSIMS's and
  KU Leuven's Z-24 access gates before committing to either. This is at least as open as
  `grid_reserve_lab`'s EIA-930 endpoint, and more open than `climate_cat_lab`'s claims-data
  situation ever was.
- **One real, flagged risk**: USGS's own page states the legacy WaterServices API "will be
  decommissioned in early 2027," migrating to `api.waterdata.usgs.gov`. Not disqualifying (the
  successor is presumably also public USGS infrastructure), but worth checking the new API's
  access model directly before building against the old one, not assumed compatible.

## A real, plausible economic decision, though not yet sourced in dollar terms

Reservoir storage-yield sizing is a genuine, established real-world decision with the same
asymmetric-cost shape as `grid_reserve_lab`'s reserve-margin problem (under-build risks shortage,
over-build has its own real cost) — one search hit even surfaces a documented, counterintuitive
finding (the "reservoir effect": over-reliance on storage can increase vulnerability to shortage
by reducing preparedness incentives) that would make an honest, non-strawman write-up more
interesting, not less. **Not yet sourced**: real dollar figures analogous to `grid_reserve_lab`'s
VOLL/reserve-capacity-cost pair — a real Phase-0-blocking research task if this lab proceeds,
same discipline as before.

## Verdict

**Passes both required conditions on current evidence, with real open data confirmed directly —
better-grounded at this pre-check stage than `shm_lab` ever was.** This is a genuinely worthwhile
subject to pursue as a properly-scoped lab: a full sourced research pass (six-to-ten claims,
`climate_cat_lab`/`grid_reserve_lab`-style rigor) is the honest next step before any Phase 0 code,
specifically to (a) confirm a real regime frequency in a real chosen basin/region rather than
assuming the return-period vocabulary transfers directly, (b) source real dollar figures for the
shortage/over-storage asymmetric cost, and (c) check `api.waterdata.usgs.gov`'s post-2027 access
model directly rather than building against a service already slated for decommission.
