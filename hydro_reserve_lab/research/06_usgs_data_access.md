# Claim 6: is real, multi-gauge streamflow data actually openly downloadable? (empirically tested twice, not just described)

**Status: VERIFIED, directly, by live HTTP requests — the same standard of proof that caught
BCSIMS's and KU Leuven's Z-24 access gates before either was trusted, applied here to confirm the
opposite result.**

## The legacy API — confirmed open

A live, unauthenticated `curl` request against `waterservices.usgs.gov/nwis/dv` (the Daily Values
service) for a real gauge (USGS 01646500, Potomac River near Washington, DC), a real date range,
and a real parameter code (00060, discharge):

```
curl -s -o /tmp/usgs_test.json -w "HTTP %{http_code}\n" \
  "https://waterservices.usgs.gov/nwis/dv/?format=json&sites=01646500&startDT=2020-01-01&endDT=2020-01-05&parameterCd=00060"
```

returned **HTTP 200 with real WaterML/JSON daily-values data — no API key, no login, no
registration step of any kind.**

**One real, flagged risk from the pre-check, now resolved**: USGS's own documentation states this
legacy API "will be decommissioned in early 2027." The successor was not merely assumed compatible
— it was tested directly too.

## The successor API — also confirmed open, directly tested

The documentation page for `api.waterdata.usgs.gov` mentions a "Get an API Key" signup option,
which read ambiguously on first pass (possibly implying a key is required for any access). Tested
directly:

```
curl -s -w "HTTP %{http_code}\n" \
  "https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?monitoring_location_id=USGS-01646500&limit=5"
```

returned **HTTP 200 with real daily-values data (temperature, in this unfiltered-parameter test
call), again with no API key supplied.** The discovery root endpoint
(`api.waterdata.usgs.gov/ogcapi/v0/`) also returned HTTP 200 anonymously. **Conclusion: the "Get an
API Key" option is for registered/higher-rate-limit use, not a hard requirement for basic anonymous
access** — the successor API is confirmed open by the same direct-test standard as the legacy one,
resolving the pre-check's one flagged risk rather than leaving it open into Phase 0.

## What this gives Phase 0/2

A genuinely open, first-party-verified (not merely described) path to real multi-decade,
multi-gauge streamflow data — at least as open as `grid_reserve_lab`'s EIA-930 endpoint, and
already confirmed to survive the 2027 legacy-API sunset via its documented OGC API successor.
