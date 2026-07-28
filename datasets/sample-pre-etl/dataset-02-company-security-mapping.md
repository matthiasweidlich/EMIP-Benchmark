# Source 2: Company / Security Mapping

Raw mapping records connecting market instruments to legal entities and company names. This source supports joins from DEBS-style ticks to company-level data.

## Pre-ETL Sample Tuples

| source | source_id | isin | ticker | exchange | company_name | lei | country |
|---|---|---|---|---|---|---|---|
| openfigi | BBG000BCZL41 | GB00B03MLX29 | RDSA | XAMS | Royal Dutch Shell plc | 21380068P1DRHMJ8KU70 | GB |
| openfigi | BBG000BVPV84 | NL0000235190 | AIR | XPAR | Airbus SE | 2JMTD21GX3W9QY3C2J51 | NL |
| openfigi | BBG000BH4R78 | DE0007236101 | SIE | XETR | Siemens AG | 529900UT4DG0LG5R9O07 | DE |
| openfigi | BBG000K4ND22 | NL0010273215 | ASML | XAMS | ASML Holding NV | 724500Y6DUVHQD16AI11 | NL |
| exchange_ref | DAX_ETR | DE0008469008 | DAX | XETR | DAX Performance Index | NULL | DE |

## ETL Notes

- Resolve exchange-code differences, for example `NL` to `XAMS` and `ETR` to `XETR`.
- Distinguish tradable companies from indices.
- Treat missing legal identifiers as data quality issues rather than fatal errors.
- Create canonical `instrument`, `company`, and `instrument_company_mapping` tables.

