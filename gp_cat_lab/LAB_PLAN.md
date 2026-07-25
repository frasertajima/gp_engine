# climate_cat_lab — how wrong is a correlation shortcut for catastrophe capital, in dollars

**Status:** Phase 0 DONE (2026-07-23) — see `RESULTS_PHASE0.md`. The oracle DGP
(`dgp_simulator.py`/`exposures.py`) checks out: systemic years are 9x more severe and
push near-pair loss correlation from ~0 to 0.477; nearby properties are more correlated
than distant ones (0.624 vs 0.277, confirming real spatial structure); and the headline
number — the literature's own upper tail-dependence coefficient λᵤ (Donnelly & Embrechts
2010, Definition 5.1) at q=0.99 — is **0.439** for nearby pairs (a 44x excess over the
0.010 independence baseline), while a Gaussian model fit to the *exact same mean and
covariance* as the oracle gives only **0.198**: two models with identical second-moment
statistics disagree by more than 2x on joint catastrophic-loss probability. A first draft
of the tail check (conditioning on total-book-loss years rather than each property's own
marginal quantile) gave a confounded, backwards result — caught, diagnosed, and fixed
before anything downstream depended on it; see `RESULTS_PHASE0.md`'s "methodology
correction" section.

**Phase 1 DONE (2026-07-23)** — see `RESULTS_PHASE1.md`. Fit all four methods on one
realistic 60-year historical sample: every method badly under-reserves (all four land
around 93.3% achieved survival vs. a 99.5% target, against a $10.2M true required capital
from a 500,000-year oracle resample) — the headline finding stands regardless of method. A
genuine surprise inside that: a better-shaped correlation alone (method 3, vanilla spatial
GP) is statistically indistinguishable from no correlation at all (method 1) — 93.30% vs.
93.29% — confirming LAB_PLAN's own flagged risk that "vanilla GP is still elliptical/
Gaussian" in the strongest possible form. A sample-size sweep (60→500 historical years)
ruled out "just needs more data" for all four methods, then an oracle-cheat diagnostic
(true regime labels, something no real method may use) isolated the actual reason: method
4's first implementation diluted its "systemic" component by mixing in ~3.7 ordinary years
per genuine systemic year (a fixed top-25%-quantile partition against a true ~6.7% regime
frequency) — a bias structural to the classifier, not fixable with more data, and given
the true labels the same machinery hit 99.54% survival. Fixed by sizing the partition to
the model's own fitted frequency estimate instead of a fixed quantile (still oracle-free):
method 4 then climbs from 94.8% (60yr) to 97.3% (500yr) survival as historical data grows
— the only one of the four methods that improves with more data at all, since it's the
only one that can represent a regime — while methods 1-3 sit on a flat, unmovable ~93.3%
ceiling regardless of sample size. Phase 2 (scale to a realistic book size, past the ~40k
in-core ceiling) not started.

**One line:** insurers and reinsurers size capital and reinsurance retention against
extreme-tail loss (99.5% 1-year VaR/TVaR is the Solvency II standard; US RBC and rating-
agency capital models are the same idea in different clothes). The number that drives
that decision comes from *aggregating* correlated exposures — and the standard method for
that aggregation, confirmed at three independent capital-adequacy frameworks (Solvency II,
A.M. Best's BCAR, S&P's Insurance Capital Model — see "Sources and verification" below), is
a fixed linear-correlation matrix: the same mathematical object whose zero tail-dependence
property is settled mathematics (Sibuya 1960; Embrechts/McNeil/Straumann 2002) and which a
peer-reviewed retrospective says "partly contributed" to the 2008 CDO mispricing (a real,
if narrower, claim than the popular "the formula that killed Wall Street" framing — see
below). Climate loss correlation is structurally the kind of thing that breaks a linear-
correlation assumption hardest exactly in the tail (one heat dome/drought/wildfire season,
one hurricane track, correlates thousands of claims at once) — and for at least one peril
family, wildfire, the growth in insured losses is no longer fully explained by exposure
growth alone (Swiss Re Institute, 2025 — see below). This lab builds a synthetic-but-
realistic cat-loss world where the *true* joint distribution is known, shows how much a
flat-correlation shortcut misprices the capital decision against that truth, and measures
how much of the gap a fitted spatial GP closes — in real dollars, at a book size the OOC
engine was built for.

## Sources and verification

Every claim above and below that asserts "this is how the industry works" was checked
against primary or near-primary sources — not just a web link, but saved verbatim quotes
with full citations — before this plan was finalized, and each has an explicit
verified/partially-verified/assumption verdict. Full detail, quotes, and citations are in
`research/` (index: `research/RESEARCH.md`); the corrections that research pass forced are
folded into the sections below rather than left in the original, less careful draft.

## Why this lab, and why now

Every GP-vs-baseline lab so far (`cvar_gp_lab`, `bayesian_decision_lab`,
`porphyry_cu_gpc_lab`) tested a specific decision-theoretic claim on a specific domain.
This lab is the first one aimed explicitly at the *failure mode* rather than the win:
not "GP beats baseline," but **"here is precisely why the shortcut can be catastrophically
wrong, and here is the dollar cost of that, in a world small enough that we know the
answer."** That framing matters more here than anywhere else in the portfolio, because:

1. **The stakes are real, but the honest figure is narrower than "climate is making
   everything worse."** Swiss Re Institute's own sigma data puts long-term global insured
   natural-catastrophe losses on a **5-7%/year growth trend, of which exposure growth (more
   property built in harm's way) explains more than 80%** — climate change is not the
   dominant driver of the aggregate trend, and this plan should not imply otherwise. Where
   Swiss Re does name a genuine climate-driven component *beyond* exposure, it is specific:
   North American **wildfire** losses growing at **14%/year**, tied explicitly to "the
   lengthening of fire seasons and long-term changes in temperature and precipitation
   patterns" (`research/04_climate_loss_trends.md`). That is a narrower, more defensible
   claim than the original draft's, and it happens to be exactly the mechanism (a correlated
   drought/heat/wildfire regime) this lab's synthetic DGP models. A capital model that
   quietly under-reserves in the tail is still exactly the kind of error that looks fine
   for years and then doesn't — that motivation stands even on the narrower claim.
2. **The failure mode is well-documented, and — checked directly — genuinely used at
   three independent capital-adequacy frameworks, not one.** Linear/Gaussian correlation
   matrices have *zero asymptotic tail dependence* — settled mathematics, not a contested
   claim (Sibuya 1960; formalized for finance by Embrechts, McNeil & Straumann 2002; restated
   with a full proof sketch in Donnelly & Embrechts 2010, `research/03_gaussian_copula_tail_dependence.md`).
   The same peer-reviewed source explicitly **rejects** the popular "the Gaussian copula
   killed Wall Street" framing (Salmon 2009) as "entirely unjustified," and instead documents
   something more defensible and more useful for this lab: the model (Li 2000) was adopted
   industry-wide — by end-2004, Fitch, Moody's, **and** S&P had all incorporated it into their
   rating toolkits — its tail-dependence blindness was publicly demonstrated in a real market
   event as early as 2005 (front-page *Wall Street Journal* coverage, three years before the
   crisis), and it remained standard practice regardless. At most, "a misuse of mathematics...
   partly contributed to the Crisis" (Donnelly & Embrechts 2010) — a known, published flaw that
   stayed in standard use, which is the actually-relevant lesson for this lab, not a claim of
   sole causation.

   Actuarial capital aggregation across risk classes/zones is architecturally the same
   linear-correlation object, and this is now **confirmed directly, not assumed**, at three
   independent frameworks: Solvency II's Basic SCR formula (Directive 2009/138/EC Art. 104 &
   Annex IV — the exact 5x5 correlation matrix is quoted verbatim in
   `research/01_solvency_ii_correlation.md`), A.M. Best's BCAR ("square root rule" covariance
   adjustment — A.M. Best's own methodology document names and critiques its own distortion),
   and S&P's Insurance Capital Model (named correlation matrices across a three-level
   diversification hierarchy — `research/02_rating_agency_capital_models.md`). A genuine bonus
   finding, not anticipated when this plan was first drafted: **S&P's own pre-2023 methodology
   carried Natural Catastrophe risk at a fixed 100% correlation to the overall capital
   charge — zero diversification credit at all** — real-world evidence that cat risk
   specifically gets the coarsest possible linear-correlation treatment in at least one major
   framework, and that the industry itself considers this a simplification worth revising
   (S&P's 2023 proposal relaxes it). This lab is not claiming any specific real cat model
   (RMS/AIR/Verisk-style physical peril simulation is far more sophisticated than a flat
   correlation matrix) makes this exact mistake at the peril-modeling layer — it is targeting
   the separate, confirmed-common capital-*aggregation* layer, and demonstrating, in a
   controlled setting where the ground truth is known, how large the resulting mistake can be.
3. **This is where the OOC engine's actual differentiator is a knockout, not a nicety.**
   A vanilla-scale GP (n ≲ 40k, in-core) is already useful for a mid-size book. A real
   regional insurer's exposure count (tens to hundreds of thousands of policies) is
   squarely in the regime that needed a cluster before `gp_ooc_solver`. If the dollar gap
   this lab measures *grows* with book size — plausible, since more exposures means more
   ways for a flat correlation matrix to misallocate — then scale is not a benchmark
   flex, it is the point.

## Precedent already in this codebase

- `cvar_gp_lab` — full posterior (mean **and** covariance), not a point estimate, feeding a
  Rockafellar-Uryasev CVaR LP (`cvar_lp.py`) via Monte Carlo scenarios sampled from that
  posterior (`scenario_gen_gp.py`). This lab reuses both modules' shape directly: same
  "sample scenarios from the fitted joint posterior, feed a CVaR-family optimizer" pipeline,
  repointed from portfolio weights to a capital/retention decision.
- `bayesian_decision_lab` — the discipline of isolating *which* Bayesian ingredient does the
  work (mean-only vs mean+variance), with a control condition designed so a result can't be
  hand-waved. This lab needs the analogous control: is the win "GP learns the real spatial
  correlation structure" (a fair fight against a smarter flat-correlation baseline) or trivially
  "any correlation beats none" (an unfair fight against pure independence)? Both baselines are
  built for this reason — see Method.
- `gblup_lab/marker_kernel.py` — the GEMM-trick kernel builder, already repointed once
  (asset return descriptors in `cvar_gp_lab/asset_kernel.py`); repointed again here at
  exposure lat/lon + hazard covariates.
- `gp_ooc_fortran.py` / `gp_ooc_solver.cuf` — the out-of-core backend, freshly hardened
  (`F1` buffer-overflow fix, `../README.md`) and the reason a >40k-exposure book is
  tractable on one consumer GPU at all.

## The core hypothesis, stated precisely (so it can be proven wrong)

> A capital or reinsurance-retention decision computed from a **flat or block linear-
> correlation aggregation** of exposure losses will, on a synthetic loss world with
> genuine climate-driven tail dependence, achieve a materially worse *actual* survival
> probability than its stated target — and a GP fit to the same historical sample, feeding
> the same CVaR-style capital calculation, will close a measurable fraction of that gap,
> worth a computable number of dollars at realistic book size.

Two ways this can come back false, and both are reported if they happen, not filed away:
- The naive baseline might already be *conservative enough* by accident (over-correlated,
  not under-) — a real possible outcome depending on calibration, and itself a finding
  worth reporting (the shortcut is wrong in the *other* direction: needless over-capitalization).
- A vanilla GP posterior is **still jointly Gaussian** — same zero-tail-dependence property
  as the naive baseline, just with a better-fitted correlation *shape* (distance-decay,
  hotspots) instead of a flat number. If most of the true tail risk comes from genuine
  nonlinear tail dependence (a shared systemic shock) rather than misallocated-but-still-
  elliptical correlation, vanilla GP may close only part of the gap — Phase 1 is designed
  to measure exactly this split, not to claim GP alone solves tail dependence it structurally
  cannot represent.

## Method

**The oracle (ground truth, known only to the simulator, never to any fitted model).**
A synthetic book of `n` insured properties with location `(lat, lon)`, insured value `V_i`,
and a base (marginal) annual hazard probability from a smooth spatial hazard surface. Annual
losses are generated by a **two-layer process**, chosen specifically to have real, checkable
tail dependence unlike a plain multivariate Gaussian:
1. A latent annual **regime** `R ~ Bernoulli(p_systemic)` — "normal year" vs "correlated
   climate-extreme year" (elevated drought/heat/storm-track conditions). `p_systemic` and the
   regime's hazard multiplier are tunable, calibrated so systemic years are rare but not
   negligible (illustrative starting point: ~1-in-15 years, consistent with how clustered bad
   cat years actually look — exact figure is a knob, not a claim).
2. Conditional on the regime, each property's loss is drawn from its own severity
   distribution, but the regime **shifts every property's hazard simultaneously** and a
   spatial correlation kernel (real, distance-decaying, not flat) governs which properties
   move together within a systemic year. This produces genuine tail dependence: the
   empirical correlation between two nearby properties' losses is measurably higher in the
   worst 1% of years than the "normal-year" correlation — the exact property a Gaussian/flat
   model cannot represent. Phase 0's sanity check is confirming this gap is real and
   sizeable in the simulator before anything is fit to it.

Every model below only ever sees a **finite historical-style sample** drawn from this oracle
(illustrative: 40-60 simulated years of book-level annual losses, in line with how much real
loss-year history actually exists) — never the oracle's true parameters. The oracle itself is
reserved for scoring: given any model's capital/retention decision, resimulate at large `N`
from the true DGP and read off the *actual* achieved survival probability and expected
shortfall.

**Four fitted methods, a ladder of increasing sophistication (isolates what's doing the work,
per `bayesian_decision_lab`'s methodological lesson):**
1. **Independence baseline** — each property's loss distribution fit marginally; portfolio
   loss = sum of independent marginals (CLT-thin tail). The crudest real shortcut, still used
   informally ("just add up the expected losses").
2. **Flat/block correlation baseline** — the actuarial-shortcut stand-in: a single pairwise
   correlation number (or a coarse zone-block matrix) fit to the same historical sample,
   aggregated as a multivariate Gaussian/lognormal. This is the fair fight — it uses
   correlation, just the wrong *shape* of it.
3. **Vanilla spatial GP** — `gp_core.py`/`gp_ooc_fortran.py` fit over the historical sample
   with a kernel built from `spatial_kernel.py` (lat/lon + hazard covariates, repointing
   `marker_kernel.py`'s GEMM trick), full posterior mean **and** covariance, scenarios via
   `scenario_gen_gp.py`'s sampler. Still jointly Gaussian — tests whether *better-shaped*
   correlation alone (vs method 2's flat number) already recovers most of the gap.
4. **GP + regime-mixture** — layers the vanilla GP's fitted spatial correlation *within* a
   two-component mixture over a fitted systemic-regime probability (estimated from the same
   historical sample, not read off the oracle), the same mechanism class as the true DGP.
   Tests whether representing genuine tail dependence, not just spatial shape, is needed to
   close the rest of the gap.

**The decision, and its dollar consequence.** Each method computes required capital (or
reinsurance retention `R`) to meet a fixed target survival probability (illustrative:
99.5%, the Solvency II SCR convention) from its own scenario-implied loss distribution —
same Rockafellar-Uryasev CVaR/TVaR machinery as `cvar_gp_lab/cvar_lp.py`, reformulated as a
capital-sizing problem rather than a portfolio-weight LP. Score every method's decision
against the oracle:
- **Achieved survival probability** — resimulate at the chosen capital level from the true
  DGP; does the method's number actually deliver ~99.5%, or is the true ruin probability
  materially higher (the "terribly wrong" finding, if it appears)?
- **Dollar gap** — expected shortfall in bad years beyond the method's chosen capital
  (under-reserving cost) *or* excess capital held beyond what the true DGP requires
  (over-reserving cost, i.e. reinsurance bought that wasn't needed) — both are real dollar
  costs, in opposite directions, and both get reported.

## Phases

**Phase 0 — the oracle and the sanity check.** `dgp_simulator.py` (regime + spatial-shock
loss generator), `exposures.py` (synthetic book: location, insured value, marginal hazard).
Verify the DGP actually has what it's built to have: empirical tail-dependence coefficient
(correlation among the worst 1% of years vs. all years) measurably `> 0` and larger than a
Gaussian sample with the same average correlation would produce — the one number that
justifies the whole lab existing. Small book (`n` ~ 500-2,000) for fast iteration.

**Phase 1 — the four-way ladder, small scale.** `naive_baselines.py` (methods 1-2),
`spatial_kernel.py` + `gp_loss_model.py` (method 3), the regime-mixture layer (method 4),
`capital_calc.py` (CVaR/TVaR-based capital sizing, reusing `cvar_lp.py`'s math). Fit all
four on one historical-style sample from Phase 0's book, score all four against the oracle.
Headline outputs: the achieved-survival-probability table and the dollar-gap table, plus
whether method 3 (vanilla GP) or only method 4 (regime-mixture) closes most of the gap —
the split that decides whether "just fit a GP" is already most of the fix or whether the
tail-dependence mechanism itself has to be modeled explicitly.

**Phase 2 — scale to where the OOC engine matters, and put a real dollar figure on it.**
Same four-way comparison at a book size calibrated to a real mid-size regional insurer.
The illustrative target (100,000-300,000 policies, mean insured value ~$300-400k,
aggregate insured value in the tens of billions) is only **partially sourced** — say so
explicitly in the writeup, not as a stated fact:
- **$300-400k average insured value** is a reasonably well-anchored consumer benchmark —
  four independent sources (Insurance.com, NerdWallet/Forbes Advisor, Insurify, Forbes
  Advisor) converge on this as the standard dwelling-coverage tier
  (`research/06_book_size_benchmarks.md`).
- **100,000-300,000 policies** is a *conservative lower bound* for "mid-size regional,"
  not a typical figure — a real named regional insurer, Florida Peninsula Holdings Group
  (NAIC 2025 Market Share Report, ranked #21 nationally among homeowners writers), wrote
  ~$1.17B in 2024 homeowners premium, which at the sourced average premium implies roughly
  400,000-470,000 policies for that one insurer alone. State the plan's range as
  deliberately conservative, not as "typical mid-size."
- **"Tens of billions" aggregate insured value** is unsourced derived arithmetic (policies
  × average value), not an independently published figure — label it as such.

Past the ~40k in-core ceiling (`test/README.md`'s measured limit), requiring
`gp_ooc_solver` to fit the joint posterior at all. Report whether the dollar gap grows,
shrinks, or holds with scale (open question, not assumed), and the absolute
capital/reinsurance-cost number at this book size — the figure meant to make "how wrong"
concrete rather than abstract.

**Phase 3 (stretch) — ground the geography in something real.** Swap the synthetic hazard
surface for FEMA National Risk Index county/census-tract-level hazard scores — confirmed
public, actively maintained (December 2025 v1.20), and covering exactly the peril families
this lab models (coastal flood, drought, hurricane, riverine flood, wildfire, wind), in
CSV/Shapefile/Geodatabase via `hazards.fema.gov/nri/data-resources`
(`research/05_fema_nri.md`) — while losses themselves stay synthetic/parametric since real
claims data is proprietary. One open item before treating redistribution as unrestricted:
the explicit license/terms-of-use statement was not read verbatim in this pass (fema.gov
blocked automated fetch); federal-public-domain status is very likely (17 U.S.C. §105,
and the dataset is mirrored on academic archives DataLumos/Harvard Dataverse) but should
be confirmed by reading FEMA's terms-of-use page directly before this phase starts. This
is the same move `porphyry_cu_gpc_lab` made going from `mining_gpc_lab`'s toy dataset to
real USGS geochemistry. Possible further stretch: multi-peril (wildfire + flood) with
cross-peril correlation, since real reinsurance treaties rarely cover one peril in
isolation.

## Files (planned)

- `dgp_simulator.py` — the oracle: regime-mixture + spatial-shock loss generator,
  `sample_true_losses(book, n_years)`.
- `exposures.py` — synthetic book builder (location, insured value, marginal hazard),
  parameterized by `n`.
- `naive_baselines.py` — independence and flat/block-correlation capital estimators.
- `spatial_kernel.py` — repoints `gblup_lab/marker_kernel.py` at exposure lat/lon + hazard
  covariates (same move as `cvar_gp_lab/asset_kernel.py`).
- `gp_loss_model.py` — GP fit via `gp_core.py` (Phase 1) / `gp_ooc_fortran.py` (Phase 2+),
  full posterior mean + covariance.
- `regime_mixture.py` — the fitted (not oracle-read) systemic-regime layer for method 4.
- `capital_calc.py` — CVaR/TVaR-based required-capital / retention solver, adapting
  `cvar_gp_lab/cvar_lp.py`'s Rockafellar-Uryasev formulation.
- `phase0_run.py`, `phase1_run.py`, `phase2_run.py` — one per phase, same convention as
  every prior lab.

## Risks / honest unknowns (stating up front)

- **Everything here is a controlled synthetic world, on purpose.** A positive result
  demonstrates a *mechanism* (linear-correlation aggregation misprices tail risk when the
  truth has regime-driven dependence, by a dollar amount that scales with book size) — it is
  not a measurement of any real insurer's or reinsurer's actual error, and the writeup must
  say so plainly, not imply otherwise.
- **Real catastrophe models are not the flat-correlation strawman.** RMS/AIR/Verisk-style
  peril simulation already models physical hazard footprints, not linear correlation. The
  target of this lab is specifically the capital-*aggregation* layer (diversification-credit
  correlation matrices), which is a real, simpler, and separately-documented practice — not
  a claim that primary cat models are this naive.
- **Vanilla GP is still elliptical/Gaussian.** If Phase 1 shows method 3 barely beats method
  2, that is a real and reportable result (matches `bayesian_decision_lab`'s precedent of
  reporting a hypothesis-contradicting finding plainly) — it would mean the regime-mixture
  layer, not the GP itself, is carrying the fix, and the writeup needs to say that rather
  than crediting "the GP" for work the mixture did.
- **Calibration numbers (systemic-year frequency, severity, correlation decay) are
  illustrative**, the same way `bayesian_decision_lab`'s first loss-matrix draft was — tunable
  parameters, checked for a real effect (Phase 0's tail-dependence sanity check) before any
  headline number depends on them, not treated as ground truth about the real world.
- **No proprietary claims or treaty data used anywhere** — synthetic throughout, Phase 3's
  FEMA NRI upgrade only grounds hazard geography, not losses.
- **The "climate is making it worse" framing is narrower than it first sounds, and the plan
  now says so.** Exposure growth, not climate change, explains most (>80%) of the long-term
  rise in insured cat losses per Swiss Re's own sigma data; the genuine climate-driven
  component this lab leans on is specifically wildfire/regime-driven, not a blanket claim
  about all perils (`research/04_climate_loss_trends.md`). Do not let phase writeups drift
  back to the broader, unsupported version.
- **The 2008-crisis framing is deliberately the softer, peer-reviewed version, not the
  popular one.** "Partly contributed" (Donnelly & Embrechts 2010), not "caused" or "killed
  Wall Street" (Salmon 2009, which the peer-reviewed source explicitly disputes) — this
  distinction matters for the lab's credibility and should not be lost in any summary or
  presentation of this work.
- **FEMA NRI's license terms were not independently confirmed** (see Phase 3) — re-check
  before treating the dataset as unrestricted for redistribution, even though public-domain
  status is very likely.

## Appendix: full research notes

The verification pass run before this plan was finalized is reproduced here in full — not
just referenced — so this document is self-contained. Six claims were checked, each against
primary or near-primary sources, with verbatim quotes and full citations saved
independently in `research/*.md` (unmodified; this appendix is a straight copy for
convenience). The index below is `research/RESEARCH.md`; the six numbered notes follow.

### Index (`research/RESEARCH.md`)

| # | Claim | Verdict | File |
|---|---|---|---|
| 1 | EU regulatory capital (Solvency II) aggregates risk categories via a fixed linear correlation matrix | **CONFIRMED** — primary legal text quoted verbatim | `research/01_solvency_ii_correlation.md` |
| 2 | This is general industry practice, not one regulator's idiosyncrasy | **CONFIRMED** at 2 more independent frameworks (A.M. Best BCAR, S&P Insurance Capital Model) | `research/02_rating_agency_capital_models.md` |
| 3a | Gaussian/linear correlation has zero asymptotic tail dependence | **VERIFIED** — settled mathematics (Sibuya 1960; Embrechts/McNeil/Straumann 2002; restated with proof in Donnelly & Embrechts 2010) | `research/03_gaussian_copula_tail_dependence.md` |
| 3b | The Gaussian copula "caused"/"killed Wall Street" in 2008 | **REJECTED as stated** — peer-reviewed source explicitly disputes this framing; softer "partly contributed" claim is defensible | `research/03_gaussian_copula_tail_dependence.md` |
| 4 | Climate trend is making the loss tail fatter every year (blanket claim) | **REJECTED as stated** — >80% of the long-term increase is exposure growth, not climate (Swiss Re sigma); real climate-driven component only clearly documented for specific perils (NA wildfire, +14%/yr) | `research/04_climate_loss_trends.md` |
| 5 | FEMA National Risk Index is a real, usable public dataset for Phase 3 | **CONFIRMED**, with one open item (license statement not read verbatim — fema.gov blocked direct fetch) | `research/05_fema_nri.md` |
| 6 | "Mid-size regional insurer" ≈ 100k-300k policies, $300-400k avg insured value, tens of billions aggregate | **PARTIALLY SOURCED** — avg insured value well anchored (4 independent consumer-data sources); policy count range is a plausible but conservative lower bound; aggregate figure is unsourced derived arithmetic | `research/06_book_size_benchmarks.md` |

### 1. Solvency II SCR aggregation via fixed linear correlation matrix

**Claim tested:** EU regulatory capital aggregation across risk categories uses a fixed
linear correlation matrix ("square root formula"), not a joint tail-dependence-aware model.

**Verdict: CONFIRMED (primary legal source, verbatim).**

**Primary source:** Directive 2009/138/EC of the European Parliament and of the Council of
25 November 2009 (Solvency II, recast), Article 104 ("Design of the Basic Solvency Capital
Requirement") and Annex IV, point 1. Consolidated/derivative full text consulted via
`https://lexparency.org/eu/32009L0138/ART_104/` (Article 104) and
`https://www.legislation.gov.uk/eudr/2009/138/annex/IV` (Annex IV, point 1 — UK's
retained-EU-law mirror, which reproduces the Directive's Annex text). Corroborating source
for the delegated-regulation-level sub-module formula: EIOPA's own rulebook,
`https://www.eiopa.europa.eu/rulebook/solvency-ii-single-rulebook/article-5784_en` (Article
164 of Commission Delegated Regulation (EU) 2015/35, market-risk sub-module aggregation —
same formula family, one level down). Accessed 2026-07-23 (EUR-Lex's own page did not render
as static text through the fetch tool used, so the UK legislation.gov.uk mirror and
lexparency.org's consolidated text were used instead — both reproduce the same
treaty/annex text, not independent secondary commentary).

**Verbatim aggregation formula (Article 104 / Annex IV point 1):**

> "Basic SCR = √(Σ Corr(i,j) × SCR(i) × SCR(j))"

where `Corr(i,j)` is defined as "the item set out in row i and in column j" of a fixed
correlation matrix, and `SCRi`/`SCRj` range over the five top-level risk modules: SCR
non-life (non-life underwriting), SCR life, SCR health, SCR market, SCR default
(counterparty default). Each module's own capital charge is itself calibrated to a 99.5%
1-year Value-at-Risk.

**Verbatim correlation matrix (Annex IV, point 1):**

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

**Assessment:** This is about as strong as primary-source confirmation gets: an EU
treaty-level Directive, still in force, whose numeric correlation matrix is quoted directly.
It confirms the lab's premise precisely as stated — the EU-wide (not one company's) standard
formula capital regime aggregates risk-category capital charges with a fixed linear
correlation matrix via a square-root (elliptical/quadratic-form) formula, which is
mathematically the same aggregation object as a multivariate Gaussian/elliptical covariance
structure — i.e. it inherits the zero-tail-dependence property this plan attributes to it
(see #3 below). Internal insurers may use full internal models instead of the Standard
Formula, but the Standard Formula (this mechanism) is the default EU-wide regime most
insurers who don't build a regulator-approved internal model actually use.

### 2. Rating-agency capital models — is correlation-matrix aggregation general industry practice?

**Question tested:** linear-correlation-matrix aggregation for insurance capital is
"general industry practice," not one regulator's idiosyncrasy. Checked whether rating-agency
capital models — S&P Global Ratings' Insurance Capital Model and A.M. Best's BCAR —
independently use the same class of method.

**Source 1: A.M. Best, "Understanding Universal BCAR"** (Best's Methodology, Criteria —
Universal). Publisher: A.M. Best Rating Services, Inc.
`https://www3.ambest.com/ambv/ratingmethodology/openpdf.aspx?ubcr=1&ri=999`. Document header
date April 28, 2016; accessed 2026-07-23.

> "A.M. Best's capital formula uses a risk-based capital approach whereby net required
> capital is calculated to support three broad risk categories: investment risk, credit risk
> and underwriting risk. A.M. Best's capital adequacy formula also contains an adjustment for
> covariance, reflecting the assumed statistical independence of the individual components. A
> company's adjusted capital is divided by its net required capital, after the covariance
> adjustment, to determine its BCAR."

> "Collectively, the investment, credit and underwriting risk components generate more than
> 99% of a company's gross required capital... A company's gross required capital, which is
> the sum of the capital required to support all of its risk components, reflects the amount
> of capital needed to support all of those risks if they were to develop simultaneously.
> However, these individual components then are subjected to a covariance calculation within
> the BCAR formula to account for the assumed statistical independence of these components.
> This covariance adjustment essentially says that it is unlikely that all of the individual
> risk components will develop simultaneously, and this adjustment generally reduces a
> company's overall required capital."

> "A.M. Best recognizes the distortions caused by the 'square root rule' covariance
> adjustment, whereby the more capital-intensive risk components are disproportionately
> accentuated while the less capital-intensive risk components are diminished in their
> relative contribution to net required capital. Nevertheless, by using other distinct
> capital measures, A.M. Best can counterbalance this apparent shortcoming."

This is an explicit, named "square root rule" — the same functional form (`sqrt` of a
covariance/correlation-weighted sum of component capital charges) as Solvency II's SCR
aggregation formula, independently arrived at by a different organization for a different
(US/global rating, not EU regulatory) purpose. A.M. Best names its own known weakness (the
square-root rule's distortion of relative risk contribution) — this is not a strawman
description, it's the rating agency's own stated caveat about its own method.

**Source 2: Aon, "Summary of S&P's Proposed Insurer Risk-Based Capital Adequacy Model"**
(June 2023), summarizing S&P Global Ratings' published request-for-comment criteria
documents (S&P's own spglobal.com pages returned HTTP 403 to direct fetch, so this Aon
secondary summary, which quotes S&P's terminology directly, is the source actually used).
`https://www.aon.com/getmedia/91436df9-f3f9-4595-9d0b-bb63f59b600d/20230614-rating-season-sp-capital-criteria-summary.pdf`,
accessed 2026-07-23.

> "The new model is to be calibrated to higher confidence levels, which has led to a general
> increase in the underlying risk charges. However, the proposed changes to correlation
> matrices and overall diversification methodology are likely to offset standalone risk
> increases, depending on an insurer's diversification."

> "Diversification will be allowed for Natural Catastrophe risk where currently it is 100
> percent correlated to the overall capital charge."

> "Diversification: S&P lowered correlations on morbidity and mortality, mortality and
> pandemic, and 'other' non-life risks from those initially proposed."

This directly confirms: (a) S&P's capital model aggregates risk charges via named
correlation matrices, not just a covariance-adjustment euphemism; (b) as of the pre-2023
methodology, natural catastrophe risk specifically was carried at a fixed 100% correlation
to the overall capital charge (the most conservative possible linear-correlation assumption
— no diversification credit at all for Nat Cat) and the 2023 proposal's revision was to
relax that fixed assumption. This is directly on-point for climate_cat_lab: it shows that
the real-world capital-model treatment of catastrophe risk correlation is exactly the
"coarse, assumption-driven number" this lab's naive baseline is modeling, not a strawman.

**Corroborating source: SOA (Society of Actuaries) Financial Reporting Newsletter**
(November 2023), "S&P Global's Revised Capital Model Change Proposal and its Implication to
U.S. Life Insurance Companies."
`https://www.soa.org/sections/financial-reporting/financial-reporting-newsletter/2023/november/fr-2023-11-sun/`,
accessed 2026-07-23. Confirms S&P's model uses a three-level diversification framework
("within business lines between non-life premium risk and reserve risk," "within risk
categories," "between risk categories"), each governed by named correlation factors that
S&P revises between drafts (example: "the correlation factor between mortality and morbidity
risks was lowered from 75 percent to 50 percent"). This corroborates the Aon summary
independently (different publisher, same underlying S&P documents) and confirms the
correlation factors are treated as tunable calibration inputs, not derived from a joint
tail-risk simulation of the actual peril process — consistent with this lab's "flat/block
correlation shortcut" framing.

**Verdict:** Confirmed at 2 independent capital-model frameworks beyond Solvency II — A.M.
Best's BCAR (global, all insurers) and S&P Global Ratings' Insurance Capital Model (used in
credit ratings worldwide) — both aggregate risk-category capital charges via a
covariance/correlation-matrix "square-root formula," structurally the same object as
Solvency II's SCR aggregation. This is not one regulator's idiosyncrasy: it is the dominant
methodological pattern across the three most influential capital-adequacy frameworks in the
(re)insurance industry (one EU regulatory, two rating-agency, covering both US and global
insurers). One caveat: none of these three sources describe using a joint stochastic
simulation with a fitted tail-dependence structure as an alternative or supplement at the
aggregation step (as opposed to peril-level cat models like RMS/AIR, which do simulate
physical hazard footprints — a separate layer, not the capital-aggregation layer this lab
targets). S&P's 2023 proposal's move to relax the 100%-correlation Nat Cat assumption is
worth citing as evidence the industry itself is aware this is a coarse simplification and is
actively revising it — supports, rather than undercuts, the lab's premise.

### 3. Gaussian copula zero tail dependence + its role in the 2008 CDO crisis

**Claim (a): Gaussian copula has zero asymptotic tail dependence — VERIFIED, primary
source.** Catherine Donnelly and Paul Embrechts, "The devil is in the tails: actuarial
mathematics and the subprime mortgage crisis," RiskLab, ETH Zürich, January 4, 2010.
Published in *ASTIN Bulletin* 40(1), pp. 1-33 (2010). PDF (author's own institutional copy):
`https://people.math.ethz.ch/~embrecht/ftp/CD_PE_devil_Jan10.pdf` — fetched and read
directly, 2026-07-23. Section 5.1 ("Inadequate modeling of default clustering"), p.13:

> **Definition 5.1.** Let X and Y be random variables with dfs F and G, respectively. The
> coefficient of upper tail dependence of X and Y is
> λ_u := λ_u(X,Y) := lim_{q→1⁻} P(Y > G^←(q) | X > F^←(q)), provided a limit λ_u ∈ [0,1]
> exists. If λ_u ∈ (0,1] then X and Y are said to show upper tail dependence. If λ_u = 0 then
> X and Y are said to be asymptotically independent in the upper tail.
>
> ... Suppose X and Y have a joint df with Gaussian copula C^gau_ρ. As long as ρ < 1, it
> turns out that the coefficient of upper tail dependence of X and Y equals zero; see McNeil
> et al. (2005, Example 5.32). This means that if we go far enough into the upper tail of the
> joint distribution of X and Y, extreme events appear to occur independently.
>
> Recall that the dependence structure in the Li model is given by the Gaussian copula. The
> asymptotic independence of extreme events for the Gaussian copula carries over to
> asymptotic independence for default times in the Li model... This undesirable property of
> the Gaussian copula is pointed out in Embrechts et al. (2002) and was explicitly mentioned
> in the talk referred to at the beginning of Section 4. A first mathematical proof is to be
> found in Sibuya (1960).

Independent corroboration: Furman, Kuznetsov, Su, Zitikis, "Tail dependence of the Gaussian
copula revisited," arXiv:1607.04736 (2016), Corollary 1(A): "λ_L*(C_ρ) = λ_L(C_ρ) = 0" for
the Gaussian copula when ρ ∈ [0,1), i.e. the lower tail dependence coefficient is zero across
the whole correlation range short of perfect correlation. The original attribution traces to
Embrechts, McNeil & Straumann (2002), "Correlation and Dependence in Risk Management:
Properties and Pitfalls," in Dempster (ed.), *Risk Management: Value at Risk and Beyond*,
Cambridge University Press, pp. 176-223 — full text paywalled and not directly accessed, but
its priority and content are independently confirmed by Donnelly & Embrechts (2010), one of
whose two authors (Embrechts) co-authored the original 2002 paper.

**Verdict: VERIFIED.** Settled mathematics, not a contested industry claim — a named theorem
with a 1960 origin (Sibuya), formalized for finance by Embrechts/McNeil/Straumann (2002), and
restated with full proof sketch above.

**Claim (b): Gaussian copula was widely used for CDO pricing, and is broadly cited as a
contributing factor in 2008 mispricing — PARTIALLY VERIFIED, with an important nuance.**

Industry adoption — verified, stronger than "one company": Donnelly & Embrechts (2010),
Section 5, p.12:

> The advantages of the model meant that it was quickly adopted by industry. For instance,
> by the end of 2004, the three main rating agencies — Fitch Ratings, Moody's and Standard &
> Poor's — had incorporated the model into their rating toolkit. Moreover, it is still
> considered an industry standard.

Popular-press attribution — verified as existing and influential: Felix Salmon, "Recipe for
Disaster: The Formula That Killed Wall Street," *Wired*, February 23, 2009 (Wired cover
story; Salmon won the American Statistical Association's 2010 Excellence in Statistical
Reporting Award for it). Original Wired URL returned 403 on fetch; text confirmed via a
contemporaneous full-text mirror (`srkaufman72.wordpress.com`, 2009-02-25 repost):

> "Armed with Li's formula, Wall Street's quants saw a new world of possibilities. And the
> first thing they did was start creating a huge number of brand-new triple-A securities."
>
> "The Gaussian copula soon became such a universally accepted part of the world's financial
> vocabulary that brokers started quoting prices for bond tranches based on their
> correlations."
>
> "People used the Gaussian copula model to convince themselves they didn't have any risk at
> all, when in fact they just didn't have any risk 99 percent of the time."

**The important nuance:** the more rigorous academic treatment of this same claim explicitly
pushes back on the popular-press framing. Donnelly & Embrechts (2010), p.1-2:

> "'Recipe for disaster: the formula that killed Wall Street'. That was the title of a
> web-article Salmon (2009) that appeared in Wired Magazine... The impression gained is that
> an actuary developed a mathematical model which subsequently caused the downfall of Wall
> Street banks."
>
> "For some of us, the implication that a mathematical model shoulders much of the blame for
> the difficulties on Wall Street and that few people were aware of its limitations are
> untenable. Indeed, we aim to demonstrate that such criticism is entirely unjustified."
>
> "We cannot answer every accusation directed at financial mathematics... It should be
> abundantly clear that it is not mathematics that caused the Crisis. At worst, a misuse of
> mathematics, and we mean mathematics in a broad sense and not just one formula, partly
> contributed to the Crisis."

And, importantly, they document that the model's specific tail-dependence flaw was known and
publicly reported years before the crisis, not discovered in hindsight — the May 2005
Ford/GM downgrade event (p.14) "brought to the attention of market participants in a
dramatic fashion," covered in a front-page 2005 *Wall Street Journal* article (Whitehouse
2005), three years before Salmon's piece. This is a stronger, more defensible version of the
claim for this lab to use than "nobody saw it coming": the tail-dependence blindness of
linear/Gaussian correlation aggregation was understood, demonstrated in a real market event,
and published while the model remained in standard industry use.

**Verdict: PARTIALLY VERIFIED, with required rephrasing.** This plan drops the Salmon
citation as primary support and leans on Donnelly & Embrechts (2010) instead — peer-reviewed,
gives the "partly contributed, not sole cause" framing that is actually more defensible, and
independently confirms three-rating-agency adoption. Not phrased as "the Gaussian copula
caused/killed Wall Street" (the popular framing, explicitly rejected by the peer-reviewed
source) — phrased instead as "a well-documented instance where a linear-correlation
aggregation shortcut's known tail-dependence blindness partly contributed to a systemic
mispricing event, and remained standard industry practice for years after the flaw was
published."

### 4. Are insured natural-catastrophe losses trending structurally upward?

**Claim tested:** "Climate-linked insured losses are trending up structurally, not just
cyclically... climate trend is making the tail fatter every year."

**Verdict: PARTIALLY VERIFIED** — the raw trend is real and well-documented, but the
dominant driver is exposure growth (more property built in harm's way), not a climate signal
alone. Wildfire and North American secondary perils are the clearest case where a genuine
climate-driven component (not just exposure) is explicitly named by a primary source.

**Source 1: NOAA NCEI / Climate Central — "U.S. Billion-Dollar Weather and Climate
Disasters."** Publisher: NOAA National Centers for Environmental Information (data), now
maintained by Climate Central as of 2025-07-28. `https://www.ncei.noaa.gov/access/billions/`.
Dashboard content is JS-rendered and did not yield verbatim quotable text via fetch — figures
below come from search-result summaries of the same dataset, treated as a secondary citation
of a primary dataset, not a verbatim primary quote. Accessed 2026-07-23. Reported figures:
403 billion-dollar disasters since 1980, damage totaling more than $2.9 trillion; average
annual count grew from ~3 events/year in the 1980s to ~20 events/year in the last decade;
2024 total $182.7 billion, 2015-2024 total >$1.4 trillion. Caveat: raw (non-normalized)
dollar totals conflate more/worse weather, more property in harm's way, and inflation — the
dataset itself does not isolate the climate-driven share.

**Source 2: North Carolina Institute for Climate Studies (NCICS), "Billion-Dollar Disasters
Are Happening More Often."** `https://ncics.org/cics-news/billion-dollar-disasters-are-happening-more-often/`,
accessed 2026-07-23.

> "the number of events has generally been increasing over the last two decades" (323 events
> 1980-2021 exceeding $1B each, cumulative >$2.195 trillion inflation-adjusted). "Climate
> change is playing a role in the increasing frequency of some types of extreme weather that
> lead to billion-dollar disasters."

No decade-by-decade breakdown or exposure-vs-climate attribution split was present in the
fetched content.

**Source 3 (the important nuance): Swiss Re Institute, sigma natural catastrophe loss trend
reporting.**
`https://www.swissre.com/press-release/Wildfires-storms-floods-contribute-to-record-92-of-global-insured-losses-in-2025-says-Swiss-Re-Institute/7b39b1a5-b878-4a55-a5ff-bf5aa561a675`,
a primary reinsurance-industry source — directly relevant since Swiss Re is exactly the kind
of institution this lab is modeling. Accessed 2026-07-23.

> "long-term global insurance losses from natural catastrophes continuing to follow the
> 5–7% annual growth rate."
>
> "between 1970 and 2025, exposure growth explains more than 80% of the long-term global
> increase in global weather-related insured losses."
>
> "in some cases, exposure alone no longer explains the speed of loss growth with hazard
> intensification and evolving vulnerability becoming increasingly material in certain
> regions and perils." Specifically for North America: "growth is driven mainly by wildfire
> and SCS [severe convective storms], with wildfire insured losses growing at an annual rate
> of 14%," attributed partly to "the lengthening of fire seasons and long-term changes in
> temperature and precipitation patterns."

**Source 4: the normalized-loss literature (Pielke, Weinkle et al.) — the strongest
counter-nuance.** Found via search, not independently fetched verbatim — flagged as
secondary summary, not a direct quote, weight accordingly. The normalization literature
(adjusting historical losses for population/wealth growth) is contested: one line of work
(Weinkle et al., NOAA/AOML-affiliated) finds normalized US hurricane damage roughly flat over
the 20th century; a competing analysis reportedly finds a statistically significant
+0.6%/year increase in normalized tropical-cyclone damage even after normalization. Both
exist in the literature; this is a live, unresolved academic disagreement, not a settled
fact either way.

**Conclusion:** The defensible claim, backed by a primary reinsurance-industry source (Swiss
Re) rather than an assumption: insured cat losses are rising at ~5-7%/year, but >80% of that
is exposure growth, not climate change — except in specific perils/regions (wildfire, North
American secondary perils) where Swiss Re itself now says exposure growth alone no longer
explains the pace, and names a real climate-linked mechanism (longer fire seasons, changing
precipitation patterns). The broader "climate change is uniformly making all tail risk
fatter every year" is NOT supported by the primary source fetched here, and the
normalized-loss literature is actively contested on this exact question for tropical
cyclones. This plan's "why now" section cites the 5-7%/year figure and the
>80%-exposure-growth caveat, and narrows the "climate is making the tail fatter" claim to
wildfire/North-American secondary perils specifically — which, usefully, is also the peril
this lab's regime-shock mechanism (drought/heat correlating a wildfire season) models most
directly.

### 5. FEMA National Risk Index (NRI)

**Claim under test:** the FEMA National Risk Index is a real, public dataset that can ground
Phase 3's hazard geography in actual data (county/census-tract hazard scores), while losses
themselves stay synthetic.

**Access note on method:** `fema.gov` and `hazards.fema.gov` returned HTTP 403 to the
WebFetch tool used on every URL tried. This looks like a bot/user-agent block on FEMA's
domain, not evidence the resource doesn't exist — WebSearch snippets (crawled directly by
the search index) and independent third-party mirrors corroborate the same facts below, so
the verdict is confirmed via corroborating sources rather than a direct fetch of the primary
domain.

**What it is** (via WebSearch, from FEMA's own indexed page text):

> "The National Risk Index dataset provides information for communities most at risk to 18
> different natural hazards and offers a baseline risk measurement for expected annual loss,
> social vulnerability and community resilience at the Census tract or county level."
>
> "The National Risk Index data leverages available source data for natural hazard and
> community risk factors to develop a baseline risk measurement for each United States county
> and U.S. Census tract. The National Risk Index dataset provides Risk Index scores and
> ratings for counties and Census tracts for all 50 states and the District of Columbia."

Independently, from SparkMap (a public-health data portal citing FEMA directly — fetched
verbatim, `https://sparkmap.org/data-info/climate-health-national-risk-index/`, accessed
2026-07-23):

> "The FEMA National Risk Index 'provides a holistic view of community-level risk nationwide
> by combining multiple hazards with socioeconomic and built environment factors.'"
>
> "The index employs the formula: NRI = Expected Annual Loss × Social Vulnerability × (1 /
> Community Resilience). Expected Annual Loss quantifies projected annual losses to
> buildings, population, and agriculture. Social Vulnerability measures community
> susceptibility to hazard impacts. Community Resilience assesses capacity to prepare, adapt,
> withstand, and recover from natural disasters."
>
> Source citation given: "Federal Emergency Management Agency, National Risk Index, 2023.
> Data sourced from the November 2021 release of the National Risk Index."

**Hazards covered** (18, per SparkMap's citation of FEMA): Avalanche, Coastal Flooding, Cold
Wave, Drought, Earthquake, Hail, Heat Wave, Hurricane, Ice Storm, Landslide, Lightning,
Riverine Flooding, Strong Wind, Tornado, Tsunami, Volcanic Activity, Wildfire, Winter
Weather. Directly relevant to this lab: coastal flood, drought, hurricane, riverine/flood,
wildfire, and wind are all present — the exact peril families this lab's synthetic DGP
models.

**Access method** (via WebSearch):

> "The December 2025 v1.20 data is now available through OpenFEMA as downloadable CSV,
> Geo-database, and Shapefiles."
>
> "Downloads are available at https://hazards.fema.gov/nri/data-resources for Geodatabase,
> Shapefile, and CSV formats."

Corroborated independently by the Data Rescue Project portal (fetched verbatim,
`https://portal.datarescueproject.org/datasets/national-risk-index-nri/`, accessed
2026-07-23), which lists the source agency as "Federal Emergency Management Agency" (DHS)
and confirms "Multiple formats are available: ZIP file, Geodatabase, Shapefile, and CSV,"
with the same `hazards.fema.gov` source and mirrors on DataLumos and Harvard Dataverse — i.e.
this dataset is mirrored by independent academic data-preservation projects, further
evidence it is a real, durable public dataset and not a single fragile government-site
listing.

**License/public-domain status:** not confirmed by direct quote in this pass — no explicit
"public domain" or license statement was captured verbatim from any source fetched. FEMA/DHS
federal datasets are conventionally public domain (17 U.S.C. §105, works of the U.S. federal
government), and the existence of third-party academic mirrors (DataLumos, Harvard Dataverse)
is consistent with that, but this specific claim should be treated as a reasonable inference,
not a verified quote, until the actual FEMA terms-of-use page is read directly (blocked in
this pass).

**Verdict: Confirmed, with one caveat.** The FEMA NRI is a real, actively maintained
(December 2025 v1.20 release referenced), public dataset at county and census-tract
resolution, covering the exact peril families this lab's synthetic DGP targets, in three
standard geospatial/tabular formats via `hazards.fema.gov/nri/data-resources` and OpenFEMA,
with independent academic mirrors. Usable as planned for Phase 3. The one open item is the
explicit license statement, which should be re-checked by reading FEMA's actual terms-of-use
page directly before treating redistribution as unrestricted.

### 6. Book-size benchmarks for Phase 2's "mid-size regional insurer"

**Claim checked:** "a book size calibrated to a real mid-size regional insurer (illustrative
target: 100,000-300,000 policies, mean insured value ~$300-400k, aggregate insured value in
the tens of billions)."

**Verdict: PARTIALLY SOURCED.** No single published report states "a mid-size regional
insurer has 100k-300k policies at $300-400k average insured value." That exact bundled
figure is a constructed illustrative estimate. But each piece is independently anchored to
real published data, and combining them lands in a plausible, defensible range.

**1. Average dwelling coverage amount: $300k-400k is a real, commonly-cited range.**
WebSearch aggregation of consumer-insurance data sites (current as of 2025-2026):

> "The average cost of homeowners insurance in the U.S. is $2,543 a year for $300,000 in
> dwelling coverage" — Insurance.com, "Average home insurance cost in 2026," accessed
> 2026-07-23.
>
> "The average cost of home insurance in the U.S. is $2,720 annually for $350,000 dwelling
> coverage" — NerdWallet/Forbes Advisor aggregation, accessed 2026-07-23.
>
> "In 2025, American homeowners pay an average of $2,927 annually for home insurance that
> provides $350,000 in dwelling coverage with a $1,000 deductible" — Insurify, "Homeowners
> Insurance Facts and Statistics (2026)," accessed 2026-07-23.
>
> "The average cost of homeowners insurance in the U.S. is about $2,490 a year for $400,000
> worth of dwelling coverage" — Forbes Advisor, "The Average Home Insurance Cost 2026,"
> accessed 2026-07-23. "Common coverage limits are between $250,000 and $500,000."

Four independent commercial sources converge on the $300k-$400k range as the standard
benchmark tier — secondary rather than a single regulatory primary source, but reasonably
well sourced.

**2. Regional insurer scale: real anchor found via NAIC 2025 Market Share Report.** NAIC's
2025 Market Share Report (compiled from P&C insurers' NAIC annual-statement State Page
filings), summarized by Agency Checklists, "NAIC 2025 Market Share Report | Top 25
Homeowners' Insurers,"
`https://agencychecklists.com/2025/03/17/naic-2025-market-share-report-top-25-homeowners-insurers-74909/`,
accessed 2026-07-23. Per the search summary: "the industry recorded approximately $1.06
trillion in Direct Premiums Written in 2024" across all P&C lines, with "approximately
97.92% of P&C insurers reporting." Within that report's Top-25 homeowners' list, Florida
Peninsula Holdings Group — explicitly named as a genuine regional (not national) insurer —
ranks #21 nationally:

> "Florida Peninsula Holdings Group's inclusion on the 2024 list reflects the increasing
> role of regional insurers in specialized markets." — ranked #21, $1,171,534,895 in direct
> premiums written (homeowners multi-peril, 2024).

Derived estimate (arithmetic, not a directly published figure): at the ~$2,500-2,900/year
average premium found in §1, $1.17B in direct premiums implies roughly 400,000-470,000
policies for Florida Peninsula alone — a single regional insurer, on the high end of, or
somewhat above, this plan's illustrative 100k-300k range. This suggests the plan's 100k-300k
figure is a plausible but conservative (lower-bound-leaning) estimate for "mid-size
regional" — a real regional insurer already near the top of the national homeowners
rankings sits above it. No policy-count figure was found directly in the NAIC report text
itself — the report reports direct premiums written, not policies in force, so the
400k-470k policy estimate above is derived, not quoted.

**3. What was NOT found.** iii.org's own "Facts and Statistics: Homeowners and Renters
Insurance" page, fetched 2026-07-23, does not contain a national average dwelling-coverage
figure, a national policy-count figure, or a "typical regional insurer size" statistic in
the content retrieved — it has state-level top-10-writer premium rankings and
claim-frequency data (5.3%-5.5% of insured homes had a claim in 2021-2022), neither of which
bears on book size. No single source gives "aggregate insured value" for a regional
insurer's book directly; the "tens of billions" figure in this plan is an unverified
back-of-envelope multiplication (policies × average insured value), not sourced
independently.

**Recommendation applied to Phase 2 above:** state the plan's 100k-300k figure as a
deliberately conservative mid-size estimate, cite Florida Peninsula Holdings Group as a real
comparator implying a policy count above this range at typical per-policy premiums, cite the
$300-400k average dwelling-coverage benchmark to its four sources, and flag "tens of
billions" aggregate insured value as derived arithmetic, not an independently sourced fact.
This keeps the scale defensible without overclaiming a single report states the bundled
number.
