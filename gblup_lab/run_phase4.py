#!/usr/bin/env python3
"""Phase 4 -- train on 2014-2023, predict the real held-out 2024 G2F season.
See g2f_2024_eval.py's module docstring for provenance and the "downloaded
after every earlier result was already written" timing note.

No CV here: hyperparameters are fit by marginal likelihood on 2014-2023
training data ONLY (same no-peeking method validated in Phase 1), then used
once, unchanged, to predict the 2024 hybrids. This is as close to the real
competition task as a marker-only (no weather/soil/GxE) model can get.

Run inside conda py314 (needs cupy):
    /var/home/fraser/miniconda3/envs/py314/bin/python run_phase4.py
"""

import cupy as cp
import numpy as np

import g2f_2024_eval as ev
from gblup_hyperopt import mle_fit, mle_fit_rkhs
from marker_kernel import apply_kernel, cross_squared_dist, squared_dist_matrix
from run_phase1 import predict_r_nll


def fit_predict_linear(X_train, y_train, X_test, y_test):
    Xtc = X_train - X_train.mean(0, keepdims=True)
    Kt = Xtc @ Xtc.T
    Xvc = X_test - X_train.mean(0, keepdims=True)
    Kv = Xvc @ Xtc.T
    scale = float(np.mean(np.diag(Kt)))   # same FP32-envelope fix as Phase 3
    Kt, Kv = Kt / scale, Kv / scale
    mle = mle_fit(Kt, y_train)
    return predict_r_nll(Kt, y_train, Kv, y_test, mle["sigma_f2"], mle["sigma_n2"]), mle


def fit_predict_rkhs(X_train, y_train, X_test, y_test, kind="rbf"):
    D2_train = squared_dist_matrix(X_train)
    mle = mle_fit_rkhs(D2_train, y_train, kind=kind)
    A_base = cp.asnumpy(apply_kernel(D2_train, mle["ell"], kind=kind))
    D2_cross = cross_squared_dist(X_test, X_train)
    A_cross = cp.asnumpy(apply_kernel(D2_cross, mle["ell"], kind=kind))
    return predict_r_nll(A_base, y_train, A_cross, y_test,
                         mle["sigma_f2"], mle["sigma_n2"]), mle


def main():
    print("Loading genotypes + 2014-2023 train / 2024 test yield ...")
    d = ev.build_split()
    print(f"genotype matrix: {d['geno_shape']}, "
         f"{d['nan_frac']*100:.2f}% missing (mean-imputed)")
    print(f"train: {len(d['y_train'])} hybrids (2014-2023), "
         f"test: {len(d['y_test'])} hybrids (2024, held-out)")
    print(f"train/test hybrid overlap: {d['train_test_overlap']} (should be 0 or near it)")
    print(f"train yield: mean={d['y_train'].mean():.3f} std={d['y_train'].std():.3f} Mg/ha")
    print(f"test  yield: mean={d['y_test'].mean():.3f} std={d['y_test'].std():.3f} Mg/ha")

    y_mean, y_std = d["y_train"].mean(), d["y_train"].std()
    y_train = (d["y_train"] - y_mean) / y_std
    y_test = (d["y_test"] - y_mean) / y_std   # standardized by TRAIN stats only

    print()
    print("=== linear (from-X, normalized), fit on 2014-2023, predict 2024 ===")
    (r, nll_m, nll_med, npat, ok), mle = fit_predict_linear(
        d["X_train"], y_train, d["X_test"], y_test)
    print(f"r={r:.4f}  NLL median={nll_med:.3f}  pathological={npat}/{len(y_test)}  "
         f"sigma_f2={mle['sigma_f2']:.4g} sigma_n2={mle['sigma_n2']:.4g}")

    print()
    print("=== RBF, fit on 2014-2023, predict 2024 ===")
    (r_rbf, _, nll_med_rbf, npat_rbf, _), mle_rbf = fit_predict_rkhs(
        d["X_train"], y_train, d["X_test"], y_test, kind="rbf")
    print(f"r={r_rbf:.4f}  NLL median={nll_med_rbf:.3f}  pathological={npat_rbf}/{len(y_test)}  "
         f"ell={mle_rbf['ell']:.4g}")

    print()
    print("=== Matern-3/2, fit on 2014-2023, predict 2024 ===")
    (r_mat, _, nll_med_mat, npat_mat, _), mle_mat = fit_predict_rkhs(
        d["X_train"], y_train, d["X_test"], y_test, kind="matern32")
    print(f"r={r_mat:.4f}  NLL median={nll_med_mat:.3f}  pathological={npat_mat}/{len(y_test)}  "
         f"ell={mle_mat['ell']:.4g}")

    print()
    print("=== summary: genuine 2024 held-out season, marker-only model ===")
    print(f"  linear   r={r:.4f}")
    print(f"  rbf      r={r_rbf:.4f}  delta vs linear = {r_rbf-r:+.4f}")
    print(f"  matern32 r={r_mat:.4f}  delta vs linear = {r_mat-r:+.4f}")


if __name__ == "__main__":
    main()
