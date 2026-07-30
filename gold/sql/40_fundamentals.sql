-- Latest pre-benchmark-week fundamentals per company (long, with units).
SET TimeZone = 'UTC';

CREATE OR REPLACE TABLE gold.fact_fundamentals_latest AS
SELECT company_id, lei, metric, value, unit, period_end
FROM silver.latest_company_fundamentals;
