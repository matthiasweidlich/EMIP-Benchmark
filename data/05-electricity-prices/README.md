# Electricity Prices & Grid Context Dataset

## Dataset scope

- **Time range:** 8 November 2021 to 14 November 2021
- **Geographic scope:** European bidding zones (DE-LU, FR, NL, AT, BE, CH)
- **Included measurements:** day-ahead auction prices, actual load,
  generation by source, cross-border flows

The selected period matches the timeframe of the DEBS 2022 Grand Challenge dataset.

---

## File 1 — Day-ahead prices (hourly, 6 zones)

**Source:** Fraunhofer ISE Energy-Charts API
**File:** `electricity_day_ahead_prices_2021-11-08_2021-11-14.csv`
**Granularity:** Hourly
**Zones:** AT, BE, CH, DE-LU, FR, NL

Day-ahead prices are auction clearing prices set the day before delivery
via the Single Day-Ahead Coupling (SDAC). One price per hour per zone.
Provenance details in `electricity_day_ahead_prices_2021-11-08_2021-11-14_metadata.json`.

Schema:
```text
timestamp_utc,timestamp_local,bidding_zone,price_eur_mwh
```

Example:
```csv
2021-11-07T23:00:00+00:00,2021-11-08T00:00:00+01:00,DE-LU,55.39
2021-11-07T23:00:00+00:00,2021-11-08T00:00:00+01:00,FR,172.86
2021-11-07T23:00:00+00:00,2021-11-08T00:00:00+01:00,NL,200.1
```

---

## File 2 — ENTSO-E grid context (15-minute, wide format)

**Source:** ENTSO-E Transparency Platform
**File:** `entsoe_debs2022_nov2021.csv`
**Granularity:** 15-minute (672 rows), Europe/Berlin timestamps
**Zones:** DE-LU, FR, NL

64 columns: day-ahead prices, actual load, actual generation by production
type (wind, solar, nuclear, gas, coal, hydro, …), and cross-border physical
flows. FR and NL generation is published hourly and forward-filled to 15
minutes. Full column documentation, including derived silver-layer signals
(carbon intensity, renewables share), in
[`entsoe_debs2022_nov2021_columns.md`](entsoe_debs2022_nov2021_columns.md).

---

## File 3 — Merged prices + load (15-minute, long format)

**File:** `electricity_prices_and_load_15min_2021-11-08_2021-11-14.csv`
**Produced by:** `merge_electricity_prices_and_load_15min.py`
**Granularity:** 15-minute, 672 intervals × 6 zones = 4,032 rows

Long-format merge of File 1 (hourly prices forward-filled to 15 min) with
actual load from File 2 where available (DE-LU, FR, NL; empty for AT/BE/CH).

Schema:
```text
timestamp_utc,timestamp_local,bidding_zone,price_eur_mwh,load_actual_mw
```

Rows are sorted by `(timestamp_utc, bidding_zone)`.
