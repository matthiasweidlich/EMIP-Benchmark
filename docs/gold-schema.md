# Gold-Level Schema

The gold layer turns the silver tables (see [`../silver/README.md`](../silver/README.md))
into dashboard-ready analytical state: conformed dimensions, time-bucketed
facts, and wide cross-dataset marts that dashboards read with single scans.
It is implemented in [`../gold/sql/`](../gold/sql/) and built with
`gold/build.sh` (full rebuild: silver, then gold, then the smoke queries in
[`../gold/dashboard_queries.sql`](../gold/dashboard_queries.sql)).

## Design Principles

- **Three time grains**, chosen by the sources' native resolutions:
  **5 minutes** for market bars (tick aggregation), **15 minutes** for the
  energy × weather × market correlation plane (ENTSO-E's grid resolution),
  and **daily** for anything involving news (GDELT GKG 1.0 has publication
  dates only).
- **Conformed keys** across all facts: `instrument_id` (DEBS symbol),
  `company_id` (`LEI:` > `ISIN:` > `YH:` preference from silver),
  `sector`, `bidding_zone`, and naive-UTC timestamps.
- **Marts are wide on purpose**: cross-dataset joins happen at build/maintain
  time, so a dashboard query is a scan plus window functions — never a
  five-way join at request time.
- Every table is defined by SQL over silver, so a batch recomputation is the
  correctness oracle for incremental maintenance.

## Dashboards → Tables

| Dashboard | Reads |
|---|---|
| D1 Energy ⇄ market over time (price, renewables share, carbon intensity vs. index/sector movement, rolling correlations) | `mart_zone_pulse`, `mart_rolling_correlation` |
| D2 Weather → load → price (demand curve, temperature sensitivity) | `mart_zone_pulse` |
| D3 News pulse (topic volume/tone vs. sector returns; abnormal news + abnormal return) | `fact_topic_news_day`, `fact_company_news_day`, `mart_sector_day` |
| D4 Company profile (identity, fundamentals, price trend, news, coverage) | `mart_company_profile`, `fact_market_bar` (price sparkline), `fact_company_news_day` |
| D5 Movers & feed health (top movers 5/30 min, staleness, coverage) | `fact_market_bar`, `fact_instrument_day`, `dim_instrument` |

## Dimensions (static per benchmark run)

| Table | Grain | Notes |
|---|---|---|
| `dim_zone` | bidding zone | zone ↔ countries ↔ timezone ↔ exchange (`DE-LU`↔XETR, `FR`↔XPAR, `NL`↔XAMS; AT/BE/CH have no exchange) |
| `dim_instrument` | DEBS symbol | type, exchange, ISIN, Yahoo ticker, resolution status, `company_id`, sector/industry |
| `dim_company` | company | silver company plus `primary_instrument_id` (listing with most tick traffic — makes per-company charts unambiguous for cross-listings) and the full `listings` array |
| `dim_sector` | sector × industry | Yahoo taxonomy |

## Base Facts

| Table | Grain | Content | From |
|---|---|---|---|
| `fact_market_bar` | instrument × 5 min | OHLC from `last`, closing bid/ask, avg spread (bps), tick/trade/quote counts, cumulative and per-bar volume, `bar_return`, last event time | `silver.market_tick` |
| `fact_instrument_day` | instrument × CET trading day | daily OHLC, `day_return`, bar-return volatility, day volume, spread, counts, last event time (staleness) | rollup of bars |
| `fact_energy_15min` | zone × 15 min | day-ahead price, load, generation grouped renewable/fossil/nuclear/other, `renewables_share`, `carbon_intensity_g_kwh` (documented emission factors; fuels without a factor excluded), `net_export_mw` | `silver.electricity_price`, `grid_load/generation/flow` |
| `fact_weather_15min` | zone × 15 min | avg/min/max temperature, avg humidity, sensor and observation counts (coverage) | `silver.weather_observation` (country tag → zone, DE feeds DE-LU) |
| `fact_company_news_day` | company × day | doc/mention counts, tone (avg/min/salience-weighted by `NUMARTS`), linked CAMEO event counts (cooperation vs. conflict), Goldstein avg | `silver.news_ticker_mention` + `news_document` + event link |
| `fact_topic_news_day` | energy topic × day | same signal set per `ENERGY_SECTORS` topic (OIL, WIND, COAL, …) — the statistically dense news signal (49k docs vs. 38 ticker-resolved companies) | `silver.news_document` |
| `fact_fundamentals_latest` | company × metric | latest pre-benchmark-week value with unit and period | `silver.latest_company_fundamentals` |

## Cross-Dataset Marts

### `mart_zone_pulse` — zone × 15 min (the correlation plane)

One row per bidding zone and 15-minute bucket with energy (price, load,
generation mix, renewables share, carbon intensity, net export), weather
(temperature, humidity, sensor coverage), and market columns for the zone's
exchange: reference-index level/return (the index instrument with the most
price ticks per exchange, chosen data-driven), median 15-min equity return,
up/down mover counts, volume, tick count, average spread. D1/D2 are scans of
this table; correlations are `corr()` window functions over it.

### `mart_sector_day` — sector × CET trading day

Market aggregates (median/avg return, avg volatility, volume, trade ticks per
sector) full-joined with the sector's company-news signal (doc count, tone,
conflict events). Cross with `fact_energy_15min` day aggregates by date for
energy-vs-sector charts.

### `mart_company_profile` — one wide current-state row per company

Identity (name, LEI, sector, country, listings, primary instrument), market
block via the primary listing (last close, last day return, week return,
volatility, volume, tick count, last tick time), `market_cap_today`
(present-day Yahoo value — labeled, not Nov 2021), news block (docs,
mentions, tone, active days), fundamentals block (revenue, net income,
assets, equity, EPS with unit and period end), and coverage flags
(`has_fundamentals`, `has_news`, `has_sector`) that double as the
data-quality dashboard input.

### `mart_rolling_correlation` — zone × 15 min × signal pair

24-hour rolling `corr()` (96 buckets, reported at ≥ 48 paired samples) for a
fixed vocabulary of pairs: price↔load, price↔temperature, temperature↔load,
renewables-share↔price, price↔index-return. Cheap to read, expensive to
maintain incrementally — deliberately a hard case for the view-maintenance
workload.

## Update Semantics (benchmark framing)

- Bars, energy, and weather facts append per closed bucket, with a
  late-arrival correction window; daily news facts append per replayed day.
- Marts are incremental joins over those facts; `mart_company_profile` is a
  latest-state upsert; `mart_rolling_correlation` slides its window per
  bucket.
- Dimensions are static for the default run; the optional correction streams
  from the scenario would turn them into slowly changing dimensions.
- Freshness targets and correctness oracles per view family are defined by
  the scenario ([`scenario.md`](scenario.md)); every gold table's oracle is
  its batch SQL definition over silver.

## Known Limits (inherited from bronze)

- News is **day-grain** (GKG 1.0): market×news correlation works daily, not
  intraday, until a GKG 2.1 (15-min) upgrade.
- The committed weekend tick files contain **zero-valued price placeholders**
  only — real OHLC/returns appear under weekday replay (Zenodo files).
  Structure and queries are validated on the Monday sample.
- Weather-to-zone mapping is bounding-box approximate, and the committed
  sample covers only the first hours of Nov 8 (regenerate the full week with
  the dataset scripts for complete coverage).
- Fundamentals exclude German issuers (no open ESEF source); `market_cap_today`
  is present-day, not Nov 2021.
