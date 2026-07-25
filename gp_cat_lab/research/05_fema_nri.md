# Research note: FEMA National Risk Index (NRI)

**Claim under test** (climate_cat_lab/LAB_PLAN.md, Phase 3 stretch): the FEMA National Risk
Index is a real, public dataset that can ground Phase 3's hazard geography in actual data
(county/census-tract hazard scores), while losses themselves stay synthetic.

**Access note on method:** `fema.gov` and `hazards.fema.gov` return HTTP 403 to this session's
WebFetch tool on every URL tried (`www.fema.gov/about/openfema/data-sets/national-risk-index-data`,
`www.fema.gov/flood-maps/products-tools/national-risk-index`, the methodology/FAQ PDFs, and
`hazards.fema.gov/nri/data-archive` — the last returned "socket closed" rather than 403, likely
the same block manifesting differently). This looks like a bot/user-agent block on FEMA's domain,
not evidence the resource doesn't exist — WebSearch snippets (which Google/Bing crawled directly)
and independent third-party mirrors corroborate the same facts below, so the verdict is confirmed
via corroborating sources rather than a direct fetch of the primary domain. Flagging this
explicitly rather than silently treating a search snippet as equivalent to a fetched primary page.

## What it is (verbatim)

From FEMA's own page text, as indexed and returned by WebSearch (query: "FEMA National Risk Index
NRI dataset county census tract hazard methodology"):

> "The National Risk Index dataset provides information for communities most at risk to 18
> different natural hazards and offers a baseline risk measurement for expected annual loss,
> social vulnerability and community resilience at the Census tract or county level."

> "The National Risk Index data leverages available source data for natural hazard and community
> risk factors to develop a baseline risk measurement for each United States county and U.S.
> Census tract. The National Risk Index dataset provides Risk Index scores and ratings for
> counties and Census tracts for all 50 states and the District of Columbia."

Independently, from SparkMap (a public-health data portal citing FEMA directly — fetched
verbatim, https://sparkmap.org/data-info/climate-health-national-risk-index/, accessed
2026-07-23):

> "The FEMA National Risk Index 'provides a holistic view of community-level risk nationwide by
> combining multiple hazards with socioeconomic and built environment factors.'"
>
> "The index employs the formula: NRI = Expected Annual Loss × Social Vulnerability × (1 /
> Community Resilience). Expected Annual Loss quantifies projected annual losses to buildings,
> population, and agriculture. Social Vulnerability measures community susceptibility to hazard
> impacts. Community Resilience assesses capacity to prepare, adapt, withstand, and recover from
> natural disasters."
>
> Source citation given: "Federal Emergency Management Agency, National Risk Index, 2023. Data
> sourced from the November 2021 release of the National Risk Index."

## Hazards covered (18, per SparkMap's citation of FEMA)

Avalanche, Coastal Flooding, Cold Wave, Drought, Earthquake, Hail, Heat Wave, Hurricane, Ice
Storm, Landslide, Lightning, Riverine Flooding, Strong Wind, Tornado, Tsunami, Volcanic Activity,
Wildfire, Winter Weather (SparkMap's list names 18 items but differs slightly in labeling from
the WebSearch-indexed FEMA list, which separately names "Sea level rise (with coastal flooding)"
and "Severe summer weather" / "Wind" as distinct entries — the two lists appear to be different
NRI dataset versions/releases, not a contradiction; both agree on the count (18) and the general
composition: flood, wind/storm, temperature, geologic, and wildfire perils). Directly relevant to
climate_cat_lab: **Coastal flood, Drought, Hurricane, Riverine/Flood, Wildfire, Wind** are all
present, i.e. the exact peril families this lab's synthetic DGP is modeling.

## Access method (verbatim, via WebSearch)

> "The December 2025 v1.20 data is now available through OpenFEMA as downloadable CSV,
> Geo-database, and Shapefiles."
>
> "Downloads are available at https://hazards.fema.gov/nri/data-resources for Geodatabase,
> Shapefile, and CSV formats."

Corroborated independently by the Data Rescue Project portal (fetched verbatim,
https://portal.datarescueproject.org/datasets/national-risk-index-nri/, accessed 2026-07-23),
which lists the source agency as "Federal Emergency Management Agency" (DHS) and confirms
"Multiple formats are available: ZIP file, Geodatabase, Shapefile, and CSV," with the same
`hazards.fema.gov` source and mirrors on DataLumos and Harvard Dataverse — i.e. this dataset is
mirrored by independent academic data-preservation projects, further evidence it is a real,
durable public dataset and not a single fragile government-site listing.

## License / public-domain status

Not confirmed by direct quote in this pass — no explicit "public domain" or license statement
was captured verbatim from any source fetched. FEMA/DHS federal datasets are conventionally
public domain (17 U.S.C. §105, works of the U.S. federal government), and the existence of
third-party academic mirrors (DataLumos, Harvard Dataverse) is consistent with that, but this
specific claim should be treated as a reasonable inference, not a verified quote, until the
actual FEMA terms-of-use page is read directly (blocked in this pass — see access note above).

## Verdict

**Confirmed, with one caveat.** The FEMA NRI is a real, actively maintained (December 2025 v1.20
release referenced), public dataset at county and census-tract resolution, covering the exact
peril families (flood, wind/hurricane, wildfire, drought) this lab's synthetic DGP targets, in
three standard geospatial/tabular formats (CSV, Shapefile, Geodatabase) via
`hazards.fema.gov/nri/data-resources` and OpenFEMA, with independent academic mirrors. It is
**usable as planned for Phase 3** (grounding hazard geography, not losses). The one open item is
the explicit license statement, which should be re-checked by reading FEMA's actual terms-of-use
page directly (this pass could not, due to `fema.gov` blocking WebFetch with HTTP 403 on every
URL tried) before treating redistribution as unrestricted — federal-public-domain status is very
likely but was not read verbatim from a primary source in this pass.
