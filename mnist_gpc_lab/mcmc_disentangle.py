#!/usr/bin/env python3
"""M4: disentangle Laplace-approximation error from MacKay's logit predictive
approximation, using elliptical slice sampling (ESS; Murray, Adams & MacKay
2010) as a tuning-free MCMC ground truth for the exact posterior.

Two separate error sources are conflated in M3's "logit is more conservative
than probit" finding:
  1. Laplace's Gaussian approximation to the true (non-Gaussian) posterior
     over f -- present for BOTH likelihoods.
  2. MacKay's sigmoid-Gaussian moment-match for the predictive probability --
     only in the logit path; probit's predictive step (GPML eq 3.25) is EXACT
     given the Laplace posterior, so probit isolates error source 1 alone.

Design: run ESS (ground truth, no Laplace/MacKay approximation at all) for
BOTH the logit-likelihood model and the probit-likelihood model, on the same
binary slice + kernel. Compare:
  - Laplace-probit vs MCMC-probit  -> pure Laplace-approximation error
  - Laplace-logit  vs MCMC-logit   -> Laplace error + MacKay error combined
The gap between those two gaps is attributable to MacKay's approximation.

Scope: one binary slice (digit 3 vs 8, matching the GPML book's own 3-vs-5
worked example in spirit), one seed, modest n -- this closes out the week's
understanding, not a full robustness sweep (see LAB_PLAN.md M4).

Usage: python3 mcmc_disentangle.py
"""

import json
import math
import sys
import os
import time

import numpy as np
import cupy as cp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datasets import _load_raw  # reuse the trusted-local-cache pickle loader
from gp_classifier import (LaplaceBinaryGPC, _squared_dist_matrix, _cross_squared_dist,
                            _kernel_value, _normal_cdf, _log1pexp)


def load_binary_slice(digit_a, digit_b, n_train_per_class, n_test_per_class, seed=0):
    """digit_a -> class 0, digit_b -> class 1, from MNIST's own train/test splits."""
    rng = np.random.default_rng(seed)
    train_full, _valid_full, test_full = _load_raw()
    X_tr_all, y_tr_all = train_full
    X_te_all, y_te_all = test_full

    def draw(X_all, y_all, n_per_class):
        idx_a = rng.choice(np.flatnonzero(y_all == digit_a), n_per_class, replace=False)
        idx_b = rng.choice(np.flatnonzero(y_all == digit_b), n_per_class, replace=False)
        idx = np.concatenate([idx_a, idx_b])
        y = np.concatenate([np.zeros(n_per_class), np.ones(n_per_class)])
        order = rng.permutation(len(idx))
        return X_all[idx[order]], y[order]

    X_train, y_train = draw(X_tr_all, y_tr_all, n_train_per_class)
    X_test, y_test = draw(X_te_all, y_te_all, n_test_per_class)
    return (X_train, y_train), (X_test, y_test)


def _loglik_logit(f, t):
    return float(cp.sum(t * f - _log1pexp(f)))


def _loglik_probit(f, t):
    y = 2.0 * t - 1.0
    Phi = cp.maximum(_normal_cdf(y * f), 1e-12)
    return float(cp.sum(cp.log(Phi)))


_LOGLIK = {"logit": _loglik_logit, "probit": _loglik_probit}


def elliptical_slice_sample(L_prior, t, likelihood, n_samples, burn_in, thin, seed=0):
    """ESS (Murray/Adams/MacKay 2010): tuning-free MCMC for f ~ N(0,K),
    y|f ~ likelihood. L_prior is the (n,n) lower Cholesky factor of K.
    Returns (n_samples, n) array of posterior draws of f."""
    rng = cp.random.default_rng(seed)
    n = L_prior.shape[0]
    loglik_fn = _LOGLIK[likelihood]

    f = cp.zeros(n, dtype=cp.float64)
    cur_ll = loglik_fn(f, t)
    total_iters = burn_in + n_samples * thin
    samples = cp.empty((n_samples, n), dtype=cp.float64)
    kept = 0

    for it in range(total_iters):
        nu = L_prior @ rng.standard_normal(n)
        log_y = cur_ll + float(cp.log(rng.uniform(0.0, 1.0)))
        theta = float(rng.uniform(0.0, 2.0 * math.pi))
        theta_min, theta_max = theta - 2.0 * math.pi, theta

        while True:
            f_prop = f * math.cos(theta) + nu * math.sin(theta)
            ll_prop = loglik_fn(f_prop, t)
            if ll_prop > log_y:
                f, cur_ll = f_prop, ll_prop
                break
            if theta < 0:
                theta_min = theta
            else:
                theta_max = theta
            theta = float(rng.uniform(theta_min, theta_max))

        if it >= burn_in and (it - burn_in) % thin == 0:
            samples[kept] = f
            kept += 1
            if kept >= n_samples:
                break

    return samples


def mcmc_predictive_prob(f_samples, K, X_train, X_test, ell, sigma_f2, kind, likelihood):
    """Monte Carlo predictive P(y=1|x*): for each posterior sample of
    f_train, draw f_star from the EXACT GP conditional (no approximation),
    push through the likelihood's response function, average over samples."""
    n = X_train.shape[0]
    L = cp.linalg.cholesky(cp.asarray(K, dtype=cp.float64))  # fresh factor, fp64
    Kstar = _kernel_value(_cross_squared_dist(cp.asarray(X_test), cp.asarray(X_train)),
                          ell, sigma_f2, kind)  # (m, n)

    # v = L^-1 k*_i for every test point i -> conditional var (shared across samples,
    # since it doesn't depend on f_train, only on the kernel).
    import cupyx.scipy.linalg as _cpx
    V = _cpx.solve_triangular(L, Kstar.T, lower=True, check_finite=False)  # (n, m)
    cond_var = sigma_f2 - cp.einsum("ij,ij->j", V, V)
    cp.maximum(cond_var, 1e-12, out=cond_var)
    cond_std = cp.sqrt(cond_var)

    # alpha_s = K^-1 f_s for every sample (solve once per sample against the
    # shared factor); mean_star_s = k*^T alpha_s.
    m = Kstar.shape[0]
    n_samples = f_samples.shape[0]
    prob_acc = cp.zeros(m, dtype=cp.float64)
    rng = cp.random.default_rng(0)
    predict_fn = _normal_cdf if likelihood == "probit" else (lambda z: 1.0 / (1.0 + cp.exp(-z)))

    for s in range(n_samples):
        alpha_s = _cpx.solve_triangular(L, f_samples[s], lower=True, check_finite=False)
        alpha_s = _cpx.solve_triangular(L.T, alpha_s, lower=False, check_finite=False)
        mean_star = Kstar @ alpha_s
        eps = rng.standard_normal(m)
        f_star_sample = mean_star + cond_std * eps
        prob_acc += predict_fn(f_star_sample)

    return prob_acc / n_samples


def main():
    digit_a, digit_b = 3, 8
    n_train_per_class, n_test_per_class = 100, 50
    ell = 6.0  # fixed, reasonable mid-range value (see LAB_PLAN.md M4 scope note)
    sigma_f2 = 1.0
    kind = "rbf"

    (X_train, y_train), (X_test, y_test) = load_binary_slice(
        digit_a, digit_b, n_train_per_class, n_test_per_class, seed=0)
    print(f"digit {digit_a} vs {digit_b}: n_train={len(y_train)} n_test={len(y_test)}")

    Xtr_cp = cp.asarray(X_train, dtype=cp.float64)
    K = cp.asnumpy(_kernel_value(_squared_dist_matrix(Xtr_cp), ell, sigma_f2, kind))
    L_prior = cp.linalg.cholesky(cp.asarray(K) + 1e-8 * cp.eye(len(y_train)))
    t = cp.asarray(y_train, dtype=cp.float64)

    results = {}
    for likelihood in ("logit", "probit"):
        print(f"\n=== {likelihood} ===")
        t0 = time.time()
        clf = LaplaceBinaryGPC(ell=ell, sigma_f=1.0, kind=kind, likelihood=likelihood)
        clf.fit(X_train, y_train)
        _, _, laplace_prob = clf.predict(X_test)
        laplace_prob = cp.asnumpy(laplace_prob)
        print(f"  Laplace fit: {time.time()-t0:.1f}s, converged={clf.fit_info.converged}, "
              f"{clf.fit_info.n_iter} iters")

        t0 = time.time()
        samples = elliptical_slice_sample(L_prior, t, likelihood,
                                          n_samples=800, burn_in=400, thin=3, seed=0)
        print(f"  ESS: {time.time()-t0:.1f}s for {samples.shape[0]} samples")

        mcmc_prob = cp.asnumpy(mcmc_predictive_prob(samples, K, X_train, X_test,
                                                     ell, sigma_f2, kind, likelihood))

        diff = laplace_prob - mcmc_prob
        print(f"  Laplace vs MCMC predictive prob: mean diff={diff.mean():+.4f}  "
              f"mean |diff|={np.abs(diff).mean():.4f}  max |diff|={np.abs(diff).max():.4f}")
        print(f"  mean confidence (dist from 0.5): Laplace={np.abs(laplace_prob-0.5).mean():.4f}  "
              f"MCMC={np.abs(mcmc_prob-0.5).mean():.4f}")

        results[likelihood] = {
            "laplace_prob": laplace_prob.tolist(),
            "mcmc_prob": mcmc_prob.tolist(),
            "y_test": y_test.tolist(),
            "mean_diff": float(diff.mean()),
            "mean_abs_diff": float(np.abs(diff).mean()),
            "mean_conf_laplace": float(np.abs(laplace_prob - 0.5).mean()),
            "mean_conf_mcmc": float(np.abs(mcmc_prob - 0.5).mean()),
        }

    print("\n=== Disentangling ===")
    logit_gap = results["logit"]["mean_abs_diff"]
    probit_gap = results["probit"]["mean_abs_diff"]
    print(f"Laplace-vs-MCMC |diff|: probit={probit_gap:.4f} (pure Laplace-approx error)")
    print(f"Laplace-vs-MCMC |diff|: logit ={logit_gap:.4f} (Laplace-approx + MacKay error)")
    print(f"Attributable to MacKay's approximation specifically: ~{logit_gap-probit_gap:+.4f}")

    with open("results/mcmc_disentangle.json", "w") as f:
        json.dump({"digit_a": digit_a, "digit_b": digit_b, "ell": ell,
                   "n_train_per_class": n_train_per_class, "n_test_per_class": n_test_per_class,
                   "results": results}, f, indent=2)
    print("\nwrote results/mcmc_disentangle.json")


if __name__ == "__main__":
    main()
