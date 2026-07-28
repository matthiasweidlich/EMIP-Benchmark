# Sensor.Community Weather Dataset for Western Europe

## Dataset scope

- **Time range:** 8 November 2021 to 14 November 2021
- **Source:** Sensor.Community archive
- **Geographic scope:** Western Europe (Filtering is based on the latitude and longitude stored in each Sensor.Community file.
  )
- **Included measurements:** temperature and humidity
- **Excluded measurements:** particulate matter
- **Final format:** one CSV (~ 3GB) sorted by timestamp

The selected period matches the timeframe of the DEBS 2022 Grand Challenge dataset.

The dataset contains 1 file per sensor each day (appr. 12,000 within Europe in Nov'21).
The schema of the csv file depends on the sensor type, we provide a script that extracts all sensors excluding particular matters for the time interval 8.11.21-14.11.2021.
and unify them into a common schema: 

## Final schema

```text
sensorID,lat,lon,timestamp,temperature,humidity
```

Example:

```csv
sensorID,lat,lon,timestamp,temperature,humidity
12345,50.1109,8.6821,2021-11-08T00:00:10.000000,8.4,72.1
12346,48.8566,2.3522,2021-11-08T00:00:12.000000,10.2,
```

Rows are sorted globally by:

```text
timestamp, sensorID
```

Missing humidity values are empty by default. A numeric sentinel such as `-1` can be configured during the final merge.

---

# Get the data 

The following contains all scripts and merges Sensor.Community weather data into one globally time-sorted CSV file.pip install -r requirements.txt

First, install requirements
```bash
pip install -r requirements.txt
```

Then, download data for the required time frame

```bash
python download_sensor_community_weather_days.py \
 --start 2021-11-08 \
 --end 2021-11-14 \
 --workers 4
```

## Step 2: Filter the data to Western Europe

```bash
python filter_and_merge_western_europe.py \
 --input sensor_community_weather_raw_days \
 --output sensor_community_weather_western_europe_2021-11-08_2021-11-14 \
 --merge-by-sensor-type
```

## Step 3: Create one globally sorted CSV

Use the Western-Europe-filtered `raw/` directory as input:

```bash
python merge_common_schema_sorted.py \
 --input sensor_community_weather_western_europe_2021-11-08_2021-11-14/raw \
 --output sensor_community_weather_western_europe_2021-11-08_2021-11-14_sorted.csv
```

The final file is:

```text
sensor_community_weather_western_europe_2021-11-08_2021-11-14_sorted.csv
```

## Memory usage

The final merge uses an external merge sort.

By default, approximately 250,000 rows are sorted in memory at once. Temporary sorted chunks are written to disk.

For a machine with limited memory:

```bash
python merge_common_schema_sorted.py \
 --input sensor_community_weather_western_europe_2021-11-08_2021-11-14/raw \
 --output sensor_community_weather_western_europe_2021-11-08_2021-11-14_sorted.csv \
 --chunk-rows 100000
```
