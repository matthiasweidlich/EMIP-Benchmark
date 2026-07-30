-- ESEF fundamentals: filings dimension and typed long-format financial facts.
SET TimeZone = 'UTC';

CREATE OR REPLACE TABLE silver.filing AS
SELECT filing_id, lei, 'LEI:' || lei AS company_id, company_name, country,
       period_end AS filing_period_end,
       CAST(date_added AS TIMESTAMP) AS published_at,
       json_url, package_url, error_count
FROM bronze.esef_filings;

CREATE OR REPLACE TABLE silver.financial_fact AS
SELECT lei, 'LEI:' || lei AS company_id, filing_id,
       concept, metric,
       try_cast(value AS DOUBLE) AS value,
       unit,
       try_cast(nullif(period_start, '') AS DATE) AS period_start,
       try_cast(nullif(period_end, '') AS DATE) AS period_end,
       try_cast(filing_period_end AS DATE) AS filing_period_end,
       try_cast(filing_published AS DATE) AS filing_published
FROM bronze.esef_fundamentals
WHERE try_cast(value AS DOUBLE) IS NOT NULL;

-- Latest annual value per company and metric (period ending before the
-- benchmark week; comparatives from later filings are allowed by design —
-- see data/dataset-03-company-fundamentals-filings.md).
CREATE OR REPLACE VIEW silver.latest_company_fundamentals AS
SELECT company_id, lei, metric,
       arg_max(value, period_end) AS value,
       arg_max(unit, period_end) AS unit,
       max(period_end) AS period_end
FROM silver.financial_fact
WHERE period_end <= DATE '2021-11-08'
GROUP BY company_id, lei, metric;
