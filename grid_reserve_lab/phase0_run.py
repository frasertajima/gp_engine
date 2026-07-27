"""Phase 0: the oracle and the sanity check.

Produces the numbers RESULTS_PHASE0.md reports. Four checks, run in order,
a direct structural port of climate_cat_lab/phase0_run.py (shortfall_mw in
place of dollar losses, "day"/"resource-drought" in place of "year"/
"systemic") -- the one number that justifies the whole lab existing is
check 3: does the synthetic DGP actually have genuine, measurable tail
dependence in fleet-wide SHORTFALL, and is it bigger than a Gaussian model
with the same average correlation would ever produce? (The Gaussian
comparator's own answer should be near zero -- settled mathematics,
research/03_correlation_assumption_resource_adequacy.md and
climate_cat_lab/research/03_gaussian_copula_tail_dependence.md; check 4
verifies it holds in this finite, simulated sample too, not just
asymptotically.)

1. Regime mechanism sanity -- drought days must show BOTH higher shortfall
   AND higher internal correlation among nearby sites than normal days, or
   the DGP isn't doing what it's built to do.
2. Distance decay -- nearby site pairs must be more correlated than distant
   pairs (confirms "real spatial structure," the reason an aggregate
   fleet-level correlation profile is the wrong resolution, not just the
   wrong number -- LAB_PLAN.md's corrected Method 2).
3. The headline tail-dependence check -- the literature's own tail-
   dependence coefficient (Donnelly & Embrechts 2010, Definition 5.1, same
   citation climate_cat_lab used): lambda_u = P(Y > G^-1(q) | X > F^-1(q))
   for nearby pairs at q=0.99, using each site's OWN marginal shortfall
   quantile. Independence gives lambda_u = 1-q = 0.01 exactly; this must
   show lambda_u measurably above that baseline.
4. The Gaussian comparator -- fit a multivariate Gaussian to the SAME
   sample's mean and full shortfall covariance (so its ordinary Pearson
   correlation matches the oracle's exactly by construction), resample from
   it, and compute the same lambda_u. It should be far smaller than the
   oracle's -- proof that the oracle's tail dependence in check 3 is a
   genuine DGP property invisible to a correlation-matrix-only model, not
   an artifact of how correlation was measured.
"""

import json

import numpy as np

from fleet import build_fleet
from dgp_simulator import sample_true_output

N_SITES = 100
N_DAYS = 50_000
SEED = 0
N_PAIRS = 40  # pairs averaged per near/far group, to reduce single-pair noise

RESULTS = {}


def _pairwise_distances(lat, lon):
    coords = np.stack([lat, lon], axis=1)
    return np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))


def _sample_pairs(dist, low, high, k, rng):
    """k index pairs (i,j), i<j, with distance in [low, high)."""
    n = dist.shape[0]
    iu, ju = np.triu_indices(n, k=1)
    d = dist[iu, ju]
    mask = (d >= low) & (d < high)
    candidates = np.stack([iu[mask], ju[mask]], axis=1)
    if len(candidates) < k:
        raise ValueError(f"only {len(candidates)} candidate pairs in [{low},{high}), need {k}")
    idx = rng.choice(len(candidates), size=k, replace=False)
    return candidates[idx]


def _avg_corr(shortfall, pairs):
    corrs = [np.corrcoef(shortfall[:, i], shortfall[:, j])[0, 1] for i, j in pairs]
    return float(np.mean(corrs)), float(np.std(corrs))


def check1_regime_mechanism(sim):
    shortfall, regime = sim["shortfall_mw"], sim["regime"]
    total = shortfall.sum(axis=1)
    mean_normal = float(total[~regime].mean())
    mean_drought = float(total[regime].mean())

    # average pairwise correlation among NEARBY sites, computed separately
    # within each regime's days -- normal days should show near-zero
    # correlation (idiosyncratic noise only), drought days should show
    # strongly positive correlation (shared spatial shock field).
    dist = _pairwise_distances(sim["fleet"]["lat"], sim["fleet"]["lon"])
    rng = np.random.default_rng(SEED + 1)
    near_pairs = _sample_pairs(dist, 0.0, sim["params"]["spatial_length_scale_deg"],
                                N_PAIRS, rng)
    corr_normal, _ = _avg_corr(shortfall[~regime], near_pairs)
    corr_drought, _ = _avg_corr(shortfall[regime], near_pairs)

    result = dict(
        n_normal_days=int((~regime).sum()), n_drought_days=int(regime.sum()),
        mean_total_shortfall_normal_mw=mean_normal,
        mean_total_shortfall_drought_mw=mean_drought,
        severity_ratio=mean_drought / mean_normal,
        near_pair_corr_normal_days=corr_normal,
        near_pair_corr_drought_days=corr_drought,
        passed=bool(mean_drought > mean_normal * 2.0 and corr_drought > corr_normal + 0.15),
    )
    print(f"[check1] drought/normal shortfall ratio={result['severity_ratio']:.2f}, "
          f"near-pair corr normal={corr_normal:.3f} drought={corr_drought:.3f} "
          f"passed={result['passed']}")
    return result


def check2_distance_decay(sim):
    shortfall = sim["shortfall_mw"]
    dist = _pairwise_distances(sim["fleet"]["lat"], sim["fleet"]["lon"])
    rng = np.random.default_rng(SEED + 2)
    ls = sim["params"]["spatial_length_scale_deg"]
    near_pairs = _sample_pairs(dist, 0.0, ls, N_PAIRS, rng)
    far_pairs = _sample_pairs(dist, 3.0 * ls, dist.max(), N_PAIRS, rng)

    corr_near, sd_near = _avg_corr(shortfall, near_pairs)
    corr_far, sd_far = _avg_corr(shortfall, far_pairs)

    result = dict(
        unconditional_corr_near=corr_near, unconditional_corr_far=corr_far,
        passed=bool(corr_near > corr_far + 0.05),
    )
    print(f"[check2] unconditional corr: near={corr_near:.3f} (sd {sd_near:.3f}) "
          f"far={corr_far:.3f} (sd {sd_far:.3f}) passed={result['passed']}")
    return result


def _tail_dependence_coeff(shortfall, pairs, q=0.99):
    """Empirical upper tail-dependence coefficient, the literature's own
    definition (Donnelly & Embrechts 2010, Definition 5.1): for each pair
    (X,Y), lambda_u = P(Y > G^-1(q) | X > F^-1(q)), using each SITE's own
    marginal shortfall q-quantile (not a fleet-total-shortfall cutoff --
    climate_cat_lab's Phase 0 found conditioning on the pooled total instead
    gives a confounded, backwards answer, since pooling across the regime
    mixture inflates unconditional correlation via the shared mean-shift
    between regimes). Symmetrized (both directions averaged) and averaged
    over `pairs`. Independence gives lambda_u = 1-q in expectation; genuine
    tail dependence gives lambda_u > 1-q."""
    vals = []
    for i, j in pairs:
        ti = np.quantile(shortfall[:, i], q)
        tj = np.quantile(shortfall[:, j], q)
        exceed_i = shortfall[:, i] > ti
        exceed_j = shortfall[:, j] > tj
        if exceed_i.sum() > 0:
            vals.append(exceed_j[exceed_i].mean())
        if exceed_j.sum() > 0:
            vals.append(exceed_i[exceed_j].mean())
    return float(np.mean(vals)), float(np.std(vals))


def check3_headline_tail_dependence(sim):
    shortfall = sim["shortfall_mw"]
    dist = _pairwise_distances(sim["fleet"]["lat"], sim["fleet"]["lon"])
    rng = np.random.default_rng(SEED + 3)
    ls = sim["params"]["spatial_length_scale_deg"]
    near_pairs = _sample_pairs(dist, 0.0, ls, N_PAIRS, rng)
    far_pairs = _sample_pairs(dist, 3.0 * ls, dist.max(), N_PAIRS, rng)

    q = 0.99
    independence_baseline = 1.0 - q  # 0.01: what independence gives, exactly
    lam_near, sd_near = _tail_dependence_coeff(shortfall, near_pairs, q)
    lam_far, sd_far = _tail_dependence_coeff(shortfall, far_pairs, q)

    result = dict(
        q=q, independence_baseline=independence_baseline,
        lambda_u_near=lam_near, lambda_u_far=lam_far,
        excess_over_independence_near=lam_near - independence_baseline,
        passed=bool(lam_near > 3.0 * independence_baseline and lam_near > lam_far),
    )
    print(f"[check3] ORACLE lambda_u (q={q}): near={lam_near:.3f} (sd {sd_near:.3f}) "
          f"far={lam_far:.3f} (sd {sd_far:.3f}) independence-baseline={independence_baseline:.3f} "
          f"passed={result['passed']}")
    return result, near_pairs


def check4_gaussian_comparator(sim, near_pairs):
    shortfall = sim["shortfall_mw"]
    n_days, n = shortfall.shape
    mean_vec = shortfall.mean(axis=0)
    cov = np.cov(shortfall, rowvar=False)
    cov = 0.5 * (cov + cov.T) + 1e-6 * np.eye(n) * np.diag(cov).mean()

    rng = np.random.default_rng(SEED + 4)
    L = np.linalg.cholesky(cov)
    z = rng.standard_normal((n_days, n))
    gauss_shortfall = mean_vec[None, :] + z @ L.T

    q = 0.99
    independence_baseline = 1.0 - q
    lam_gauss, sd_gauss = _tail_dependence_coeff(gauss_shortfall, near_pairs, q)
    lam_oracle_near = RESULTS["check3_headline_tail_dependence"]["lambda_u_near"]

    result = dict(
        q=q, lambda_u_gaussian=lam_gauss, lambda_u_oracle_near=lam_oracle_near,
        independence_baseline=independence_baseline,
        # Same mean vector AND same full covariance matrix as the oracle --
        # so any pairwise Pearson correlation is identical by construction.
        # The only thing that can differ is tail behavior.
        passed=bool(lam_gauss < 0.5 * lam_oracle_near),
    )
    print(f"[check4] GAUSSIAN COMPARATOR (same mean+cov as oracle) lambda_u near "
          f"pairs={lam_gauss:.3f} (sd {sd_gauss:.3f}) vs oracle={lam_oracle_near:.3f} "
          f"independence-baseline={independence_baseline:.3f} passed={result['passed']}")
    return result


def main():
    fleet = build_fleet(N_SITES, seed=SEED)
    print(f"fleet: {N_SITES} sites, region {fleet['lat'].min():.2f}-"
          f"{fleet['lat'].max():.2f}N x {fleet['lon'].min():.2f}-{fleet['lon'].max():.2f}E, "
          f"mean nameplate {fleet['nameplate_mw'].mean():,.0f} MW, "
          f"mean cf {fleet['cf'].mean():.2f}")

    sim = sample_true_output(fleet, N_DAYS, seed=SEED)
    print(f"simulated {N_DAYS} days, {int(sim['regime'].sum())} drought days "
          f"({sim['regime'].mean():.1%})")

    RESULTS["n_sites"] = N_SITES
    RESULTS["n_days"] = N_DAYS
    RESULTS["params"] = sim["params"]

    RESULTS["check1_regime_mechanism"] = check1_regime_mechanism(sim)
    RESULTS["check2_distance_decay"] = check2_distance_decay(sim)
    check3_result, near_pairs = check3_headline_tail_dependence(sim)
    RESULTS["check3_headline_tail_dependence"] = check3_result
    RESULTS["check4_gaussian_comparator"] = check4_gaussian_comparator(sim, near_pairs)

    all_passed = all(RESULTS[k]["passed"] for k in
                      ["check1_regime_mechanism", "check2_distance_decay",
                       "check3_headline_tail_dependence", "check4_gaussian_comparator"])
    RESULTS["all_passed"] = bool(all_passed)
    print(f"\nALL CHECKS PASSED: {all_passed}")

    with open("results_phase0.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    print("wrote results_phase0.json")


if __name__ == "__main__":
    main()
