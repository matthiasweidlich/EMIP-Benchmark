# EMIP DuckDB Table Sizes

Generated 2026-07-30 from `silver/emip.duckdb` by `gold/report_table_sizes.py` (rerun after a rebuild).

Database file: **5.9 GiB** (23,545 blocks x 256 KiB). Bronze is views over the raw files (no database storage); silver and gold are materialized tables.

| Table | Rows | Columns | On disk | % of stored bytes | Bytes/row |
|---|---:|---:|---:|---:|---:|
| `silver.market_tick` | 289,049,746 | 22 | 3.9 GiB | 70.7% | 14 |
| `silver.news_document` | 861,582 | 25 | 862.5 MiB | 15.4% | 1,050 |
| `silver.weather_observation` | 30,159,403 | 7 | 458.0 MiB | 8.2% | 16 |
| `silver.cameo_event` | 1,502,999 | 16 | 137.5 MiB | 2.5% | 96 |
| `gold.fact_market_bar` | 2,630,917 | 17 | 111.5 MiB | 2.0% | 44 |
| `silver.news_event_link` | 2,373,101 | 2 | 47.8 MiB | 0.9% | 21 |
| `silver.weather_rejects` | 451,096 | 7 | 8.5 MiB | 0.2% | 20 |
| `gold.fact_instrument_day` | 37,172 | 15 | 2.2 MiB | 0.0% | 63 |
| `silver.market_tick_rejects` | 67,056 | 24 | 1.0 MiB | 0.0% | 16 |
| `gold.mart_company_profile` | 2,652 | 34 | 768.0 KiB | 0.0% | 297 |
| `gold.dim_company` | 2,652 | 15 | 512.0 KiB | 0.0% | 198 |
| `gold.dim_instrument` | 5,502 | 11 | 512.0 KiB | 0.0% | 95 |
| `gold.mart_zone_pulse` | 4,032 | 26 | 512.0 KiB | 0.0% | 130 |
| `silver.company` | 2,652 | 13 | 512.0 KiB | 0.0% | 198 |
| `silver.financial_fact` | 26,501 | 11 | 512.0 KiB | 0.0% | 20 |
| `silver.instrument` | 5,502 | 10 | 512.0 KiB | 0.0% | 95 |
| `gold.dim_sector` | 141 | 4 | 256.0 KiB | 0.0% | 1,859 |
| `gold.dim_zone` | 6 | 6 | 256.0 KiB | 0.0% | 43,691 |
| `gold.fact_company_news_day` | 171 | 11 | 256.0 KiB | 0.0% | 1,533 |
| `gold.fact_energy_15min` | 4,032 | 12 | 256.0 KiB | 0.0% | 65 |
| `gold.fact_fundamentals_latest` | 5,142 | 6 | 256.0 KiB | 0.0% | 51 |
| `gold.fact_topic_news_day` | 98 | 10 | 256.0 KiB | 0.0% | 2,675 |
| `gold.fact_weather_15min` | 4,021 | 8 | 256.0 KiB | 0.0% | 65 |
| `gold.mart_rolling_correlation` | 10,658 | 5 | 256.0 KiB | 0.0% | 25 |
| `gold.mart_sector_day` | 77 | 11 | 256.0 KiB | 0.0% | 3,404 |
| `silver.electricity_price` | 1,008 | 4 | 256.0 KiB | 0.0% | 260 |
| `silver.exchange` | 3 | 6 | 256.0 KiB | 0.0% | 87,381 |
| `silver.filing` | 868 | 10 | 256.0 KiB | 0.0% | 302 |
| `silver.grid_flow` | 2,688 | 4 | 256.0 KiB | 0.0% | 98 |
| `silver.grid_generation` | 33,601 | 5 | 256.0 KiB | 0.0% | 8 |
| `silver.grid_load` | 2,016 | 3 | 256.0 KiB | 0.0% | 130 |
| `silver.instrument_company` | 2,985 | 5 | 256.0 KiB | 0.0% | 88 |
| `silver.news_ticker_mention` | 2,311 | 6 | 256.0 KiB | 0.0% | 113 |
| `silver.sector` | 141 | 4 | 256.0 KiB | 0.0% | 1,859 |
| `silver.zone_region_map` | 6 | 3 | 256.0 KiB | 0.0% | 43,691 |
| **total** | | | **5.5 GiB** | 100% | |

Notes:

- On-disk size counts the distinct storage blocks used per table (`pragma_storage_info`), i.e. compressed size including per-column metadata; small tables round up to one block.
- The database file can be larger than the sum of table bytes (free blocks from rebuilds, catalog, WAL checkpointing).
- Row counts are exact (`count(*)` at generation time).
