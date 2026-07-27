# Research note: would US electricity market participants oppose/be expected to oppose a latent-variable or mixture-model reserve requirement unless it were fully transparent, reproducible, and deterministic?

**Claim being tested:** "Market participants (generators, traders) in US electricity markets
oppose or would be expected to oppose dynamic/regime-based reserve targets unless the
underlying statistical model is fully transparent, reproducible, and deterministic —
specifically because a latent-variable/mixture-model reserve requirement (where a 'regime
responsibility' value isn't a simple deterministic formula) could create settlement disputes
or be challenged by market participants if reserve requirements (which affect
market-clearing prices) fluctuate based on a statistical model's internal, less-transparent
state."

**Verdict: this is a PLAUSIBLE, WELL-GROUNDED INFERENCE from real, well-documented FERC/ISO
transparency norms — NOT a directly documented instance of the specific concern in the
claim.** I found no FERC order, ISO stakeholder filing, market monitor report, or academic
paper that discusses a latent-variable/mixture/regime-switching statistical model being
proposed or used to set a reserve requirement, and no one has (yet) objected to one on
these grounds — because, as far as this search could determine, no ISO has ever proposed
one. What *is* real, heavily documented, and directly on point as a general principle is
this: FERC has an explicit, decades-old, litigated policy that any value that feeds into
a jurisdictional rate or market-clearing price must be transparent, independently
verifiable by outside parties, and subject to a defined challenge process — and FERC has
forced ISOs/utilities to redesign mechanisms specifically because that transparency was
lacking. That is real, strong, but *general* evidence for the underlying norm the claim
invokes. The leap from "FERC/ISOs require transparency and challengeability of
market-affecting formulas in general" to "market participants would specifically object to
a mixture-model/regime reserve target on transparency grounds" is a reasonable and
well-motivated inference, not a documented fact. The write-up below is honest about that
gap.

---

## Part 1 — The general principle IS real and heavily documented: FERC requires
## transparency and independent verifiability of any formula/methodology that feeds a
## jurisdictional rate or market-clearing price

### Source 1: FERC Staff, "Staff's Guidance on Formula Rate Updates," July 17, 2014

- URL: https://www.ferc.gov/sites/default/files/2020-04/staff-guidance.pdf — fetched directly
  (downloaded and read via `pdftotext`), 2026-07-27.

Verbatim, p.1:

> "The Commission recognizes that the integrity and transparency of formula rates and their
> implementation are critically important in ensuring just and reasonable rates. Therefore,
> the Commission's policy is that utilities include safeguards in their transmission formula
> rate protocols to provide transparency in the utilities' implementation of their
> transmission formula rates, **to ensure that the input data is the correct data and that
> calculations are performed consistent with the formula.**"

And, on the specific verifiability requirement (p.1-2, footnoting the seminal 2013 MISO
formula-rate-protocols order):

> "Annual updates posted for interested parties and filed with the Commission as informational
> filings must contain sufficient support for all inputs **so that interested parties can
> verify that each input is consistent with the requirements of the formula.**" (footnote 2:
> *Midwest Indep. Transmission Sys. Operator, Inc.*, 143 FERC ¶ 61,149, at P 86 (2013))

This is FERC's own staff explicitly stating the causal mechanism the claim invokes: a
formula that sets rates/prices must be verifiable by outside parties, or FERC will not
approve it as just and reasonable.

### Source 2: 143 FERC ¶ 61,149 (2013) — the MISO formula-rate-protocols order (via secondary
sources, since the primary PDF's electricity-market summaries were consistent across sources
but the order itself was not text-extractable from the mirrors checked)

Per the S&P Global Commodity Insights and Winston & Strawn summaries of the order (fetched via
WebSearch synthesis, cross-checked against two independent summaries, 2026-07-27):

> "The May 16 Order requires revisions to the MISO formula rate protocols in order to (1)
> permit all interested parties to be eligible to participate in formula rate information
> exchange and review processes; (2) make revenue requirements, inputs, calculations and other
> information publicly available, providing interested parties with the opportunity to review
> that information; and (3) **afford parties the opportunity to engage in informal and formal
> challenge processes regarding implementation of the formula rate.**"

FERC's finding, per the same summaries: MISO and 37 transmission owners' existing protocols
were **not sufficient to ensure that transmission rates are just and reasonable**, precisely
because a lack of transparency and challenge procedure created (or would create) disputes
over formula-driven charges — the same causal chain (opaque formula → disputes over
formula-driven charges → regulatory intervention) the claim asserts for reserve
requirements. Note: this is a *cost-recovery* formula-rate case, not a reserve-requirement
or market-clearing-input case — the mechanism is analogous, not identical.

### Source 3: FERC Order No. 844 (2018) — transparency in RTO/ISO markets

- Per WebSearch synthesis of FERC's own news release (ferc.gov/news-events/news/ferc-issues-final-rules-improve-regional-market-transparency-interconnections)
  and industry summaries (Troutman Pepper's Washington Energy Report), 2026-07-27.

FERC required RTOs/ISOs to add to their tariffs "the transmission constraint penalty factor
values used in its market software," "the circumstances ... under which the transmission
constraint penalty factors can set LMPs," and the procedures for changing those values — i.e.,
FERC required that a market-clearing-price-setting input *internal to ISO market software*
be published, documented, and rendered auditable in the tariff, precisely because — per
FERC's own stated rationale (industry-summary paraphrase) — "current RTO and ISO reporting
obligations ... [were] insufficiently transparent to permit market participants to fully
understand how prices reflect the actual marginal cost of serving load." This is the closest
documented precedent to "a less-transparent internal state of market-clearing software must
be made transparent by FERC order" — but it concerns penalty factors and uplift, not a
statistical/probabilistic reserve requirement.

---

## Part 2 — A reserve-requirement-specific analogue: PJM's Variable Resource Requirement
## (VRR) curve lists "transparency" as an explicit design criterion, precisely because it
## sets capacity-market-clearing prices

### Source: The Brattle Group, "Sixth Review of PJM's Variable Resource Requirement Curve,"
prepared for PJM, April 2025.

- URL: https://www.brattle.com/wp-content/uploads/2025/04/Sixth-Review-of-PJMs-Variable-Resource-Requirement-Curve.pdf
  — fetched (downloaded, read via `pdftotext`), 2026-07-27.

The report lists the stakeholder-endorsed design objectives for the VRR curve — the demand
curve for capacity that, together with supply offers, directly sets the RPM capacity-auction
clearing price (i.e., PJM's reserve requirement, expressed as a demand curve, function of
Net CONE and other parameters). Verbatim, from the enumerated criteria (p.15 area):

> "Aim for simplicity, stability, and transparency"

listed alongside criteria such as "Maintain reliability across a range of potential market
conditions," "Reduce price volatility due to small changes in supply and demand," and
"Mitigate susceptibility to exercise of market power." This is a concrete, named instance of
"transparency" being an explicit, stakeholder-adopted design requirement for the specific
type of object the claim is about: a reserve-requirement curve that determines
market-clearing prices in a real US capacity market. It is evidence *for* the general
principle, but it is a design objective, not a recorded instance of participants rejecting a
proposed dynamic/statistical curve on transparency grounds — no such proposal (mixture-model
or regime-based VRR curve) appears to have been made to PJM stakeholders in the material
reviewed here.

### Related, weaker-but-relevant: ERCOT's Operating Reserve Demand Curve (ORDC) shows
real methodological/statistical disputes over a reserve-pricing mechanism — but the
dispute is about mathematical correctness, not "black box"/opacity per se

- Richard Wakeland, "The ERCOT ORDC Under-Estimates the LOLP Because of a Misapplication of
  Normal Distribution Probability Theory," SSRN working paper (abstract_id=3180714), and a
  companion paper "Fundamental Problems with ERCOT's Operating Reserve Demand Curve and a
  Proposed Solution" (abstract_id=3193493). Full text behind SSRN's access wall (WebFetch
  returned HTTP 403 on both); content below is from WebSearch's synthesis of the abstracts/
  secondary discussion, not a verified direct quote — flagged as such.

Per that synthesis: critics argue the ORDC's loss-of-load-probability (LOLP) curve — which
is a statistically-derived, not simple-deterministic, input that sets real-time scarcity
prices every 5-minute interval — "incorrectly applies the hour-ahead forecasted reserve
level error distribution to the real-time reserve level, with no basis in probability
theory for this application." This is a real, publicly documented dispute over a
statistically-modeled reserve-pricing input in an actual US market — but the criticism found
is about the model's mathematical validity, not explicitly framed as "this isn't transparent/
reproducible enough" or "a market participant could dispute a settlement because they can't
reproduce the internal state." I could not verify (SSRN paywalled, and no other source
found) whether the *transparency* framing specifically — as opposed to the *correctness*
framing — was raised in ERCOT stakeholder proceedings about the ORDC. This is flagged as an
unconfirmed gap, not claimed as support.

---

## Part 3 — What was explicitly searched for and NOT found: no documented instance of a
## latent-variable/mixture-model/regime-switching reserve requirement being proposed,
## discussed, or objected to by any ISO, market monitor, or FERC filing

Searches run (2026-07-27), all via WebSearch, none returning a relevant hit:

- `"regime-switching" OR "hidden Markov" OR "mixture model" electricity market reserve
  requirement FERC transparency concern` — returned only academic modeling papers on
  regime-switching price *forecasting*, none connected to reserve-requirement setting,
  FERC review, or any stakeholder/transparency objection.
- `independent market monitor concerns "machine learning" OR "black box" model reserve
  requirement electricity` — returned only general ML-in-energy academic literature
  (interpretability trade-offs in deep learning for market-manipulation detection), nothing
  from an actual IMM (Monitoring Analytics/PJM, Potomac Economics/ERCOT-NYISO-MISO, or
  CAISO's DMM) objecting to a statistical reserve model.
- `ISO stakeholders concern "not reproducible" OR "cannot replicate" statistical model market
  clearing input` — no relevant hits.

This is meaningful negative evidence for scoping the claim honestly: it is very likely that
no US ISO has ever proposed a latent-variable/mixture-model reserve requirement, so there is
no historical record of participants opposing one — the claim is necessarily prospective/
hypothetical on that specific point, and can only be supported by the adjacent, real
evidence in Parts 1-2 about transparency norms for *other* market-clearing formulas and
reserve-pricing curves.

---

## Assessment (plain language)

The claim bundles two things that need to be pulled apart:

1. **"FERC-jurisdictional US electricity markets have a real, hard, litigated norm that any
   formula/model feeding market-clearing prices must be transparent and independently
   verifiable, and FERC has forced redesigns specifically to fix opacity"** — this part is
   **CONFIRMED**, directly, with primary-source quotes (FERC staff guidance citing the 2013
   MISO order; Order No. 844's penalty-factor transparency mandate; PJM's VRR curve listing
   "transparency" as a named design criterion for a reserve-requirement curve that sets
   capacity prices).

2. **"Market participants would specifically oppose a latent-variable/mixture-model reserve
   requirement (as opposed to a deterministic one) on these grounds, because its internal
   state is less transparent and could create settlement disputes"** — this part is **NOT
   CONFIRMED as a documented fact**. No source found describes this specific scenario, this
   specific model class, or any real objection along these lines. It is a reasonable
   extrapolation from (1) — since FERC and ISOs have consistently required transparency and
   challengeability for far simpler formula-rate and penalty-factor inputs than a
   latent-variable mixture model, it is plausible that a genuinely internal-state-dependent,
   non-deterministic reserve requirement would draw the same kind of scrutiny or worse — but
   this is inference from precedent and regulatory culture, not a documented instance of the
   claim's specific scenario.

For `grid_reserve_lab`'s purposes, this claim should be presented as: *"FERC and ISO
governance have a strong, real, and litigated track record of requiring transparency and
independent verifiability for any input that affects market-clearing prices, and have
forced redesigns of formula rates and market software specifically to fix insufficient
transparency (143 FERC ¶ 61,149 (2013); Order No. 844 (2018)). By clear analogy, a
latent-variable/mixture-model reserve requirement — whose value depends on unobserved
internal model state rather than a auditable deterministic calculation — would very likely
face the same kind of scrutiny or resistance, though no ISO has yet proposed such a model
and so no documented instance of this specific objection exists."* That framing keeps the
real, sourced part of the claim intact while being honest that the reserve-requirement-
specific application is inference, not precedent.

---

## Sources used

1. FERC Staff, "Staff's Guidance on Formula Rate Updates," July 17, 2014.
   https://www.ferc.gov/sites/default/files/2020-04/staff-guidance.pdf (fetched and read
   directly via pdftotext, 2026-07-27)
2. *Midwest Indep. Transmission Sys. Operator, Inc.*, 143 FERC ¶ 61,149 (2013) — the MISO
   formula-rate-protocols order establishing the transparency/verifiability/challenge-process
   standard; order itself not text-extractable from mirrors checked, content confirmed via
   two independent secondary summaries: S&P Global Commodity Insights
   (https://www.spglobal.com/commodityinsights/en/market-insights/latest-news/electric-power/051613-us-ferc-orders-miso-to-update-transmission-formula-rate-protocols,
   WebFetch 403'd, content via WebSearch synthesis) and Winston & Strawn
   (https://www.winston.com/en/energy-industry-watch/ferc-initiates-investigation-into-miso-transmission-owners-formula-rate.html,
   via WebSearch synthesis), and directly cited/footnoted in Source 1 above.
3. FERC, Order No. 844, "Uplift Cost Allocation and Transparency" (2018) — content via
   WebSearch synthesis of FERC's own news release
   (https://www.ferc.gov/news-events/news/ferc-issues-final-rules-improve-regional-market-transparency-interconnections)
   and Troutman Pepper's Washington Energy Report summary
   (https://www.troutmanenergyreport.com/2018/04/ferc-issues-final-rule-regarding-transparency-price-formation/).
4. The Brattle Group, "Sixth Review of PJM's Variable Resource Requirement Curve," prepared
   for PJM, April 2025. https://www.brattle.com/wp-content/uploads/2025/04/Sixth-Review-of-PJMs-Variable-Resource-Requirement-Curve.pdf
   (fetched and read directly via pdftotext, 2026-07-27).
5. Richard Wakeland, "The ERCOT ORDC Under-Estimates the LOLP Because of a Misapplication of
   Normal Distribution Probability Theory" (SSRN 3180714) and "Fundamental Problems with
   ERCOT's Operating Reserve Demand Curve and a Proposed Solution" (SSRN 3193493) — both
   403'd on direct WebFetch (SSRN access wall); content is from WebSearch's synthesis of
   abstracts/secondary discussion only, flagged as unverified direct quotes.
6. Negative-result searches documented in Part 3 (no hits for regime-switching/mixture-model/
   latent-variable reserve-requirement transparency objections in any FERC, ISO, or market
   monitor source).
