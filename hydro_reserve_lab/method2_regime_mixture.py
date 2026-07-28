"""Method 2 — GP + soft-EM regime-mixture, fifth port of the mechanism `climate_cat_lab` ->
`cvar_gp_lab` -> `grid_reserve_lab` -> `shm_lab` -> here, and the first to use a TIME-VARYING
regime probability rather than a fixed rate — a direct, evidence-driven response to Phase 0's
finding that the real post-2000 drought rate is measurably higher than the pre-2000 baseline
(RESULTS_PHASE0.md), not a stylistic choice."""

import numpy as np
from scipy.special import expit

from hydro_gaussian import fit_regime_mixture_time_varying
from reservoir_sim import cfs_mean_to_annual_af

LEES_FERRY_COL = 0


class RegimeMixtureTimeVarying:
    def __init__(self, n_traces=3000, horizon=26, seed=0):
        self.n_traces = n_traces
        self.horizon = horizon
        self.seed = seed

    def fit(self, log_flow_train, years_train):
        self.fitted = fit_regime_mixture_time_varying(log_flow_train, years_train, seed=self.seed)
        return self

    def pi_drought(self, years):
        f = self.fitted
        return expit(f["a"] + f["b"] * (np.asarray(years) - f["year_ref"]))

    def sample_traces(self, years):
        """years: the REAL calendar years being forecast (e.g. 2000-2025) — this is what lets the
        fitted trend extrapolate a higher drought probability into the real megadrought period,
        unlike Method 0/1's time-invariant forecast."""
        rng = np.random.default_rng(self.seed)
        years = np.asarray(years)
        f = self.fitted
        pi = self.pi_drought(years)  # (horizon,)

        traces = np.zeros((self.n_traces, len(years)))
        for t, p in enumerate(pi):
            is_drought = rng.uniform(size=self.n_traces) < p
            n_drought = int(is_drought.sum())
            n_normal = self.n_traces - n_drought
            draws = np.empty((self.n_traces, len(f["mu_drought"])))
            if n_drought:
                draws[is_drought] = rng.multivariate_normal(f["mu_drought"], f["cov"], size=n_drought)
            if n_normal:
                draws[~is_drought] = rng.multivariate_normal(f["mu_normal"], f["cov"], size=n_normal)
            lees_ferry_cfs = np.exp(draws[:, LEES_FERRY_COL])
            traces[:, t] = cfs_mean_to_annual_af(lees_ferry_cfs)
        return traces
