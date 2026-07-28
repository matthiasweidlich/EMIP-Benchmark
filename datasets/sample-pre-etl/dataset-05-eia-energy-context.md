# Source 5: EIA / Energy Context

Raw energy-market indicators. This source provides external context for energy-transition stock signals.

## Pre-ETL Sample Tuples

| series_id | region | timestamp | indicator | fuel | value | unit | frequency |
|---|---|---|---|---|---:|---|---|
| eia-elec-de-001 | Germany | 2021-11-08T08:00:00Z | generation | wind | 28450 | MWh | hourly |
| eia-elec-fr-001 | France | 2021-11-08T08:00:00Z | generation | nuclear | 43120 | MWh | hourly |
| eia-price-eu-001 | Europe | 2021-11-08 | natural_gas_price | gas | 24.8 | EUR/MMBtu | daily |
| eia-oil-001 | Global | 2021-11-08 | brent_spot_price | oil | 83.43 | USD/bbl | daily |
| eia-elec-nl-001 | Netherlands | 2021-11-08T08:00:00Z | generation | solar | 3120 | MWh | hourly |

## ETL Notes

- Normalize timestamp granularity across hourly and daily series.
- Map regions to company exposure regions.
- Standardize fuel and indicator taxonomies.
- Convert units and currencies when needed.
- Create `energy_indicator`, `fuel_price_context`, and `sector_energy_context` tables.

