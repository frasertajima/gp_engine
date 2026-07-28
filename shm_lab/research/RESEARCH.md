# Research pass index — shm_lab

Research pass DONE 2026-07-28. Five claims checked against primary/near-primary sources, same
discipline as `climate_cat_lab/research/` and `grid_reserve_lab/research/`. **One claim forced a
real, load-bearing correction to this lab's stated contribution** (claim 3) — folded into
`LAB_PLAN.md` directly, not left in a superseded draft.

| # | Claim | Status | File |
|---|---|---|---|
| 1 | EOV (temperature) causes bigger frequency shifts than typical early damage | VERIFIED (general phenomenon; not yet confirmed specifically for KW51 — Phase 0 task) | `01_environmental_operational_variability.md` |
| 2 | A real classical EOV-correction baseline exists to benchmark against | PARTIALLY VERIFIED — three real methods found (regression, PCA, cointegration); **a regime-switching cointegration method already exists in the literature**, undercutting the claim that regime-awareness itself is novel | `02_classical_eov_correction_methods.md` |
| 3 | GP regression is a novel idea to apply to SHM/EOV removal | **CORRECTED, not confirmed as drafted** — GP regression (including heteroscedastic GP) is already an established, actively-published SHM technique. This lab's honest contribution narrows to testing the specific soft-EM regime-mixture mechanism, not "GP for SHM" generally | `03_gp_already_used_in_shm.md` |
| 4 | KW51 dataset specifics (retrofit reason/dates, sensors, license) | VERIFIED, with one real correction: the retrofit was **due to a construction error found on inspection**, not routine planned work — and the dataset's 15-month window is a slice of a longer (~6-year) real monitoring campaign | `04_kw51_dataset_specifics.md` |
| 5 | Real-world SHM practice status + cost figures for the asymmetric-cost framing | PARTIALLY VERIFIED — real US inspection-practice and real Florida SHM cost figures found ($29,000 scour system; $11,900/pier cathodic protection); no sourced figure yet for the false-negative (missed-damage) cost side | `05_shm_practice_and_cost.md` |

## Net read — how this changes the lab's own framing

The most important finding is claim 3: **this lab is not testing a novel idea (GP for SHM EOV
removal) — that already exists and is published.** Combined with claim 2's finding that
regime-switching cointegration also already exists, the honest, narrowed hypothesis is: does the
*specific* soft-EM regime-mixture mechanism already validated three times in this codebase
(`climate_cat_lab` → `cvar_gp_lab` → `grid_reserve_lab`) perform competitively on this real
dataset and this real intervention event, benchmarked against both a plain classical baseline and
(if time permits) the more sophisticated published alternatives (heteroscedastic GP,
regime-switching cointegration) — not a claim to be inventing regime-awareness or GP-for-SHM from
scratch. `LAB_PLAN.md`'s hypothesis section has been rewritten to say this plainly.

Claim 4's correction (construction defect, not planned upgrade) strengthens the lab's real-world
relevance rather than weakening it — worth keeping, not softening.

Claim 5's gap (no false-negative cost figure) means the economic-layer stretch goal stays
explicitly unconfirmed; the core three-method detection comparison does not depend on it.
