-- Rolling cross-signal correlations over mart_zone_pulse.
-- 24 h window (96 x 15 min), reported when at least 48 paired samples exist.
SET TimeZone = 'UTC';

CREATE OR REPLACE TABLE gold.mart_rolling_correlation AS
WITH pairs AS (
    SELECT bidding_zone, ts_utc, 'price_vs_load' AS signal_pair,
           price_eur_mwh AS x, load_mw AS y FROM gold.mart_zone_pulse
    UNION ALL
    SELECT bidding_zone, ts_utc, 'price_vs_temperature',
           price_eur_mwh, temp_avg_c FROM gold.mart_zone_pulse
    UNION ALL
    SELECT bidding_zone, ts_utc, 'temperature_vs_load',
           temp_avg_c, load_mw FROM gold.mart_zone_pulse
    UNION ALL
    SELECT bidding_zone, ts_utc, 'renewables_share_vs_price',
           renewables_share, price_eur_mwh FROM gold.mart_zone_pulse
    UNION ALL
    SELECT bidding_zone, ts_utc, 'price_vs_index_return',
           price_eur_mwh, index_return FROM gold.mart_zone_pulse)
SELECT * FROM (
    SELECT bidding_zone, ts_utc, signal_pair,
           corr(x, y) OVER w AS corr_24h,
           count(*) FILTER (x IS NOT NULL AND y IS NOT NULL) OVER w AS samples
    FROM pairs
    WINDOW w AS (PARTITION BY bidding_zone, signal_pair ORDER BY ts_utc
                 ROWS BETWEEN 95 PRECEDING AND CURRENT ROW))
WHERE samples >= 48 AND corr_24h IS NOT NULL;
