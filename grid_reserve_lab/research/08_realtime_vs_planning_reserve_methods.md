# Research note: does long-term resource-adequacy planning use sequential Monte Carlo while real-time/day-ahead operating-reserve sizing uses deterministic heuristics because Monte Carlo is too slow for a 5-15 minute solve window?

**Claim being tested:** "US grid operators (ISOs/RTOs) use sophisticated sequential Monte
Carlo simulation (e.g. SERVM/MARS/GE-MAPS) for LONG-TERM resource adequacy planning (annual
reserve margins, years in advance), but for REAL-TIME or day-ahead operating-reserve sizing,
they instead rely on deterministic heuristics (N-1 largest-single-contingency rules, fixed
percentage margins) or simpler dynamic rules — specifically because real-time
dispatch/market-clearing software must solve within a strict 5-to-15-minute execution
window, which is too short for a full Monte Carlo simulation."

**Verdict: MIXED / PARTIALLY VERIFIED.** The long-term-planning half of the claim is
solidly confirmed. The real-time half is confirmed for PJM and MISO's actual reserve
*requirement quantities* (N-1 largest-single-contingency rules, a genuinely deterministic
heuristic) but is **contradicted in an important, specific way by ERCOT**, whose real-time
scarcity-pricing mechanism — the Operating Reserve Demand Curve (ORDC) — is explicitly
probabilistic, recalculated every 5-minute SCED interval, and built directly from a
loss-of-load-probability (LOLP) calculation. However, ORDC is **not** itself a live Monte
Carlo simulation run inside the 5-minute window — it is a fast, pre-computed
analytical/statistical LOLP curve, refreshed only 24 times a year, not simulated fresh each
dispatch cycle. So the claim's underlying causal mechanism (full sequential Monte Carlo is
too slow for a ~5-minute real-time solve) is well supported by a primary academic source,
but the claim's binary framing ("real-time = deterministic heuristics only") is an
oversimplification: at least one major ISO runs a genuinely probabilistic, dynamic,
real-time reserve/pricing construct that is neither a fixed N-1 rule nor a full Monte Carlo
simulation — a third category the claim's dichotomy omits. The "5-to-15-minute" figure is
also only half-sourced: 5 minutes (the SCED execution interval) is extremely well
documented across ISOs; "15 minutes" was not found as a distinct, separately-sourced figure
in this pass.

---

## Part 1: long-term resource-adequacy planning uses sequential Monte Carlo — CONFIRMED

### Source 1: GE Vernova, "Resource Adequacy Software" (PlanOS / formerly MARS)

- URL: https://www.gevernova.com/consulting/planos/resource-adequacy
- Accessed: 2026-07-27.

Per WebFetch synthesis of the page: GE Vernova's Resource Adequacy software (formerly MARS)
"performs a chronological simulation of the system—comparing the hourly load demand in each
area to the total available generation in the area—adjusted to account for planned
maintenance and randomly occurring forced outages," and "uses Full Sequential Monte Carlo,
which simulates thousands of future scenarios to assess the risk of power shortfalls and
grid reliability." The Multi-Area Reliability Simulation (MARS) program was originally
developed by General Electric and "is based on a sequential Monte Carlo simulation
technique." Key output metrics cited: Loss of Load Expectation (LOLE) and Expected Energy
Not Supplied (EENS), used to support Reserve Capacity Obligation levels (e.g. cited example
of 15% for thermal-dominated systems, 10% for hydro-dominated systems).
(Note: this is a WebFetch AI-summarized paraphrase of the vendor page, not a hand-verified
verbatim excerpt — treat as a strong secondary source rather than a primary-document
verbatim quote, but the "sequential Monte Carlo" / "thousands of scenarios" / LOLE framing
is consistent with the independently-known technical literature on MARS.)

### Source 2: PowerGEM, "SERVM — Resource Adequacy Planning Software"

- URL: https://power-gem.co/software/servm-resource-adequacy-planning/
- Accessed: 2026-07-27.

Per WebFetch synthesis: SERVM is described as software for "Scenario modeling for resource
adequacy analysis and capacity expansion planning that simultaneously optimizes reliability
and economics," designed to "produce an economically optimal expansion plan that addresses
all reliability and environmental requirements," and to "Simulate thousands of scenarios"
covering "extreme weather, resource performance, and market constraints." This matches the
independent WebSearch-synthesized description found separately: "SERVM's proprietary
algorithms rapidly simulate thousands of scenarios in the time it typically takes other
tools to simulate just one." The page text did not itself use the words "Monte Carlo,"
though the "thousands of scenarios" framing is the standard vendor description of SERVM's
known Monte Carlo/scenario engine.

**Assessment of Part 1:** the claim that SERVM/MARS(GE-MAPS successor)/similar tools use
sequential Monte Carlo simulation for long-term, years-ahead resource-adequacy and reserve-
margin planning is well supported — this is the well-known, largely undisputed technical
identity of these specific named tools, and is corroborated by this lab's own prior note
(`01_nerc_lole_reserve_standard.md`, not re-read in this pass) on LOLE-based reserve
standards.

---

## Part 2: real-time/day-ahead reserve sizing — deterministic rules confirmed for PJM/MISO, but NOT universal

### Source 3: PJM (via WebSearch synthesis of PJM Manual 11/12/13 material; PDF text could
not be extracted verbatim by WebFetch in this session — the underlying PDFs returned only
raw compressed-stream binary to the fetch tool, so what follows is a search-engine synthesis
of PJM manual content, not an independently hand-verified verbatim quote)

- URLs referenced: https://www.pjm.com/-/media/DotCom/documents/manuals/m12.pdf (Manual 12:
  Balancing Operations); PJM Manual 11 (Energy & Ancillary Services Market Operations)
  revisions 118/119/130, e.g.
  https://www.pjm.com/-/media/DotCom/committees-groups/task-forces/rcstf/2024/20240612/20240612-item-04a---pjm-manual-11---reserve-requirements-updates---june-2024.pdf
- Accessed: 2026-07-27.

Reported content (WebSearch synthesis, flagged as secondary/paraphrase, not verbatim):
"Spinning and non-spinning zonal reserve requirements are determined 100 percent and 50
percent of the largest single contingency in that zone, respectively, which ensures that the
system is able to meet N-1 criteria on the generation side." PJM "identifies its Most Severe
Single Contingency by surveying the greatest MW loss due to a single contingency" and
"schedules reserves on a day-ahead basis and operates in real-time to ensure
Contingency/Primary (10 minute) Synchronized/Spinning and Secondary/Operating reserve
requirements are maintained."

This is a textbook deterministic N-1/largest-single-contingency rule, exactly as the claim
describes, applied by PJM in both its day-ahead scheduling and real-time reserve
maintenance.

### Source 4: MISO Most Severe Single Contingency (MSSC) — WebSearch synthesis

- Accessed: 2026-07-27.
- Reported: MISO's Most Severe Single Contingency is cited at 1,500 MW, described as "the
  largest single contingency that the system must be prepared to handle," and characterized
  as following "a comparable approach to MISO" relative to PJM's N-1-based zonal reserve
  rule. The synthesis also notes: "the North American Electric Reliability Corporation
  (NERC) requires power systems to withstand the loss of a single bulk electric element
  (N-1), which is the foundational reliability standard that underpins MISO's operating
  reserve methodology based on the largest single contingency."

**Assessment so far:** PJM and MISO real-time/day-ahead reserve *quantity* requirements are
confirmed, via search-engine synthesis of primary manual content (not independently
verbatim-verified from the PDFs themselves in this pass), to be deterministic N-1/largest-
single-contingency rules — matching the claim closely for these two RTOs.

### Source 5 (the important complication): ERCOT's Operating Reserve Demand Curve (ORDC) —
a real-time, probabilistic, dynamically-updating mechanism

- URLs: https://www.ercot.com/files/docs/2024/10/31/2024-biennial-ercot-report-on-the-ordc-20241031.pdf
  (ERCOT primary source — WebFetch could not reliably extract this PDF's text in this
  session, so the description below draws on WebSearch synthesis of this and related
  documents, corroborated across multiple independent search results; treat as secondary
  synthesis of primary content, not a hand-verified verbatim quote); also
  https://www.sciencedirect.com/science/article/abs/pii/S0301421520307680 ("Operating
  reserve demand curve, scarcity pricing and intermittent generation: Lessons from the Texas
  ERCOT experience") — abstract page returned HTTP 403, so this too is WebSearch-synthesized,
  not independently fetched.
- Accessed: 2026-07-27.

Reported findings (WebSearch synthesis of ERCOT's own ORDC report and academic commentary,
consistent across multiple independent search results, so treated as reasonably reliable
even though not hand-verified verbatim from the primary PDF):

- "For each execution of the Security Constrained Economic Dispatch (SCED), the ORDC is
  constructed as probability of reserves falling below the minimum contingency level
  (PBMCL) multiplied by the difference between Value of Lost Load (VOLL) and System Lambda."
- "there is a probability, referred to as the Loss of Load Probability (LOLP), that
  operating reserves will fall to the level that would require involuntary load
  curtailment" — computed from "net load forecast error and other factors" over "the
  near-term operational timeframe of the next 30 minutes to one hour."
- "ERCOT produces six curves a day, four seasons a year for a total of 24 different loss
  of load probability distributions. This dynamic approach accounts for variations in
  reserve uncertainty throughout the day and year."
- The ORDC feeds directly into real-time prices via a scarcity "price adder" — the
  Real-Time On-Line Reserve Price Adder (RTORPA) — added to the Locational Marginal Price.
- Academic critique (Wakeland, SSRN; and independent commentary) notes ERCOT's LOLP
  calculation "incorrectly applies the hour-ahead forecasted reserve level error
  distribution to the real-time reserve level," i.e. the methodology is contested/imperfect,
  but this critique is itself evidence that ORDC's mechanism *is* probabilistic (the
  critique is about probabilistic methodology being applied incorrectly, not about ORDC
  being deterministic).

**Why this matters for the claim:** ORDC is executed every SCED interval — i.e. every 5
minutes, in real time — and it is fundamentally a loss-of-load-probability calculation, not
a fixed percentage margin or a static N-1 rule. This directly contradicts a reading of the
claim that says ALL US ISOs rely on deterministic heuristics in real time. ERCOT is the
clear counterexample: its central real-time reserve/scarcity mechanism is dynamic and
probabilistic by design, explicitly because ERCOT (an energy-only market with no separate
capacity market) needed a way to price scarcity continuously rather than via a fixed
administrative reserve margin.

**However — the important nuance that reconciles this with the claim's causal logic:**
ORDC is NOT a live sequential Monte Carlo simulation running inside the 5-minute SCED
window. It is a **pre-computed, closed-form statistical curve** (a parameterized LOLP
distribution recalculated only 24 times per year — 6 times a day across 4 seasons — not
simulated fresh at each dispatch interval). The heavy probabilistic computation (fitting the
forecast-error distributions) happens offline/periodically; what runs inside each 5-minute
SCED cycle is just an evaluation of an already-fitted curve. This is fully consistent with
—and arguably supports — the claim's underlying reasoning that genuine per-interval Monte
Carlo simulation is too computationally expensive for a 5-minute real-time solve, while
showing that ISOs have found a middle path (a fast, dynamic, probabilistic — but not
Monte-Carlo — real-time construct) that the claim's simple binary framing omits.

---

## Part 3: is "5-to-15 minutes" a real, sourced execution-window figure?

### Source 6: multiple corroborating sources on the 5-minute SCED interval

- WebSearch synthesis (multiple independent hits) states plainly: "In the U.S.,
  Independent System Operators (ISOs) solve a security-constrained economic dispatch (SCED)
  every five minutes to clear real-time electricity markets, co-optimizing energy dispatch
  and reserve to minimize costs while meeting physical and reliability constraints," and
  specifically that "TSOs like MISO and PJM execute a SCED every five minutes" and "ERCOT
  executes SCED every five minutes in its nodal market."

### Source 7 (strongest, most directly on-point primary-adjacent source): arXiv preprint,
"On the Viability of Stochastic Economic Dispatch for Real-Time Energy Market Clearing"

- URL: https://arxiv.org/abs/2308.06386
- Accessed: 2026-07-27 (WebFetch summary of the paper's own text).

Verbatim-as-returned quotes: the paper states ISOs "solve a security-constrained economic
dispatch (SCED) every five minutes to clear real-time electricity markets," and identifies
the reason stochastic/probabilistic real-time dispatch has historically been avoided as
"high computational costs and, to a lesser extent, the availability of probabilistic
forecasts." The paper's own contribution is a method whose "instances [are] being solved in
under 5 minutes" on industry-sized grids — i.e. the paper exists specifically to demonstrate
that stochastic (probabilistic, Monte-Carlo-adjacent) real-time dispatch is *now* becoming
computationally viable within the 5-minute window, implying it historically was not.

**Assessment:** the "5 minute" figure is very well documented and is the correct, specific,
sourced number — it is the SCED execution interval used by MISO, PJM, and ERCOT alike. The
"15 minute" half of "5-to-15 minutes" was **not** found as a distinct, separately-sourced
figure in this research pass; it may loosely reflect real-time market intervals or
regulation/AGC cycles at other ISOs, or simply be a rounding/hedging addition in the claim
rather than a documented figure. This part of the claim should be treated as **not
independently confirmed** — the 5-minute figure is solid, the "or up to 15" is unsourced in
what was found.

---

## Overall verdict

**MIXED / PARTIALLY VERIFIED.**

1. Long-term resource adequacy planning via sequential Monte Carlo (SERVM, MARS/GE-Vernova
   PlanOS) — **CONFIRMED**, well-documented, vendor and industry-standard framing.
2. Real-time/day-ahead reserve sizing as deterministic N-1/largest-single-contingency rules
   — **CONFIRMED for PJM and MISO** specifically (search-synthesized from PJM Manual
   11/12/13 content and MISO MSSC descriptions; not independently hand-verified verbatim
   from the primary PDFs due to a PDF text-extraction limitation in this session).
3. The claim's implicit universality ("real-time = deterministic heuristics" as if this
   applies across all ISOs) — **CONTRADICTED by ERCOT's ORDC**, which is explicitly a
   real-time, dynamic, probabilistic (loss-of-load-probability-based) construct recalculated
   every 5-minute SCED cycle, not a fixed percentage or N-1 rule. This is a genuine, named,
   well-documented counterexample and should be flagged prominently if this claim is used in
   the lab's write-up.
4. The claim's proposed *causal mechanism* — that a full live sequential Monte Carlo
   simulation is too computationally expensive to run inside a real-time dispatch window —
   is well supported, including by a source (arXiv 2308.06386) that exists specifically to
   overturn this historical limitation, confirming it was real. ERCOT's own resolution of
   this tension (a pre-computed, periodically-refreshed LOLP curve rather than a live
   simulation) is consistent with, not contradictory to, this causal logic — it shows how
   ISOs get probabilistic real-time behavior without paying the full Monte Carlo
   computational cost, rather than showing that the cost concern is false.
5. The specific "5-to-15 minute" framing is only half-confirmed: 5 minutes (SCED interval)
   is solid and multiply-sourced; 15 minutes was not found as a distinct sourced figure.

**Recommendation for the lab's write-up:** state the claim more precisely as: "most US
ISOs (PJM, MISO, and historically ERCOT's non-ORDC ancillary services) size real-time/
day-ahead operating reserves via deterministic N-1/largest-contingency or fixed-quantity
rules, reserving full sequential Monte Carlo simulation for years-ahead resource-adequacy
planning — with the important exception of ERCOT's ORDC, a real-time (5-minute SCED-cycle)
probabilistic scarcity-pricing mechanism built on a periodically-refreshed loss-of-load-
probability curve rather than either a static heuristic or a live Monte Carlo simulation."
This preserves the claim's core causal logic (Monte Carlo is genuinely too slow for a
5-minute real-time solve) while correcting its overgeneralized "real-time is universally
deterministic" framing.

## Caveats on source quality in this pass

Several primary-source PDFs (PJM Manual 11, the AESO/PJM SCED overview slide deck, ERCOT's
2024 Biennial ORDC Report, and an arXiv PDF on alternative operating-reserve modeling) could
not be parsed into verbatim text by the WebFetch tool in this session — they returned only
raw/compressed binary streams. Where this happened, the note relies instead on WebSearch's
own synthesis of the same documents (cross-checked across multiple independent search
results for consistency) rather than a hand-verified verbatim quote, and this is flagged
explicitly at each such point above. This is a real evidentiary gap: a follow-up pass using
a local PDF-to-text tool (as the lab's own `02_deterministic_reserve_heuristic.md` note did
successfully via `curl` + `pdftotext`) would strengthen Part 2 and Part 3 to primary-source
verbatim-quote standard.
