-- News facts at daily grain (GDELT GKG 1.0 carries publication dates only).
SET TimeZone = 'UTC';

-- Per-document CAMEO event context (documents link to many events).
CREATE OR REPLACE TEMP VIEW _doc_events AS
SELECT l.document_id,
       count(*) AS event_count,
       count(*) FILTER (e.quad_class IN (1, 2)) AS coop_event_count,
       count(*) FILTER (e.quad_class IN (3, 4)) AS conflict_event_count,
       avg(e.goldstein_scale) AS goldstein_avg
FROM silver.news_event_link l
JOIN silver.cameo_event e USING (global_event_id)
GROUP BY 1;

CREATE OR REPLACE TABLE gold.fact_company_news_day AS
SELECT m.company_id,
       m.publication_date,
       count(DISTINCT m.document_id) AS doc_count,
       count(*) AS mention_count,
       avg(d.tone_avg) AS tone_avg,
       min(d.tone_avg) AS tone_min,
       sum(d.tone_avg * d.article_count) / nullif(sum(d.article_count), 0) AS tone_weighted,
       sum(d.article_count) AS article_count,
       sum(e.event_count) AS event_count,
       sum(e.conflict_event_count) AS conflict_event_count,
       avg(e.goldstein_avg) AS goldstein_avg
FROM silver.news_ticker_mention m
JOIN silver.news_document d USING (document_id)
LEFT JOIN _doc_events e ON e.document_id = m.document_id
WHERE m.company_id IS NOT NULL
GROUP BY 1, 2;

-- Topic grain (OIL, WIND, POWER_GRID, ...): the statistically dense news signal.
CREATE OR REPLACE TABLE gold.fact_topic_news_day AS
SELECT t.topic,
       d.publication_date,
       count(*) AS doc_count,
       avg(d.tone_avg) AS tone_avg,
       min(d.tone_avg) AS tone_min,
       sum(d.tone_avg * d.article_count) / nullif(sum(d.article_count), 0) AS tone_weighted,
       sum(d.article_count) AS article_count,
       sum(e.event_count) AS event_count,
       sum(e.conflict_event_count) AS conflict_event_count,
       avg(e.goldstein_avg) AS goldstein_avg
FROM silver.news_document d
JOIN LATERAL unnest(d.energy_sectors) AS t(topic) ON true
LEFT JOIN _doc_events e ON e.document_id = d.document_id
GROUP BY 1, 2;
