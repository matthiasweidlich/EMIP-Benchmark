# EMIP Scenario

The Energy Market Intelligence Platform (EMIP) benchmark models a data
aggregation and analytics company for energy markets — a Bloomberg-style
terminal specialized for energy-transition intelligence. The platform
integrates a high-volume market tick stream with company metadata,
financial filings, news, electricity-grid data, and weather into a
continuously updated view of European energy markets.

The benchmark is designed around a realistic data *product* rather than a
single isolated query. Every source is real public data, and all sources
cover one common week: **2021-11-08 to 2021-11-14**, the DEBS 2022 Grand
Challenge capture week — which happened to be the final week of COP26 and
an early leg of the European energy crisis, so the week genuinely contains
the cross-dataset signals the platform is meant to surface (day-ahead
power prices swinging 55–300 EUR/MWh, a wind-generation ramp, negative
coal/oil news tone, activist news shocks on oil majors).

The motivating question:

> Can a data system keep an energy-market intelligence platform fresh,
> correct, and queryable while it ingests high-volume tick data and
> continuously integrates slower, messier contextual data?

## Application Setting

EMIP serves analysts who track companies and market instruments exposed to
energy: utilities, oil & gas, renewables, and their industrial neighbors.
The platform ingests raw data from heterogeneous public sources and turns
it into harmonized tables, materialized views, dashboards, alert streams,
and prediction features.

The central live source is the DEBS 2022 Grand Challenge trading stream
(equities and indices on Xetra, Euronext Paris, and Euronext Amsterdam).
All other sources enrich this stream — which makes **entity resolution
the connective tissue** of the benchmark: DEBS symbols resolve through
ISINs to companies (LEI-keyed where an ESEF filing exists), sectors, news
ticker mentions, and bidding-zone geography. Resolution is deliberately
partial: 29% of the 2021 equities cannot be resolved by present-day
lookups (delistings, renames, nationalizations), and recovering majors
like Shell or EDF requires curated crosswalks. This is workload, not
noise.

## Data Domains

| Domain | Source (dataset) | Scale, full week | Role in the benchmark |
|---|---|---|---|
| Market stream | DEBS 2022 ticks (01) | 289M events, 24.9 GB, 5,502 symbols, 39 sparse columns | The high-volume stream; replayed in event time, scaled by throughput |
| Instrument / company metadata | Yahoo Finance resolution + curated seeds (02) | 2,996 equities, 2,119 resolved, 141 sector/industry pairs | Static dimensions; entity-resolution and coverage workload |
| Company fundamentals | ESEF/ESMA XBRL via GLEIF (03) | 868 filings, 394 companies, 26,501 facts | Slowly changing company state; point-in-time correctness |
| News and events | GDELT GKG 1.0 + CAMEO (04) | Two weeks: 861,582 documents, 1.5M events, 3.8M links; 49,298 energy-tagged | Historic corpus + low-rate publication-time stream; date granularity only |
| Electricity prices & grid | ENTSO-E (05) | 6 bidding zones, 15-min prices; load/generation/flows for DE-LU/FR/NL | Physical-world context; spike/ramp event source |
| Weather | Sensor.Community (06) | 30.6M observations, 8,447 sensors, 15-min zone aggregates | Dense environmental context; dirty-sensor data quality |
| Climate / emissions exposure | planned (07) | — | Future transition-risk dimension |
| Derived serving state | silver + gold layers | 5.9 GB DuckDB, 2.6M 5-min bars, zone/company marts | Maintained by the system under test; freshness and correctness are outputs |

Timestamps span four conventions (naive CET ticks, tz-aware electricity,
naive-UTC weather, date-only news) and normalize to UTC in silver.
Market hours vs. physical-world hours matter: power prices spike in the
evening after the 17:30 CET market close, so event studies must branch
between intraday and overnight-gap semantics.

### Natural throughput

| Domain | Natural replay rate |
|---|---|
| Market ticks | ~478 events/s averaged over the week; ~1.9k/s over trading days; bursty peaks far higher (opening/closing auctions ~7M ticks/hour) |
| Weather | ~50 observations/s, near-constant around the clock |
| Electricity | 6 zones x 15-min buckets (prices); day-ahead prices arrive as a daily auction vector |
| News | ~1 GKG document/s (all topics); ~0.08/s energy-tagged; date-granular publication time |
| Metadata / fundamentals | Static for the week; optional correction events (late mappings, restatements) |

## Workload Classes

**ELT / data integration** (implemented in `silver/`): lenient parsing of
non-RFC CSV with in-line comments and ragged rows; nullifying placeholder
zero prices; timezone normalization; symbol->ISIN->LEI->company
resolution with explicit unresolved statuses; sensor plausibility
filtering with reject tables; deduplication and identity (document ids,
event ids) across weeks.

**Materialized view maintenance** (implemented in `gold/`): 5-min OHLC
bars with returns and spreads over 289M ticks; 15-min zone facts joining
price, load, generation mix, carbon intensity, and weather; daily news
facts by topic and company; company profiles; rolling 24h cross-signal
correlations. Views are specified by inputs, update semantics, and
expected results — not physical schema — so stream processors,
incremental-view engines, and lakehouse ELT can all implement them.

**Dashboard queries** (D1–D5, `gold/dashboard_queries.sql`): interactive
queries over the maintained state — zone pulse, weather->load->price
correlations, news pulse, company 360 profile, feed health. Must stay
low-latency while ingestion continues.

**Benchmark queries** (B1–B6, `gold/benchmark_queries.sql`): six
verifiable queries, one per query-shape family, jointly covering all six
datasets — the DEBS Grand Challenge EMA/crossover queries in batch form
(B1), windowed top-K (B2), a five-source power-spike event study with
market-hours branching (B3), a four-grain cross-domain scorecard (B4), an
as-of join (B5), and a news-shock event study conditioned on fundamentals
(B6). Reference runtimes: [benchmark-results.md](benchmark-results.md).

**Alerts and decision support**: the signal family behind B1/B3 —
crossover advisories, price-spike and ramp detection, feed-health
anomalies — evaluated as low-latency stateful pattern detection during
replay.

**Prediction and feature generation** (planned): hourly per-instrument
feature rows blending bars, as-of power prices, and day-grain news tone,
plus forward-return labels via time-offset windows — evaluating
point-in-time-correct feature freshness, not model training.

## Evaluation Focus

The benchmark is scaled by tick throughput; the metric is the maximum
scale at which a system meets the latency thresholds of every workload
class simultaneously. All workloads have exact, verifiable answers over
the fixed historical week. A single-node DuckDB batch implementation of
the ELT, view, dashboard, and query workloads is included as the
reference baseline ([benchmark-results.md](benchmark-results.md)); the
streaming driver concept is sketched in
[benchmark-driver.md](benchmark-driver.md).
