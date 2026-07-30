# Source 2: Instrument / Company Metadata & Mapping

Mapping records connecting DEBS market instruments to companies, sectors, and
alternative identifiers. This source supports joins from DEBS ticks to
company-level data. Built from the DEBS weekend files plus Yahoo Finance
metadata (via `yfinance`); see
[02-instrument-company-metadata/README.md](02-instrument-company-metadata/README.md)
for the full extraction methodology.

## Files In This Repo (`02-instrument-company-metadata/`)

| File | Rows | Description |
|---|---|---|
| `symbols_weekend.txt` | 5,499 | Full instrument universe as `symbol,type` (`E` = equity: 2,996, `I` = index: 2,503) |
| `equities_symbols.txt` | 2,996 | Equity symbols, one per line (DEBS format, e.g. `SIE.ETR`) |
| `indices_symbols.txt` | 2,503 | Index symbols |
| `sym_isin.txt` | 5,486 | `symbol,ISIN` map extracted from the weekend tick files |
| `table1_equities_metadata.csv` | 2,119 | Resolved equities: DEBS symbol, Yahoo ticker, name, sector, industry, country, currency, market cap, ISIN |
| `table2_sector_by_exchange.csv` | — | Summary pivot: resolved equities per sector × exchange |
| `table3_unresolved_symbols.csv` | 877 | Unresolved symbols with status (`isin_not_found`, `no_data`) |
| `equities_metadata_raw.csv`, `equities_metadata_isin.csv` | | Intermediate per-pass resolution results |

## Sample Tuples (`table1_equities_metadata.csv`)

| debs_symbol | yahoo_ticker | exchange | resolved_via | longName | sector | country | currency | isin_yf |
|---|---|---|---|---|---|---|---|---|
| AIR.FR | AIR.PA | FR | ticker | Airbus SE | Industrials | Netherlands | EUR | |
| 121806.ETR | A7A.DE | ETR | isin | Heliad AG | Financial Services | Germany | EUR | DE0001218063 |
| 120471.ETR | TIAJF | ETR | isin | Telecom Italia S.p.A. | Communication Services | Italy | USD | IT0003497176 |

## ETL Notes

- Coverage is deliberately partial: 2,119 of 2,996 equities resolved (71%),
  1,702 with sector/industry. The 877 unresolved symbols (mostly delisted,
  merged, or renamed since Nov 2021) are a data-quality workload, not an error.
- Notable gap: Royal Dutch Shell (`RDSA.NL`, ISIN `GB00B03MLX29`) is
  unresolved because the company renamed to Shell plc (`SHEL`) in Jan 2022 —
  relevant when joining GDELT ticker mentions (dataset 04).
- 135 ISINs map to more than one DEBS symbol (cross-listings, e.g.
  Saint-Gobain as `SGO.FR` and `872087.ETR`): distinguish instrument-level
  (symbol) from security/company-level (ISIN) entities.
- Many `ETR` identifiers are numeric WKN-style codes (e.g. `120071.ETR`);
  exchange suffix mapping: `.ETR` → Xetra (`XETR`, DE), `.FR` → Paris
  (`XPAR`, FR), `.NL` → Amsterdam (`XAMS`, NL).
- Metadata reflects Yahoo Finance **today**, not Nov 2021 (market cap,
  employees in particular) — treat as a static dimension with known drift.
- LEI-based identifiers arrive with dataset 03 (fundamentals): ISIN → LEI →
  ESEF filings.
- Create canonical `instrument`, `company`, and `instrument_company` tables.
