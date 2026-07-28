# EMIP-Benchmark

## Benchmark scenario

Energy Market Intelligence Platform (EMIP) for renewable energy
markets, a "Bloomberg for Energy Markets". The platform integrates
diverse public real-world data sources covering companies, equities,
commodities, news, weather, and related domains across a common time
interval. ELT pipelines in medallion architecture ingest, harmonize,
and prepare the data. The resulting platform supports real-time
alerts, dashboards, and long-term strategic projections/trends.

See [docs/scenario.md](docs/scenario.md) for an extended description of
the benchmark scenario and workload classes.

## Dataset Sketch

The first sample dataset package is in [datasets/sample-pre-etl](datasets/sample-pre-etl). It contains small pre-ETL examples for the main source layers:

- DEBS-style market ticks
- company/security mapping
- company fundamentals and filings
- GDELT-style news events
- EIA-style energy context
- climate and emissions exposure
