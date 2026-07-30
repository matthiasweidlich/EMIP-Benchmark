-- Gold dimensions: thin, conformed, static for a benchmark run.
SET TimeZone = 'UTC';
CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.dim_zone AS
SELECT z.bidding_zone, z.country_codes, z.timezone,
       e.exchange_code, e.mic, e.exchange_name
FROM silver.zone_region_map z
LEFT JOIN silver.exchange e USING (bidding_zone);

CREATE OR REPLACE TABLE gold.dim_instrument AS
SELECT i.instrument_id, i.sec_type, i.exchange_code, i.isin, i.yahoo_ticker,
       i.instrument_name, i.quote_type, i.resolution_status, i.company_id,
       c.sector, c.industry
FROM silver.instrument i
LEFT JOIN silver.company c USING (company_id);

-- Primary listing per company: the instrument with the most tick traffic.
CREATE OR REPLACE TABLE gold.dim_company AS
WITH traffic AS (
    SELECT i.company_id, t.instrument_id, count(*) AS n
    FROM silver.market_tick t
    JOIN silver.instrument i ON i.instrument_id = t.instrument_id
    WHERE i.company_id IS NOT NULL
    GROUP BY 1, 2),
    prim AS (
    SELECT company_id, arg_max(instrument_id, n) AS primary_instrument_id
    FROM traffic GROUP BY 1)
SELECT c.*, p.primary_instrument_id,
       (SELECT list(i.instrument_id ORDER BY i.instrument_id)
        FROM silver.instrument i WHERE i.company_id = c.company_id) AS listings
FROM silver.company c
LEFT JOIN prim p USING (company_id);

CREATE OR REPLACE TABLE gold.dim_sector AS
SELECT * FROM silver.sector;
