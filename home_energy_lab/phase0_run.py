"""Phase 0 -- does this real 10-year Vancouver weather record actually show:
(1) a real, physically sensible solar generation and heating-load seasonal
    shape (sanity checks on solar_model.py/load_model.py),
(2) a real winter low-solar/high-heating-demand co-occurrence (the "stress
    regime" LAB_PLAN.md's hypothesis targets) that's genuinely correlated,
    not just two marginal seasonal trends coinciding by construction, and
(3) real multi-day persistence (weather systems lasting days), not an
    i.i.d. day-to-day draw?
Same "does the mechanism actually exist in this specific real data"
discipline as every prior lab's Phase 0 -- nothing assumed from research.
"""

import json

import numpy as np
import pandas as pd

from data_weather import load_hourly
from solar_model import pv_output_kw
from load_model import hourly_load_kw

SOLAR_NAMEPLATE_KW = 8.0
LOW_SOLAR_PCTL = 25.0
HIGH_HEAT_PCTL = 75.0


def main():
    df = load_hourly(2016, 2025)
    solar_kw = pv_output_kw(df["shortwave_radiation"].values, nameplate_kw=SOLAR_NAMEPLATE_KW)
    load_kw = hourly_load_kw(df["temperature_2m"].values, df.index)

    daily = pd.DataFrame({
        "solar_kwh": solar_kw, "load_kwh": load_kw, "temp": df["temperature_2m"].values,
    }, index=df.index).resample("D").agg({"solar_kwh": "sum", "load_kwh": "sum", "temp": "mean"})
    daily["heating_degree"] = np.maximum(0.0, 18.0 - daily["temp"])
    n_days = len(daily)

    # --- Check 1: real seasonal shape (already eyeballed in solar_model.py/load_model.py
    #     __main__ blocks; recorded here numerically) ---
    monthly_solar = daily.groupby(daily.index.month)["solar_kwh"].mean()
    monthly_load = daily.groupby(daily.index.month)["load_kwh"].mean()
    summer_solar = monthly_solar.loc[[6, 7, 8]].mean()
    winter_solar = monthly_solar.loc[[12, 1, 2]].mean()
    winter_load = monthly_load.loc[[12, 1, 2]].mean()
    summer_load = monthly_load.loc[[6, 7, 8]].mean()

    # --- Check 2: does low-solar co-occur with high-heating more than independence predicts? ---
    low_solar_thresh = np.percentile(daily["solar_kwh"], LOW_SOLAR_PCTL)
    high_heat_thresh = np.percentile(daily["heating_degree"], HIGH_HEAT_PCTL)
    is_low_solar = daily["solar_kwh"] <= low_solar_thresh
    is_high_heat = daily["heating_degree"] >= high_heat_thresh

    p_low_solar = float(is_low_solar.mean())
    p_high_heat = float(is_high_heat.mean())
    p_both = float((is_low_solar & is_high_heat).mean())
    p_both_independence = p_low_solar * p_high_heat
    excess_ratio = p_both / p_both_independence if p_both_independence > 0 else float("nan")

    # --- Check 3: real multi-day persistence of the joint stress state ---
    is_stress = (is_low_solar & is_high_heat).values.astype(int)
    p_stress_tomorrow_given_stress_today = float(
        is_stress[1:][is_stress[:-1] == 1].mean()) if is_stress[:-1].sum() > 0 else float("nan")
    p_stress_marginal = float(is_stress.mean())
    persistence_ratio = (p_stress_tomorrow_given_stress_today / p_stress_marginal
                         if p_stress_marginal > 0 else float("nan"))

    results = {
        "n_days": int(n_days),
        "solar_nameplate_kw": SOLAR_NAMEPLATE_KW,
        "annual_solar_kwh": float(daily["solar_kwh"].sum() / 10),
        "annual_load_kwh": float(daily["load_kwh"].sum() / 10),
        "seasonal_shape": {
            "summer_solar_kwh_day": float(summer_solar), "winter_solar_kwh_day": float(winter_solar),
            "winter_load_kwh_day": float(winter_load), "summer_load_kwh_day": float(summer_load),
        },
        "stress_regime_check": {
            "low_solar_threshold_kwh_day": float(low_solar_thresh),
            "high_heat_threshold_degree_days": float(high_heat_thresh),
            "p_low_solar": p_low_solar, "p_high_heat": p_high_heat,
            "p_both_observed": p_both, "p_both_if_independent": p_both_independence,
            "excess_ratio_vs_independence": excess_ratio,
        },
        "persistence_check": {
            "p_stress_marginal": p_stress_marginal,
            "p_stress_tomorrow_given_stress_today": p_stress_tomorrow_given_stress_today,
            "persistence_ratio": persistence_ratio,
        },
    }

    with open("results_phase0.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"{n_days} days, {SOLAR_NAMEPLATE_KW}kW solar system")
    print(f"annual solar generation: {results['annual_solar_kwh']:,.0f} kWh/yr "
          f"({results['annual_solar_kwh']/SOLAR_NAMEPLATE_KW:,.0f} kWh/yr/kW)")
    print(f"annual load: {results['annual_load_kwh']:,.0f} kWh/yr")
    print(f"\nSeasonal shape: summer solar {summer_solar:.1f} kWh/day vs winter {winter_solar:.1f} "
          f"kWh/day ({summer_solar/winter_solar:.1f}x)")
    print(f"                winter load {winter_load:.1f} kWh/day vs summer {summer_load:.1f} "
          f"kWh/day ({winter_load/summer_load:.1f}x)")
    print(f"\nStress-regime co-occurrence: P(low-solar)={p_low_solar:.3f}  P(high-heat)={p_high_heat:.3f}")
    print(f"  observed P(both)={p_both:.4f} vs independence-implied {p_both_independence:.4f} "
          f"-> {excess_ratio:.2f}x excess")
    print(f"\nPersistence: P(stress tomorrow | stress today)={p_stress_tomorrow_given_stress_today:.3f} "
          f"vs marginal P(stress)={p_stress_marginal:.3f} -> {persistence_ratio:.2f}x")
    print("\nwrote results_phase0.json")


if __name__ == "__main__":
    main()
