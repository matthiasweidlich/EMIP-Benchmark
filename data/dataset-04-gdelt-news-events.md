# Source 4: GDELT News Events — Energy-Market Enrichment, Nov 8–14, 2021

Two consecutive weeks of GDELT data, preprocessed into analysis-ready tables for an
energy-markets application. Everything derives from two GDELT 1.0 feeds:

- **Event export** files (`YYYYMMDD.export.CSV`) — CAMEO events, 58 columns.
- **GKG 1.0** daily files (`YYYYMMDD.gkg.csv`) — the Global Knowledge Graph: themes,
  tone, organizations, persons, locations, and event linkage per news document.

Each week exists at two levels:
- **Energy** = GKG documents filtered to energy-relevant themes (see classifier notes).
- **Unfiltered (all)** = every GKG document, with the energy tags retained as columns.

The unfiltered tables are **strict supersets** of the energy tables: filtering
`ENERGY_SECTORS <> ''` (document tables) or `Energy_Sectors <> ''` (bridges) reproduces
the energy version exactly. All files are **tab-delimited, UTF-8, with a header row**.

---

## File manifest

The following files are available as a single zip file `gdelt_gkg_energy_nov1-14_2021.zip` stored with GIT LFS as listed here https://github.com/matthiasweidlich/EMIP-Benchmark/blob/main/data/04-gdelt-news-events/.gitattributes .

| File | Level | Rows | Notes |
|---|---|---|---|
| `gdelt_20211101-07_merged.CSV` | events | 725,518 | Nov 1–7 CAMEO events, 58 cols |
| `gdelt_20211108-14_merged.CSV` | events | 777,481 | Nov 8–14 CAMEO events, 58 cols |
| `gkg_energy_enriched_nov1-7.csv` | energy doc | 51,364 | Nov 1–7 energy documents |
| `gkg_energy_enriched.csv` | energy doc | 49,298 | Nov 8–14 energy documents |
| `gkg_energy_event_link_nov1-7.csv` | energy bridge | 291,991 | Nov 1–7 doc×event |
| `gkg_energy_event_link.csv` | energy bridge | 224,424 | Nov 8–14 doc×event |
| `gkg_all_enriched_nov1-7.csv` (+`.gz`) | all doc | 430,664 | Nov 1–7, every document |
| `gkg_all_enriched_nov8-14.csv` (+`.gz`) | all doc | 430,918 | Nov 8–14, every document |
| `gkg_all_event_link_nov1-7.csv.gz` | all bridge | 1,857,813 | Nov 1–7, every doc×event |
| `gkg_all_event_link_nov8-14.csv.gz` | all bridge | 1,917,264 | Nov 8–14, every doc×event |

Per-week extraction stats:

| Week | GKG scanned | Energy docs | Referenced events | Matched in event file |
|---|---|---|---|---|
| Nov 1–7 | 430,664 | 51,364 (11.9%) | 110,653 | 107,106 (96.8%) |
| Nov 8–14 | 430,918 | 49,298 (11.4%) | 105,910 | 102,415 (96.7%) |

> Naming note: the Nov 8–14 **energy** files carry no week suffix (`…enriched.csv`,
> `…event_link.csv`); Nov 1–7 files use the `_nov1-7` suffix; unfiltered files use
> `_nov8-14` / `_nov1-7`. Both weeks now have all four tables (energy + unfiltered).

---

## Table A — energy document table
`gkg_energy_enriched.csv` (Nov 8–14) · `gkg_energy_enriched_nov1-7.csv` (Nov 1–7)
One row per energy-relevant news document.

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
| CAMEO_EVENT_IDS | `,`-separated GlobalEventIDs → join key to the event files / bridge |

## Table B — energy bridge (doc ⋈ CAMEO event)
`gkg_energy_event_link.csv` (Nov 8–14) · `gkg_energy_event_link_nov1-7.csv` (Nov 1–7)
One row per (energy document, matched event) link.

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

## Table C — unfiltered document table (superset of A)
`gkg_all_enriched_nov8-14.csv` (+`.gz`) · `gkg_all_enriched_nov1-7.csv` (+`.gz`). One row per GKG document (all topics).
Same as Table A **except**: no energy filter; `THEMES` holds the *full* theme list and
`ORGANIZATIONS`/`PERSONS` are the *full* extracted lists; energy tags are retained but
populated only on energy documents.

| Column | Meaning |
|---|---|
| DATE, SOURCE, SOURCEURL, NUMARTS | as Table A |
| THEMES | full `;`-separated theme list for the document (all topics) |
| THEME_COUNT | number of themes on the document |
| TONE_AVG … TONE_SELFREF | parsed 6-part GDELT tone vector (as Table A) |
| ORGANIZATIONS | full `;`-separated organization list (unfiltered) |
| PERSONS | full `;`-separated person list |
| COUNTRY_CODES | `|`-separated FIPS country codes |
| TOP_LOCATIONS | up to 3 `Name|CC|Lat|Long`, ` ;; `-separated |
| CAMEO_EVENT_IDS | `,`-separated GlobalEventIDs → join key |
| ENERGY_SECTORS / ENERGY_TICKERS / ENERGY_ENTITIES | energy tags; non-empty only on energy documents (49,298 for Nov 8–14; 51,364 for Nov 1–7) |

## Table D — unfiltered bridge (superset of B)
`gkg_all_event_link_nov8-14.csv.gz` · `gkg_all_event_link_nov1-7.csv.gz`. One row per
(any document, matched event) link. Identical columns to Table B.
- Nov 8–14: 1,917,264 links from 201,787 documents; 75,985 refs skipped as unmatched.
- Nov 1–7: 1,857,813 links from 200,420 documents; 74,592 refs skipped as unmatched.

Unmatched references cite `GlobalEventID`s outside the week's event files — GDELT
documents can reference events collected on other dates.

---

## Notes & caveats
- **Tone is GDELT document-level tone**, not a finance-tuned sentiment model. It is a reasonable
  first-order bull/bear proxy; a FinBERT pass on titles would sharpen it.
- **Energy theme classifier** was validated against substring false positives it explicitly drops:
  `POLITICAL_TURMOIL` (turm-OIL), `TAX_WORLDMAMMALS_DRILL` (a drill is a monkey),
  `TAX_WEAPONS_TEAR_GAS`, `TAX_FOODSTAPLES_OLIVE_OIL`, `WB_569_HYDROMET_SERVICES` (weather),
  `NATURAL_DISASTER_STRONG_WINDS` (weather).
- **Ticker precision** favored over recall: exact-name + collision-free word-boundary matching only,
  so arenas ("Xcel Energy Center"), universities ("Old Dominion"), and people ("Sherwin Williams")
  are deliberately *not* tagged. Some real mentions are therefore missed. `ENERGY_TICKERS` covers
  energy names only — a general all-sector ticker column would need a broader resolver
  (e.g., SEC EDGAR `company_tickers.json` + entity linking).
- **Entity variants** are not yet canonicalized (e.g., "energy information administration" vs
  "u s energy information administration" are separate strings). Trivial to fold.
- **Event files are keyed on collection date**, not event date. When stacking the two weeks into a
  time series, dedupe on `GlobalEventID` across files and, if you need true event-date alignment,
  filter on `SQLDATE`.
- **Not in GKG 1.0** (would require GKG 2.1, the 15-min v2 feed): numeric **AMOUNTS**
  (barrels, MW, prices, %), **GCAM** 2,000+ emotion/theme dimensions, quotations, and
  character-offset entity positions. These are the highest-value additions for a trading terminal.

## Known gaps / next steps
- Both weeks are now complete at both levels (energy + unfiltered, document + bridge).
- A deduped 14-day panel (both weeks stacked, proper date index, sector-level tone/conflict
  time series) is the natural input for the app's charts.
- Optional GKG 2.1 `AMOUNTS`/`GCAM` layer for quantitative signals.
