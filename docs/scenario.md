# EMIP Scenario

The Energy Market Intelligence Platform (EMIP) benchmark models a data aggregation and analytics company for renewable energy markets. The platform is similar in spirit to a Bloomberg-style market terminal, but specialized for energy-transition intelligence: it combines live market data, company metadata, energy-sector context, news, weather, and climate exposure signals into a continuously updated view of renewable energy markets.

The benchmark is designed around a realistic data product rather than a single isolated streaming query. Analysts use EMIP to monitor European equities and indices, understand sector-level movements, detect market and climate-related events, and prepare features for short-term prediction and longer-term strategic analysis.

## Application Setting

EMIP serves analysts who track companies and market instruments that are exposed to renewable energy, electrification, climate policy, fossil-fuel transition risk, energy infrastructure, and related supply chains. The platform ingests raw data from heterogeneous public and semi-public sources and turns them into harmonized analytical tables, materialized views, dashboards, and alert streams.

The central live source is the DEBS 2022 Grand Challenge trading dataset, which provides European market tick data for equities and indices traded in Paris, Amsterdam, and Frankfurt/Xetra. This source acts as the high-volume stream. Other sources enrich the stream with entity metadata, fundamentals, energy-market indicators, climate/emissions exposure, and news or event signals.

The motivating question is:

> Can a streaming data system keep an energy-market intelligence platform fresh, correct, and queryable while it ingests high-volume tick data and continuously integrates slower, messier contextual data?

## Data Domains

| Domain | Role | Example Sources |
|---|---|---|
| Market stream | High-volume updates over instruments | DEBS 2022 trading ticks |
| Instrument and company metadata | Entity resolution and sector grouping | DEBS symbols, Yahoo Finance-style metadata, OpenFIGI, LEI, Wikidata |
| Company fundamentals | Slowly changing company state | filings, annual reports, financial facts |
| Energy and commodity context | External drivers of market movement | EIA-style energy indicators, electricity generation, fuel prices |
| News and event context | Text/event signals around companies and sectors | GDELT-style news events |
| Climate exposure | Transition-risk and emissions context | Climate TRACE/EPA-style facility or asset data |
| Derived serving state | Tables and views consumed by applications | live features, sector aggregates, prediction feature store |

## Workload Classes

### ELT / Data Integration

The ELT workload ingests raw source data into a medallion-style architecture. Raw data is loaded first, then cleaned, harmonized, and enriched.

Representative tasks include:

- parsing DEBS tick files with many sparse columns and mixed instrument types;
- separating equities from indices;
- resolving DEBS symbols to exchange symbols, ISINs, companies, and sectors;
- handling unresolved or ambiguous instrument identifiers;
- normalizing timestamps, currencies, exchanges, and units;
- joining market data to company metadata and energy-sector classifications;
- deduplicating news and event records;
- aligning slow context signals with high-frequency market ticks.

This workload stresses messy source ingestion, schema normalization, entity resolution, data quality handling, and reproducible table construction.

### Materialized View Maintenance

The materialized-view workload maintains continuously updated analytical state over the incoming data.

Important views include:

- `instrument_live_state`: latest price, bid/ask, spread, last update time, volume, and data-quality status per instrument;
- `instrument_live_features`: rolling returns, volatility, spread, tick counts, and moving-average indicators;
- `sector_market_state`: aggregate momentum, volume, and volatility by sector and exchange;
- `company_profile`: current company metadata, sector, country, market-cap bucket, and identifier mappings;
- `company_news_signal`: recent news intensity, event themes, tone, and salience per company;
- `company_transition_exposure`: renewable-energy, fossil-fuel, emissions, or climate-risk exposure scores;
- `prediction_feature_store`: latest feature vector per instrument or company for short-horizon prediction.

This workload stresses incremental maintenance, high-cardinality state, temporal joins, rolling windows, late context updates, partial entity coverage, and shared derived state.

### Dashboard Queries

The dashboard workload represents interactive analyst queries over the maintained state. These queries should stay low-latency while ingestion continues.

Example dashboard views:

- top moving instruments over the last 5 or 30 minutes;
- most volatile instruments by exchange;
- sector momentum across renewable energy, utilities, industrials, semiconductors, and fossil-fuel-exposed firms;
- clean-energy versus fossil-energy performance;
- companies with abnormal news pressure and corresponding price movement;
- instruments with stale ticks, missing metadata, or unresolved identifiers;
- live pipeline health and data freshness by source.


### Alerts And Decision Support

The alerting workload detects conditions that require analyst attention.

Examples:

- abnormal price movement or volatility spike;
- sudden spread widening or liquidity drop;
- sector-wide movement following energy-price or policy news;
- market reaction after a major company or climate-related event;
- stale or suspicious instrument feed;
- divergence between predicted and observed movement.

This workload stresses low-latency rule evaluation, stateful pattern detection, and explainability of alert triggers.

### Prediction And Feature Generation

The prediction workload is not meant to benchmark model training itself. Instead, it evaluates whether the system can maintain fresh and correct feature tables for downstream stock or sector movement prediction.

Feature examples:

- rolling returns and volatility from tick data;
- short-window volume and spread features;
- sector-relative momentum;
- recent news intensity and tone;
- energy-price and generation-context indicators;
- company-sector and transition-exposure features;
- labels such as future return, abnormal return, or direction over a fixed horizon.

The important system properties are freshness, correctness, feature reproducibility, and consistent alignment of event time across sources.

## Evaluation Focus

The benchmark is scaled by the tick throughput. The benchmark metric is the maximum scale.

A valid benchmark execution must meet latency thresholds for every workload. All workloads have exact verifiable answers.

