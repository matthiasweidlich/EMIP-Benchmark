-- Cleaned, typed tick stream. Event time normalized CET -> UTC.
SET TimeZone = 'UTC';
-- Rows without a parseable event time go to silver.market_tick_rejects.

CREATE OR REPLACE TEMP VIEW _tick_parsed AS
SELECT ID AS instrument_id,
       SecType AS sec_type,
       try_strptime("Date" || ' ' || "Time", '%d-%m-%Y %H:%M:%S.%g') AS event_time_local,
       try_strptime("Trading date" || ' ' || "Trading time", '%d-%m-%Y %H:%M:%S.%g') AS trading_time_local,
       try_strptime("Trading date", '%d-%m-%Y') AS trading_date,
       Currency AS currency_raw,
       CASE WHEN Currency = 'XXP' THEN 0.01 ELSE 1.0 END AS price_scale,
       CASE WHEN Currency = 'XXP' THEN 'GBP' ELSE Currency END AS currency,
       try_cast(Bid AS DOUBLE) AS bid,
       try_cast("Bid volume" AS DOUBLE) AS bid_volume,
       try_cast(Ask AS DOUBLE) AS ask,
       try_cast("Ask volume" AS DOUBLE) AS ask_volume,
       try_cast(Last AS DOUBLE) AS last,
       try_cast("Last volume" AS DOUBLE) AS last_volume,
       try_cast("Total volume" AS DOUBLE) AS total_volume,
       try_cast("Mid price" AS DOUBLE) AS mid_price,
       try_cast("Open" AS DOUBLE) AS open,
       try_cast("Close" AS DOUBLE) AS close,
       try_cast("Day's high" AS DOUBLE) AS day_high,
       try_cast("Day's low" AS DOUBLE) AS day_low,
       nullif(ISIN, '') AS isin,
       filename AS source_file,
       row_number() OVER () AS source_row
FROM bronze.market_tick;

-- CET = UTC+1 constantly during 2021-11-08..14 (no DST transition in window).
CREATE OR REPLACE TABLE silver.market_tick AS
SELECT instrument_id, sec_type,
       event_time_local - INTERVAL 1 HOUR AS event_time_utc,
       trading_time_local - INTERVAL 1 HOUR AS trading_time_utc,
       trading_date,
       bid * price_scale AS bid,
       bid_volume,
       ask * price_scale AS ask,
       ask_volume,
       last * price_scale AS last,
       last_volume,
       total_volume,
       mid_price * price_scale AS mid_price,
       open * price_scale AS open,
       close * price_scale AS close,
       day_high * price_scale AS day_high,
       day_low * price_scale AS day_low,
       currency, currency_raw, isin, source_file, source_row
FROM _tick_parsed
WHERE event_time_local IS NOT NULL;

CREATE OR REPLACE TABLE silver.market_tick_rejects AS
SELECT *, 'unparseable event time' AS reject_reason
FROM _tick_parsed
WHERE event_time_local IS NULL;
