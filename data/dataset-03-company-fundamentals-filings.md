# Source 3: Company Fundamentals / Filings

Raw company facts from annual reports, SEC filings, or filing-like public-company disclosures. This source is the relational fundamentals layer.

## Pre-ETL Sample Tuples

| source | company_id | company_name | report_type | report_date | filing_date | metric | value | unit |
|---|---|---|---|---|---|---|---:|---|
| annual_report | LEI:21380068P1DRHMJ8KU70 | Royal Dutch Shell plc | annual | 2020-12-31 | 2021-03-11 | revenue | 180543000000 | USD |
| sec_20f | CIK:0001306965 | ASML Holding NV | 20-F | 2020-12-31 | 2021-02-10 | net_income | 3583000000 | EUR |
| annual_report | LEI:529900UT4DG0LG5R9O07 | Siemens AG | annual | 2021-09-30 | 2021-12-02 | revenue | 62300000000 | EUR |
| annual_report | LEI:2JMTD21GX3W9QY3C2J51 | Airbus SE | annual | 2020-12-31 | 2021-02-18 | revenue | 49912000000 | EUR |
| sec_6k | CIK:0000313510 | Shell plc | 6-K | 2021-09-30 | 2021-10-28 | operating_cash_flow | 16300000000 | USD |

## ETL Notes

- Normalize company identifiers across LEI, CIK, names, and tickers.
- Standardize metrics into canonical financial concepts.
- Convert currencies where benchmark rules require comparable values.
- Handle amended filings and duplicate facts.
- Create `filing`, `financial_fact`, and `latest_company_fundamentals` tables.

