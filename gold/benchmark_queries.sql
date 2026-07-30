-- EMIP benchmark queries over the silver/gold layers.
-- Six queries, one per workload class (see docs/some-interesting-queries.md
-- and the DEBS 2022 Grand Challenge, arXiv:2206.13237). Each is a plain
-- SELECT against silver/emip.duckdb. Run all: gold/run_benchmark_queries.sh
-- Note: the runner splits statements on the semicolon character, so keep
-- comments free of it.

-- B1 DEBS Grand Challenge, batch edition (recursion + pattern + top-N).
-- Query 1: EMA-38/100 per symbol over 5-min windows via the GC recurrence
-- EMA_i = close_i * 2/(1+j) + EMA_{i-1} * (1 - 2/(1+j)) as a recursive CTE
-- over all ~5k symbols. Query 2: crossover buy/sell advisories, reported as
-- the GC's "last three advice events" for the subscribed set (here: the
-- energy & utilities basket). One deviation from the GC spec: it defines
-- EMA_0 = 0, which over a two-day replay keeps the fast EMA above the slow
-- one nearly everywhere (both are still warming up from zero), so we seed
-- both EMAs with the first close and crossings mark real trend reversals.
WITH RECURSIVE bars AS (
    SELECT instrument_id, bucket_start, close,
           row_number() OVER (PARTITION BY instrument_id ORDER BY bucket_start) AS seq
    FROM gold.fact_market_bar
    WHERE close IS NOT NULL
), ema AS (
    SELECT instrument_id, seq, bucket_start, close,
           close AS ema38, close AS ema100
    FROM bars WHERE seq = 1
    UNION ALL
    SELECT b.instrument_id, b.seq, b.bucket_start, b.close,
           b.close * (2 / 39.0)  + e.ema38  * (1 - 2 / 39.0),
           b.close * (2 / 101.0) + e.ema100 * (1 - 2 / 101.0)
    FROM ema e JOIN bars b ON b.instrument_id = e.instrument_id AND b.seq = e.seq + 1
), crossings AS (
    SELECT *, lag(ema38)  OVER w AS prev38, lag(ema100) OVER w AS prev100
    FROM ema WINDOW w AS (PARTITION BY instrument_id ORDER BY seq)
), advice AS (
    SELECT instrument_id, bucket_start,
           CASE WHEN ema38 > ema100 THEN 'buy' ELSE 'sell' END AS advice,
           round(ema38, 4) AS ema38, round(ema100, 4) AS ema100
    FROM crossings
    WHERE (ema38 > ema100 AND prev38 <= prev100)
       OR (ema38 < ema100 AND prev38 >= prev100)
), subscribed AS (
    SELECT i.instrument_id, c.company_name
    FROM gold.dim_instrument i JOIN gold.dim_company c USING (company_id)
    WHERE c.sector IN ('Energy', 'Utilities')
)
SELECT s.company_name, a.*
FROM advice a JOIN subscribed s USING (instrument_id)
QUALIFY row_number() OVER (PARTITION BY a.instrument_id
                           ORDER BY a.bucket_start DESC) <= 3
ORDER BY s.company_name, a.bucket_start;

-- B2 Top-K movers, last 30 minutes (windowed top-N + dimension chain).
-- Dashboard-refresh query: percent move from the first to the last traded
-- price in the lookback window ending at the reference time, top 10 per
-- exchange by magnitude, resolved to company name and sector.
WITH params AS (SELECT TIMESTAMP '2021-11-09 15:00' AS ref_time),
moves AS (
    SELECT i.exchange_code, m.instrument_id,
           arg_min(m.close, m.bucket_start) AS price_from,
           arg_max(m.close, m.bucket_start) AS price_to,
           sum(m.trade_tick_count) AS trades
    FROM gold.fact_market_bar m
    JOIN gold.dim_instrument i USING (instrument_id), params p
    WHERE i.sec_type = 'E' AND m.close IS NOT NULL
      AND m.bucket_start > p.ref_time - INTERVAL 30 MINUTE
      AND m.bucket_start <= p.ref_time
    GROUP BY 1, 2
    HAVING count(*) >= 3
)
SELECT v.exchange_code, v.instrument_id, c.company_name, c.sector,
       round(100 * (v.price_to / v.price_from - 1), 2) AS move_pct, v.trades
FROM moves v
JOIN gold.dim_instrument i USING (instrument_id)
LEFT JOIN gold.dim_company c USING (company_id)
QUALIFY row_number() OVER (PARTITION BY v.exchange_code
                           ORDER BY abs(v.price_to / v.price_from - 1) DESC) <= 10
ORDER BY v.exchange_code, move_pct DESC;

-- B3 Power-spike event study (the trap: five sources, market-hours logic).
-- Detect day-ahead price spikes per bidding zone (rolling 24h z-score),
-- collapse to episodes, then measure the median reaction of the zone
-- exchange's energy & utilities equities vs all other sectors - intraday
-- (next hour) when the market is open, otherwise as the overnight gap
-- (last close before vs first price after). Weather and news tone at the
-- event complete the picture. Spikes outside tick coverage surface as
-- rows with no reaction - deliberately.
WITH exch_zone(exchange_code, bidding_zone) AS (
    VALUES ('ETR', 'DE-LU'), ('FR', 'FR'), ('NL', 'NL')
), priced AS (
    SELECT bidding_zone, ts_utc, price_eur_mwh,
           (price_eur_mwh - avg(price_eur_mwh) OVER w) / stddev_samp(price_eur_mwh) OVER w AS z,
           count(*) OVER w AS n24
    FROM gold.fact_energy_15min
    WINDOW w AS (PARTITION BY bidding_zone ORDER BY ts_utc
                 ROWS BETWEEN 96 PRECEDING AND 1 PRECEDING)
), episodes AS (
    SELECT bidding_zone, ts_utc, price_eur_mwh, z
    FROM (SELECT *, lag(ts_utc) OVER (PARTITION BY bidding_zone ORDER BY ts_utc) AS prev
          FROM priced WHERE z > 1.75 AND n24 >= 48)
    WHERE prev IS NULL OR ts_utc - prev > INTERVAL 1 HOUR
), bounds AS (
    SELECT *,
           CASE WHEN CAST(ts_utc AS TIME) BETWEEN TIME '08:00' AND TIME '15:30'
                THEN 'intraday' ELSE 'overnight' END AS kind,
           CASE WHEN CAST(ts_utc AS TIME) < TIME '08:00'
                THEN CAST(ts_utc AS DATE) - 1 ELSE CAST(ts_utc AS DATE) END AS pre_day,
           CASE WHEN CAST(ts_utc AS TIME) < TIME '08:00'
                THEN CAST(ts_utc AS DATE) ELSE CAST(ts_utc AS DATE) + 1 END AS post_day
    FROM episodes
), windows AS (
    SELECT bidding_zone, ts_utc, price_eur_mwh, z, kind,
           CASE kind WHEN 'intraday' THEN ts_utc - INTERVAL 1 HOUR
                     ELSE pre_day + TIME '15:00' END AS pre_lo,
           CASE kind WHEN 'intraday' THEN ts_utc
                     ELSE pre_day + TIME '16:30' END AS pre_hi,
           CASE kind WHEN 'intraday' THEN ts_utc
                     ELSE post_day + TIME '08:00' END AS post_lo,
           CASE kind WHEN 'intraday' THEN ts_utc + INTERVAL 1 HOUR
                     ELSE post_day + TIME '09:00' END AS post_hi
    FROM bounds
), reaction AS (
    SELECT w.bidding_zone, w.ts_utc, w.kind,
           CASE WHEN c.sector IN ('Energy', 'Utilities')
                THEN 'energy_utilities' ELSE 'other_sectors' END AS grp,
           m.instrument_id,
           arg_max(m.close, m.bucket_start)
               FILTER (m.bucket_start BETWEEN w.pre_lo AND w.pre_hi) AS close_pre,
           CASE w.kind WHEN 'intraday'
                THEN arg_max(m.close, m.bucket_start)
                     FILTER (m.bucket_start > w.post_lo AND m.bucket_start <= w.post_hi)
                ELSE arg_min(m.close, m.bucket_start)
                     FILTER (m.bucket_start >= w.post_lo AND m.bucket_start <= w.post_hi)
           END AS close_post
    FROM windows w
    JOIN exch_zone x USING (bidding_zone)
    JOIN gold.dim_instrument i
      ON i.exchange_code = x.exchange_code AND i.sec_type = 'E'
    JOIN gold.dim_company c USING (company_id)
    JOIN gold.fact_market_bar m
      ON m.instrument_id = i.instrument_id AND m.close IS NOT NULL
     AND m.bucket_start BETWEEN w.pre_lo AND w.post_hi
    WHERE c.sector IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5
), reacted AS (
    SELECT bidding_zone, ts_utc, grp,
           count(*) FILTER (close_pre IS NOT NULL AND close_post IS NOT NULL) AS stocks,
           round(100 * median(close_post / close_pre - 1), 3) AS median_ret_pct
    FROM reaction GROUP BY 1, 2, 3
)
SELECT w.bidding_zone, w.ts_utc AS spike_utc, round(w.price_eur_mwh) AS eur_mwh,
       round(w.z, 2) AS z, w.kind,
       round(we.temp_avg_c, 1) AS temp_c, round(n.tone_avg, 2) AS energy_news_tone,
       coalesce(r.grp, CASE WHEN w.bidding_zone IN ('DE-LU', 'FR', 'NL')
                            THEN '(no tick coverage)'
                            ELSE '(zone has no DEBS exchange)' END) AS grp,
       r.stocks, r.median_ret_pct
FROM windows w
LEFT JOIN reacted r ON r.bidding_zone = w.bidding_zone AND r.ts_utc = w.ts_utc
LEFT JOIN gold.fact_weather_15min we
       ON we.bidding_zone = w.bidding_zone AND we.ts_utc = w.ts_utc
LEFT JOIN gold.fact_topic_news_day n
       ON n.publication_date = CAST(w.ts_utc AS DATE) AND n.topic = 'ENERGY_GENERAL'
ORDER BY w.ts_utc, w.bidding_zone, grp;

-- B4 Daily cross-domain sector scorecard (pre-aggregate then join).
-- Four fact sources at four natural grains (per-instrument-day ticks,
-- per-company-day news, 15-min electricity, 15-min weather) pre-aggregated
-- in CTEs and joined through the sector/exchange dimension chain without
-- fan-out. One row per (trading day, exchange, sector).
WITH exch_zone(exchange_code, bidding_zone) AS (
    VALUES ('ETR', 'DE-LU'), ('FR', 'FR'), ('NL', 'NL')
), mkt AS (
    SELECT d.trading_day, i.exchange_code, c.sector,
           count(DISTINCT d.instrument_id) AS instruments,
           round(100 * median(d.day_return), 3) AS ret_median_pct,
           sum(d.trade_tick_count) AS trades
    FROM gold.fact_instrument_day d
    JOIN gold.dim_instrument i USING (instrument_id)
    JOIN gold.dim_company c USING (company_id)
    WHERE d.close IS NOT NULL AND c.sector IS NOT NULL
    GROUP BY 1, 2, 3
), news AS (
    SELECT n.publication_date AS trading_day, i.exchange_code, c.sector,
           sum(n.doc_count) AS news_docs, round(avg(n.tone_avg), 2) AS news_tone
    FROM gold.fact_company_news_day n
    JOIN gold.dim_company c USING (company_id)
    JOIN gold.dim_instrument i ON i.instrument_id = c.primary_instrument_id
    GROUP BY 1, 2, 3
), elec AS (
    SELECT CAST(ts_utc AS DATE) AS trading_day, bidding_zone,
           round(avg(price_eur_mwh)) AS power_avg_eur_mwh,
           round(max(price_eur_mwh)) AS power_max_eur_mwh
    FROM gold.fact_energy_15min GROUP BY 1, 2
), wx AS (
    SELECT CAST(ts_utc AS DATE) AS trading_day, bidding_zone,
           round(avg(temp_avg_c), 1) AS temp_c
    FROM gold.fact_weather_15min GROUP BY 1, 2
)
SELECT m.trading_day, m.exchange_code, m.sector, m.instruments,
       m.ret_median_pct, m.trades, n.news_docs, n.news_tone,
       e.power_avg_eur_mwh, e.power_max_eur_mwh, w.temp_c
FROM mkt m
LEFT JOIN news n USING (trading_day, exchange_code, sector)
JOIN exch_zone x USING (exchange_code)
LEFT JOIN elec e ON e.trading_day = m.trading_day AND e.bidding_zone = x.bidding_zone
LEFT JOIN wx w ON w.trading_day = m.trading_day AND w.bidding_zone = x.bidding_zone
WHERE m.sector IN ('Energy', 'Utilities', 'Basic Materials', 'Industrials')
ORDER BY m.trading_day, m.exchange_code, m.sector;

-- B5 As-of join: every utility trade tick priced against the electricity
-- price in effect at that moment (correlated LATERAL, the planner-hostile
-- non-equi pattern - DuckDB also offers native ASOF JOIN as a variant),
-- then aggregated to a per-company correlation between its trade prices
-- and the concurrent power price. Level correlation over two days - a
-- join-pattern showcase, not an econometric claim.
WITH exch_zone(exchange_code, bidding_zone) AS (
    VALUES ('ETR', 'DE-LU'), ('FR', 'FR'), ('NL', 'NL')
), utility_ticks AS (
    SELECT t.instrument_id, t.event_time_utc, t.last AS trade_price,
           x.bidding_zone, c.company_name
    FROM silver.market_tick t
    JOIN gold.dim_instrument i ON i.instrument_id = t.instrument_id
    JOIN gold.dim_company c USING (company_id)
    JOIN exch_zone x ON x.exchange_code = i.exchange_code
    WHERE c.sector = 'Utilities' AND t.last IS NOT NULL
)
SELECT u.company_name, u.bidding_zone, count(*) AS trade_ticks,
       round(corr(u.trade_price, p.price_eur_mwh), 3) AS corr_stock_vs_power
FROM utility_ticks u,
     LATERAL (SELECT e.price_eur_mwh
              FROM gold.fact_energy_15min e
              WHERE e.bidding_zone = u.bidding_zone AND e.ts_utc <= u.event_time_utc
              ORDER BY e.ts_utc DESC LIMIT 1) p
GROUP BY 1, 2
HAVING count(*) >= 200
ORDER BY abs(corr_stock_vs_power) DESC
LIMIT 10;

-- B6 News-shock event study (news as the event driver, fundamentals as
-- conditioning - together with B1-B5 this completes dataset coverage).
-- A shock is a (company, day) whose news pressure is unusual for that
-- company - mention volume well above its own average, or strongly
-- negative tone. The reaction is the close-to-close abnormal return
-- (company minus sector median) the same day and the next trading day:
-- GDELT GKG 1.0 is date-granular, so day-grain windows are the honest
-- finest resolution. Fundamentals enter as a leverage bucket
-- (equity/assets from the latest pre-week ESEF filing).
WITH pressure AS (
    SELECT company_id, publication_date AS day, doc_count, tone_avg,
           conflict_event_count,
           doc_count / avg(doc_count) OVER (PARTITION BY company_id) AS news_ratio
    FROM gold.fact_company_news_day
), shocks AS (
    SELECT * FROM pressure
    WHERE doc_count >= 2 AND (news_ratio >= 1.5 OR tone_avg <= -2)
), leverage AS (
    SELECT company_id,
           max(value) FILTER (metric = 'total_equity')
               / nullif(max(value) FILTER (metric = 'total_assets'), 0) AS equity_ratio
    FROM gold.fact_fundamentals_latest
    GROUP BY 1
), comp_ret AS (
    SELECT c.company_id, c.sector, d.trading_day, d.day_return
    FROM gold.dim_company c
    JOIN gold.fact_instrument_day d ON d.instrument_id = c.primary_instrument_id
    WHERE d.day_return IS NOT NULL AND c.sector IS NOT NULL
), abnormal AS (
    SELECT company_id, trading_day, abn_ret,
           lead(abn_ret) OVER (PARTITION BY company_id ORDER BY trading_day) AS abn_ret_next
    FROM (SELECT r.company_id, r.trading_day,
                 r.day_return - median(r.day_return)
                     OVER (PARTITION BY r.sector, r.trading_day) AS abn_ret
          FROM comp_ret r)
)
SELECT c.company_name, c.sector, s.day, s.doc_count,
       round(s.news_ratio, 2) AS news_ratio, round(s.tone_avg, 2) AS tone,
       s.conflict_event_count AS conflict_events,
       CASE WHEN l.equity_ratio IS NULL THEN '(no fundamentals)'
            WHEN l.equity_ratio < 0.35 THEN 'high leverage'
            ELSE 'low/mid leverage' END AS leverage_bucket,
       round(100 * a.abn_ret, 3) AS abn_ret_pct,
       round(100 * a.abn_ret_next, 3) AS abn_ret_next_pct
FROM shocks s
JOIN gold.dim_company c USING (company_id)
LEFT JOIN leverage l USING (company_id)
LEFT JOIN abnormal a ON a.company_id = s.company_id AND a.trading_day = s.day
ORDER BY s.day, s.news_ratio DESC;
