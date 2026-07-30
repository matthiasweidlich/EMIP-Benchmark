-- EMIP-Benchmark: candidate relational queries (DuckDB dialect)
--
-- Assumes the gold-level schema documented in docs/gold-schema.md:
--   exchange, instrument, company, sector, instrument_company, company_sector,
--   market_tick, news_document, news_event_link, news_ticker_mention,
--   electricity_price, weather_observation, market_bar, market_feature,
--   prediction_label
--
-- These queries run against a static historical replay (DEBS week
-- 2021-11-08 .. 2021-11-14), so time-relative predicates use a fixed
-- reference timestamp inside that window instead of now().
--
-- DuckDB-specific idioms used below:
--   - ASOF JOIN / LEFT ASOF JOIN   (point-in-time / as-of joins)
--   - arg_min(x, y) / arg_max(x, y) (value of x at the extreme of y)
--   - FILTER (WHERE ...) on aggregates
--   - RANGE BETWEEN INTERVAL ... window frames


-- =====================================================================
-- 1. Core dimensional joins
-- =====================================================================

-- 1a. instrument -> company -> sector resolution chain
SELECT i.instrument_id, i.debs_symbol, c.short_name, s.sector_name, s.industry_name
FROM instrument i
JOIN instrument_company ic ON ic.instrument_id = i.instrument_id
JOIN company c ON c.company_id = ic.company_id
JOIN company_sector cs ON cs.company_id = c.company_id
JOIN sector s ON s.sector_id = cs.sector_id;

-- 1b. company count and market cap by sector, per exchange
SELECT e.exchange_name, s.sector_name, count(*) AS n_companies, sum(c.market_cap) AS total_cap
FROM instrument i
JOIN exchange e ON e.exchange_id = i.exchange_id
JOIN instrument_company ic ON ic.instrument_id = i.instrument_id
JOIN company c ON c.company_id = ic.company_id
JOIN company_sector cs ON cs.company_id = c.company_id
JOIN sector s ON s.sector_id = cs.sector_id
GROUP BY e.exchange_name, s.sector_name
ORDER BY total_cap DESC;


-- =====================================================================
-- 2. ELT / entity-resolution queries
-- =====================================================================

-- 2a. unresolved instruments (no company match)
SELECT i.instrument_id, i.debs_symbol, i.resolution_status
FROM instrument i
LEFT JOIN instrument_company ic ON ic.instrument_id = i.instrument_id
WHERE ic.instrument_id IS NULL;

-- 2b. conflicting ISINs -- run against the pre-dedup silver extract, not the
-- already-deduplicated gold `instrument` table (which is 1 row per instrument)
SELECT debs_symbol, count(DISTINCT isin) AS isin_variants
FROM stg_instrument_raw
GROUP BY debs_symbol
HAVING count(DISTINCT isin) > 1;


-- =====================================================================
-- 3. Windowed aggregation / materialized-view maintenance
-- =====================================================================

-- 3a. 1-minute OHLCV bars, using arg_min/arg_max instead of ordered first()/last()
SELECT
  instrument_id,
  date_trunc('minute', event_time) AS window_start,
  arg_min(last_price, event_time) AS open_price,
  max(last_price) AS high_price,
  min(last_price) AS low_price,
  arg_max(last_price, event_time) AS close_price,
  sum(last_volume) AS volume,
  sum(last_price * last_volume) / nullif(sum(last_volume), 0) AS vwap,
  count(*) AS tick_count
FROM market_tick
GROUP BY instrument_id, date_trunc('minute', event_time)
ORDER BY instrument_id, window_start;

-- 3b. rolling 30-min volatility -- split into two query levels since a window
-- function (lag) can't be nested inside another window function (stddev) directly
WITH returns AS (
  SELECT instrument_id, event_time,
         ln(last_price / lag(last_price) OVER (PARTITION BY instrument_id ORDER BY event_time)) AS log_return
  FROM market_tick
)
SELECT instrument_id, event_time,
       stddev_samp(log_return) OVER (
         PARTITION BY instrument_id ORDER BY event_time
         RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND CURRENT ROW
       ) AS rolling_volatility_30m
FROM returns;


-- =====================================================================
-- 4. Dashboard / top-K queries
-- =====================================================================

-- 4a. top 10 movers in the last 30 minutes (reference point fixed inside the DEBS week)
WITH params AS (SELECT TIMESTAMP '2021-11-12 15:00:00' AS as_of),
recent AS (
  SELECT mt.instrument_id, mt.event_time, mt.last_price
  FROM market_tick mt, params
  WHERE mt.event_time > params.as_of - INTERVAL '30 minutes'
    AND mt.event_time <= params.as_of
)
SELECT instrument_id,
       arg_max(last_price, event_time) / arg_min(last_price, event_time) - 1 AS pct_change
FROM recent
GROUP BY instrument_id
ORDER BY abs(pct_change) DESC
LIMIT 10;

-- 4b. sector momentum over the last hour
SELECT s.sector_name, avg(mf.return_value) AS avg_sector_return
FROM market_feature mf
JOIN instrument_company ic ON ic.instrument_id = mf.instrument_id
JOIN company_sector cs ON cs.company_id = ic.company_id
JOIN sector s ON s.sector_id = cs.sector_id
WHERE mf.feature_time > TIMESTAMP '2021-11-12 15:00:00' - INTERVAL '1 hour'
  AND mf.horizon = '1h'
GROUP BY s.sector_name
ORDER BY avg_sector_return DESC;


-- =====================================================================
-- 5. Cross-domain temporal joins
-- =====================================================================

-- 5a. price move following high-Goldstein energy news events, by company
SELECT c.short_name, nel.global_event_id, nel.goldstein_scale, nel.event_date, mf.return_value
FROM news_event_link nel
JOIN news_document nd ON nd.document_id = nel.document_id
JOIN news_ticker_mention ntm ON ntm.document_id = nd.document_id
JOIN instrument_company ic ON ic.instrument_id = ntm.instrument_id
JOIN company c ON c.company_id = ic.company_id
JOIN market_feature mf ON mf.instrument_id = ic.instrument_id
 AND mf.feature_time BETWEEN nel.event_date AND nel.event_date + INTERVAL '1 day'
WHERE abs(nel.goldstein_scale) > 5;

-- 5b. as-of join: electricity price at time of each utility-sector tick,
-- via DuckDB's native ASOF JOIN
WITH tick_zone AS (
  SELECT mt.instrument_id, mt.event_time, mt.last_price,
         CASE e.country_code WHEN 'FR' THEN 'FR' WHEN 'NL' THEN 'NL' WHEN 'DE' THEN 'DE-LU' END AS bidding_zone
  FROM market_tick mt
  JOIN instrument i ON i.instrument_id = mt.instrument_id
  JOIN exchange e ON e.exchange_id = i.exchange_id
  JOIN instrument_company ic ON ic.instrument_id = i.instrument_id
  JOIN company_sector cs ON cs.company_id = ic.company_id
  JOIN sector s ON s.sector_id = cs.sector_id AND s.sector_name = 'Utilities'
)
SELECT tz.instrument_id, tz.event_time, tz.last_price, ep.price_eur_mwh
FROM tick_zone tz
LEFT ASOF JOIN electricity_price ep
  ON tz.event_time >= ep.timestamp_utc
 AND tz.bidding_zone = ep.bidding_zone
ORDER BY tz.instrument_id, tz.event_time;


-- =====================================================================
-- 6. Alerting queries
-- =====================================================================

-- 6a. spread-widening alert -- split into CTEs since a window-function alias
-- (spread_pct) can't be referenced in the same SELECT's WHERE clause
WITH spreads AS (
  SELECT instrument_id, event_time, (ask_price - bid_price) / mid_price AS spread_pct
  FROM market_tick
  WHERE mid_price > 0
),
with_baseline AS (
  SELECT *,
         avg(spread_pct) OVER (
           PARTITION BY instrument_id ORDER BY event_time
           ROWS BETWEEN 100 PRECEDING AND 1 PRECEDING
         ) AS rolling_avg_spread
  FROM spreads
)
SELECT instrument_id, event_time, spread_pct, rolling_avg_spread
FROM with_baseline
WHERE spread_pct > 1.5 * rolling_avg_spread;

-- 6b. stale feed detection
SELECT instrument_id, max(event_time) AS last_tick
FROM market_tick
GROUP BY instrument_id
HAVING max(event_time) < TIMESTAMP '2021-11-12 15:00:00' - INTERVAL '5 minutes';


-- =====================================================================
-- 7. Data-quality / coverage queries
-- =====================================================================

-- 7a. news documents that fail to resolve to any known instrument
SELECT nd.document_id, nd.source_url
FROM news_document nd
LEFT JOIN news_ticker_mention ntm
  ON ntm.document_id = nd.document_id AND ntm.instrument_id IS NOT NULL
WHERE ntm.document_id IS NULL;

-- 7b. coverage: % of instruments with resolved company + sector
SELECT count(*) FILTER (WHERE cs.sector_id IS NOT NULL) * 1.0 / count(*) AS coverage_pct
FROM instrument i
LEFT JOIN instrument_company ic ON ic.instrument_id = i.instrument_id
LEFT JOIN company_sector cs ON cs.company_id = ic.company_id;


-- =====================================================================
-- 8. Feature / label generation
-- =====================================================================

-- 8a. market_feature construction
SELECT
  mb.instrument_id, mb.window_end AS feature_time,
  mb.close_price, mb.vwap, mb.volume,
  news.news_intensity, news.avg_tone,
  ep.price_eur_mwh
FROM market_bar mb
LEFT JOIN (
  SELECT ntm.instrument_id, date_trunc('hour', nd.publication_date) AS hr,
         count(*) AS news_intensity, avg(nd.tone_avg) AS avg_tone
  FROM news_document nd
  JOIN news_ticker_mention ntm ON ntm.document_id = nd.document_id
  GROUP BY ntm.instrument_id, date_trunc('hour', nd.publication_date)
) news ON news.instrument_id = mb.instrument_id AND news.hr = date_trunc('hour', mb.window_end)
LEFT JOIN electricity_price ep ON ep.timestamp_utc = date_trunc('hour', mb.window_end);

-- 8b. future-return label -- LEAD() can't express a *time*-based offset (row
-- offset only), so this uses a self ASOF JOIN to find "the next tick >= 1 hour
-- later" instead
SELECT t0.instrument_id,
       t0.event_time AS label_time,
       t0.last_price AS reference_price,
       t1.last_price AS future_price,
       t1.last_price / t0.last_price - 1 AS future_return
FROM market_tick t0
LEFT ASOF JOIN market_tick t1
  ON t1.instrument_id = t0.instrument_id
 AND t1.event_time >= t0.event_time + INTERVAL '1 hour';


-- =====================================================================
-- 9. Aggregations over a big join (many relations)
-- =====================================================================

-- 9a. Daily cross-domain sector scorecard
WITH tick_agg AS (
  SELECT instrument_id, trading_date,
    avg(last_price) AS avg_price,
    stddev(last_price) AS price_volatility,
    sum(last_volume) AS total_volume,
    avg((ask_price - bid_price) / nullif(mid_price,0)) AS avg_spread_pct,
    count(*) AS tick_count
  FROM market_tick
  GROUP BY instrument_id, trading_date
),
news_agg AS (
  SELECT ntm.instrument_id, nd.publication_date AS trading_date,
    count(*) AS news_count, avg(nd.tone_avg) AS avg_tone
  FROM news_document nd
  JOIN news_ticker_mention ntm ON ntm.document_id = nd.document_id
  WHERE ntm.instrument_id IS NOT NULL
  GROUP BY ntm.instrument_id, nd.publication_date
),
elec_agg AS (
  SELECT bidding_zone, date_trunc('day', timestamp_utc) AS trading_date,
    avg(price_eur_mwh) AS avg_price_eur_mwh
  FROM electricity_price
  GROUP BY bidding_zone, date_trunc('day', timestamp_utc)
),
weather_agg AS (
  SELECT
    CASE WHEN latitude BETWEEN 41 AND 51 AND longitude BETWEEN -5 AND 9 THEN 'FR'
         WHEN latitude BETWEEN 50 AND 55 AND longitude BETWEEN 3 AND 7  THEN 'NL'
         WHEN latitude BETWEEN 47 AND 55 AND longitude BETWEEN 6 AND 15 THEN 'DE' END AS country_code,
    date_trunc('day', observation_time) AS trading_date,
    avg(temperature_celsius) AS avg_temp_c
  FROM weather_observation
  GROUP BY 1, 2
)
SELECT
  e.exchange_name, s.sector_name, t.trading_date,
  count(DISTINCT t.instrument_id) AS n_instruments,
  avg(t.avg_price) AS sector_avg_price,
  avg(t.price_volatility) AS sector_avg_volatility,
  sum(t.total_volume) AS sector_total_volume,
  avg(t.avg_spread_pct) AS sector_avg_spread,
  sum(n.news_count) AS sector_news_count,
  avg(n.avg_tone) AS sector_avg_tone,
  avg(el.avg_price_eur_mwh) AS avg_electricity_price,
  avg(w.avg_temp_c) AS avg_temperature
FROM tick_agg t
JOIN instrument i ON i.instrument_id = t.instrument_id
JOIN exchange e ON e.exchange_id = i.exchange_id
JOIN instrument_company ic ON ic.instrument_id = i.instrument_id
JOIN company_sector cs ON cs.company_id = ic.company_id
JOIN sector s ON s.sector_id = cs.sector_id
LEFT JOIN news_agg n ON n.instrument_id = t.instrument_id AND n.trading_date = t.trading_date
LEFT JOIN elec_agg el ON el.bidding_zone = e.country_code AND el.trading_date = t.trading_date
LEFT JOIN weather_agg w ON w.country_code = e.country_code AND w.trading_date = t.trading_date
GROUP BY e.exchange_name, s.sector_name, t.trading_date
ORDER BY t.trading_date, sector_avg_volatility DESC;

-- 9b. Company 360 profile
SELECT
  c.short_name, s.sector_name, date_trunc('week', mf.feature_time) AS week,
  avg(mf.return_value) AS avg_weekly_return,
  avg(mf.volatility) AS avg_weekly_volatility,
  avg(mf.news_intensity) AS avg_news_intensity,
  avg(mf.news_tone_avg) AS avg_news_tone,
  avg(mf.energy_event_goldstein_avg) AS avg_goldstein,
  count(DISTINCT nel.global_event_id) AS n_events,
  avg(pl.future_return) FILTER (WHERE pl.horizon = '1d') AS avg_next_day_return
FROM company c
JOIN instrument_company ic ON ic.company_id = c.company_id
JOIN company_sector cs ON cs.company_id = c.company_id
JOIN sector s ON s.sector_id = cs.sector_id
JOIN market_feature mf ON mf.instrument_id = ic.instrument_id
LEFT JOIN prediction_label pl ON pl.instrument_id = ic.instrument_id AND pl.label_time = mf.feature_time
LEFT JOIN news_ticker_mention ntm ON ntm.instrument_id = ic.instrument_id
LEFT JOIN news_document nd ON nd.document_id = ntm.document_id
  AND date_trunc('week', nd.publication_date) = date_trunc('week', mf.feature_time)
LEFT JOIN news_event_link nel ON nel.document_id = nd.document_id
GROUP BY c.short_name, s.sector_name, date_trunc('week', mf.feature_time);

-- 9c. Event-type impact leaderboard
WITH event_window AS (
  SELECT nel.global_event_id, nel.event_root_code, nel.quad_class_name, nel.goldstein_scale,
    ntm.instrument_id, nd.publication_date
  FROM news_event_link nel
  JOIN news_document nd ON nd.document_id = nel.document_id
  JOIN news_ticker_mention ntm ON ntm.document_id = nd.document_id
  WHERE ntm.instrument_id IS NOT NULL
),
price_before_after AS (
  SELECT ew.*,
    (SELECT avg(last_price) FROM market_tick mt
     WHERE mt.instrument_id = ew.instrument_id
       AND mt.event_time BETWEEN ew.publication_date - INTERVAL '1 day' AND ew.publication_date) AS price_before,
    (SELECT avg(last_price) FROM market_tick mt
     WHERE mt.instrument_id = ew.instrument_id
       AND mt.event_time BETWEEN ew.publication_date AND ew.publication_date + INTERVAL '1 day') AS price_after
  FROM event_window ew
)
SELECT
  s.sector_name, pba.event_root_code, pba.quad_class_name,
  count(*) AS n_events,
  avg(pba.goldstein_scale) AS avg_goldstein,
  avg((pba.price_after - pba.price_before) / nullif(pba.price_before,0)) AS avg_price_reaction
FROM price_before_after pba
JOIN instrument_company ic ON ic.instrument_id = pba.instrument_id
JOIN company_sector cs ON cs.company_id = ic.company_id
JOIN sector s ON s.sector_id = cs.sector_id
GROUP BY s.sector_name, pba.event_root_code, pba.quad_class_name
ORDER BY avg_price_reaction DESC;
