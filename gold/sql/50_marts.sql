-- Cross-dataset marts: what dashboards read with single scans.
SET TimeZone = 'UTC';

-- Per-instrument 15-min closes/returns (aligned to the energy grid).
CREATE OR REPLACE TEMP VIEW _eq_15min AS
WITH b AS (
    SELECT instrument_id, sec_type,
           time_bucket(INTERVAL 15 MINUTE, bucket_start) AS ts_utc,
           arg_max(close, bucket_start) FILTER (close IS NOT NULL) AS close,
           sum(volume_delta) AS volume_delta,
           sum(tick_count) AS tick_count,
           sum(trade_tick_count) AS trade_tick_count,
           avg(spread_bps_avg) AS spread_bps_avg
    FROM gold.fact_market_bar
    GROUP BY 1, 2, 3)
SELECT *,
       close / nullif(lag(close IGNORE NULLS)
           OVER (PARTITION BY instrument_id ORDER BY ts_utc), 0) - 1 AS return_15min
FROM b;

-- Reference index per exchange: the index instrument with the most price ticks.
CREATE OR REPLACE TEMP VIEW _ref_index AS
SELECT i.exchange_code,
       arg_max(d.instrument_id, d.trade_tick_count) AS instrument_id
FROM (SELECT instrument_id, sum(trade_tick_count) AS trade_tick_count
      FROM gold.fact_instrument_day GROUP BY 1) d
JOIN gold.dim_instrument i USING (instrument_id)
WHERE i.sec_type = 'I'
GROUP BY 1;

-- mart_zone_pulse: zone x 15 min, energy + weather + market side by side.
CREATE OR REPLACE TABLE gold.mart_zone_pulse AS
WITH mkt AS (
    SELECT i.exchange_code, e.ts_utc,
           median(e.return_15min) AS eq_return_median,
           count(*) FILTER (e.return_15min > 0) AS eq_movers_up,
           count(*) FILTER (e.return_15min < 0) AS eq_movers_down,
           sum(e.volume_delta) AS eq_volume,
           sum(e.tick_count) AS eq_tick_count,
           avg(e.spread_bps_avg) AS eq_spread_bps_avg
    FROM _eq_15min e
    JOIN gold.dim_instrument i USING (instrument_id)
    WHERE e.sec_type = 'E'
    GROUP BY 1, 2),
idx AS (
    SELECT r.exchange_code, e.ts_utc,
           e.close AS index_level, e.return_15min AS index_return
    FROM _eq_15min e
    JOIN _ref_index r USING (instrument_id))
SELECT en.*,
       w.temp_avg_c, w.temp_min_c, w.temp_max_c, w.humidity_avg_pct, w.sensor_count,
       z.exchange_code,
       ix.index_level, ix.index_return,
       m.eq_return_median, m.eq_movers_up, m.eq_movers_down,
       m.eq_volume, m.eq_tick_count, m.eq_spread_bps_avg
FROM gold.fact_energy_15min en
LEFT JOIN gold.fact_weather_15min w USING (bidding_zone, ts_utc)
LEFT JOIN gold.dim_zone z USING (bidding_zone)
LEFT JOIN idx ix ON ix.exchange_code = z.exchange_code AND ix.ts_utc = en.ts_utc
LEFT JOIN mkt m ON m.exchange_code = z.exchange_code AND m.ts_utc = en.ts_utc;

-- mart_sector_day: sector x trading day, market aggregates + news signal.
CREATE OR REPLACE TABLE gold.mart_sector_day AS
WITH sector_mkt AS (
    SELECT i.sector, d.trading_day,
           count(DISTINCT d.instrument_id) AS instruments,
           median(d.day_return) AS return_median,
           avg(d.day_return) AS return_avg,
           avg(d.bar_return_stddev) AS volatility_avg,
           sum(d.day_volume) AS volume_sum,
           sum(d.trade_tick_count) AS trade_tick_count
    FROM gold.fact_instrument_day d
    JOIN gold.dim_instrument i USING (instrument_id)
    WHERE i.sector IS NOT NULL AND d.sec_type = 'E'
    GROUP BY 1, 2),
sector_news AS (
    SELECT i.sector, n.publication_date AS trading_day,
           sum(n.doc_count) AS news_doc_count,
           avg(n.tone_avg) AS news_tone_avg,
           sum(n.conflict_event_count) AS news_conflict_events
    FROM gold.fact_company_news_day n
    JOIN (SELECT DISTINCT company_id, sector FROM gold.dim_instrument
          WHERE sector IS NOT NULL) i USING (company_id)
    GROUP BY 1, 2)
SELECT coalesce(m.sector, n.sector) AS sector,
       coalesce(m.trading_day, n.trading_day) AS trading_day,
       m.instruments, m.return_median, m.return_avg, m.volatility_avg,
       m.volume_sum, m.trade_tick_count,
       n.news_doc_count, n.news_tone_avg, n.news_conflict_events
FROM sector_mkt m
FULL JOIN sector_news n ON m.sector = n.sector AND m.trading_day = n.trading_day;

-- mart_company_profile: one wide current-state row per company.
CREATE OR REPLACE TABLE gold.mart_company_profile AS
WITH px AS (
    SELECT d.instrument_id,
           arg_max(d.close, d.trading_day) FILTER (d.close IS NOT NULL) AS last_close,
           arg_max(d.day_return, d.trading_day) FILTER (d.day_return IS NOT NULL) AS last_day_return,
           arg_max(d.close, d.trading_day) FILTER (d.close IS NOT NULL)
               / nullif(arg_min(d.open, d.trading_day) FILTER (d.open IS NOT NULL), 0) - 1 AS week_return,
           avg(d.bar_return_stddev) AS volatility_avg,
           sum(d.day_volume) AS week_volume,
           sum(d.tick_count) AS tick_count,
           max(d.last_event_time_utc) AS last_tick_time_utc
    FROM gold.fact_instrument_day d
    GROUP BY 1),
news AS (
    SELECT company_id,
           sum(doc_count) AS news_docs,
           sum(mention_count) AS news_mentions,
           avg(tone_avg) AS news_tone_avg,
           count(DISTINCT publication_date) AS news_days
    FROM gold.fact_company_news_day
    GROUP BY 1),
fx AS (
    SELECT company_id,
           max(value) FILTER (metric = 'revenue') AS revenue,
           any_value(unit) FILTER (metric = 'revenue') AS revenue_unit,
           max(value) FILTER (metric = 'net_income') AS net_income,
           max(value) FILTER (metric = 'total_assets') AS total_assets,
           max(value) FILTER (metric = 'total_equity') AS total_equity,
           max(value) FILTER (metric = 'eps_basic') AS eps_basic,
           max(period_end) AS fundamentals_period_end
    FROM gold.fact_fundamentals_latest
    GROUP BY 1)
SELECT c.company_id, c.lei, c.company_name, c.sector, c.industry, c.country,
       c.city, c.website, c.currency, c.market_cap_today, c.employees_today,
       c.primary_instrument_id, c.listings,
       px.last_close, px.last_day_return, px.week_return, px.volatility_avg,
       px.week_volume, px.tick_count, px.last_tick_time_utc,
       n.news_docs, n.news_mentions, n.news_tone_avg, n.news_days,
       fx.revenue, fx.revenue_unit, fx.net_income, fx.total_assets,
       fx.total_equity, fx.eps_basic, fx.fundamentals_period_end,
       (fx.company_id IS NOT NULL) AS has_fundamentals,
       (n.company_id IS NOT NULL) AS has_news,
       (c.sector IS NOT NULL) AS has_sector
FROM gold.dim_company c
LEFT JOIN px ON px.instrument_id = c.primary_instrument_id
LEFT JOIN news n USING (company_id)
LEFT JOIN fx USING (company_id);
