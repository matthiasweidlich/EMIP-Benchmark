# Climate Finance Streaming Benchmark Sample Dataset

This folder contains a small pre-ETL sample dataset for a streaming benchmark inspired by a climate-finance market intelligence company.

The scenario combines a high-volume European market tick stream with public data sources that enrich stock-price prediction, dashboard queries, materialized views, and ETL workloads.

## Files

| File | Source Part | Purpose |
|---|---|---|
| [dataset-01-debs-tick-stream.md](dataset-01-debs-tick-stream.md) | Market stream | Raw trading ticks before feature extraction |
| [dataset-02-company-security-mapping.md](dataset-02-company-security-mapping.md) | Entity mapping | Raw identifier mappings across symbols, ISINs, LEIs, and names |
| [dataset-03-company-fundamentals-filings.md](dataset-03-company-fundamentals-filings.md) | Fundamentals | Raw filing/fundamental facts before normalization |
| [dataset-04-gdelt-news-events.md](dataset-04-gdelt-news-events.md) | News/events | Raw event and text signals before company/entity resolution |
| [dataset-05-eia-energy-context.md](dataset-05-eia-energy-context.md) | Energy context | Raw energy-market indicators before alignment with companies/sectors |
| [dataset-06-climate-emissions-exposure.md](dataset-06-climate-emissions-exposure.md) | Climate exposure | Raw facility/source emissions before owner resolution |

## Integration Goal

The ETL workload should normalize timestamps, resolve identifiers, classify companies and sectors, align market ticks with context signals, and produce integrated tables such as:

- `instrument_live_features`
- `company_profile`
- `company_news_signal`
- `company_transition_exposure`
- `prediction_feature_store`
- `sector_market_state`
