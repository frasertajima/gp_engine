# Research note: do resource-adequacy / LOLE studies use simplified correlation
# assumptions for wind/solar output rather than a full spatially-resolved joint model?

**Claim being tested:** "Modern probabilistic resource-adequacy / reserve-sizing studies used
by grid operators and reliability organizations (NERC's own Probabilistic Adequacy studies, or
ISO/RTO-specific Loss-of-Load-Expectation simulations at MISO/PJM/ERCOT/CAISO) commonly
aggregate wind/solar output variability or forecast error across many geographically
distributed sites using a SIMPLIFIED correlation assumption — e.g., treating sites as
independent, or using a single fleet-wide/regional correlation coefficient — rather than a
full spatially-resolved joint model that captures genuine tail dependence (the risk that many
sites underperform simultaneously during a regional wind/solar drought)."

**Verdict: MIXED / PARTIALLY VERIFIED, with an important nuance that cuts against the
"independence assumption" framing specifically, but supports the broader "simplified relative
to genuine spatial tail-dependence" framing.** No primary source found describes ISO/RTO
practice as treating sites as statistically *independent* — that specific phrasing is not
supported and should be dropped or softened. What IS well documented, verbatim, in primary
ISO methodology filings: (1) operators DO preserve real historical correlation by using
actual historical time-synchronous wind/solar output data rather than independent draws, but
(2) that correlation is captured only in *aggregate* form — a single fleet-wide or zone-wide
capacity-factor time series per region/LRZ — not as a spatially-resolved multi-site joint
model that could reveal tail dependence beyond what happened to occur in the historical
record; and (3) at least one 2025 peer-reviewed paper explicitly states that the impact of
*correlated* multi-site outages/shortfalls on planned-system reliability has received "little
attention to date" in resource-adequacy assessments. This is the load-bearing nuance the lab
plan should carry forward: it is not "operators assume independence," it is "operators bake in
whatever correlation happened to occur in the historical record, at a coarse (fleet/zone)
resolution, and few published RA studies explicitly test whether that historical sample
under-represents the true tail-dependence risk of a multi-region simultaneous shortfall."

---

## Source 1: MISO, "Planning Year 2025-2026 Loss of Load Expectation Study Report"

- Publisher: Midcontinent Independent System Operator (MISO), the actual ISO/RTO body running
  the LOLE study referenced in the claim.
- URL: https://cdn.misoenergy.org/PY%202025-2026%20LOLE%20Study%20Report685316.pdf
- Accessed: fetched directly as PDF, extracted with `pdftotext -layout`, 2026-07-27.

Section 3.2.5 ("Intermittent Resources"), verbatim, on how wind output is aggregated across
the fleet of individual physical sites:

> "Using historical wind operational data from 279 front-of-meter wind resources from 2013 to
> 2023, normalized hourly capacity profiles were developed and aggregated at the LRZ level to
> represent hourly wind capability in the model. As a result of the LOLE analysis that is based
> on 30 weather years (1994 – 2023), synthetic shapes were developed by Astrapé for the 1994 –
> 2013 period based on historical wind performance and temperatures. Once the weather and wind
> performance matching has been performed, the data is analyzed as a function of load to ensure
> the variability around the load profiles is reasonable."
>
> "Solar profiles were also developed by Astrapé using historical solar irradiance data from
> the NREL National Solar Radiation Database (NSRDB) from 1998 – 2023."

This is the key methodological fact: MISO does **not** treat the 279 individual wind sites as
independent random draws — it uses their actual joint historical output, so real historical
correlation across sites is preserved for the observed 2013-2023 window. But the model then
**aggregates that correlated behavior into a single normalized hourly capacity profile per
Local Resource Zone (LRZ)** — i.e., the granular, site-level joint structure collapses into
one zone-level time series, and the pre-2013 "synthetic shapes" (two-thirds of the 30-year
study window) are statistically reconstructed from historical wind-performance/temperature
matching, not drawn from genuine observed multi-site joint data. So the correlation that
matters for the claim — "do many geographically distributed sites underperform
simultaneously" — is only visible at the zone-aggregate level and only directly observed for
about a third of the modeled 30-year record.

## Source 2: MISO, "Wind and Solar Capacity Credit Report, Planning Year 2024-2025"

- URL: https://cdn.misoenergy.org/Wind%20and%20Solar%20Capacity%20Credit%20Report%20PY%202024-2025632351.pdf
- Accessed: fetched directly as PDF, extracted with `pdftotext -layout`, 2026-07-27.

Section "Correlated Peak Load and Wind Output" / "Deterministic Analytical Technique",
verbatim, on how the fleet-wide result is then allocated back to individual generators (i.e.
the single-coefficient / fleet-wide simplification referenced in the claim):

> "Fleet-wide wind SAC is allocated across the existing and in-operation front-of-meter wind
> resources based on their historical performance during seasonal peak. This is calculated by
> multiplying the seasonal wind ELCC % determined from the LOLE Study modeling by the total
> Registered Maximum Output of the existing and in-operation front-of-meter wind fleet."
>
> "To account for the diverse generation profile of numerous wind CPNodes throughout the MISO
> system (281 front-of-meter wind resources as of December 2024), a deterministic approach that
> accounts for historical performance during unique-day system peak demand hours is used to
> equitably allocate the seasonal fleet-wide wind SAC to all registered wind resources..."

This directly confirms the "single fleet-wide ... coefficient" half of the claim: MISO
computes one seasonal ELCC percentage for the *entire* wind fleet, then allocates it
proportionally back to hundreds of individual sites — it does not carry forward a
site-by-site or sub-region joint distribution into the credit calculation.

## Source 3: E3, "RECAP Probabilistic Loss of Load Model Documentation" (August 2021)

- Publisher: Energy and Environmental Economics (E3) — RECAP is the LOLP/resource-adequacy
  tool used in CPUC/CAISO-adjacent Integrated Resource Planning work referenced in the claim.
- URL: https://www.ethree.com/wp-content/uploads/2022/10/RECAP-Documentation.pdf
- Accessed: fetched directly as PDF, extracted with `pdftotext -layout`, 2026-07-27.

Section 3.1 ("Load & Renewable Simulation"), verbatim — this is the clearest statement found
of the "good" side of the nuance (real historical correlation preserved, not assumed away):

> "The modeling framework is built around capturing correlations among weather, load, and
> renewable generation."
>
> "Generating an extensive record of load and renewable profiles that capture both the range
> of variability of each as well as the key correlations between them is a necessary but
> challenging step in reliability modeling. To generate such a record, RECAP relies upon
> historical time-synchronous load and renewable profiles but also uses statistical approaches
> to extend what is typically a limited historical record."
>
> "Developing a dataset of load and renewables that is weather-matched based on actual
> historical conditions allows the modeling to account for the actual observed correlations
> between load and renewables."
>
> "Hourly profiles for wind and solar should (ideally) cover the same historical period. Like
> above, this allows the model to preserve actual observed correlations."

Notably, the RECAP documentation (25+ pages reviewed) contains **no discussion at all** of
multi-site spatial resolution, per-site joint modeling, or explicit correlation
coefficients between individual wind/solar plants — the correlation-preservation claim is
made entirely at the level of one aggregate regional time series being time-synchronous with
load, which is consistent with the claim's framing of "simplified" relative to a genuine
spatially-resolved multi-site joint model.

## Source 4: Gunda, T., Moore, A.G., Jackson, N.D., Dhulipala, S.C., Awara, S., "A resource
adequacy assessment of correlated wide-area outages in the power grid," *Environmental
Research: Energy* 2, 025009 (2025), Sandia National Laboratories

- URL: https://www.osti.gov/servlets/purl/2585202 (OSTI-hosted full text) /
  https://doi.org/10.1088/2753-3751/add465
- Accessed: fetched directly as PDF, extracted with `pdftotext -layout`, 2026-07-27.

This is the strongest direct-critique source found — a 2025 peer-reviewed paper from a US
national lab whose entire premise is that correlated multi-site renewable/generator shortfall
is under-studied in resource-adequacy practice. Verbatim, Introduction:

> "Historical assessments indicate that a key feature of WAEEs are correlated reductions in
> generator availabilities [22, 25]. **However, many of the assessments to date have not
> evaluated the impact of these co-occurrences on overall reliability of the planned power
> grid systems.** This study addresses this critical gap by using a RA-based assessment to
> characterize risk of power grid systems to WAEEs."

and, on RA's general institutional status quo:

> "Resource Adequacy (RA) techniques, which focus on assessing whether there are sufficient
> available resources to meet load across multiple scenarios, have also been used to assess
> uncertainties in different assumptions (e.g. load, battery storage) in these studies... While
> RA methods have been used to characterize some historical events [22], **the impact of WAEE
> on these synthetic systems has received little attention to date.**"

Important scope caveat: this paper's own case study is about correlated *solar PV* outages
during a hurricane-inspired wide-area extreme event (a different mechanism than a
low-wind/low-solar "drought," which is the mechanism `04_dunkelflaute.md` in this same
directory covers) — but its framing of the state of the field ("many of the assessments to
date have not evaluated the impact of these co-occurrences") is a general, direct statement
about resource-adequacy practice broadly, made by domain researchers at a national lab, in a
peer-reviewed 2025 paper — which is exactly the kind of documented acknowledgment the task
asked to look for.

## What was searched for and NOT found

- NERC's own "Probabilistic Adequacy and Measures" report (April 2018,
  https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/pawg/probabilistic_adequacy_and_measures_report.pdf)
  was fetched and text-searched for "correlat*"; it discusses sequential vs. non-sequential
  Monte Carlo methods and notes sequential simulation "can model issues of concern that
  involve time correlations, such as unit starting times or deferred unplanned outages" — but
  contains no discussion of spatial correlation across wind/solar sites specifically. This is
  a methodology reference document, not a study, so its silence on this point is not strong
  evidence either way — it simply did not surface anything to quote.
- Two Dunkelflaute-methodology papers (Kittel & Schill, "Measuring the Dunkelflaute: how (not)
  to analyze variable renewable energy shortage," arXiv:2402.06758, and "Coping with the
  Dunkelflaute," arXiv:2411.17683) were fetched and searched specifically for critique of
  ISO/TSO correlation-modeling practice. Neither contains it — they are about *defining and
  measuring* drought events from time-series data, not about critiquing how RA studies
  aggregate correlation. The closest passage found (Kittel & Schill) only frames the choice
  between "perfect interconnection" and "island system" assumptions in academic drought
  analysis, not ISO/TSO adequacy-study practice.
- No source was found stating that any ISO/RTO explicitly assumes cross-site
  **independence** for wind/solar output. That specific wording in the claim is
  not supported by anything found and should be removed or clearly hedged — every primary
  ISO/RTO methodology document found (MISO, and by description E3's RECAP for CAISO-adjacent
  IRP work) uses real historical time-series data specifically *because* it preserves
  correlation, the opposite of an independence assumption.

## Plain-language assessment and recommendation for the lab plan

The honest, defensible version of this claim is **not** "grid operators assume renewable
output at different sites is statistically independent" — no evidence for that specific claim
was found, and the primary sources actively contradict it (MISO and E3/RECAP both explicitly
use real historical time-synchronous data to *preserve* correlation). The defensible version
is narrower and more interesting: **operators capture whatever correlation happened to occur
in the historical record, but only at a coarse, aggregate (fleet-wide or zone-wide) level —
collapsing potentially hundreds of individual sites into one time series or one ELCC
percentage — rather than carrying forward a spatially-resolved multi-site joint model that
could be interrogated for tail dependence beyond the historical sample.** And separately, at
least one 2025 peer-reviewed national-lab paper states plainly that the reliability impact of
*correlated* multi-site shortfalls has received "little attention to date" in resource-
adequacy assessments generally.

Recommend `LAB_PLAN.md` rephrase the claim from "...using a SIMPLIFIED correlation assumption
— e.g., treating sites as independent..." to something like: "...using a simplified,
aggregate representation of cross-site correlation — a single fleet-wide capacity-factor time
series or ELCC percentage built from whatever correlation happened to occur in the historical
record — rather than a spatially-resolved joint model of individual sites that could quantify
tail dependence (the risk that many specific sites underperform simultaneously) beyond what
the historical sample happened to contain." Drop "treating sites as independent" as an
option entirely — it is not supported and is contradicted by the primary sources found.

## Sources used

1. MISO, "Planning Year 2025-2026 Loss of Load Expectation Study Report."
   https://cdn.misoenergy.org/PY%202025-2026%20LOLE%20Study%20Report685316.pdf (fetched as
   PDF, extracted with pdftotext, read directly, 2026-07-27)
2. MISO, "Wind and Solar Capacity Credit Report, Planning Year 2024-2025."
   https://cdn.misoenergy.org/Wind%20and%20Solar%20Capacity%20Credit%20Report%20PY%202024-2025632351.pdf
   (fetched as PDF, extracted with pdftotext, read directly, 2026-07-27)
3. E3 (Energy and Environmental Economics), "RECAP Probabilistic Loss of Load Model
   Documentation," August 2021.
   https://www.ethree.com/wp-content/uploads/2022/10/RECAP-Documentation.pdf (fetched as PDF,
   extracted with pdftotext, read directly, 2026-07-27)
4. Gunda, T., Moore, A.G., Jackson, N.D., Dhulipala, S.C., Awara, S. (2025). "A resource
   adequacy assessment of correlated wide-area outages in the power grid." *Environmental
   Research: Energy* 2, 025009. https://doi.org/10.1088/2753-3751/add465, full text via OSTI:
   https://www.osti.gov/servlets/purl/2585202 (fetched as PDF, extracted with pdftotext, read
   directly, 2026-07-27)
5. NERC, "Probabilistic Adequacy and Measures" (Technical Reference Report, April 2018).
   https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/pawg/probabilistic_adequacy_and_measures_report.pdf
   (fetched as PDF, extracted with pdftotext, text-searched for "correlat*", 2026-07-27 —
   checked, nothing on spatial wind/solar correlation found to quote)
6. Kittel, M., Roth, A., Schill, W.-P., "Measuring the Dunkelflaute: how (not) to analyze
   variable renewable energy shortage," arXiv:2402.06758 (checked via WebFetch, 2026-07-27 —
   no relevant critique of ISO/TSO correlation-modeling practice found)
7. Kittel, M., Roth, A., Schill, W.-P., "Coping with the Dunkelflaute: Power sector
   implications of variable renewable energy droughts in Europe," arXiv:2411.17683 (checked
   via WebFetch, 2026-07-27 — no relevant critique of ISO/TSO correlation-modeling practice
   found; see also `04_dunkelflaute.md` in this directory, which uses this source for the
   separate "is Dunkelflaute real" claim)
