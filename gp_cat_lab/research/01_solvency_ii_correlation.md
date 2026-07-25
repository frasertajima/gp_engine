# Research note: Solvency II SCR aggregation via fixed linear correlation matrix

**Claim tested (from `climate_cat_lab/LAB_PLAN.md`):** EU regulatory capital aggregation
across risk categories uses a fixed linear correlation matrix ("square root formula"),
not a joint tail-dependence-aware model.

**Verdict: CONFIRMED (primary legal source, verbatim).**

## Primary source

- **Directive 2009/138/EC** of the European Parliament and of the Council of 25 November
  2009 (Solvency II, recast), **Article 104** ("Design of the Basic Solvency Capital
  Requirement") and **Annex IV, point 1**.
- Consolidated/derivative full text consulted via:
  - `https://lexparency.org/eu/32009L0138/ART_104/` (Article 104)
  - `https://www.legislation.gov.uk/eudr/2009/138/annex/IV` (Annex IV, point 1 — UK's
    retained-EU-law legislation.gov.uk mirror, which reproduces the Directive's Annex text)
  - Corroborating source for the delegated-regulation-level sub-module formula: EIOPA's own
    rulebook, `https://www.eiopa.europa.eu/rulebook/solvency-ii-single-rulebook/article-5784_en`
    (Article 164 of Commission Delegated Regulation (EU) 2015/35, market-risk sub-module
    aggregation — same formula family, one level down).
- Accessed 2026-07-23 (via WebSearch/WebFetch; EUR-Lex's own page did not render as static
  text through the fetch tool, so the UK legislation.gov.uk mirror and lexparency.org's
  consolidated text were used instead — both reproduce the same treaty/annex text, not
  independent secondary commentary).

## Verbatim aggregation formula (Article 104 / Annex IV point 1)

> "Basic SCR = √(Σ Corr(i,j) × SCR(i) × SCR(j))"

where `Corr(i,j)` is defined as "the item set out in row i and in column j" of a fixed
correlation matrix, and `SCRi`/`SCRj` range over the five top-level risk modules: SCR
non-life (non-life underwriting), SCR life, SCR health, SCR market, SCR default
(counterparty default). Each module's own capital charge is itself calibrated to a 99.5%
1-year Value-at-Risk.

## Verbatim correlation matrix (Annex IV, point 1)

| | Market | Default | Life | Health | Non-life |
|---|---|---|---|---|---|
| **Market** | 1 | 0,25 | 0,25 | 0,25 | 0,25 |
| **Default** | 0,25 | 1 | 0,25 | 0,25 | 0,5 |
| **Life** | 0,25 | 0,25 | 1 | 0,25 | 0 |
| **Health** | 0,25 | 0,25 | 0,25 | 1 | 0 |
| **Non-life** | 0,25 | 0,5 | 0 | 0 | 1 |

(Comma decimal notation is the EU legal text's own convention, reproduced as quoted.)

The same architecture recurses one level down: within the market-risk module, sub-risks
(interest rate, equity, property, spread, currency, concentration) are aggregated with
their own fixed correlation matrix via the identical square-root formula (Commission
Delegated Regulation (EU) 2015/35, Article 164) — confirming this is not a one-off top-level
simplification but the standard formula's aggregation mechanism used repeatedly throughout
the whole SCR calculation, non-life premium/reserve risk correlations by line of business
included (Annex III/IV of the Delegated Regulation; not independently re-fetched here, but
consistent with the pattern found at both levels checked).

## Assessment

This is about as strong as primary-source confirmation gets: an EU treaty-level Directive,
still in force, whose numeric correlation matrix is quoted directly. It confirms the lab's
premise precisely as stated — the EU-wide (not one company's) standard-formula capital
regime aggregates risk-category capital charges with a **fixed linear correlation matrix**
via a square-root (elliptical/quadratic-form) formula, which is mathematically the same
aggregation object as a multivariate Gaussian/elliptical covariance structure — i.e. it
inherits the zero-tail-dependence property `LAB_PLAN.md` attributes to it (see
`03_gaussian_copula_tail_dependence.md` for that separate mathematical claim). Internal
insurers may use full internal models instead of the Standard Formula, but the Standard
Formula (this mechanism) is the default EU-wide regime most insurers who don't build a
regulator-approved internal model actually use.
