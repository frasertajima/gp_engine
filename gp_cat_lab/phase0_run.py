"""Phase 0: the oracle and the sanity check.

Produces the numbers RESULTS_PHASE0.md reports. Four checks, run in order --
the one number that justifies the whole lab existing is check 3: does the
synthetic DGP actually have genuine, measurable tail dependence, and is it
bigger than a Gaussian model with the same average correlation would ever
produce? (The Gaussian comparator's own answer should be near zero -- that's
the point verified mathematically in research/03_gaussian_copula_tail_dependence.md;
check 4 verifies it holds in this finite, simulated sample too, not just
asymptotically.)

1. Regime mechanism sanity -- systemic years must be both more severe AND
   more internally correlated than normal years, or the DGP isn't doing
   what it's built to do.
2. Distance decay -- nearby property pairs must be more correlated than
   distant pairs (confirms "real spatial structure," the reason a flat
   correlation shortcut is the wrong shape, not just the wrong number).
3. The headline tail-dependence check -- the literature's own tail-
   dependence coefficient (Donnelly & Embrechts 2010, Definition 5.1):
   lambda_u = P(Y > G^-1(q) | X > F^-1(q)) for nearby pairs at q=0.99,
   using each property's OWN marginal quantile. (An earlier draft of this
   check conditioned on total book loss instead and got a confounded,
   backwards-looking answer -- see the docstring on
   `_tail_dependence_coeff` below for why pooling across the regime
   mixture makes that particular measure misleading. The per-property
   joint-exceedance-probability definition used here is the standard one
   and doesn't have that confound.) Independence gives lambda_u = 1-q =
   0.01 exactly; this must show lambda_u measurably above that baseline.
4. The Gaussian comparator -- fit a multivariate Gaussian to the SAME
   sample's mean and full covariance (so its ordinary Pearson correlation
   matches the oracle's exactly by construction), resample from it, and
   compute the same lambda_u. It should be far smaller than the oracle's --
   proof that the oracle's tail dependence in check 3 is a genuine DGP
   property invisible to a correlation-matrix-only model, not an artifact
   of how correlation was measured.
"""

import json

import numpy as np

from exposures import build_book
from dgp_simulator import sample_true_losses

N_PROPERTIES = 500
N_YEARS = 50_000
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


def _avg_corr(losses, pairs):
    corrs = [np.corrcoef(losses[:, i], losses[:, j])[0, 1] for i, j in pairs]
    return float(np.mean(corrs)), float(np.std(corrs))


def check1_regime_mechanism(sim):
    losses, regime = sim["losses"], sim["regime"]
    total = losses.sum(axis=1)
    mean_normal = float(total[~regime].mean())
    mean_systemic = float(total[regime].mean())

    # average pairwise correlation among NEARBY properties, computed
    # separately within each regime's years -- normal years should show
    # near-zero correlation (idiosyncratic noise only), systemic years
    # should show strongly positive correlation (shared spatial field).
    dist = _pairwise_distances(sim["book"]["lat"], sim["book"]["lon"])
    rng = np.random.default_rng(SEED + 1)
    near_pairs = _sample_pairs(dist, 0.0, sim["params"]["spatial_length_scale_deg"],
                                N_PAIRS, rng)
    corr_normal, _ = _avg_corr(losses[~regime], near_pairs)
    corr_systemic, _ = _avg_corr(losses[regime], near_pairs)

    result = dict(
        n_normal_years=int((~regime).sum()), n_systemic_years=int(regime.sum()),
        mean_total_loss_normal=mean_normal, mean_total_loss_systemic=mean_systemic,
        severity_ratio=mean_systemic / mean_normal,
        near_pair_corr_normal_years=corr_normal,
        near_pair_corr_systemic_years=corr_systemic,
        passed=bool(mean_systemic > mean_normal * 2.0 and corr_systemic > corr_normal + 0.15),
    )
    print(f"[check1] systemic/normal severity ratio={result['severity_ratio']:.2f}, "
          f"near-pair corr normal={corr_normal:.3f} systemic={corr_systemic:.3f} "
          f"passed={result['passed']}")
    return result


def check2_distance_decay(sim):
    losses = sim["losses"]
    dist = _pairwise_distances(sim["book"]["lat"], sim["book"]["lon"])
    rng = np.random.default_rng(SEED + 2)
    ls = sim["params"]["spatial_length_scale_deg"]
    near_pairs = _sample_pairs(dist, 0.0, ls, N_PAIRS, rng)
    far_pairs = _sample_pairs(dist, 3.0 * ls, dist.max(), N_PAIRS, rng)

    corr_near, sd_near = _avg_corr(losses, near_pairs)
    corr_far, sd_far = _avg_corr(losses, far_pairs)

    result = dict(
        unconditional_corr_near=corr_near, unconditional_corr_far=corr_far,
        passed=bool(corr_near > corr_far + 0.05),
    )
    print(f"[check2] unconditional corr: near={corr_near:.3f} (sd {sd_near:.3f}) "
          f"far={corr_far:.3f} (sd {sd_far:.3f}) passed={result['passed']}")
    return result


def _tail_dependence_coeff(losses, pairs, q=0.99):
    """Empirical upper tail-dependence coefficient, the literature's own
    definition (Donnelly & Embrechts 2010, Definition 5.1 -- see
    research/03_gaussian_copula_tail_dependence.md): for each pair (X,Y),
    lambda_u = P(Y > G^-1(q) | X > F^-1(q)), using each PROPERTY's own
    marginal q-quantile (not a book-total-loss cutoff -- an earlier version
    of this check conditioned on total book loss instead and got a
    confounded, misleading answer: pooling across the regime mixture
    inflates the *unconditional* correlation via the shared mean-shift
    between regimes, which then makes a tail-conditioned correlation look
    LOWER than unconditional even though genuine tail dependence is
    present. The per-property-marginal joint-exceedance-probability
    definition used here doesn't have that confound.) Symmetrized (both
    directions averaged) and averaged over `pairs`. Independence gives
    lambda_u = 1-q in expectation; genuine tail dependence gives
    lambda_u > 1-q."""
    vals = []
    for i, j in pairs:
        ti = np.quantile(losses[:, i], q)
        tj = np.quantile(losses[:, j], q)
        exceed_i = losses[:, i] > ti
        exceed_j = losses[:, j] > tj
        if exceed_i.sum() > 0:
            vals.append(exceed_j[exceed_i].mean())
        if exceed_j.sum() > 0:
            vals.append(exceed_i[exceed_j].mean())
    return float(np.mean(vals)), float(np.std(vals))


def check3_headline_tail_dependence(sim):
    losses = sim["losses"]
    dist = _pairwise_distances(sim["book"]["lat"], sim["book"]["lon"])
    rng = np.random.default_rng(SEED + 3)
    ls = sim["params"]["spatial_length_scale_deg"]
    near_pairs = _sample_pairs(dist, 0.0, ls, N_PAIRS, rng)
    far_pairs = _sample_pairs(dist, 3.0 * ls, dist.max(), N_PAIRS, rng)

    q = 0.99
    independence_baseline = 1.0 - q  # 0.01: what independence gives, exactly
    lam_near, sd_near = _tail_dependence_coeff(losses, near_pairs, q)
    lam_far, sd_far = _tail_dependence_coeff(losses, far_pairs, q)

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
    losses = sim["losses"]
    n_years, n = losses.shape
    mean_vec = losses.mean(axis=0)
    cov = np.cov(losses, rowvar=False)
    cov = 0.5 * (cov + cov.T) + 1e-6 * np.eye(n) * np.diag(cov).mean()

    rng = np.random.default_rng(SEED + 4)
    L = np.linalg.cholesky(cov)
    z = rng.standard_normal((n_years, n))
    gauss_losses = mean_vec[None, :] + z @ L.T
    gauss_losses = np.clip(gauss_losses, 0.0, None)  # losses can't be negative

    q = 0.99
    independence_baseline = 1.0 - q
    lam_gauss, sd_gauss = _tail_dependence_coeff(gauss_losses, near_pairs, q)
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
    book = build_book(N_PROPERTIES, seed=SEED)
    print(f"book: {N_PROPERTIES} properties, region {book['lat'].min():.2f}-"
          f"{book['lat'].max():.2f}N x {book['lon'].min():.2f}-{book['lon'].max():.2f}E, "
          f"mean insured value ${book['insured_value'].mean():,.0f}")

    sim = sample_true_losses(book, N_YEARS, seed=SEED)
    print(f"simulated {N_YEARS} years, {int(sim['regime'].sum())} systemic "
          f"({sim['regime'].mean():.1%})")

    RESULTS["n_properties"] = N_PROPERTIES
    RESULTS["n_years"] = N_YEARS
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
