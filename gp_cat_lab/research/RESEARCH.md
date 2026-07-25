# climate_cat_lab — premise verification (2026-07-23)

Every load-bearing claim in `LAB_PLAN.md` was checked against primary or near-primary sources
before any code was written, per Fraser's direction: assertions about "industry practice" need
more than one source, and everything must be backed by actual saved text, not just a link. Six
research passes, each with its own file (verbatim quotes, full citations, explicit verdict) in
this directory. This file is the index and the net effect on `LAB_PLAN.md`.

| # | Claim | Verdict | File |
|---|---|---|---|
| 1 | EU regulatory capital (Solvency II) aggregates risk categories via a fixed linear correlation matrix | **CONFIRMED** — primary legal text quoted verbatim | `01_solvency_ii_correlation.md` |
| 2 | This is general industry practice, not one regulator's idiosyncrasy | **CONFIRMED** at 2 more independent frameworks (A.M. Best BCAR, S&P Insurance Capital Model) | `02_rating_agency_capital_models.md` |
| 3a | Gaussian/linear correlation has zero asymptotic tail dependence | **VERIFIED** — settled mathematics (Sibuya 1960; Embrechts/McNeil/Straumann 2002; restated with proof in Donnelly & Embrechts 2010) | `03_gaussian_copula_tail_dependence.md` |
| 3b | The Gaussian copula "caused"/"killed Wall Street" in 2008 | **REJECTED as stated** — peer-reviewed source explicitly disputes this framing; softer "partly contributed" claim is defensible | `03_gaussian_copula_tail_dependence.md` |
| 4 | Climate trend is making the loss tail fatter every year (blanket claim) | **REJECTED as stated** — >80% of the long-term increase is exposure growth, not climate (Swiss Re sigma); real climate-driven component only clearly documented for specific perils (NA wildfire, +14%/yr) | `04_climate_loss_trends.md` |
| 5 | FEMA National Risk Index is a real, usable public dataset for Phase 3 | **CONFIRMED**, with one open item (license statement not read verbatim — fema.gov blocked direct fetch) | `05_fema_nri.md` |
| 6 | "Mid-size regional insurer" ≈ 100k-300k policies, $300-400k avg insured value, tens of billions aggregate | **PARTIALLY SOURCED** — avg insured value well anchored (4 independent consumer-data sources); policy count range is a plausible but conservative lower bound (a real regional insurer, Florida Peninsula Holdings, implies ~400-470k policies); aggregate figure is unsourced derived arithmetic | `06_book_size_benchmarks.md` |

## Net effect: what changed in `LAB_PLAN.md`

1. **Strengthened**, not weakened: the central "flat/linear correlation aggregation is real,
   general industry practice" premise is now backed by three independent frameworks (Solvency II,
   A.M. Best BCAR, S&P's Insurance Capital Model) with verbatim quotes, not one. A genuine bonus
   finding: S&P's own pre-2023 methodology carried Natural Catastrophe risk at a **fixed 100%
   correlation** (i.e. *zero* diversification credit) — real-world evidence that cat risk
   specifically gets the coarsest possible linear-correlation treatment in at least one major
   framework, which is closer to this lab's own naive baseline than the plan even originally
   claimed.
2. **Softened**: the 2008-crisis framing. The peer-reviewed source (Donnelly & Embrechts 2010)
   explicitly rejects "the Gaussian copula caused the crisis" and calls that popular framing
   (Felix Salmon's *Wired* piece) "entirely unjustified." The defensible claim is narrower: three
   major rating agencies adopted the model industry-wide by 2004, its tail-dependence blindness
   was publicly demonstrated in a real market event in 2005 (three years before the crisis, per
   a front-page *Wall Street Journal* story), and it remained standard practice regardless — "a
   known flaw that stayed in standard use," not "the formula that caused 2008."
3. **Narrowed**: the climate-urgency framing. Swiss Re Institute's own sigma data says exposure
   growth explains >80% of the long-term rise in insured losses; a genuine climate-driven
   component beyond exposure is clearly named only for specific perils (wildfire and North
   American secondary perils). The lab now cites the 5-7%/year growth figure and the exposure-
   growth caveat explicitly, and narrows the "climate signal" framing to wildfire/drought-driven
   regime shocks — which, usefully, is also the exact mechanism the lab's synthetic DGP models.
4. **Qualified**: Phase 2's book-size numbers now cite their real anchors (average dwelling
   coverage; a named real regional insurer's premium volume) instead of presenting the bundled
   100k-300k/$300-400k/"tens of billions" figure as if it were itself a single sourced fact.

## What remains an explicit, flagged assumption (not verified, and said so in `LAB_PLAN.md`)

- The synthetic DGP's regime-frequency, severity, and correlation-decay parameters — illustrative,
  checked only for producing a real tail-dependence effect (Phase 0's own sanity check), not
  claimed to match any real peril's true statistics.
- "Aggregate insured value in the tens of billions" (Phase 2) — derived arithmetic, not an
  independently published figure.
- FEMA NRI's redistribution/license terms — very likely public domain (federal dataset,
  17 U.S.C. §105, mirrored on academic archives) but not confirmed by a verbatim terms-of-use
  quote in this pass (fema.gov blocked direct fetch).
- The normalized-loss literature on whether tropical-cyclone damage shows a residual climate
  signal after adjusting for exposure is contested in the academic literature itself (Weinkle et
  al. vs. a competing analysis) — this lab does not take a side and does not need to; it uses the
  uncontested wildfire/regime finding instead.
