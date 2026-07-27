"""Method 4 (GP + soft-EM regime-mixture) of grid_reserve_lab's five-method
ladder -- the third domain for the identical soft-EM mechanism
`climate_cat_lab/regime_mixture.py` (Method 4) and `cvar_gp_lab/regime_gp.py`
already validated, now pointed at fleet-wide daily shortfall instead of
annual catastrophe loss or daily asset returns. Uses the SOFT
(responsibility-weighted) fit directly, not the hard-partition version
climate_cat_lab tried first and found had a real, fixable bug (a fixed
top-quantile partition diluting the systemic component, RESULTS_PHASE1.md)
-- `gp_cvar_soft` in `portfolio_studio` already validated soft as the
production-worthy variant, so this lab starts there rather than
re-discovering the same lesson a third time.

Every-day-weighted GP fit (gp_shortfall_model.fit_gp_shortfall_model_weighted)
replaces the hard stress/normal split: each day contributes to BOTH the
"calm" and "drought" component's spatial-kernel fit, weighted by that day's
GaussianMixture-fitted posterior responsibility -- no day is discarded, no
partition-sizing quantile to tune.
"""

import numpy as np
from sklearn.mixture import GaussianMixture

from gp_shortfall_model import (fit_gp_shortfall_model, fit_gp_shortfall_model_weighted,
                                 sample_gp_scenarios)


def _fit_gmm_regime(shortfall, signed_shortfall, seed, p_hat_bounds, min_effective_days):
    """Shared regime-detection step for both the soft and hard variants
    below -- identical GMM, identical p_hat/responsibilities, so a
    soft-vs-hard comparison isolates ONLY the downstream GP-fitting
    difference (weighted-fit-on-everyone vs hard-split-and-discard), not a
    difference in how the regime itself was detected."""
    if signed_shortfall is None:
        signed_shortfall = shortfall
    regime_feature = signed_shortfall.sum(axis=1)
    n_days = shortfall.shape[0]
    if p_hat_bounds is None:
        floor = min_effective_days / n_days
        p_hat_bounds = (floor, 1.0 - floor)

    gmm = GaussianMixture(n_components=2, random_state=seed, n_init=5)
    gmm.fit(regime_feature.reshape(-1, 1))
    means = gmm.means_.ravel()
    drought_component = int(np.argmax(means))
    p_hat_raw = float(gmm.weights_[drought_component])
    p_hat = float(np.clip(p_hat_raw, p_hat_bounds[0], p_hat_bounds[1]))
    resp = gmm.predict_proba(regime_feature.reshape(-1, 1))[:, drought_component]
    return dict(p_hat=p_hat, p_hat_raw=p_hat_raw, resp=resp,
                gmm_weights=gmm.weights_.tolist(), gmm_means=means.tolist(),
                n_days=n_days, p_hat_bounds=p_hat_bounds)


def fit_regime_mixture_soft(shortfall, fleet, signed_shortfall=None, kind="rbf", seed=0,
                             p_hat_bounds=None, min_effective_days=10):
    """Fits a 2-component GMM on the fleet-wide SIGNED total deviation
    (climatology minus actual, summed across sites BEFORE any clipping) to
    estimate a drought-regime probability and per-day responsibility, then
    fits TWO weighted spatial-GP shortfall models (fit_gp_shortfall_model_
    weighted, on the usual CLIPPED `shortfall`): one weighted toward "calm"
    days, one toward "drought" days. Returns dict(p_hat, p_hat_raw,
    responsibilities, gmm_weights, gmm_means, fit_normal, fit_drought, n,
    n_days, mean_responsibility, p_hat_bounds).

    `signed_shortfall`: (n_days, n) UNCLIPPED per-site deviation (positive
    = underperformed, negative = overperformed). If None, falls back to
    `shortfall` itself (the old, clipped behavior) for backward
    compatibility with any caller that hasn't been updated to pass it --
    but every current caller should pass the real signed array.

    **Why this matters, found directly on real EIA-930 data (RESULTS_
    PHASE2.md's "Follow-up" section), not a hypothetical concern**:
    summing the already-CLIPPED per-site shortfall across a fleet creates
    a spurious near-zero mass point at the fleet-total level -- a fleet
    total is only exactly (or near) zero when EVERY site simultaneously
    performed at-or-above its own expectation, a much rarer joint event
    than "the fleet's NET output, allowing sites to offset each other, was
    near its combined expectation." Fitting the GMM on the clipped total
    produced a 2-component split that exactly tracked "fraction of days
    with near-zero clipped total" (a mechanical artifact of the clip-then-
    sum order of operations) rather than anything resembling a genuine
    correlated drought event -- confirmed by checking the minority
    component's weight against that exact fraction directly. Summing the
    UNCLIPPED signed deviation first (allowing offsetting), THEN letting
    the GMM see a real two-sided distribution, avoids the artifact by
    construction. No log-transform is applied (unlike climate_cat_lab's
    version) -- a signed deviation isn't strictly positive, so there's
    nothing to take a log of; this quantity is also far less skewed than
    strictly-positive dollar losses were, so a raw fit is the natural
    choice, not a stand-in for a transform that didn't fit.

    `p_hat_bounds`: if None (default), computed as
    (min_effective_days/n_days, 1 - min_effective_days/n_days) -- a purely
    NUMERICAL floor (enough effective days on each side for a stable
    weighted spatial-kernel fit, the same concern climate_cat_lab's own
    min_stress_years guarded against) computed FROM this call's own n_days,
    not a domain assumption about how common the "regime" should be.

    An earlier version hardcoded (0.02, 0.5) -- copied unchanged from
    climate_cat_lab's synthetic calibration, where the true DGP's regime
    frequency really was rare (~6.8%) by construction. Real EIA-930 data
    doesn't have that same one-sided guarantee (RESULTS_PHASE2.md's
    Finding 2 found a genuinely wide ~85%/15% split once a leaking
    climatology baseline was also fixed) -- an upper bound of 0.5 baked in
    "the regime is a minority," an assumption this domain does not
    obviously satisfy and shouldn't be forced to. The data-driven default
    here only prevents numerical degeneracy, not a particular real-world
    regime frequency."""
    g = _fit_gmm_regime(shortfall, signed_shortfall, seed, p_hat_bounds, min_effective_days)
    resp = g["resp"]

    fit_normal = fit_gp_shortfall_model_weighted(shortfall, fleet, weights=1.0 - resp, kind=kind)
    fit_drought = fit_gp_shortfall_model_weighted(shortfall, fleet, weights=resp, kind=kind)

    return dict(p_hat=g["p_hat"], p_hat_raw=g["p_hat_raw"], responsibilities=resp.tolist(),
                gmm_weights=g["gmm_weights"], gmm_means=g["gmm_means"],
                fit_normal=fit_normal, fit_drought=fit_drought, n=fleet["n"],
                n_days=g["n_days"], mean_responsibility=float(resp.mean()),
                p_hat_bounds=g["p_hat_bounds"])


def fit_regime_mixture_hard(shortfall, fleet, signed_shortfall=None, kind="rbf", seed=0,
                             p_hat_bounds=None, min_effective_days=10):
    """The hard-partition counterpart of fit_regime_mixture_soft, built
    ONLY to answer a direct question (does soft's advantage come from "not
    throwing away data," and how much is it worth here specifically) --
    not used by phase1_run.py/phase2_run.py's Method 4 (which stays soft).
    Uses the IDENTICAL GMM regime-detection step as the soft fit
    (_fit_gmm_regime, same p_hat/responsibilities) so a soft-vs-hard
    comparison isolates only the downstream difference: each day is
    rounded to whichever component has resp >= 0.5 and contributes ONLY to
    that component's (unweighted) GP fit -- the other component never sees
    that day at all, discarding whatever information it carried about the
    other regime. This is the literal "soft weights re-rounded to {0,1}"
    framing climate_cat_lab's own docstring uses."""
    g = _fit_gmm_regime(shortfall, signed_shortfall, seed, p_hat_bounds, min_effective_days)
    resp = g["resp"]
    is_drought_day = resp >= 0.5
    n_drought, n_normal = int(is_drought_day.sum()), int((~is_drought_day).sum())
    if n_drought < 3 or n_normal < 3:
        raise ValueError(f"hard partition too imbalanced for a stable fit "
                          f"(drought={n_drought}, normal={n_normal})")

    fit_normal = fit_gp_shortfall_model(shortfall[~is_drought_day], fleet, kind=kind)
    fit_drought = fit_gp_shortfall_model(shortfall[is_drought_day], fleet, kind=kind)

    return dict(p_hat=g["p_hat"], p_hat_raw=g["p_hat_raw"], responsibilities=resp.tolist(),
                is_drought_day=is_drought_day.tolist(), n_drought=n_drought, n_normal=n_normal,
                gmm_weights=g["gmm_weights"], gmm_means=g["gmm_means"],
                fit_normal=fit_normal, fit_drought=fit_drought, n=fleet["n"],
                n_days=g["n_days"], p_hat_bounds=g["p_hat_bounds"])


def sample_regime_mixture_scenarios(fit, n_scenarios, seed=0):
    rng = np.random.default_rng(seed)
    is_drought_draw = rng.random(n_scenarios) < fit["p_hat"]
    n_drought = int(is_drought_draw.sum())
    n_normal = n_scenarios - n_drought

    out = np.empty((n_scenarios, fit["n"]))
    if n_normal > 0:
        out[~is_drought_draw] = sample_gp_scenarios(fit["fit_normal"], n_normal, seed=seed + 1)
    if n_drought > 0:
        out[is_drought_draw] = sample_gp_scenarios(fit["fit_drought"], n_drought, seed=seed + 2)
    return out
