"""Method 2 -- a vanilla GP day-ahead forecast informing the overnight
pre-charge target. No archived real weather FORECAST exists to train
against (only realized history) -- instead of persistence/autocorrelation
being assumed, `phase0_run.py` already found and measured it directly (a
real 4.5x day-to-day stress-state persistence ratio), so this reuses that
confirmed mechanism: predict TODAY's net load from YESTERDAY's, a genuine
lag-1 autoregression, not an external forecast product.

Reuses `shm_lab/gp1d.py`'s minimal exact GP regression unchanged (no GPU
engine needed at this domain's scale -- ~1,000 training days -- same
scoping note `shm_lab` made for its own ~100-400 point fits).
"""

import os
import sys

import numpy as np

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shm_lab"))
from gp1d import GP1D  # noqa: E402

CAPACITY_KWH = 13.5


def fit(train_daily):
    """train_daily: DataFrame with a `net_load_kwh` column, daily-indexed,
    already sorted. Fits net_load(day) ~ net_load(day-1). Returns the fitted
    GP1D."""
    y = train_daily["net_load_kwh"].values[1:]
    x = train_daily["net_load_kwh"].values[:-1]
    gp = GP1D().fit(x, y, n_restarts=4)
    return gp


def predict_targets(gp, daily_index, net_load_series, capacity_kwh=CAPACITY_KWH):
    """daily_index: the dates to produce a target for (e.g. train+test).
    net_load_series: a pandas Series of REALIZED net_load, indexed by date,
    covering at least one day before `daily_index[0]` (so day d's target can
    use day d-1's real, already-known net load -- no lookahead into day d
    itself). Returns dict date -> target_soc_kwh."""
    import datetime
    one_day = datetime.timedelta(days=1)

    targets = {}
    for d in daily_index:
        prev_day = d - one_day
        if prev_day not in net_load_series.index:
            targets[d] = 0.0  # no prior-day data (first day of record) -- fall back to no pre-charge
            continue
        x_star = np.array([net_load_series.loc[prev_day]])
        mean, var = gp.predict(x_star)
        targets[d] = float(np.clip(mean[0], 0.0, capacity_kwh))
    return targets


if __name__ == "__main__":
    from daily_agg import build_daily, TRAIN_YEARS, TEST_YEARS

    daily = build_daily()
    daily.index = daily.index.date
    # date-typed index doesn't support string year slicing directly -- filter by year instead
    years = np.array([d.year for d in daily.index])
    train_mask = (years >= TRAIN_YEARS[0]) & (years <= TRAIN_YEARS[1])
    train_daily = daily.loc[train_mask]

    gp = fit(train_daily)
    print(f"GP1D fit: ell={gp.ell:.3f}  sigma_f2={gp.sigma_f2:.3f}  sigma_n2={gp.sigma_n2:.3f}")

    targets = predict_targets(gp, daily.index[1:200], daily["net_load_kwh"])
    vals = np.array(list(targets.values()))
    print(f"sample targets (first 200 test days): mean={vals.mean():.2f}  "
          f"range=[{vals.min():.2f},{vals.max():.2f}]")

    # Real predictive check: correlation between predicted and actual next-day net load
    actual = daily["net_load_kwh"].values[1:]
    pred_all = np.array([targets.get(d, np.nan) for d in daily.index[1:200]])
    actual_200 = daily["net_load_kwh"].values[1:200]
    corr = np.corrcoef(pred_all, actual_200)[0, 1]
    print(f"correlation(predicted target, actual next-day net load), first 200 test days: {corr:.3f}")
