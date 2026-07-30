# EMIP Silver Layer

Cleans, types, normalizes, and links the bronze sources in [`../data/`](../data/)
into a queryable DuckDB database. Raw quirks (comment headers, sparse columns,
sentinel values, mixed timezones, pence quotes) are resolved here; rejected rows
are kept in `*_rejects` tables for the data-quality workloads.

## Build

```bash
pip install duckdb   # python3 + duckdb package required
silver/build.sh      # writes silver/emip.duckdb
gold/build.sh        # full rebuild: silver + gold layer + dashboard smoke queries
```

The build unzips the GDELT archives in place (extracted CSVs are gitignored),
then executes `sql/*.sql` in order. It is idempotent.

## Conventions

- **All event times are naive UTC timestamps** (`*_utc` columns). DEBS tick
  times are local CET and are shifted by the constant −1 h offset valid for the
  DST-free benchmark week; electricity timestamps carry explicit offsets;
  weather timestamps are already UTC. GDELT has publication dates only.
- **Company identity**: `company_id` prefers `LEI:<lei>` (via the GLEIF/ESEF
  crosswalk of dataset 03), falls back to `ISIN:<isin>`, then `YH:<ticker>`.
- **Prices**: DEBS `XXP` (pence) prices are scaled ×0.01 and reported as GBP
  (`currency_raw` keeps the original code).
- Unresolved and rejected data is preserved, not dropped:
  `instrument.resolution_status`, `market_tick_rejects`, `weather_rejects`,
  and unresolved `news_ticker_mention` rows (`isin IS NULL`).

## Tables

| Table | Content |
|---|---|
| `silver.exchange`, `silver.zone_region_map` | Venue and bidding-zone dimensions (tiny, seeded) |
| `silver.instrument` | All 5,499 DEBS symbols: type, exchange, ISIN, Yahoo ticker, resolution status, company FK |
| `silver.company`, `silver.sector`, `silver.instrument_company` | Company dimension (LEI/ISIN-keyed), Yahoo sector taxonomy, bridge |
| `silver.market_tick` / `market_tick_rejects` | Typed tick stream, UTC event time, scaled prices / unparseable rows |
| `silver.news_document` | GDELT docs: split multi-value fields, canonical URL, tone metrics |
| `silver.news_ticker_mention` | Exploded ticker mentions resolved to ISINs (Yahoo ticker + curated crosswalk in `seed/gdelt_ticker_crosswalk.csv`) |
| `silver.cameo_event`, `silver.news_event_link` | Event dimension reconstructed from the link file; doc↔event bridge |
| `silver.electricity_price` | Hourly day-ahead prices, 6 zones, long format |
| `silver.grid_load`, `silver.grid_generation`, `silver.grid_flow` | ENTSO-E 15-min load, per-fuel generation (unpivoted), cross-border flows |
| `silver.weather_observation` / `weather_rejects` | Filtered observations with approximate country tag / sentinel & out-of-region rows |
| `silver.filing`, `silver.financial_fact` | ESEF filings and typed long-format IFRS facts |
| `silver.latest_company_fundamentals` | View: latest pre-benchmark-week value per company & metric |
