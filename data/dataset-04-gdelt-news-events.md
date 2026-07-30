# Source 4: GDELT News Events — Energy-Market Enrichment, Nov 8–14, 2021

Built from the **GDELT GKG 1.0** daily files (`YYYYMMDD.gkg.csv`) for the week, filtered to
energy-relevant documents and linked to the **CAMEO Event** files (the raw CAMEO
event files themselves are not in the repo; the link table below carries the
relevant event attributes denormalized).

## Files In This Repo (`04-gdelt-news-events/`)

| File | Description |
|---|---|
| `gkg_energy_enriched.zip` | Table 1, full week (49,298 rows, 26 MB unzipped) |
| `gkg_energy_enriched_sample100.csv` | Table 1, first 100 rows |
| `gkg_energy_event_link.zip` | Table 2, full week (224,424 rows, 278 MB unzipped) |
| `gkg_energy_event_link_sample100.csv` | Table 2, first 100 rows |

- GKG records scanned: **430,918**
- Energy-relevant records: **49,298** (11.4%)
- Referenced CAMEO events: **105,910** — **102,415 (96.7%)** matched in the event files
- Document × event links: **224,424**

Both files are **tab-delimited, UTF-8, with a header row**.

---

## Table 1 — `gkg_energy_enriched.csv`  (one row per energy news document)

| Column | Meaning |
|---|---|
| DATE | Publication date (YYYYMMDD) |
| SOURCE | Source domain(s) |
| SOURCEURL | Article URL |
| NUMARTS | Article count for the record (salience / buzz weight) |
| ENERGY_SECTORS | `|`-separated sub-sectors (OIL, NATURAL_GAS, COAL, NUCLEAR, SOLAR, WIND, HYDRO, BIOFUEL, POWER_GRID, PIPELINES_INFRA, PRICES_SUBSIDIES, RENEWABLE_GENERAL, CARBON_TRANSITION, ENERGY_GENERAL) |
| ENERGY_THEMES | `|`-separated raw GDELT/World-Bank theme codes that triggered the match |
| TONE_AVG | GDELT document tone (−100…+100); bullish/bearish proxy |
| TONE_POS / TONE_NEG | Positive / negative word density |
| TONE_POLARITY | Emotionally charged language density |
| TONE_ACTIVITY | Activity-reference density |
| TONE_SELFREF | Self/group-reference density |
| ENERGY_TICKERS | `|`-separated equity tickers (precise exact/word-boundary match) |
| ENERGY_ENTITIES | `|`-separated market-moving non-equity entities (OPEC, IEA, EIA, Gazprom, Aramco, Rosneft, PDVSA…) |
| COUNTRY_CODES | `|`-separated FIPS country codes mentioned |
| TOP_LOCATIONS | up to 3 `Name|CC|Lat|Long`, ` ;; `-separated |
| PERSONS | `;`-separated persons (GDELT extraction) |
| CAMEO_EVENT_IDS | `,`-separated GlobalEventIDs → join key to the event files / Table 2 |

## Table 2 — `gkg_energy_event_link.csv`  (bridge: doc ⋈ CAMEO event)

| Column | Meaning |
|---|---|
| GlobalEventID | CAMEO event id (FK to event files) |
| DATE | News document date |
| EventRootCode | CAMEO root action code |
| QuadClass / QuadClassName | 1 VerbalCoop, 2 MaterialCoop, 3 VerbalConflict, 4 MaterialConflict |
| GoldsteinScale | −10…+10 conflict/cooperation intensity |
| Event_AvgTone | Event-level tone from the event record |
| ActionGeo_FullName / ActionGeo_CC | Where the event took place |
| Energy_Sectors | Sectors of the linking news document |
| Doc_Tone | Document tone of the linking news document |
| Doc_Tickers | Tickers of the linking news document |
| SourceURL | Linking news document URL |

---

## Notes & caveats
- **Join keys:** Table 2 joins to Table 1 on `(SourceURL, DATE)` — verified
  complete (all 22,881 distinct link URLs match a Table 1 row). `SOURCEURL`
  can contain multiple `<UDIV>`-separated URLs (5,630 rows); split before
  URL-level dedup.
- **Date-only granularity:** GKG 1.0 provides a publication *date*, not a
  time. Replaying "by publication time" requires a documented intra-day time
  assignment (or a switch to the 15-min GKG 2.1 feed).
- **Tickers are US/LSE-style** (e.g. `SHEL`, `XOM`, `NG.L`), not DEBS symbols;
  resolve via `table1_equities_metadata.csv.yahoo_ticker` (~half match
  directly) plus a rename crosswalk (e.g. `SHEL` → `RDSA.NL`, renamed Jan 2022).
  Only ~3.8% of documents carry ticker tags.
- **Tone is GDELT document-level tone**, not a finance-tuned sentiment model. It is a reasonable
  first-order bull/bear proxy; a FinBERT pass on titles would sharpen it.
- **Ticker precision** favored over recall: exact-name + collision-free word-boundary matching only,
  so arenas ("Xcel Energy Center"), universities ("Old Dominion"), and people ("Sherwin Williams")
  are deliberately *not* tagged. Some real mentions are therefore missed.
- **Entity variants** are not yet canonicalized (e.g., "energy information administration" vs
  "u s energy information administration" are separate strings). Trivial to fold.
- **Not in GKG 1.0** (would require GKG 2.1, the 15-min v2 feed): numeric **AMOUNTS**
  (barrels, MW, prices, %), **GCAM** 2,000+ emotion/theme dimensions, quotations, and
  character-offset entity positions. These are the highest-value additions for a trading terminal.


