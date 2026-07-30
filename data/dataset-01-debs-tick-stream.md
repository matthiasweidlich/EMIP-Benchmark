# Source 1: DEBS Tick Stream

Raw market tick events from the DEBS 2022 Grand Challenge stock trading dataset
(tick data captured by Infront Financial Technology GmbH; CC BY-NC-SA 4.0).
This source is the high-volume streaming input: the full week has about 289M
tick events (24.9 GB) over 5,504 equities and indices traded in Paris (`FR`),
Amsterdam (`NL`), and Frankfurt/Xetra (`ETR`).

## Files In This Repo (`01-debs-tick-stream/`)

| File | Description |
|---|---|
| `debs2022-gc-trading-day-08-11-21_sample100.csv` | Sample of the Monday file (~1,000 rows around 09:01) |
| `debs2022-gc-trading-day-13-11-21.csv` | Full Saturday file (~33k data rows, all-hours index/quote updates) |
| `debs2022-gc-trading-day-14-11-21.csv` | Full Sunday file (~26k data rows) |

The two weekend files together contain 5,499 of the 5,504 documented symbols —
effectively the full instrument universe. The five weekday files are ~5 GB each
and are not committed; use the Zenodo links below.

## Links to Data Files
 - https://zenodo.org/records/6382482/files/debs2022-gc-trading-day-08-11-21.csv?download=1
 - https://zenodo.org/records/6382482/files/debs2022-gc-trading-day-09-11-21.csv?download=1
 - https://zenodo.org/records/6382482/files/debs2022-gc-trading-day-10-11-21.csv?download=1
 - https://zenodo.org/records/6382482/files/debs2022-gc-trading-day-11-11-21.csv?download=1
 - https://zenodo.org/records/6382482/files/debs2022-gc-trading-day-12-11-21.csv?download=1
 - https://zenodo.org/records/6382482/files/debs2022-gc-trading-day-13-11-21.csv?download=1
 - https://zenodo.org/records/6382482/files/debs2022-gc-trading-day-14-11-21.csv?download=1


## Actual File Format

Each file starts with a multi-line `#` comment preamble (license), then the CSV
header with **39 columns**, then a second in-line `#` comment row repeating the
column descriptions. Rows are extremely sparse: each tick carries only the
fields that changed (e.g. a bid update leaves ask/last/volume empty).

Key columns: `ID` (DEBS symbol, e.g. `AIR.FR`), `SecType` (`E`quity/`I`ndex),
`Date` (`DD-MM-YYYY`), `Time` (`HH:MM:SS.mmm`, local CET), bid/ask price and
volume, `Last`/`Last volume`, `Trading time`/`Trading date` (time of last
trade), `Total volume`, `ISIN`, `Currency` (ISO 4217, plus pseudo-code `XXP`
for GBp pence).

Real sample rows (selected columns):

| ID | SecType | Date | Time | Last | Trading time |
|---|---|---|---|---:|---|
| BN.FR | E | 08-11-2021 | 09:01:00.000 | 57.15 | 09:01:00.600 |
| NLBM.NL | I | 08-11-2021 | 09:01:00.000 | 1719.10 | 09:01:00.306 |
| FRBM.FR | I | 08-11-2021 | 09:01:00.000 | 2455.86 | 09:01:00.307 |

## ETL Notes

- Skip `#` comment lines (preamble and the in-line description row); the CSV is
  not strictly RFC 4180 (ragged rows, needs lenient parsing).
- Parse separate `Date` and `Time` fields into an event-time timestamp;
  times are local CET (UTC+1 during the benchmark week) — normalize to UTC.
- Known quality issues in the weekend files: a few rows with empty `Date`,
  ~17% with empty or malformed `Time` (literal `::`), column names with
  leading spaces, currencies other than EUR (USD, GBP, SEK, CHF, JPY, and
  `XXP` = pence, to be scaled by 1/100 to GBP).
- Resolve `ID` and `ISIN` to canonical instruments (see dataset 02); the same
  ISIN can trade under different symbols on multiple exchanges.
- Filter or separately model indices where `SecType = I` (indices update
  around the clock, also on weekends; equities trade 09:00–17:30 CET).
- Derive rolling market features such as returns, volatility, spread, and volume.

