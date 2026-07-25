# Research note: are insured natural-catastrophe losses trending structurally upward?

**Claim being tested (from LAB_PLAN.md):** "Climate-linked insured losses are trending up
structurally, not just cyclically... climate trend is making the tail fatter every year."

**Verdict: PARTIALLY VERIFIED — the raw trend is real and well-documented, but the
dominant driver is exposure growth (more property built in harm's way), not a climate
signal alone. Wildfire and North American secondary perils are the clearest case where a
genuine climate-driven component (not just exposure) is explicitly named by a primary
source. LAB_PLAN.md's framing should be tightened to this more precise, defensible claim
rather than the blanket "climate trend is making the tail fatter" statement.**

---

## Source 1: NOAA NCEI / Climate Central — "U.S. Billion-Dollar Weather and Climate Disasters"

- Publisher: NOAA National Centers for Environmental Information (data), now maintained by
  Climate Central as of 2025-07-28.
- URL: https://www.ncei.noaa.gov/access/billions/ (dataset home); dashboard content is
  JS-rendered and did not yield verbatim quotable text via fetch — the figures below come
  from search-result summaries of the same dataset, corroborated by a second source below.
  Treat as a secondary citation of a primary dataset, not a verbatim primary quote.
- Accessed: 2026-07-23.

Reported figures (via search synthesis, not independently verified verbatim from the
dataset page itself):
- 403 billion-dollar disasters since 1980, damage totaling more than $2.9 trillion.
- Average annual count grew from ~3 events/year in the 1980s to ~20 events/year in the last
  decade.
- 2024 total: $182.7 billion. 2015-2024 total: >$1.4 trillion.

**Caveat on this source:** raw (non-normalized) dollar totals conflate three things —
more/worse weather, more property in harm's way, and inflation. The dataset itself does not,
in the material fetched here, isolate the climate-driven share. See Source 3.

## Source 2: North Carolina Institute for Climate Studies (NCICS), "Billion-Dollar Disasters Are Happening More Often"

- URL: https://ncics.org/cics-news/billion-dollar-disasters-are-happening-more-often/
- Accessed: 2026-07-23.

Verbatim: "the number of events has generally been increasing over the last two decades,"
citing 323 events 1980-2021 exceeding $1B each, cumulative >$2.195 trillion inflation-
adjusted. Verbatim: "Climate change is playing a role in the increasing frequency of some
types of extreme weather that lead to billion-dollar disasters." No decade-by-decade
breakdown or exposure-vs-climate attribution split was present in the fetched content.

## Source 3 (the important nuance): Swiss Re Institute, sigma natural catastrophe loss trend reporting

- URL: https://www.swissre.com/press-release/Wildfires-storms-floods-contribute-to-record-92-of-global-insured-losses-in-2025-says-Swiss-Re-Institute/7b39b1a5-b878-4a55-a5ff-bf5aa561a675
- Publisher: Swiss Re Institute (sigma research), a primary reinsurance-industry source —
  directly relevant since Swiss Re is exactly the kind of institution climate_cat_lab is
  modeling.
- Accessed: 2026-07-23.

Verbatim: "long-term global insurance losses from natural catastrophes continuing to follow
the 5–7% annual growth rate."

Verbatim (the key nuance): **"between 1970 and 2025, exposure growth explains more than 80%
of the long-term global increase in global weather-related insured losses."**

Verbatim (where a real climate signal is explicitly named, beyond exposure): "in some cases,
exposure alone no longer explains the speed of loss growth with hazard intensification and
evolving vulnerability becoming increasingly material in certain regions and perils." And,
specifically for North America: "growth is driven mainly by wildfire and SCS [severe
convective storms], with wildfire insured losses growing at an annual rate of 14%," attributed
partly to "the lengthening of fire seasons and long-term changes in temperature and
precipitation patterns."

## Source 4: the normalized-loss literature (Pielke, Weinkle et al.) — the strongest counter-nuance

- Found via search, not independently fetched verbatim (Substack/PNAS/AMS paywall/format
  limits in this session) — flagged as **secondary summary, not a direct quote**, weight
  accordingly.
- The normalization literature (adjusting historical losses for population/wealth growth to
  ask "would this event cost the same today") is contested: one line of work (Weinkle et al.,
  NOAA/AOML-affiliated) finds normalized US hurricane damage roughly flat over the 20th
  century; a competing analysis reportedly finds a statistically significant +0.6%/year
  increase in normalized tropical-cyclone damage even after normalization. Both exist in the
  literature; this is a live, unresolved academic disagreement, not a settled fact either way.

## Conclusion for LAB_PLAN.md's framing

The defensible claim, backed by a primary reinsurance-industry source (Swiss Re) rather than
an assumption: **insured cat losses are rising at ~5-7%/year, but >80% of that is exposure
growth, not climate change** — except in specific perils/regions (wildfire, North American
secondary perils) where Swiss Re itself now says exposure growth alone no longer explains the
pace, and names a real climate-linked mechanism (longer fire seasons, changing precipitation
patterns). The broader "climate change is uniformly making all tail risk fatter every year" is
NOT supported by the primary source fetched here, and the normalized-loss literature is
actively contested on this exact question for tropical cyclones.

**Recommendation:** LAB_PLAN.md's "why now" section should be edited to (a) cite the 5-7%/year
figure and the >80%-exposure-growth caveat rather than asserting an unqualified climate trend,
and (b) narrow the "climate is making the tail fatter" claim to wildfire/North-American
secondary perils specifically, where Swiss Re's own language supports a genuine (if partial)
climate-driven component — which, usefully, is also the peril climate_cat_lab's regime-shock
mechanism (drought/heat correlating a wildfire season) is modeling most directly.
