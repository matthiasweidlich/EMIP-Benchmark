# Source 6: Weather Observations (Sensor.Community)

Crowd-sourced temperature and humidity observations from the Sensor.Community
archive for the benchmark week. This source provides dense environmental
context (weather drives both energy demand and renewable generation). See
[06-weather/README.md](06-weather/README.md) for the download/merge pipeline.

## Files In This Repo (`06-weather/`)

| File | Description |
|---|---|
| `sensor_community_weather_western_europe_sample_100mb.csv` | 100 MB sample: ~1.7M rows, ~12k sensors, covering the **first ~6 hours** of 2021-11-08 |
| `sensor_community_weather_western_europe_2021-11-08_2021-11-14_sorted.csv` | **Full week** (gitignored, regenerate via scripts): 30,610,499 rows, 1.8 GB, one globally time-sorted CSV from 57,656 Western-European sensor-day files |
| `download_sensor_community_weather_days.py`, `filter_and_merge_western_europe.py`, `merge_common_schema_sorted.py`, `run_all.sh` | Regeneration pipeline (download ~86k global weather-sensor files for the week, filter by coordinates, external merge sort; ~2 h total) |

The silver build automatically uses the full-week file when present, else the
committed sample.

## Schema and Sample Tuples

```text
sensorID,lat,lon,timestamp,temperature,humidity
```

| sensorID | lat | lon | timestamp | temperature | humidity |
|---|---:|---:|---|---:|---:|
| 957 | 48.802 | 9.224 | 2021-11-08T00:00:00.000000 | 9.0 | 99.9 |
| 2200 | 48.762 | 9.168 | 2021-11-08T00:00:00.000000 | 8.6 | 90.8 |

## ETL Notes

- Timestamps are naive UTC; rows are sorted by `(timestamp, sensorID)`.
- Sensor data is dirty by nature — the sample contains hardware error
  sentinels such as temperature `-3276.7` and `65536.0`: filter to a physical
  plausibility range (e.g. −40…+60 °C, 0…100 % RH) and keep rejects for
  data-quality metrics.
- Despite the file name, the current sample contains sensors far outside
  Western Europe (longitudes from −124 to 175): re-apply a geographic filter
  in the silver layer.
- Missing humidity (~3%) is an empty field — keep as NULL, do not use a
  numeric sentinel.
- Sensors carry no region labels: geo-bucket `lat`/`lon` to country / bidding
  zone to join with electricity prices (dataset 05) and company geography.
- Create a `weather_observation` fact and regional aggregate views.
