# Source 1: DEBS Tick Stream

Raw market tick events modeled after the DEBS 2022 stock trading dataset. This source is the high-volume streaming input.

## Pre-ETL Sample Tuples

| raw_symbol | exchange | sec_type | date | time | isin | currency | bid | ask | last | volume |
|---|---|---:|---|---|---|---|---:|---:|---:|---:|
| RDSA.NL | NL | E | 08-11-2021 | 09:00:01.1200 | GB00B03MLX29 | EUR | 19.842 | 19.846 | 19.844 | 3200 |
| AIR.FR | FR | E | 08-11-2021 | 09:00:02.4300 | NL0000235190 | EUR | 112.32 | 112.36 | 112.34 | 840 |
| SIE.ETR | ETR | E | 08-11-2021 | 09:00:03.0200 | DE0007236101 | EUR | 145.18 | 145.24 | 145.20 | 1200 |
| ASML.NL | NL | E | 08-11-2021 | 09:00:03.9100 | NL0010273215 | EUR | 742.10 | 742.50 | 742.30 | 95 |
| DAX.ETR | ETR | I | 08-11-2021 | 09:00:04.1500 | DE0008469008 | EUR | 16052.4 | 16053.1 | 16052.8 | 0 |

## ETL Notes

- Parse separate `date` and `time` fields into an event-time timestamp.
- Normalize exchange codes, for example `NL`, `FR`, and `ETR`.
- Resolve `raw_symbol` and `isin` to canonical instruments.
- Filter or separately model indices where `sec_type = I`.
- Derive rolling market features such as returns, volatility, spread, and volume.

