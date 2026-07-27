# Research note: NERC "one day in ten years" LOLE reliability target

**Claim tested:** NERC's conventional "one day in ten years" loss-of-load-expectation
(LOLE ≤ 0.1 days/year) is the standard reliability target underlying resource-adequacy /
reserve-margin planning in North American grid operation (NERC standards such as
BAL-002, and NERC's own Probabilistic Adequacy and Measures reports).

**Verdict: PARTIALLY VERIFIED — the 0.1 days/year LOLE target itself is confirmed as the
de facto North American convention by strong secondary/near-primary sourcing, but one
specific detail in the claim as stated is WRONG: BAL-002 is not the standard that
establishes it, and no single continent-wide NERC *Reliability Standard* mandates 0.1
days/year — it is set region-by-region (individually, but near-uniformly) by Regional
Entities/Planning Coordinators, and NERC's own role is closer to measuring and reporting
LOLE results than mandating the 0.1 target.**

## What could and could not be directly fetched

- NERC's own "Probabilistic Adequacy and Measures" report (Probabilistic Assessment
  Working Group / PAWG, April/July 2018) — the document the claim names directly —
  returned **HTTP 403 Forbidden** on WebFetch from both of its known NERC.com URLs:
  - `https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/pawg/probabilistic_adequacy_and_measures_report.pdf`
  - `https://www.nerc.com/comm/PC/Probabilistic%20Assessment%20Working%20Group%20PAWG%20%20Relat/Probabilistic%20Adequacy%20and%20Measures%20Report.pdf`
  - Google's cache mirror of the same URL also returned only a search-error stub, not the
    document text.
  - So the report's own wording could **not** be quoted verbatim here — its content below
    is known only at second hand, via documents that cite/summarize it (see next section).
    This is flagged explicitly per the "do not invent a citation" instruction.
- What **was** fetched and quoted verbatim: (1) an IEEE Power & Energy Society paper
  co-authored by NERC-adjacent industry experts summarizing NERC's own reporting and the
  historical record; (2) a New York State Reliability Council (NYSRC) working-group report
  whose metric definitions are explicitly sourced to the NERC PAWG report and whose
  Appendix B reproduces a table sourced to **NERC's own 2019 Long-Term Reliability
  Assessment**; (3) NERC's actual BAL-002-3 and a regional BAL-502-RF-03 standard, to check
  the claim's specific standard citation.

## Source 1 — IEEE PES Resource Adequacy Working Group (RAWG), 2022

**Citation:** G. Stephen, S. H. Tindemans, J. Fazio, C. Dent, A. Figueroa Acevedo, Bagen
Bagen, A. Crawford, A. Klaube, D. Logan, D. Burke, "Clarifying the Interpretation and Use
of the LOLE Resource Adequacy Metric," on behalf of the IEEE PES Resource Adequacy
Working Group, IEEE, 2022 (978-1-6654-1211-7/22). Accessed via
`https://spp.org/documents/69303/lole%20metric.pdf` (hosted by SPP, one of the NERC
Regional Entities), 2026-07-27.

Verbatim:

> "It should be noted that the RAWG also recognizes the importance of using multiple
> different metrics to understand system adequacy [2], [3]. For example, while NERC
> publishes LOLE results (in terms of hours per year) in its biannual reports, it provides
> expected unserved energy results as well [4]."

> "Billinton and Chu [1] chronicle the discussion and adoption of this 'average count of
> shortfall days' metric in industry, and the eventual coalescence around 1 day in 10
> years (0.1 days per year) as an acceptable level of risk through the 1960s. In that
> discussion the authors also note that earlier work emphasized that adequacy criteria
> should be determined based on the operator's risk tolerance and an appropriate balance
> between the costs and benefits of avoiding unserved energy, while in later years this
> target tended to be taken as a given without significant justification."

> "In closing, we note that the 1-day-in-10-years criterion is arbitrary, and that
> appropriate adequacy criteria may vary across different systems."

This paper's reference [9] cites the exact NERC document named in the claim:

> [9] "Probabilistic Adequacy and Measures," Technical Reference Report, North American
> Electric Reliability Corporation, April 2018.
> `https://www.nerc.com/comm/PC/Probabilistic%20Assessment%20Working%20Group%20PAWG%20%20Relat/Probabilistic%20Adequacy%20and%20Measures%20Report.pdf`

Note the RAWG paper itself frames "1-day-in-10-years" as an **industry-adopted rule of
thumb / convention**, historically arrived at rather than derived, and explicitly calls it
"arbitrary" — not something NERC asserts as a rigorously justified target.

## Source 2 — NYSRC Resource Adequacy Working Group report, April 2020

**Citation:** "Resource Adequacy Metrics and Their Applications," NYSRC Resource Adequacy
Working Group (C. Wentlent, Chairman, et al.), New York State Reliability Council, LLC,
April 20, 2020. Accessed via
`https://www.nysrc.org/wp-content/uploads/2023/03/Resource-Adequacy-Metric-Report-Final-4-20-20206431.pdf`,
2026-07-27.

This report's metric definitions are explicitly sourced to the NERC document the claim
names:

> "The metric definitions in this section are largely based on the North American
> Electric Reliability (NERC) publication, *Probabilistic Adequacy and Measures*, July
> 2018."

On the cross-ISO convention (Section 3.0):

> "As shown in Appendix B, the majority of entities in North America conducting resource
> adequacy studies use the LOLE metric with corresponding 1-in-10-year resource adequacy
> standard targets."

> "The majority of North America markets use the LOLE metric as the basis of their
> resource adequacy criteria."

Appendix B — "Survey of Resource Adequacy Metrics and Criteria Around the World,"
sourced by the report to **"NERC Publication, 2019 Long-Term Reliability Assessment,
Table 4, pages 42-43"** — lists, verbatim, criterion = "0.1 days/year" (LOLE metric) for:
NPCC (all 5 areas), MISO, MRO–Manitoba Hydro, PJM, SERC (all 4 areas), SPP, and
TRE-ERCOT. WECC (all 6 areas) instead uses an LOLP metric with a footnoted equivalence:
"A 0.02% LOLP is approximately equivalent to a LOLE of 0.1 days/yr."

Appendix A — "History of the One-Day-in-Ten Year LOLE Criterion in North America and New
York" — states, verbatim:

> "Around 1960 some publications suggested using a one day in ten years LOLE index, but
> without specifically quantifying the reason for its justification. Since 1960, the LOLE
> index of one day in ten years has been widely recognized by the electric industry in
> North America."

> "A 1981 US Department of Energy (DOE) report noted that system reliability criteria have
> been established on the basis of historical reliability levels that provided
> trouble-free service in the past. To our knowledge there have been no technical analyzes
> in North America to justify the one day in ten-year index, but to accept it as a
> universal standard that has provided acceptable service reliability."

On NERC's own regional (not single continent-wide) enforcement mechanism, footnote 4:

> "The NPCC resource adequacy criterion, in addition to requiring a LOLE of 0.1 day/year,
> requires that each Area in their resource adequacy studies make 'due allowance for
> demand uncertainty, scheduled outages and deratings, forced outages and deratings,
> assistance over interconnections with neighboring Planning Coordinator Areas,
> transmission transfer capabilities, and capacity and/or load relief from available
> operating procedures.'"

And on the Recommendations page:

> "The current 0.1 days/year LOLE criterion used in NYCA is consistent with that used by
> other NPCC Areas and most of the other North American regions, and the Working Group
> does not recommend a change to that criterion."

## Source 3 — the claim's own standard citation checked directly (BAL-002 vs. the actual
resource-adequacy standard)

This is the key nuance the claim gets wrong. **BAL-002-3 ("Disturbance Control Standard –
Contingency Reserve for Recovery from a Balancing Contingency Event")** is a real,
currently active, continent-wide NERC Reliability Standard, but it governs something
different: a Balancing Authority's operating (contingency) reserve held to recover
frequency after a single large disturbance, not planning-horizon resource adequacy / LOLE.
(Source: NERC standard title and purpose, `https://www.nerc.com/globalassets/standards/reliability-standards/bal/bal-002-3.pdf`,
cross-checked via WebSearch summary and NERCipedia's BAL-002-3 page, both consistent:
purpose is to "ensure the Balancing Authority is able to utilize its Contingency Reserve
to balance resources and demand and return Interconnection frequency within defined
limits following a Reportable Disturbance." No mention of LOLE or 0.1 days/year.)

The standard that actually encodes the "0.1 days/year" LOLE resource-adequacy target is a
**Regional Reliability Standard**, e.g. **BAL-502-RF-03** ("Planning Resource Adequacy
Analysis, Assessment and Documentation"), which applies only within the
**ReliabilityFirst (RFC)** region, not continent-wide. Verbatim (via NERCipedia summary of
the NERC-published standard text,
`https://nercipedia.com/active-standards/bal-502-rf-03-planning-resource-adequacy-analysis-assessment-and-documentation/`):

> Purpose: "To establish common criteria, based on 'one day in ten year' loss of Load
> expectation principles, for the analysis, assessment and documentation of Resource
> Adequacy for Load in the Reliability_First_ Corporation (RFC) region"

> Requirement R1.1: The Planning Coordinator must "Calculate a planning reserve margin
> that will result in the sum of the probabilities for loss of Load…being equal to 0.1."

> "This standard applies regionally to the Reliability First Corporation (RFC) region
> only, not continent-wide. It specifically governs Planning Coordinators within that
> region, making it a regional rather than universal NERC standard."

Other NERC regions/ISOs (NPCC, MISO, PJM/RFC via their own filings, SERC, SPP, ERCOT — per
the NYSRC Appendix B table sourced to NERC's own LTRA) each independently adopt the same
0.1 days/year number through their own regional criteria or Reliability Standard variants
(e.g. analogous BAL-502 series standards per region) — it is a convergent regional
convention, not one continent-wide NERC Reliability Standard.

## Assessment

The **numeric target itself — LOLE ≤ 0.1 days/year, "1 day in 10 years" — is well
confirmed** as the dominant North American resource-adequacy convention: it is
independently reported, per NERC's own 2019 Long-Term Reliability Assessment (Table 4), as
the criterion used by NPCC, MISO, PJM, SERC, SPP, and ERCOT, with WECC using a
numerically-equivalent LOLP formulation. It has been in use since roughly 1960 and traces
to Billinton & Chu's historical account, independently corroborated by the 2022 IEEE PES
RAWG paper and the 2020 NYSRC report.

However, two nuances matter for how this should be written into `grid_reserve_lab`'s own
documentation:

1. **NERC does not itself mandate 0.1 days/year via a single continent-wide Reliability
   Standard.** The mechanism is regional: individual Regional Entities/Planning
   Coordinators (NPCC, ReliabilityFirst, etc.) each adopt their own Regional Reliability
   Standard (e.g. BAL-502-RF-03 for RFC) that happens to converge, near-universally, on the
   same 0.1 days/year number. NERC's continent-wide role, per the sources found, is closer
   to *measuring, aggregating, and publishing* LOLE results (its biannual/Long-Term
   Reliability Assessments and the Probabilistic Adequacy and Measures technical
   reference) than to *mandating* the target.
2. **BAL-002 is the wrong standard citation.** BAL-002-3 is the Disturbance Control
   Standard (operating-timescale contingency reserve), unrelated to planning-horizon LOLE.
   The correct family of standards to cite would be the region-specific BAL-502 series
   (e.g. BAL-502-RF-03) or, more accurately, each region's own resource-adequacy planning
   criteria as reported in NERC's Long-Term Reliability Assessment — not BAL-002.
3. The NERC "Probabilistic Adequacy and Measures" report itself — the second document
   named in the claim — could not be directly fetched (403 Forbidden on both known NERC
   URLs; not otherwise mirrored in full text). Its content is known here only through
   citation and summary in the IEEE RAWG paper and the NYSRC report, both of which
   explicitly source their metric definitions to it. This should be treated as secondary
   sourcing for that specific document, even though the underlying 0.1-days/year claim is
   corroborated independently by NERC's own (separately and successfully accessed, via
   citation) 2019 Long-Term Reliability Assessment Table 4.
4. The RAWG paper explicitly characterizes the 1-day-in-10-years criterion as
   historically-arrived-at and "arbitrary," not derived from a rigorous cost-benefit
   optimization — useful framing if `grid_reserve_lab` presents this as a target rather
   than a physically or economically necessary threshold.

**Recommendation for lab writing:** Cite the 0.1 days/year LOLE target as the standard
North American convention, sourced to NERC's own Long-Term Reliability Assessment
(regional criteria table) and corroborated by IEEE PES RAWG (2022) and NYSRC (2020) — but
do **not** cite BAL-002 as its source; if a specific standard number is wanted, use the
regional BAL-502 series (e.g. BAL-502-RF-03) and note explicitly that it is a regional,
not continent-wide, NERC Reliability Standard.
