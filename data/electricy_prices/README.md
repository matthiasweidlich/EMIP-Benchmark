# Electricity Prices Dataset

## Dataset scope

- **Time range:** 8 November 2021 to 14 November 2021
- **Geographic scope:** European bidding zones (DE-LU, FR, NL, AT, BE, CH)
- **Included measurements:** day-ahead auction prices + imbalance settlement prices

The selected period matches the timeframe of the DEBS 2022 Grand Challenge dataset.

---

## File 1 — Day-ahead prices

**Source:** Fraunhofer ISE Energy-Charts API  
**File:** `electricity_day_ahead_prices_2021-11-08_2021-11-14.csv`  
**Granularity:** Hourly  
**Zones:** AT, BE, CH, DE-LU, FR, NL

Day-ahead prices are auction clearing prices set the day before delivery
via the Single Day-Ahead Coupling (SDAC). One price per hour per zone.

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

## File 2 — Imbalance settlement prices

**Source:** ENTSO-E Transparency Platform (document type A85)  
**File:** `electricity_imbalance_prices_2021-11-08_2021-11-14.csv`  
**Granularity:** 15-minute  
**Zones:** DE-LU, FR, NL

Imbalance prices are actual post-delivery settlement prices applied to
market parties who were long or short in the balancing timeframe. More
volatile than day-ahead prices; directly reflects real-time supply/demand
stress. For Germany this corresponds to the reBAP price.

Schema adds a `price_type` column to distinguish long/short imbalance:
```text
timestamp_utc,timestamp_local,bidding_zone,price_eur_mwh,price_type
```

Example:
```csv
2021-11-08T00:00:00+00:00,2021-11-08T01:00:00+01:00,DE-LU,62.10,imbalance_long
2021-11-08T00:00:00+00:00,2021-11-08T01:00:00+01:00,DE-LU,58.40,imbalance_short
```

---

## Get the data

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Day-ahead prices (no API key required)
python download_electricity_prices.py

# Imbalance prices (ENTSO-E API key required — register free at
# https://transparency.entsoe.eu)
python download_imbalance_prices.py <YOUR_ENTSOE_API_KEY>
```

Output files:
```text
electricity_day_ahead_prices_2021-11-08_2021-11-14.csv
electricity_imbalance_prices_2021-11-08_2021-11-14.csv
```

Rows in both files are sorted by `(timestamp_utc, bidding_zone)`.