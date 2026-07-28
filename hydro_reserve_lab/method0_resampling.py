"""Method 0 — historical-scenario resampling, the REAL practice (Bureau of Reclamation's CRSS
model resamples the historical/paleo record; research/03_real_reservoir_planning_practice.md).
Simplified here to i.i.d. resampling of pre-2000 annual Lees Ferry flows (no block-bootstrap
preserving autocorrelation, no paleo-record extension — both real, honest simplifications, stated
plainly, not the full CRSS machinery)."""

import numpy as np

from reservoir_sim import cfs_mean_to_annual_af


class HistoricalResampling:
    def __init__(self, n_traces=3000, horizon=26, seed=0):
        self.n_traces = n_traces
        self.horizon = horizon
        self.seed = seed

    def fit(self, lees_ferry_cfs_train):
        self.train_af = cfs_mean_to_annual_af(np.asarray(lees_ferry_cfs_train, dtype=float))
        return self

    def sample_traces(self, years=None):
        """years: ignored (this method is explicitly stationary/time-invariant, the real
        practice's own property CRSS's ensemble resampling shares)."""
        rng = np.random.default_rng(self.seed)
        idx = rng.integers(0, len(self.train_af), size=(self.n_traces, self.horizon))
        return self.train_af[idx]
