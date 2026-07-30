-- Bronze views: read raw source files as-is (lenient parsing, no cleaning).
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;

-- DEBS tick files: '#' comment preamble + in-line comment header, ragged rows.
-- Parsed without header/comment detection: DuckDB's comment handling eats the
-- first byte of the first data row after an in-line comment line, and default
-- quote handling can glue lines (the files use no quoting). One physical line
-- = one row; preamble/header/description rows are filtered out.
-- Read one file per branch: multi-file globs confuse the sniffer on this format,
-- and the parallel reader rejects the multi-GB weekday files (parallel = false).
CREATE OR REPLACE MACRO bronze_read_ticks(path) AS TABLE
SELECT * FROM read_csv(path,
    header = false, all_varchar = true, quote = '',
    strict_mode = false, null_padding = true, sample_size = -1, parallel = false,
    names = ['ID', 'SecType', 'Date', 'Time', 'Ask', 'Ask volume', 'Bid',
             'Bid volume', 'Ask time', 'Day''s high ask', 'Close', 'Currency',
             'Day''s high ask time', 'Day''s high', 'ISIN', 'Auction price',
             'Day''s low ask', 'Day''s low', 'Day''s low ask time', 'Open',
             'Nominal value', 'Last', 'Last volume', 'Trading time',
             'Total volume', 'Mid price', 'Trading date', 'Profit',
             'Current price', 'Related indices', 'Day high bid time',
             'Day low bid time', 'Open Time', 'Last trade time', 'Close Time',
             'Day high Time', 'Day low Time', 'Bid time', 'Auction Time'])
WHERE ID IS NOT NULL AND ID NOT LIKE '#%' AND ID <> 'ID';

CREATE OR REPLACE VIEW bronze.market_tick AS
SELECT *, 'debs2022-gc-trading-day-13-11-21.csv' AS filename
FROM bronze_read_ticks('data/01-debs-tick-stream/debs2022-gc-trading-day-13-11-21.csv')
UNION ALL
SELECT *, 'debs2022-gc-trading-day-14-11-21.csv' AS filename
FROM bronze_read_ticks('data/01-debs-tick-stream/debs2022-gc-trading-day-14-11-21.csv')
UNION ALL
SELECT *, 'debs2022-gc-trading-day-08-11-21_sample100.csv' AS filename
FROM bronze_read_ticks('data/01-debs-tick-stream/debs2022-gc-trading-day-08-11-21_sample100.csv');

-- Full-week universe (extract_symbol_universe.py over all downloaded DEBS days).
CREATE OR REPLACE VIEW bronze.symbols AS
SELECT * FROM read_csv('data/02-instrument-company-metadata/symbols_week.txt',
                       header = false, names = ['symbol', 'sec_type']);

CREATE OR REPLACE VIEW bronze.sym_isin AS
SELECT * FROM read_csv('data/02-instrument-company-metadata/sym_isin_week.txt',
                       header = false, names = ['symbol', 'isin']);

CREATE OR REPLACE VIEW bronze.equities_metadata AS
SELECT * FROM read_csv('data/02-instrument-company-metadata/table1_equities_metadata.csv', header = true);

CREATE OR REPLACE VIEW bronze.unresolved_symbols AS
SELECT * FROM read_csv('data/02-instrument-company-metadata/table3_unresolved_symbols.csv', header = true);

CREATE OR REPLACE VIEW bronze.esef_company_match AS
SELECT * FROM read_csv('data/03-company-fundamentals/esef_company_match.csv', header = true);

CREATE OR REPLACE VIEW bronze.esef_filings AS
SELECT * FROM read_csv('data/03-company-fundamentals/esef_filings.csv', header = true);

CREATE OR REPLACE VIEW bronze.esef_fundamentals AS
SELECT * FROM read_csv('data/03-company-fundamentals/esef_fundamentals.csv',
                       header = true, all_varchar = true);

-- GDELT full files must be unzipped first (build.sh does this).
CREATE OR REPLACE VIEW bronze.gkg_energy AS
SELECT * FROM read_csv('data/04-gdelt-news-events/gkg_energy_enriched.csv',
                       delim = '\t', header = true, quote = '', sample_size = -1);

CREATE OR REPLACE VIEW bronze.gkg_event_link AS
SELECT * FROM read_csv('data/04-gdelt-news-events/gkg_energy_event_link.csv',
                       delim = '\t', header = true, quote = '', sample_size = -1);

CREATE OR REPLACE VIEW bronze.electricity_day_ahead AS
SELECT * FROM read_csv('data/05-electricity-prices/electricity_day_ahead_prices_2021-11-08_2021-11-14.csv', header = true);

CREATE OR REPLACE VIEW bronze.entsoe AS
SELECT * FROM read_csv('data/05-electricity-prices/entsoe_debs2022_nov2021.csv', header = true);

CREATE OR REPLACE VIEW bronze.weather AS
SELECT * FROM read_csv('data/06-weather/sensor_community_weather_western_europe_sample_100mb.csv',
                       header = true, sample_size = -1);

CREATE OR REPLACE VIEW bronze.gdelt_ticker_crosswalk AS
SELECT * FROM read_csv('silver/seed/gdelt_ticker_crosswalk.csv', header = true);

-- Curated metadata for majors that present-day Yahoo lookups cannot resolve
-- (delisted / renamed / nationalized since Nov 2021, e.g. Shell, EDF).
CREATE OR REPLACE VIEW bronze.company_overrides AS
SELECT * FROM read_csv('silver/seed/company_overrides.csv', header = true);
