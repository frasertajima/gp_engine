#!/usr/bin/env python3
"""Phase 2 -- RKHS (Gaussian / Matern-3/2) marker kernel vs Phase 1's fixed
linear GRM (LAB_PLAN.md). This is the actual gp_engine value-add MPDOK never
had: MPDOK's `gblup.py` only ever fits the linear VanRaden GRM (a fixed
kernel); here the *shape* of the kernel is fit too, via marginal likelihood,
on raw marker dosage (`X`) instead of the precomputed GRM (`A`).

Same 5-fold split, same wheat/mice data (`MPDOK/gblup/data/`, read in place --
see RESULTS_PHASE0.md / RESULTS_PHASE1.md for full MPDOK provenance notes).

Literature context (to verify before calling this a "beat," per LAB_PLAN.md's
Phase 2 note): Gianola & van Kaam 2008 and de los Campos et al. 2009/2010
compared a Gaussian/RKHS marker kernel against linear GBLUP, in some cases on
these exact BGLR wheat/mice sets -- worth locating and citing precisely rather
than treating this run as the first such comparison ever made.

Run inside conda py314 (needs cupy):
    /var/home/fraser/miniconda3/envs/py314/bin/python run_phase2.py
"""

import time

import cupy as cp
import numpy as np

import datasets
from gblup_hyperopt import mle_fit_rkhs
from marker_kernel import apply_kernel, cross_squared_dist, squared_dist_matrix
from run_phase1 import predict_r_nll  # generic over A_base/A_cross, reused as-is

# Phase 0 (== MPDOK live cv_lambda_sweep) and Phase 1 (MLE linear GRM) r,
# from RESULTS_PHASE0.md / RESULTS_PHASE1.md
PHASE0_R = {"wheat/E1": 0.4264, "wheat/E2": 0.3880, "wheat/E3": 0.3678,
           "wheat/E4": 0.4534, "mice/bmi": 0.1378}
PHASE1_R = {"wheat/E1": 0.4232, "wheat/E2": 0.3860, "wheat/E3": 0.3518,
           "wheat/E4": 0.4516, "mice/bmi": 0.1378, "mice/blen": 0.1049}


def phase2_trait(X, y, label, kind="rbf", k=5, seed=42):
    splits = datasets.kfold_indices(len(y), k=k, seed=seed)
    fold_r, fold_nll_mean, fold_nll_med, fold_patho = [], [], [], []
    fold_ell, fold_sf2, fold_sn2 = [], [], []
    t0 = time.time()
    for train, val in splits:
        X_tt, X_vt = X[train], X[val]
        D2_train = squared_dist_matrix(X_tt)
        mle = mle_fit_rkhs(D2_train, y[train], kind=kind)
        A_base = cp.asnumpy(apply_kernel(D2_train, mle["ell"], kind=kind))
        D2_cross = cross_squared_dist(X_vt, X_tt)
        A_cross = cp.asnumpy(apply_kernel(D2_cross, mle["ell"], kind=kind))
        r, nll_m, nll_med, n_patho, ok = predict_r_nll(
            A_base, y[train], A_cross, y[val], mle["sigma_f2"], mle["sigma_n2"])
        fold_r.append(r)
        fold_nll_mean.append(nll_m)
        fold_nll_med.append(nll_med)
        fold_patho.append(n_patho)
        fold_ell.append(mle["ell"])
        fold_sf2.append(mle["sigma_f2"])
        fold_sn2.append(mle["sigma_n2"])
    dt = time.time() - t0
    mean_r = float(np.mean(fold_r))
    mean_nll_med = float(np.mean(fold_nll_med))
    total_patho = int(np.sum(fold_patho))
    p0, p1 = PHASE0_R.get(label), PHASE1_R.get(label)
    d0 = f"{mean_r - p0:+.4f}" if p0 is not None else "n/a"
    d1 = f"{mean_r - p1:+.4f}" if p1 is not None else "n/a"
    patho_flag = f"  [{total_patho} pathological pts]" if total_patho else ""
    print(f"[{label}/{kind}] r={mean_r:.4f}  vs Phase0={d0}  vs Phase1-linear={d1}  "
         f"NLL median={mean_nll_med:.3f}{patho_flag}  "
         f"ell={np.mean(fold_ell):.4g} sigma_f2={np.mean(fold_sf2):.4g} "
         f"sigma_n2={np.mean(fold_sn2):.4g}  ({dt:.1f}s)")
    return dict(label=label, kind=kind, mean_r=mean_r, mean_nll_med=mean_nll_med,
               n_pathological=total_patho, fold_patho=fold_patho)


def main():
    print("=== wheat (Crossa et al. 2010) -- RKHS marker kernel, no CV peeking ===")
    w = datasets.load_wheat()
    results = []
    for i, trait in enumerate(w["trait_names"]):
        for kind in ("rbf", "matern32"):
            results.append(phase2_trait(w["X"], w["Y"][:, i], f"wheat/{trait}", kind=kind))

    print()
    print("=== mice (Valdar et al. 2006) ===")
    m = datasets.load_mice()
    for kind in ("rbf", "matern32"):
        results.append(phase2_trait(m["X"], m["y_bmi"], "mice/bmi", kind=kind))
        results.append(phase2_trait(m["X"], m["y_blen"], "mice/blen", kind=kind))

    print()
    print("=== wheat/E3 calibration check: did RKHS fix Phase 1's fold-4 variance collapse? ===")
    e3 = [r for r in results if r["label"] == "wheat/E3"]
    for r in e3:
        print(f"  {r['kind']:9s} pathological points per fold: {r['fold_patho']} "
             f"(Phase 1 linear GRM had 46 in fold 4)")

    print()
    print("=== summary (RKHS r minus Phase0 CV-grid r / Phase1 MLE-linear r) ===")
    for r in results:
        p0, p1 = PHASE0_R.get(r["label"]), PHASE1_R.get(r["label"])
        d0 = f"{r['mean_r'] - p0:+.4f}" if p0 is not None else "n/a"
        d1 = f"{r['mean_r'] - p1:+.4f}" if p1 is not None else "n/a"
        print(f"  {r['label']:12s} {r['kind']:9s} vsPhase0={d0}  vsPhase1={d1}")


if __name__ == "__main__":
    main()
