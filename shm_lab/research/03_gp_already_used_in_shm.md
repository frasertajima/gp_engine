# Claim 3: is GP regression already a known/used technique for EOV removal in SHM?

**Status: VERIFIED — yes, unambiguously. This is the single most important correction from this
research pass and must reframe this lab's stated contribution.**

Multiple independent, real, published sources confirm GP regression is an established (not novel)
tool in this specific sub-field:

- Teimouri, Milani, Loeppky, Seethaler (2017), "A Gaussian process-based approach to cope with
  uncertainty in structural health monitoring," *Structural Health Monitoring* (DOI
  10.1177/1475921716669722) — a GP-based approach to SHM uncertainty, published nearly a decade
  before this lab.
- "Exploring Environmental and Operational Variations in SHM Data Using Heteroscedastic Gaussian
  Processes" (Springer, `978-3-319-29751-4_15`) — explicitly a **two-stage procedure using
  heteroscedastic Gaussian processes to remove EOV**, i.e. almost exactly this lab's stated Method
  1 (vanilla spatial GP over temperature), already done, published, and using a *more* sophisticated
  GP variant (heteroscedastic, meaning input-dependent noise) than this lab's plain draft method.
- "A Gaussian process form for population-based structural health monitoring" (ResearchGate
  334250549) — GP used to build a *population* model across nominally-identical structures for
  novelty detection, a further-developed direction than this lab's single-structure scope.
- Worden and colleagues are directly confirmed (across multiple independent hits) as a
  long-standing contributing research group specifically on GP-for-SHM and novelty detection —
  this is not a fringe or obscure application of GPs.
- A 2025 paper (Advances in Bridge Engineering, `10.1186/s43251-025-00169-1`) on GP-regression-based
  missing-data imputation for bridge SHM confirms the technique remains an active, current research
  area, not a one-off historical curiosity.

## Why this matters — a real correction to this lab's framing, not a footnote

Every prior lab in this family (`climate_cat_lab`, `cvar_gp_lab`, `grid_reserve_lab`) could
honestly frame "vanilla spatial GP" as a genuinely untested-in-that-domain idea, with the
soft-EM regime-mixture layer as the second, larger contribution on top. **That framing does NOT
hold here.** GP regression for EOV removal in SHM is an established, actively-published technique
— this lab's vanilla-GP rung (Method 1 in the current draft ladder) is reproducing known prior art,
not testing something new. Combined with `research/02_classical_eov_correction_methods.md`'s
finding that a **regime-switching cointegration** method already exists for the same
regime-awareness idea, this lab's genuinely novel-to-the-literature contribution narrows to a
specific, honest claim:

> **Does the specific soft-EM regime-mixture mechanism this codebase has already validated three
> times (climate risk, portfolio CVaR, grid reserves) transfer to this domain and this real
> dataset — not "is GP or regime-awareness a good idea for SHM" (both already established), but
> "does this particular implementation, on this particular real intervention event, perform
> competitively with or better than the published alternatives (heteroscedastic GP, regime-
> switching cointegration)."**

This is a narrower, more honest claim than the lab's first draft implied, and `LAB_PLAN.md`'s
hypothesis section must be corrected to say so plainly — the same discipline `grid_reserve_lab`
applied when its research pass found real ISO practice already uses historical correlation, not
independence, and narrowed its own claim accordingly.
