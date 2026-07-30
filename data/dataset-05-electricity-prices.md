# Source 5: Electricity Prices & Grid Context

Electricity market and grid data for the benchmark week. This source provides
the external energy-market drivers for energy-transition stock signals:
day-ahead prices, actual load, generation mix, and cross-border flows. It
replaces the earlier EIA-style sketch with real ENTSO-E / Energy-Charts data.
See [05-electricity-prices/README.md](05-electricity-prices/README.md) for
per-file details.

## Files In This Repo (`05-electricity-prices/`)

| File | Granularity | Zones | Content |
|---|---|---|---|
| `electricity_day_ahead_prices_2021-11-08_2021-11-14.csv` | hourly | AT, BE, CH, DE-LU, FR, NL | Day-ahead auction prices (EUR/MWh), UTC + local timestamps |
| `entsoe_debs2022_nov2021.csv` | 15 min, wide (64 cols) | DE-LU, FR, NL | Prices, actual load, generation by source, cross-border flows ([column docs](05-electricity-prices/entsoe_debs2022_nov2021_columns.md)) |
| `electricity_prices_and_load_15min_2021-11-08_2021-11-14.csv` | 15 min, long | all 6 | Merged prices + load (`merge_electricity_prices_and_load_15min.py`) |

## Sample Tuples (merged 15-min file)

| timestamp_utc | timestamp_local | bidding_zone | price_eur_mwh | load_actual_mw |
|---|---|---|---:|---:|
| 2021-11-07T23:00:00+00:00 | 2021-11-08T00:00:00+01:00 | AT | 101.31 | |
| 2021-11-07T23:00:00+00:00 | 2021-11-08T00:00:00+01:00 | DE-LU | 55.39 | 49211.35 |
| 2021-11-07T23:00:00+00:00 | 2021-11-08T00:00:00+01:00 | FR | 172.86 | 53728.0 |

## ETL Notes

- Timestamps are timezone-aware Europe/Berlin (CET, UTC+1); the day-ahead and
  merged files also carry explicit UTC — normalize all series to UTC.
- Day-ahead prices are hourly auction results held constant across the four
  15-min intervals of each hour; FR/NL generation and load are hourly,
  forward-filled to 15 min — do not mistake forward-fill for measurements.
- Unpivot the wide ENTSO-E file into long `(zone, time, fuel, value)` form for
  generation, and derive carbon intensity and renewables share per zone
  (emission factors in the column docs).
- Map bidding zones to DEBS exchanges and company countries:
  DE-LU ↔ Xetra (`ETR`), FR ↔ Paris (`FR`), NL ↔ Amsterdam (`NL`).
- Benchmark-week context: Nov 2021 sits in the European energy crisis — FR/NL
  prices are 2–4× the DE level, French nuclear is reduced by maintenance
  outages, German wind is high. Good stress data for cross-zone divergence.
- Create `electricity_price`, `grid_load`, `grid_generation`, and `grid_flow`
  tables.
