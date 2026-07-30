-- Electricity prices (long), grid load, generation by fuel, cross-border flows.
SET TimeZone = 'UTC';

-- Canonical price table: hourly day-ahead auction prices, 6 zones.
CREATE OR REPLACE TABLE silver.electricity_price AS
SELECT CAST(timestamp_utc AS TIMESTAMP) AS ts_utc,
       bidding_zone,
       price_eur_mwh,
       'energy_charts_day_ahead' AS source
FROM bronze.electricity_day_ahead;

-- Actual load, 15-min (FR hourly forward-filled at source).
CREATE OR REPLACE TABLE silver.grid_load AS
SELECT CAST(timestamp_berlin AS TIMESTAMP) AS ts_utc, z.zone AS bidding_zone, z.load_mw
FROM bronze.entsoe,
LATERAL (VALUES ('DE-LU', load_actual_DE_LU_MW),
                ('FR',    load_actual_FR_MW),
                ('NL',    load_actual_NL_MW)) AS z(zone, load_mw)
WHERE z.load_mw IS NOT NULL;

-- Generation by production type, 15-min, long format.
CREATE OR REPLACE TABLE silver.grid_generation AS
SELECT CAST(timestamp_berlin AS TIMESTAMP) AS ts_utc,
       replace(regexp_extract(col, '^gen_(DE_LU|FR|NL)_', 1), 'DE_LU', 'DE-LU') AS bidding_zone,
       regexp_extract(col, '^gen_(?:DE_LU|FR|NL)_(.+)_Actual_(?:Aggregated|Consumption)_MW$', 1) AS fuel,
       lower(regexp_extract(col, '_(Aggregated|Consumption)_MW$', 1)) AS kind,
       mw
FROM (UNPIVOT bronze.entsoe ON COLUMNS('^gen_.*') INTO NAME col VALUE mw)
WHERE mw IS NOT NULL;

-- Cross-border physical flows, 15-min.
CREATE OR REPLACE TABLE silver.grid_flow AS
SELECT CAST(timestamp_berlin AS TIMESTAMP) AS ts_utc, f.from_zone, f.to_zone, f.mw
FROM bronze.entsoe,
LATERAL (VALUES ('DE-LU', 'FR',    flow_DE_LU_to_FR_MW),
                ('FR',    'DE-LU', flow_FR_to_DE_LU_MW),
                ('DE-LU', 'NL',    flow_DE_LU_to_NL_MW),
                ('NL',    'DE-LU', flow_NL_to_DE_LU_MW)) AS f(from_zone, to_zone, mw)
WHERE f.mw IS NOT NULL;
