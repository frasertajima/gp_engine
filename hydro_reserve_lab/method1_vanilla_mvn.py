"""Method 1 — vanilla joint-Gaussian across the 5 gauges (log-flow), STATIONARY: no time trend,
no regime. Tests whether pooling correlated gauges alone (without any nonstationarity awareness)
already closes any gap over Method 0's plain resampling. The "spatial kernel" simplification is
documented in `hydro_gaussian.py`'s own module docstring."""

import numpy as np

from hydro_gaussian import fit_mvn
from reservoir_sim import cfs_mean_to_annual_af

LEES_FERRY_COL = 0  # column 0 by convention (see phase1_run.py's column ordering)


class VanillaMVN:
    def __init__(self, n_traces=3000, horizon=26, seed=0):
        self.n_traces = n_traces
        self.horizon = horizon
        self.seed = seed

    def fit(self, log_flow_train):
        self.mu, self.cov = fit_mvn(log_flow_train)
        return self

    def sample_traces(self, years=None):
        rng = np.random.default_rng(self.seed)
        n_years = self.horizon if years is None else len(years)
        draws = rng.multivariate_normal(self.mu, self.cov, size=(self.n_traces, n_years))
        lees_ferry_log = draws[:, :, LEES_FERRY_COL]
        lees_ferry_cfs = np.exp(lees_ferry_log)
        return cfs_mean_to_annual_af(lees_ferry_cfs)
