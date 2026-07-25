"""Robustness check: is the soft-classifier finding an artifact of one
hand-picked DGP configuration? One-at-a-time sweep around
dgp_simulator.py's defaults over the spatial length scale (ell), the true
regime frequency (p_sys), and the regime severity multiplier (m_sys), plus
one non-stationary variant (p_sys drifting upward across the historical
window, testing whether historical fitting under-represents a "climate
trend" future). For each config: fit methods 1, 3, 4 (hard), 4 (soft) on a
FIXED, moderate historical sample size (120 years, realistic-to-generous
company history), 3 seeds averaged, scored against a config-specific
oracle.
"""

import json

import numpy as np

from exposures import build_book
from dgp_simulator import sample_true_losses, DEFAULT_PARAMS
import naive_baselines as nb
import gp_loss_model as gpl
import regime_mixture as rm
import capital_calc as cc

N_PROPERTIES = 500
BOOK_SEED = 0
ORACLE_YEARS = 200_000
ORACLE_SEED = 999
N_SCENARIOS = 20_000
TARGET_SURVIVAL = 0.995
HISTORICAL_YEARS = 120
SEEDS_PER_CONFIG = 3
SEED_BASE = 7000

CONFIGS = {
    "baseline": dict(),
    "ell=0.1 (localized field)": dict(spatial_length_scale_deg=0.1),
    "ell=1.5 (regional field)": dict(spatial_length_scale_deg=1.5),
    "p_sys=1/30 (rarer)": dict(p_systemic=1 / 30),
    "p_sys=1/5 (frequent)": dict(p_systemic=1 / 5),
    "m_sys=2.0 (weak signal)": dict(regime_severity_mult=2.0),
    "m_sys=10.0 (strong signal)": dict(regime_severity_mult=10.0),
}


def sample_true_losses_drifting(book, n_years, p_start, p_end, params=None, seed=0,
                                 jitter=1e-9):
    """Non-stationary variant: p_systemic drifts LINEARLY from p_start to
    p_end across the n_years historical window (a stand-in for a warming
    climate trend the historical window only partially reflects), instead
    of dgp_simulator.py's fixed p_systemic. Otherwise identical mechanism.
    Self-contained here rather than added to dgp_simulator.py -- a
    one-off robustness config, not a fixture other scripts reuse."""
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    rng = np.random.default_rng(seed)
    n = book["n"]
    mu = book["mu"]
    V = book["insured_value"]
    coords = np.stack([book["lat"], book["lon"]], axis=1)
    d2 = ((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1)
    K = p["spatial_field_sigma"] ** 2 * np.exp(-0.5 * d2 / p["spatial_length_scale_deg"] ** 2)
    L = np.linalg.cholesky(K + jitter * np.eye(n))

    p_t = np.linspace(p_start, p_end, n_years)
    regime = rng.random(n_years) < p_t
    idio = rng.normal(0.0, p["idio_sigma"], size=(n_years, n))
    n_sys = int(regime.sum())
    z_field = np.zeros((n_years, n))
    if n_sys > 0:
        z_field[regime] = rng.standard_normal((n_sys, n)) @ L.T

    log_ratio = idio - 0.5 * p["idio_sigma"] ** 2
    mult = np.where(regime[:, None], p["regime_severity_mult"], 1.0)
    loss_ratio = mu[None, :] * mult * np.exp(log_ratio + z_field)
    return dict(losses=loss_ratio * V[None, :], regime=regime, book=book, params=p, seed=seed)


def run_trial(book, oracle_total, oracle_true_capital, losses_hist):
    V = book["insured_value"]
    table = {}

    fit1 = nb.fit_independence(losses_hist, book)
    scen1 = nb.sample_independence_scenarios(fit1, V, N_SCENARIOS, seed=1)
    table["1_independence"] = scen1.sum(axis=1)

    fit3 = gpl.fit_gp_loss_model(losses_hist, book)
    scen3 = gpl.sample_gp_scenarios(fit3, V, N_SCENARIOS, seed=3)
    table["3_vanilla_gp"] = scen3.sum(axis=1)

    try:
        fit4h = rm.fit_regime_mixture(losses_hist, book)
        table["4_hard"] = rm.sample_regime_mixture_scenarios(
            fit4h, V, N_SCENARIOS, seed=4).sum(axis=1)
    except ValueError:
        table["4_hard"] = None

    fit4s = rm.fit_regime_mixture_soft(losses_hist, book)
    table["4_soft"] = rm.sample_regime_mixture_scenarios(
        fit4s, V, N_SCENARIOS, seed=5).sum(axis=1)

    scored = {}
    for name, scenario_total in table.items():
        if scenario_total is None:
            continue
        capital = cc.required_capital(scenario_total, TARGET_SURVIVAL)
        scored[name] = dict(
            required_capital=capital,
            achieved_survival_probability=cc.survival_probability(oracle_total, capital),
            capital_gap_vs_oracle_dollars=capital - oracle_true_capital)
    return scored


def summarize(book, params, draw_fn):
    oracle = draw_fn(book, ORACLE_YEARS, seed=ORACLE_SEED)
    oracle_total = oracle["losses"].sum(axis=1)
    oracle_true_capital = cc.required_capital(oracle_total, TARGET_SURVIVAL)

    per_method_survival = {}
    for s in range(SEEDS_PER_CONFIG):
        historical = draw_fn(book, HISTORICAL_YEARS, seed=SEED_BASE + s)
        scored = run_trial(book, oracle_total, oracle_true_capital, historical["losses"])
        for name, row in scored.items():
            per_method_survival.setdefault(name, []).append(row["achieved_survival_probability"])

    return dict(oracle_true_capital=oracle_true_capital,
                methods={name: float(np.mean(vals)) for name, vals in per_method_survival.items()})


def main():
    book = build_book(N_PROPERTIES, seed=BOOK_SEED)
    results = {}

    for label, override in CONFIGS.items():
        print(f"\n=== {label} ===", flush=True)
        draw_fn = lambda b, ny, seed, override=override: sample_true_losses(
            b, ny, params=override, seed=seed)
        summary = summarize(book, override, draw_fn)
        results[label] = summary
        for name, v in summary["methods"].items():
            print(f"    {name:14s} achieved_survival={v:.4f}", flush=True)

    print("\n=== non-stationary: p_sys drifts 1/30 -> 1/5 across history, "
          "oracle at 1/5 (future) ===", flush=True)
    draw_fn = lambda b, ny, seed: sample_true_losses_drifting(
        b, ny, p_start=1 / 30, p_end=1 / 5, seed=seed)
    summary = summarize(book, dict(p_systemic="drift 1/30->1/5"), draw_fn)
    results["non-stationary (p_sys drift 1/30->1/5)"] = summary
    for name, v in summary["methods"].items():
        print(f"    {name:14s} achieved_survival={v:.4f}", flush=True)

    with open("results_phase1_param_sweep.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote results_phase1_param_sweep.json", flush=True)


if __name__ == "__main__":
    main()
