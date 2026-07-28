# Claim 5: is there a real reliability-standard convention analogous to NERC's LOLE?

**Status: VERIFIED** — a real, sourced, concrete industry convention exists, playing the same role
`grid_reserve_lab`'s 0.1-days/year LOLE target did.

## Firm Yield — the real, standard technical quantity

**"Firm Yield"** is the standard water-supply-planning term: the simulated maximum annual average
withdrawal rate a reservoir system can sustain every day **during a drought** — i.e. exactly the
quantity `hydro_reserve_lab`'s method ladder would need each method to compute, the direct water-
sector analogue of `grid_reserve_lab`'s "reserve requirement (MW)."

## A real, sourced reliability standard, from a real utility

**Seattle's water supply system is documented as meeting a 98% reliability standard, defined
concretely as "1 shortfall allowed to occur in a 50-year period of record."** This is a real,
specific, checkable number from a real utility — not an invented placeholder — and gives this lab
a genuine target-reliability convention to size against, the same role NERC's "1 day in 10 years"
LOLE standard played for `grid_reserve_lab`. (Caveat, stated honestly: this is one utility's stated
standard, not yet confirmed as a nationwide or Colorado-River-Basin-specific convention the way
NERC's LOLE target was confirmed across six independent US grid regions — a real difference in how
broadly this specific number generalizes, worth checking further before treating it as *the*
Colorado River Basin's own target rather than an illustrative comparable.)

## Real professional guidance

The **American Water Works Association (AWWA) M60 manual, "Drought Preparedness and Response"**
(2nd edition) is confirmed as the real, current, professional-association guidance document for
water-utility drought planning — the water-sector analogue of NERC's own standards documents in
`grid_reserve_lab`'s domain. Worth pulling a copy/summary of its actual reliability-planning
guidance in Phase 0, rather than relying solely on Seattle's single illustrative figure.

## What this gives Phase 0

A real, named quantity to compute (**Firm Yield**) and at least one real, sourced reliability
target to size against (**98% / 1-in-50-year**, Seattle) — enough to build a method ladder that
computes each method's implied firm yield and scores it against a real reliability target, mirroring
`grid_reserve_lab`'s reserve-sizing-vs-LOLE-target structure directly, rather than inventing an
artificial target the way a less-sourced lab might have had to.
