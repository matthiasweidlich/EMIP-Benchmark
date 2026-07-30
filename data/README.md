# EMIP Bronze-Level Source Data

This directory contains the raw (bronze-level) source data for the EMIP benchmark.
All sources cover the DEBS 2022 Grand Challenge week, **2021-11-08 to 2021-11-14**.

Each dataset has a numbered directory with the actual files and a matching
`dataset-0X-*.md` document describing schema, provenance, and ETL notes.

## Datasets

| # | Dataset | Directory | Documentation | Data in repo |
|---|---|---|---|---|
| 01 | DEBS tick stream | [01-debs-tick-stream/](01-debs-tick-stream/) | [dataset-01-debs-tick-stream.md](dataset-01-debs-tick-stream.md) | Weekend days committed; `day-08`/`day-09` downloaded locally (gitignored, ~10 GB); full week via Zenodo links (~25 GB) |
| 02 | Instrument & company metadata | [02-instrument-company-metadata/](02-instrument-company-metadata/) | [dataset-02-company-security-mapping.md](dataset-02-company-security-mapping.md) | Complete (canonical week universe + extraction/resolution scripts, resolved/unresolved metadata) |
| 03 | Company fundamentals / filings | [03-company-fundamentals/](03-company-fundamentals/) | [dataset-03-company-fundamentals-filings.md](dataset-03-company-fundamentals-filings.md) | Complete (868 ESEF filings, 394 companies, 26.5k XBRL facts + LEI crosswalk) |
| 04 | GDELT news & events | [04-gdelt-news-events/](04-gdelt-news-events/) | [dataset-04-gdelt-news-events.md](dataset-04-gdelt-news-events.md) | Complete (zipped full week + samples) |
| 05 | Electricity prices & grid context | [05-electricity-prices/](05-electricity-prices/) | [dataset-05-electricity-prices.md](dataset-05-electricity-prices.md) | Complete (ENTSO-E 15-min prices/load/generation/flows; day-ahead prices, 6 zones) |
| 06 | Weather observations | [06-weather/](06-weather/) | [dataset-06-weather.md](dataset-06-weather.md) | 100 MB sample (first hours of Nov 8); full ~3 GB regenerated via scripts |
| 07 | Climate / emissions exposure | — | [dataset-07-climate-emissions-exposure.md](dataset-07-climate-emissions-exposure.md) | **Planned — no data yet** (sketch only) |

## Conventions

- Directories are numbered `01`–`0N`; the number is stable and used in docs and pipelines.
- Small full datasets are committed directly; larger ones are committed as `.zip`
  or regenerated with the scripts included in the dataset directory.
- Every large file has a small `*_sample100.csv` companion committed in plain text
  for quick inspection and smoke tests.
- All files are raw bronze data: file-specific quirks (comment headers, sparse
  columns, sentinel values, mixed timezones) are preserved on purpose and handled
  in the silver layer.

## Timezone Summary

| Dataset | Timestamp semantics |
|---|---|
| 01 DEBS ticks | Naive local time, CET (UTC+1); separate `Date` and `Time` columns |
| 03 Fundamentals | Dates only (period end, filing/publication date) |
| 04 GDELT | Publication **date** only (`YYYYMMDD`, UTC days); no intra-day time in GKG 1.0 |
| 05 Electricity | Timezone-aware Europe/Berlin (`+01:00`); day-ahead file also has explicit UTC |
| 06 Weather | Naive UTC |

## Integration Goal

The ELT workload normalizes timestamps to UTC, resolves identifiers
(DEBS symbol ↔ ISIN ↔ ticker ↔ company ↔ LEI), classifies companies and
sectors, aligns market ticks with context signals, and produces integrated
silver tables ([../silver/](../silver/README.md)) and gold-level dashboards
state ([../docs/gold-schema.md](../docs/gold-schema.md)).
