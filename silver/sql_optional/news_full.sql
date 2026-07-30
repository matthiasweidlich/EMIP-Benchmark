-- Full two-week GDELT layer (all documents, real CAMEO event records).
-- Run by build.sh only when the regenerated files exist (see
-- data/04-gdelt-news-events/build_full_tables.py); replaces the energy-only
-- Nov 8-14 news tables built by 30_news.sql with strict supersets.
SET TimeZone = 'UTC';

CREATE OR REPLACE VIEW bronze.cameo_events AS
SELECT * FROM read_csv(['data/04-gdelt-news-events/gdelt_20211101-07_merged.CSV',
                        'data/04-gdelt-news-events/gdelt_20211108-14_merged.CSV'],
                       delim = '\t', header = true,
                       all_varchar = true, sample_size = -1);

CREATE OR REPLACE VIEW bronze.gkg_all AS
SELECT * FROM read_csv(['data/04-gdelt-news-events/gkg_all_enriched_nov1-7.csv.gz',
                        'data/04-gdelt-news-events/gkg_all_enriched_nov8-14.csv.gz'],
                       delim = '\t', header = true, sample_size = -1);

CREATE OR REPLACE VIEW bronze.gkg_all_link AS
SELECT * FROM read_csv(['data/04-gdelt-news-events/gkg_all_event_link_nov1-7.csv.gz',
                        'data/04-gdelt-news-events/gkg_all_event_link_nov8-14.csv.gz'],
                       delim = '\t', header = true, sample_size = -1);

-- All documents, both weeks. Energy tag columns are non-empty only where the
-- energy classifier output exists (Nov 8-14 in this repo).
CREATE OR REPLACE TABLE silver.news_document AS
SELECT md5(SOURCEURL || '|' || DATE) AS document_id,
       strptime(CAST(DATE AS TEXT), '%Y%m%d')::DATE AS publication_date,
       SOURCE AS source_domains,
       SOURCEURL AS source_url_raw,
       string_split(SOURCEURL, '<UDIV>')[1] AS source_url,
       len(string_split(SOURCEURL, '<UDIV>')) AS url_count,
       NUMARTS AS article_count,
       (ENERGY_SECTORS IS NOT NULL AND ENERGY_SECTORS <> '') AS is_energy,
       string_split(nullif(ENERGY_SECTORS, ''), '|') AS energy_sectors,
       NULL::VARCHAR[] AS energy_themes,
       THEMES AS themes_raw, THEME_COUNT AS theme_count,
       TONE_AVG AS tone_avg, TONE_POS AS tone_positive, TONE_NEG AS tone_negative,
       TONE_POLARITY AS tone_polarity, TONE_ACTIVITY AS tone_activity,
       TONE_SELFREF AS tone_self_reference,
       string_split(nullif(ENERGY_TICKERS, ''), '|') AS energy_tickers,
       string_split(nullif(ENERGY_ENTITIES, ''), '|') AS energy_entities,
       string_split(nullif(COUNTRY_CODES, ''), '|') AS country_codes,
       TOP_LOCATIONS AS top_locations_raw,
       string_split(nullif(ORGANIZATIONS, ''), ';') AS organizations,
       string_split(nullif(PERSONS, ''), ';') AS persons,
       [try_cast(x AS BIGINT) FOR x IN string_split(nullif(CAMEO_EVENT_IDS, ''), ',')] AS cameo_event_ids
FROM bronze.gkg_all;

-- Real CAMEO event dimension from the merged export files (both weeks).
CREATE OR REPLACE TABLE silver.cameo_event AS
SELECT try_cast(GlobalEventID AS BIGINT) AS global_event_id,
       any_value(EventRootCode) AS event_root_code,
       any_value(try_cast(QuadClass AS INTEGER)) AS quad_class,
       any_value(CASE QuadClass WHEN '1' THEN 'VerbalCoop' WHEN '2' THEN 'MaterialCoop'
                 WHEN '3' THEN 'VerbalConflict' WHEN '4' THEN 'MaterialConflict' END)
           AS quad_class_name,
       any_value(try_cast(GoldsteinScale AS DOUBLE)) AS goldstein_scale,
       any_value(try_cast(AvgTone AS DOUBLE)) AS event_avg_tone,
       any_value(ActionGeo_FullName) AS action_geo_name,
       any_value(ActionGeo_CountryCode) AS action_geo_cc,
       min(try_strptime(DATEADDED, '%Y%m%d')::DATE) AS first_seen_date,
       any_value(try_strptime(SQLDATE, '%Y%m%d')::DATE) AS event_date,
       any_value(EventCode) AS event_code,
       any_value(nullif(Actor1Name, '')) AS actor1_name,
       any_value(nullif(Actor2Name, '')) AS actor2_name,
       any_value(try_cast(NumMentions AS INTEGER)) AS num_mentions,
       any_value(try_cast(NumArticles AS INTEGER)) AS num_articles,
       any_value(SOURCEURL) AS source_url
FROM bronze.cameo_events
GROUP BY 1;

-- (document, event) links for all documents, matched events only.
CREATE OR REPLACE TABLE silver.news_event_link AS
SELECT DISTINCT r.global_event_id, r.document_id
FROM (SELECT document_id, unnest(cameo_event_ids) AS global_event_id
      FROM silver.news_document WHERE cameo_event_ids IS NOT NULL) r
JOIN silver.cameo_event e USING (global_event_id);

-- Ticker mentions: same resolution logic as 30_news.sql over the superset
-- (tickers exist only on energy-tagged documents).
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
