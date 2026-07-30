-- Market facts: 5-minute bars and daily instrument summaries.
-- Trading day is the CET calendar date (UTC+1 during the benchmark week).
SET TimeZone = 'UTC';

CREATE OR REPLACE TABLE gold.fact_market_bar AS
WITH base AS (
    SELECT instrument_id, sec_type,
           time_bucket(INTERVAL 5 MINUTE, event_time_utc) AS bucket_start,
           count(*) AS tick_count,
           count(last) AS trade_tick_count,
           count(*) FILTER (bid IS NOT NULL OR ask IS NOT NULL) AS quote_tick_count,
           arg_min(last, event_time_utc) FILTER (last IS NOT NULL) AS open,
           max(last) AS high,
           min(last) AS low,
           arg_max(last, event_time_utc) FILTER (last IS NOT NULL) AS close,
           arg_max(bid, event_time_utc) FILTER (bid IS NOT NULL) AS close_bid,
           arg_max(ask, event_time_utc) FILTER (ask IS NOT NULL) AS close_ask,
           avg((ask - bid) / nullif((ask + bid) / 2, 0) * 10000)
           FILTER (ask IS NOT NULL AND bid IS NOT NULL AND ask >= bid) AS spread_bps_avg,
           max(total_volume) AS volume_cum,
           max(event_time_utc) AS last_event_time_utc
    FROM silver.market_tick
    GROUP BY 1, 2, 3)
SELECT *,
       -- return vs previous bar with a close; spans overnight gaps at day borders
       close / nullif(lag(close IGNORE NULLS) OVER w, 0) - 1 AS bar_return,
       -- Total volume is cumulative per trading day; delta vs previous bar
       volume_cum - lag(volume_cum IGNORE NULLS)
           OVER (PARTITION BY instrument_id, CAST(bucket_start + INTERVAL 1 HOUR AS DATE)
                 ORDER BY bucket_start) AS volume_delta
FROM base
WINDOW w AS (PARTITION BY instrument_id ORDER BY bucket_start);

CREATE OR REPLACE TABLE gold.fact_instrument_day AS
WITH day_agg AS (
    SELECT instrument_id,
           any_value(sec_type) AS sec_type,
           CAST(bucket_start + INTERVAL 1 HOUR AS DATE) AS trading_day,
           arg_min(open, bucket_start) FILTER (open IS NOT NULL) AS open,
           max(high) AS high,
           min(low) AS low,
           arg_max(close, bucket_start) FILTER (close IS NOT NULL) AS close,
           stddev_samp(bar_return) AS bar_return_stddev,
           max(volume_cum) AS day_volume,
           sum(tick_count) AS tick_count,
           sum(trade_tick_count) AS trade_tick_count,
           sum(quote_tick_count) AS quote_tick_count,
           avg(spread_bps_avg) AS spread_bps_avg,
           max(last_event_time_utc) AS last_event_time_utc
    FROM gold.fact_market_bar
    GROUP BY instrument_id, trading_day)
SELECT *, close / nullif(open, 0) - 1 AS day_return
FROM day_agg;
