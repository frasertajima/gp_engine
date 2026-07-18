# Data source

**File:** `nure_multistate_az_ca_id_mt_nv_nm_ut_or.csv` (25 MB, 54,157 records, 65 columns)

**Origin:** USGS ScienceBase item *"Reanalysis of Selected Archived NURE-HSSR Sediment and Soil
Samples from Arizona, California, Idaho, Montana, Nevada, New Mexico, and Utah"*
(DOI: [10.5066/F7765DHF](https://doi.org/10.5066/F7765DHF), ScienceBase item
[5a0b3136e4b09af898cb6f56](https://www.sciencebase.gov/catalog/item/5a0b3136e4b09af898cb6f56)),
downloaded 2026-07-18 directly from ScienceBase's file endpoint. Public domain, no registration.

Same "reanalysis" program `mining_gpc_lab`'s `nevada_nure_raw.csv` came from (that file is the
Nevada-only subset of essentially this same underlying NURE-HSSR sample archive) — a 2015-onward
USGS/Rio Tinto Exploration technical assistance project that pulled ~60,000 archived NURE-HSSR
sample splits from the USGS National Geochemical Sample Archive and reanalyzed them via ALS
Global's ultra-trace 4-acid-digestion ICP-MS method (ALS ME-MS61L), 51 elements: Ag, Al, As, Ba,
Be, Bi, Ca, Cd, Ce, Co, Cr, Cs, Cu, Fe, Ga, Ge, Hf, In, K, La, Li, Mg, Mn, **Mo**, Na, Nb, Ni, P, Pb,
Rb, **Re**, S, Sb, Sc, Se, Sn, Sr, Ta, Te, Th, Ti, Tl, U, V, W, Y, Zn, Zr, plus Au, Pt, Pd. Same QC
protocol (blind SRMs/blanks/duplicates every 36 samples) as the Nevada file.

**State breakdown** (`State` column):

| State | n |
|---|---|
| NV | 13,828 |
| MT | 11,512 |
| ID | 7,766 |
| **AZ** | **7,633** |
| UT | 5,258 |
| NM | 3,487 |
| OR | 2,020 |
| CA | 644 |

**Why Arizona for this lab**: the classic US porphyry copper province — Morenci, Bagdad, Ray,
Miami-Globe, Safford, Resolution/Superior, Sierrita/Twin Buttes, Mission, Silver Bell are all
Arizona porphyry Cu(-Mo) deposits. 7,633 AZ samples is comparable in scale to `mining_gpc_lab`'s
4,106-sample Carlin Trend subset.

**Sanity check already run (2026-07-18)**: top-20 highest-Cu_ppm AZ samples cluster in the TUCSON
quadrangle (32.4-32.7°N, -111.4 to -111.1°W — right at Sierrita/Twin Buttes/Mission) and the MESA
quadrangle (33.4°N, -110.8°W — at Superior/Resolution/Miami-Globe) — the real known porphyry
districts, not a random scatter. Same kind of built-in geographic validation the Carlin Trend
bounding box had for gold.

**Key AZ stats** (raw ppm, not log): Cu_ppm mean 80.1, p95 133.5, max 19,000 (1.9%); Mo_ppm mean
2.67, p95 4.47, max 2,540 ppm; Re_ppm range -0.002 to 0.303 (negative = below detection, same
NURE convention as the gold data — needs the same `> 0` filter before log-transforming); Au_sq_ppm
range -0.0004 to 12.55 (many porphyry Cu deposits in this belt are Cu-Au, not just Cu-Mo).

**Bonus not yet used**: this single file also covers NV/UT/NM/MT, all of which host real porphyry
Cu districts of their own (Yerington NV, Bingham Canyon UT, Chino/Tyrone NM, Butte MT) — a second or
third porphyry-Cu-vertical lab could reuse this exact file with a different state filter, no new
data hunting needed.
