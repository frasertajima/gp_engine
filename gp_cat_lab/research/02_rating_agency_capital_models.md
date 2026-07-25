# Research: rating-agency capital models — is correlation-matrix aggregation general industry practice?

**Question tested:** climate_cat_lab/LAB_PLAN.md claims linear-correlation-matrix aggregation for
insurance capital is "general industry practice," not one regulator's idiosyncrasy (Solvency II).
This file checks whether rating-agency capital models — S&P Global Ratings' Insurance Capital
Model and AM Best's BCAR — independently use the same class of method.

## Source 1: A.M. Best, "Understanding Universal BCAR" (Best's Methodology, Criteria — Universal)

- **Publisher:** A.M. Best Rating Services, Inc.
- **URL:** https://www3.ambest.com/ambv/ratingmethodology/openpdf.aspx?ubcr=1&ri=999
- **Date:** April 28, 2016 (document header date); accessed 2026-07-23. Full PDF also saved locally
  at fetch time (binary, not re-saved here — verbatim text below was extracted directly from the
  PDF's rendered pages).

Verbatim quotes:

> "A.M. Best's capital formula uses a risk-based capital approach whereby net required capital is
> calculated to support three broad risk categories: investment risk, credit risk and underwriting
> risk. A.M. Best's capital adequacy formula also contains an adjustment for covariance, reflecting
> the assumed statistical independence of the individual components. A company's adjusted capital
> is divided by its net required capital, after the covariance adjustment, to determine its BCAR."

> "Collectively, the investment, credit and underwriting risk components generate more than 99% of
> a company's gross required capital... A company's gross required capital, which is the sum of the
> capital required to support all of its risk components, reflects the amount of capital needed to
> support all of those risks if they were to develop simultaneously. However, these individual
> components then are subjected to a covariance calculation within the BCAR formula to account for
> the assumed statistical independence of these components. This covariance adjustment essentially
> says that it is unlikely that all of the individual risk components will develop simultaneously,
> and this adjustment generally reduces a company's overall required capital."

> "A.M. Best recognizes the distortions caused by the 'square root rule' covariance adjustment,
> whereby the more capital-intensive risk components are disproportionately accentuated while the
> less capital-intensive risk components are diminished in their relative contribution to net
> required capital. Nevertheless, by using other distinct capital measures, A.M. Best can
> counterbalance this apparent shortcoming."

> "In addition, there is credit for a well-diversified book of business, but this credit is
> minimized for those companies that maintain small books of many lines of business and may not
> necessarily have expertise in each of them."

This is an explicit, named "square root rule" — the same functional form (`sqrt` of a
covariance/correlation-weighted sum of component capital charges) as Solvency II's SCR aggregation
formula (see `01_solvency_ii_correlation.md`), independently arrived at by a different
organization for a different (US/global rating, not EU regulatory) purpose. A.M. Best names its own
known weakness (the square-root rule's distortion of relative risk contribution) — i.e. this is not
a strawman description, it's the rating agency's own stated caveat about its own method.

## Source 2: Aon, "Summary of S&P's Proposed Insurer Risk-Based Capital Adequacy Model" (June 2023)

- **Publisher:** Aon (major reinsurance broker), summarizing S&P Global Ratings' published request-
  for-comment criteria documents (S&P's own criteria articles are cited by title inside this Aon
  document: "Request For Comment: Insurer Risk-Based Capital Adequacy — Methodology And
  Assumptions"; "Credit FAQ: Understanding S&P Global Ratings' Request For Comment On Proposed
  Changes To Its Insurer Risk-Based Capital Adequacy Methodology"; "Summary Of Feedback On Proposed
  Criteria For Insurer Risk-Based Capital Adequacy" — S&P's spglobal.com pages for these documents
  returned HTTP 403 to direct fetch, so this Aon secondary summary, which quotes S&P's terminology
  directly, is the source actually used here.)
- **URL:** https://www.aon.com/getmedia/91436df9-f3f9-4595-9d0b-bb63f59b600d/20230614-rating-season-sp-capital-criteria-summary.pdf
- **Date:** June 2023; accessed 2026-07-23.

Verbatim quotes:

> "The new model is to be calibrated to higher confidence levels, which has led to a general
> increase in the underlying risk charges. However, the proposed changes to correlation matrices
> and overall diversification methodology are likely to offset standalone risk increases,
> depending on an insurer's diversification."

> "Diversification will be allowed for Natural Catastrophe risk where currently it is 100 percent
> correlated to the overall capital charge."

> "Diversification: S&P lowered correlations on morbidity and mortality, mortality and pandemic,
> and 'other' non-life risks from those initially proposed."

This directly confirms: (a) S&P's capital model aggregates risk charges via named **correlation
matrices**, not just a covariance-adjustment euphemism; (b) as of the pre-2023 methodology, natural
catastrophe risk specifically was carried at a **fixed 100% correlation** to the overall capital
charge (the most conservative possible linear-correlation assumption — no diversification credit at
all for Nat Cat) and the 2023 proposal's revision was to relax that fixed assumption. This is
directly on-point for climate_cat_lab: it shows that the real-world capital-model treatment of
catastrophe risk correlation is exactly the "coarse, assumption-driven number" climate_cat_lab's
naive baseline is modeling, not a strawman.

## Corroborating source: SOA (Society of Actuaries) Financial Reporting Newsletter (November 2023)

- **Publisher:** Society of Actuaries, "S&P Global's Revised Capital Model Change Proposal and its
  Implication to U.S. Life Insurance Companies"
- **URL:** https://www.soa.org/sections/financial-reporting/financial-reporting-newsletter/2023/november/fr-2023-11-sun/
- **Date:** November 2023; accessed 2026-07-23.

Verbatim/paraphrased-with-quotes findings (WebFetch-summarized, quotes preserved from the article):
S&P's model uses a **three-level diversification framework** — "within business lines between
non-life premium risk and reserve risk" (Level 1), "within risk categories, i.e., life technical
risk... and market risk" (Level 2), and "between risk categories" (Level 3) — each governed by
named correlation factors (example given: "the correlation factor between mortality and morbidity
risks was lowered from 75 percent to 50 percent" between draft revisions, and "the correlation
factor between pandemic and mortality risks" was lowered "from 50 percent to 25 percent").

This corroborates the Aon summary independently (different publisher, same underlying S&P
documents) and confirms the correlation factors are treated as **tunable calibration inputs S&P
revises between drafts**, not something derived from a joint tail-risk simulation of the actual
peril process — consistent with climate_cat_lab's "flat/block correlation shortcut" framing.

## Verdict

**Confirmed at 2 independent capital-model frameworks beyond Solvency II** — A.M. Best's BCAR
(global, all insurers) and S&P Global Ratings' Insurance Capital Model (used in credit ratings
worldwide) — both aggregate risk-category capital charges via a covariance/correlation-matrix
"square-root formula," structurally the same object as Solvency II's SCR aggregation. This is not
one regulator's idiosyncrasy: it is the dominant methodological pattern across the three most
influential capital-adequacy frameworks in the (re)insurance industry (one EU regulatory, two
rating-agency, covering both US and global insurers).

One caveat for the lab writeup: none of these three sources describe using a **joint stochastic
simulation with a fitted tail-dependence structure** as an alternative or supplement at the
aggregation step (as opposed to peril-level cat models like RMS/AIR, which do simulate physical
hazard footprints — a separate layer, not the capital-aggregation layer this lab targets). The
S&p 2023 proposal's move to *relax* the 100%-correlation Nat Cat assumption is worth citing in the
lab as evidence the industry itself is aware this is a coarse simplification and is actively
revising it — supports, rather than undercuts, the lab's premise.

No paywall blocked the substantive claim here: S&P's own spglobal.com pages 403'd to direct
fetch, but Aon's and SOA's professional summaries quote S&P's terminology and specific correlation
figures directly and consistently with each other, which is sufficient corroboration for the
factual claim being tested (that S&P's model works this way) even though S&P's original PDF text
was not directly retrieved.
