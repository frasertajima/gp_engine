# Research: VOLL and reserve/capacity cost figures for grid_reserve_lab

Format follows climate_cat_lab's `06_book_size_benchmarks.md`: claim, verdict, verbatim
quotes + citations, plain-language read, explicit note on what's directly sourced vs. derived.

---

## Claim 1

> "Value of Lost Load (VOLL) — the economic cost per MWh of unserved electricity during an
> outage/reliability event — is a real, published figure used by grid operators/regulators, and
> public estimates for the US (illustratively ERCOT-era figures) commonly fall in a very high
> range, plausibly $9,000-$30,000/MWh or similar order of magnitude."

**VERDICT: CONFIRMED, with the caveat that the real range is wider and more time-varying than a
single band — VOLL is a real, regulator-adopted figure, and ERCOT specifically has used numbers
that bracket and exceed the $9,000-$30,000/MWh guess at different points in time.**

### What was found — ERCOT's VOLL is a real, PUC-adopted number that has moved a lot

ERCOT's VOLL is not just an academic estimate — it is written directly into ERCOT's Operating
Reserve Demand Curve (ORDC) methodology and has historically been set equal to the System-Wide
Offer Cap (SWCAP):

> "In April 2012, the PUCT approved two proposals to raise the system wide offer cap from
> $3,000/MWh in 2011 up to $9,000/MWh beginning on June 1, 2015... The OBD, Methodology for
> Implementing Operating Reserve Demand Curve (ORDC) to Calculate Real-Time Reserve Price Adder,
> defines the VOLL to be equal to the SWCAP, so the VOLL will also transition to the LCAP value."
— summarized from ERCOT market notice archives / EIA "Today in Energy"
(https://www.eia.gov/todayinenergy/detail.php?id=22532), accessed 2026-07-27.

> "An amendment to §25.505 of the PUCT Substantive Rules lowers the HCAP from its current value
> of $9,000/MWh to a value of $5,000/MWh with an effective date of January 1, 2022."
— ERCOT market notice archive (https://www.ercot.com/services/comm/mkt_notices/archives/5275),
accessed 2026-07-27.

So the **historical (2015-2021) ERCOT VOLL/System-Wide Offer Cap was exactly $9,000/MWh** —
matching the low end of the claim precisely. It was then cut to $5,000/MWh in 2022, held there
as an interim figure, and then substantially revised upward following a dedicated 2024 VOLL study
(Brattle Group, for ERCOT/PUCT Project No. 55837):

> "The PUC's commissioners approved a VOLL of $35,000 per megawatt-hour using results from a
> survey of consumers in the ERCOT region." — TCCFUI, "PUC Adopts Reliability Standard for
> ERCOT, Orders Increase to Value of Lost Load"
> (https://tccfui.org/puc-adopts-reliability-standard-orders-increase-to-value-of-lost-load/),
> accessed 2026-07-27.

> "As recently as 2022, the VOLL was set at $5,000 per mWh, according to a 2023 IMM report."
— same source.

> By customer class (1-hour outage duration), from ERCOT's 2024 VOLL study: "about $4,000 per
> MWh for residential customers, $667,000 per MWh for small C&I customers, and $23,000 per MWh
> for medium/large C&I customers." System-wide average recommendation: "~$35,000 per MWh."
— EnergyChoiceMatters.com, "ERCOT VOLL Study Shows VOLL As $667,000/MWh for Small C&Is..."
(http://www.energychoicematters.com/stories/20240822e.html), accessed 2026-07-27. Underlying
study: Brattle Group, "Review of Value of Lost Load in the ERCOT Market," PUCT Project No. 55837
(https://www.brattle.com/wp-content/uploads/2024/09/Value-of-Lost-Load-Study-for-the-ERCOT-Region.pdf).

An interim value of $25,000/MWh was also used by the PUC pending completion of the full study
(per the same TCCFUI/EnergyChoiceMatters reporting) — which sits almost exactly at the midpoint
of the original $9,000-$30,000 guess.

### Assessment

Putting the actual timeline together for ERCOT alone:

| Period | ERCOT VOLL / SWCAP | Source |
|---|---|---|
| 2011 | $3,000/MWh | EIA / ERCOT notices |
| 2015-2021 | **$9,000/MWh** | EIA / ERCOT notices |
| 2022-2024 (interim) | $5,000/MWh, then $25,000/MWh (pending study) | TCCFUI / IMM 2023 report |
| Aug 2024-present | **$35,000/MWh** (system-wide average; residential ~$4,000, medium/large C&I ~$23,000, small C&I ~$667,000) | Brattle Group study for PUCT; PUC order Aug 29, 2024 |

The original claim's $9,000-$30,000/MWh band is a real historical range for ERCOT specifically
(it is literally the $9,000 SWCAP-era value at the low end, and close to the $25,000 interim /
$23,000 medium-large-C&I figures at the high end), but the *current* PUC-adopted system-wide
VOLL ($35,000/MWh) is now somewhat above that band, and the small-C&I class figure ($667,000/MWh)
is two orders of magnitude above it — a reminder that VOLL is extremely sensitive to customer
class and outage duration, not a single clean number. **Recommendation for the lab: cite VOLL as
"on the order of $5,000-$35,000/MWh for ERCOT system-wide averages depending on year/methodology,
with customer-class values ranging from ~$4,000/MWh (residential) to $600,000+/MWh (small
commercial/industrial)," rather than asserting a single fixed $9,000-$30,000 band as current.**

Other US utilities' VOLL/interruption-cost estimates (LBNL "Interruption Cost Estimate" (ICE)
Calculator, built on the Sullivan/Freeman Sullivan & Co. meta-analysis of 34 utility "value of
service reliability" studies covering 100,000+ customer survey responses, 1989-2015) are the
other major well-known body of US VOLL work referenced in the claim's prompt. I confirmed this
research program is real and is the standard secondary reference cited across VOLL literature,
but did not pull a specific national-average $/MWh headline number out of the LBNL PDFs directly
(the ICE Calculator computes interruption costs per utility/region/customer-class combination
rather than publishing one national figure) — this is flagged as **not directly quoted** below.

- LBNL, "Improving the Estimated Cost of Sustained Power Interruptions to Electricity Customers"
  (https://eta-publications.lbl.gov/sites/default/files/copi_26sept2018.pdf)
- LBNL, "Interruption Cost Estimate (ICE) Calculator" guidebook
  (https://eta-publications.lbl.gov/sites/default/files/interruption_cost_estimate_guidebook_final2_9july2018.pdf)
- LBNL ICE Calculator (https://icecalculator.com)

### What was NOT found

- No single national (all-US, cross-ISO) VOLL figure — VOLL is set/estimated per-ISO or
  per-utility, not nationally, so any "US average VOLL" statement should be treated as an
  ERCOT-specific or utility-specific figure unless stated otherwise.
- Did not pull an explicit $/MWh headline figure directly from the LBNL ICE Calculator study PDFs
  in this pass (would require running the calculator itself, not just reading the methodology
  PDF).

---

## Claim 2

> "The annual cost of holding/procuring operating reserve or capacity (a $/MW-year or $/kW-year
> figure) is a real, findable figure from ISO/RTO capacity markets (e.g. PJM capacity market
> clearing prices, MISO Planning Resource Auction, ERCOT ORDC-related costs) or utility resource
> plans."

**VERDICT: CONFIRMED.** Both PJM and MISO publish real, audited capacity-market clearing prices
every year, quoted in $/MW-day, which convert straightforwardly to $/MW-year. Figures below are
directly sourced from ISO press releases and market-monitor/trade-press reporting of those
releases.

### PJM Base Residual Auction (BRA) clearing prices

> "Capacity prices in the PJM Interconnection's latest capacity auction hit a $329.17/MW-day
> price cap across its region, up 22% from a year ago for most of PJM." — Utility Dive, "PJM
> capacity prices set another record with 22% jump"
> (https://www.utilitydive.com/news/pjm-interconnection-capacity-auction-prices/753798/),
> accessed 2026-07-27, reporting on PJM's 2026/2027 Base Residual Auction (held July 2025).

> Prior delivery year, 2025/2026: **$269.92/MW-day** RTO-wide (most zones), with some zones
> clearing at their zonal price caps — $466.35/MW-day for parts of Maryland (BGE zone) and
> $444.26/MW-day for parts of Virginia/North Carolina (Dominion zone). — same source, and
> PJM Inside Lines, "PJM Auction Procures 134,311 MW of Generation Resources"
> (https://insidelines.pjm.com/pjm-auction-procures-134311-mw-of-generation-resources-supply-responds-to-price-signal/),
> accessed 2026-07-27.

> For comparison, the 2024/2025 delivery year cleared at **$28.92/MW-day** in most zones — nearly
> 10x lower than the following year, "PJM Auction Procures 134,311 MW..." (RTO Insider summary),
> accessed 2026-07-27.

> Total procurement cost across PJM rose from roughly $2.2 billion in an earlier low-price
> auction to **$14.7 billion** for the 2025/2026 delivery year and **$16.1 billion** for
> 2026/2027 — Utility Dive, same article as above.

**Unit conversion:** $329.17/MW-day x 365 days = **~$120,150/MW-year** (~$120/kW-year) for the
2026/2027 PJM RTO-wide clearing price; the 2024/2025 clearing price of $28.92/MW-day annualizes
to **~$10,556/MW-year** (~$10.6/kW-year) — a roughly 10x swing in one year, driven by data-center
load growth and generator retirements per PJM/IEEFA reporting (IEEFA, "Projected data center
growth spurs PJM capacity prices by factor of 10,"
https://ieefa.org/resources/projected-data-center-growth-spurs-pjm-capacity-prices-factor-10,
accessed 2026-07-27).

### MISO Planning Resource Auction (PRA) clearing prices

> "MISO's 2025/26 capacity auction returned $666.50/MW-day prices across all zones in the
> summer." — RTO Insider, "MISO Summer Capacity Prices Shoot to $666.50 in 2025/26 Auction"
> (https://www.rtoinsider.com/104023-miso-summer-capacity-prices-2025-26-auction/), accessed
> 2026-07-27.

> "On an annualized basis, PY 25/26 prices cleared ten times higher than PY 24/25, up to
> $217/MW-day, compared to $21/MW-day for PY 24/25." — same source (MISO now clears seasonally:
> Summer, Fall, Spring, Winter — the $666.50 figure is Summer-only, and the ~$217/MW-day figure
> is the annualized blend across all four seasons for PY 2025/26).

> Fall/Spring 2025-26 pricing: "$91.60/MW-day in the North/Central subregion and $74.09/MW-day in
> the South subregion," with "Spring 2026 cleared at $69.88[/MW-day]." — same source.

> For the following delivery year: "MISO 2026/27 capacity prices decreased 42% to $126/MW-day" —
> Modo Energy, "MISO 2026/27 capacity prices decreased 42% to $126/MW-day"
> (https://modoenergy.com/research/en/miso-2026-27-capacity-prices-results), accessed 2026-07-27
> (this appears to be the annualized/blended figure, analogous to PJM's annual clearing price).

**Unit conversion:** MISO's annualized PY 2025/26 price of ~$217/MW-day x 365 = **~$79,200/MW-year**
(~$79/kW-year); PY 2024/25 at ~$21/MW-day annualizes to **~$7,665/MW-year** (~$7.7/kW-year); the
Summer-2025/26-only price of $666.50/MW-day, if it applied year-round (it doesn't — MISO prices
by season), would annualize to ~$243,300/MW-year, illustrating why season/period must be stated
explicitly when quoting MISO figures.

### ERCOT (no capacity market — reserve costs flow through ORDC scarcity pricing instead)

ERCOT is an energy-only market with no capacity auction; its analog to "reserve procurement cost"
is the Operating Reserve Demand Curve (ORDC) adder embedded in real-time energy prices, which is
directly a function of the VOLL figures documented in Claim 1 above (VOLL sets the scarcity-price
curve's ceiling/shape). I did not find a clean, separate "$/MW-year cost of ERCOT reserves"
headline figure in this pass — ORDC costs show up as an add-on to real-time energy prices system-
wide rather than a discrete capacity-market clearing price, so it is **not directly comparable in
the same units** to PJM/MISO $/MW-day figures without ERCOT-specific market-monitor modeling.
Flag this as a gap if the lab wants an ERCOT-specific reserve-cost number — it would need to come
from ERCOT's Independent Market Monitor (Potomac Economics) annual "State of the Market" report
rather than a capacity auction result, since none exists in ERCOT.

### Assessment

Both PJM and MISO capacity clearing prices are real, official, annually re-set auction outputs,
directly quoted here in $/MW-day from ISO releases and trade press covering those releases. The
conversion to $/MW-year (×365) is straightforward arithmetic, not itself a published figure — flag
as **derived** when citing the annualized numbers. The prices have moved by roughly an order of
magnitude year-over-year in both markets (2024/25 → 2025/26 → 2026/27), driven primarily by data-
center load growth and thermal-generator retirements per IEEFA/RTO Insider reporting — so any
single number cited in the lab should be dated and zone/season-qualified, exactly as this note
does, rather than presented as a stable constant.

### What was NOT found

- A single "US average" $/MW-year reserve/capacity cost across all ISOs — figures are
  auction/zone/season-specific by design and vary 10x+ year over year; there is no single
  authoritative blended national number.
- An ERCOT-specific $/MW-year reserve cost figure directly comparable to PJM/MISO capacity
  prices (ERCOT has no capacity market; see note above).
- A direct national-average $/MWh VOLL headline number from the LBNL ICE Calculator itself (see
  Claim 1 "what was NOT found").

---

## Bottom line for the lab

- **VOLL**: real, regulator-set figure. ERCOT's own history spans $3,000/MWh (2011) → $9,000/MWh
  (2015-2021) → $5,000/MWh (2022-2024 interim) → $35,000/MWh system-wide average (Aug 2024-present,
  per Brattle Group study/PUC order), with customer-class values from ~$4,000/MWh (residential) to
  $667,000/MWh (small C&I). The original $9,000-$30,000/MWh guess is a reasonable historical
  order-of-magnitude band but is now stale on the high side relative to the current $35,000/MWh
  PUC-adopted figure — cite a range like "$5,000-$35,000+/MWh, strongly dependent on customer
  class and year" instead of a fixed band.
- **Reserve/capacity cost**: real, auction-cleared figures. PJM 2026/27 BRA: $329.17/MW-day
  (~$120,150/MW-year, ~$120/kW-year). PJM 2024/25: $28.92/MW-day (~$10,556/MW-year). MISO PY
  2025/26 annualized: ~$217/MW-day (~$79,200/MW-year); PY 2024/25: ~$21/MW-day (~$7,665/MW-year).
  These are directly sourced auction results; the $/MW-year conversions are simple derived
  arithmetic (×365), not separately published figures. ERCOT has no equivalent capacity-market
  number since it is energy-only with ORDC-based scarcity pricing instead.
