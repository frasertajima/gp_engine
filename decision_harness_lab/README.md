# decision_harness_lab — a generic decision harness on top of decision.py, and does outcome shape carry information?

**Status:** Phase 0 DONE (2026-08-06) — `expected_value_nstate`/`bayes_action_nstate`/
`realized_value_nstate`/`oracle_value_nstate` added to `../decision.py`, fully additive (existing
2-state functions and every prior lab's call sites unchanged); k=2 parity self-test plus a genuine
k=3 smoke test both pass. **Phase 1 DONE (2026-08-06)** — `harness.py`'s `Action`/`Decision`
dataclasses and `simulate`/`summarize`/`check_against_closed_form` Monte Carlo engine, validated on
its own self-test and on all three `toy_examples/` (Monte Carlo mean within tolerance of
`decision.py`'s closed-form `expected_value_nstate` in every case, best-action agreement exact in
every case — see "Phase 1 result" below). **Phase 2 DONE (2026-08-06)** — `viz.py`'s
`plot_outcome_distributions`/`plot_outcome_cdf`/`plot_risk_return`/`summary_markdown_table`,
`build_notebook.py` → `DECISION_HARNESS_LAB.ipynb`, executed end to end (0 errors, 9 images render).
See "Phase 2 result" below for the concrete "shape matters" finding this lab set out to check.
**Phase 2.5 DONE (2026-08-06)** — `shape_diagnostics.py` (`count_modes_kde`, `count_modes_by_mass`,
`separation_ratio_from_samples`) and `OUTCOME_SHAPE_TAXONOMY.md`: a taxonomy of outcome shapes,
their generative mechanisms, and which ones are actually GP-soft-EM candidates, grounded in real
diagnostic numbers run against this lab's own toy examples (not asserted from the charts alone).
**Real methodological finding along the way**: a naive height-based mode counter misses
`self_insure`'s rare disaster cluster entirely (its KDE peak is too short, even though it holds real
8% probability mass) — a mass-based counter was added specifically because of this, see
`OUTCOME_SHAPE_TAXONOMY.md`'s "Diagnostics used" section for the full account.

**One line:** every prior decision lab in this codebase (`bayesian_decision_lab`,
`porphyry_cu_gpc_lab`, `home_energy_lab`, `grid_reserve_lab`) compared *point* expected values —
one number per action. This lab asks a narrower, prerequisite question first: before wiring in a GP
soft-EM regime posterior anywhere, does simulating and *looking at the shape* of each action's
outcome distribution surface anything a scalar EV comparison hides? Answered on synthetic toy data
only — no GP, no real dataset, see "Risks" for exactly what that does and doesn't establish.

## Why this lab, and why now

Fraser's framing (session transcript, 2026-08-06): after `home_energy_lab`'s dispatch-policy value
being swamped by capital costs, and an EV-trip-optimizer idea that turned out to need a real
telemetry dataset before any GP work could even start, the next idea was a *generic* decision-making
harness — an array of choices, costs, and outcomes, Monte Carlo simulation, and eventually a GP
soft-EM posterior feeding the state probabilities — starting with toy examples specifically to see
whether the *shape* of the simulated outcome distributions (not just their means) reveals structure
worth building on. This lab is exactly that first step, deliberately scoped to stop before any GP
work: build the generic harness, prove it's correct against the existing decision core, and check
whether shape visualization earns its keep on cases designed to have different shapes.

## Precedent already in this codebase

`../decision.py`/`../voi.py` already generalize once (`bayesian_decision_lab` → shared engine-level
modules, see that lab's `LAB_PLAN.md` "Moved out of this lab" note) — a 3-action, 2-state Bayes
decision core reused verbatim by four labs since. This lab is the same move one level further:
generalizing 2 states to *k* states (additively, in `decision.py` itself) and adding a Monte Carlo
outcome-simulation layer no prior lab has needed, because every prior lab's payoff was a fixed
constant per (action, state) cell — never a *distribution* to be visualized.

## Data and models

**None — by design.** Every `toy_examples/` decision is synthetic, built around a hand-specified
analytic payoff matrix `V[action, state]` and a hand-specified state prior, with noise distributions
chosen to produce a specific outcome shape (multi-lump, bimodal, right-skewed) rather than fit to any
real data. This is the correct scope for Phase 0-2 (validate the harness mechanism), and explicitly
the *wrong* scope for demonstrating GP soft-EM's value (see "Risks" — that has never once come from
synthetic-only data in this codebase).

## Method

**The generalization** (`../decision.py`): `expected_value_nstate(p, V)` computes `p @ V.T` for `p`
an `(n, k)` categorical state-probability array and `V` an `(n_actions, k)` payoff matrix —
`expected_value`'s `(1-p)*V[:,0] + p*V[:,1]` is exactly the `k=2` special case, checked directly by a
self-test that both must agree bit-for-bit at `k=2`. `bayes_action_nstate`, `realized_value_nstate`,
`oracle_value_nstate` generalize the remaining three the same way.

**The harness** (`harness.py`): `Action(name, outcome_fn)` where `outcome_fn(rng, n, state_idx) ->
(n,) ndarray` is a plain callable, not a schema — so a toy example can express any distribution
(Gaussian, lognormal, a state-dependent mixture) without a new DSL. `Decision(name, actions,
state_names, state_prior, V=None)` holds an optional analytic `V` used only for the closed-form
cross-check. `simulate(decision, n_draws, rng)` draws one shared latent state per trial (`rng.choice`
on `state_prior`) and samples every action's outcome conditioned on that *same* draw — a fair paired
comparison, not independent Monte Carlo worlds per action. `summarize` reduces the raw draws to
mean/std/P5/P50/P95/P(loss)/CVaR-5% per action. `check_against_closed_form` compares the Monte Carlo
mean against `expected_value_nstate`'s analytic answer (tolerance `atol + rtol*|closed_form|`, so a
near-zero closed-form EV like "skip" doesn't blow up a relative error) and confirms the harness's
best-by-mean action matches `bayes_action_nstate`'s pick exactly.

**The three toy examples**, chosen specifically to produce three different shapes:
1. **`newsvendor`** — order-quantity decision, 3 imbalanced demand states (50/35/15), demand
   deterministic within a state (small independent price/cost noise only) — shape comes from the
   discrete states themselves, expect a multi-lumped histogram.
2. **`insure_vs_self_insure`** — buy-insurance vs. self-insure against a rare catastrophic loss, 2
   states (92% no-disaster / 8% disaster — the same rare/imbalanced shape `../PLAN.md` section 7's
   soft-EM litmus test requires of a regime). `self_insure`'s outcome is genuinely bimodal.
3. **`invest_decision`** — conservative vs. aggressive allocation, 2 roughly balanced states
   (45/55), aggressive's bull-state noise is a zero-mean-shifted lognormal (right-skewed) — a third,
   distinct shape.

## Phases

**Phase 0 — the nstate generalization.** DONE. `../decision.py` additions + self-test (k=2 parity,
genuine k=3 smoke test with a hand-built 3-action/3-state payoff matrix, oracle-dominance invariant
checked directly, not assumed).

**Phase 1 — the Monte Carlo harness + toy examples.** DONE, see "Phase 1 result" below.

## Phase 1 result (2026-08-06)

All three toy examples' Monte Carlo means matched `decision.py`'s closed-form
`expected_value_nstate` within `atol=0.02, rtol=0.05` at `n_draws=200,000`, and the harness's
best-by-mean action matched `bayes_action_nstate`'s pick exactly in every case:

| toy example | winning action (both MC and closed-form agree) | MC EV | closed-form EV |
|---|---|---|---|
| newsvendor | order_medium | 224.51 | 225.00 |
| insure_vs_self_insure | buy_insurance | -5,080.72 | -5,080.00 |
| invest_decision | aggressive | 3,158.43 | 3,150.00 |

(exact numbers as printed by `DECISION_HARNESS_LAB.ipynb`'s own executed run, single shared `rng`
across all three examples in sequence — not independently reseeded per example, so these will not
exactly match a standalone `python3 toy_examples/insure_vs_self_insure.py` run's numbers, which reseeds
`rng` fresh; both converge to the same closed-form EV regardless.)

The Monte Carlo layer is verified against the shared decision core, not just plausible-looking —
exactly the discipline `check_against_closed_form` exists to enforce before any chart is trusted.

**Phase 2 — visualization + notebook.** DONE, see "Phase 2 result" below.

## Phase 2 result (2026-08-06)

`viz.py`'s three chart types (`plot_outcome_distributions`, `plot_outcome_cdf`, `plot_risk_return`)
render correctly for all three toy examples in `DECISION_HARNESS_LAB.ipynb` (`jupyter nbconvert
--execute`, 0 errors, 9 images). The concrete "does shape matter" finding, per example:

- **newsvendor**: the histogram is visibly multi-lumped (up to 3 separated peaks per action,
  matching the 3 discrete demand states) — a shape a mean/std pair alone would never suggest.
- **insure_vs_self_insure**: `self_insure`'s outcome is visibly bimodal on a symlog x-axis (needed —
  on a linear axis the near-$0 cluster is invisible next to the -$200k tail, a real charting finding
  in its own right, not just a data one). The CDF makes this sharpest: a long, nearly flat plateau
  (the rare disaster tail) followed by a sharp rise through $0 (the common no-disaster outcome) — the
  textbook shape of a rare/imbalanced latent regime. `buy_insurance` wins on mean (-5,081 vs
  -16,168 in the executed run), but `self_insure`'s CVaR-5% (-212,386) and P(loss) (54.1%) are
  nowhere in that mean comparison.
- **invest_decision**: `aggressive`'s histogram is asymmetric and noticeably wider than
  `conservative`'s near-Gaussian one, with a visible right-skew consistent with the lognormal
  bull-state noise it was built from — `aggressive` wins on mean (3,158 vs 2,551) despite carrying
  real bear-state loss risk (P(loss)=44.7%, CVaR-5%=-6,552) `conservative` (P(loss)=0.0%) doesn't.

**Answering the motivating question directly**: yes, on this synthetic evidence, shape visualization
surfaces real structure a scalar EV table hides — but *which* structure differs by example (discrete
multimodality vs. bimodal regime-mixture vs. continuous skew), and only the bimodal case
(`insure_vs_self_insure`, by construction) resembles the specific kind of shape a GP soft-EM regime
posterior is built to model. That's a designed-in result of this lab's own toy-example choices, not
independent evidence that soft-EM would help here — see "Risks" below before reading it as more than
that.

## Risks / honest unknowns

- **This lab used engineered toy examples, not real data — it cannot and does not claim GP soft-EM
  would help on any real decision.** `insure_vs_self_insure`'s bimodality is real in the sense that
  the code that produced it is inspectable, but the shape was *chosen* to be bimodal, not discovered
  in a real historical sample the way `grid_reserve_lab`'s regime or `climate_cat_lab`'s storm years
  were. Every prior convincing result in `../PLAN.md` section 7 came from real, recurring data —
  extending this harness to a soft-EM application requires picking one such real domain first and
  checking it against that litmus test (regime recurs many times, regime is rare/imbalanced), not
  assuming the toy result generalizes.
- **The symlog x-axis needed for `insure_vs_self_insure`'s chart is itself a finding worth
  remembering**: a >100x scale difference between clusters silently defeats a plain linear-axis
  histogram (the near-$0 cluster was genuinely invisible before `xscale="symlog"` was added) — a real
  charting failure mode, flagged here so a future real-data version of this chart doesn't quietly
  hide its own most important cluster.
- **`check_against_closed_form`'s tolerance (`atol=0.02, rtol=0.05`) is a Monte Carlo sampling-noise
  budget, not a correctness proof** — it passed at `n_draws=200,000` for all three examples here; a
  future toy example with a much higher-variance outcome (e.g. a heavier tail than
  `insure_vs_self_insure`'s) could need more draws or a looser tolerance to pass reliably.
- **The `V`/`outcome_fn` pairing in each toy example is hand-verified, not automatically checked**
  beyond the Monte Carlo cross-check itself — an author error in either (e.g. a noise distribution
  whose true mean doesn't match its `V` cell) would show up as `check_against_closed_form` failing,
  but only at the specific `n_draws` and states actually run.

## Structure

```
decision_harness_lab/
  LAB_PLAN.md                  this file
  harness.py                   DONE -- Action/Decision, simulate/summarize/check_against_closed_form,
                                self-test
  viz.py                       DONE -- plot_outcome_distributions/plot_outcome_cdf/plot_risk_return/
                                summary_markdown_table, house palette (viz.apply_house_style)
  toy_examples/
    newsvendor.py               DONE
    insure_vs_self_insure.py    DONE
    invest_decision.py          DONE
  build_notebook.py             DONE -- assembles DECISION_HARNESS_LAB.ipynb via nbformat
  DECISION_HARNESS_LAB.ipynb    DONE -- executed, 0 errors, 9 images render
  shape_diagnostics.py          DONE -- count_modes_kde/count_modes_by_mass/
                                separation_ratio_from_samples, self-test prints real numbers for
                                all three toy examples
  OUTCOME_SHAPE_TAXONOMY.md     DONE -- the shape taxonomy, its generative mechanisms, and the
                                Phase 3 readiness checklist
  results/                      (empty -- no results/*.json convention needed yet; every number in
                                this lab is cheap enough to recompute live in the notebook)
```

**Engine dependency**: `../decision.py` gained four new, additive functions
(`expected_value_nstate`, `bayes_action_nstate`, `realized_value_nstate`, `oracle_value_nstate`) —
every existing lab's call sites (`bayesian_decision_lab`, `porphyry_cu_gpc_lab`, `home_energy_lab`,
`grid_reserve_lab`) are untouched and still pass their own tests unchanged. `../voi.py` was not
touched — this lab has no sequential/Probe-style action yet (every toy example is single-shot
Skip/Drill-style), so there was nothing to extend there.

**Phase 3 (not started, explicitly out of scope for this lab)**: pick one real, recurring decision
domain, run `OUTCOME_SHAPE_TAXONOMY.md`'s Phase 3 readiness checklist against its real historical
data (not just this lab's synthetic examples), and swap that domain's `Decision.state_prior` for a
fitted GPC's `(mean, var, prob)` posterior — the seam `harness.py`'s module docstring already
documents. Not attempted here; this lab's job was to get the generic harness and its shape
diagnostics right first.
