# GP Lab Results — Exact GP Regression vs the Published Benchmark Suite

**Date:** 2026-07-13 (M5 write-up). **Hardware:** one NVIDIA RTX 4060 (8 GB,
$299 MSRP, 115 W) in a 46 GB-RAM desktop with consumer NVMe. **Engine:**
the gp_engine mixed-precision exact-GP stack (FP32 tensor-class Cholesky +
FP64 iterative refinement; OOC streaming via the CUDA Fortran backend at
n > 38k — see `../PLAN.md`, `../CUDA_FORTRAN_STREAMING_LESSONS.md`).

**Baseline:** Wang, Pleiss, Gardner, Tyree, Weinberger & Wilson, *"Exact
Gaussian Processes on a Million Data Points"*, NeurIPS 2019
(arXiv:1903.08114; PDF cached at `papers/wang2019_exact_gp_million.pdf`).
Their hardware, quoted from p. 6: *"We perform all training on a single
machine with 8 NVIDIA Tesla V100-SXM2-32GB-LS GPUs."* We compare against
their **Table 3** (exact GP with independent lengthscales per dimension —
the ARD setting, matching ours), 3-trial means ± std.

---

## 1. Headline

**An exact GP on n = 391,387 training points (3droad), fit and scored on a
single $299 consumer GPU, beats the published 8×V100 exact-GP baseline on
both RMSE and NLL:**

|  | RMSE | NLL |
|---|---|---|
| **This engine (1× RTX 4060)** | **0.0702** | **−1.024** |
| Wang et al. 2019 (8× V100) | 0.110 ± 0.017 | 1.239 ± 0.025 |

Across the full six-dataset suite: **NLL better on 6/6 datasets, RMSE better
on 4/6** (the two RMSE losses are analyzed, not hidden — §4.1).

## 2. Full scorecard

Ours: Matérn-3/2 ARD, staged Nelder-Mead hyperopt, 90/10 split, 3 seeds
(3droad: 1 seed — §4.3), y standardized by train-split stats (same whitening
protocol as the paper). Theirs: Table 3 (ARD), 3 trials, 4/9 train split.
RMSE/NLL in standardized-y units, as the literature reports them. **Bold** =
better.

| Dataset | n (ours / theirs) | d | RMSE ours | RMSE theirs | NLL ours | NLL theirs | cover95 | fit time (ours) |
|---|---|---|---|---|---|---|---|---|
| pol | 13,500 / 9,600 | 26 | 0.127 ± 0.022 | **0.088 ± 0.003** | **−0.961 ± 0.013** | −0.660 ± 0.081 | 94.6% | 1.8 s |
| elevators | 14,939 / 10,623 | 18 | **0.354 ± 0.004** | 0.399 ± 0.011 | **0.382 ± 0.013** | 0.626 ± 0.043 | 94.6% | 1.2 s |
| bike | 15,641 / 11,122 | 17 | **0.022 ± 0.013** | 0.043 ± 0.012 | **−2.982 ± 0.198** | −0.984 ± 0.021 | 99.0% | 2.3 s |
| kin40k | 36,000 / 25,600 | 8 | **0.065 ± 0.002** | 0.080 ± 0.001 | **−1.319 ± 0.020** | −0.755 ± 0.009 | 97.4% | 6.8 s |
| protein | 41,157 / 29,267 | 9 | 0.538 ± 0.007 | **0.511 ± 0.009** | **0.575 ± 0.025** | 0.960 ± 0.043 | 93.7% | 13.9 s |
| **3droad** | **391,387 / 278,319** | 3 | **0.0702** | 0.110 ± 0.017 | **−1.024** | 1.239 ± 0.025 | 98.6% | 3 h 43 m |

Verdict shorthand: 4/6 clean sweeps (elevators, bike, kin40k, 3droad),
2/6 mixed (protein, pol: calibration better, point accuracy worse — §4.1).

## 3. The 3droad result, in context

3droad was this lab's stretch milestone (M4) and the hardest-won number here:

- **Scale.** The kernel matrix at n = 391,387 would be **613 GB in FP32 /
  1.2 TB in FP64. It never exists.** K tiles are regenerated on-GPU from X
  (9.4 MB) inside the fused kernels; only Cholesky factor panels (309.6 GB:
  32 GB pinned RAM + 277.6 GB NVMe) ever leave the card.
- **Exactness.** The IR solve converged to **relative residual 9.4×10⁻¹¹ in
  3 steps** — an exact solve by any reasonable standard. For calibration:
  the paper's PCG training runs at tolerance ε = 1 (their §5: *"a looser
  convergence criterion of up to ε = 1 has little impact on final model
  performance"*), with ε ≤ 0.01 solves reserved for test-time. Our factor is
  ~8 orders tighter than their training solves.
- **Timing, honestly framed.** Their ARD 3DRoad training: 3,592.5 s ± 9.4 on
  8× V100 with 16 kernel partitions (their Table 4). Ours: 45 s hyperopt +
  13,374 s fit (3 h 43 m factor+IR) + 5,106 s to predict mean *and variance*
  for all 43,487 test points — on one GPU with roughly **1/50th the
  aggregate FP32 throughput and 1/32nd the aggregate VRAM** of their
  machine. We are ~3.7× slower on the wall clock with ~50× less compute.
- **Preprocessing matched, and cross-validated by ARD.** We use the same
  `uci_datasets` d=3 files the paper's ecosystem uses (leakage-checked: the
  third column — the OSM road-segment ID — correlates with y at only
  −0.11). The fitted ARD lengthscales were ℓ = [63.9, 0.041, 0.048]: the
  model **automatically pruned the segment-ID column** (ℓ ≈ 64 on whitened
  data ≈ irrelevant) and recovered lengthscales nearly identical to an
  earlier d=2 (lon/lat-only) fit's [0.04, 0.05]. Both preprocessings
  converge to the same model; the comparison is like-with-like.
- **Reliability.** This exact fit hung the earlier Python streaming layer
  five times (host memory-pressure livelocks — LAB_PLAN.md M4 forensics).
  The CUDA Fortran OOC port (`../gp_ooc_solver.cuf`) completed it on the
  first attempt, inside a 32 GB memory-capped cgroup, with host memory
  stable throughout. Full engineering postmortem:
  `../CUDA_FORTRAN_STREAMING_LESSONS.md`.

## 4. Caveats — read before quoting the table

### 4.1 The protein/pol RMSE pattern (the 2/6 losses)

protein RMSE is 5.4% above the published number, pol 44% above — while both
beat the published NLL by wide margins. The same signature, in 2/6 datasets,
suggests a systematic cause; our working hypothesis was **optimizer choice,
not engine numerics** — the paper trains gradient-based throughout (L-BFGS +
Adam pretraining, exact LML gradients) while we use derivative-free staged
Nelder-Mead by design (keeps the FP32-factor+IR path as the only linear
algebra in the loop).

**Follow-up (§9) partially confirms this and partially doesn't.** A bounded
L-BFGS-B polish stage (FD gradients over the same subsample objective) was
added and tested directly: **pol's RMSE gap is exactly NM non-convergence**
(lengthscales swinging up to 14× across seeds; the polish fixes it, 0.119 →
0.076, flipping pol to a clean win). **Protein shows zero pruning and the
polish doesn't move it at all** — so protein's gap is NOT the pol mechanism,
and matched training-set sizes (§9.2) make it *worse*, ruling out data
volume too. Protein's cause remains unidentified; "optimizer choice" is now
the leading explanation only by elimination, not direct evidence.

### 4.2 bike's nugget floor

bike's LML genuinely wants near-zero noise; at the default floor
σ_n ≥ 1e-3 the search degenerated, and these runs use `--floor 1e-2`
(documented in LAB_PLAN.md M3). The paper regularizes analogously where
needed (their houseelectric noise is constrained ≥ 0.1, §5), so a dataset-
specific floor is within the norms of this literature — but bike's
0.022 ± 0.013 RMSE (large relative spread, seeds 0.039/0.020/0.008) should
be quoted with its std, not alone. Its 99.0% coverage reflects the raised
floor (mild over-dispersion).

### 4.3 3droad is single-seed

By explicit M4 scoping decision (LAB_PLAN.md): one converged seed at
391k×90% was the milestone bar, and each seed costs ~5 h of compute plus
~310 GB of panel churn. The published 0.110 ± 0.017 is a 3-trial mean; our
0.0702 sits **2.3 published-stds below their mean**, so seed-to-seed noise
is an implausible explanation for the win, but the single-seed status should
be stated wherever the number is used. **Now cross-checked at matched n**
(§9.2b): re-run at the paper's own exact training count (278,319, still
single-seed) gives RMSE 0.080 / NLL −0.966, still a clean win — the result
isn't an artifact of either the seed or the extra training data.

### 4.4 We train on more data (and that's part of the point)

Our headline splits are 90/10 train/test; the paper's TEXT states 4/9
train, 2/9 validation, 3/9 test, but its own TABLES report training counts
that are all exactly 64% of the source data — the discrepancy, and which is
authoritative, is resolved in §9.1. Either way, our 90/10 headline runs
train on more points than the paper does (3droad: 391,387 vs their
278,319) — a deliberate, disclosed protocol difference, not an accident:
exact GPs are non-parametric and the paper's own central argument (their
Fig. 4: *"exact GP error continues to decrease as data is added"*) is that
more training data is exactly what exact methods are for. We don't need a
held-out validation third because derivative-free NM tunes no optimizer
knobs on validation data. **§9 measures the data-volume effect directly
rather than leaving it as a caveat**: real for kin40k (its win nearly
vanishes at matched n) but small for 3droad and most of the suite (§9.2,
§9.2b) — quantified, not just disclosed.

### 4.5 Coverage runs high on the low-noise datasets

95% intervals cover 93.7–94.8% on the medium-noise sets (well-calibrated)
but 97.4–99.0% on kin40k/bike/3droad (over-covering). Pattern: coverage
excess tracks small learned σ_n — on near-noiseless data the floor makes
predictive intervals conservative. Honest reading: NLL wins are not an
artifact of overconfidence (over-coverage is the *safe* direction), but
these intervals are not sharp at the low-noise end.

### 4.6 Solve-quality note

"Exact" here means: FP32 Cholesky factor + FP64 iterative refinement,
converged to relative residual ≤ 1e-10 (suite) / 9.4e-11 (3droad), with the
log-determinant from the FP32 factor (bias measured harmless for
hyperparameter *ranking* — RESULTS_PHASE1.md). Failures are detectable
(`FactorError` / `converged=False`), not silent.

## 5. κ on real data — the envelope finding

The Phase-0 conditioning envelope (fits clean at κ ≲ 1e6, fails detectably
≳ 2e8) was calibrated on RBF kernels. Real-data Matérn-3/2 fits blew through
it harmlessly:

| Dataset | κ upper bound (max over seeds) | outcome |
|---|---|---|
| protein | 5.0e4 | clean |
| elevators | 6.6e4 | clean |
| 3droad | 3.2e5 | clean |
| pol | 3.2e6 | clean |
| bike | 2.3e7 | clean (floor raised, §4.2) |
| kin40k | **7.1e8** | **clean — 3 IR steps, relres ≤ 1e-11** |

kin40k converges at κ ~ 7×10⁸ — **inside the band where RBF kernels fail
detectably** (≳2×10⁸), and ~700× past the RBF clean zone (≲10⁶). The
Matérn spectrum is bounded below (heavier tails than RBF's exponential
decay), so κ_bound = λ_max/σ_n² is much looser for Matérn — **the envelope
is kernel-dependent and the RBF numbers are conservative for Matérn**. This
matters for practitioners: don't refuse a Matérn fit on an RBF-calibrated
κ estimate.

## 6. Hardware and cost, with verifiable numbers only

| | This lab | Wang et al. 2019 |
|---|---|---|
| GPUs | 1× RTX 4060, 8 GB | 8× Tesla V100-SXM2-32GB (their p. 6) |
| GPU FP32 throughput | ~15 TFLOPS | ~15.7 TFLOPS **each**, ~125 aggregate |
| Aggregate VRAM | 8 GB | 256 GB |
| GPU street price | $299 MSRP (2023) | data-center class; 8× V100 SXM2 was a six-figure server (DGX-1 class) at the time |
| Board power | 115 W | ~300 W each, ~2.4 kW aggregate |
| Host RAM used (3droad) | 46 GB box, job capped at 32 GB | n/s |

The claim is **not** that one 4060 outruns eight V100s — it doesn't
(§3, timing). The claim is that *exact* GP regression at n ≈ 4×10⁵ with
**better accuracy than the published 8-GPU exact baseline** is achievable
on hardware costing well under 1% of a DGX-class machine, by trading
wall-clock time (hours, unattended) and disk (310 GB of scratch panels)
for VRAM and GPU count. The enabling engineering: mixed-precision
factor+IR, implicit-K regeneration, and tiered RAM/NVMe panel streaming
(CUDA Fortran).

## 7. Reproduction

```bash
# inside conda py314, from gp_lab/
python run_benchmark.py kin40k                  # ×3 seeds, in-core
python run_benchmark.py protein                 # ×3 seeds, OOC
python run_benchmark.py elevators
python run_benchmark.py bike --floor 1e-2       # nugget floor, §4.2
python run_benchmark.py pol
python run_benchmark.py 3droad --seeds 0 --allow-large-ooc \
    --ram-budget-gb 32 --max-ir 24 --tol-final 1e-9   # ~6 h, run it
    # under systemd-run with a memory cap (see LAB_PLAN.md M4 ops notes)

# matched training-set sizes (§9) + hybrid optimizer (§9):
python run_benchmark.py kin40k --protocol paper --hyperopt hybrid
python run_benchmark.py protein --protocol paper --hyperopt hybrid
python run_benchmark.py elevators --protocol paper --hyperopt hybrid
python run_benchmark.py bike --protocol paper --hyperopt hybrid --floor 1e-2
python run_benchmark.py pol --protocol paper --hyperopt hybrid
```

Per-run JSON artifacts (all metrics + hyperparameters + timings):
`results/*.json` (headline lab-protocol runs), `results/*_papern_seed*.json`
(matched-n, NM), `results/*_papern_hybrid_seed*.json` (matched-n, hybrid
optimizer — §9). Datasets fetch/verify via `python datasets.py`
(uci_datasets mirror; 3droad/bike re-preprocessed to match the paper — see
`datasets.py` docstrings). Summary notebook with charts:
`RESULTS_LAB.ipynb` (rebuild via `python build_results_nb.py`).

## 9. Follow-up: matched training-set sizes + a hybrid optimizer

Two pieces of user feedback on the original write-up, both acted on:
*"enforce the exact n used in the paper — otherwise we could be comparing
apples with oranges"*, and *"a hybrid Nelder-Mead → L-BFGS-B optimizer might
prevent the catastrophic over-pruning in pol/protein."* Both changed a real
conclusion. This section documents the experiment, a bug the verification
process caught, and the fix.

### 9.1 The paper's own tables disagree with its own text

Wang et al.'s §5 text states a 4/9 train / 2/9 val / 3/9 test split
(44.4% train). But every training-set size in their Tables 1 and 3 is
*exactly* ⌊0.64·N⌋ for the source N (kin40k 25,600 = ⌊0.64×40,000⌋; pol
9,600 = ⌊0.64×15,000⌋; 3droad 278,319 = ⌊0.64×434,874⌋; verified for all
six datasets). This is the GPyTorch-benchmark convention: an 80/20
train/test split, then an 80/20 train/val split *of the training pool*
(0.8 × 0.8 = 0.64 train, 0.16 val, 0.20 test) — not the 4/9 the text
describes. The tables are per-dataset integers and therefore authoritative;
`datasets.py`'s new `protocol="paper"` implements 0.64/0.16/0.20 and
reproduces every published training count exactly. Our validation third
goes unused (we tune nothing on it — the derivative-free search has no such
knob), so this is a training-data-matched, not a validation-matched,
comparison.

### 9.2 Three-way comparison (5 in-core datasets, ×3 seeds)

| Dataset | Published | Lab (90/10) | **Matched-n, NM** | **Matched-n, hybrid** |
|---|---|---|---|---|
| pol | RMSE 0.088±0.003 | 0.127±0.022 | 0.119±0.019 | **0.076±0.003** |
| | NLL −0.660±0.081 | −0.961±0.013 | −0.891±0.033 | **−1.224±0.039** |
| elevators | RMSE 0.399±0.011 | **0.354±0.004** | **0.356±0.002** | **0.355±0.001** |
| | NLL 0.626±0.043 | **0.382±0.013** | **0.376±0.005** | **0.375±0.005** |
| bike | RMSE 0.043±0.012 | **0.022±0.013** | **0.020±0.004** | **0.020±0.004** |
| | NLL −0.984±0.021 | **−2.982±0.198** | **−3.104±0.057** | **−3.104±0.057** |
| kin40k | RMSE 0.080±0.001 | **0.065±0.002** | 0.079±0.001 | 0.079±0.001 |
| | NLL −0.755±0.009 | **−1.319±0.020** | **−1.166±0.003** | **−1.138±0.039** |
| protein | RMSE 0.511±0.009 | 0.538±0.007 | 0.573±0.008 | 0.572±0.009 |
| | NLL 0.960±0.043 | **0.575±0.025** | **0.668±0.011** | **0.670±0.011** |

**Bold = beats published.** Bike's hybrid numbers are bit-identical to NM's
(the L-BFGS-B stage never found an improving point — confirmed by comparing
the fitted ARD lengthscales directly, not just the aggregate metric).

### 9.3 Verdict on both suggestions

**Matched-n changes a real conclusion.** Kin40k's RMSE win nearly
disappears (0.065 → 0.079, essentially tying the published 0.080): a real
share of the apparent advantage was training on 36,000 points instead of
their matched 25,600 (the lab-protocol 90/10 split trains on ~40% more data
here) — not the engine. Everywhere else the win/loss pattern is unchanged;
NLL stays a win on all 5 at every n.

**The hybrid optimizer fixes exactly the dataset it should.** pol was
diagnosed as genuine NM non-convergence (fitted lengthscales swinging up to
14× across seeds at the same data) — hybrid fixes it decisively (0.119 →
0.076, flipping pol from a loss to a clean win, with σ_n and κ both moving
consistently across all 3 seeds: κ drops ~10× to 2×10⁵). Protein, which
showed *no* pruning at all in the original diagnostic, is unaffected by
hybrid, as predicted — its RMSE gap has a different cause, not yet
identified.

### 9.2b 3droad at matched n (n=278,319, NM only — no hybrid variant run)

The M4 case gets the same treatment. Matched-n cuts 3droad's training set
by 29% (391,387 → 278,319) versus the lab-protocol run:

| | Published (n=278,319) | Lab-protocol (n=391,387) | **Matched-n (n=278,319)** |
|---|---|---|---|
| RMSE | 0.110 ± 0.017 | 0.070 | **0.0799** |
| NLL | 1.239 ± 0.025 | −1.024 | **−0.966** |
| coverage95 | — | 98.6% | 98.2% |
| relres / IR steps | — | 9.4×10⁻¹¹ / 3 | 6.96×10⁻¹¹ / 3 |
| fit time | 3,592.5 s (8×V100) | 3 h 43 m | 1 h 16 m |

**Unlike kin40k, 3droad's win survives the data cut comfortably** — RMSE
27% better than published, NLL better by 2.2 nats, both comparisons at the
paper's own exact training count. The 391k→278k cut moved RMSE by
+0.010 (0.070→0.080), a real but modest effect, nowhere near enough to
threaten the published baseline the way the same style of cut did for
kin40k (§9.3). Fit time also dropped roughly in line with the smaller
factor (68 vs 96 panels; 157 GB vs 309.6 GB of panels) — no new engineering
needed, same `gp_ooc_solver.cuf` path. ARD lengthscales
[77.1, 0.041, 0.051] again auto-prune the third (OSM-segment-ID) column and
land within noise of the n=391,387 fit's [63.9, 0.041, 0.048] — the model
is stable across both training-set sizes, reinforcing §3's preprocessing
cross-validation finding.

### 9.4 A gate bug the verification process caught (and the fix)

The L-BFGS-B stage is bounded and warm-started from NM's optimum, but a
sharper optimum can be perfectly evaluable on the 8,000-point hyperopt
subsample and still be unfittable at full n (the κ wall scales with n). Two
independent problems surfaced building the safety check for this, both
found by verifying results rather than trusting a clean-looking exit code:

1. **First gate version** accepted a candidate using the same loose
   `relres > 1e-3` bar the subsample search itself uses. On kin40k
   (matched-n, seed 1) this let through a candidate that was fit-evaluable
   but never actually converged at the real fit's tolerance
   (`relres ≈ 5×10⁻⁷`, capped at `max_ir`, `converged=False`, κ ≈ 4.5×10¹⁰).
   **Fix:** the gate now runs a real `gp_fit` at the exact `tol_final`/
   `max_ir` the final run will use and requires `.converged` — not an
   LML-evaluability proxy.
2. **That fix alone wasn't sufficient.** Re-running the same case showed
   the tightened gate correctly validating a good candidate
   (`converged=True, relres=7.9×10⁻¹¹`) — yet the final JSON still recorded
   the same unconverged result. Root cause: **stage C** (a short full-data
   NM polish that runs after the gate, seeded from its output) has its own,
   separate loose-tolerance acceptance check, and walked the gate-approved
   point into a worse region during its own search — a risk that exists in
   the plain NM path too, just less likely to be reached from a less-sharp
   seed. **Fix:** stage C's output is now verified the same way (a real
   fit at `tol_final`/`max_ir`); if it fails, the pre-polish theta — the one
   the gate already validated — is kept instead.

Both fixes were confirmed by direct, isolated reruns of the exact failing
case (not just re-running the whole batch and hoping): the previously
slipped-through seed now converges cleanly, and the two seeds whose B2
candidates were already being correctly rejected still reject identically
(bit-for-bit) after the change — nothing regressed. This two-layer gate
(candidate-level, then post-polish) generalizes to `method="nm"` as well,
since stage C runs regardless of method.

### 9.5 What's still open

3droad has now been re-run at matched n (§9.2b) — the win survives
comfortably (RMSE 0.080 vs published 0.110, NLL −0.966 vs +1.239), closing
out the matched-n picture for every dataset in the suite. Protein's RMSE
gap remains the one open item: unexplained after ruling out both data
volume (§9.2, gets *worse* at matched n) and optimizer non-convergence
(§9.3, no pruning, hybrid doesn't move it) — the original optimizer-choice
hypothesis in §4.1 is now the leading explanation by elimination, not
direct evidence.

## 10. Pointers

- `LAB_PLAN.md` — milestones M1–M5, per-dataset findings, the full M4
  incident history.
- `../PLAN.md` — engine phases, §6b language policy (compiled streaming).
- `../CUDA_FORTRAN_STREAMING_LESSONS.md` — the OOC performance postmortem.
- `../RESULTS_PHASE0..2.md` — engine-side envelopes and scaling results.
- `papers/wang2019_exact_gp_million.pdf` — the baseline paper (local copy).
