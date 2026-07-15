"""Marker-space squared-distance matrix via the GEMM trick -- the actual
value-add of Phase 2 (LAB_PLAN.md): a Gaussian/Matern kernel over raw SNP
dosage, instead of MPDOK's fixed linear VanRaden GRM.

Same identity MPDOK already uses in `rbf_kernel.py` / `kriging_kernel.py`:

    ||a - b||^2 = ||a||^2 + ||b||^2 - 2 a.b

one DGEMM, no N x M x N intermediate -- and it works for any d (M markers can
be in the thousands to tens of thousands; the register-resident coordinate
kernel in gp_core.py cannot do this, see LAB_PLAN.md's engine-gap section).
The distance matrix D2 doesn't depend on any hyperparameter, so it's built
**once per fold** and reused across every hyperopt eval; only the cheap
elementwise kernel transform (RBF or Matern-3/2) changes per eval.
"""

import cupy as cp
import numpy as np

_SQRT3 = 1.7320508075688772


def squared_dist_matrix(X):
    """(n,n) FP64 squared-distance matrix for X (n,d), any d, via one GEMM."""
    X = cp.asarray(X, dtype=cp.float64)
    sq = cp.sum(X * X, axis=1)
    D2 = sq[:, None] + sq[None, :] - 2.0 * (X @ X.T)
    cp.maximum(D2, 0.0, out=D2)
    return D2


def cross_squared_dist(X1, X2):
    """(m,n) FP64 squared-distance matrix between X1 (m,d) and X2 (n,d)."""
    X1 = cp.asarray(X1, dtype=cp.float64)
    X2 = cp.asarray(X2, dtype=cp.float64)
    sq1 = cp.sum(X1 * X1, axis=1)
    sq2 = cp.sum(X2 * X2, axis=1)
    D2 = sq1[:, None] + sq2[None, :] - 2.0 * (X1 @ X2.T)
    cp.maximum(D2, 0.0, out=D2)
    return D2


def apply_kernel(D2, ell, kind="rbf"):
    """Elementwise kernel transform (no sigma_f2 scale, no nugget -- those are
    applied by PrecomputedKernel). D2 unchanged; this is the cheap per-eval
    step in the hyperopt loop."""
    if kind == "rbf":
        return cp.exp((-1.0 / (2.0 * ell * ell)) * D2)
    elif kind == "matern32":
        d = cp.sqrt(D2) * (_SQRT3 / ell)
        return (1.0 + d) * cp.exp(-d)
    else:
        raise ValueError(f"kind must be 'rbf' or 'matern32', got {kind!r}")


def median_dist_scale(D2, max_sample=512):
    """Median pairwise distance -- a standard bandwidth-initialization
    heuristic (same one MPDOK's kriging_kernel.py uses), not the fitted value."""
    n = D2.shape[0]
    idx = cp.asarray(np.random.default_rng(0).choice(n, size=min(max_sample, n),
                                                      replace=False))
    sub = D2[cp.ix_(idx, idx)]
    d = cp.sqrt(sub[sub > 1e-15])
    return float(cp.median(d)) if d.size else 1.0
