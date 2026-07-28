"""Method 3 — the MANDATORY non-mixture control (`gp_engine/PLAN.md` §7): a single multivariate
Gaussian with a linear time TREND on the mean, no latent regime, no EM at all. Isolates whether a
trend alone (pooling + nonstationarity-awareness, but no mixture) already captures whatever benefit
Method 2's regime-mixture shows — the exact check `shm_lab`'s Phase 1c found necessary, run from
the start this time rather than added after an initial result."""

import numpy as np

from hydro_gaussian import fit_mvn_trend
from reservoir_sim import cfs_mean_to_annual_af

LEES_FERRY_COL = 0


class TrendControl:
    def __init__(self, n_traces=3000, horizon=26, seed=0):
        self.n_traces = n_traces
        self.horizon = horizon
        self.seed = seed

    def fit(self, log_flow_train, years_train):
        self.mu0, self.trend, self.year_ref, self.cov = fit_mvn_trend(log_flow_train, years_train)
        return self

    def sample_traces(self, years):
        rng = np.random.default_rng(self.seed)
        years = np.asarray(years)
        traces = np.zeros((self.n_traces, len(years)))
        for t, yr in enumerate(years):
            mu_t = self.mu0 + self.trend * (yr - self.year_ref)
            draws = rng.multivariate_normal(mu_t, self.cov, size=self.n_traces)
            lees_ferry_cfs = np.exp(draws[:, LEES_FERRY_COL])
            traces[:, t] = cfs_mean_to_annual_af(lees_ferry_cfs)
        return traces
