# Gold-Level Relational Schema

This document sketches a gold-level relational schema for EMIP. It is grounded in the source files under `data/` and is intended to be fillable from those files after bronze ingestion and silver-level parsing, cleaning, and normalization.

The schema deliberately excludes benchmark execution metadata and separate data-quality tables. Quality checks can still be part of validation, but they are not part of the integrated gold dataset.

## Design Principles

- Use the current `data/` directory as the contract for the schema.
- Keep raw file-specific quirks in bronze and silver layers.
- Make gold tables relational, joinable, and suitable for dashboards, materialized views, ETL validation, and feature generation.
- Preserve source identifiers needed for traceability, especially DEBS symbols, ISINs, GDELT URLs, and GDELT event IDs.
- Treat company metadata, sectors, exchanges, and instrument mappings as static dimensions for the default one-week benchmark run.

## Source Files

| Source Area | Files | Gold Use |
|---|---|---|
| DEBS instruments and metadata | `data/company-info/symbols_weekend.txt`, `equities_symbols.txt`, `indices_symbols.txt`, `sym_isin.txt`, `table1_equities_metadata.csv`, `table2_sector_by_exchange.csv`, `table3_unresolved_symbols.csv` | Instrument, exchange, company, sector, and mapping dimensions |
| DEBS tick stream | Current samples `data/company-info/day13.csv`, `day14.csv`; forthcoming DEBS samples in `data/` | High-volume market tick fact table and derived market windows |
| GDELT energy news | `data/gdelt/gkg_energy_enriched_sample100.csv`, `data/gdelt/gkg_energy_enriched.zip` | Energy-relevant news documents |
| GDELT event links | `data/gdelt/gkg_energy_event_link_sample100.csv`, `data/gdelt/gkg_energy_event_link.zip` | Document-to-event links and event-context features |
| Electricity prices | `data/electricy_prices/electricity_day_ahead_prices_2021-11-08_2021-11-14.csv` | Hourly regional energy price context |
| Weather observations | `data/weather/sensor_community_weather_western_europe_sample_100mb.csv` and generated weather files | Sensor-level environmental context |

The directory name `data/electricy_prices` is used as-is here, even though it appears to contain a spelling typo.

## Table Overview

| Table | Kind | Filled From | Purpose |
|---|---|---|---|
| `exchange` | Dimension | DEBS symbol suffixes and metadata files | Canonical trading venues represented in DEBS |
| `instrument` | Dimension | DEBS symbol lists, ISIN map, metadata, tick IDs | Canonical traded instruments, including equities and indices |
| `company` | Dimension | Resolved equity metadata | Company entities behind resolved equity instruments |
| `sector` | Dimension | Resolved equity metadata and sector summary | Normalized sector and industry labels |
| `instrument_company` | Bridge | Resolved equity metadata | Many-to-one mapping from instruments to companies |
| `company_sector` | Bridge | Resolved equity metadata | Company-to-sector classification |
| `market_tick` | Fact / Stream | DEBS tick CSV files | Cleaned tick events |
| `news_document` | Fact / History + Stream | GDELT energy enrichment file | Energy-relevant documents and document-level tone |
| `news_event_link` | Fact / Bridge | GDELT event-link file | Links news documents to CAMEO events |
| `news_ticker_mention` | Bridge | Split GDELT `ENERGY_TICKERS` / `Doc_Tickers` | Mentions linking news to instruments and companies |
| `electricity_price` | Fact / Context | Electricity price CSV | Hourly day-ahead electricity prices by bidding zone |
| `weather_observation` | Fact / Context | Sensor.Community weather CSVs | Temperature and humidity observations |
| `market_bar` | Derived Fact | `market_tick` | Windowed OHLCV-style market summaries |
| `market_feature` | Derived Fact | Market, news, electricity, weather tables | Feature rows for dashboards, alerts, and prediction |
| `prediction_label` | Derived Fact | `market_tick` or `market_bar` | Future-return labels for prediction workloads |

## Fillability From Current Sources

| Gold Table | Fillability | Notes |
|---|---|---|
| `exchange` | Directly fillable now | Derived from DEBS suffixes `FR`, `NL`, and `ETR`. |
| `instrument` | Directly fillable now | Use `symbols_weekend.txt` as the full instrument universe and enrich with `sym_isin.txt`, metadata, and observed tick fields. |
| `company` | Directly fillable now for resolved equities | Use `table1_equities_metadata.csv`; unresolved symbols remain only in `instrument`. |
| `sector` | Directly fillable now | Use non-empty `sector` and `industry` values from `table1_equities_metadata.csv`; `table2_sector_by_exchange.csv` is a validation summary. |
| `instrument_company` | Directly fillable now for resolved equities | Use `debs_symbol`, `yahoo_ticker`, `resolved_via`, and `isin_yf`. |
| `company_sector` | Directly fillable now for resolved equities with classifications | Use metadata rows with sector or industry values. |
| `market_tick` | Directly fillable from DEBS samples | Current weekend files provide the schema; forthcoming DEBS samples can be loaded with the same parser. |
| `news_document` | Fillable from current GDELT samples and archive | Load `gkg_energy_enriched_sample100.csv` for a small sample or unzip `gkg_energy_enriched.zip` for the full one-week slice. Both are tab-delimited with the same header. |
| `news_event_link` | Fillable from current GDELT samples and archive | Load `gkg_energy_event_link_sample100.csv` for a small sample or unzip `gkg_energy_event_link.zip` for the full one-week slice. Both are tab-delimited with the same header. |
| `news_ticker_mention` | Derived from current GDELT samples and archive | Split ticker lists and resolve to `instrument` where possible. |
| `electricity_price` | Directly fillable now | CSV already uses the target source schema. |
| `weather_observation` | Directly fillable now | CSV already uses the target source schema. |
| `market_bar`, `market_feature`, `prediction_label` | Derived after source loading | Computed from gold source facts and dimensions. |

## Detailed Tables

### `exchange`

One row per trading venue or exchange code represented in DEBS.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `exchange_id` | text | derived | Stable key, e.g. `XPAR`, `XAMS`, `XETR` |
| `debs_exchange_code` | text | DEBS symbol suffix / `table1_equities_metadata.csv.exchange` | Values include `FR`, `NL`, `ETR` |
| `exchange_name` | text | derived mapping | Human-readable exchange name |
| `country_code` | text | derived mapping | `FR`, `NL`, `DE` |
| `timezone` | text | derived mapping | Local exchange timezone |

### `instrument`

One row per traded instrument in the DEBS universe.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `instrument_id` | text | derived from `debs_symbol` | Stable primary key |
| `debs_symbol` | text | `symbols_weekend.txt`, DEBS `ID` | Original DEBS symbol |
| `instrument_type` | text | `symbols_weekend.txt`, DEBS `SecType` | `E` for equity, `I` for index |
| `exchange_id` | text | derived from symbol suffix | FK to `exchange` |
| `isin` | text | `sym_isin.txt`, DEBS `ISIN`, `table1_equities_metadata.csv.isin_yf` | Null if unavailable |
| `yahoo_ticker` | text | `table1_equities_metadata.csv.yahoo_ticker` | Null for unresolved instruments and indices |
| `currency` | text | DEBS `Currency`, metadata `currency` | Prefer observed DEBS currency when available |
| `instrument_name` | text | metadata `shortName` or `longName` | For indices, use the DEBS symbol unless a name source is added |
| `quote_type` | text | metadata `quoteType` | Mostly available for resolved equities |
| `resolution_status` | text | metadata and unresolved-symbol table | `resolved`, `unresolved`, or source-specific status |

### `company`

One row per resolved company from `table1_equities_metadata.csv`.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `company_id` | text | derived | Prefer ISIN when available, otherwise stable hash of resolved name/ticker |
| `short_name` | text | `shortName` | Short company name |
| `long_name` | text | `longName` | Full company name |
| `country` | text | `country` | Headquarters country when available |
| `city` | text | `city` | Headquarters city when available |
| `website` | text | `website` | Company website |
| `market_cap` | numeric | `marketCap` | Current Yahoo value, not necessarily Nov 2021 |
| `full_time_employees` | numeric | `fullTimeEmployees` | Current Yahoo value |
| `source` | text | constant | e.g. `yahoo_finance` |

### `sector`

Normalized sectors and industries observed in the company metadata.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `sector_id` | text | derived | Stable key from `sector_name` and `industry_name` |
| `sector_name` | text | metadata `sector` | Yahoo sector classification |
| `industry_name` | text | metadata `industry` | Yahoo industry classification |
| `taxonomy` | text | constant | e.g. `yahoo_finance` |

### `instrument_company`

Bridge from DEBS instruments to resolved companies.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `instrument_id` | text | metadata `debs_symbol` | FK to `instrument` |
| `company_id` | text | derived from metadata row | FK to `company` |
| `resolved_via` | text | metadata `resolved_via` | `ticker` or `isin` |
| `isin` | text | metadata `isin_yf` | Useful audit field |
| `yahoo_ticker` | text | metadata `yahoo_ticker` | Useful audit field |

### `company_sector`

Bridge from resolved companies to sector and industry classifications.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `company_id` | text | derived from metadata row | FK to `company` |
| `sector_id` | text | derived from sector and industry | FK to `sector` |
| `source` | text | constant | e.g. `yahoo_finance` |

### `market_tick`

Cleaned tick stream from DEBS. The table keeps the core fields needed by downstream workloads and avoids carrying every raw DEBS column into gold. Additional DEBS fields can stay in bronze/silver or be added as optional columns if a workload needs them.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `tick_id` | text | derived | Stable hash or sequence from source file, row number, instrument, and event time |
| `instrument_id` | text | DEBS `ID` | FK to `instrument` |
| `instrument_type` | text | DEBS `SecType` | Redundant but useful for stream-local filtering |
| `event_time` | timestamp | DEBS `Date` + `Time` | Parsed event timestamp |
| `trading_date` | date | DEBS `Trading date` or `Date` | Trading-day assignment |
| `ask_price` | numeric | DEBS `Ask` | Nullable |
| `ask_volume` | numeric | DEBS `Ask volume` | Nullable |
| `bid_price` | numeric | DEBS `Bid` | Nullable |
| `bid_volume` | numeric | DEBS `Bid volume` | Nullable |
| `last_price` | numeric | DEBS `Last` | Nullable |
| `last_volume` | numeric | DEBS `Last volume` | Nullable |
| `total_volume` | numeric | DEBS `Total volume` | Nullable |
| `mid_price` | numeric | DEBS `Mid price` | Nullable |
| `open_price` | numeric | DEBS `Open` | Nullable |
| `close_price` | numeric | DEBS `Close` | Nullable |
| `current_price` | numeric | DEBS `Current price` | Nullable |
| `day_high_price` | numeric | DEBS `Day's high` | Nullable |
| `day_low_price` | numeric | DEBS `Day's low` | Nullable |
| `currency` | text | DEBS `Currency` | Nullable |
| `isin` | text | DEBS `ISIN` | Useful source-local identifier |
| `source_file` | text | file path | Input file name |
| `source_row_number` | bigint | ingestion metadata | Row number within source file |

### `news_document`

Energy-relevant GDELT document records from `gkg_energy_enriched.csv`.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `document_id` | text | derived | Stable hash of `SOURCEURL` and `DATE` |
| `publication_date` | date | GDELT `DATE` | `YYYYMMDD` |
| `source` | text | `SOURCE` | Source domain or domains |
| `source_url` | text | `SOURCEURL` | Document URL |
| `article_count` | integer | `NUMARTS` | Salience / buzz weight |
| `energy_sectors` | text | `ENERGY_SECTORS` | Pipe-separated source value |
| `energy_themes` | text | `ENERGY_THEMES` | Pipe-separated source value |
| `tone_avg` | numeric | `TONE_AVG` | GDELT tone |
| `tone_positive` | numeric | `TONE_POS` | Positive density |
| `tone_negative` | numeric | `TONE_NEG` | Negative density |
| `tone_polarity` | numeric | `TONE_POLARITY` | Polarity measure |
| `tone_activity` | numeric | `TONE_ACTIVITY` | Activity-reference density |
| `tone_self_reference` | numeric | `TONE_SELFREF` | Self/group-reference density |
| `energy_tickers_raw` | text | `ENERGY_TICKERS` | Pipe-separated ticker mentions |
| `energy_entities` | text | `ENERGY_ENTITIES` | Pipe-separated source value |
| `country_codes` | text | `COUNTRY_CODES` | Pipe-separated country codes |
| `top_locations` | text | `TOP_LOCATIONS` | Source location string |
| `persons` | text | `PERSONS` | Semicolon-separated source value |
| `cameo_event_ids` | text | `CAMEO_EVENT_IDS` | Comma-separated source event IDs |

### `news_event_link`

Bridge from GDELT documents to CAMEO event records. The current source contains the event-link table rather than a fully normalized CAMEO event dimension.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `global_event_id` | text | `GlobalEventID` | CAMEO event identifier |
| `document_id` | text | derived from `SourceURL` and `DATE` | FK to `news_document` |
| `event_date` | date | `DATE` | `YYYYMMDD` |
| `event_root_code` | text | `EventRootCode` | CAMEO root action code |
| `quad_class` | integer | `QuadClass` | CAMEO quad class |
| `quad_class_name` | text | `QuadClassName` | Human-readable quad class |
| `goldstein_scale` | numeric | `GoldsteinScale` | Conflict/cooperation intensity |
| `event_avg_tone` | numeric | `Event_AvgTone` | Event-level tone |
| `action_geo_full_name` | text | `ActionGeo_FullName` | Event location |
| `action_geo_country` | text | `ActionGeo_CC` | Event country/location code |
| `energy_sectors` | text | `Energy_Sectors` | Energy sectors from linking document |
| `document_tone` | numeric | `Doc_Tone` | Document tone |
| `document_tickers_raw` | text | `Doc_Tickers` | Tickers from linking document |
| `source_url` | text | `SourceURL` | Joining document URL |

### `news_ticker_mention`

One row per document and ticker mention extracted from the pipe-separated ticker lists.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `document_id` | text | derived from GDELT document | FK to `news_document` |
| `ticker` | text | split from `ENERGY_TICKERS` or `Doc_Tickers` | Raw ticker mention |
| `instrument_id` | text | resolved through `instrument.yahoo_ticker` or `instrument.debs_symbol` | Nullable when no match exists |
| `company_id` | text | resolved through `instrument_company` | Nullable when no match exists |
| `mention_source` | text | constant | `gkg_energy_enriched` or `gkg_energy_event_link` |

### `electricity_price`

Hourly day-ahead electricity prices.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `price_id` | text | derived | Stable key from timestamp and bidding zone |
| `timestamp_utc` | timestamp | `timestamp_utc` | UTC timestamp |
| `timestamp_local` | timestamp | `timestamp_local` | Local timestamp with offset |
| `bidding_zone` | text | `bidding_zone` | European bidding zone, e.g. `DE-LU`, `FR`, `NL` |
| `price_eur_mwh` | numeric | `price_eur_mwh` | Day-ahead price in EUR/MWh |
| `source` | text | constant | e.g. `fraunhofer_ise_energy_charts` |

### `weather_observation`

Weather observations in the common Sensor.Community schema.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `observation_id` | text | derived | Stable key from sensor, timestamp, latitude, longitude |
| `sensor_id` | text | `sensorID` | Sensor.Community sensor identifier |
| `latitude` | numeric | `lat` | Sensor latitude |
| `longitude` | numeric | `lon` | Sensor longitude |
| `observation_time` | timestamp | `timestamp` | Sensor observation timestamp |
| `temperature_celsius` | numeric | `temperature` | Celsius when available |
| `relative_humidity` | numeric | `humidity` | Nullable |
| `source` | text | constant | `sensor_community` |

### `market_bar`

Derived time-bucketed market bars for dashboard and feature workloads.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `instrument_id` | text | `market_tick` | FK to `instrument` |
| `window_start` | timestamp | derived | Start of event-time window |
| `window_end` | timestamp | derived | End of event-time window |
| `window_size` | text | configuration | e.g. `1m`, `5m`, `1h`, `1d` |
| `open_price` | numeric | derived | First observed price in window |
| `high_price` | numeric | derived | Max observed price in window |
| `low_price` | numeric | derived | Min observed price in window |
| `close_price` | numeric | derived | Last observed price in window |
| `volume` | numeric | derived | Sum or delta of traded volume, depending on source semantics |
| `tick_count` | bigint | derived | Number of ticks in window |
| `vwap` | numeric | derived | Volume-weighted average price when enough data is available |

### `market_feature`

Derived features consumed by dashboards, alerts, and prediction workloads.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `instrument_id` | text | derived | FK to `instrument` |
| `feature_time` | timestamp | derived | Feature timestamp |
| `horizon` | text | configuration | e.g. `5m`, `30m`, `1h`, `1d` |
| `return_value` | numeric | `market_tick`, `market_bar` | Rolling return |
| `volatility` | numeric | `market_tick`, `market_bar` | Rolling volatility |
| `spread_bps` | numeric | `market_tick` | Bid/ask spread in basis points |
| `volume_zscore` | numeric | `market_bar` | Relative volume |
| `news_intensity` | numeric | `news_document`, `news_ticker_mention` | Recent linked news count or weighted count |
| `news_tone_avg` | numeric | `news_document`, `news_ticker_mention` | Recent average document tone |
| `energy_event_count` | numeric | `news_event_link` | Recent linked CAMEO energy-event count |
| `energy_event_goldstein_avg` | numeric | `news_event_link` | Recent average Goldstein scale |
| `electricity_price_eur_mwh` | numeric | `electricity_price` | Context value matched by time and region where available |
| `weather_temperature_celsius` | numeric | `weather_observation` | Aggregated regional weather context |
| `weather_relative_humidity` | numeric | `weather_observation` | Aggregated regional weather context |

### `prediction_label`

Derived future-return labels for supervised prediction tasks.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `instrument_id` | text | `market_tick`, `market_bar` | FK to `instrument` |
| `label_time` | timestamp | derived | Time at which the feature vector would be evaluated |
| `horizon` | text | configuration | e.g. `5m`, `30m`, `1h`, `1d` |
| `future_return` | numeric | derived from future market prices | Relative return over horizon |
| `direction` | integer | derived | `-1`, `0`, or `1` |
| `reference_price` | numeric | derived | Price at `label_time` |
| `future_price` | numeric | derived | Price at `label_time + horizon` |

## Notes On Source Alignment

- The DEBS tick table is defined from the current weekend sample header. Future DEBS samples should be accepted if they keep the same DEBS 2022 Grand Challenge column layout.
- GDELT is represented both as a historic corpus and as a low-throughput replay stream. The sample CSVs and full zipped files expose the same tab-delimited schema, so the gold schema is the same for smoke tests, full historic loading, and replay; only input size and ingestion scheduling change.
- Multi-valued GDELT fields remain as source-compatible text in `news_document` and `news_event_link`. The benchmark normalizes only ticker mentions into `news_ticker_mention`, because those are the primary join path to instruments and companies.
- `market_bar`, `market_feature`, and `prediction_label` are gold-level derived tables. They are fillable from the cleaned source facts and dimensions, but they are not direct source extracts.
- Company metadata is static for the default one-week run. Optional correction streams can update `instrument`, `company`, `instrument_company`, and `company_sector`, but those update streams are benchmark variants rather than required source tables.
