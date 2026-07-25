"""OOC-scale companion to gp_loss_model.py, for Phase 2's n=45,000 book.

Reuses Phase 1's fitted spatial length scale `ell` as a FIXED, geography-
driven parameter -- the correlation length scale describes the underlying
hazard process's spatial reach, not how many properties happen to be
sampled from that region, a standard geostatistical assumption, not new to
this lab -- and does a SMALL, genuine OOC-based refinement of
(sigma_f2, sigma_n2) jointly (a 3-point scale sweep around the Phase 1 fit,
not a full from-scratch Nelder-Mead search). Each OOC evaluation at
n=45,000 is real, GPU-bound compute: ~30s to factor plus ~3.5s per
historical year to IR-solve, measured directly on this session's actual
GPU (4GB VRAM -- see RESULTS_PHASE2.md for the benchmark and for this
session's own measured in-core ceiling, ~30,000, lower than the 8GB-GPU
figure test/README.md cites). A full ~150-eval search at that per-eval
cost would take hours; this is a deliberate, disclosed scoping decision,
not a silent downgrade -- Phase 1 already validated the fitting
METHODOLOGY at small scale, and Phase 2's job is to test whether
gp_ooc_solver makes EVALUATING (not re-discovering from scratch) that
model tractable at a scale no in-core method on this GPU can reach at all.

Scenario generation reuses rff_sampler.py (validated against exact
Cholesky sampling at Phase 0's n=500 scale, phase2_rff_validation.py):
gp_ooc_fortran.py exposes SOLVE, not the "multiply by L" a joint sample
needs -- see rff_sampler.py's docstring for why.
"""

import os
import sys
import time

import cupy as cp
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import gp_core  # noqa: E402
import gp_ooc_fortran as gp_ooc  # noqa: E402

from rff_sampler import rff_features


def _evaluate_lml_on_factor(fac, kern, coords, R, tol=1e-5, max_ir=5, weights=None):
    """Runs the IR-solve loop (one solve per year of R) against an already-
    factored `fac`/`kern`, without touching panel allocation. Split out of
    evaluate_ooc_lml so refine_sigma_scale_ooc can reuse ONE factor object
    across a sigma sweep via OOCCholeskyF.refactor() instead of a fresh
    init/close cycle per scale -- see refactor()'s docstring in
    gp_ooc_fortran.py for why that matters.

    `weights` (n_years,), if given, is the OOC-scale counterpart of
    gp_loss_model.py's _repeated_measures_lml_weighted -- each year's
    quadratic-form contribution is scaled by weights[t], and the
    logdet/normalization terms use sum(weights) instead of n_years, so a
    GaussianMixture component's posterior responsibility can be used
    directly instead of a hard year subset. Default (None) is equivalent
    to all-ones (unweighted, exactly the original behavior)."""
    n = coords.shape[0]
    n_years = R.shape[0]
    w = np.ones(n_years) if weights is None else np.asarray(weights, dtype=np.float64)
    total_quad = 0.0
    worst_relres = 0.0
    t0 = time.perf_counter()
    for t in range(n_years):
        y_t = cp.asarray(R[t], dtype=cp.float64)
        alpha, relres, n_ir, ok = gp_core.spd_solve_ir(
            fac, kern, coords, y_t, tol=tol, max_ir=max_ir,
            potrs=lambda F, r: F.potrs_inplace(r))
        total_quad += float(w[t]) * float(y_t @ alpha)
        worst_relres = max(worst_relres, relres)
    t_solve = time.perf_counter() - t0
    eff_n = float(w.sum())
    lml = (-0.5 * total_quad - 0.5 * eff_n * fac.logdet
           - 0.5 * eff_n * n * np.log(2 * np.pi))
    return dict(lml=float(lml), worst_relres=float(worst_relres),
                t_solve=t_solve, n_years=n_years, eff_n_years=eff_n)


def evaluate_ooc_lml(coords, R, ell, sigma_f2, sigma_n2, backing_dir,
                      b=2048, R_chunk=4096, ram_budget_gb=16.0, tol=1e-5, max_ir=5,
                      verbose=False):
    """Repeated-measures LML (gp_loss_model.py's definition) at OOC scale:
    ONE gp_ooc_fortran factor, then one IR solve per year of R (n_years,n),
    reusing the same factored panels. Returns dict(lml, worst_relres,
    t_factor, t_solve, n_years)."""
    kern = gp_core.Kernel(ell=ell, sigma_f=np.sqrt(sigma_f2), sigma_n2=sigma_n2, kind="rbf")

    t0 = time.perf_counter()
    fac = gp_ooc.OOCCholeskyF(kern, coords, b=b, R=R_chunk, backing=backing_dir,
                              ram_budget_gb=ram_budget_gb, verbose=verbose)
    fac.factor()
    t_factor = time.perf_counter() - t0

    result = _evaluate_lml_on_factor(fac, kern, coords, R, tol=tol, max_ir=max_ir)
    fac.close()
    result["t_factor"] = t_factor
    return result


def refine_sigma_scale_ooc(coords, R, ell, sigma_f2_0, sigma_n2_0, backing_dir,
                            scales=(0.7, 1.0, 1.4), b=2048, R_chunk=4096,
                            ram_budget_gb=16.0, tol=1e-5, max_ir=5, verbose=False,
                            weights=None):
    """3-point joint scale sweep of (sigma_f2, sigma_n2) around a Phase-1-
    fitted starting point, each point evaluated via a REAL OOC factor+solve
    pass. Picks the highest-LML scale. Returns dict(sigma_f2, sigma_n2,
    scale, evals).

    Reuses ONE OOCCholeskyF across the whole sweep (init once, refactor()
    per scale, close once) rather than a fresh factor object per eval:
    panel geometry (coords/n/b/R/ram_budget) doesn't change across the
    sweep, only sigma does, and OOCCholeskyF.refactor() updates sigma
    in-place and re-factors reusing the existing pinned panel buffers.
    Repeated multi-GB pinned allocate/deallocate cycles (a fresh
    init/close per eval) measurably degrade over several cycles within one
    process -- see RESULTS_PHASE2.md's rerun notes, where this was
    diagnosed as the cause of a multi-hour stall.

    `weights` (n_years,), if given, is passed through to
    _evaluate_lml_on_factor -- see its docstring. Lets the OOC-scale
    refinement use a GaussianMixture component's soft responsibility
    directly (regime_mixture.fit_regime_mixture_soft's approach, ported to
    OOC scale) instead of R already being a hard-partitioned subset of
    years."""
    kern = gp_core.Kernel(ell=ell, sigma_f=np.sqrt(sigma_f2_0), sigma_n2=sigma_n2_0,
                          kind="rbf")
    fac = gp_ooc.OOCCholeskyF(kern, coords, b=b, R=R_chunk, backing=backing_dir,
                              ram_budget_gb=ram_budget_gb, verbose=verbose)
    evals = []
    try:
        for s in scales:
            t0 = time.perf_counter()
            fac.refactor(sigma_f2_0 * s, sigma_n2_0 * s)
            t_factor = time.perf_counter() - t0
            r = _evaluate_lml_on_factor(fac, kern, coords, R, tol=tol, max_ir=max_ir,
                                        weights=weights)
            r["t_factor"] = t_factor
            r["scale"] = s
            evals.append(r)
            print(f"    OOC eval scale={s:.2f}: lml={r['lml']:.1f} "
                  f"t_factor={r['t_factor']:.1f}s t_solve={r['t_solve']:.1f}s "
                  f"relres={r['worst_relres']:.2e}", flush=True)
    finally:
        fac.close()
    best = max(evals, key=lambda r: r["lml"])
    return dict(sigma_f2=sigma_f2_0 * best["scale"], sigma_n2=sigma_n2_0 * best["scale"],
                scale=best["scale"], evals=evals)


def sample_gp_scenarios_rff(mu, coords, ell, sigma_f2, sigma_n2, insured_value,
                             n_scenarios, n_features=800, seed=0, feature_seed=0):
    """RFF-based scenario sampler for the fitted spatial GP at OOC scale --
    see rff_sampler.py's docstring for why this, not an exact Cholesky
    sample, is used here."""
    n = coords.shape[0]
    phi = rff_features(coords, ell, n_features, seed=feature_seed)
    rng = np.random.default_rng(seed)
    z_m = rng.standard_normal((n_scenarios, n_features))
    z_n = rng.standard_normal((n_scenarios, n))
    w = np.sqrt(sigma_f2) * (z_m @ phi.T) + np.sqrt(sigma_n2) * z_n
    log_ratio = mu[None, :] + w
    return np.exp(log_ratio) * insured_value[None, :]
