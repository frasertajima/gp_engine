# Research note: does regulatory asymmetry (blackout risk vs. diffuse ratepayer cost) explain
utilities' preference for conservative deterministic reserve heuristics over statistically-optimal
dynamic models — and is "legal defensibility of an established methodology" the documented reason?

**Claim tested:** Utilities and ISOs have a structural incentive to prefer conservative,
deterministic rule-of-thumb reserve heuristics (N-1 largest-contingency rules, fixed percentage
margins) over statistically-optimal dynamic models, because (a) over-procurement imposes a small,
diffuse ratepayer cost that draws little scrutiny, while (b) under-procurement risks blackouts,
extreme VOLL costs, regulatory fines and political fallout — and a simple, well-established
deterministic heuristic offers better legal/regulatory defensibility as a "standard of care" during
a reliability event than a newer statistical model would, even if the statistical model is proven
more economically efficient.

**Verdict: MIXED — TWO OF THE THREE MOVING PARTS ARE WELL-SOURCED IN REAL REGULATORY-ECONOMICS
LITERATURE; THE THIRD (THE SPECIFIC "LEGAL DEFENSIBILITY OF ESTABLISHED METHOD OVER NOVEL
STATISTICAL MODEL" CAUSAL MECHANISM) IS A PLAUSIBLE, STRUCTURALLY-CONSISTENT INFERENCE THAT NO
SOURCE FOUND STATES DIRECTLY.**

- **Well-sourced:** Utilities/consultants/regulators explicitly recommend reserve margins ABOVE the
  lowest-average-cost ("risk-neutral economically optimal") level, and justify this explicitly by
  the asymmetry between the cost of rare, severe under-procurement events and the cost of routine,
  modest over-procurement — this is documented in primary regulatory-economics reports (NARUC/
  Brattle/Astrapé; E3 for El Paso Electric), not just inferred.
- **Well-sourced (separately):** The dominant physical/deterministic reliability standard (the
  "1-in-10" LOLE criterion and, more generally, N-1-style deterministic rules) is documented in the
  same literature as persisting largely because it is entrenched and customers "rarely complain,"
  not because anyone has shown it to be the economically efficient target — i.e., inertia/legal-
  familiarity is the documented explanation for *why the rule survives*, distinct from (but
  compatible with) a defensibility argument.
- **NOT found stated anywhere:** an explicit claim that regulators or courts treat "reliance on an
  established, simple heuristic" as conferring *litigation or prudence-review* safety relative to a
  provably-better statistical model. The "prudent utility standard" / "20-20 hindsight" doctrine is
  real and well-documented, but every source describes it as judging reasonableness against
  information available *at the time*, not as an explicit preference for older/simpler methods over
  newer/statistical ones. That specific mechanism remains a structurally plausible but unconfirmed
  inference.

---

## Source 1 (primary regulatory-economics report): Kevin Carden & Nick Wintermantel (Astrapé
Consulting) and Johannes Pfeifenberger (The Brattle Group), *"The Economics of Resource Adequacy
Planning: Why Reserve Margins Are Not Just About Keeping the Lights On,"* National Regulatory
Research Institute (NRRI), Report 11-09, April 2011.

- **Publisher:** National Regulatory Research Institute (the research arm affiliated with NARUC,
  the U.S. National Association of Regulatory Utility Commissioners).
- **URL:** https://pubs.naruc.org/pub/FA865D94-FA0B-F4BA-67B3-436C4216F135
- **Date:** April 2011; accessed 2026-07-27. Fetched as raw PDF and converted with `pdftotext`
  locally (WebFetch's built-in PDF summarizer could not parse this file's compressed text streams
  reliably — same issue noted in this lab's `02_deterministic_reserve_heuristic.md`; local
  extraction is the actual source of the quotes below, not WebFetch's summary).

Verbatim quotes:

> "Considering that customers, utilities, regulators, and policy makers all tend to be risk-averse
> to high-cost outcomes, the ―optimal‖ target reserve margin should consequently not be based
> solely on the lowest-average cost reserve margin, shown as 12% in Figure 4. While a 12% reserve
> margin would offer the cheapest option for customers in terms of long-run average costs, the
> highest-cost outcomes that load-serving entities and customers would be exposed to might be
> unacceptable."

> "For example, while the expected average of annual reliability-related costs at a 12% reserve
> margin is only $240 million, Figure 5 shows that there is a very small chance that total annual
> reliability-related costs could be as high as $8.3 billion. Assuming total retail rates are 10
> cents/kWh, this maximum cost exposure would raise consumers' annual costs by 50% for the system
> analyzed. These numbers are not out of line with estimates that the California Energy Crisis
> would have doubled retail rates if all costs had been passed through to customers."

> "For decades, the utility industry has been using the 1-in-10 standard as the primary if not sole
> means for setting target reserve margins and capacity requirements in resource adequacy analyses.
> ... In the literature we surveyed, no justification was given for the reasonableness of the
> standard other than that it is approximately the level that customers were accustomed to. Because
> customers rarely complain about the level of reliability they receive under the 1-in-10 standard,
> few question the 1-in-10 metric as an appropriate standard."

This is a direct, on-point primary source for two separate sub-claims:
1. **The asymmetric-cost-drives-conservatism mechanism is real and explicitly argued** — the report
   itself recommends target reserve margins above the lowest-average-cost point precisely because
   of "risk aversion to high-cost outcomes," i.e., the fat right tail of blackout/reliability-event
   costs, not the thin, low, predictable cost of a few extra percentage points of installed
   capacity.
2. **The entrenchment of the deterministic 1-in-10/N-1-style standard is explicitly attributed to
   inertia and lack of customer scrutiny** ("customers rarely complain... few question the 1-in-10
   metric"), not to any demonstrated superiority over statistical/probabilistic alternatives — this
   is close to, but not identical with, the claim's legal-defensibility argument. It supports "the
   heuristic persists because it draws no scrutiny" but does not itself invoke litigation/prudence-
   review defensibility as the reason.

## Source 2 (primary consulting report used in an actual utility rate proceeding): Energy and
Environmental Economics, Inc. (E3), *"Estimating the Economically Optimal Planning Reserve
Margin,"* prepared on behalf of El Paso Electric Co., May 2015.

- **Publisher:** E3 (Energy and Environmental Economics, Inc.), a firm regularly retained by
  utilities and regulators for resource-adequacy economics.
- **URL:** https://www.ethree.com (report fetched from a mirrored/cached PDF; original filed with
  El Paso Electric's regulatory proceedings).
- **Date:** May 2015; accessed 2026-07-27. Fetched as raw PDF, converted locally with `pdftotext`.

Verbatim quotes:

> "While our analysis shows that a PRM of 13% has the same expected societal costs as a PRM of 18%,
> the variability in annual costs is much higher at the lower PRM. This is because customer outages
> are infrequent but extremely costly, whereas the carrying cost of additional capacity is modest
> but incurred each year. ... To the extent that utility customers are risk-averse, they will seek
> less variance in total annual costs and should prefer a higher PRM to a lower PRM given that the
> incremental annual systems costs are equal. This concept of risk aversion is well-established in
> the literature, although it is difficult to quantify."

> "The inherent planning difficulties associated with maintaining a tPRM will mean that EPE is
> often slightly over or under the target. In these cases, we recommend that EPE maintain an
> over-reliable system rather than under-reliable, all else being equal."

This is a second, independent (different firm, different utility, different year) primary source
making the identical asymmetric-cost argument, and it goes one step further than Source 1: it is an
explicit, actionable recommendation — filed in a real regulatory economics study for a specific
utility — that when in doubt, err toward *over*-procurement rather than under-procurement, on
exactly the stated grounds that outage costs are "infrequent but extremely costly" while excess
capacity cost is "modest but incurred each year." This is close to a verbatim confirmation of
sub-claims (a) and (b) of the claim under test (the cost asymmetry itself), independent of the
"legal defensibility" mechanism.

## Source 3 (on the "prudent utility standard" / legal doctrine): Kirsten Jarvis (student
author), *"Keeping the Lights On—At All Costs? Imploring Consistent Prudence Review and a Prudence
Standard That Includes Demand Response and Responsible Portfolio Management,"* Vermont Law
Review, vol. 29, 2005, pp. 1037 ff.

- **Publisher:** Vermont Law Review.
- **URL:** https://lawreview.vermontlaw.edu/wp-content/uploads/2012/02/jarvis.pdf
- **Date:** 2005 (article); accessed 2026-07-27. Fetched as raw PDF, converted locally with
  `pdftotext`.

Verbatim quotes:

> "The historical standard for prudence is what a reasonable, professional utility manager would
> have done in the situation under scrutiny. A thorough prudence review examines every aspect of
> information available to a utility at the time it made a particular decision and then assesses
> how the utility performed based on that information—whether the utility's decisions and actions
> reflect prudent care."

> "Because state PUCs apply a prudence standard in retrospect, according to what a decision-maker
> knew or should have known at the time the decision was made, '[t]he further the review is from
> the utility decision, the more difficult it is. [The prudence review] should not be influenced by
> new information arising subsequent to the time such management decisions were made, since to do
> so results in an inequitable "20-20 hindsight" analysis.'" (quoting William A. Badger, *Prudence
> Reviews: New Approaches Are Needed*, 130 Pub. Util. Fort., July 15, 1992, at 22, 24)

This confirms that a real, named legal/regulatory doctrine — the "prudent utility"/"prudent
manager" standard, applied via post-hoc "prudence review" by state Public Utility Commissions —
genuinely exists and genuinely governs whether a utility's decisions (including reliability-related
ones) get treated as reasonable after the fact, with an explicit doctrine against judging with
hindsight. **However, nothing in this article (or found elsewhere) states that this doctrine
specifically favors reliance on an older/simpler/deterministic methodology over a newer/statistical
one.** The doctrine as described is method-neutral on its face: it asks whether the decision was
reasonable given information available at the time, which in principle could favor either a
well-validated new statistical model or an old rule of thumb, depending on what a "reasonable
professional utility manager" would have relied on. The inference that an established heuristic is
*specifically* safer under this doctrine than a novel statistical model — because, e.g., it has
decades of precedent behind it and a novel model does not — is a reasonable extrapolation from how
prudence review is described, but it is not itself asserted by this or any other source found.

## Source 4 (adjacent corroboration — burden of proof on non-conventional/abnormal methodologies):
NARUC/NRRI, *"Looking Before Leaping: Are Your Utility's Gas Price Forecasts Accurate?"*

- **Publisher:** National Regulatory Research Institute (NARUC-affiliated).
- **URL:** https://pubs.naruc.org/pub/FA85C1D7-EEFB-B8E4-63EA-1D3561638B86
- **Date:** accessed 2026-07-27; fetched as raw PDF, converted locally with `pdftotext` (WebFetch's
  summarizer again failed to parse the compressed PDF streams).

Verbatim quote:

> "Regulators should also require utilities to compare their forecasts with other forecasts derived
> by government agencies or private entities. A comparison can help regulators gauge the
> reasonableness of a utility's forecast, and where it lies relative to other forecasts. ... If a
> utility's forecast is an abnormality, the utility should then have the burden to explain why its
> forecast differs so much from other forecasts."

This is about gas-price forecasting, not reserve margins specifically, but it is the closest thing
found in this search to a documented "burden of proof falls on the outlier/novel methodology"
regulatory norm: a forecast (or, by extension, a methodology) that departs from the conventional
comparison set is treated as the thing that needs extra justification, while conformity with the
conventional/established approach is implicitly the lower-friction default. This is suggestive
corroboration for the claim's legal-defensibility mechanism — the same asymmetry (established
method = default-safe, novel method = burden-bearing) shows up in an adjacent regulatory-economics
context — but it is still not a direct statement about reserve-margin heuristics specifically, and
it is being used here as an analogy, not as direct evidence for the claim.

## What was searched but did not yield direct evidence

Multiple targeted searches for the *specific* causal claim — "utilities prefer deterministic
heuristics over statistical models because of legal/regulatory defensibility during a reliability
event, even when the statistical model is proven more efficient" — returned only generic material
on deterministic-vs-probabilistic reliability-criteria adoption barriers (e.g., a ScienceDirect
paper, "A multi-dimensional analysis of reliability criteria: From deterministic N-1 to a
probabilistic approach," paywalled at 403 and not retrievable in full; CAISO's own probabilistic
planning-reserve-margin research, which frames the barrier as a "conservative operating paradigm
from the past" rather than an active legal-risk calculation). No source found states or implies
that a utility's *specific reason* for preferring N-1/fixed-percentage rules is that they would
survive a prudence review or litigation better than a statistically-optimal model would. This
absence is itself informative: it suggests that if this mechanism operates, it is an unstated,
background assumption among utility planners and their counsel rather than something written down
and defended in the regulatory-economics literature that does exist on reserve-margin conservatism.

## Verdict, disaggregated by sub-claim

1. **"Over-procurement imposes small, diffuse costs that draw little scrutiny."** — WELL-SOURCED.
   Source 1 states plainly that customers "rarely complain" and "few question" the 1-in-10 standard
   despite reliability critics arguing it "results in reserve margins that impose too large a cost
   on customers."
2. **"Under-procurement risks blackouts, extreme VOLL costs, and political fallout."** — WELL-
   SOURCED as an economic mechanism (Sources 1 and 2 both quantify the fat right tail of outage
   costs — e.g., "$8.3 billion" in a tail scenario against a "$240 million" average — as the
   explicit reason to hold reserves above the lowest-average-cost point). The "regulatory fines and
   political fallout" framing specifically is plausible and consistent with how prudence review
   (Source 3) operates, but is not separately quantified or evidenced in these sources; it's a
   reasonable gloss on "extreme cost outcomes," not something separately documented.
3. **"A simple deterministic heuristic offers better legal/regulatory defensibility as a 'standard
   of care' than a newer statistical model, even if the statistical model is more efficient."** —
   NOT DIRECTLY SOURCED. The "prudent utility standard" and post-hoc "prudence review" doctrine
   (Source 3) are real and well-documented, and the general pattern of "conventional methodology is
   the low-friction default, departure bears the burden of proof" shows up in an adjacent context
   (Source 4, gas-price forecasting). But no source states that this doctrine specifically
   privileges an older/simpler/deterministic method over a newer/statistically-validated one when
   both are available. This part of the claim should be labeled in any lab writeup as **a
   structurally plausible inference consistent with the documented doctrine and with observed
   utility conservatism, not itself a documented finding.**

**Bottom line for the lab:** it is well-documented, from primary regulatory-economics literature
independent of climate/insurance sources, that utilities and their consultants explicitly recommend
holding reserve margins above the "lowest-average-cost" economically optimal point *because of* the
asymmetric tail cost of blackouts versus the modest, steady cost of excess capacity — this is not a
strawman, it is argued by name in NRRI/Brattle/Astrapé (2011) and E3 (2015) reports written for and
used by actual utilities and commissions. It is separately documented that the deterministic 1-in-10
standard persists largely through inertia and lack of customer/regulatory scrutiny rather than
demonstrated efficiency. What is NOT documented anywhere found is the narrower, sharper claim that
the *specific reason* utilities/ISOs stick with deterministic heuristics over provably-better
statistical models is that the heuristic is a legally safer "standard of care" in a prudence review
or litigation — that is a coherent, well-motivated inference built from real adjacent doctrine
(prudence review, hindsight-bias avoidance, burden-of-proof-on-the-outlier-forecast), but it should
be presented in the lab as inference layered on top of solidly-sourced material, not as an
independently-confirmed regulatory-economics finding.
