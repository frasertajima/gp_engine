# Claim 1: EOV (chiefly temperature) causes bigger frequency shifts than typical early damage

**Status: VERIFIED**, against two primary/near-primary sources.

## Source A — Sohn, H. (2007), "Effects of environmental and operational variability on structural
health monitoring," *Phil. Trans. R. Soc. A*, 365, 539-560.

The canonical review paper for this exact problem. Confirmed via Semantic Scholar / ADS abstract
record (`ui.adsabs.harvard.edu/abs/2007RSPTA.365..539S`) and cross-referenced citations
(ResearchGate record 6549211). Core finding, paraphrased from the abstract record (full text not
directly fetched, but the abstract's framing is corroborated by every secondary citation found):
structures are subject to changing environmental and operational conditions, and these ambient
variations "can often mask subtle changes in the system's vibration signal caused by damage" —
i.e. the review's entire premise is that EOV effects are large enough, relative to typical damage
signatures, to be a first-order confound requiring dedicated "data normalization" methods, not a
second-order nuisance.

## Source B — Peeters, B. & De Roeck, G. (2001), "One-year monitoring of the Z24-Bridge:
environmental effects versus damage events," *Earthquake Engineering & Structural Dynamics*, 30(2),
149-171.

Direct empirical demonstration on a comparable bridge (Z-24, Switzerland, monitored ~1 year before
being artificially damaged as part of the same European SIMCES project that also produced the
BCSIMS-adjacent literature reviewed earlier this session). Confirmed finding, corroborated across
multiple secondary sources (Wiley abstract record, a 2022 topological-cointegration case study
built on the same dataset, and independent literature reviews on temperature effects in bridges):
**Z-24's bending-mode natural frequency showed a bilinear relationship with temperature** — frequency
increased with temperature above 0°C, and the opposite trend below 0°C (freezing changes the
effective boundary/material stiffness). The paper's stated core problem, paraphrased consistently
across every source that cites it: "when using vibration measurements as a tool for health
monitoring of bridges, the problem arises of separating abnormal changes from normal changes in the
dynamic behaviour, with normal changes caused by varying environmental conditions such as
humidity, wind and, most important, temperature" — and the temperature effect was "clearly visible"
in the data, large enough that removing it was a stated prerequisite for damage detection to work
at all on this bridge.

## Read for `shm_lab`

Both sources are about a **different bridge** (Z-24, not KW51) — this is directionally strong
support for the *general* EOV/temperature-confound phenomenon in bridge SHM, not proof that KW51
specifically exhibits the same bilinear temperature relationship. KW51's own temperature-frequency
relationship must be checked directly in Phase 0 once `trackedmodes.zip` is downloaded — treat this
claim as "well-established as a general SHM phenomenon," not yet as "confirmed for this specific
bridge and dataset."
