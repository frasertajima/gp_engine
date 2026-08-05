# Alternative hardware options: cheaper batteries and balcony solar (2026-08-04)

Done to ground the Scenario Builder's hardware catalog in real, current, sourced figures rather than
inventing illustrative numbers for options Fraser specifically asked about.

## Anker SOLIX (a real, cheaper battery alternative to Tesla Powerwall)

**Real 2026 pricing** (Anker's own published guide, cross-checked against independent reviews):
home batteries in 2026 run **$700-$1,300 USD per kWh**; a standard 10-13.5 kWh setup costs
**$10,000-$16,000 USD fully installed**. For comparison, Tesla Powerwall 3 lands at
**$850-$1,220 USD per kWh** installed (~$998/kWh headline figure, ~13% cheaper than the
EnergySage-marketplace average). **At the low end, Anker SOLIX genuinely is cheaper than
Powerwall** ($700 vs. $850-998/kWh); at the high end the two ranges converge — "cheaper" is real
but conditional on the specific configuration, not a blanket statement.

**Currency note**: these figures are USD, unlike this lab's own BC Hydro/CAD-denominated numbers
(`research/05...md`). The Scenario Builder keeps hardware options tagged by source currency and
lets the user apply their own exchange rate, rather than silently mixing currencies.

## Balcony/plug-in solar (Steckersolar/Balkonkraftwerk)

**Germany** (the most mature real market): legal output capped at **800W** (raised from 600W in a
May 2024 regulatory change). Real cost: **€400-€800** to buy and install. Real, named city
subsidies: **Berlin and Munich up to €500**, Hamburg up to €500 for combined heating+solar —
stacking a city grant with the VAT exemption can cut effective cost by €300-600. Real payback:
**3-5 years unsubsidized, 1.5-2.5 years with a city grant**, at Germany's real ~€0.32/kWh
residential rate — savings of **~€150-280/year** for an 800W south-facing system.

**United States**: systems typically 400-1,200W, **$350-700 USD for a complete 800W kit**
(microinverter + mounting). No dedicated federal balcony-solar subsidy; whether the general 30%
federal ITC applies depends on installation permanency and IRS interpretation (not resolved here,
matches this lab's own posture of not claiming a US credit applies without confirming it — see
`research/05...md`'s correction). Regulatory legalization is actively in progress state-by-state
(Utah first, March 2025; Virginia, March 2026) — not yet universal.

**A real, unconfirmed gap for Fraser's own jurisdiction**: no source was checked this pass for
whether grid-tied balcony/plug-in solar is legal or utility-interconnection-approved in British
Columbia specifically. The Scenario Builder includes balcony solar as a real, costed option (using
the German/US figures above as an illustrative cost anchor) but does **not** claim it is legal or
BC-Hydro-interconnection-approved in Vancouver — flagged explicitly in the notebook, not assumed.

## Net effect on the Scenario Builder

Both options are added to the hardware catalog as real, sourced, currency-tagged presets alongside
the existing Tesla-Powerwall-class (CAD) and generic-solar (CAD) options from `research/05...md` —
the user can pick any preset or fully override every field with a custom option, per Fraser's own
request that the tool stay generically useful even if only some features are used.
