"""Method 3 -- GP forecast (Method 2, unchanged) plus a soft-EM regime-
mixture safety margin, reusing this codebase's own recurring pattern
(`climate_cat_lab`/`grid_reserve_lab`/`hydro_reserve_lab`'s `regime_mixture.py`):
a 2-component Gaussian mixture on daily net load (normal vs. stress),
`sklearn.mixture.GaussianMixture`, giving a genuine soft responsibility
P(stress) per day.

The real 4.5x persistence ratio `phase0_run.py` already measured (P(stress
tomorrow | stress today) vs. the marginal rate) is the justification for
using YESTERDAY's responsibility to size TODAY's stress response -- a real,
checked mechanism, not an assumed one.

**WHAT THE STRESS RESPONSE ACTUALLY CONTROLS, and why it changed
(CODE_REVIEW.md C1, 2026-08-05).** The first version of this module added the
regime margin to Method 2's overnight CHARGE TARGET. That was measured to be
structurally dead: `gp_forecast_model.predict_targets` clips the target at
battery capacity, and real daily net load exceeds capacity on 49.5% of days,
so on exactly the high-demand days this layer exists for, the target was
already saturated and the margin was clipped to zero. Measured on the real
2017-2025 record, the old margin fired ONLY on days whose actual net load
averaged 3.9 kWh (summer) and was exactly zero on the days averaging 25.7
kWh. Phase 1's original "regime-awareness is a small negative" result was
therefore not a measurement of regime-awareness at all.

The margin now sizes a PEAK-WINDOW DISCHARGE RESERVE instead
(`dispatch_sim.RESERVE_HOURS`): on a predicted stress day, hold back SOC
through the standard-rate hours so it is still available during the 4-9pm
surcharge window. That quantity is not bounded by the charge target, so it
has real headroom on stress days. Method 3's charge targets are now
IDENTICAL to Method 2's -- the regime layer's entire contribution is the
reserve, making this a clean superset test of Method 2.

Per this lab's own C2 lesson (don't read a flat result as a finding about a
mechanism until you've checked the mechanism could move the number at all),
`constant_reserves` provides the matching ablation: the same reserve floor,
sized by a fixed constant instead of by P(stress). If Method 3 does not beat
that, the soft-EM layer is not what is doing the work.
"""

import numpy as np
from sklearn.mixture import GaussianMixture

import gp_forecast_model as gpf

CAPACITY_KWH = 13.5


def fit(train_daily, seed=0):
    """Returns (gp, gmm) -- the same GP1D fit as Method 2, plus a 2-component
    GaussianMixture on the training daily net_load."""
    gp = gpf.fit(train_daily)
    gmm = GaussianMixture(n_components=2, random_state=seed, n_init=3)
    gmm.fit(train_daily["net_load_kwh"].values.reshape(-1, 1))
    return gp, gmm


def _stress_component(gmm):
    return int(np.argmax(gmm.means_.ravel()))


def predict_targets(gp, daily_index, net_load_series, capacity_kwh=CAPACITY_KWH):
    """Method 3's overnight charge targets are IDENTICAL to Method 2's -- the
    regime layer contributes the peak-window reserve (`predict_reserves`),
    not a charge margin. See this module's docstring for why the charge
    target cannot carry a stress response."""
    return gpf.predict_targets(gp, daily_index, net_load_series, capacity_kwh=capacity_kwh)


def margin_scale(gmm):
    """The mixture's own stress-vs-normal mean gap (kWh) -- a real,
    data-derived scale for the stress response, not an arbitrary constant."""
    stress_idx = _stress_component(gmm)
    normal_idx = 1 - stress_idx
    return max(float(gmm.means_.ravel()[stress_idx] - gmm.means_.ravel()[normal_idx]), 0.0)


def predict_reserves(gmm, daily_index, net_load_series, capacity_kwh=CAPACITY_KWH):
    """dict date -> peak-window SOC reserve (kWh), sized by YESTERDAY's
    P(stress) (the GMM's own soft responsibility for yesterday's realized net
    load) times the mixture's stress-vs-normal mean gap. Consumed by
    `dispatch_sim.simulate_with_targets(daily_reserve_kwh=...)`.

    Using yesterday's responsibility is justified by the real 4.5x
    day-to-day persistence `phase0_run.py` measured directly -- not assumed."""
    import datetime
    one_day = datetime.timedelta(days=1)

    stress_idx = _stress_component(gmm)
    scale = margin_scale(gmm)

    reserves = {}
    for d in daily_index:
        prev_day = d - one_day
        if prev_day not in net_load_series.index:
            reserves[d] = 0.0
            continue
        prev_val = net_load_series.loc[prev_day]
        p_stress_yesterday = float(gmm.predict_proba([[prev_val]])[0, stress_idx])
        reserves[d] = float(np.clip(scale * p_stress_yesterday, 0.0, capacity_kwh))
    return reserves


def constant_reserves(daily_index, reserve_kwh, capacity_kwh=CAPACITY_KWH):
    """Ablation for Method 3 (Method 3b): the SAME peak-window reserve floor,
    sized by a fixed constant rather than by the soft-EM P(stress). Isolates
    whether the regime layer's per-day sizing adds anything over simply
    always reserving. See this module's docstring."""
    r = float(np.clip(reserve_kwh, 0.0, capacity_kwh))
    return {d: r for d in daily_index}


if __name__ == "__main__":
    from daily_agg import build_daily, TRAIN_YEARS

    daily = build_daily()
    daily.index = daily.index.date
    years = np.array([d.year for d in daily.index])
    train_mask = (years >= TRAIN_YEARS[0]) & (years <= TRAIN_YEARS[1])
    train_daily = daily.loc[train_mask]

    gp, gmm = fit(train_daily)
    stress_idx = _stress_component(gmm)
    print(f"GMM fit: means={gmm.means_.ravel()}  weights={gmm.weights_}  "
          f"stress_component_idx={stress_idx}  margin_scale={margin_scale(gmm):.2f} kWh")

    # Charge targets must now be identical to Method 2's by construction.
    idx = daily.index[1:200]
    t3 = predict_targets(gp, idx, daily["net_load_kwh"])
    t2 = gpf.predict_targets(gp, idx, daily["net_load_kwh"])
    assert all(t3[d] == t2[d] for d in idx), "Method 3 targets must equal Method 2's"
    print("charge targets identical to Method 2: OK")

    # The stress response now lives in the reserve, which must be able to fire on
    # HIGH-demand days -- the regression CODE_REVIEW.md C1 caught.
    res = predict_reserves(gmm, idx, daily["net_load_kwh"])
    r = np.array([res[d] for d in idx])
    nl = daily["net_load_kwh"].loc[idx].values
    hi, lo = r >= np.percentile(r, 67), r <= np.percentile(r, 33)
    print(f"reserve: mean={r.mean():.2f} max={r.max():.2f} kWh  "
          f"corr(reserve, actual net load)={np.corrcoef(r, nl)[0,1]:+.3f}")
    print(f"  mean ACTUAL net load, top-third reserve days:    {nl[hi].mean():.1f} kWh")
    print(f"  mean ACTUAL net load, bottom-third reserve days: {nl[lo].mean():.1f} kWh")
    print("  (the response must be LARGER on the high-net-load days. The old charge-margin "
          "version had this backwards -- it fired on 3.9 kWh days, never on 25.7 kWh days.)")
