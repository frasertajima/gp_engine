"""Validates rff_sampler.py BEFORE Phase 2 trusts it at OOC scale: samples
the SAME spatial kernel (dgp_simulator.py's own length scale and field
variance) two ways at Phase 0's exact n=500 scale --

1. EXACT: dense Cholesky (dgp_simulator.py's own approach, the one Phase 0
   validated).
2. APPROXIMATE: rff_sampler.py's Random Fourier Features.

-- and compares near-pair / far-pair correlation. If they agree closely,
RFF is trustworthy for Phase 2's OOC-scale sampling (where exact Cholesky
sampling is infeasible); if they don't, Phase 2 must not proceed on RFF
without fixing the mismatch first (e.g. more features).
"""

import numpy as np

from exposures import build_book
from dgp_simulator import _rbf_kernel, DEFAULT_PARAMS
from rff_sampler import sample_rff_field

N_PROPERTIES = 500
SEED = 0
N_SCENARIOS = 40_000
N_FEATURES = 800


def _pairwise_distances(lat, lon):
    coords = np.stack([lat, lon], axis=1)
    return np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))


def _sample_pairs(dist, low, high, k, rng):
    n = dist.shape[0]
    iu, ju = np.triu_indices(n, k=1)
    d = dist[iu, ju]
    mask = (d >= low) & (d < high)
    candidates = np.stack([iu[mask], ju[mask]], axis=1)
    idx = rng.choice(len(candidates), size=min(k, len(candidates)), replace=False)
    return candidates[idx]


def _avg_corr(field, pairs):
    return float(np.mean([np.corrcoef(field[:, i], field[:, j])[0, 1] for i, j in pairs]))


def main():
    book = build_book(N_PROPERTIES, seed=SEED)
    coords = np.stack([book["lat"], book["lon"]], axis=1)
    ell = DEFAULT_PARAMS["spatial_length_scale_deg"]
    sigma_f2 = DEFAULT_PARAMS["spatial_field_sigma"] ** 2

    dist = _pairwise_distances(book["lat"], book["lon"])
    rng = np.random.default_rng(1)
    near_pairs = _sample_pairs(dist, 0.0, ell, 40, rng)
    far_pairs = _sample_pairs(dist, 3.0 * ell, dist.max(), 40, rng)

    K = _rbf_kernel(book["lat"], book["lon"], ell, sigma_f2)
    L = np.linalg.cholesky(K + 1e-9 * np.eye(N_PROPERTIES))
    rng2 = np.random.default_rng(2)
    z_exact = rng2.standard_normal((N_SCENARIOS, N_PROPERTIES)) @ L.T

    z_rff = sample_rff_field(coords, ell, sigma_f2, sigma_n2=0.0,
                              n_scenarios=N_SCENARIOS, n_features=N_FEATURES,
                              seed=3, feature_seed=4)

    exact_near, exact_far = _avg_corr(z_exact, near_pairs), _avg_corr(z_exact, far_pairs)
    rff_near, rff_far = _avg_corr(z_rff, near_pairs), _avg_corr(z_rff, far_pairs)

    print(f"exact  : near_corr={exact_near:.4f}  far_corr={exact_far:.4f}")
    print(f"RFF({N_FEATURES} features): near_corr={rff_near:.4f}  far_corr={rff_far:.4f}")
    print(f"abs diff: near={abs(exact_near - rff_near):.4f}  far={abs(exact_far - rff_far):.4f}")

    passed = abs(exact_near - rff_near) < 0.03 and abs(exact_far - rff_far) < 0.03
    print(f"VALIDATION {'PASSED' if passed else 'FAILED'} (tolerance 0.03)")
    return passed


if __name__ == "__main__":
    ok = main()
    import sys
    sys.exit(0 if ok else 1)
