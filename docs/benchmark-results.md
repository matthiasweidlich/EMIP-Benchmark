# EMIP Reference Results — DuckDB Single-Node Baseline

Measured 2026-07-30 on the full local data set. These numbers are a
*reference baseline* for the batch (ELT + query) half of the benchmark on a
single machine — not a target: the point of the benchmark is to compare
systems against exactly this workload.

## Environment

| | |
|---|---|
| CPU | AMD Ryzen 9 9950X (16 cores / 32 threads) |
| RAM | 60 GB |
| Storage | NVMe SSD |
| OS | Linux |
| Engine | DuckDB 1.5.3 (Python client) |
| Database | `silver/emip.duckdb`, **5.9 GB** after full build |

## Data volume (bronze inputs)

| Source | Volume |
|---|---|
| 01 DEBS ticks, full week (7 files) | 24.9 GB CSV, 289,116,802 parsed data rows |
| 04 GDELT, two weeks unfiltered | 1.5M CAMEO events, 861,582 GKG documents, 3.8M doc-event links |
| 05 ENTSO-E electricity | 672 15-min buckets x 6 zones (prices, load, generation, flows) |
| 06 Sensor.Community weather | 30,610,499 observations, 1.8 GB CSV |
| 03 ESEF fundamentals | 868 filings, 26,501 XBRL facts |

## Build (ELT bronze -> silver -> gold)

Full rebuild via `gold/build.sh`: **~13 minutes** wall clock, dominated by
the single-threaded tick CSV parse (the DEBS format defeats DuckDB's
parallel CSV reader; ~300 MB/s single-threaded) and the two scans it feeds
(clean + rejects).

Key output tables:

| Table | Rows |
|---|---|
| `silver.market_tick` | 289,049,746 (+ 67,056 rejects, 0.023%) |
| `silver.news_document` | 861,582 (49,298 energy-tagged) |
| `silver.cameo_event` | 1,502,999 |
| `silver.weather_observation` | 30,159,403 (+ 451,096 rejects) |
| `gold.fact_market_bar` (5-min OHLC) | 2,630,917 |
| `gold.fact_instrument_day` | 37,172 |
| `gold.mart_zone_pulse` / `fact_energy_15min` | 4,032 |
| `gold.mart_company_profile` | 2,652 |

## Query runtimes

All 11 queries against the fully built database, read-only connection,
two consecutive runs (`run1` includes any cold-cache effects). Dashboard
queries D1–D5: `gold/dashboard_queries.sql`; benchmark queries B1–B6:
`gold/benchmark_queries.sql` (runner: `gold/run_benchmark_queries.sh`).

| Query | Description | Rows | Run 1 (s) | Run 2 (s) |
|---|---|---:|---:|---:|
| D1 | Energy vs market: DE-LU price, renewables share, index level | 12 | 0.00 | 0.00 |
| D2 | Weather -> load -> price per-zone correlations, full week | 6 | 0.00 | 0.00 |
| D3 | News pulse: top energy topics per day with tone | 21 | 0.00 | 0.00 |
| D4 | Company profile (TotalEnergies): market + news + fundamentals | 2 | 0.00 | 0.00 |
| D5 | Feed health: instruments, price coverage, latest activity | 6 | 0.01 | 0.01 |
| B1 | DEBS GC batch: recursive EMA-38/100 + crossover advisories, last 3 per symbol | 193 | 13.34 | 13.40 |
| B2 | Top-K movers, 30-min lookback, per exchange | 30 | 0.02 | 0.01 |
| B3 | Power-spike event study (5 sources, intraday/overnight branching) | 42 | 0.01 | 0.01 |
| B4 | Daily cross-domain sector scorecard (4 facts, 4 grains) | 60 | 0.01 | 0.01 |
| B5 | As-of join: utility trade ticks vs concurrent power price | 10 | 0.16 | 0.10 |
| B6 | News-shock event study (news driver + fundamentals conditioning) | 35 | 0.01 | 0.01 |

## Reading the numbers

- Every query except B1 runs in milliseconds because it reads
  pre-aggregated gold tables: the medallion design pays the integration
  cost once at build time (~13 min for 289M ticks + 861k news documents +
  30M weather observations), after which interactive dashboards are
  essentially free. "Pre-aggregate then join" vs "join raw then aggregate"
  is an explicit benchmark axis (see B4).
- B1 is the deliberate outlier: the DEBS Grand Challenge EMA recurrence is
  a linear recursion over 1.85M priced bars with per-symbol sequences up to
  ~2,000 windows — resistant to both parallelism and pre-aggregation. It is
  the headline query for engine comparison on this workload.
- B5's as-of join (correlated LATERAL over ~34k utility trade ticks) is the
  second-slowest; DuckDB's native `ASOF JOIN` is a documented alternative
  formulation.
- These are single-run wall-clock times on a warm OS page cache; rows are
  result-set sizes, not rows scanned.
