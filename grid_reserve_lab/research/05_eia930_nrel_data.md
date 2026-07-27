# Research note: EIA-930 Hourly Electric Grid Monitor and NREL Wind Toolkit / NSRDB

**Claims under test** (grid_reserve_lab, modeled on climate_cat_lab's FEMA NRI verification pass —
see `climate_cat_lab/research/05_fema_nri.md` for the reference format):

1. EIA-930 (the EIA's hourly electric grid monitor) provides real, public, continuously-updated
   hourly data on demand, net generation by fuel type (including wind and solar), and interchange,
   per Balancing Authority, across the US grid.
2. NREL's Wind Toolkit and/or National Solar Radiation Database (NSRDB) provide real, public,
   site-resolved historical wind/solar resource and modeled-output data at a granularity useful for
   building a synthetic or semi-real fleet of wind/solar sites with realistic spatial correlation
   structure.

**Access note on method:** `eia.gov` was directly fetchable in this pass (unlike FEMA's domain in
the climate_cat_lab precedent) — `www.eia.gov/todayinenergy/detail.php?id=40993` and
`www.eia.gov/about/copyrights_reuse.php` both returned full page content. `nrel.gov` and
`developer.nrel.gov`, however, failed on every attempt with a DNS resolution error
(`getaddrinfo ENOTFOUND www.nrel.gov`, same for `developer.nrel.gov` and `nsrdb.nrel.gov`) rather
than an HTTP block — this looks like a network/DNS-level issue specific to this session's fetch
tool for the `nrel.gov` domain (possibly a NXDOMAIN response returned to automated clients, or an
environment-level block), not evidence the resource doesn't exist. Two NREL-hosted mirrors were
fetchable directly and stood in for the primary domain: the AWS Open Data Registry pages
(`registry.opendata.aws/nrel-pds-nsrdb/`, `registry.opendata.aws/nrel-pds-wtk/`) and the OpenEI
submission page (`data.openei.org/submissions/2`), both of which are NREL/DOE-authored content
mirrored on non-`nrel.gov` infrastructure. WebSearch snippets (Google/Bing-crawled, including
direct quotes from `nrel.gov` and `developer.nrel.gov` pages that this session's WebFetch could not
reach) fill the remaining gaps. Flagging this explicitly, per the same honesty pattern as the FEMA
note.

---

## Claim 1: EIA-930

### What it is (verbatim, fetched directly from `www.eia.gov/todayinenergy/detail.php?id=40993`)

> "The tool displays hourly electricity generation by energy source and hourly subregional demand"
> across the Lower 48 states. It includes demand forecasts, net generation, and interchange data
> collected from 65 electricity balancing authorities.

Corroborated by WebSearch snippet of EIA's own product description:

> "Form EIA-930 collects data from the 65 electricity balancing authorities that operate the
> electric grid in the Lower 48 states." Data elements: "hourly demand, hourly day-ahead demand
> forecast, net generation, and net interchange with each adjacent balancing authority. Starting in
> July 2018, data including net generation by fuel type and subregion demand are now available."

### Update frequency (fetched verbatim)

> "Demand data: Available on a near-real-time basis, approximately one hour after each hour
> concludes." "Other data elements: Generally accessible with a one- to two-day lag."

### Geographic / historical coverage (fetched verbatim)

> Spans "65 balancing authorities" in the Lower 48 states. Subregional demand breakdowns available
> for 8 named operators (CISO, ERCO, MISO, ISNE, NYIS, PJM, PNM, SWPP). Historical depth: "New
> elements (generation by source, subregional demand): back to July 2018"; "original elements: back
> to July 2015."

### Access method (fetched verbatim)

> "Custom interactive dashboards (saveable and shareable)"; "CSV, JSON, and XLSX file downloads";
> "Application programming interface (API) and Excel Add-In"; "static chart/map exports as PDF or
> PNG files."

One caveat surfaced in the same page: "The tool excludes distributed resources like rooftop solar
that balancing authorities don't directly monitor" — i.e. EIA-930's wind/solar generation figures
are utility-scale, grid-metered generation only, not total wind/solar output including behind-the-
meter/rooftop.

### Independent corroboration

- **PUDL (Catalyst Cooperative)**, an open-source energy-data ETL project, documents and ingests
  EIA-930 directly (`docs.catalyst.coop/pudl/en/nightly/data_sources/eia930.html`), i.e. a third
  party has built production tooling against this exact dataset, evidence it is a real, stable,
  machine-consumable data source and not a one-off web page.
- **DOE OSTI Data Explorer** lists "Form EIA-930 Data" and "Form EIA-930 Data Reformatted" as
  archived datasets (`osti.gov/dataexplorer/biblio/dataset/1963660` and `/1963662`).
- Academic/applied use: the Stanford "Grid Emissions" project (J. DeChalendar et al., "A
  physics-informed data reconciliation framework for real-time electricity and emissions
  tracking") builds directly on EIA-930 reported data, reconciling it against physical grid
  constraints — direct evidence of real-world research reliance on this dataset for exactly the
  demand/generation/interchange fields the claim describes.
- Per WebSearch summary of EIA's own site: as of 2024Q3, EIA-930 fuel-type categories were
  expanded to split wind/solar with and without storage, add battery storage and geothermal
  categories — i.e. the dataset is under active, ongoing schema maintenance, not a frozen legacy
  product.

### License / public-domain status (fetched verbatim, `www.eia.gov/about/copyrights_reuse.php`)

> "U.S. government publications are in the public domain and are not subject to copyright
> protection."
>
> "You may use and/or distribute any of our data, files, databases, reports, graphs, charts, and
> other information products that are on our website or that you receive through our email
> distribution service."
>
> Required attribution format: "Source: U.S. Energy Information Administration (Oct 2008)."

This is a direct, verbatim, primary-source confirmation — stronger than the FEMA note's precedent,
which could only infer public-domain status from 17 U.S.C. §105 and third-party mirrors without a
verbatim EIA-equivalent quote. Here the explicit statement was read directly from EIA's own page.

### Verdict — Claim 1: **CONFIRMED**

EIA-930 is real, public, continuously updated (near-real-time demand, 1-2 day lag for other
fields), covers 65 Balancing Authorities across the Lower 48 states, includes hourly demand, net
generation by fuel type (including utility-scale wind and solar, but excluding rooftop/distributed
solar), and interchange between adjacent BAs — exactly as claimed. Access is via API, bulk
CSV/JSON/XLSX, and an Excel add-in. Public-domain status is confirmed by direct verbatim quote from
EIA's own copyright/reuse policy page (fetched directly in this pass, not inferred). The only
caveat to carry into the lab's design: generation-by-fuel-type figures are grid-metered utility-
scale only, so behind-the-meter solar is not represented in EIA-930 and would need to come from
elsewhere if the lab needs it.

---

## Claim 2: NREL Wind Toolkit and NSRDB

### NSRDB — what it is (fetched verbatim via AWS Open Data Registry mirror,
`registry.opendata.aws/nrel-pds-nsrdb/`, since `nrel.gov`/`developer.nrel.gov` were unreachable
from this session)

> "Serially complete collection of hourly and half-hourly values of the three most common
> measurements of solar radiation – global horizontal, direct normal, and diffuse horizontal
> irradiance — and meteorological data."

### NSRDB spatial/temporal resolution (fetched verbatim)

> - v3 main dataset: 4 km × 30-minute intervals (1998-2018)
> - CONUS data: 2 km × 5-minute intervals (2018-present)
> - Western Hemisphere (GOES): 2 km × 10-minute intervals (2018-present)
> - Puerto Rico: 2 km × 5-minute intervals (1998-2017)
> - Meteosat: 4 km × 15-minute intervals (2017-present)
> - Himawari: 4 km × 10-minute intervals (2015-present)

### NSRDB access / license (fetched verbatim)

> Format: HDF5. Update frequency: annually. License: "Creative Commons Attribution 3.0 United
> States License."

### WIND Toolkit — what it is (fetched verbatim via OpenEI mirror, `data.openei.org/submissions/2`,
and AWS registry `registry.opendata.aws/nrel-pds-wtk/`, primary `nrel.gov` domain unreachable)

> "Wind resource data for North America was produced using the Weather Research and Forecasting
> Model (WRF)." Initialized from ERA-Interim reanalysis at 54 km, refined through nested domains to
> a final 2 km grid, spanning 2007-2014.

### WIND Toolkit fields and resolution (fetched verbatim)

> Wind speed and direction at 10, 40, 60, 80, 100, 120, 140, 160, 200 m; temperature at 2, 10, 40,
> 60, 80, 100, 120, 140, 160, 200 m; pressure at 0, 100, 200 m; surface precipitation rate,
> relative humidity, inverse Monin-Obukhov length. "Wind speed and direction: full 5-minute
> resolution available; all other variables: hourly instantaneous values. Spatial resolution: 2 km
> final grid spacing." Coverage: "more than 126,000 land-based and offshore wind power production
> sites" across the contiguous United States (per WebSearch snippet of NREL's own description,
> corroborating the OpenEI page).

### WIND Toolkit access method (fetched verbatim + WebSearch corroboration)

> API: "Wind Toolkit Data API enables users to create large downloadable data archives via a data
> request." AWS S3: "nrel-pds-wtk" bucket, "2.67 petabytes," accessible via AWS CLI. HSDS: "Jupyter
> Notebook examples demonstrate programmatic access... through the HSDS Service" — a Python client
> (`h5pyd`) compatible with `h5py`, hitting an NREL-hosted API endpoint
> (`developer.nrel.gov/api/hsds`) that requires a free API key.

One older WebSearch snippet (apparently from an earlier NREL documentation revision) stated that
full-resolution WIND Toolkit data was "not publicly available at this time" and required a
"detailed request" — this appears to describe the raw underlying WRF model output (which at
petabyte scale was historically request-only), not the extracted/processed per-site toolkit data
product, which the AWS registry, OpenEI, and HSDS/h5pyd documentation all currently describe as
openly and programmatically accessible without a gatekept request process, only a free API-key
signup. Flagging the discrepancy rather than silently picking the more convenient reading: the
current (2024-era, per a WebSearch-summarized DOE/energy.gov item on a March 2024 "Wind Resource
Database" launch) state of the art is open AWS S3 / HSDS access; older cached documentation may
still describe a request-gated predecessor.

### WIND Toolkit license (fetched verbatim)

> "Publicly accessible License" under Creative Commons Attribution 4.0 (CC-BY). DOI:
> 10.25984/1822195.

### Independent corroboration relevant to the specific claim (spatial correlation structure)

A paper on synthesizing Phasor Measurement Unit data from large-scale electric network models
(WebSearch-indexed, arxiv.org/pdf/1909.03187) used simulated 5-minute wind speed profiles from the
WIND Toolkit for synthetic wind farms placed by geographic location, and explicitly computed
pairwise correlations among the synthetic farms, fitting a two-segment polynomial curve relating
correlation to inter-site distance. This is a direct, independent precedent for exactly the use
case in Claim 2 — building a synthetic fleet of sites with realistic spatial correlation structure
from WIND Toolkit data — and confirms the dataset supports it in practice, not just in principle.

Further corroboration: "A Multi-Decadal Hourly Coincident Wind and Solar Power Production Dataset
for the Contiguous United States" (Nature *Scientific Data*, 2024,
nature.com/articles/s41597-024-03894-w, WebSearch-indexed) is a recent peer-reviewed dataset paper
built jointly on WIND Toolkit and NSRDB data to produce coincident, correlated wind+solar power
time series across CONUS — i.e. current (2024) academic work independently validates both datasets
as suitable inputs for exactly this kind of joint/correlated synthetic generation-fleet modeling.

### Verdict — Claim 2: **CONFIRMED**

Both NSRDB (solar: irradiance components at 2-4 km / 5-30 minute resolution depending on product
version, 1998/2015/2017-present depending on region, CC-BY 3.0 US, HDF5, AWS + API access) and the
WIND Toolkit (wind: speed/direction at multiple hub heights on a 2 km grid, 5-minute for wind
speed/direction, hourly for other variables, 2007-2014, >126,000 CONUS sites, CC-BY 4.0, AWS S3 /
HSDS / API access) are real, public, site-resolved datasets at a granularity well above what's
needed to place a synthetic fleet of wind/solar sites with realistic spatial correlation — and at
least one independent paper has done precisely that (synthetic wind farms + pairwise correlation
vs. distance) using WIND Toolkit data, with a 2024 peer-reviewed paper doing the joint wind+solar
version using both datasets together. License terms (CC-BY 3.0/4.0) were captured verbatim, though
note this is a Creative Commons attribution license (from NREL, operated for DOE by Alliance for
Sustainable Energy, LLC — a contractor, not a federal agency directly) rather than the bare public-
domain statement EIA gave; reuse requires attribution but is otherwise unrestricted, consistent
with, but not identical in form to, straightforward 17 U.S.C. §105 public-domain status.

---

## Access blockers encountered (explicit, per lab convention)

- `eia.gov` pages: fetchable directly, no blocker.
- `nrel.gov` and `developer.nrel.gov` (including `nsrdb.nrel.gov` and
  `www.nrel.gov/grid/wind-toolkit`): every attempt returned `getaddrinfo ENOTFOUND` — a DNS
  resolution failure, not an HTTP-level block (contrast with FEMA's HTTP 403 in the climate_cat_lab
  precedent). Worked around via NREL/DOE-authored mirrors on other domains
  (`registry.opendata.aws`, `data.openei.org`) that were directly fetchable, plus WebSearch
  snippets that quote `nrel.gov`/`developer.nrel.gov` pages this session's fetch tool could not
  reach. All verbatim NREL-sourced quotes above are therefore either (a) fetched directly from a
  non-`nrel.gov` mirror, or (b) WebSearch-indexed snippets of the primary `nrel.gov` pages,
  explicitly labeled as such inline — none were silently treated as directly fetched when they were
  not.

## Overall verdict

Both claims are **CONFIRMED**. EIA-930 and NREL's WIND Toolkit/NSRDB are real, currently
maintained, public, well-documented datasets, each independently corroborated by third-party
tooling (PUDL, OSTI) and peer-reviewed academic use (Stanford Grid Emissions reconciliation project
for EIA-930; the PMU-synthesis paper and the 2024 *Scientific Data* coincident wind+solar paper for
WIND Toolkit/NSRDB), with licensing terms captured verbatim in both cases (EIA: explicit public-
domain statement; NREL: CC-BY 3.0/4.0 attribution licenses). grid_reserve_lab can proceed treating
both as viable real-data grounding sources, with two caveats to carry forward: EIA-930's fuel-type
generation figures are utility-scale/grid-metered only (no rooftop solar), and WIND Toolkit's full
5-minute-resolution raw archive access pattern should be re-checked against current NREL
documentation directly once `nrel.gov` is reachable, to resolve the minor discrepancy noted above
between an older "request-only" description and the current AWS/HSDS open-access description.
