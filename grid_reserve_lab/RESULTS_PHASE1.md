# Phase 1 results — the five-method ladder, small scale, both languages

**Status: DONE (2026-07-27).** `phase1_run.py` / `results_phase1.json`. Same 100-site fleet as
Phase 0 (seed 0). Historical fit sample: 730 days (~2 years, 42 drought days) — a plausible amount
of daily fleet history a real operator might actually have. Oracle scoring sample: 500,000 days.
Target reliability: 0.999726 (the 0.1-days/year LOLE convention, translated to a daily rate,
`research/01_nerc_lole_reserve_standard.md`). True required reserve at that target, read directly
off the oracle: **5,059.8 MW**.

## Headline scorecard

| Method | Reserve (MW) | Achieved reliability | Under-cost ($/yr) | Over-cost ($/yr) | Net gap ($/yr) |
|---|---|---|---|---|---|
| 0 — ERCOT N-1 (largest unit) | 571.0 | 2.9% | $27.4B | $0 | $27.4B |
| 0 — generic "5% of wind" | 728.5 | 34.5% | $17.1B | $0 | $17.1B |
| 1 — Independence (control only) | 1,478.7 | 93.6% | $8.6B | $0 | $8.6B |
| **2 — Aggregate correlation (real ISO practice)** | 3,047.3 | 96.3% | $2.2B | $0 | $2.2B |
| 3 — Vanilla spatial GP | 2,644.1 | 95.3% | $3.5B | $0 | $3.5B |
| **4 — GP + soft-EM regime-mixture** | 5,925.2 | ≥99.9998%* | ~$0 | $104M | $104M |

\* Zero exceedances observed in 500,000 oracle days — at that sample size, reliability can't be
resolved finer than ~1/500,000 = 0.0002%, so this is a lower bound, not a literal claim of exactly
100%. It comfortably clears the 99.9726% target either way.

Dollar figures use ERCOT's current VOLL ($35,000/MWh, `research/06_voll_and_reserve_cost.md`) and
PJM's 2026/27 cleared capacity price (≈$120,150/MW-year) per `reserve_calc.py`'s constants, with a
Phase-1 simplification stated plainly in that module: a violation day's excess MW is costed as a
6-hour event (a rough middle-of-the-road figure against `research/04_dunkelflaute.md`'s real event
durations — ERCOT's worst logged wind-drought event was 15 hours) — not a calibrated figure, and
Phase 2 should replace it with real hourly EIA-930 data. At the historical low end of ERCOT's VOLL
range ($9,000/MWh, a straight linear rescale since under-cost is linear in VOLL), every under-cost
figure above scales down by 9/35 (e.g. method 2's $2.2B becomes ~$563M) — the dollar *magnitude* is
sensitive to this assumption, but the *ranking* of methods is not, since VOLL multiplies every
method's under-cost by the same factor.

## The central finding, reported plainly either way it came out

**Method 3 (vanilla spatial GP) does not beat Method 2 (the real-practice aggregate-correlation
baseline) — it does slightly worse** (95.3% vs. 96.3% achieved reliability, $3.5B vs. $2.2B net
gap). This is a genuine, hypothesis-relevant result, not a bug: LAB_PLAN.md's Risks section flagged
this exact possibility going in ("vanilla GP is still elliptical/Gaussian... may close only part of
the gap"), and here it closes *none* of it — a smooth distance-decaying spatial kernel, fit on only
730 historical days, evidently isn't a better bet than a single well-estimated fleet-wide
correlation number for this particular oracle and sample size. Only **Method 4 (GP + soft-EM
regime-mixture)** — which explicitly represents the same two-layer mechanism class as the true DGP,
a fitted rare-event regime rather than a smooth spatial-only correlation shape — closes the gap to
target. This mirrors `climate_cat_lab`'s own finding almost exactly (there, method 3 barely beat
method 2, 93.30% vs. 93.29%): **representing genuine regime-driven tail dependence, not just a
better-shaped elliptical correlation, is what the reserve-sizing decision actually needs.**

Method 4 also isn't perfectly calibrated — it over-procures by ~17% (5,925 MW vs. the true 5,059.8
MW), costing ~$104M/year in excess capacity. That is a real, reportable imperfection, but it is a
dramatically cheaper kind of mistake than every other method's under-procurement (the next-best,
Method 2, still carries a $2.2B/year gap) — the asymmetry LAB_PLAN.md's dollar-gap framing exists to
surface.

## An honest caveat on Method 0 (deliberately surfaced, not buried)

ERCOT's real N-1 "largest single in-service unit" rule and the generic "5% of wind capacity" rule
are being asked here to cover a risk they were never designed for: correlated, weather-driven,
fleet-wide renewable output shortfall, not a single generator/equipment contingency (N-1's actual
job) or a coarse sizing heuristic for ancillary services broadly. Their catastrophic-looking
scorecard numbers (2.9%/34.5% achieved reliability) are not evidence that ERCOT is under-reserved in
real life — ERCOT's actual reserve product mix includes ORDC-based scarcity pricing and other
mechanisms this lab does not model. What this *does* show is the raw magnitude of the gap between
"a rule sized for a different risk" and "a rule sized for this one" — useful context for why
resource-adequacy studies moved toward statistical methods (methods 1-2) at all, not a claim about
any real utility's current reliability.

## Rust benchmark

The `reserve_baseline` Rust crate (methods 0-2, rayon-parallel Monte Carlo) vs. a vectorized NumPy
reference at 500,000 scenarios:

| Method | Rust | NumPy | Speedup |
|---|---|---|---|
| 1 (independence) | 31.2ms | 1,081ms | **34.6x** |
| 2 (aggregate correlation) | 29.7ms | 1,371ms | **46.2x** |

(Subprocess call overhead, including JSON I/O, adds ~32ms on top of Rust's own compute time — still
over an order of magnitude faster than the NumPy reference even counting that.) This confirms
LAB_PLAN.md's fairness premise: the traditional methods' large dollar-gap loss in the scorecard
above isn't an artifact of them being handicapped on speed — they're both fast and wrong, which is a
stronger result than slow-and-wrong would have been.

## Not yet done

- **VOLL/reserve-cost sensitivity sweep** — only a linear rescale noted above, not a full sweep
  across the historical VOLL band or PJM-vs-MISO capacity-cost figures, as LAB_PLAN.md calls for.
- **Real geography/data** — this fleet and its drought mechanism remain entirely synthetic; Phase 2
  grounds both in real NREL WIND Toolkit/EIA-930 data at a scale requiring `gp_ooc_fortran.py`.
- **Hourly (not daily) event dynamics** — the 6-hour event-duration assumption in the dollar
  conversion is a stated Phase-1 simplification, to be replaced once real hourly data is in hand.
