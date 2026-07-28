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

Symbols were resolved on Yahoo Finance in two passes:

1. **Direct ticker mapping** — DEBS exchange suffixes translated to Yahoo suffixes:
   `.ETR` → `.DE` (Xetra), `.FR` → `.PA` (Paris), `.NL` → `.AS` (Amsterdam).
   Works for mnemonic tickers (e.g. `AIR.FR` → `AIR.PA`); resolved 1,009 equities.
2. **ISIN lookup** — the DEBS Xetra equities are identified by WKN codes (e.g. `A0HN5C.ETR`),
   which do not exist as Yahoo tickers. For every symbol the first pass missed, the ISIN
   (taken from the ISIN column of the weekend CSVs, see `sym_isin.txt`) was searched on
   Yahoo to find the corresponding ticker; resolved a further 1,110 equities.

**Coverage: 2,119 of 2,996 equities resolved (71%); 1,702 with sector/industry.**
The remaining 877 are almost all `isin_not_found` — securities delisted, merged, or
renamed between the Nov-2021 capture and today.

### Intermediate files

| File | Rows | Description |
|---|---|---|
| `sym_isin.txt` | 5,486 | `symbol,ISIN` map extracted from the weekend CSVs (covers 5,486 of 5,499 symbols). |
| `equities_metadata_raw.csv` | 2,996 | Pass-1 per-symbol results (`status` ∈ `ok` / `no_data` / `error:*`). |
| `equities_metadata_isin.csv` | 1,975 | Pass-2 results for symbols pass 1 missed (`status` ∈ `ok_isin` / `isin_not_found`). |

### Final tables

#### `table1_equities_metadata.csv` — main deliverable (2,119 rows)

One row per resolved equity, combining both passes:

| Column | Description |
|---|---|
| `debs_symbol` | Original symbol as it appears in the DEBS dataset (e.g. `AIR.FR`, `A0HN5C.ETR`) |
| `yahoo_ticker` | Resolved Yahoo Finance ticker (e.g. `AIR.PA`) — use this for further `yfinance` queries |
| `exchange` | DEBS exchange code: `ETR`, `FR`, or `NL` |
| `resolved_via` | `ticker` (pass 1) or `isin` (pass 2) |
| `shortName`, `longName` | Company name |
| `sector` | Yahoo sector classification (e.g. Industrials, Technology) — 1,702 rows populated; empty for funds/certificates and some small caps |
| `industry` | Finer-grained industry (e.g. Aerospace & Defense) |
| `country`, `city` | Headquarters location |
| `currency` | Trading currency |
| `quoteType` | Yahoo security type (`EQUITY`, `ETF`, `MUTUALFUND`, …) |
| `marketCap` | Market capitalization (current, not as of 2021) |
| `fullTimeEmployees` | Employee count |
| `website` | Company website |
| `isin_yf` | ISIN |

Note: metadata reflects Yahoo Finance **today**, not the state in November 2021
(market cap and employees in particular).

#### `table2_sector_by_exchange.csv` — summary pivot

Count of resolved equities per `sector` × `exchange`, with a `Total` column,
sorted by total. Top sectors: Industrials (292), Technology (270),
Consumer Cyclical (237), Financial Services (186), Healthcare (185).

#### `table3_unresolved_symbols.csv` — unresolved symbols (877 rows)

Symbols that could not be resolved, with `status` explaining why:
`isin_not_found` (865 — ISIN no longer known to Yahoo; typically delisted/merged/renamed)
or `no_data` (12 — ticker exists but Yahoo returns no metadata).

