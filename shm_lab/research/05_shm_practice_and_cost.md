# Claim 5: real-world SHM adoption status, and sourced cost figures for the asymmetric-cost framing

**Status: PARTIALLY VERIFIED.** Real, credible, government/practitioner-informed source found for
US bridge inspection practice and a handful of real SHM system cost figures. No source found yet
for a bridge-specific dollar figure on "cost of a missed real damage event" (the false-negative
side of the asymmetric-cost story) — that gap is stated honestly below, not papered over.

## Source — Agdas, Rice, Martinez, Lasa, "Comparison of Visual Inspection and Structural-Health
Monitoring as Bridge Condition Assessment Methods" (QUT eprints 86517; authors affiliated with
Queensland University of Technology, University of Florida, and the Florida Department of
Transportation — a real practitioner-informed source, not a vendor blog).

### US bridge inspection practice — confirmed as still visual-inspection-default, not GP/SHM-based

- **The governing US standard is the National Bridge Inspection Standards (NBIS, FHWA 2004)**,
  which the paper states implies a **maximum 24-month inspection interval**, with visual inspection
  as "the *de facto* method of routine inspection."
- Direct quote, confirming this lab's litmus-test condition that a real (not strawman) classical
  incumbent exists and is what actually runs today: **"full-scale, permanent structural
  health-monitoring systems are sparingly used"** in current US bridge-maintenance practice; where
  SHM is deployed, it is overwhelmingly targeted at "monitoring for known problems such as
  corrosion and scour," not general-purpose damage detection of the kind this lab's GP soft-EM
  method targets.
- Scale context (from the American Society of Civil Engineers' Infrastructure Report Card, as
  cited in the paper): **607,380 bridges in the US, 66,749 (~11%) rated structurally deficient.**
  A real, large-scale, cited figure — useful context for why this problem matters, not a claim
  about KW51 or any specific structure.

### Real, sourced SHM cost figures (Florida-specific installed systems, not vendor marketing)

- A scour-monitoring system on a Florida coastal bascule bridge (four sonar sensors + weather
  station): **~$29,000 total, including sensor equipment, labor, and miscellaneous hardware.**
- Cathodic-protection corrosion monitoring on the Howard Frankland Bridge (Tampa Bay, I-275, 20
  critical piers): **~$11,900/pier**, equipment and labor included.
- These are **real, specific, sourced dollar figures for real installed SHM systems** — a much
  stronger citation than the vendor-blog range ($25,000-$300,000 lifetime cost) found earlier in
  this pass, which is kept only as a rough directional cross-check, not a primary figure.

### A directly relevant quote on liability — reinforces this lab's disclaimer, not incidental

The paper raises exactly the concern this lab's disclaimer is meant to foreclose: **"The ability of
an SHM system to continuously generate data has the potential to create liability issues... Should
a structural change leading to bridge failure be missed, which party, if any, holds the
responsibility?"** This is independent, real-world confirmation (from a practitioner-informed
academic source, not this lab's own reasoning) that SHM output carries genuine liability weight in
real practice — a concrete reason this lab's disclaimer must be as unambiguous as it is, not an
overcautious add-on.

## What is still NOT sourced (honest gap)

No source was found in this pass for a dollar figure on the **false-negative side** specifically —
the cost of a real missed structural-damage event leading to failure, in a form usable for an
asymmetric-cost economic layer analogous to `mining_gpc_lab`'s ranked-campaign model. Bridge-
collapse cost figures (e.g. the I-35W collapse referenced in the paper) exist in the literature but
were not pulled into a specific number here, and using one would require significant care not to
conflate a single catastrophic event's cost with this lab's much narrower "did we detect a
retrofit-driven state change cleanly" question. **The economic-layer stretch goal in `LAB_PLAN.md`
remains explicitly unconfirmed and lower priority than the core three-method detection comparison**
— do not invent a placeholder figure to fill this gap.
