# EMIP Scenario

The Energy Market Intelligence Platform (EMIP) benchmark models a data aggregation and analytics company for renewable energy markets. The platform is similar in spirit to a Bloomberg-style market terminal, but specialized for energy-transition intelligence: it combines live market data, company metadata, energy-sector context, news, weather, and climate exposure signals into a continuously updated view of renewable energy markets.

The benchmark is designed around a realistic data product rather than a single isolated streaming query. Analysts use EMIP to monitor European equities and indices, understand sector-level movements, detect market and climate-related events, and prepare features for short-term prediction and longer-term strategic analysis.

## Application Setting

EMIP serves analysts who track companies and market instruments that are exposed to renewable energy, electrification, climate policy, fossil-fuel transition risk, energy infrastructure, and related supply chains. The platform ingests raw data from heterogeneous public and semi-public sources and turns them into harmonized analytical tables, materialized views, dashboards, and alert streams.

The central live source is the DEBS 2022 Grand Challenge trading dataset, which provides European market tick data for equities and indices traded in Paris, Amsterdam, and Frankfurt/Xetra. This source acts as the high-volume stream. Other sources enrich the stream with entity metadata, fundamentals, energy-market indicators, climate/emissions exposure, and news or event signals.

The motivating question is:

> Can a streaming data system keep an energy-market intelligence platform fresh, correct, and queryable while it ingests high-volume tick data and continuously integrates slower, messier contextual data?

## Data Domains

| Domain | Role | Example Sources | Current Size / Scale | Update Behavior |
|---|---|---|---|---|
| Market stream | High-volume updates over instruments | DEBS 2022 trading ticks | Full DEBS week: about 289M tick events, 24.9 GB, 5,504 equities and indices. Current repo sample: weekend files `day13.csv` and `day14.csv`, about 59k lines total. | Main streamed input. Replay in event time or accelerated; benchmark scale is primarily controlled by tick throughput. |
| Instrument and company metadata | Entity resolution and sector grouping | DEBS symbols, Yahoo Finance-style metadata, OpenFIGI, LEI, Wikidata | Current repo: 5,499 symbols, 2,996 equities, 2,503 indices, 5,486 symbol-to-ISIN mappings, 2,119 resolved equity metadata rows. | Static dimension data for a one-week benchmark run, except optional correction/update events for entity-resolution workloads. |
| Company fundamentals | Slowly changing company state | filings, annual reports, financial facts | Expected to be much smaller than the tick stream for the one-week interval; typically one row per company, filing, metric, and reporting period. | Static for the default one-week benchmark, because annual/quarterly fundamentals rarely change within the replay window. Optional filing or restatement events may be injected for view-maintenance stress tests. |
| Energy and commodity context | External drivers of market movement | EIA-style energy indicators, electricity generation, fuel prices | Small to medium time-series data: hourly, daily, weekly, or monthly indicators over the benchmark interval and relevant regions. | Low-rate contextual updates; usually replayed at natural timestamp frequency or loaded as slowly changing context. |
| News and event context | Text/event signals around companies and sectors | GDELT-style news events | Current repo: 430,918 GKG records scanned for Nov 8-14, 2021; 49,298 energy-relevant records; 224,424 document-event links in compressed enrichment files. | Medium-rate event stream or micro-batch source. Can be replayed by publication time and joined with market windows. |
| Climate exposure | Transition-risk and emissions context | Climate TRACE/EPA-style facility or asset data | Usually asset/facility-level annual or monthly data; much smaller and slower-moving than market ticks. | Static dimension/enrichment data for a one-week benchmark run. Updates are optional and model corrections or new disclosure releases. |
| Derived serving state | Tables and views consumed by applications | live features, sector aggregates, prediction inputs, dashboard state | Size depends on configured workloads: typically proportional to instruments, sectors, windows, and retained feature history. | Continuously maintained by the system under test; freshness and correctness are benchmark outputs. |

The default benchmark treats company metadata, company fundamentals, and climate exposure as static for the one-week DEBS interval. They provide relational and enrichment complexity without pretending that annual reports, sector classifications, or facility emissions update at tick-stream speed. Optional benchmark variants may inject corrections, late mappings, new filings, or restatements to test systems that support dynamic dimension updates.

### Real-World Throughput

The following rates describe approximate real-world or natural replay speed. Benchmark stress runs may accelerate these rates, but the natural rates are useful for defining baseline freshness expectations.

| Domain | Natural Throughput / Update Rate | Notes |
|---|---|---|
| Market stream | About 478 ticks/s over the full seven-day DEBS interval; about 1.9k ticks/s when averaged over five 8.5-hour trading days. | Actual market traffic is bursty, so short-window peaks are higher. The benchmark scale factor should multiply this stream. |
| Instrument and company metadata | Static for the default one-week run. | Metadata is loaded before replay. Optional correction streams may add low-rate updates for symbol, ISIN, sector, or company mappings. |
| Company fundamentals | Static for the default one-week run. | Annual and quarterly facts do not normally change within the week. Optional filing/restatement events can be injected at low rate. |
| Energy and commodity context | Low rate: hourly, daily, weekly, or monthly depending on series. | Treated as slowly changing context; replay by source timestamp or load as reference data. |
| News and event context | Medium rate: current sample has 49,298 energy-relevant GKG records over seven days, about 0.08 records/s on average; 224,424 document-event links, about 0.37 links/s on average. | Real publication traffic is bursty. For alert workloads, replay by publication time rather than uniform rate. |
| Climate exposure | Static for the default one-week run. | Facility and emissions disclosures are typically annual or monthly. Updates represent corrections or new disclosure releases. |
| Derived serving state | No independent input rate. | Its update rate is induced by the market stream, context updates, and the configured view definitions. |

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

The materialized-view workload maintains continuously updated analytical state over the incoming data. It should not be tied to a single fixed schema. Instead, the benchmark should define view families that systems may implement using their native representation, as long as the externally visible results are equivalent.

The maintained state should cover several generic categories:

- latest-state views over fast-moving entities, such as instruments, sectors, feeds, or alerts;
- rolling aggregate views over event-time windows, such as price movement, volume, volatility, news intensity, or data-quality rates;
- enrichment views that combine raw stream events with slower-changing metadata, such as company, sector, exchange, geography, or identifier mappings;
- cross-domain views that relate market behavior to contextual signals, such as news, energy indicators, weather, or climate exposure;
- feature views that expose the current inputs needed by prediction, alerting, or dashboard workloads;
- data-quality and coverage views that track missing fields, unresolved identifiers, stale sources, duplicate records, and late arrivals.

The benchmark should specify each view by its input relations, update semantics, expected result, freshness target, and correctness oracle, rather than by requiring a particular physical schema. This keeps the workload portable across stream processors, streaming databases, incremental view-maintenance systems, and lakehouse-style ELT engines.

This workload stresses incremental maintenance, high-cardinality state, temporal joins, rolling windows, top-k maintenance, late context updates, partial entity coverage, and shared derived state.

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
