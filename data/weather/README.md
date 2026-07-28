# Sensor.Community 


The dataset contains 1 file per sensor each day. The schema of the csv file depends on the sensor type. Below we give an overview of these schemas and also give example data.

As a first step, we focus on temperature and humidity only. We first drop files that do not include temperature and then  project all remaining files onto the following schema:
`sensor_id|lat|lon|timestamp|temperature|humidity`. 


## Sensor Types & Schemas (November 2021)

Source: `archive.sensor.community/csv_per_month/2021-11/` and `archive.sensor.community/2021/2021-11-08/`


| Sensor Type | Category | Description | # Columns | Columns |
|---|---|---|---|---|
| bme280 | Temperature / Humidity / Pressure | Bosch combo sensor | 11 | sensor_id, sensor_type, location, lat, lon, timestamp, pressure, altitude, pressure_sealevel, temperature, humidity |
| bmp180 | Temperature / Pressure | Older Bosch pressure sensor | 10 | sensor_id, sensor_type, location, lat, lon, timestamp, pressure, altitude, pressure_sealevel, temperature |
| bmp280 | Temperature / Pressure | Newer Bosch pressure sensor (no humidity) | 10 | sensor_id, sensor_type, location, lat, lon, timestamp, pressure, altitude, pressure_sealevel, temperature |
| dht22 | Temperature / Humidity | Common, inexpensive temp/humidity sensor | 8 | sensor_id, sensor_type, location, lat, lon, timestamp, temperature, humidity |
| ds18b20 | Temperature | Waterproof digital temperature probe | 7 | sensor_id, sensor_type, location, lat, lon, timestamp, temperature |
| hpm | Particulate Matter | Honeywell PM sensor | 8 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, P2 |
| htu21d | Temperature / Humidity | Alternative to DHT22, more outdoor-stable | 8 | sensor_id, sensor_type, location, lat, lon, timestamp, temperature, humidity |
| laerm | Noise | Sound level sensor | 11 | sensor_id, sensor_type, location, lat, lon, timestamp, noise_LAeq, noise_LA_min, noise_LA_max, noise_LA01, noise_LA95 |
| pms1003 | Particulate Matter | Plantower PM sensor | 9 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, P2, P0 |
| pms3003 | Particulate Matter | Plantower PM sensor | 9 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, P2, P0 |
| pms5003 | Particulate Matter | Plantower PM sensor | 9 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, P2, P0 |
| pms6003 | Particulate Matter | Plantower PM sensor | 9 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, P2, P0 |
| pms7003 | Particulate Matter | Plantower PM sensor | 9 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, P2, P0 |
| ppd42ns | Particulate Matter | Shinyei dust sensor (older/simpler) | 12 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, durP1, ratioP1, P2, durP2, ratioP2 |
| sds011 | Particulate Matter | Nova Fitness PM sensor — most common sensor in the network | 12 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, durP1, ratioP1, P2, durP2, ratioP2 |
| sht11 | Temperature / Humidity | Sensirion temp/humidity sensor | 8 | sensor_id, sensor_type, location, lat, lon, timestamp, temperature, humidity |
| sht30 | Temperature / Humidity | Sensirion temp/humidity sensor | 8 | sensor_id, sensor_type, location, lat, lon, timestamp, temperature, humidity |
| sht31 | Temperature / Humidity | Sensirion temp/humidity sensor | 8 | sensor_id, sensor_type, location, lat, lon, timestamp, temperature, humidity |
| sht35 | Temperature / Humidity | Sensirion temp/humidity sensor | 8 | sensor_id, sensor_type, location, lat, lon, timestamp, temperature, humidity |
| sht85 | Temperature / Humidity | Sensirion temp/humidity sensor | 8 | sensor_id, sensor_type, location, lat, lon, timestamp, temperature, humidity |
| sps30 | Particulate Matter | Sensirion PM sensor (adds particle-count channels) | 16 | sensor_id, sensor_type, location, lat, lon, timestamp, P1, P4, P2, P0, N10, N4, N25, N1, N05, TS |

## Example Data (2021-11-08)

Three sample rows per sensor type, taken from a real sensor file in `archive.sensor.community/2021/2021-11-08/`.

### bme280

| sensor_id | sensor_type | location | lat | lon | timestamp | pressure | altitude | pressure_sealevel | temperature | humidity |
|---|---|---|---|---|---|---|---|---|---|---|
| 113 | BME280 | 45999 | 48.808 | 9.182 | 2021-11-08T00:00:13 | 98523.84 |  |  | 7.24 | 93.40 |
| 113 | BME280 | 45999 | 48.808 | 9.182 | 2021-11-08T00:02:41 | 98522.38 |  |  | 7.21 | 94.89 |
| 113 | BME280 | 45999 | 48.808 | 9.182 | 2021-11-08T00:05:10 | 98522.16 |  |  | 7.23 | 94.28 |

### bmp180

| sensor_id | sensor_type | location | lat | lon | timestamp | pressure | altitude | pressure_sealevel | temperature |
|---|---|---|---|---|---|---|---|---|---|
| 3286 | BMP180 | 1654 | 52.002 | 10.266 | 2021-11-08T00:02:10 | 99600.00 |  |  | 7.90 |
| 3286 | BMP180 | 1654 | 52.002 | 10.266 | 2021-11-08T00:04:43 | 99594.00 |  |  | 7.90 |
| 3286 | BMP180 | 1654 | 52.002 | 10.266 | 2021-11-08T00:07:16 | 99595.00 |  |  | 7.80 |

### bmp280

| sensor_id | sensor_type | location | lat | lon | timestamp | pressure | altitude | pressure_sealevel | temperature |
|---|---|---|---|---|---|---|---|---|---|
| 1532 | BMP280 | 759 | 53.170 | 8.210 | 2021-11-08T00:02:09 | 101305.00 |  |  | 6.83 |
| 1532 | BMP280 | 759 | 53.170 | 8.210 | 2021-11-08T00:04:51 | 101322.66 |  |  | 6.92 |
| 1532 | BMP280 | 759 | 53.170 | 8.210 | 2021-11-08T00:07:19 | 101362.47 |  |  | 7.20 |

### dht22

| sensor_id | sensor_type | location | lat | lon | timestamp | temperature | humidity |
|---|---|---|---|---|---|---|---|
| 93 | DHT22 | 16232 | 48.800 | 9.002 | 2021-11-08T00:01:38 | 6.00 | 99.90 |
| 93 | DHT22 | 16232 | 48.800 | 9.002 | 2021-11-08T00:04:06 | 6.00 | 99.90 |
| 93 | DHT22 | 16232 | 48.800 | 9.002 | 2021-11-08T00:06:34 | 6.00 | 99.90 |

### ds18b20

| sensor_id | sensor_type | location | lat | lon | timestamp | temperature |
|---|---|---|---|---|---|---|
| 11301 | DS18B20 | 5706 | 50.650 | 13.380 | 2021-11-08T00:02:27 | 5.06 |
| 11301 | DS18B20 | 5706 | 50.650 | 13.380 | 2021-11-08T00:04:54 | 5.06 |
| 11301 | DS18B20 | 5706 | 50.650 | 13.380 | 2021-11-08T00:07:22 | 5.06 |

### hpm

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | P2 |
|---|---|---|---|---|---|---|---|
| 26640 | HPM | 14269 | 47.358 | 0.724 | 2021-11-08T00:00:40 | 46.0 | 48.0 |
| 26640 | HPM | 14269 | 47.358 | 0.724 | 2021-11-08T00:03:22 | 42.0 | 44.0 |
| 26640 | HPM | 14269 | 47.358 | 0.724 | 2021-11-08T00:06:02 | 46.0 | 48.0 |

### htu21d

| sensor_id | sensor_type | location | lat | lon | timestamp | temperature | humidity |
|---|---|---|---|---|---|---|---|
| 216 | HTU21D | 45701 | 48.81287245 | 9.14186865 | 2021-11-08T00:01:20 | 7.92 | 79.17 |
| 216 | HTU21D | 45701 | 48.81287245 | 9.14186865 | 2021-11-08T00:03:47 | 8.20 | 79.29 |
| 216 | HTU21D | 45701 | 48.81287245 | 9.14186865 | 2021-11-08T00:06:17 | 8.09 | 78.57 |

### laerm

| sensor_id | sensor_type | location | lat | lon | timestamp | noise_LAeq | noise_LA_min | noise_LA_max | noise_LA01 | noise_LA95 |
|---|---|---|---|---|---|---|---|---|---|---|
| 4048 | Laerm | 2038 | 51.728 | 6.674 | 2021-11-08T00:00:58 | 48.53 | 34.31 | 65.80 |  |  |
| 4048 | Laerm | 2038 | 51.728 | 6.674 | 2021-11-08T00:03:25 | 38.38 | 33.90 | 41.30 |  |  |
| 4048 | Laerm | 2038 | 51.728 | 6.674 | 2021-11-08T00:05:57 | 46.60 | 34.31 | 65.59 |  |  |

### pms1003

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | P2 | P0 |
|---|---|---|---|---|---|---|---|---|
| 26720 | PMS1003 | 15950 | 51.112 | 6.966 | 2021-11-08T00:01:24 | 004 | 003 |  |
| 26720 | PMS1003 | 15950 | 51.112 | 6.966 | 2021-11-08T00:03:25 | 003 | 002 |  |
| 26720 | PMS1003 | 15950 | 51.112 | 6.966 | 2021-11-08T00:05:26 | 003 | 002 |  |

### pms3003

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | P2 | P0 |
|---|---|---|---|---|---|---|---|---|
| 12542 | PMS3003 | 6337 | 49.556 | 25.594 | 2021-11-08T00:01:44 | 23.17 | 12.97 |  |
| 12542 | PMS3003 | 6337 | 49.556 | 25.594 | 2021-11-08T00:04:12 | 29.37 | 13.97 |  |
| 12542 | PMS3003 | 6337 | 49.556 | 25.594 | 2021-11-08T00:06:39 | 35.23 | 14.93 |  |

### pms5003

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | P2 | P0 |
|---|---|---|---|---|---|---|---|---|
| 10689 | PMS5003 | 5394 | 27.222 | 78.010 | 2021-11-08T00:01:25 | 505.50 | 382.75 | 160.00 |
| 10689 | PMS5003 | 5394 | 27.222 | 78.010 | 2021-11-08T00:03:57 | 472.00 | 373.00 | 162.25 |
| 10689 | PMS5003 | 5394 | 27.222 | 78.010 | 2021-11-08T00:06:29 | 497.25 | 382.75 | 160.25 |

### pms6003

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | P2 | P0 |
|---|---|---|---|---|---|---|---|---|
| 46591 | PMS6003 | 32314 | 48.748 | 9.656 | 2021-11-08T03:45:07 | 9.00 | 8.50 | 6.00 |
| 46591 | PMS6003 | 32314 | 48.748 | 9.656 | 2021-11-08T03:47:54 | 17.00 | 15.00 | 8.50 |
| 46591 | PMS6003 | 32314 | 48.748 | 9.656 | 2021-11-08T03:50:52 | 17.25 | 15.75 | 10.75 |

### pms7003

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | P2 | P0 |
|---|---|---|---|---|---|---|---|---|
| 8761 | PMS7003 | 4417 | 42.140 | 24.794 | 2021-11-08T00:00:33 | 64.00 | 43.40 | 28.00 |
| 8761 | PMS7003 | 4417 | 42.140 | 24.794 | 2021-11-08T00:03:03 | 60.60 | 44.20 | 29.20 |
| 8761 | PMS7003 | 4417 | 42.140 | 24.794 | 2021-11-08T00:05:30 | 59.00 | 43.60 | 28.40 |

### ppd42ns

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | durP1 | ratioP1 | P2 | durP2 | ratioP2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 107 | PPD42NS | 49 | 48.530 | 9.200 | 2021-11-08T00:02:19 | 538.19 | 311790.00 | 1.04 | 0.62 | 0.00 | 0.00 |
| 107 | PPD42NS | 49 | 48.530 | 9.200 | 2021-11-08T00:04:46 | 1407.63 | 815191.00 | 2.72 | 0.62 | 0.00 | 0.00 |
| 107 | PPD42NS | 49 | 48.530 | 9.200 | 2021-11-08T00:07:13 | 869.41 | 504405.00 | 1.68 | 0.62 | 0.00 | 0.00 |

### sds011

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | durP1 | ratioP1 | P2 | durP2 | ratioP2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 92 | SDS011 | 16232 | 48.800 | 9.002 | 2021-11-08T00:01:37 | 13.97 |  |  | 10.27 |  |  |
| 92 | SDS011 | 16232 | 48.800 | 9.002 | 2021-11-08T00:04:06 | 17.73 |  |  | 10.43 |  |  |
| 92 | SDS011 | 16232 | 48.800 | 9.002 | 2021-11-08T00:06:33 | 14.43 |  |  | 10.37 |  |  |

### sht11

| sensor_id | sensor_type | location | lat | lon | timestamp | temperature | humidity |
|---|---|---|---|---|---|---|---|
| 38798 | SHT11 | 24546 | 52.240 | 16.826 | 2021-11-08T00:03:01 | 8.40 | 99.90 |
| 38798 | SHT11 | 24546 | 52.240 | 16.826 | 2021-11-08T00:08:03 | 8.50 | 99.90 |
| 38798 | SHT11 | 24546 | 52.240 | 16.826 | 2021-11-08T00:13:06 | 8.50 | 99.90 |

### sht30

| sensor_id | sensor_type | location | lat | lon | timestamp | temperature | humidity |
|---|---|---|---|---|---|---|---|
| 11999 | SHT30 | 40817 | 51.520 | 9.954 | 2021-11-08T00:02:32 | 8.10 | 99.90 |
| 11999 | SHT30 | 40817 | 51.520 | 9.954 | 2021-11-08T00:02:32 | 8.52 | 81.34 |
| 11999 | SHT30 | 40817 | 51.520 | 9.954 | 2021-11-08T00:05:00 | 8.20 | 99.90 |

### sht31

| sensor_id | sensor_type | location | lat | lon | timestamp | temperature | humidity |
|---|---|---|---|---|---|---|---|
| 1886 | SHT31 | 943 | 51.568 | 6.998 | 2021-11-08T00:02:01 | 6.10 | 99.90 |
| 1886 | SHT31 | 943 | 51.568 | 6.998 | 2021-11-08T00:04:32 | 6.20 | 99.90 |
| 1886 | SHT31 | 943 | 51.568 | 6.998 | 2021-11-08T00:07:01 | 6.20 | 99.90 |

### sht35

| sensor_id | sensor_type | location | lat | lon | timestamp | temperature | humidity |
|---|---|---|---|---|---|---|---|
| 47757 | SHT35 | 22147 | 52.388 | 13.390 | 2021-11-08T00:01:05 | 7.41 | 87.23 |
| 47757 | SHT35 | 22147 | 52.388 | 13.390 | 2021-11-08T00:03:31 | 7.48 | 87.16 |
| 47757 | SHT35 | 22147 | 52.388 | 13.390 | 2021-11-08T00:06:03 | 7.47 | 87.11 |

### sht85

| sensor_id | sensor_type | location | lat | lon | timestamp | temperature | humidity |
|---|---|---|---|---|---|---|---|
| 35085 | SHT85 | 21267 | 51.032 | 6.998 | 2021-11-08T00:01:00 | 7.32 | 92.39 |
| 35085 | SHT85 | 21267 | 51.032 | 6.998 | 2021-11-08T00:03:28 | 7.14 | 92.81 |
| 35085 | SHT85 | 21267 | 51.032 | 6.998 | 2021-11-08T00:06:02 | 7.05 | 92.94 |

### sps30

| sensor_id | sensor_type | location | lat | lon | timestamp | P1 | P4 | P2 | P0 | N10 | N4 | N25 | N1 | N05 | TS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 18453 | SPS30 | 9356 | 52.202 | 20.950 | 2021-11-08T00:00:39 | 9.32 | 9.32 | 9.30 | 8.78 | 70.11 | 70.09 | 70.06 | 69.63 | 58.56 | 0.50 |
| 18453 | SPS30 | 9356 | 52.202 | 20.950 | 2021-11-08T00:01:57 | 9.43 | 9.43 | 9.40 | 8.87 | 70.81 | 70.79 | 70.76 | 70.31 | 59.12 | 0.50 |
| 18453 | SPS30 | 9356 | 52.202 | 20.950 | 2021-11-08T00:03:07 | 9.94 | 9.94 | 9.92 | 9.37 | 74.83 | 74.82 | 74.79 | 74.32 | 62.51 | 0.49 |



