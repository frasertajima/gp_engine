"""Capital/retention sizing from Monte Carlo scenarios -- the Rockafellar-
Uryasev CVaR/TVaR machinery cvar_gp_lab/cvar_lp.py uses for a portfolio-
weight decision, reformulated here for climate_cat_lab's single-number
capital-sizing decision. For ONE asset (total book loss, no weights to
optimize), the Rockafellar-Uryasev minimization has a closed form -- the
optimal threshold variable t equals VaR at the target confidence level --
so this module computes the quantile directly rather than invoking a
general LP solver (unlike cvar_lp.py's genuinely multi-asset weight
problem, which needs one). Same underlying quantity (99.5% 1-year VaR/TVaR,
the Solvency II SCR convention -- research/01_solvency_ii_correlation.md),
just without machinery this simpler problem doesn't need.
"""

import numpy as np


def required_capital(scenario_total_losses, target_survival=0.995):
    """VaR at target_survival -- the capital level such that
    P(total loss <= capital) = target_survival under the model's own
    scenario distribution. This is what LAB_PLAN.md's "decision" is: how
    much capital (or reinsurance retention) to hold."""
    return float(np.quantile(scenario_total_losses, target_survival))


def cvar_at_capital(scenario_total_losses, capital):
    """Expected shortfall beyond `capital` -- the average dollar loss, in
    years where losses exceed the chosen capital level (zero if none do)."""
    excess = scenario_total_losses[scenario_total_losses > capital] - capital
    return float(excess.mean()) if len(excess) else 0.0


def survival_probability(total_losses, capital):
    """Fraction of years (from any sample, model or oracle) where total
    loss <= capital -- the ACHIEVED survival probability, to compare
    against a method's target."""
    return float(np.mean(total_losses <= capital))


def expected_shortfall(total_losses, capital):
    """Same computation as cvar_at_capital, named for oracle-scoring
    context: dollar expected annual shortfall beyond `capital`, evaluated
    against the ground-truth oracle sample rather than a model's own
    scenarios."""
    return cvar_at_capital(total_losses, capital)
