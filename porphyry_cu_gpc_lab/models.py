"""Loads this lab's own exact seed-0 spatial models -- reproduced from the
frozen hyperparameters `results/porphyry_gpc_seed0_spatial.json` already
recorded there (ell=100.27 km, kind=matern32, sigma_f=1.0 for the GPC;
gamma=4.97e-05 for the SVM), not a new hyperparameter search. Same
convention `bayesian_decision_lab/models.py` established for `mining_gpc_lab`
-- this lab never re-grids `ell`/`gamma` here, it takes the already-fitted
posterior as given and only varies the downstream *decision rule*.

"Refitting" here means calling `.fit()` again to reproduce the identical
frozen model (deterministic given the same split/seed/hyperparameters,
already verified bit-reproducible in this lab's own Phase 1) -- not fitting
a new model. No model-serialization step exists upstream, so this is the
only way to get the actual fitted objects back.
"""

import os
import sys

import cupy as cp
import numpy as np
from sklearn.svm import SVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # gp_classifier.py, decision.py, voi.py live in gp_engine/

from datasets import load_split  # noqa: E402
from gp_classifier import LaplaceBinaryGPC  # noqa: E402
from run_lab import KERNEL_KIND  # noqa: E402

# Frozen exact values from results/porphyry_gpc_seed0_spatial.json -- see
# this module's docstring for why these are read off, not re-searched.
GPC_ELL = 100.26902531455256
GPC_SIGMA_F = 1.0
GPC_KIND = KERNEL_KIND  # "matern32"
SVM_GAMMA = 4.973205642367758e-05
FEATURE_SET = "spatial"
FRAC_TRAIN, FRAC_VAL = 0.6, 0.2
CUTOFF_QUANTILE = 0.95


def fit_models(seed=0):
    """Returns (gpc, svm, X_train, y_train, X_test, y_test) for a fresh
    stratified split at `seed`, fit with the frozen hyperparameters above --
    same convention as this lab's own `confidence_study.py`: the split is
    fresh per seed, the hyperparameters (ell/gamma) are not re-gridded per
    seed. Seed 0 reproduces `run_lab.py`'s exact fit."""
    (X_train, y_train), _, (X_test, y_test) = load_split(
        feature_set=FEATURE_SET, frac_train=FRAC_TRAIN, frac_val=FRAC_VAL,
        seed=seed, cutoff_quantile=CUTOFF_QUANTILE)

    gpc = LaplaceBinaryGPC(ell=GPC_ELL, sigma_f=GPC_SIGMA_F, kind=GPC_KIND)
    gpc.fit(X_train, y_train)

    svm = SVC(kernel="rbf", gamma=SVM_GAMMA, probability=True, random_state=seed)
    svm.fit(X_train, y_train)

    return gpc, svm, X_train, y_train, X_test, y_test


def load_seed0_models():
    """`fit_models(seed=0)` -- the exact seed-0 spatial fit `run_lab.py`
    produced, reproduced here (not re-searched)."""
    return fit_models(seed=0)


def gpc_mean_var_prob(gpc, X):
    """(mean, var, prob) at X, all numpy float64 -- the full posterior
    LaplaceBinaryGPC.predict() already returns, just pulled to host memory
    once so every downstream script in this lab works in plain numpy."""
    mean, var, prob = gpc.predict(X)
    return cp.asnumpy(mean), cp.asnumpy(var), cp.asnumpy(prob)


def svm_prob(svm, X):
    """P(class=1) from sklearn's Platt-scaled SVM, numpy float64 (m,)."""
    probs = svm.predict_proba(X)
    col1 = list(svm.classes_).index(1)
    return probs[:, col1]


def _logit(p, eps=1e-9):
    p = np.clip(p, eps, 1.0 - eps)
    return np.log(p / (1.0 - p))


def all_conditions(gpc, svm, X):
    """dict condition_name -> (p_now, pseudo_mean, var) -- same convention
    `bayesian_decision_lab/models.py` established: SVM and "GPC, mean-only"
    both get var=0 by construction (SVM has no posterior at all; mean-only
    forces it to zero) with a *pseudo*-mean chosen so sigmoid(pseudo_mean)
    reproduces that condition's own p_now exactly. var=0 is what makes
    `voi.probe_value` structurally never prefer Probe for either of those
    two conditions (see `../voi.py`'s module docstring)."""
    mean, var, prob_full = gpc_mean_var_prob(gpc, X)
    p_svm = svm_prob(svm, X)
    prob_mean_only = 1.0 / (1.0 + np.exp(-mean))
    zeros = np.zeros_like(mean)
    return {
        "svm": (p_svm, _logit(p_svm), zeros),
        "gpc_mean": (prob_mean_only, mean, zeros),
        "gpc_full": (prob_full, mean, var),
    }


if __name__ == "__main__":
    gpc, svm, X_train, y_train, X_test, y_test = load_seed0_models()
    mean, var, prob = gpc_mean_var_prob(gpc, X_test)
    p_svm = svm_prob(svm, X_test)
    print(f"n_train={len(y_train)}  n_test={len(y_test)}  n_ore_test={int(y_test.sum())}")
    print(f"GPC: mean range=[{mean.min():.3f},{mean.max():.3f}]  "
          f"var range=[{var.min():.4f},{var.max():.4f}]  "
          f"prob range=[{prob.min():.4f},{prob.max():.4f}]")
    print(f"SVM: prob range=[{p_svm.min():.4f},{p_svm.max():.4f}]")
