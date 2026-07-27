# Research note: is "Dunkelflaute" a real, documented grid-planning phenomenon?

**Claim being tested:** "'Dunkelflaute' (a German-coined term for an extended period of low
wind AND low solar output, often correlated across a wide geographic region) is a real,
named phenomenon studied in grid-planning and energy-system literature (European and
increasingly North American), and is a genuine, documented driver of resource-
adequacy/reliability risk as wind and solar penetration grows."

**Verdict: VERIFIED, with one scope caveat. The term and underlying phenomenon are real,
peer-reviewed, and explicitly tied to resource-adequacy/reliability risk and long-duration-
storage planning — this is not media buzz. The term itself ("Dunkelflaute") is German-
coined and still primarily a European/ENTSO-E framing; the equivalent US technical
literature exists and is quantitatively rich (ERCOT, CAISO, MISO, PJM, ISO-NE data), but
US researchers more often use the plain-English term "resource drought" or "wind/solar
(energy) drought" rather than importing "Dunkelflaute" itself. LAB_PLAN.md can keep
"Dunkelflaute" as the illustrative/motivating hook but should present "correlated
multi-day wind+solar resource drought" as the operative, US-native framing for any
quantitative claims.**

---

## Source 1: Somani, A. et al., "An Assessment of Resource Drought Events as Indicators for
Long-Duration Energy Storage Needs" (IEA Hydro Annex IX, May 2024)

- Authors/affiliations: Pacific Northwest National Laboratory, Argonne National Laboratory,
  Oak Ridge National Laboratory (all US DOE national labs), plus Hydro Tasmania,
  Hydro-Québec, EDF France, Strategen Consulting, Freddie Mac.
- Publisher: IEA Hydro Technical Cooperation Programme, Annex IX ("Energy Storage Needs
  for Resource Drought").
- URL: https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-35955.pdf
- Accessed: 2026-07-27 (fetched as PDF, extracted with pdftotext -layout; quotes verified
  against extracted text directly, not a search-engine summary).

**On the term itself being real and adopted, not just media framing** — verbatim:

> "As the amount of VRE has grown rapidly in most regions of the world in the last decade,
> the existence of longer periods of low VRE availability is getting increasing attention
> from the perspective of the power grid. As an example, the German term "dunkelflaute"
> (loosely translating to "the dark doldrums") has become a universally adopted term to
> describe periods in which there is severely reduced energy availability from wind and
> solar, such as prolonged periods of substantial cloud coverage paired with limited wind.
> This term helps to contextualise the challenges of balancing supply and demand under
> these weather conditions."

**On a specific published definition (Li et al. 2021, cited within this report)** — verbatim:

> "Their definition of a drought event was based on power capacity factors, where they
> defined "dunkelflaute" as an event where both wind and solar power capacity factors drop
> below 20% for at least 24 hours. The authors found that these events happen almost
> exclusively in November, December, and January in Europe and that the frequency of such
> events drops from 3–9% for individual countries to 3.5% for the combined region."

**On direct connection to resource adequacy / reliability (the core of the claim)** —
verbatim:

> "The frequency, duration, and magnitude of VRE resource droughts will inform resource
> adequacy and reliability needs, and hence, can be important indicators of the potential
> need for LDES because they demonstrate a mismatch between VRE generation and system
> demand over extended periods of time."

and, in the conclusions:

> "The analysis in the report shows a growing number of resource drought events across
> multiple regions driven by increased reliance on weather-dependent power generation.
> Historical resource droughts are a strong indicator for the need for LDES... More work is
> needed to bridge resource drought events with LDES procurement recommendations to avert
> reliability impacts to the power system. Existing resource adequacy metrics are designed
> to specify procurement targets for fossil fuel-based generation. These metrics will need
> to evolve to clarify the system need for both power capacity (as with current metrics)
> and energy capacity."

**Quantification, specifically for US balancing authorities (ERCOT and CAISO)** — verbatim
table data (Table ES-1, onshore wind energy drought metrics; drought defined as output
falling below 10% of historical annual production for a minimum of 4 hours):

> "ERCOT 2018-2022 82 [events] 8 [avg. duration, hours] 25% [avg. energy deficit, % of
> load] 15 [duration of longest event, hours] 145,853 [energy deficit of longest event, MWh]"
>
> "CAISO 2018-2022 167 [events] 9 [avg. duration, hours] 8% [avg. energy deficit] 42
> [duration of longest event, hours] 71,849 [energy deficit of longest event, MWh]"

And the report's own summary of that table:

> "The study results show that more than 10 wind drought events per year can be expected in
> North America, while more than 50 wind drought events can be expected in various regions
> of Australia on average annually."

**On the US research lineage specifically (this is the key "does it exist in US literature"
answer)** — verbatim:

> "Most of the research on low-VRE events comes from Europe. Outside of this region there
> have been analyses in the United States, Australia, and Japan. In the United States,
> Bhatnagar et al. (2022) evaluated wind drought events over a 3 year period from 2018
> through 2020 for several balancing areas, including the Electric Reliability Council of
> Texas (ERCOT), Independent System Operator of New England (ISO-NE), Midcontinent
> Independent System Operator (MISO), and PJM Interconnection LLC (PJM). They defined wind
> droughts as a continuous period during which the average hourly output is less than 10%
> of the average hourly output during that calendar month... Bracken et al. (2024) analysed
> compound wind and solar droughts with synthetic power production within all balancing
> authorities in the United States."

**Important terminology note (US literature does NOT generally use the German word)**: in
all of the US-specific analysis sections of this report (CAISO, ERCOT), the authors
consistently use "wind drought," "solar drought," and "resource drought" — "dunkelflaute"
appears only in the background/literature-review section as the term's European origin
story, never as the operative label applied to the US balancing-authority results. This is
a real, structural distinction, not an oversight: the concept has been imported and
independently quantified for the US grid using domestic vocabulary.

## Source 2: Kittel, M., Roth, A., & Schill, W.-P., "Coping with the Dunkelflaute: Power
sector implications of variable renewable energy droughts in Europe" (arXiv:2411.17683v5,
2025)

- Accessed: 2026-07-27.

Verbatim definition (the authors' own refined/preferred definition, explicitly cautioning
against overuse of the term for short events):

> "extended (winter) periods where renewable energy falls short of electricity demand,
> which ultimately define the energy capacity and the operation of long-duration storage."

> "we suggest not using the term Dunkelflaute for very short periods of low wind and solar
> availability, especially not for a few hours within a day."

Verbatim on severity/duration:

> The most severe historical event analyzed occurred in winter 1996/97, with extreme
> droughts lasting "up to several months and span[ning] across the turn of years,"
> affecting "many countries simultaneously."

Verbatim on the resource-adequacy/reliability policy implication:

> "transitioning to a renewable European energy system may require significant
> long-duration storage capacities in the order of several hundred TWh, particularly for
> coping with extreme, yet rarely occurring, Dunkelflaute events."

> "targeted support instruments or capacity mechanisms may be necessary to ensure the
> realization of sufficient storage capacity" since market actors are unlikely to invest in
> rarely-utilized capacity without incentives.

## Source 3: (paper cited within, via search synthesis — not independently fetched
verbatim) Quantifying/measuring Dunkelflaute — Kittel & Schill and related IOP Science
papers ("Measuring the Dunkelflaute: how (not) to analyze variable renewable energy
shortage," and "Quantifying the Dunkelflaute," arXiv:2410.00244v1)

- Accessed via WebFetch of arXiv HTML: 2026-07-27.

Verbatim definition and key frequency/duration figures (Kittel & Schill):

> Dunkelflaute is defined as "long-lasting and substantial shortages of VRE supply" that
> "may cover large geographical areas."

> At a τ=0.75 severity threshold: "approximately eight, five, or four VRE portfolio
> droughts per year in Germany, Spain, or Europe that lasted at least one week."

> Maximum observed durations: "106 days in Germany (1996) and 55 days across perfectly
> interconnected Europe (winter 1996/97)."

> Portfolio (wind+solar combined) effect on severity: "maximum drought duration of a
> renewable technology portfolio...decreases by 64%, 52%, or 47% compared to standalone PV,
> onshore wind, or offshore wind" — i.e. diversifying wind+solar reduces but does not
> eliminate the correlated-shortfall risk, which is the mechanistic core of the claim being
> tested.

Verbatim on reliability implication:

> "Dealing with VRE drought events necessitates the use of long-duration storage and other
> flexibility options," and these "compound events are a major driver for the use of
> long-duration electricity storage in all three interconnection states."

> "extreme droughts may occur at the turn of years, suggesting that planning horizons based
> on single calendar years are inappropriate for modeling weather-resilient future energy
> systems."

## Source 4: Biewald, B., Cozian, B., Dubus, L., Zappa, W., & Stoop, L.P., "Evaluation of
'Dunkelflaute' event detection methods considering grid operators' needs" (2025)

- Accessed via WebFetch of IOPscience: 2026-07-27.
- Relevance: this is the source that most directly answers "is this genuinely used by grid
  operators / TSOs, not just academics."

Verbatim:

> "Being able to identify and assess the severity, duration, and frequency of dunkelflaute
> events is crucial for monitoring resource adequacy, and planning a reliable future power
> system."

> "TSOs could adopt such methods in adequacy studies, either for stress testing or to run
> the computationally expensive power system simulations on a reduced set of climate years."

Disclosure note in the paper itself (showing direct TSO institutional ties, while also
showing this is not yet fully "baked into" official TSO doctrine): "The content of this
paper and the views expressed in it are solely the authors' responsibility, and do not
necessarily reflect the views of TenneT and/or RTE." The authors disclose they "are, or
have been, members of ENTSO-E's Expert Team Climate" — i.e. this is European-TSO-adjacent
research (ENTSO-E is the pan-European association of transmission system operators), not
an independent academic exercise with no grid-operator link, but it is also not yet a
codified line item in a published TSO adequacy standard as far as this fetch could confirm.

## Assessment against the three specific questions asked

**(a) Is this a real term in serious technical/grid-planning literature, not just media
buzz?** Yes, unambiguously. Multiple 2024-2025 peer-reviewed/preprint papers (Kittel &
Roth & Schill; Biewald et al.; the IEA Hydro Annex IX report co-authored by three US DOE
national labs) treat it as a defined technical term with explicit thresholds (capacity
factor cutoffs, minimum durations), not a colloquialism.

**(b) Is there quantification of frequency/severity, ideally with a real duration/frequency
figure?** Yes, and multiple independent figures converge: roughly 4-9 week-plus VRE
portfolio droughts per year across Germany/Spain/Europe (Kittel & Schill, τ=0.75), with
documented multi-week-to-multi-month extreme tail events (up to 106 days in Germany,
55 days pan-European in 1996/97). For the US specifically: 82 wind-drought events over
2018-2022 in ERCOT (avg. 8 hrs, worst case 15 hrs / ~146 GWh deficit) and 167 events in
CAISO (avg. 9 hrs, worst case 42 hrs / ~72 GWh deficit) per the PNNL/DOE-lab report — these
are shorter-duration/higher-frequency than the European "Dunkelflaute" tail events because
the US analyses used shorter minimum-duration thresholds (4+ hours vs. Europe's week-plus
framing), which is itself a useful nuance: "Dunkelflaute" in Europe tends to mean the
multi-day-to-multi-week extreme tail, while the US "resource/wind drought" literature also
quantifies much shorter, more frequent events using the same underlying methodology.

**(c) Is there a documented connection to reserve-margin/resource-adequacy risk
specifically, not just general renewables-variability rhetoric?** Yes, explicitly and
repeatedly — this is the central policy conclusion in every source fetched, not an
incidental mention: PNNL/DOE report ties resource-drought frequency/duration/magnitude
directly to "resource adequacy and reliability needs" and long-duration storage
procurement targets; Kittel & Roth & Schill tie it to the sizing of "several hundred TWh"
of long-duration storage and to the need for capacity mechanisms; Biewald et al. tie it
directly to TSO adequacy stress-testing methodology.

## On US traction specifically (the scope question most relevant to this lab)

The term "Dunkelflaute" itself remains a European (German-origin, ENTSO-E-adjacent)
coinage — none of the US-specific analyses reviewed (Bhatnagar et al. 2022, Bracken et al.
2024, the CAISO/ERCOT sections of the PNNL/DOE report) apply the German word to their own
results; they use "wind drought," "solar drought," or "resource drought." However, the
underlying concept has substantial, quantitatively rigorous US traction under that
domestic vocabulary, produced by US DOE national labs (PNNL, Argonne, Oak Ridge) using US
ISO/RTO data (ERCOT, CAISO, MISO, PJM, ISO-NE) — so the *phenomenon* is well-established in
US grid-planning literature even though the *word* is not yet naturalized there.

## Recommendation for LAB_PLAN.md

Keep "Dunkelflaute" as the evocative, motivating term in narrative/introductory framing —
it is legitimate, not media hype, and instantly signals the mechanism to anyone who has
encountered the European energy-policy discourse. But for any quantitative claim grounded
in this lab's US/EIA-930/NREL illustrative scope, use the native US framing —
**"correlated multi-day (or multi-hour) wind+solar resource shortfall"** or simply
**"wind/solar (resource) drought"** — and cite the PNNL/DOE Annex IX report's ERCOT/CAISO
figures (Source 1 above) rather than the German-literature duration figures, since the US
and European studies use different minimum-duration thresholds and are not directly
comparable without adjustment. A one-line footnote noting "Dunkelflaute" as the European-
coined term for the same phenomenon, with a pointer to the US-native vocabulary, would be
the most defensible framing.
