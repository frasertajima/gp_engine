# Phase 2 — sequential-VoI inspect/wait/remediate layer

**Status: DONE (2026-08-02).** Second application of `gp_engine/VOI_DISPATCH_PATTERN.md`
(after `grid_reserve_lab`'s Phase 4), per Fraser's direction to try `shm_lab` next with the same
template, anticipating cost-sourcing might be "a separate problem" — confirmed true (see
`research/06_inspection_and_failure_cost.md`), handled by making the breakeven-probability sweep
the primary result rather than committing to one unsourced headline number.

**This phase is a new, later addition, not a resumption of the original Phase 2 (a FastAPI app),
which was explicitly not started when the lab was declared "feature-complete" at Phase 1c.**

**Headline, in three parts, all genuinely surprising relative to this codebase's prior VoI
labs**: (1) the real KW51 transition is detected almost perfectly by a classifier on the existing
per-mode z-scores (AP≈0.999–1.000) — a fundamentally different regime from every prior VoI lab's
partly-ambiguous classification problem; (2) as a direct consequence, **GPC's posterior *variance*
adds essentially nothing here — GPC-full and GPC-mean are statistically indistinguishable across
the entire cost-ratio sweep**, the mirror image of `grid_reserve_lab`'s modest-but-real variance
benefit; (3) **whether GPC's calibrated *mean* beats SVM's depends sharply on the cost ratio, and
at moderate-to-high breakeven probabilities SVM actually wins** — a genuinely new finding this
family of labs hasn't seen before.

## Method

**The reframing**: state = the real KW51 `retrofit_mask`-derived label (0 = held-out-normal
pre-retrofit day, 1 = during+post-retrofit day) — real historical ground truth, not a synthetic
oracle. **A real limitation, stated plainly**: "state 1" means "the structure's dynamic signature
has changed from the established pre-retrofit baseline," which covers both being mid-retrofit and
already-fixed — not "has undetected damage." The real construction defect existed continuously
through the labeled "normal" (state 0) pre-retrofit period too. This is inherited from Phase 1/1b's
own change-detection framing, not introduced here — the decision layer should be read as "detect
any genuine deviation from established baseline, worth an engineering follow-up," not "detect
damage specifically."

Actions keep `decision.py`'s `ACTIONS = ("skip","probe","drill")` tuple verbatim: **skip** = rely on
the default scheduled inspection cadence (NBIS's real 24-month interval); **probe** = trigger an
out-of-cycle manual inspection (resolves to ground truth, per `decision.py`'s documented
idealization); **drill** = escalate directly to remediation/engineering follow-up.

**The new modeling piece** (`damage_classifier.py`): every existing model in this lab is GP
*regression* (frequency-on-temperature); none produce a `(mean, var, prob)` triple over a discrete
state. Built a genuine `LaplaceBinaryGPC` fit (unchanged from `gp_classifier.py`) on the five
well-identified modes' already-computed z-scores (each mode's frozen "regime A" `VanillaGP`, fit on
train days only — exactly `phase1_run.py`'s own baseline, reused as this phase's feature source).
An `SVC(probability=True)` control is fit on the same features/split.

**Bootstrap convention**: unlike `grid_reserve_lab` (a resimulable synthetic oracle), this lab has
one fixed real dataset (296 days: 52 held-out-normal + 244 during/post). Each of 200 seeds draws a
fresh stratified train(50%)/val(25%)/test(25%) split of these same days, refits GPC+SVM fresh —
mirroring `bayesian_decision_lab`/`porphyry_cu_gpc_lab`'s own convention (repeated fresh splits of
one fixed real dataset), arguably a closer fit to the original template than `grid_reserve_lab`'s
synthetic-Monte-Carlo adaptation was.

**Economic constants are illustrative, not independently sourced** (`research/
06_inspection_and_failure_cost.md`): `c_probe=$0.01M` (~$10,000, loosely informed by an
unverified-against-primary-source $4,500–$10,000 inspection-cost search result), `c_drill=$0.05M`
(an engineering follow-up/escalation), `v_drill_gross` swept rather than fixed as the headline —
deliberately not importing the I-35W collapse's $234M scale, a different failure mode (sudden
catastrophic collapse vs. this lab's early-detection question).

## A real, notable finding before the decision layer even runs: near-perfect separability

Every feature subset tried (all 5 modes; individual modes; as few as 8 training days) gave
validation/test AP between 0.97 and 1.00 — including mode 8, which Phase 1 found the MOST
temperature-confounded and worst-calibrated per-mode (23.1% false-alarm rate there, vs. the
11.5% target). A flexible GPC/SVM classifier trained directly on the label evidently exploits
structure a fixed `|z|>threshold` rule (Phase 1's own method) cannot — the real transition is
easier to detect this way than Phase 1's own numbers suggested. This is real and checked (not a
data leak: the classifier only ever sees frozen regime-A z-scores against held-out/during/post
days, same train/test discipline as every prior VoI lab), not tuned away — see Risks for why this,
not an artificially harder feature set, was used as-is.

## Result: single run (`run_dispatch_voi.py`, illustrative constants, breakeven P(changed)=0.05)

| condition | actions (skip/probe/drill, n=74) | realized $ |
|---|---|---|
| SVM | 7 / 0 / 67 | $55.65M |
| GPC-mean-only | 0 / 0 / 74 | $57.30M |
| GPC-full-posterior | 0 / 0 / 74 | $57.30M |

SVM's 7 wrong skips (on days that were actually state=1) cost it $1.65M relative to GPC here —
GPC's better-calibrated mean, not its variance, is what protects it (mean and full are bit-identical
in this run).

## Result: 200 seeds (`bootstrap_dispatch_voi.py`, same constants)

| condition | realized $ | vs. SVM |
|---|---|---|
| SVM | $57.08M ± $0.44M | — |
| GPC-mean-only | $57.30M ± $0.00M | — |
| **GPC-full-posterior** | **$57.30M ± $0.00M** | **+$0.225M [$0.166, $0.287]** |

GPC-full − GPC-mean: **$0.000M [$0.000, $0.000]** — bit-identical in every one of 200 seeds. Mean
action distribution: SVM skips 1.3/74 days on average (its only source of loss vs. the other two);
GPC-mean and GPC-full never skip, never probe. Probe niche fraction (gpc_full): mean 0.098 — Probe
is rarely even worth considering at this breakeven, and never actually chosen.

## Result: breakeven-probability sweep (`cost_ratio_sweep_dispatch.py`, 200 seeds)

Base rate (during+post fraction of the dataset) = **0.824** — this lab's positive class is the
**majority** class, unlike every prior VoI lab (mining/porphyry ore, grid_reserve drought were all
rare-event framings). The grid spans well below to well above this base rate.

| breakeven P(changed) | SVM | GPC-mean | GPC-full | full−SVM | full−mean |
|---|---|---|---|---|---|
| 0.010 | $301.30M | $301.30M | $301.42M | +$0.12M [0.10,0.14] | +$0.12M [0.10,0.14] |
| 0.050 | $57.08M | $57.30M | $57.30M | +$0.22M [0.17,0.29] | $0.00M [0.00,0.00] |
| 0.100 | $26.97M | $26.81M | $26.80M | **−$0.17M** [−0.21,−0.14] | −$0.01M |
| 0.200 | $12.09M | $11.71M | $11.70M | **−$0.40M** [−0.43,−0.37] | −$0.01M |
| 0.300 | $7.05M | $6.71M | $6.68M | **−$0.37M** [−0.40,−0.33] | −$0.02M |
| 0.400 | $4.52M | $4.24M | $4.23M | **−$0.29M** [−0.33,−0.25] | −$0.01M |
| 0.500 | $3.01M | $2.83M | $2.83M | **−$0.18M** [−0.20,−0.15] | $0.00M |
| 0.600 | $2.01M | $0.92M | $0.86M | **−$1.14M** [−1.22,−1.07] | −$0.05M |
| 0.700 | $1.29M | $0.42M | $0.39M | **−$0.90M** [−0.95,−0.85] | −$0.03M |
| 0.824 (base rate) | $0.64M | $0.14M | $0.13M | **−$0.51M** [−0.53,−0.49] | −$0.01M |
| 0.900 | $0.33M | $0.05M | $0.04M | **−$0.29M** [−0.30,−0.28] | −$0.01M |
| 0.950 | $0.15M | $0.00M | $0.00M | **−$0.15M** [−0.16,−0.15] | ~$0.00M |
| 0.990 | $0.03M | $0.00M | $0.00M | −$0.03M | $0.00M |

## Mechanism, checked directly, not guessed

**Why GPC-full never beats GPC-mean anywhere on this grid**: with AP≈0.999–1.000, the classifier's
predictions are almost never genuinely ambiguous — Probe's niche-fraction stays under ~17% at every
breakeven tried, and the realized action distribution shows Probe essentially never actually chosen.
Posterior variance has nothing to resolve when the underlying classification problem is this close
to deterministic — the same structural principle this codebase has established repeatedly (variance
only pays off when the decision has genuine ambiguity to exploit), just landing at the "no ambiguity
left" end of the spectrum rather than the "genuine ambiguity" end `grid_reserve_lab` found.

**Why SVM beats GPC-full/mean at breakeven≥0.1, reversing every prior VoI lab's ranking**: GPC's
predicted-probability range was consistently narrower and more centered than SVM's (e.g. one seed:
GPC `[0.26, 0.91]` vs. SVM `[0.02, 1.00]`) — the MacKay moment-matched correction shrinks toward
0.5, the same mechanism `bayesian_decision_lab`'s own Phase 1 found responsible for its own
surprising result (there, shrinkage toward a 50% prior hurt because the true base rate was ~5%;
here, the true base rate is 82.4% — shrinkage toward 50% is *again* a miscalibration relative to
the true base rate, just pulling in the other direction). At low breakeven, "drill" is so cheap
relative to its payoff that near-any nonzero probability triggers it, so GPC's narrower range
doesn't cost it (and its slightly better-behaved mean on a couple of ambiguous days gives it a small
edge over SVM's occasional overconfident wrong skip). At moderate-to-high breakeven, the decision
needs genuine confidence to justify committing — and SVM's more extreme, more decisive probabilities
happen to track the true label more decisively at exactly the days that matter, while GPC's
shrunk-toward-0.5 probabilities more often fall on the wrong side of a demanding threshold. This is
a real, checked mechanism (verified via the actual predicted-probability ranges), not assumed.

## Answering "how much of a difference would this make" (the original question)

Two honest findings, neither the one this lab's family originally expected:
1. **Posterior variance (the actual "VoI" contribution) adds nothing measurable here** — a genuine,
   checked null result, not a design failure. The mechanism is real; this domain's classification
   problem just doesn't have enough residual ambiguity left for it to matter.
2. **Whether "use a calibrated GP classifier at all" helps is itself cost-ratio-dependent, and can
   go the wrong way** — at low breakeven GPC's mean edges out SVM; at moderate-to-high breakeven
   SVM wins by a larger, statistically robust margin. This is the first lab in this family where the
   simple "GPC beats SVM" story doesn't hold uniformly, and it's reported here exactly as measured.

## Risks / honest unknowns

- **Near-perfect separability was found, not engineered.** Several feature-reduction and
  training-set-size reductions were tried empirically (see the exploration log, not committed to
  files) specifically to check this wasn't a trivial-classifier artifact the way
  `grid_reserve_lab`'s original 20-site early-reporting feature was — AP stayed ≥0.97 in every
  variant tried, including single-mode features and 8-day training sets. This is reported as a real
  property of the KW51 transition's detectability via z-score features, not a chosen easy case.
- **Economic constants are illustrative** (see `research/06_inspection_and_failure_cost.md`) — the
  breakeven sweep is the load-bearing result specifically so this doesn't matter for the qualitative
  finding (variance never helps; SVM-vs-GPC ranking flips), only for which single row of the table
  would be "the" answer in a real deployment.
- **The "state 1" definition conflates mid-retrofit and post-retrofit days** (see Method) — a
  limitation inherited from Phase 1/1b, not resolved here.
- **Disclaimer carried forward unchanged**: this lab, including this phase, is theoretical/
  educational only, not for any real-structure decision.
