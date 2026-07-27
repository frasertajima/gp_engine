# Research note: the "3% of load + 5% of wind" deterministic reserve-margin heuristic

**Claim tested:** Before probabilistic resource-adequacy methods matured, grid operators
(commonly cited: ERCOT) used a simple deterministic reserve-margin heuristic of roughly
"3% of forecast peak load plus 5% of installed wind capacity" (or a similar simple
percentage-of-capacity rule) to size operating reserves, rather than a
statistical/correlation-aware method.

**Verdict: PARTIALLY VERIFIED — the "3%+5%" ("3+5") rule itself is real and well-attested,
but NOT as an ERCOT rule. It traces through the wind-integration/stochastic-unit-commitment
academic literature as a generic "naive deterministic baseline," and every source found
attributes it to a Western-interconnection/California-type study and to a 2011 stochastic-
programming paper — never to ERCOT specifically. ERCOT's own primary protocol documents
(2004/2005 "Methodologies for Determining Ancillary Service Requirements") describe a
DIFFERENT set of deterministic rules: a fixed 2300 MW quantity for Responsive Reserve, a
"largest single in-service unit" (N-1 contingency) rule for Non-Spinning Reserve, and — most
interestingly — a statistical standard-deviation-based rule for Regulation Reserve that was
already quasi-probabilistic well before the "probabilistic era" the claim implies. The lab
plan should drop the ERCOT attribution for "3%+5%" and either (a) cite it as a generic
academic-literature baseline heuristic, not an ERCOT rule, or (b) use ERCOT's own
documented "largest contingency" / fixed-MW rules, which are the primary-sourced,
ERCOT-specific deterministic heuristics.**

## What was searched and what could/could not be fetched

- ERCOT's own historical Ancillary Service methodology filings (2004, 2005, 2023, 2024,
  2025, 2026 board recommendation documents) were located and fetched directly from
  ercot.com — these ARE primary sources, and are the strongest evidence in this note.
- The academic citation trail for "3+5" was traced by pulling PDF text directly (via
  `curl` + `pdftotext`, since WebFetch's AI summarizer could not reliably parse several of
  the underlying PDFs' compressed text streams) from: an arXiv preprint that states the
  rule with a citation, and — going one link further back — a University of Washington PhD
  dissertation (Ting Qiu, advised by Daniel Kirschen) that states the rule explicitly with
  two citations of its own.
- Two sources the citation trail ultimately points to — A. Papavasiliou, S. Oren, R.
  O'Neill, "Reserve Requirements for Wind Power Integration: A Scenario-Based Stochastic
  Programming Framework," *IEEE Trans. Power Syst.*, vol. 26, no. 4, 2011 (paywalled, IEEE
  Xplore returned HTTP 418 to direct fetch), and NREL's "Western Wind and Solar Integration
  Study" (2010) (docs.nrel.gov and www.nrel.gov both failed DNS resolution from this
  environment/sandbox) — could **not** be read directly. This is a real gap: I cannot
  independently confirm from the ultimate primary sources whether either of them frames
  "3%+5%" as an ERCOT-specific rule, a CAISO-specific rule, or a generic industry rule of
  thumb. Everything below the dissertation link is second-hand.

## Source 1 (primary, ERCOT): "2005 ERCOT Methodologies for Determining Ancillary Service
Requirements" (ROS, Oct. 6, 2005 TAC packet item) and the 2004 predecessor document

- **Publisher:** ERCOT (Reliability and Operations Subcommittee / Technical Advisory
  Committee).
- **URLs:**
  - https://www.ercot.com/files/docs/2005/09/30/tac10062005_9.doc
  - https://www.ercot.com/files/docs/2004/08/11/ros08102004_9.doc
- **Date:** 2004 and 2005 (document headers); accessed 2026-07-27.

Verbatim/quoted findings (extracted via WebFetch's document summarizer directly from the
.doc files — quotes below are as returned, since these are Word documents rather than
compressed-stream PDFs, WebFetch's parser handled them cleanly):

> "By arranging for 2.5 standard deviations times the historic average usage for each
> hours requirement; ERCOT provides the mathematical expectation that sufficient
> regulation will be available 98.8% of all periods." (Regulation Reserve, RGRS)

> "ERCOT will purchase NSRS equal to the largest unit planned to be in operation for
> periods of projected higher risk." (Non-Spinning Reserve, NSRS)

> "The ERCOT Operating Guides establish a fixed requirement of 2300 MW of Responsive
> Reserve Service (RRS)." (Responsive Reserve, RRS)

**No formula referencing a percentage of forecast load and/or a percentage of installed
wind capacity appears in either document.** ERCOT's own stated ancillary-service sizing
rules circa 2004–2005 were: (1) a statistical (2.5-sigma) rule for Regulation — already a
probabilistic-flavored heuristic, not a flat percentage; (2) a classic "largest single
contingency" (N-1) rule for Non-Spin; (3) a flat fixed-MW quantity (2300 MW) for
Responsive Reserve, with no load or wind term at all.

This directly weighs against the claim's specific "ERCOT used 3%+5%" framing: ERCOT's own
primary protocol language from the era in question describes different rules entirely.

## Source 2 (secondary, tracing the "3+5" rule): Ting Qiu, PhD dissertation, University of
Washington, Dept. of Electrical Engineering (advisor: Daniel S. Kirschen), 2018

- **Publisher:** University of Washington (REAL lab, Kirschen research group).
- **URL:** https://labs.ece.uw.edu/real/Library/Thesis/Qiu.pdf
- **Date:** 2018 (per document, "© Copyright 2018 Ting Qiu"); accessed 2026-07-27.
  Fetched as raw PDF via `curl` and converted with `pdftotext` (WebFetch's PDF summarizer
  could not reliably parse this file's compressed streams; the local extraction below is
  verbatim from the plain-text conversion).

Verbatim quotes:

> "RESERVE REQUIREMENT
> Most planning models do not consider the need to provide operating reserve. As the
> proportion of stochastic renewable generation increases, this simplification becomes
> untenable. The proposed model considers the reserve constraint in the unit commitment
> and uses the 3+5 rule to specify the amount of operating reserve, which means that the
> reserve required is equal to 3% of the forecast load prediction plus 5% of the forecast
> wind generation [2, 83]."

> "Equation (3.19) defines the 3+5 reserve requirement [2, 83], i.e. the total reserve
> should be no less than 3% of the forecasted load plus 5% of the forecasted wind power."
> (repeated near-verbatim at a second point in the dissertation, describing the same rule
> in a later chapter's model)

Bibliography entries for citations [2] and [83]:

> "[2] A. Papavasiliou, S. Oren and R. O'Neill, 'Reserve Requirements for Wind Power
> Integration: A Scenario-Based Stochastic Programming Framework', IEEE Trans. Power
> Syst., vol. 26, no. 4, pp. 2197-2206, 2011."

> "[83] Western wind and solar integration study. National Renewable Energy Laboratory,
> 2010."

This confirms the "3%+5%" rule is a real, named heuristic ("the 3+5 rule") used
repeatedly in the stochastic-unit-commitment/reserve-sizing academic literature as the
canonical "naive deterministic" comparison baseline against which a proposed
probabilistic/stochastic method is shown to do better — structurally exactly the framing
in the claim being tested ("before probabilistic methods... a simple deterministic
heuristic... rather than a statistical/correlation-aware method"). But note what it is
NOT: neither citation is an ERCOT document. [2] is a scenario-based stochastic programming
paper tested on a model of the California system (per its own abstract, corroborated
independently via WebSearch — see Source 3 below); [83] is NREL's Western Wind and Solar
Integration Study, a WECC/western-interconnection-wide study, not an ERCOT-specific one.

## Source 3 (secondary, corroborating): downstream citation of the same rule in a 2024
arXiv preprint

- **Publisher:** arXiv preprint (IEEE-submission-track paper on hybrid AC/DC transmission
  expansion planning).
- **Title:** "Hybrid AC/DC Transmission Expansion Planning Considering HVAC to HVDC
  Conversion Under Renewable Penetration."
- **URL:** https://arxiv.org/pdf/2310.05828
- **Date:** 2023; accessed 2026-07-27 (fetched raw PDF via `curl` + `pdftotext`; WebFetch's
  PDF summarizer again could not parse the compressed streams reliably).

Verbatim quote:

> "the total reserve is assumed to be greater than the summation of 5% and 3% of the
> forecasted wind and load, respectively [13]. The integration of renewable resources
> needs a new kind of spinning reserve named by flexible ramp reserve to handle the
> uncertainty of renewable resources... a minimum of 5% of the forecasted wind generation
> is required to be assigned as flexible ramp reserve."

Its citation [13]:

> "[13] T. Qiu, B. Xu, Y. Wang, Y. Dvorkin, and D. S. Kirschen, 'Stochastic multi-stage
> coplanning of transmission expansion and energy storage,' IEEE Trans. Power Syst., vol.
> 32, no. 1, pp. 643-651, 2016."

This is the peer-reviewed journal version of the same rule from the same UW/Kirschen
research group whose dissertation (Source 2) is the more detailed exposition — i.e. this
is not an independent re-derivation, it is the same lineage propagating forward through
later papers that treat "3+5" as an established, citable convention rather than deriving
it fresh. It corroborates that the rule is a recognized fixture in this literature, but it
does not add a new, independent source for ERCOT attribution.

## Source 4 (secondary, on Papavasiliou/Oren/O'Neill's own framing): WebSearch-summarized
abstract/description

Direct PDF fetch of the Papavasiliou/Oren/O'Neill 2011 paper failed (IEEE Xplore returned
HTTP 418 to WebFetch; no accessible preprint mirror was found). A WebSearch summary of
secondary descriptions of the paper stated:

> "The authors tested their scenario generation methodology on a model of California
> consisting of 122 generators, and showed that the stochastic programming unit
> commitment policy outperforms common reserve rules... the proposed model is shown to
> outperform deterministic reserve schedules based on a certain percentage of forecast
> peak load and wind power generation."

This is a WebSearch-engine-generated paraphrase, not a verbatim quote from the paper
itself — treat it as weak, tertiary evidence. But it is consistent with everything else
found: the paper's own test system was California-based, not ERCOT, and its deterministic
comparison baseline is described in exactly the same "percentage of load + percentage of
wind" functional form as the "3+5 rule," suggesting this may be the rule's point of origin
into the academic literature (with NREL's WWSIS 2010 report as the likely applied-industry
source it drew the specific 3%/5% numbers from) — but this could not be confirmed by
reading either document directly.

## What ERCOT-related "largest contingency" and margin-percentage heuristics ARE well
documented (per item 3 of the task)

Two more general deterministic heuristics turned up repeatedly and ARE clearly documented,
including in ERCOT's own primary filings pulled for this note:

1. **"Largest single contingency" reserve sizing** — ERCOT's own Non-Spinning Reserve rule
   (Source 1 above: "ERCOT will purchase NSRS equal to the largest unit planned to be in
   operation") is a textbook instance of the classic N-1/largest-contingency deterministic
   heuristic used across NERC-region grid operators historically, predating and
   coexisting with probabilistic ancillary-service sizing. ERCOT's more recent methodology
   documents (e.g. "PUBLIC Item 15: Recommendation regarding 2026 ERCOT Methodologies for
   Determining Minimum Ancillary Service Requirements," ercot.com, Sept. 2025 — located but
   its PDF text could not be reliably extracted through either WebFetch or local
   `pdftotext`, so no verbatim quote is given here) describe ERCOT's ongoing shift of ECRS
   and Non-Spin sizing toward probabilistic modeling of forced-outage and net-load-forecast
   error distributions, which is the "probabilistic era" side of the claim's contrast and is
   corroborated by WebSearch summaries of that same document (see log; not independently
   quote-verified).
2. **NERC Reference Margin Level / generic Planning Reserve Margin percentage** — a
   distinct, longer-run resource-adequacy concept (not an operating-reserve/ancillary-
   service concept) — e.g. ERCOT's current board-approved minimum target reserve margin of
   13.75% of peak demand (per WebSearch of ercot.com resource-adequacy materials, not
   independently verbatim-quoted here). This is the generic "reserve margin target of
   roughly 12–15%" heuristic flagged in the task's item 3, and it long predates and
   continues to run alongside probabilistic LOLE-based adequacy assessment (see this lab's
   `01_nerc_lole_reserve_standard.md`).

## Verdict and recommendation

**The specific "ERCOT used a 3% load + 5% wind rule" claim is NOT CONFIRMED as an ERCOT
rule.** ERCOT's own primary ancillary-service methodology documents from the relevant era
describe different deterministic rules (fixed 2300 MW Responsive Reserve; largest-unit
N-1 rule for Non-Spin; a statistical 2.5-sigma rule for Regulation). The "3%+5%"
("3+5 rule") formulation IS real and well-attested — it appears verbatim, named as such,
in a University of Washington PhD dissertation and its published journal version, both
citing a 2011 IEEE stochastic-programming paper (tested on a California system model, not
ERCOT) and NREL's 2010 Western Wind and Solar Integration Study (a WECC-wide study, not
ERCOT-specific) as its sources. It functions in this literature exactly as the claim
describes functionally — a simple deterministic baseline that probabilistic/stochastic
reserve-sizing methods are shown to beat — but the ERCOT attribution appears to be an
unsupported (or at least unconfirmed) embellishment somewhere in the claim's own transmission,
not something found in any source consulted here.

**Recommendation for the lab plan:** drop the ERCOT attribution for the specific "3%+5%"
numbers. Two defensible alternatives, both supportable by what was found:
- Cite "3+5" as a generic literature-baseline deterministic heuristic (Qiu 2018 UW
  dissertation / Qiu et al. 2016 IEEE TPS; ultimately traced to Papavasiliou, Oren &
  O'Neill 2011 and NREL's 2010 WWSIS), used as the standard "naive" comparison point in
  stochastic-reserve papers — without naming ERCOT as its source.
- Or use ERCOT's own actual, primary-sourced historical deterministic heuristics instead:
  the fixed-MW Responsive Reserve rule and the largest-single-contingency Non-Spin rule
  quoted in Source 1 above — these ARE ERCOT-specific and ARE primary-sourced, and match
  the task's alternative framing ("largest single contingency plus X%").

Either framing is more defensible than asserting ERCOT specifically ran "3% load + 5%
wind" — that combination was not found attributed to ERCOT anywhere in this search.
