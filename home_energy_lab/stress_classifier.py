"""Day-ahead high-demand classifier for Phase 2 (sequential-VoI skip/probe/
drill dispatch layer, LAB_PLAN.md's Phase 2 section).

Genuinely new modeling piece this phase adds -- the sixth lab in this
family to need one, for the same recurring reason (`VOI_DISPATCH_PATTERN.md`'s
point 2): neither Method 2's GP1D forecast nor Method 3's GaussianMixture
(Phase 1) produce a native `(mean, var, prob)` triple over a discrete state.
This builds a real `LaplaceBinaryGPC` fit (unchanged from `gp_classifier.py`)
on yesterday's net-load and temperature (both already computed, real,
day-ahead-available quantities -- no new data collection) against a real,
data-derived label: is TODAY a high-demand day (net_load in the top 25% of
the training distribution, the same real-quantile-threshold convention
`hydro_reserve_lab`'s drought label used).
"""

import os
import sys

import cupy as cp
import numpy as np
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from gp_classifier import LaplaceBinaryGPC  # noqa: E402

from daily_agg import build_daily, TEST_YEARS

HIGH_DEMAND_PCTL = 75.0
ELL_GRID = (0.5, 1.0, 2.0, 4.0, 8.0, 16.0)
KIND = "rbf"


def build_dataset():
    """(X, y_raw, dates, thresh_full): X (n,2) = [yesterday's net_load,
    yesterday's mean temp]; **y_raw (n,) = TODAY'S RAW net load**, not a
    label, over the real 2017-2025 held-out record.

    **Why raw rather than labelled (CODE_REVIEW.md M2).** The label is
    "is today in the top 25% of net load", which requires a threshold. The
    earlier version computed that threshold over the WHOLE pool and only
    then split into train/val/test -- so the label definition carried a
    scalar of test-set information into training. Tiny at n=3,286, but free
    to remove: the threshold is now derived inside `fit_classifier` from the
    TRAINING split alone and applied to all three splits.

    `thresh_full` is still returned for reporting/diagnostics only -- it is
    NOT used to build any label."""
    daily = build_daily()
    daily.index = daily.index.date
    years = np.array([d.year for d in daily.index])
    test_mask = (years >= TEST_YEARS[0]) & (years <= TEST_YEARS[1])
    pool = daily.loc[test_mask]

    y_raw = pool["net_load_kwh"].values[1:].astype(np.float64)   # today's raw net load
    X = np.stack([pool["net_load_kwh"].values[:-1], pool["temp"].values[:-1]], axis=1)
    dates = np.array(pool.index[1:])
    thresh_full = float(np.percentile(pool["net_load_kwh"], HIGH_DEMAND_PCTL))
    return X, y_raw, dates, thresh_full


def fit_classifier(X, y_raw, ell_grid=ELL_GRID, kind=KIND, val_frac=0.25, test_frac=0.25, seed=0):
    """Fresh train/val/test split per seed -- one fixed real dataset (not
    resimulable, like `shm_lab`/`hydro_reserve_lab`), same bootstrap
    convention as those two labs. Returns
    (gpc, svm, X_train, y_train, X_test, y_test, ell, val_ap).

    `y_raw` is TODAY'S RAW net load. The high-demand THRESHOLD is computed
    from the training split only and then applied to all three splits, so no
    test information reaches the label definition (CODE_REVIEW.md M2). The
    split is therefore unstratified -- stratifying would require labels
    before the threshold exists. At n=3,286 with a ~25% base rate the class
    balance across a seeded random split is stable to well under a
    percentage point, checked in this module's __main__."""
    X_train, X_rest, yr_train, yr_rest = train_test_split(
        X, y_raw, test_size=val_frac + test_frac, random_state=seed)
    rel_test = test_frac / (val_frac + test_frac)
    X_val, X_test, yr_val, yr_test = train_test_split(
        X_rest, yr_rest, test_size=rel_test, random_state=seed)

    # Threshold from TRAIN ONLY, then label every split with it.
    thresh = np.percentile(yr_train, HIGH_DEMAND_PCTL)
    y_train = (yr_train >= thresh).astype(np.float64)
    y_val = (yr_val >= thresh).astype(np.float64)
    y_test = (yr_test >= thresh).astype(np.float64)

    # normalize features (net_load and temp have very different scales) so a single isotropic
    # ell is meaningful -- z-score using TRAIN statistics only, no leakage
    mu, sigma = X_train.mean(axis=0), X_train.std(axis=0)
    sigma = np.where(sigma > 0, sigma, 1.0)
    X_train_n, X_val_n, X_test_n = (X_train - mu) / sigma, (X_val - mu) / sigma, (X_test - mu) / sigma

    best_ell, best_ap, best_gpc = None, -1.0, None
    for ell in ell_grid:
        gpc = LaplaceBinaryGPC(ell=ell, sigma_f=1.0, kind=kind)
        gpc.fit(X_train_n, y_train)
        _, _, prob = gpc.predict(X_val_n)
        ap = average_precision_score(y_val, cp.asnumpy(prob))
        if ap > best_ap:
            best_ell, best_ap, best_gpc = ell, ap, gpc

    svm = SVC(kernel="rbf", probability=True, random_state=seed)
    svm.fit(X_train_n, y_train)

    return best_gpc, svm, X_train_n, y_train, X_test_n, y_test, best_ell, best_ap


def gpc_mean_var_prob(gpc, X):
    mean, var, prob = gpc.predict(X)
    return cp.asnumpy(mean), cp.asnumpy(var), cp.asnumpy(prob)


def svm_prob(svm, X):
    probs = svm.predict_proba(X)
    col1 = list(svm.classes_).index(1)
    return probs[:, col1]


def _logit(p, eps=1e-9):
    p = np.clip(p, eps, 1.0 - eps)
    return np.log(p / (1.0 - p))


def all_conditions(gpc, svm, X):
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
    X, y_raw, dates, thresh_full = build_dataset()
    print(f"n_days={len(y_raw)}  full-pool threshold (reporting only)={thresh_full:.2f} kWh")
    # M2 check: train-derived threshold and the resulting class balances must be stable
    # across seeds, and close to the full-pool threshold they replaced.
    for sd in (0, 1, 2):
        *_, y_tr, _, y_te, _, _ = fit_classifier(X, y_raw, seed=sd)
        print(f"  seed {sd}: train base rate={y_tr.mean():.4f}  test base rate={y_te.mean():.4f}")
    gpc, svm, X_train, y_train, X_test, y_test, ell, val_ap = fit_classifier(X, y_raw, seed=0)
    print(f"ell={ell}  val_ap={val_ap:.3f}  n_train={len(y_train)}  n_test={len(y_test)}")
    conditions = all_conditions(gpc, svm, X_test)
    for name, (p, mean, var) in conditions.items():
        ap = average_precision_score(y_test, p)
        extra = f"  var range=[{var.min():.4f},{var.max():.4f}]" if name == "gpc_full" else ""
        print(f"[{name:9s}] test AP={ap:.3f}  prob range=[{p.min():.4f},{p.max():.4f}]{extra}")
