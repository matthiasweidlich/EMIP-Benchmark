# Sensor.Community Weather Dataset for Western Europe

## Dataset scope

- **Time range:** 8 November 2021 to 14 November 2021
- **Source:** Fraunhofer ISE Energy-Charts API
- **Geographic scope:** European bidding zones
- **Included measurements:** hourly day-ahead electricity prices in EUR/MWh
- **Final format:** one CSV sorted by timestamp

The selected period matches the timeframe of the DEBS 2022 Grand Challenge dataset.

## Final schema

```text
timestamp_utc,timestamp_local,bidding_zone,price_eur_mwh
```

Example:
```csv
timestamp_utc,timestamp_local,bidding_zone,price_eur_mwh
2021-11-07T23:00:00+00:00,2021-11-08T00:00:00+01:00,AT,101.31
2021-11-07T23:00:00+00:00,2021-11-08T00:00:00+01:00,BE,177.3
2021-11-07T23:00:00+00:00,2021-11-08T00:00:00+01:00,CH,176.2
2021-11-07T23:00:00+00:00,2021-11-08T00:00:00+01:00,DE-LU,55.39
```

Rows are sorted globally by:

```text
timestamp, bidding_zone
```

# Get the data 

The following contains all scripts to  generate one globally time-sorted CSV file.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python download_electricity_prices.py
```

The final file is:

```text
electricity_day_ahead_prices_2021-11-08_2021-11-14.csv
```