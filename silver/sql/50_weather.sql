-- Weather observations: plausibility filter, Western-Europe filter, region tag.
SET TimeZone = 'UTC';
-- Rejects (sensor error sentinels, out-of-region coordinates) are kept separately.

CREATE OR REPLACE TEMP VIEW _weather_classified AS
SELECT sensorID AS sensor_id, lat, lon,
       timestamp AS observation_time_utc,   -- source timestamps are UTC
       temperature AS temperature_c,
       humidity AS humidity_pct,
       CASE
           WHEN temperature IS NULL OR temperature < -40 OR temperature > 60
               THEN 'implausible temperature'
           WHEN humidity IS NOT NULL AND (humidity < 0 OR humidity > 100)
               THEN 'implausible humidity'
           WHEN lat IS NULL OR lon IS NULL OR lat < 35 OR lat > 72 OR lon < -25 OR lon > 32
               THEN 'outside western europe'
       END AS reject_reason,
       -- crude country tag via bounding boxes, checked small-to-large
       CASE
           WHEN lat BETWEEN 50.7 AND 53.7 AND lon BETWEEN 3.3 AND 7.3   THEN 'NL'
           WHEN lat BETWEEN 49.5 AND 51.6 AND lon BETWEEN 2.5 AND 6.4   THEN 'BE'
           WHEN lat BETWEEN 45.8 AND 47.9 AND lon BETWEEN 5.9 AND 10.5  THEN 'CH'
           WHEN lat BETWEEN 46.3 AND 49.1 AND lon BETWEEN 9.5 AND 17.2  THEN 'AT'
           WHEN lat BETWEEN 47.2 AND 55.1 AND lon BETWEEN 5.8 AND 15.1  THEN 'DE'
           WHEN lat BETWEEN 42.3 AND 51.1 AND lon BETWEEN -5.2 AND 8.3  THEN 'FR'
       END AS country_approx
FROM bronze.weather;

CREATE OR REPLACE TABLE silver.weather_observation AS
SELECT sensor_id, lat, lon, observation_time_utc,
       temperature_c, humidity_pct, country_approx
FROM _weather_classified WHERE reject_reason IS NULL;

CREATE OR REPLACE TABLE silver.weather_rejects AS
SELECT sensor_id, lat, lon, observation_time_utc,
       temperature_c, humidity_pct, reject_reason
FROM _weather_classified WHERE reject_reason IS NOT NULL;
