# DEBS 2022 Grand Challenge — Symbols & Organization Metadata

Stock symbols extracted from the [DEBS 2022 Grand Challenge trading dataset](https://zenodo.org/records/6382482)
(tick data captured by Infront Financial Technology GmbH, week of 2021-11-08 to 2021-11-14),
enriched with organization metadata (sector, industry, …) from Yahoo Finance via `yfinance`.

The dataset covers 5,504 equities and indices traded on three European exchanges:
Paris (`FR`), Amsterdam (`NL`), and Frankfurt/Xetra (`ETR`). Symbols are structured as
`<identifier>.<exchange>`, e.g. `RDSA.NL` is Royal Dutch Shell on the Amsterdam exchange.

Source data license: CC BY-NC-SA 4.0 (© Infront Financial Technology GmbH).

## Raw data (from Zenodo)

| File | Description |
|---|---|
| `day13.csv` | `debs2022-gc-trading-day-13-11-21.csv` — raw tick data, Saturday 2021-11-13 (~3 MB, 39 columns: ID, SecType, Date, Time, bid/ask, ISIN, …) |
| `day14.csv` | `debs2022-gc-trading-day-14-11-21.csv` — raw tick data, Sunday 2021-11-14 (~2 MB) |

Only the two small weekend files were downloaded (the five weekday files are ~5 GB each).
Together they contain 5,499 of the 5,504 documented symbols — effectively the full universe.

## Symbol lists (extracted)

| File | Rows | Description |
|---|---|---|
| `symbols_weekend.txt` | 5,499 | All unique symbols as `symbol,type` pairs. Type `E` = equity (2,996), `I` = index (2,503). |
| `equities_symbols.txt` | 2,996 | Equity symbols only, one per line (DEBS format, e.g. `SIE.ETR`). |
| `indices_symbols.txt` | 2,503 | Index symbols only, one per line. |

Note: many `ETR` equity identifiers are numeric WKN-style codes (e.g. `120071.ETR`)
that do not resolve on Yahoo Finance.

## Yahoo Finance metadata

Exchange suffixes are mapped to Yahoo Finance suffixes before lookup:
`.ETR` → `.DE` (Xetra), `.FR` → `.PA` (Paris), `.NL` → `.AS` (Amsterdam).

| File | Description |
|---|---|
| `equities_metadata_raw.csv` | Raw per-symbol fetch results for all 2,996 equities. Columns: `debs_symbol`, `yahoo_ticker`, `exchange`, `status` (`ok` / `no_data` / `error:*`), `shortName`, `longName`, `sector`, `industry`, `country`, `city`, `currency`, `quoteType`, `marketCap`, `fullTimeEmployees`, `website`, `isin_yf`. |
| `table1_equities_metadata.csv` | **Main deliverable** — successfully resolved equities with organization metadata (name, sector, industry, country, market cap, employees, website, ISIN). |
| `table2_sector_by_exchange.csv` | Summary pivot: count of resolved equities per sector × exchange. |
| `table3_unresolved_symbols.csv` | Symbols that could not be resolved on Yahoo Finance, with failure status. |

## Scripts

| File | Description |
|---|---|
| `fetch_metadata.py` | Initial threaded fetch of `yfinance` `Ticker.info` for all equities (resumable; appends to `equities_metadata_raw.csv`). |
| `retry_failed.py` | Sequential retry of rate-limited symbols with exponential backoff (Yahoo throttles aggressive fetching). |
| `build_tables.py` | Builds `table1`–`table3` from `equities_metadata_raw.csv`. |

## Reproducing

```sh
pip install yfinance pandas
python3 fetch_metadata.py   # initial fetch (threaded)
python3 retry_failed.py     # retry rate-limited symbols (slow, sequential)
python3 build_tables.py     # produce the final tables
```
