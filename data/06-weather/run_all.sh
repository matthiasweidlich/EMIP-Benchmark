#!/usr/bin/env bash
set -euo pipefail

python download_sensor_community_weather_days.py \
  --start 2021-11-08 \
  --end 2021-11-14 \
  --workers 4

python filter_and_merge_western_europe.py \
  --input sensor_community_weather_raw_days \
  --output sensor_community_weather_western_europe_2021-11-08_2021-11-14

python merge_common_schema_sorted.py \
  --input sensor_community_weather_western_europe_2021-11-08_2021-11-14/raw \
  --output sensor_community_weather_western_europe_2021-11-08_2021-11-14_sorted.csv
