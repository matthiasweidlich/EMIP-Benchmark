-- GDELT news: documents, ticker mentions (resolved to companies), event links.
SET TimeZone = 'UTC';

CREATE OR REPLACE TABLE silver.news_document AS
SELECT md5(SOURCEURL || '|' || DATE) AS document_id,
       strptime(CAST(DATE AS TEXT), '%Y%m%d')::DATE AS publication_date,
       SOURCE AS source_domains,
       SOURCEURL AS source_url_raw,
       string_split(SOURCEURL, '<UDIV>')[1] AS source_url,
       len(string_split(SOURCEURL, '<UDIV>')) AS url_count,
       NUMARTS AS article_count,
       string_split(ENERGY_SECTORS, '|') AS energy_sectors,
       string_split(ENERGY_THEMES, '|') AS energy_themes,
       TONE_AVG AS tone_avg, TONE_POS AS tone_positive, TONE_NEG AS tone_negative,
       TONE_POLARITY AS tone_polarity, TONE_ACTIVITY AS tone_activity,
       TONE_SELFREF AS tone_self_reference,
       string_split(nullif(ENERGY_TICKERS, ''), '|') AS energy_tickers,
       string_split(nullif(ENERGY_ENTITIES, ''), '|') AS energy_entities,
       string_split(nullif(COUNTRY_CODES, ''), '|') AS country_codes,
       TOP_LOCATIONS AS top_locations_raw,
       string_split(nullif(PERSONS, ''), ';') AS persons,
       [try_cast(x AS BIGINT) FOR x IN string_split(nullif(CAMEO_EVENT_IDS, ''), ',')] AS cameo_event_ids
FROM bronze.gkg_energy;

-- One row per (document, ticker); resolved to a company ISIN where possible:
-- 1. directly via Yahoo ticker of a resolved DEBS equity,
-- 2. via the curated crosswalk (renames, ADR tickers, delistings).
CREATE OR REPLACE TABLE silver.news_ticker_mention AS
WITH mention AS (
    SELECT document_id, publication_date, unnest(energy_tickers) AS ticker
    FROM silver.news_document WHERE energy_tickers IS NOT NULL),
    yahoo AS (
    SELECT t1.yahoo_ticker,
           coalesce(any_value(t1.isin_yf), any_value(si.isin)) AS isin
    FROM bronze.equities_metadata t1
    LEFT JOIN bronze.sym_isin si ON si.symbol = t1.debs_symbol
    GROUP BY t1.yahoo_ticker)
SELECT m.document_id, m.publication_date, m.ticker,
       coalesce(y.isin, x.isin) AS isin,
       c.company_id,
       CASE WHEN y.yahoo_ticker IS NOT NULL THEN 'yahoo_ticker'
            WHEN x.gdelt_ticker IS NOT NULL THEN 'crosswalk' END AS match_method
FROM mention m
LEFT JOIN yahoo y ON y.yahoo_ticker = m.ticker
LEFT JOIN bronze.gdelt_ticker_crosswalk x ON x.gdelt_ticker = m.ticker
LEFT JOIN (SELECT DISTINCT isin, company_id FROM silver.instrument
           WHERE isin IS NOT NULL AND company_id IS NOT NULL) c
       ON c.isin = coalesce(y.isin, x.isin);

-- CAMEO event dimension, reconstructed from the denormalized link table.
CREATE OR REPLACE TABLE silver.cameo_event AS
SELECT GlobalEventID AS global_event_id,
       any_value(EventRootCode) AS event_root_code,
       any_value(QuadClass) AS quad_class,
       any_value(QuadClassName) AS quad_class_name,
       any_value(GoldsteinScale) AS goldstein_scale,
       any_value(Event_AvgTone) AS event_avg_tone,
       any_value(ActionGeo_FullName) AS action_geo_name,
       any_value(ActionGeo_CC) AS action_geo_cc,
       min(strptime(CAST(DATE AS TEXT), '%Y%m%d')::DATE) AS first_seen_date
FROM bronze.gkg_event_link
GROUP BY GlobalEventID;

CREATE OR REPLACE TABLE silver.news_event_link AS
SELECT DISTINCT l.GlobalEventID AS global_event_id,
       md5(g.SOURCEURL || '|' || g.DATE) AS document_id
FROM bronze.gkg_event_link l
JOIN bronze.gkg_energy g ON l.SourceURL = g.SOURCEURL AND l.DATE = g.DATE;
