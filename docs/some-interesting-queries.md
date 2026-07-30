# Windowed aggregation / materialized-view maintenance
  - 1-minute OHLCV bars: groups market_tick by instrument and time bucket, computing open/high/low/close, volume, VWAP, and tick count — literally constructing the market_bar table. This is
  the core "materialized view maintenance" workload: high-cardinality windowed aggregation over a high-volume stream.
  - Rolling 30-min volatility: a window function computing stddev of log returns over a time-based (not row-based) frame. Time-range window frames are handled unevenly across engines, and
  this needs continuous incremental recomputation as new ticks land.

# Top-K queries
  - Top 10 movers, last 30 min: window function computing % change from the earliest tick in a lookback window, ranked and limited to the top 10 by magnitude. Representative of a dashboard
  refresh — needs to stay low-latency while ingestion continues.
  - Sector momentum, last hour: averages an already-derived feature column (market_feature.return_value) grouped up through the sector dimension chain. Tests that rollups over derived state
  don't require re-deriving the join at query time.

# Cross-domain temporal joins
  - News-driven price move: joins CAMEO events → documents → ticker mentions → instrument/company, then joins to market_feature within a day-long window after the event, filtered to
  significant Goldstein scores. A genuine time-range join condition, not equality — and a selective predicate that has to push through several join hops.
  - As-of join for electricity price: for each utility-sector tick, finds the most recent electricity price at or before that tick's timestamp via a correlated LATERAL subquery. The classic
  "as-of join" pattern — notoriously awkward for query planners since it can't be expressed as a plain equi-join.

# Event-type impact leaderboard (7-9 relations, self-referential)
  Joins back onto market_tick twice via correlated subqueries — once before a news event, once after — then aggregates the price reaction by sector and CAMEO event type. Tests a before/after
  comparison pattern (two correlated subqueries against the same table with different time predicates) combined with a full dimension-chain join to make results business-meaningful rather
  than per-instrument noise.

# Daily cross-domain sector scorecard (~10-11 relations)
  Pre-aggregates market_tick, news, electricity, and weather into day-grain CTEs, then joins each into the sector/exchange dimension chain and aggregates again by (exchange, sector, day).
  Tests whether an engine handles a genuinely wide multi-fact join without fan-out blowup from the grain mismatch between ticks (intraday), news (per-document), electricity (hourly), and
  weather (per-reading). Also a natural pair for testing "pre-aggregate then join" vs. "join raw then aggregate" query plans.


# Company 360 profile (9 relations)
  Joins company/sector dimensions to the benchmark's own derived tables (market_feature, prediction_label) plus news linkage, grouped by company and week. Tests mixed joins between base fact
  tables and materialized/derived tables in one query — relevant because in a real deployment some of these will be physical tables and others views, and the query has to treat them
  uniformly.

# Core dimensional joins
  - Instrument → company → sector resolution chain: walks the full join path from a traded instrument to its human-readable company name and sector classification. The simplest possible
  correctness check — does the join graph actually resolve end-to-end.
  - Company count / market cap by sector & exchange: aggregates over that same join chain, grouped by exchange and sector. A baseline sanity query before anything harder.

# Feature / label generation
  - market_feature construction: a wide join blending market bars, hourly-aggregated news sentiment, and hourly electricity price into one feature row per instrument per hour. The hard part
  is reconciling mismatched natural grains — tick-level, per-document, and hourly — onto a single hourly grid.
  - Future-return label: a LEAD() window function looking a fixed interval ahead to compute the return actually realized after a given point, for supervised-learning labels. Tests
  forward-looking, time-offset window functions and the "label uses future data, but the feature it's paired with must not" discipline of point-in-time-correct ML pipelines.





