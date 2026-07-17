#!/usr/bin/env python3
"""Phase 4: per-pathfinder-element ARD lengthscales.

Phase 1 fit a single pooled Matern-3/2 lengthscale (70.99 km) over the two
spatial dimensions alone. This phase adds the six pathfinder elements
(As/Sb/Ag/Cu/Zn/Tl, `datasets.spatial_pathfinder_features`, d=8) and fits a
*separate* lengthscale per dimension via Nelder-Mead maximization of the
Laplace-approximate log marginal likelihood -- same optimizer/convention
`gp_hyperopt.py`/`gblup_hyperopt.py` already use for GP regression ARD, now
applied to `gp_classifier.py`'s `LaplaceBinaryGPC` for the first time (the
scalar-ell -> vector-ell extension this phase needed; see gp_classifier.py's
`LaplaceBinaryGPC` docstring and `LAB_PLAN.md` Phase 4).

Carlin-type deposits have known pathfinder theory: arsenic, antimony, and
thallium co-occur with invisible gold in arsenian pyrite (mining_mpdok's own
README), while copper/zinc/silver are a base-metal contrast group with no
particular reason to track Carlin-style mineralisation. The question: do the
*fitted* lengthscales reproduce that ranking, or is it not visible in this
data at this scale?

Reading ARD lengthscales: a SHORT lengthscale means the kernel decorrelates
fast along that axis -- the dimension is doing real work explaining the
data. A LONG lengthscale (relative to the dimension's own data spread) means
the kernel is nearly flat along that axis -- ARD is effectively pruning it.
So "As/Sb/Tl are more informative than Cu/Zn/Ag" predicts *shorter*
lengthscales for the former, relative to each dimension's own spread (raw
ell isn't comparable across dimensions in different units -- km for the
spatial pair, natural-log-ppm for the geochemical six -- so this script
reports both raw ell and ell/std(dim) per dimension).

Usage: python3 pathfinder_ard.py [--n-seeds 50]
Writes results/pathfinder_ard.json.
"""

import argparse
import json
import math
import os
import sys
import time

import cupy as cp
import numpy as np
from scipy.optimize import minimize
from sklearn.svm import SVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datasets import PATHFINDER_ELEMENTS, load_split
from gp_classifier import LaplaceBinaryGPC
from run_lab import (KERNEL_KIND, average_precision_score, eval_binary,
                      imbalance_stats, log_loss_binary, median_pairwise_dist)

DIM_NAMES = ["x_km", "y_km"] + PATHFINDER_ELEMENTS


def fit_ard_lengthscales(X_train, y_train, maxfev=None, verbose=True):
    """Nelder-Mead over log(ell_1..ell_8, sigma_f), maximizing
    LaplaceBinaryGPC's Laplace-approximate log marginal likelihood on the
    training fold. Same pattern as gp_hyperopt.py's ARD path (theta =
    per-dim ell + sigma_f + sigma_n), minus sigma_n -- the classification
    likelihood has no separate noise variance to fit."""
    d = X_train.shape[1]
    n_ell = d
    if maxfev is None:
        maxfev = 40 * (n_ell + 1)  # lighter than gp_hyperopt's 60x -- one fit here is ~0.5-1s, not a GEMM-bound regression solve

    spans = X_train.max(axis=0) - X_train.min(axis=0)
    ell0 = 0.2 * spans
    start = np.concatenate([ell0, [1.0]])  # sigma_f0 = 1.0

    history = []

    def objective(logp):
        p = np.exp(logp)
        ell, sigf = p[:n_ell], p[n_ell]
        clf = LaplaceBinaryGPC(ell=ell, sigma_f=sigf, kind=KERNEL_KIND)
        t0 = time.time()
        try:
            clf.fit(X_train, y_train)
            lml = clf.fit_info.log_marginal
            if not math.isfinite(lml):
                lml = -1e12
        except Exception:
            lml = -1e12
        dt = time.time() - t0
        history.append((ell.tolist(), float(sigf), float(lml), dt))
        if verbose:
            print(f"    eval {len(history):3d}: LML={lml:12.1f}  sigma_f={sigf:.3f}  ({dt:.2f}s)", flush=True)
        return -lml

    t0 = time.time()
    res = minimize(objective, np.log(start), method="Nelder-Mead",
                    options=dict(maxfev=maxfev, xatol=1e-2, fatol=1.0))
    wall = time.time() - t0
    p = np.exp(res.x)
    ell, sigma_f = p[:n_ell], float(p[n_ell])
    print(f"NM done: {res.nfev} evals, {wall:.0f}s, LML={-res.fun:.1f}")
    return ell, sigma_f, {"nfev": res.nfev, "wall_s": wall, "lml": -res.fun, "history": history}


def run_one_seed(seed, ell_ard, sigma_f, svm_gamma, frac_train, frac_val, cutoff_quantile):
    (X_train, y_train), _, (X_test, y_test) = load_split(
        feature_set="spatial_pathfinder", frac_train=frac_train, frac_val=frac_val,
        seed=seed, cutoff_quantile=cutoff_quantile)

    gpc = LaplaceBinaryGPC(ell=ell_ard, sigma_f=sigma_f, kind=KERNEL_KIND)
    gpc.fit(X_train, y_train)
    _, _, p1 = gpc.predict(X_test)
    gpc_p1 = cp.asnumpy(p1)

    mu, sigma = X_train.mean(axis=0), X_train.std(axis=0)
    sigma[sigma < 1e-12] = 1.0
    Xtr_s, Xte_s = (X_train - mu) / sigma, (X_test - mu) / sigma
    svm = SVC(kernel="rbf", gamma=svm_gamma, probability=True, random_state=seed)
    svm.fit(Xtr_s, y_train)
    svm_probs = svm.predict_proba(Xte_s)
    p1_col = list(svm.classes_).index(1)
    svm_p1 = svm_probs[:, p1_col]

    def stats(p1):
        labels, conf, correct = eval_binary(y_test, p1)
        wrong = conf[correct == 0]
        return {
            "accuracy": float(correct.mean()),
            "average_precision": float(average_precision_score(y_test, p1)),
            "log_loss": log_loss_binary(y_test, p1),
            "n_wrong": int((correct == 0).sum()),
            "n_confidently_wrong_gt_0.9": int((wrong > 0.9).sum()),
            "frac_confidently_wrong_gt_0.9": float((wrong > 0.9).mean()) if wrong.size else None,
        }

    return {"seed": seed, "gpc_ard": stats(gpc_p1), "svm": stats(svm_p1)}


def pooled_confident_wrong(model, runs):
    n_wrong = np.array([r[model]["n_wrong"] for r in runs])
    n_cw = np.array([r[model]["n_confidently_wrong_gt_0.9"] for r in runs])
    rng = np.random.default_rng(0)
    n = len(runs)
    boots = []
    for _ in range(10000):
        idx = rng.integers(0, n, n)
        num, den = n_cw[idx].sum(), n_wrong[idx].sum()
        if den > 0:
            boots.append(num / den)
    boots = np.array(boots)
    point = n_cw.sum() / n_wrong.sum()
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return point, lo, hi, int(n_wrong.sum()), int(n_cw.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=50)
    ap.add_argument("--frac-train", type=float, default=0.6)
    ap.add_argument("--frac-val", type=float, default=0.2)
    ap.add_argument("--cutoff-quantile", type=float, default=0.95)
    ap.add_argument("--maxfev", type=int, default=None)
    ap.add_argument("--out", type=str, default="results/pathfinder_ard.json")
    args = ap.parse_args()

    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_split(
        feature_set="spatial_pathfinder", frac_train=args.frac_train,
        frac_val=args.frac_val, seed=0, cutoff_quantile=args.cutoff_quantile)

    print(f"Fitting ARD lengthscales on seed-0 train fold (n={len(y_train)}, d={X_train.shape[1]})...")
    ell_ard, sigma_f, nm_info = fit_ard_lengthscales(X_train, y_train, maxfev=args.maxfev)

    stds = X_train.std(axis=0)
    print(f"\n{'dim':>10}  {'ell (raw units)':>16}  {'ell / std(dim)':>16}")
    for name, e, s in zip(DIM_NAMES, ell_ard, stds):
        print(f"{name:>10}  {e:16.3f}  {e/s:16.3f}")

    pathfinder_idx = list(range(2, 8))
    pf_ratio = {name: float(ell_ard[i] / stds[i]) for i, name in zip(pathfinder_idx, PATHFINDER_ELEMENTS)}
    carlin_pathfinders = ["As_ppm", "Sb_ppm", "Tl_ppm"]
    base_metals = ["Ag_ppm", "Cu_ppm", "Zn_ppm"]
    carlin_mean = np.mean([pf_ratio[e] for e in carlin_pathfinders])
    base_mean = np.mean([pf_ratio[e] for e in base_metals])
    print(f"\nMean ell/std -- Carlin pathfinders (As/Sb/Tl): {carlin_mean:.3f}   "
          f"Base metals (Ag/Cu/Zn): {base_mean:.3f}")
    print(f"Carlin pathfinders {'SHORTER (more informative)' if carlin_mean < base_mean else 'LONGER (less informative)'} "
          f"than base metals, by this fit.")

    # Validation AP with the fitted ARD lengthscales (sanity check the fit
    # is actually useful, not just a high-LML degenerate solution).
    gpc_ard = LaplaceBinaryGPC(ell=ell_ard, sigma_f=sigma_f, kind=KERNEL_KIND)
    gpc_ard.fit(X_train, y_train)
    _, _, p1_val = gpc_ard.predict(X_val)
    val_ap = float(average_precision_score(y_val, cp.asnumpy(p1_val)))
    print(f"\nARD-GPC validation AP: {val_ap:.3f}")

    # SVM baseline on the same 8 features (standardized -- an isotropic RBF
    # over raw km + log-ppm units would be dominated by the km-scale spatial
    # dims otherwise). Small ell grid on standardized features, same
    # median-heuristic + AP-selection convention as run_lab.py.
    mu, sigma = X_train.mean(axis=0), X_train.std(axis=0)
    sigma[sigma < 1e-12] = 1.0
    Xtr_s, Xv_s = (X_train - mu) / sigma, (X_val - mu) / sigma
    rng = np.random.default_rng(0)
    ell0 = median_pairwise_dist(Xtr_s, rng)
    best = None
    for ellc in [ell0 * f for f in (0.5, 0.75, 1.0, 1.5, 2.0)]:
        gamma = 1.0 / (2.0 * ellc ** 2)
        svm = SVC(kernel="rbf", gamma=gamma, probability=True, random_state=0)
        svm.fit(Xtr_s, y_train)
        p1_col = list(svm.classes_).index(1)
        ap = float(average_precision_score(y_val, svm.predict_proba(Xv_s)[:, p1_col]))
        print(f"  SVM ellc={ellc:.2f}  val_AP={ap:.3f}")
        if best is None or ap > best["ap"]:
            best = {"gamma": gamma, "ap": ap}
    svm_gamma = best["gamma"]
    print(f"selected SVM gamma={svm_gamma:.5f} (val_AP={best['ap']:.3f})")

    print(f"\nRunning {args.n_seeds}-seed comparison (fixed ARD ell / SVM gamma)...")
    results = []
    t_start = time.time()
    for i in range(args.n_seeds):
        t0 = time.time()
        r = run_one_seed(i, ell_ard, sigma_f, svm_gamma, args.frac_train,
                          args.frac_val, args.cutoff_quantile)
        dt = time.time() - t0
        elapsed = time.time() - t_start
        print(f"[{i+1}/{args.n_seeds}] seed={i}  "
              f"gpc_ard_AP={r['gpc_ard']['average_precision']:.3f}  "
              f"svm_AP={r['svm']['average_precision']:.3f}  ({dt:.2f}s, elapsed={elapsed:.0f}s)", flush=True)
        results.append(r)

    out = {
        "n_seeds": args.n_seeds, "kernel_kind": KERNEL_KIND,
        "dim_names": DIM_NAMES, "ell_ard": ell_ard.tolist(), "sigma_f": sigma_f,
        "ell_over_std": (ell_ard / stds).tolist(), "svm_gamma": svm_gamma,
        "nm_lml": nm_info["lml"], "nm_nfev": nm_info["nfev"], "nm_wall_s": nm_info["wall_s"],
        "val_ap_ard": val_ap,
        "pf_ratio": pf_ratio, "carlin_mean_ell_std": carlin_mean, "base_metal_mean_ell_std": base_mean,
        "frac_train": args.frac_train, "frac_val": args.frac_val,
        "cutoff_quantile": args.cutoff_quantile,
        "wall_time_s": time.time() - t_start,
        "runs": results,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f)
    print(f"\nwrote {args.out}")

    gpc_ap = np.array([r["gpc_ard"]["average_precision"] for r in results])
    svm_ap = np.array([r["svm"]["average_precision"] for r in results])
    print(f"\n=== {args.n_seeds}-seed comparison, spatial+pathfinder (d=8) ===")
    print(f"Average precision: GPC-ARD {gpc_ap.mean():.3f}+/-{gpc_ap.std():.3f}   "
          f"SVM {svm_ap.mean():.3f}+/-{svm_ap.std():.3f}")

    gpc_point, gpc_lo, gpc_hi, gpc_tw, gpc_tcw = pooled_confident_wrong("gpc_ard", results)
    svm_point, svm_lo, svm_hi, svm_tw, svm_tcw = pooled_confident_wrong("svm", results)
    print(f"Confidently-wrong-on-a-miss (pooled, 95% CI):")
    print(f"  GPC-ARD: {100*gpc_point:.1f}% [{100*gpc_lo:.1f}%, {100*gpc_hi:.1f}%]  ({gpc_tcw}/{gpc_tw})")
    print(f"  SVM:     {100*svm_point:.1f}% [{100*svm_lo:.1f}%, {100*svm_hi:.1f}%]  ({svm_tcw}/{svm_tw})")
    print(f"\nCompare against Phase 1's spatial-only GPC: AP 0.240+/-0.053, "
          f"confident-wrong 52.8% [51.7,53.9]")


if __name__ == "__main__":
    main()
