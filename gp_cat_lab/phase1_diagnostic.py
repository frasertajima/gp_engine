"""Phase 1 diagnostic (not one of the four real methods -- this one CHEATS
on purpose, to isolate a mechanism, and is reported as a diagnostic, never
as a fifth "method").

phase1_sweep.py ruled out the first hypothesis (regime-FREQUENCY estimation
noise, fixable with more historical years): by n_years=500, method 4's
fitted p_hat (0.065) essentially matches the true p_systemic (0.0667), yet
achieved survival probability is still stuck at ~93.4%, barely above
methods 1-3's ~93.3%, versus a 99.5% target.

This script tests the second hypothesis directly: method 4's fixed top-25%-
quantile partition (used to guarantee enough years to fit each component's
spatial kernel -- see regime_mixture.py's docstring) mixes many ordinary
"just a bit worse than average" years in with the true systemic years
(since true p_systemic ~6.7% << the 25% partition), DILUTING the fitted
"systemic" component's severity toward something much milder than the true
regime -- a bias that does NOT shrink with more data, because the dilution
ratio (25% / 6.7%) stays roughly constant regardless of sample size.

To test this, this script fits the SAME regime-mixture GP shape but using
the TRUE oracle regime labels (`historical["regime"]`) to partition years,
instead of the top-25%-quantile proxy -- something none of the four real
methods are allowed to do, since the whole point of this lab is that a
real model never sees the true regime. If achieved survival jumps close to
99.5% once the partition is exact, that confirms the diluted-partition
mechanism as the dominant driver of Phase 1's gap, not some other bug.
"""

from exposures import build_book
from dgp_simulator import sample_true_losses
import gp_loss_model as gpl
import capital_calc as cc

N_PROPERTIES = 500
BOOK_SEED = 0
HISTORICAL_YEARS = 500
HISTORICAL_SEED = 1000 + 500 * 100  # same seed phase1_sweep.py's first n_years=500 trial used
ORACLE_YEARS = 500_000
ORACLE_SEED = 999
N_SCENARIOS = 20_000
TARGET_SURVIVAL = 0.995


def sample_oracle_partitioned_scenarios(fit_normal, fit_systemic, p_true, V,
                                         n_scenarios, seed=0):
    import numpy as np
    rng = np.random.default_rng(seed)
    is_sys = rng.random(n_scenarios) < p_true
    n_sys, n_norm = int(is_sys.sum()), int((~is_sys).sum())
    out = np.empty((n_scenarios, fit_normal["n"]))
    if n_norm > 0:
        out[~is_sys] = gpl.sample_gp_scenarios(fit_normal, V, n_norm, seed=seed + 1)
    if n_sys > 0:
        out[is_sys] = gpl.sample_gp_scenarios(fit_systemic, V, n_sys, seed=seed + 2)
    return out


def main():
    book = build_book(N_PROPERTIES, seed=BOOK_SEED)
    V = book["insured_value"]

    oracle = sample_true_losses(book, ORACLE_YEARS, seed=ORACLE_SEED)
    oracle_total = oracle["losses"].sum(axis=1)
    oracle_true_capital = cc.required_capital(oracle_total, TARGET_SURVIVAL)
    print(f"oracle true capital @ {TARGET_SURVIVAL:.1%} = ${oracle_true_capital:,.0f}")

    historical = sample_true_losses(book, HISTORICAL_YEARS, seed=HISTORICAL_SEED)
    losses_hist = historical["losses"]
    is_true_systemic = historical["regime"]
    p_true = historical["params"]["p_systemic"]
    n_true = int(is_true_systemic.sum())
    print(f"historical: {HISTORICAL_YEARS} years, {n_true} TRUE systemic years "
          f"(oracle-cheat diagnostic uses this exact label, unlike any real method)")

    fit_normal = gpl.fit_gp_loss_model(losses_hist[~is_true_systemic], book)
    fit_systemic = gpl.fit_gp_loss_model(losses_hist[is_true_systemic], book)
    print(f"systemic-component fit: sigma_f2={fit_systemic['sigma_f2']:.4f} "
          f"sigma_n2={fit_systemic['sigma_n2']:.4f} (vs normal-component "
          f"sigma_f2={fit_normal['sigma_f2']:.4f} sigma_n2={fit_normal['sigma_n2']:.4f})")

    scen = sample_oracle_partitioned_scenarios(fit_normal, fit_systemic, p_true, V,
                                                N_SCENARIOS, seed=42)
    scen_total = scen.sum(axis=1)
    capital = cc.required_capital(scen_total, TARGET_SURVIVAL)
    achieved = cc.survival_probability(oracle_total, capital)
    shortfall = cc.expected_shortfall(oracle_total, capital)
    gap = capital - oracle_true_capital

    print(f"\n[oracle-cheat diagnostic] capital=${capital:,.0f} "
          f"achieved_survival={achieved:.4f} (target {TARGET_SURVIVAL:.4f}) "
          f"shortfall=${shortfall:,.0f}/yr gap_vs_true=${gap:,.0f}")


if __name__ == "__main__":
    main()
