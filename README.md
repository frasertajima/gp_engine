# GP Engine — preview release

Exact Gaussian-process regression at consumer-GPU scale: fit, log marginal
likelihood, hyperparameter optimization, and prediction with uncertainty, on
dense RBF kernel systems up to **n = 40,000 in-core on an 8 GB GPU** (and to
n = 200,000 with the out-of-core module, not included in this preview — see
below).

**What's in this folder**

| file | what it is |
|---|---|
| `gp_solver.so` | the solver core: CUDA Fortran, compiled for cc86/cc89 (Ampere & Ada) |
| `gp_engine.py` | self-contained Python wrapper: `RBFKernel`, `gp_fit`, `gp_predict` |
| `gp_engine_demo.ipynb` | executed demo notebook — start here |
| `build_demo_nb.py` | regenerates the notebook |

Requirements: CUDA 12.x driver, CuPy, NumPy, SciPy (for the hyperopt demo
cell), a GPU with compute capability 8.6 or 8.9. This is a **preview**: the
solver core is shipped as a binary; source, the out-of-core module, and the
larger benchmark suite are in development.

---

## The family this comes from (and how the three engines differ)

This is the third engine in a line built on one idea: on consumer GPUs,
FP64 runs at **1/64** the FP32 rate — so do the O(n³) bulk work in low
precision on the fast units, then recover high precision with cheap
corrections. Each engine applies that idea to a different layer of the
numerical stack.

### Tensor Core Engine v5.1 — the GEMM layer
*[link]*

A CUDA Fortran shared library exposing dense GPU matrix ops to Python.
Its differentiator over stock CuPy is **split-precision GEMM**
(Ozaki/Dekker-style splitting): TF32 tensor-core *throughput* at
FP32-to-near-FP64 *accuracy* (~1e-6…1e-7), plus fused cuBLASLt neural-net
epilogues (bias/ReLU). It accelerates a single operation — the matrix
multiply — and is the right tool when a workload is dominated by dense or
batched GEMM that plain TF32 isn't accurate enough for.

### MPDOK — the solver layer
*[link]*

Mixed-Precision Dense-Operator Krylov solver: **GMRES-IR** and **LU-IR**,
i.e. factor or precondition in FP32, then a few FP64 iterative-refinement
steps to reach relative residuals of 1e-11…1e-13. Where the tensor core
engine accelerates a multiply, MPDOK accelerates a *solve* — `Ax = b` for
general dense systems — and it has been validated across ~30 application
labs (boundary-element scattering, kriging, quantum dynamics, portfolio
problems, …). Its sweet spot: dense linear systems where FP64 `solve` is
the baseline to beat, on ill-conditioned matrices where plain FP32 fails.

### GP Engine (this) — the application layer
*[link]*

Where MPDOK solves *a* linear system, the GP engine owns the **whole
Gaussian-process pipeline**, and that changes the design in three ways:

1. **The matrix is implicit.** A kernel matrix isn't data — it's generated
   from the inputs X (n×d, a few MB). So the engine never forms K in FP64
   at all: fused CUDA kernels compute `x_i·x_j → exp → accumulate` straight
   from X in registers, for the FP32 build, the FP64 IR residuals, and the
   prediction cross-kernels alike. At n = 200k the kernel matrix "is" 320 GB
   in FP64 — here it never exists in any precision.
2. **SPD structure + the log-determinant.** GP training needs Cholesky (2×
   cheaper than LU, guaranteed for SPD) and the log-determinant for the
   marginal likelihood — MPDOK exposes neither. The engine's factorization
   returns log|K| for free from the factor's diagonal, which is what turns
   "a fast solver" into "a GP engine": hyperparameter optimization re-uses
   one resident X and re-factors per candidate θ.
3. **An accuracy contract with a stated envelope.** FP32-factor IR converges
   for κ(K+σₙ²I) ≲ 1e7 — i.e. GP regression with a real noise nugget, which
   is most real GP. Outside the envelope the engine fails *detectably*
   (`FactorError` / `converged=False`), never silently — unlike stock FP32,
   which at high κ happily returns NaN garbage without raising (the demo
   notebook shows this live).

### Measured results (RTX 4060 8 GB, 46 GB RAM desktop)

| n | time (fit + logdet) | accuracy (relres) | vs FP64 cuSOLVER |
|---|---|---|---|
| 12,000 | 0.34 s | 2.6e-12 | 8.6× |
| 27,000 | 2.5 s | 6e-12 | **12.6×** (FP64's last in-core size) |
| 40,000 | 6.5 s | 6e-12 | FP64 cannot allocate |
| 100,000* | 5.4 min | 3e-11 | — |
| 200,000* | 71 min | 3.4e-10, converged | — |

\* out-of-core (factor streamed to pinned RAM + NVMe memmap panels); module
not included in this preview. An 80-eval hyperparameter fit at n = 27k runs
in ~2.8 min where FP64 would need ~41 min.

The speedups are consumer-GPU numbers (FP64 at 1/64 rate). On datacenter
parts with 1:2 FP64 the honest expectation is 3–5×, not 12×.

## Quickstart

```python
import cupy as cp
import numpy as np
from gp_engine import RBFKernel, gp_fit, gp_predict

X = cp.asarray(np.random.rand(20000, 3))          # inputs, d <= 16
y = cp.sin(3 * X[:, 0]) + 0.1 * cp.random.standard_normal(20000)

kern = RBFKernel(ell=0.3, sigma_f=1.0, sigma_n2=1e-2)
fit = gp_fit(kern, X, y)                          # FP32 factor + FP64 IR
print(fit.relres, fit.n_ir, fit.logdet)           # ~1e-12, ~6 steps, LML-ready

mean, var = gp_predict(fit, kern, X, X[:500])     # mean ± uncertainty
```

Open `gp_engine_demo.ipynb` for the guided tour: the conditioning wall,
head-to-head timings vs CuPy FP64, IR convergence traces, hyperparameter
fitting, and uncertainty bands.

## Limits

- Operating envelope κ ≲ 1e7 (real noise nugget); detectable failure outside.
- RBF/SE kernel, d ≤ 16, in this preview.
- log|K| from the FP32 factor carries a ~2–5 nat bias — measured harmless for
  hyperparameter *ranking* (100% rank agreement); refine at the optimum if you
  need absolute LML values for cross-model comparison.
- Below n ≈ 2,000 just use FP64 — the engine's edge grows with n³.
