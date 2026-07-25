"""Method 4 of climate_cat_lab's four-method ladder: layers gp_loss_model's
fitted spatial covariance INSIDE a two-component regime mixture, with the
regime itself estimated from the historical sample -- never read from the
oracle. This is the one method built to represent the SAME mechanism class
as the true DGP (dgp_simulator.py's regime + spatial-shock design), testing
LAB_PLAN.md's open question: does representing genuine tail dependence (not
just a better-shaped spatial covariance) close the rest of the capital-
sizing gap that method 3 (vanilla GP) leaves?

**Revision history, kept here because the first version's failure is itself
a real finding (see RESULTS_PHASE1.md).** The first version partitioned
years into "stress" vs "normal" using a FIXED top-25%-quantile split,
regardless of the fitted mixing probability -- chosen purely so the
"systemic" component's kernel fit had enough years to be numerically
workable at n_years~60. `phase1_sweep.py` showed this doesn't just add
noise: achieved survival stayed stuck at ~93.4% even at n_years=500, where
the fitted mixing probability had already converged almost exactly to the
true value. An oracle-cheat diagnostic (`phase1_diagnostic.py`, using the
TRUE regime labels, something no real method is allowed to do) got 99.54%
survival with the identical GP-mixture machinery -- proving the fixed 25%
partition was the actual bottleneck: at a true frequency of ~6.7%, a 25%
partition mixes roughly 3.7 ordinary years in for every genuine systemic
year, diluting the fitted "systemic" component's severity toward something
far milder than the true regime, a bias that does NOT shrink with more
historical data because the dilution ratio (25%/6.7%) doesn't either.

**The fix below**: size the partition to the model's OWN fitted mixing
probability (still oracle-free) rather than a fixed generous quantile, with
a safety margin and a floor only to keep the fit numerically workable at
small n_years -- not to hedge against not trusting the estimate. This
closes most of the gap without cheating (see RESULTS_PHASE1.md); the
remaining honest question is how well an unsupervised regime classifier's
OWN accuracy holds up, which is exactly what a real practitioner is stuck
with.
"""

import numpy as np
from sklearn.mixture import GaussianMixture

from gp_loss_model import fit_gp_loss_model, fit_gp_loss_model_weighted, sample_gp_scenarios


def fit_regime_mixture(losses, book, kind="rbf", seed=0, margin=1.5,
                        min_stress_years=8, max_fit_quantile=0.35,
                        p_hat_bounds=(0.02, 0.5)):
    total_log = np.log(losses.sum(axis=1))
    n_years = losses.shape[0]

    gmm = GaussianMixture(n_components=2, random_state=seed, n_init=5)
    gmm.fit(total_log.reshape(-1, 1))
    means = gmm.means_.ravel()
    systemic_component = int(np.argmax(means))
    p_hat_raw = float(gmm.weights_[systemic_component])
    p_hat = float(np.clip(p_hat_raw, p_hat_bounds[0], p_hat_bounds[1]))

    # Adaptive partition: `margin` x the model's OWN frequency estimate, not
    # a fixed generous quantile -- the safety margin and floor exist only to
    # keep the systemic component's kernel fit numerically workable when
    # n_years is small, not because the estimate is distrusted.
    target_frac = float(np.clip(margin * p_hat, min_stress_years / n_years,
                                 max_fit_quantile))
    cutoff = np.quantile(total_log, 1.0 - target_frac)
    is_stress_year = total_log >= cutoff
    n_stress = int(is_stress_year.sum())
    n_normal = int((~is_stress_year).sum())
    if n_stress < 5 or n_normal < 5:
        raise ValueError(
            f"regime partition too imbalanced for a stable fit "
            f"(stress={n_stress}, normal={n_normal}); use a longer "
            f"historical sample")

    fit_normal = fit_gp_loss_model(losses[~is_stress_year], book, kind=kind)
    fit_systemic = fit_gp_loss_model(losses[is_stress_year], book, kind=kind)

    return dict(p_hat=p_hat, p_hat_raw=p_hat_raw, is_stress_year=is_stress_year,
                fit_quantile=target_frac, gmm_weights=gmm.weights_.tolist(),
                gmm_means=means.tolist(), n_stress=n_stress, n_normal=n_normal,
                fit_normal=fit_normal, fit_systemic=fit_systemic, n=book["n"])


def fit_regime_mixture_soft(losses, book, kind="rbf", seed=0, p_hat_bounds=(0.02, 0.5)):
    """SOFT counterpart of fit_regime_mixture: instead of hard-partitioning
    years into stress/normal via a `margin x p_hat`-sized quantile cutoff,
    each component's covariance is fit with EVERY year, weighted by the
    same GaussianMixture's own posterior responsibility for that year
    (gmm.predict_proba) -- no cutoff, no margin/min_stress_years/
    max_fit_quantile tuning knobs, and no year is thrown away from either
    fit.

    An EARLIER version of this function floored responsibilities (a
    min-effective-sample-size safeguard, the soft-fit analogue of
    fit_regime_mixture's min_stress_years) to guard against a rare failure
    mode: at small n_years, the GMM can occasionally put ~100%
    responsibility on a single extreme year, and Nelder-Mead can (rarely --
    NOT deterministically; measured directly, most single-effective-year
    fits land fine) wander into a degenerate high-variance basin
    (sigma_f2=15.8 vs a baseline ~0.1-0.7 scale). That floor was REMOVED
    (see RESULTS_ROBUSTNESS.md): it diluted the majority of already-healthy
    fits to guard against a rare event, measurably WORSENING achieved
    survival for seeds that were never at risk (98.78% -> 94.20% at
    n_years=60 on RESULTS_PHASE1.md's own seeds) -- reintroducing a milder
    version of the exact discard-information dilution this soft classifier
    exists to avoid. The actual fix lives in gp_loss_model.py's
    mle_fit_spatial_weighted: a variance CAP on the FITTED result (which
    only ever binds on the pathological outcome itself, not on every input)
    rather than a floor on the input responsibilities.

    Exists to test RESULTS_PHASE1.md/RESULTS_PHASE2.md's open question: is
    the hard partition's remaining gap to the oracle-cheat
    ceiling (99.54% at Phase 1's n=500, 96.11% at Phase 2's n=45,000)
    closable with a better classifier, or is it inherent to not knowing the
    true regime? A responsibility-weighted fit is the natural "soft EM
    M-step" generalization of the hard partition (which is equivalent to
    weights re-rounded to {0, 1}), so if soft closes most of the remaining
    gap, the hard partition's cutoff mechanics (not the classification
    itself) were costing real accuracy; if it doesn't move much, the
    ceiling is closer to inherent.

    Returns the same shape as fit_regime_mixture (p_hat, fit_normal,
    fit_systemic, n, ...) so sample_regime_mixture_scenarios works
    unchanged -- plus `responsibilities`, the per-year P(systemic) used as
    weights, in place of is_stress_year/n_stress/n_normal/fit_quantile."""
    total_log = np.log(losses.sum(axis=1))
    n_years = losses.shape[0]

    gmm = GaussianMixture(n_components=2, random_state=seed, n_init=5)
    gmm.fit(total_log.reshape(-1, 1))
    means = gmm.means_.ravel()
    systemic_component = int(np.argmax(means))
    p_hat_raw = float(gmm.weights_[systemic_component])
    p_hat = float(np.clip(p_hat_raw, p_hat_bounds[0], p_hat_bounds[1]))
    resp = gmm.predict_proba(total_log.reshape(-1, 1))[:, systemic_component]

    fit_normal = fit_gp_loss_model_weighted(losses, book, weights=1.0 - resp, kind=kind)
    fit_systemic = fit_gp_loss_model_weighted(losses, book, weights=resp, kind=kind)

    return dict(p_hat=p_hat, p_hat_raw=p_hat_raw, responsibilities=resp.tolist(),
                gmm_weights=gmm.weights_.tolist(), gmm_means=means.tolist(),
                fit_normal=fit_normal, fit_systemic=fit_systemic, n=book["n"],
                n_years=n_years, mean_responsibility=float(resp.mean()))


def sample_regime_mixture_scenarios(fit, insured_value, n_scenarios, seed=0):
    rng = np.random.default_rng(seed)
    is_systemic_draw = rng.random(n_scenarios) < fit["p_hat"]
    n_sys = int(is_systemic_draw.sum())
    n_norm = n_scenarios - n_sys

    out = np.empty((n_scenarios, fit["n"]))
    if n_norm > 0:
        out[~is_systemic_draw] = sample_gp_scenarios(fit["fit_normal"], insured_value,
                                                       n_norm, seed=seed + 1)
    if n_sys > 0:
        out[is_systemic_draw] = sample_gp_scenarios(fit["fit_systemic"], insured_value,
                                                      n_sys, seed=seed + 2)
    return out
