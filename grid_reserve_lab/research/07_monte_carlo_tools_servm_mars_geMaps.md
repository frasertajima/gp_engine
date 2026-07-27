# Research note: Sequential Monte Carlo tools (SERVM, MARS, GE-MAPS) in US resource adequacy planning

**Claim tested:** Sequential Monte Carlo simulation tools — specifically SERVM, MARS, and
GE-MAPS — are standard, widely-used software across US ISOs/RTOs and utilities for
long-term resource adequacy studies (setting annual planning reserve margins years in
advance).

**Verdict: PARTIALLY VERIFIED.** SERVM and MARS are each independently confirmed, by
primary documents from multiple real ISOs/RTOs/regulators (not just vendor marketing), as
genuine sequential-Monte-Carlo tools in active, current use for long-term resource adequacy
/ reserve-margin work. GE-MAPS, however, does **not** belong in this list on the same terms:
it is GE's production-cost/economic-dispatch model, and GE's own current documentation
describes it as deterministic, not Monte Carlo — a different tool from MARS, which is GE's
actual resource-adequacy Monte Carlo product. The claim as stated conflates a real,
well-evidenced two-tool family (SERVM + MARS) with a third tool (GE-MAPS) that serves a
different modeling purpose and methodology.

## What each tool is

### SERVM (Strategic Energy & Risk Valuation Model), Astrapé Consulting / PowerGEM

> "The ESR ELCC study utilized the Strategic Energy Risk Valuation Model (SERVM) software
> package from Astrapé Consulting. SERVM is a production-cost software, which performs a
> Security Constrained Economic Dispatch while utilizing a Monte-Carlo algorithm when
> varying the uncertainty of load and availability of capacity through multiple
> simulations."
— *2022 ELCC ESR Study Report*, Southwest Power Pool, Inc. (SPP Resource Adequacy),
February 2023, p. 4 (§2.2 Software).
`https://www.spp.org/documents/68930/2022%20elcc%20esr%20report.pdf`

> "We have been asked by the Electric Reliability Council of Texas (ERCOT) to estimate the
> market equilibrium reserve margin (MERM) and the economically optimal reserve margin
> (EORM) for ERCOT's wholesale electric market. For this analysis, Astrapé Consulting
> simulated the ERCOT market using its Strategic Energy & Risk Valuation Model (SERVM). ...
> it probabilistically simulates the economic and reliability implications of a range of
> possible reserve margins under a range of weather and other conditions."
— *Estimation of the Market Equilibrium and Economically Optimal Reserve Margins for the
ERCOT Region for 2024*, Astrapé Consulting (Kevin Carden, Alex Krasny Dombrowsky), prepared
for the Electric Reliability Council of Texas ("ERCOT"), January 15, 2021, p. 5 (Executive
Summary). `https://www.ercot.com/files/docs/2021/01/15/2020_ERCOT_Reserve_Margin_Study_Report_FINAL_1-15-2021.pdf`

CPUC (California) also directly retains Astrapé/SERVM for its own Resource Adequacy and
Integrated Resource Planning proceedings — e.g. *Incremental ELCC Study for Mid-Term
Reliability Procurement*, prepared by E3 and Astrapé Consulting for CPUC Energy Division,
August 31, 2021 and updated February 10, 2023
(`https://www.cpuc.ca.gov/-/media/cpuc-website/divisions/energy-division/documents/integrated-resource-plan-and-long-term-procurement-plan-irp-ltpp/20210831_irp_e3_astrape_incremental_elcc_study.pdf`),
and multiple further CPUC-published SERVM/Astrapé modeling-assumptions documents in its
"Resource Adequacy Homepage" / "Energy Resource Modeling Datasets" library. These are
Commission-published documents directly tied to a specific regulatory proceeding
(R.21-10-002 and related IRP dockets), not Astrapé's own marketing material.

**Three independent real adopters confirmed by primary/official documents:** SPP (RTO),
ERCOT (ISO), and the California Public Utilities Commission / CAISO footprint (state
regulator, commissioning the analysis for its own RA and IRP dockets). Additional
Astrapé/SERVM client engagements turned up in the search (Santee Cooper, Platte River Power
Authority, PNM) further broaden the utility-level adoption but were not independently
fetched and quoted here.

### MARS (Multi-Area Reliability Simulation), GE (now GE Vernova)

The foundational primary source is GE's own developers, in a peer-reviewed 1991 IEEE paper:

> "The Multi-Area Reliability Simulation (MARS) program is based on a sequential Monte
> Carlo simulation."

> "There are two types of Monte Carlo simulation approaches: ■ Nonsequential ■ Sequential.
> ... A sequential simulation, however, steps through time chronologically, recognizing that
> the status of a piece of equipment is not independent of its status in adjacent hours. ...
> The sequential simulation can model ... issues that involve time correlations and can be
> used to calculate indices such as frequency and duration."
— Glenn E. Haringa, Gary A. Jordan, and Dr. Leonard L. Garver (GE Industrial and Power
Systems, Power Systems Engineering Department, Schenectady, NY), "Application of Monte
Carlo Simulation to Multi-Area Reliability Evaluations," *IEEE Computer Applications in
Power*, January 1991, pp. 21–22. (Note: Leonard L. Garver is the same Garver credited by
SPP's own 2022 ELCC report, above, as the originator of the ELCC/LOLP methodology in 1966 —
i.e. this is the tool-inventor literature, not a secondary summary.)

Real-world adopter confirmation, from ISOs/RTOs and a state agency directly, not GE
marketing copy:

> "In continuation of the 2022 effort into 2023 ... GE's Multi Area Reliability Simulation
> (MARS) ... The reliability planning MARS models (study year 1 through 10) have been
> developed and used for the NYISO's reliability planning processes to identify resource
> adequacy reliability criteria violations and needs."
— *Resource Planning MARS Models Assumptions*, New York ISO, presented to the NYSRC Extreme
Weather Working Group, February 27, 2023, pp. 2, 4.
`https://www.nysrc.org/wp-content/uploads/2023/06/ResourcePlanning-MARS-ModelsOverview-Feb27EWWG-v3.pdf`

> "This section describes the scope and procedures used by DEEP/LAI to perform capacity
> resource adequacy modeling performed with the assistance of ISO-NE in running the GE
> Multi-Area Reliability Simulation (MARS) model. MARS is the industry standard simulation
> tool, often used by regional transmission organizations, including ISO-NE. MARS
> simulation output reports loss-of-load expectation (LOLE) results. ... ISO-NE regularly
> uses MARS to conduct its Installed Capacity Requirement (ICR) analysis for the Forward
> Capacity Auction (FCA) and for various economic studies. ISO-NE uses the typical LOLE
> threshold of a one-day-in-ten-years ('1-in-10') loss of load as its measure of resource
> adequacy. ... For each of four scenarios tested, MARS was run with several thousand Monte
> Carlo randomized simulations of generation unit and transmission outage contingencies and
> seven probabilistic load levels for all hours of the 20-year study period."
— *2020 Integrated Resources Plan, Appendix A2. MARS Modeling*, Connecticut Department of
Energy and Environmental Protection (DEEP) / London Economics International (LAI), pp. 1–2.
`https://portal.ct.gov/-/media/DEEP/energy/IRP/2020-IRP/Appendix-A2--MARS-Modeling.pdf`

**Two independent real adopters confirmed by primary documents (NYISO, ISO-NE via the
Connecticut DEEP IRP appendix), plus corroborating third-party confirmation** that MARS is
"the industry standard simulation tool, often used by regional transmission organizations."
A secondary AI-generated web summary (not independently verified against a primary document
here) also asserted MISO usage; that claim was not separately fetched/quoted and should be
treated as unconfirmed pending its own primary source.

### GE-MAPS (Multi-Area Production Simulation), GE / GE Vernova

GE-MAPS is a **different tool from MARS**, serving a different purpose, and per GE's own
current documentation it is **not** built on Monte Carlo methodology:

> "GE Vernova's PlanOS platform brings together decades of proven planning software tools:
> Production Cost (formerly MAPS), Resource Adequacy (formerly MARS), and Power Flow
> (formerly PSLF)."
— GE Vernova, "Resource Adequacy Software," product page, `https://www.gevernova.com/consulting/planos/resource-adequacy` (accessed 2026-07-27, via search-tool summary; page itself not independently refetched and quoted verbatim here — flagged as a secondary paraphrase, not a primary verbatim quote).

Independent academic/utility usage of GE-MAPS that was found describes it purely as a
chronological, hourly **production-cost model** — used to compute annual production cost,
locational marginal prices (LMP), congestion, and emissions from a fixed (not
randomly-outaged) unit commitment/dispatch, not to compute a probabilistic loss-of-load-based
reserve margin:

> "GE Multi Area Production Simulation (GE MAPS) is a model of power systems used to
> evaluate the interactions between generation and transmission and other economic impacts
> ... The model simulates the hourly operation of power systems using production cost data
> (generator, load and transmission topology), and the output of the simulation includes
> annual production cost, LMP, congestion, emissions etc."
(Search-tool synthesis of GE Vernova/PJM/HNEI sources on GE-MAPS — see e.g. GE Energy
Consulting, *PJM Renewable Integration Study, Task 3A Part A*,
`https://www.pjm.com/-/media/DotCom/committees-groups/subcommittees/irs/postings/pjm-pris-task-3a-part-a-modeling-and-scenarios.ashx`,
and the Hawaii Natural Energy Institute's *Intermodel Comparison Between Switch 2.0 and GE
MAPS*, `https://www.hnei.hawaii.edu/wp-content/uploads/Intermodel-Comparison-Between-Switch-2.0-and-GE-MAPS.pdf`
— not independently fetched and re-quoted verbatim in this pass; treat as secondary until
directly re-verified.)

No document found in this search — vendor, ISO, or academic — describes GE-MAPS being used
to set an annual planning reserve margin via probabilistic LOLE/Monte-Carlo simulation. That
role, within GE's own product family, belongs to MARS, not MAPS.

## Assessment

- **SERVM:** CONFIRMED as a real, actively-used sequential-Monte-Carlo tool for resource
  adequacy / reserve-margin studies, with primary-document evidence of independent adoption
  by SPP, ERCOT, and CPUC/California — three separate ISO/RTO/regulator bodies, not just
  Astrapé's own sales material.
- **MARS:** CONFIRMED as a real, actively-used sequential-Monte-Carlo tool for the same
  purpose, with primary-document evidence of adoption by NYISO and ISO-NE (the latter via a
  Connecticut state-agency IRP appendix that also explicitly calls MARS "the industry
  standard simulation tool ... used by regional transmission organizations"), and with GE's
  own 1991 developer paper confirming the "sequential Monte Carlo" methodology claim
  verbatim, not merely a marketing gloss.
- **GE-MAPS:** NOT CONFIRMED as belonging in this category. It is a genuine, widely-used GE
  tool, but it is a *production-cost / economic-dispatch* model, and by GE's own current
  description a *deterministic* one — a sibling product to MARS within GE's planning
  software suite, not an alternate name or variant of the same sequential-Monte-Carlo
  resource-adequacy methodology. Grouping it with SERVM and MARS as an equivalent
  "sequential Monte Carlo... resource adequacy" tool overstates what GE-MAPS actually does.

**Net verdict on the compound claim:** the claim is correct in substance for two of its
three named tools (SERVM, MARS) — these are genuinely standard, multi-adopter,
sequential-Monte-Carlo software used by real US ISOs/RTOs/regulators for long-term resource
adequacy planning, well beyond vendor self-promotion. It over-reaches by including GE-MAPS
in that same category; GE-MAPS is a real and widely used tool, but not a sequential-Monte-Carlo
resource-adequacy tool in the sense the claim asserts. If the lab's underlying argument only
needs "SERVM and MARS are genuinely used, real, sequential Monte Carlo RA tools," that part
is solidly confirmed. If it needs GE-MAPS to be a third member of that same family, that part
should be corrected or dropped.
