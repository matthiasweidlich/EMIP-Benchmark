-- Dimensions: exchange, zone map, instrument, company, sector, bridges.
SET TimeZone = 'UTC';

CREATE OR REPLACE TABLE silver.exchange (
    exchange_code TEXT PRIMARY KEY,   -- DEBS suffix
    mic TEXT, exchange_name TEXT, country_code TEXT,
    timezone TEXT, bidding_zone TEXT);
INSERT INTO silver.exchange VALUES
    ('ETR', 'XETR', 'Deutsche Boerse Xetra', 'DE', 'Europe/Berlin',    'DE-LU'),
    ('FR',  'XPAR', 'Euronext Paris',        'FR', 'Europe/Paris',     'FR'),
    ('NL',  'XAMS', 'Euronext Amsterdam',    'NL', 'Europe/Amsterdam', 'NL');

CREATE OR REPLACE TABLE silver.zone_region_map (
    bidding_zone TEXT PRIMARY KEY, country_codes TEXT[], timezone TEXT);
INSERT INTO silver.zone_region_map VALUES
    ('DE-LU', ['DE', 'LU'], 'Europe/Berlin'),
    ('FR',    ['FR'],       'Europe/Paris'),
    ('NL',    ['NL'],       'Europe/Amsterdam'),
    ('BE',    ['BE'],       'Europe/Brussels'),
    ('AT',    ['AT'],       'Europe/Vienna'),
    ('CH',    ['CH'],       'Europe/Zurich');

-- Company key preference: LEI (via GLEIF/ESEF) > ISIN > Yahoo ticker.
CREATE OR REPLACE TEMP VIEW _isin_lei AS
SELECT isin, any_value(lei) AS lei FROM bronze.esef_company_match GROUP BY isin;

CREATE OR REPLACE TABLE silver.instrument AS
WITH base AS (
    SELECT s.symbol AS instrument_id,
           s.sec_type,
           regexp_extract(s.symbol, '\.([A-Z]+)$', 1) AS exchange_code,
           si.isin,
           t1.yahoo_ticker,
           coalesce(t1.longName, t1.shortName) AS instrument_name,
           t1.quoteType AS quote_type,
           t1.currency AS metadata_currency,
           CASE
               WHEN t1.debs_symbol IS NOT NULL THEN 'resolved_' || t1.resolved_via
               WHEN u.debs_symbol IS NOT NULL THEN 'unresolved_' || u.status
               WHEN s.sec_type = 'I' THEN 'index_not_attempted'
               ELSE 'no_isin'
           END AS resolution_status
    FROM bronze.symbols s
    LEFT JOIN bronze.sym_isin si USING (symbol)
    LEFT JOIN bronze.equities_metadata t1 ON t1.debs_symbol = s.symbol
    LEFT JOIN bronze.unresolved_symbols u ON u.debs_symbol = s.symbol)
SELECT b.*,
       CASE WHEN l.lei IS NOT NULL THEN 'LEI:' || l.lei
            WHEN b.isin IS NOT NULL AND b.sec_type = 'E' THEN 'ISIN:' || b.isin
            WHEN b.yahoo_ticker IS NOT NULL THEN 'YH:' || b.yahoo_ticker
       END AS company_id
FROM base b LEFT JOIN _isin_lei l ON b.isin = l.isin AND b.sec_type = 'E';

CREATE OR REPLACE TABLE silver.company AS
WITH inst AS (
    SELECT company_id, isin, yahoo_ticker
    FROM silver.instrument WHERE company_id IS NOT NULL),
    esef_names AS (
    SELECT 'LEI:' || lei AS company_id, any_value(nullif(company_name, '')) AS esef_name,
           any_value(lei) AS lei
    FROM bronze.esef_company_match GROUP BY 1)
SELECT i.company_id,
       e.lei,
       any_value(t1.isin_yf) AS isin_yf,
       arbitrary(i.isin) AS isin,
       coalesce(any_value(nullif(t1.longName, '')),
                any_value(nullif(t1.shortName, '')),
                any_value(e.esef_name),
                any_value(o.company_name)) AS company_name,
       coalesce(any_value(t1.sector), any_value(o.sector)) AS sector,
       coalesce(any_value(t1.industry), any_value(o.industry)) AS industry,
       coalesce(any_value(t1.country), any_value(o.country)) AS country,
       any_value(t1.city) AS city,
       any_value(t1.website) AS website,
       any_value(t1.currency) AS currency,
       any_value(t1.marketCap) AS market_cap_today,
       any_value(t1.fullTimeEmployees) AS employees_today
FROM inst i
LEFT JOIN bronze.equities_metadata t1 ON t1.yahoo_ticker = i.yahoo_ticker
LEFT JOIN esef_names e USING (company_id)
LEFT JOIN bronze.company_overrides o ON o.isin = i.isin
GROUP BY i.company_id, e.lei;

CREATE OR REPLACE TABLE silver.sector AS
SELECT row_number() OVER (ORDER BY sector, industry) AS sector_id,
       sector, industry, 'yahoo_finance' AS taxonomy
FROM (SELECT DISTINCT sector, industry
      FROM bronze.equities_metadata WHERE sector IS NOT NULL);

CREATE OR REPLACE TABLE silver.instrument_company AS
SELECT instrument_id, company_id, resolution_status, isin, yahoo_ticker
FROM silver.instrument
WHERE company_id IS NOT NULL AND sec_type = 'E';
