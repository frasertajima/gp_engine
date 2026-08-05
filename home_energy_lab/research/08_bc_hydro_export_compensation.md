# BC Hydro's real export compensation for self-generation (2026-08-05)

Prompted by `CODE_REVIEW.md` H1: this lab simulated `grid_export_kwh` in three modules and monetized
it **nowhere**. The 8kW reference system exports ~2,700 kWh/yr, which was being valued at $0. The
strings *net metering*, *net-metering*, *feed-in* and *buyback* appeared zero times across all
previous research files, both notebooks, and all four RESULTS docs — the single largest unexamined
domain assumption in the lab.

## The real finding: the program changed on 2026-07-01, five weeks before this check

**This is why the rate had to be looked up rather than recalled.** An assumed figure would have been
the *old* program's, and the old program is closed.

| | Old | Current |
|---|---|---|
| Rate schedule | **RS 1289** (Net Metering Service Rate) | **RS 2289** (Self-Generation Service Rate) |
| Status | closed to new customers 2026-07-01 | effective 2026-07-01 |
| Compensation | kWh **banked** as credits, offsetting current and future billed consumption, settled annually | flat **monetary** credit |
| Export rate | (implicit — offset at the retail rate you would otherwise pay) | **$0.10/kWh, flat** |
| Settlement | annual anniversary | **every billing cycle** |

Primary sources, both fetched live 2026-08-05 from bchydro.com:
- [Customer generation service rates updates](https://www.bchydro.com/toolbar/about/strategies-plans-regulatory/rate-design/self-generation-rate-updates.html)
  — RS 2289, effective July 1 2026, "10 cents per kWh", monetary compensation "each billing cycle".
- [Net metering / self-generation](https://www.bchydro.com/accounts-billing/electrical-connections/net-metering.html)
  — worked example: 50 kWh net export in a billing cycle → **$5.00** monetary credit (50 × $0.10).

## Three real modeling constraints this imposes

1. **Flat 10¢, not the retail rate.** Export is compensated *below* the Step 1 retail rate
   (10.97¢) and well below Step 2 (14.08¢) and the peak TOD rate (15.97¢). Exporting is strictly
   worse than self-consuming — which is exactly the economic asymmetry a battery is supposed to
   exploit, and it is now priced rather than ignored.
2. **Credits cover Energy Charges only.** BC Hydro states plainly: *"Self-generation bill credits
   cover Energy Charges only. You'll still need to pay any other charges that are part of your bill,
   such as the Basic Charge."* So the credit is capped at the month's energy charge — a large
   exporter cannot drive the bill negative, or below the $6.17/month basic charge.
3. **Per-billing-cycle settlement, not annual.** Surplus in a high-export summer month cannot be
   carried forward to offset a high-consumption winter month. This matters a lot for an oversized
   system in a heating-dominated climate like Vancouver's, and it is the main reason the old RS 1289
   annual-banking arrangement was more generous than RS 2289 for exactly this load shape.

## Which rate this lab should use, and why

**RS 2289.** `capacity_sizing.py` applies BC Hydro's real solar rebate, and BC Hydro's own transition
rule makes that determinative: *"Customers who accepted BC Hydro's solar rebate were automatically
transitioned to Rate Schedule 2289 as of July 1, 2026."* A household taking the rebate this lab
already models **cannot** be on the legacy rate. The two assumptions are consistent only under
RS 2289.

## Honest unknowns

- The 10¢ figure is BCUC-approved and current as of 2026-08-05; it is a set price, not indexed, and
  a future BCUC decision could move it. `EXPORT_CREDIT_PER_KWH` is a module constant for that reason.
- Whether an unused monetary credit rolls forward to the next billing cycle when it exceeds that
  cycle's energy charge is **not stated** on either page. This lab takes the conservative reading
  (credit capped at the month's energy charge, remainder forfeited).

  **Correction (measured after this file was first written).** The initial draft of this section
  guessed that the cap "binds rarely" on Phase 3's grid. That was wrong, and the re-run measured it:

  | Solar kW | Export kWh/yr | Credit forfeited to the cap |
  |---|---|---|
  | 4 | 1,051 | $0/yr |
  | 6 | 2,476 | $43/yr |
  | 8 | 4,108 | $158/yr |
  | 12 | 7,651 | $448/yr |
  | 20 | 15,173 | **$1,117/yr** |

  The cap is not a marginal correction — beyond ~6kW it is the dominant term in the export
  economics, because a Vancouver summer month pairs peak export with a small energy charge and the
  surplus cannot be carried into winter. Uncapped, a 20kW array would run a **negative** annual bill
  (−$745/yr), which RS 2289 plainly does not permit. **This single unresolved rule is therefore the
  largest remaining uncertainty in Phase 3's sizing conclusion** and should be settled against the
  RS 2289 tariff sheet or a BC Hydro rep before any oversized-array recommendation is made.
- RS 2289's own full tariff sheet was not fetched; both figures above come from BC Hydro's customer-
  facing rate-change pages, which agree with each other and with a worked numeric example.
