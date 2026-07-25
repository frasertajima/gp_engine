# Research: book-size benchmarks for climate_cat_lab Phase 2's "mid-size regional insurer"

**Claim being checked (from LAB_PLAN.md Phase 2):** "a book size calibrated to a real mid-size
regional insurer (illustrative target: 100,000-300,000 policies, mean insured value ~$300-400k,
aggregate insured value in the tens of billions)."

**Verdict: PARTIALLY SOURCED.** No single published report states "a mid-size regional insurer
has 100k-300k policies at $300-400k average insured value." That exact bundled figure is a
constructed illustrative estimate. But each piece is independently anchored to real published
data, and combining them lands in a plausible, defensible range — this section documents the
pieces and the arithmetic, so the plan can cite the anchors rather than asserting the bundle as
if it were itself a sourced fact.

## 1. Average dwelling coverage amount: $300k-400k is a real, commonly-cited range

Source: WebSearch aggregation of consumer-insurance data sites (Insurance.com, NerdWallet, Forbes
Advisor, Insurify), all reporting the range insurers commonly use as their benchmark dwelling
coverage tier for average-cost quotes, current as of 2025-2026:

> "The average cost of homeowners insurance in the U.S. is $2,543 a year for $300,000 in dwelling
> coverage" — Insurance.com, "Average home insurance cost in 2026"
> (https://www.insurance.com/average-home-insurance-rates), accessed 2026-07-23.

> "The average cost of home insurance in the U.S. is $2,720 annually for $350,000 dwelling
> coverage" — cited via NerdWallet/Forbes Advisor aggregation, accessed 2026-07-23.

> "In 2025, American homeowners pay an average of $2,927 annually for home insurance that
> provides $350,000 in dwelling coverage with a $1,000 deductible" — Insurify, "Homeowners
> Insurance Facts and Statistics (2026)" (https://insurify.com/homeowners-insurance/knowledge/homeowners-insurance-facts/),
> accessed 2026-07-23.

> "The average cost of homeowners insurance in the U.S. is about $2,490 a year for $400,000 worth
> of dwelling coverage" — Forbes Advisor, "The Average Home Insurance Cost 2026"
> (https://www.forbes.com/financial-services/average-cost-homeowners-insurance/), accessed
> 2026-07-23. "Common coverage limits are between $250,000 and $500,000."

These are consumer-facing rate-comparison sites, not a single authoritative regulator/NAIC
figure — they cite Insurance Information Institute (Triple-I) data but I could not pull an
explicit average-dwelling-coverage number directly off iii.org (see "What was NOT found" below).
Still, four independent commercial sources converge on the same $300k-$400k range as the standard
benchmark tier, which is a reasonable basis for the lab's per-property average insured value
assumption. **Verdict on this piece: reasonably well sourced, though secondary rather than a
single regulatory primary source.**

## 2. Regional insurer scale: real anchor found via NAIC 2025 Market Share Report

Source: NAIC's 2025 Market Share Report (compiled from P&C insurers' NAIC annual-statement State
Page filings), summarized by Agency Checklists:
"NAIC 2025 Market Share Report | Top 25 Homeowners' Insurers"
(https://agencychecklists.com/2025/03/17/naic-2025-market-share-report-top-25-homeowners-insurers-74909/),
accessed 2026-07-23. Per the search summary: "the industry recorded approximately $1.06 trillion
in Direct Premiums Written in 2024" across all P&C lines, with "approximately 97.92% of P&C
insurers reporting."

Within that report's Top-25 homeowners' list, **Florida Peninsula Holdings Group** — explicitly
named as a genuine regional (not national) insurer — ranks #21 nationally:

> "Florida Peninsula Holdings Group's inclusion on the 2024 list reflects the increasing role of
> regional insurers in specialized markets." — ranked #21, **$1,171,534,895** in direct premiums
> written (homeowners multi-peril, 2024).

**Derived estimate (my arithmetic, not a directly published figure):** at the ~$2,500-2,900/year
average premium found in §1, $1.17B in direct premiums implies roughly **400,000-470,000
policies** for Florida Peninsula alone — a single regional insurer, on the *high* end of, or
somewhat above, the plan's illustrative 100k-300k range. This suggests the plan's 100k-300k
figure is a **plausible but conservative (lower-bound-leaning) estimate for "mid-size regional"**
— a real regional insurer already near the top of the national homeowners rankings sits above it.
The plan should say this explicitly rather than implying 100k-300k is a typical ceiling.

No policy-count figure was found directly in the NAIC report text itself — the report reports
direct premiums written, not policies in force, so the 400k-470k policy estimate above is derived,
not quoted.

## 3. What was NOT found

- iii.org's own "Facts and Statistics: Homeowners and Renters Insurance" page
  (https://www.iii.org/fact-statistic/facts-statistics-homeowners-and-renters-insurance),
  fetched 2026-07-23, does **not** contain a national average dwelling-coverage figure, a
  national policy-count figure, or a "typical regional insurer size" statistic in the content
  retrieved. It does contain state-level top-10-writer premium rankings (e.g. Mississippi) and
  claim-frequency data (5.3%-5.5% of insured homes had a claim in 2021-2022), neither of which
  bears on book size.
- No single source gives "aggregate insured value" for a regional insurer's book directly;
  the "tens of billions" figure in the plan is an unverified back-of-envelope multiplication
  (policies × average insured value), not sourced independently. Flag as an assumption, not a
  fact, if cited standalone.

## Recommendation for LAB_PLAN.md

Change the Phase 2 wording from an unqualified "illustrative target" to something like: *"100k-300k
policies is a deliberately conservative mid-size estimate — for comparison, Florida Peninsula
Holdings Group, a real regional insurer, wrote ~$1.17B in 2024 homeowners premium (NAIC 2025
Market Share Report), implying a policy count above this range at typical per-policy premiums.
Average insured value of $300-400k matches the commonly cited national average dwelling-coverage
benchmark (Insurance.com/Forbes Advisor/Insurify, 2025-2026). Aggregate insured value is a derived
multiplication, not independently sourced."* This keeps the scale defensible without overclaiming
a single report states the bundled number.
