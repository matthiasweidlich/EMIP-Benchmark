# EMIP-Benchmark

The **Energy Market Intelligence Platform (EMIP)** benchmark models a
"Bloomberg for energy markets": a data product that integrates a
high-volume market tick stream with company metadata, financial filings,
news, electricity-grid data, and weather — all real public data covering
one common week, **2021-11-08 to 2021-11-14** (the DEBS 2022 Grand
Challenge week, which was also the final week of COP26).

Unlike single-query streaming benchmarks, EMIP is built around a complete
medallion-architecture data product: raw bronze sources, a cleaned and
entity-resolved silver layer, a dashboard-ready gold layer, and a suite of
cross-dataset benchmark queries with verifiable answers. A full DuckDB
reference implementation is included and measured
([docs/benchmark-results.md](docs/benchmark-results.md)).

See [docs/scenario.md](docs/scenario.md) for the benchmark scenario and
workload classes.

## The data

Six real sources, one shared week (see [data/README.md](data/README.md)
and the per-dataset `data/dataset-0X-*.md` documents):

| # | Source | Content | Scale (full week) |
|---|---|---|---|
| 01 | [DEBS 2022 tick stream](data/dataset-01-debs-tick-stream.md) | Market ticks, 3 exchanges (Xetra, Paris, Amsterdam), 39 sparse columns | **289M events, 24.9 GB**, 5,502 symbols |
| 02 | [Instrument & company metadata](data/dataset-02-company-security-mapping.md) | Symbol -> ISIN -> company/sector resolution (Yahoo Finance + curated seeds) | 2,996 equities, 2,119 resolved (71%), 877 permanently drift-lost |
| 03 | [Company fundamentals](data/dataset-03-company-fundamentals-filings.md) | ESEF/ESMA XBRL filings via GLEIF ISIN->LEI | 868 filings, 394 companies, 26.5k facts |
| 04 | [GDELT news & events](data/dataset-04-gdelt-news-events.md) | GKG documents + CAMEO events, energy-classified, two weeks (Nov 1–14) | 861,582 documents, 1.5M events, 3.8M links |
| 05 | [Electricity prices & grid](data/dataset-05-electricity-prices.md) | ENTSO-E day-ahead prices (6 bidding zones), load, generation mix, flows | 15-min resolution, full week |
| 06 | [Weather](data/dataset-06-weather.md) | Sensor.Community crowd-sourced temperature/humidity, Western Europe | 30.6M observations, 8.4k sensors |
| 07 | [Climate / emissions exposure](data/dataset-07-climate-emissions-exposure.md) | Planned — sketch only | — |

Small files and samples are committed; large files (weekday tick CSVs,
full weather week, unfiltered GDELT) are gitignored and regenerated with
scripts committed next to each dataset. **The builds auto-detect what is
present**: with only the committed samples you get a small but working
stack; with the full local data you get the numbers above.

## The layers

- **Bronze** — `data/`: raw files with all their quirks preserved
  (comment preambles, sparse columns, zero-price placeholders, sensor
  sentinels, mixed timezones). The quirks are workload, not noise.
- **Silver** — `silver/` (`silver/build.sh`): typed, UTC-normalized,
  entity-resolved tables in DuckDB — 289M cleaned ticks with a rejects
  table, instrument/company/sector dimensions keyed LEI > ISIN > ticker,
  news documents with resolved ticker mentions, long-format grid and
  weather tables. See [silver/README.md](silver/README.md).
- **Gold** — `gold/` (`gold/build.sh`, runs silver first): dashboard-ready
  dimensions, facts, and marts — 5-min OHLC bars, 15-min energy/weather
  zone facts, daily news facts, company profiles, rolling cross-signal
  correlations. Schema: [docs/gold-schema.md](docs/gold-schema.md).

## The workloads

**Benchmark queries** (`gold/benchmark_queries.sql`, runner
`gold/run_benchmark_queries.sh`) — six queries, one per workload class,
every dataset covered:

| Query | Class | Datasets |
|---|---|---|
| B1 DEBS Grand Challenge, batch edition (recursive EMA-38/100 + crossover advisories) | recursion, pattern detection, top-N per group | 01 02 |
| B2 Top-K movers, 30-min lookback | windowed top-K + dimension chain | 01 02 |
| B3 Power-spike event study (intraday vs overnight-gap branching) | multi-source event study, market-hours logic | 01 02 04 05 06 |
| B4 Daily cross-domain sector scorecard | pre-aggregate-then-join, 4 grains | 01 02 04 05 06 |
| B5 As-of join: utility ticks vs concurrent power price | as-of / non-equi join | 01 02 05 |
| B6 News-shock event study (news drives, fundamentals condition) | self-relative baselines, abnormal returns | 01 02 03 04 |

**Dashboard queries** (`gold/dashboard_queries.sql`, D1–D5) — smoke
queries for the five dashboards the gold schema serves: energy-vs-market
pulse, weather->load->price correlations, news pulse, company profile,
feed health. Further candidate queries:
[docs/some-interesting-queries.md](docs/some-interesting-queries.md) /
[.sql](docs/some-interesting-queries.sql). A streaming benchmark driver is
sketched in [docs/benchmark-driver.md](docs/benchmark-driver.md).

**Validation plots** (`gold/validate_plots.py` -> `gold/plots/*.png`) —
per-dataset time-series coverage plots for the week; genuine data events
(the Monday 300 EUR/MWh price spike, the Tuesday wind ramp, a Saturday
weather-archive outage) are visible at a glance.

## Quick start

```bash
pip install duckdb            # >= 1.5; matplotlib for the plots
./gold/build.sh               # bronze -> silver -> gold + dashboard smoke queries
./gold/run_benchmark_queries.sh   # B1-B6 with timings
python3 gold/validate_plots.py    # coverage plots
```

With only the committed data this builds in well under a minute. For the
full-scale build (~13 min, 5.9 GB database), fetch the large inputs first
— each is a script or documented download next to its dataset:
weekday tick files (Zenodo links in dataset-01), the weather week
(`data/06-weather/run_all.sh`), and the two-week GDELT tables
(`data/04-gdelt-news-events/build_full_tables.py`).

## Licensing

Sources retain their original terms: DEBS 2022 trading data is
CC BY-NC-SA 4.0 (© Infront Financial Technology GmbH); ENTSO-E,
GDELT, Sensor.Community, GLEIF, and filings.xbrl.org data follow their
respective open-data terms. This repository's own code and documentation
are provided for research use.
