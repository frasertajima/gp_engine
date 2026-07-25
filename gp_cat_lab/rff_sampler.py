"""Random Fourier Features (RFF) approximate sampler for the RBF spatial
kernel -- used ONLY at Phase 2's OOC scale, because neither gp_core.py nor
gp_ooc_fortran.py expose a "multiply by the Cholesky factor" primitive.
Both only expose SOLVE (potrs: given a right-hand side, return K^-1 b),
which is exactly what GP fitting/prediction needs -- but generating a joint
sample from N(0, Sigma) needs the FORWARD operation (L @ z, a square root
of Sigma), which is a different primitive current gp_engine does not
expose at OOC scale. This is a genuine, reportable gap in the engine's API
surface (see RESULTS_PHASE2.md), not something this lab papers over.

Standard technique instead (Rahimi & Recht 2007, "Random Features for
Large-Scale Kernel Machines"): for the RBF kernel
k(x,y) = exp(-||x-y||^2 / (2*ell^2)), Bochner's theorem gives an explicit
finite-dimensional feature map phi(x) such that phi(x).phi(y) ~= k(x,y),
letting samples be drawn in O(n*m) work and O(n*m) memory (m = number of
random features, a few hundred) instead of the O(n^2) memory / O(n^3)
factorization an exact Cholesky sample needs -- works at n=45,000+
trivially, on CPU, no GPU/OOC involvement at all for this specific step.

This module's docstring is not the trust boundary -- `phase2_run.py`'s
validation step (comparing RFF-sampled near/far correlation against
dgp_simulator.py's EXACT Cholesky-based z_field at Phase 0's n=500 scale,
same kernel hyperparameters) is. Only trust the numbers below that
validation passes.
"""

import numpy as np


def rff_features(coords, ell, n_features, seed=0):
    """(n, n_features) feature matrix phi such that phi @ phi.T ~= the
    UNIT-VARIANCE RBF kernel exp(-||x-y||^2/(2*ell^2)) (sigma_f2=1 -- scale
    the returned features by sqrt(sigma_f2) to match a scaled kernel)."""
    d = coords.shape[1]
    rng = np.random.default_rng(seed)
    omega = rng.standard_normal((n_features, d)) / ell
    b = rng.uniform(0.0, 2.0 * np.pi, size=n_features)
    proj = coords @ omega.T + b[None, :]
    return np.sqrt(2.0 / n_features) * np.cos(proj)


def sample_rff_field(coords, ell, sigma_f2, sigma_n2, n_scenarios, n_features=500,
                      seed=0, feature_seed=0):
    """(n_scenarios, n) approximate samples from N(0, sigma_f2*K(coords;ell)
    + sigma_n2*I). `feature_seed` fixes the random Fourier features
    themselves (the same features define ONE approximate covariance
    structure, reused across scenarios); `seed` controls the per-scenario
    draws against that fixed structure."""
    n = coords.shape[0]
    phi = rff_features(coords, ell, n_features, seed=feature_seed)
    rng = np.random.default_rng(seed)
    z_m = rng.standard_normal((n_scenarios, n_features))
    z_n = rng.standard_normal((n_scenarios, n))
    return np.sqrt(sigma_f2) * (z_m @ phi.T) + np.sqrt(sigma_n2) * z_n
