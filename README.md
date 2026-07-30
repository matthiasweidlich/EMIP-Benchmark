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
the benchmark scenario and workload classes, and
[docs/gold-schema.md](docs/gold-schema.md) for the dashboard-driven
gold-level schema (built by [gold/build.sh](gold/build.sh) on top of the
[silver layer](silver/README.md)).

## Datasets

The bronze-level source data lives in [data/](data/) — one numbered directory
plus a `dataset-0X-*.md` document per source (see [data/README.md](data/README.md)
for the index and conventions):

- DEBS 2022 market tick stream (high-volume streaming input)
- instrument and company metadata / identifier mapping
- company fundamentals and filings (ESEF/ESMA XBRL)
- GDELT news events with energy enrichment
- electricity prices and grid context (ENTSO-E)
- weather observations (Sensor.Community)
- climate and emissions exposure (planned)
