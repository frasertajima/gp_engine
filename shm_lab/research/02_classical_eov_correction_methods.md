# Claim 2: a real, currently-practiced classical baseline exists for EOV correction

**Status: PARTIALLY VERIFIED — three real candidate methods found, no single source confirms which
is "most common in real-world practice" (as opposed to most published-on in academic literature).
This is an important, honest gap: the research pass found what methods EXIST and are studied, not
a survey of which one a working bridge-inspection agency actually runs day to day.**

## Three real, sourced classical methods (not strawmen)

1. **Linear/polynomial regression of frequency (or other damage-sensitive feature) on temperature**
   — the baseline against which every more sophisticated method in this literature is compared,
   including in the Z-24 work itself (Peeters & De Roeck's own follow-on work develops regression-
   based and ARX/ARMAX normalization specifically because a naive fixed-threshold approach without
   temperature correction fails). Treated in this literature as the textbook first-pass approach,
   not as something we are inventing to strawman.
2. **PCA-based EOV removal** — confirmed as a real, published, classical approach (ResearchGate
   record 262601505, "Structural Health Monitoring based on principal component analysis: damage
   detection, localization and classification"). One sourced limitation found directly relevant to
   this lab's framing: "classical PCA and other statistical modelling methods are not applicable
   when data is nonstationary because the statistical properties of nonstationary variables are
   time-variant" — i.e. PCA's own literature already documents its EOV-tracking limitation, which
   is the same shape of gap this lab's regime-mixture hypothesis targets.
3. **Cointegration** — confirmed as a real, actively-published method specifically for this problem
   (Cross, E. J. and coauthors; ScienceDirect records S0263224123000672 and S0888327017305411,
   "A regime-switching cointegration approach for removing environmental and operational variations
   in structural health monitoring"). Definition, quoted: "cointegration is defined as the
   stationary linear combination of two or more nonstationary time series, meaning the time series
   can be represented to have a stable relationship known as a long-term equilibrium... the effects
   of environmental temperature and humidity on frequency can be eliminated by cointegration
   equations."

## An important, honest complication found directly relevant to this lab's own hypothesis

A **"regime-switching cointegration"** method already exists in the published literature
(ScienceDirect S0263224123002464 and S0888327017305411) — i.e. **someone has already published a
regime-aware extension to a classical EOV-correction method**, for essentially the same reason this
lab's soft-EM regime-mixture layer is being proposed: "conventional techniques like PCA and
cointegration have been somewhat effective, [but] challenges such as measurement noise, nonlinear
behavior, and non-Gaussian data distribution continue to affect their performance," and the
regime-switching variant "transform[s] nonlinear relationships between damage features into
piecewise linear relationships by choosing an appropriate switching temperature point."

**This must be stated honestly in `LAB_PLAN.md`, not glossed over**: this lab's premise (a
regime-aware model beats a single-relationship classical baseline) is not a novel idea in the SHM
literature in the abstract — regime-switching cointegration already exists and targets the same
gap. This lab's specific, narrower contribution is testing whether the **GP soft-EM** mechanism
already proven in three prior labs in this codebase family provides the same or better benefit,
ported to this domain and this specific real dataset (KW51) — not a claim of being the first to
notice classical single-relationship EOV correction has regime-dependent blind spots.

## What is still NOT sourced

Which of the three (plain regression, PCA, cointegration) is the field's actual most-common
real-world default, as opposed to most-published-about, was not established. Given FDOT's own
practitioner-level description (`research/05_shm_practice_and_cost.md`) that full-scale permanent
SHM is "sparingly used" and most routine bridge condition assessment in practice is still visual
inspection (not any signal-processing method at all), the honest framing to adopt is: **the
classical baseline this lab benchmarks against is a real, published, textbook-standard method
within the SHM signal-processing literature (regression is the simplest and most universally cited
starting point) — not necessarily "the" universally-deployed real-world practice**, since much of
real bridge condition assessment doesn't use vibration-based EOV correction of any kind yet.
