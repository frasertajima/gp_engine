#!/usr/bin/env python3
"""GP Lab benchmark runner — full protocol per LAB_PLAN.md.

    python run_benchmark.py kin40k --repeats 3

Pipeline per repeat (seeded): load standardized split -> staged hyperparameter
optimization -> final fit at tight tol -> predict -> metrics -> results JSON.

Staged optimizer (the fix for Nelder-Mead burning ~600 full-cost evals at
d+2 params): hyperparameters are largely stable in n for large n, so
  stage A: isotropic (3 params) on a cheap subsample        (~60 evals, cheap)
  stage B: ARD (d+2 params) on the subsample, from A        (~400 evals, cheap)
  stage C: short full-data polish from B                    (~60 evals, full)
Full-cost evals drop ~10x vs naive full-data ARD NM.

Nugget floor: sigma_n^2 = floor^2 + exp(2*theta), so noiseless datasets
(kin40k is a deterministic simulator) cannot push the nugget to zero and out
of the FP32-IR envelope. FactorError / IR breakdown still return a penalty,
so the optimizer routes around any remaining kappa wall.
"""

import argparse
import json
import math
import os
import time

import cupy as cp
import numpy as np
from scipy.optimize import minimize

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir))
from gp_core import FactorError, Kernel, gp_fit, gp_predict   # noqa: E402
from gp_hyperopt import lml_mp                                # noqa: E402
# Two OOC backends share one call shape. Default is the CUDA Fortran port
# (gp_ooc_solver.so via gp_ooc_fortran) — validated bit-identical vs the
# Python backend at 12k/60k/100k/200k and the only one that has completed
# n=391k (the Python streaming layer hit host-memory-pressure hangs there;
# see LAB_PLAN.md M4 + ../CUDA_FORTRAN_STREAMING_LESSONS.md). The Python
# backend stays available as the cross-check oracle (--ooc-backend python).
import gp_ooc                                                  # noqa: E402
import gp_ooc_fortran                                          # noqa: E402
_OOC_BACKENDS = {"fortran": gp_ooc_fortran, "python": gp_ooc}

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "results")
PANELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "ooc_panels")
PENALTY = 1e12
LOG2PI = math.log(2.0 * math.pi)

# In-core VRAM headroom (Phase 1 measured n=40k at 7.0 GB on an 8 GB card).
# A full-data LML eval builds K32 alongside other live state (X, IR scratch),
# so we cap slightly below that observed ceiling.
IN_CORE_MAX = 38000
# Above this n, OOC is a deliberate multi-tens-of-GB-panel job (M4/3droad
# territory, hours not minutes) — require --allow-large-ooc rather than
# have a routine M2/M3 invocation accidentally kick one off.
OOC_AUTO_MAX = 150000

# A single one-off full-data LML eval (hyperopt stage C) is a different
# risk calculus than the FIT going OOC: it's one build, not hundreds, so
# it's worth affording slightly past IN_CORE_MAX (Phase 1 proved n=40,000
# safe at 7.0 GB / 8 GB card). Guarded with a try/except OOM fallback
# below regardless.
FULL_POLISH_MAX = 42000


def _kernel(theta, d, kind, ard, floor):
    """theta = log(ell_1..ell_k), log(sigma_f), raw noise param."""
    n_ell = d if ard else 1
    ell = np.exp(theta[:n_ell])
    sigf = math.exp(theta[n_ell])
    sign2 = floor ** 2 + math.exp(2.0 * theta[n_ell + 1])
    return Kernel(ell if ard else float(ell[0]), sigma_f=sigf,
                  sigma_n2=sign2, kind=kind)


def _neg_lml(theta, X, y, d, kind, ard, floor, tol, counter, best):
    """best: {'loss': inf, 'theta': None} — tracks the best NON-penalty
    point seen across the whole search. Nelder-Mead's own res.x can
    legitimately BE a penalty point (measured: on `bike`, the final simplex
    wandered into all-infeasible territory near the noise floor and NM's
    reported minimum was a PENALTY value, `argmin` over a region where
    every candidate was infeasible) — the caller must use this tracker,
    not res.x, to recover a real optimum."""
    kern = _kernel(theta, d, kind, ard, floor)
    counter[0] += 1
    try:
        lml, relres = lml_mp(kern, X, y, tol=tol)
        loss = PENALTY if relres > 1e-3 else -lml
    except FactorError:
        loss = PENALTY
    if loss < best["loss"]:
        best["loss"] = loss
        best["theta"] = theta.copy()
    return loss


def optimize_hyperparams(Xtr, ytr, kind="matern32", ard=True, n_sub=8000,
                         floor=1e-3, seed=0, verbose=True, full_polish=True,
                         method="nm", tol_final=1e-10, max_ir=16):
    """Staged hyperopt. Returns (kernel, info dict).

    method="nm" (default): the original staged Nelder-Mead (A: iso
    subsample, B: ARD subsample, C: full-data polish).

    method="hybrid": adds stage B2 between B and C — bounded L-BFGS-B
    with finite-difference gradients over the SAME subsample LML
    objective, warm-started from B's optimum. Rationale (RESULTS_LAB.md
    §4.1 follow-up): NM under-converges in high-d ARD spaces (pol, d=26:
    lengthscales for the same data swing 14x across seeds), trading RMSE
    for noise; a local gradient polish sharpens the optimum NM located.
    The objective is deterministic (same theta -> bit-identical LML via
    the FP32-factor+IR path), so FD gradients are well-defined; eps=1e-3
    on log-params keeps FD differences well above the FP32-factor's LML
    error. Box bounds (log-ell in [-6,6] etc.) also hard-prevent runaway
    lengthscale pruning. No new engine machinery: gradient-free at the
    engine level, gradients exist only as scipy-side finite differences.

    full_polish=False skips stage C (full-data eval) entirely — used when
    n_train exceeds the in-core VRAM headroom (IN_CORE_MAX): a full-data
    LML eval there would build a K32 at the same size as an in-core gp_fit,
    which is exactly the regime we don't want the search loop repeatedly
    hitting. The last subsample stage's theta is used as final in that
    case; the OOC fit's own IR is a far more thorough check of that theta
    than one more low-tol NM eval would have been anyway.
    """
    n, d = Xtr.shape
    rng = np.random.default_rng(seed)
    sub = rng.permutation(n)[:min(n_sub, n)]
    Xs, ys = cp.asarray(Xtr[sub]), cp.asarray(ytr[sub])
    counter = [0]
    t0 = time.perf_counter()

    def run(theta0, X, y, is_ard, maxfev, tol):
        best = {"loss": math.inf, "theta": None}
        res = minimize(
            _neg_lml, theta0, method="Nelder-Mead",
            args=(X, y, d, kind, is_ard, floor, tol, counter, best),
            options=dict(maxfev=maxfev, xatol=1e-2, fatol=0.25))
        if best["loss"] >= PENALTY:
            # best["theta"] is NOT None here (the first eval always sets it,
            # since loss < inf trivially) — checking "is None" is dead code
            # and was the actual bug: an entirely-infeasible search would
            # silently return whatever theta happened to be tried first.
            raise RuntimeError(
                "hyperopt stage found NO feasible (non-penalty) point in "
                f"{maxfev} evals — every candidate was either not SPD in "
                f"FP32 or broke IR. Try a higher --floor (current nugget "
                f"floor may be too small for this dataset's conditioning).")
        if res.fun > best["loss"]:
            # NM's own argmin was itself a penalty point (measured on
            # `bike`: the final simplex was entirely infeasible) — use the
            # tracked best instead of trusting res.x blindly.
            res.x, res.fun = best["theta"], best["loss"]
        return res

    # stage A: isotropic on subsample
    spans = Xtr.max(axis=0) - Xtr.min(axis=0)
    ystd = float(np.std(ytr))
    thA0 = np.log([0.2 * float(np.median(spans)), ystd, 0.3 * ystd])
    resA = run(thA0, Xs, ys, False, 80, 1e-7)
    evals_A = counter[0]

    # stage B: ARD on subsample, seeded from A
    if ard:
        thB0 = np.concatenate([np.full(d, resA.x[0]), resA.x[1:]])
        resB = run(thB0, Xs, ys, True, 60 * (d + 2), 1e-7)
    else:
        resB = resA
    evals_B = counter[0] - evals_A

    # stage B2 (method="hybrid" only): bounded L-BFGS-B, FD gradients,
    # same subsample objective, warm-started from B. A B2 candidate is
    # accepted only if (a) it improves on B's best feasible subsample
    # LML AND (b) it survives a feasibility eval at min(n, FULL_POLISH_MAX)
    # points that checks REAL convergence to the fit's own tol_final/
    # max_ir — not the loose relres>1e-3 threshold _neg_lml's PENALTY
    # logic uses internally for the subsample search stages.
    #
    # (b) is not optional, and the strict tol_final/max_ir check is not
    # optional either — first version of this gate used _neg_lml's
    # relres>1e-3 pass/fail and still let a bad candidate through: kin40k
    # (paper split) seed 1 passed that loose check yet the REAL fit
    # (tol_final=1e-10-ish, max_ir=16) landed at kappa~4.5e10 and never
    # converged (relres ~5e-7, capped at max_ir, converged=False) — a
    # softer failure than the original ungated case (kappa~1.6e11,
    # relres~7e-2) but still not a real solve. Checking gp_fit's own
    # `.converged` at the SAME tol_final/max_ir the real fit will use
    # closes that gap. NM's stage-B result is never mutated — every
    # fallback path below keeps the original B optimum.
    evals_B2 = 0
    theta_seed = resB.x   # what stage C starts from (B, or accepted B2)
    if method == "hybrid":
        n_ell = d if ard else 1
        bounds = ([(-6.0, 6.0)] * n_ell        # log-ell: e^-6..e^6 on
                  + [(-4.0, 4.0)]              # whitened data; log-sigma_f
                  + [(-8.0, 4.0)])             # raw noise param
        bestB2 = {"loss": math.inf, "theta": None}
        try:
            minimize(_neg_lml, resB.x, method="L-BFGS-B",
                     args=(Xs, ys, d, kind, ard, floor, 1e-7,
                           counter, bestB2),
                     bounds=bounds,
                     options=dict(maxfun=60 * (d + 2), eps=1e-3))
        except Exception as e:
            # FD across a penalty cliff can, in principle, upset scipy;
            # B's optimum remains a valid fallback either way.
            if verbose:
                print(f"    hyperopt stage B2 aborted ({e}); keeping B",
                      flush=True)
        if (bestB2["theta"] is not None
                and bestB2["loss"] < PENALTY
                and bestB2["loss"] < resB.fun):
            # feasibility gate at (near-)full scale: a REAL fit at the
            # exact tol_final/max_ir the final run will use, requiring
            # .converged — not a loose LML-evaluability check.
            n_val = min(n, FULL_POLISH_MAX)
            vsub = rng.permutation(n)[:n_val]
            Xv, yv = cp.asarray(Xtr[vsub]), cp.asarray(ytr[vsub])
            counter[0] += 1
            gate_ok = False
            try:
                kern_v = _kernel(bestB2["theta"], d, kind, ard, floor)
                fit_v = gp_fit(kern_v, Xv, yv, tol=tol_final, max_ir=max_ir)
                gate_ok = bool(fit_v.converged)
            except FactorError:
                gate_ok = False
            finally:
                del Xv, yv
                cp.get_default_memory_pool().free_all_blocks()
            if gate_ok:
                theta_seed = bestB2["theta"]
            elif verbose:
                print(f"    hyperopt: B2 candidate improved subsample LML "
                      f"but FAILED the n={n_val} feasibility eval (did not "
                      f"converge at tol={tol_final:.0e}/max_ir={max_ir} — "
                      f"kappa wall) — keeping NM's optimum", flush=True)
        evals_B2 = counter[0] - evals_A - evals_B

    # stage C: short full-data polish (skipped above FULL_POLISH_MAX; a
    # single one-off eval, so this is affordable slightly past IN_CORE_MAX
    # even when the FIT itself will go OOC — but caught in case VRAM is
    # tighter than expected on a given machine/session).
    if full_polish:
        Xf, yf = cp.asarray(Xtr), cp.asarray(ytr)
        try:
            resC = run(theta_seed, Xf, yf, ard,
                       8 * (d + 2) if ard else 60, 1e-8)
            lml_report = -float(resC.fun)
            # Stage C's own PENALTY check inside `run` uses a loose
            # relres>1e-3 bar at tol=1e-8 (not this fit's real tol_final/
            # max_ir) — it can walk a perfectly good theta_seed into a
            # region that satisfies THAT loose bar but fails to converge
            # at the tolerance the actual fit will be judged by. Measured
            # on kin40k (paper split + hybrid): the B2 gate correctly
            # validated a candidate (converged=True, relres 7.9e-11) but
            # stage C's subsequent 80-eval polish, seeded from it, walked
            # to a theta that never converges at tol_final/max_ir
            # (relres ~1e-7, capped, converged=False every time —
            # confirmed not an FP32/ordering fluke, reproduced across 4
            # independent trials). This check applies regardless of
            # method — NM-only stage C is exposed to the exact same risk,
            # just less likely to wander there from a less-sharp seed —
            # so it's a general safety net, not hybrid-specific.
            kern_c = _kernel(resC.x, d, kind, ard, floor)
            fit_c = gp_fit(kern_c, Xf, yf, tol=tol_final, max_ir=max_ir)
            if not fit_c.converged:
                if verbose:
                    print(f"    hyperopt: stage C polish did not converge "
                          f"at tol={tol_final:.0e}/max_ir={max_ir} "
                          f"(relres={fit_c.relres:.1e}) — reverting to "
                          f"the pre-polish theta", flush=True)
                resC = type("R", (), {"x": theta_seed})()
                lml_report = None
        except (cp.cuda.memory.OutOfMemoryError, RuntimeError):
            # OOM: VRAM tighter than expected. RuntimeError: stage C found
            # no feasible point near stage B's optimum (rare — B already
            # found one — but possible near a conditioning cliff). Either
            # way, stage B's already-validated theta is the safe fallback.
            resC = resB
            lml_report = None
            full_polish = False   # record what actually happened
        finally:
            # Stage C's ~4n^2-byte K32 build (and NM's repeated rebuilds)
            # leave CuPy's memory pool holding several GB even after Xf/yf
            # go out of scope — del doesn't return pool blocks to the
            # driver. Without this, the subsequent OOC fit's first panel
            # allocation OOMs even though nothing is "really" using the
            # memory (measured: this exact failure at n=41157).
            del Xf, yf
            cp.get_default_memory_pool().free_all_blocks()
    else:
        resC = type("R", (), {"x": theta_seed})()   # B, or gate-passed B2
        lml_report = None    # not evaluated on full data; don't fabricate it
    evals_C = counter[0] - evals_A - evals_B - evals_B2
    wall = time.perf_counter() - t0

    kern = _kernel(resC.x, d, kind, ard, floor)
    info = dict(evals=dict(iso_sub=evals_A, ard_sub=evals_B,
                           lbfgsb_sub=evals_B2, full=evals_C),
                method=method,
                full_polish=full_polish, lml_full=lml_report, wall_s=wall,
                ell=np.atleast_1d(kern.ell).tolist(),
                sigma_f=math.sqrt(kern.sigma_f2),
                sigma_n=math.sqrt(kern.sigma_n2), floor=floor)
    if verbose:
        lml_s = f"{lml_report:.1f}" if lml_report is not None else "n/a (skipped)"
        print(f"    hyperopt[{method}]: {counter[0]} evals "
              f"(iso-sub {evals_A}, ard-sub {evals_B}, "
              f"lbfgsb-sub {evals_B2}, full {evals_C}) "
              f"in {wall:.0f}s -> sigma_n={info['sigma_n']:.4f}, "
              f"LML={lml_s}", flush=True)
    return kern, info


def kappa_bound(kern, X, iters=8):
    """Power-iteration lambda_max; kappa <= lambda_max / sigma_n^2 (loose
    for Matern, whose spectrum is bounded below without the nugget)."""
    n = X.shape[0]
    v = cp.random.default_rng(1).standard_normal(n)
    v /= cp.linalg.norm(v)
    lam = 0.0
    for _ in range(iters):
        w = kern.matvec(X, v)
        lam = float(cp.linalg.norm(w))
        v = w / lam
    return lam, lam / kern.sigma_n2


def run_one(name, seed, kind, ard, n_sub, floor, tol_final, verbose=True,
           ram_budget_gb=12.0, allow_large_ooc=False, max_ir=16,
           panel_b=4096, ooc_backend="fortran", protocol="lab",
           hyperopt_method="nm"):
    from datasets import load
    ds = load(name, seed=seed, protocol=protocol)
    m = ds["meta"]
    ooc = m["n_train"] > IN_CORE_MAX
    mode = "OOC" if ooc else "in-core"
    print(f"== {name} seed {seed}: train {m['n_train']} x {m['d']}, "
          f"test {m['n_test']}, kernel {kind}{' ARD' if ard else ''}  "
          f"[{mode}, {protocol} split, hyperopt {hyperopt_method}]",
          flush=True)
    if ooc and m["n_train"] > OOC_AUTO_MAX and not allow_large_ooc:
        raise RuntimeError(
            f"n_train={m['n_train']} exceeds OOC_AUTO_MAX={OOC_AUTO_MAX} — "
            f"this is a multi-tens-of-GB panel job (M4/3droad territory, "
            f"likely hours). Pass allow_large_ooc=True / --allow-large-ooc "
            f"once you mean to run it, ideally under a detached "
            f"compute.slice service (see RESULTS_PHASE2.md).")

    kern, hyp = optimize_hyperparams(ds["Xtr"], ds["ytr"], kind=kind,
                                     ard=ard, n_sub=n_sub, floor=floor,
                                     seed=seed, verbose=verbose,
                                     full_polish=m["n_train"] <= FULL_POLISH_MAX,
                                     method=hyperopt_method,
                                     tol_final=tol_final, max_ir=max_ir)
    # Hundreds of subsample-stage NM evals each alloc/free a K32 etc.;
    # CuPy's pool keeps freed blocks reserved (fragmentation-like), and the
    # full_polish path's own free_all_blocks() doesn't run when polish is
    # skipped (large-n OOC datasets always skip it). Without this, a big
    # OOC fit's first panel allocation can OOM against "phantom" reserved
    # memory that nothing is actually using (measured: exactly this, on
    # 3droad — ~1.3 GB reserved after 166 subsample evals).
    cp.get_default_memory_pool().free_all_blocks()
    Xtr, ytr = cp.asarray(ds["Xtr"]), cp.asarray(ds["ytr"])
    Xte, yte = cp.asarray(ds["Xte"]), cp.asarray(ds["yte"])

    extra = {}
    if ooc:
        be = _OOC_BACKENDS[ooc_backend]
        backing = os.path.join(PANELS_DIR, f"{name}_seed{seed}")
        # b=4096 is the only panel width ever validated end-to-end, in both
        # backends. (Shrinking b was tried for the n=391k/3droad case and
        # caused a real hang — more panels means more (panel, prior-panel)
        # pairs, ~27x more at b=1536 than at the proven b=4096.)
        b = panel_b or 4096
        fit = be.ooc_gp_fit(kern, Xtr, ytr, b=b, tol=tol_final,
                            max_ir=max_ir, backing=backing,
                            ram_budget_gb=ram_budget_gb, verbose=verbose)
        alpha, logdet = fit["alpha"], fit["logdet"]
        relres, n_ir, converged = fit["relres"], fit["n_ir"], fit["converged"]
        t_fit = fit["t_total"]
        extra = dict(t_factor=fit["t_factor"], t_ir=fit["t_ir"],
                    host_gb=fit["host_gb"],
                    tiers=fit["factor"].tier_summary(),
                    ooc_backend=ooc_backend)
        t0 = time.perf_counter()
        mean, var = be.ooc_predict(fit, kern, Xtr, Xte, include_noise=True)
        t_pred = time.perf_counter() - t0
        fit["factor"].close()
    else:
        t0 = time.perf_counter()
        fit = gp_fit(kern, Xtr, ytr, tol=tol_final, max_ir=max_ir)
        t_fit = time.perf_counter() - t0
        alpha, logdet = fit.alpha, fit.logdet
        relres, n_ir, converged = fit.relres, fit.n_ir, fit.converged
        t0 = time.perf_counter()
        mean, var = gp_predict(fit, kern, Xtr, Xte, include_noise=True)
        t_pred = time.perf_counter() - t0

    sd = cp.sqrt(var)
    rmse = float(cp.sqrt(cp.mean((mean - yte) ** 2)))
    nll_pt = 0.5 * cp.log(2 * cp.pi * var) + 0.5 * (yte - mean) ** 2 / var
    nll = float(cp.mean(nll_pt))
    nll_median = float(cp.median(nll_pt))
    # Points where the model is both near-certain and badly wrong (a real
    # GP pathology on data with near-duplicate X rows and label noise —
    # e.g. CASP/protein — not a code defect; see LAB_PLAN.md M2 notes).
    # Threshold: per-point NLL > 50 means resid^2/var alone exceeds ~100,
    # i.e. the residual is >10 predictive sigmas.
    n_pathological = int(cp.sum(nll_pt > 50))
    cover = float(cp.mean((yte > mean - 1.96 * sd)
                          & (yte < mean + 1.96 * sd)))
    lam_max, kap = kappa_bound(kern, Xtr)

    res = dict(dataset=name, seed=seed, kind=kind, ard=ard, mode=mode,
               protocol=protocol, hyperopt_method=hyperopt_method,
               n_train=m["n_train"], n_test=m["n_test"], d=m["d"],
               rmse=rmse, nll=nll, nll_median=nll_median,
               n_pathological=n_pathological, coverage95=cover,
               fit_s=t_fit, pred_s=t_pred, relres=relres,
               ir_steps=n_ir, converged=bool(converged),
               lambda_max=lam_max, kappa_bound=kap, hyperopt=hyp, **extra)
    print(f"    RMSE {rmse:.4f}  NLL {nll:.4f} (median {nll_median:.4f})  "
          f"cover95 {cover*100:.1f}%  pathological {n_pathological}/{len(yte)}"
          f"  | fit {t_fit:.1f}s relres {relres:.1e}/{n_ir} "
          f"(converged={converged})  kappa<= {kap:.1e}", flush=True)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    # Non-default protocol/optimizer runs get suffixed filenames so the
    # headline (lab-protocol, NM) results are never overwritten.
    tag = (("_papern" if protocol == "paper" else "")
           + ("_hybrid" if hyperopt_method == "hybrid" else ""))
    out = os.path.join(RESULTS_DIR, f"{name}_{kind}"
                       f"{'_ard' if ard else ''}{tag}_seed{seed}.json")
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    del fit, Xtr, ytr, Xte, yte
    cp.get_default_memory_pool().free_all_blocks()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--kind", default="matern32",
                    choices=["rbf", "matern32", "matern52"])
    ap.add_argument("--no-ard", action="store_true")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--n-sub", type=int, default=8000)
    ap.add_argument("--floor", type=float, default=1e-3,
                    help="nugget floor on sigma_n (std-y units)")
    ap.add_argument("--tol-final", type=float, default=1e-10)
    ap.add_argument("--ram-budget-gb", type=float, default=12.0,
                    help="OOC pinned-RAM panel budget (ignored in-core)")
    ap.add_argument("--allow-large-ooc", action="store_true",
                    help="permit n_train > OOC_AUTO_MAX (M4/3droad scale)")
    ap.add_argument("--max-ir", type=int, default=16,
                    help="IR step cap (Phase2b: large-n fits want >=16-20 "
                         "with tol=1e-9, not the tighter default)")
    ap.add_argument("--panel-b", type=int, default=0,
                    help="OOC panel width; 0 = default (4096, the only "
                         "value validated end-to-end)")
    ap.add_argument("--ooc-backend", default="fortran",
                    choices=["fortran", "python"],
                    help="OOC streaming backend: fortran (gp_ooc_solver.so, "
                         "default — the only one validated at n=391k) or "
                         "python (gp_ooc.py, kept as cross-check oracle)")
    ap.add_argument("--seeds", default=None,
                    help="comma-separated explicit seed list (overrides "
                         "--repeats), e.g. --seeds 0 for a single-seed "
                         "M4-scale run")
    ap.add_argument("--protocol", default="lab", choices=["lab", "paper"],
                    help="split protocol: lab (90/10, the headline runs) or "
                         "paper (train n = floor(0.64*N), matching Wang et "
                         "al. 2019's Tables 1/3 exactly — see datasets.py)")
    ap.add_argument("--hyperopt", default="nm", choices=["nm", "hybrid"],
                    help="hyperopt method: nm (staged Nelder-Mead) or hybrid "
                         "(NM + bounded FD-L-BFGS-B subsample polish)")
    args = ap.parse_args()

    dev = cp.cuda.runtime.getDeviceProperties(0)
    print(f"GPU: {dev['name'].decode()}")
    seeds = ([int(s) for s in args.seeds.split(",")] if args.seeds
             else list(range(args.repeats)))
    rows = []
    for seed in seeds:
        rows.append(run_one(args.dataset, seed, args.kind, not args.no_ard,
                            args.n_sub, args.floor, args.tol_final,
                            max_ir=args.max_ir, panel_b=args.panel_b,
                            ram_budget_gb=args.ram_budget_gb,
                            allow_large_ooc=args.allow_large_ooc,
                            ooc_backend=args.ooc_backend,
                            protocol=args.protocol,
                            hyperopt_method=args.hyperopt))
    r = np.array([x["rmse"] for x in rows])
    n_ = np.array([x["nll"] for x in rows])
    nm = np.array([x["nll_median"] for x in rows])
    c = np.array([x["coverage95"] for x in rows])
    p = np.array([x["n_pathological"] for x in rows])
    print(f"\n== {args.dataset} over {len(rows)} seed(s): "
          f"RMSE {r.mean():.4f} +/- {r.std():.4f}   "
          f"NLL {n_.mean():.4f} +/- {n_.std():.4f} "
          f"(median-of-points {nm.mean():.4f})   "
          f"cover95 {c.mean()*100:.1f}%   "
          f"pathological pts {p.mean():.1f}/{rows[0]['n_test']}")


if __name__ == "__main__":
    main()
