-- Zone-level energy and weather facts on the 15-minute grid.
SET TimeZone = 'UTC';

-- Fuel groups and emission factors (tCO2/MWh) from the ENTSO-E column docs;
-- fuels without a documented factor are excluded from the carbon estimate.
CREATE OR REPLACE TEMP VIEW _fuel_map AS
SELECT * FROM (VALUES
    ('Solar',                            'renewable', 0.045),
    ('Wind_Offshore',                    'renewable', 0.011),
    ('Wind_Onshore',                     'renewable', 0.011),
    ('Hydro_Run-of-river_and_poundage',  'renewable', 0.024),
    ('Hydro_Water_Reservoir',            'renewable', 0.024),
    ('Hydro_Pumped_Storage',             'renewable', 0.024),
    ('Biomass',                          'renewable', 0.23),
    ('Geothermal',                       'renewable', NULL),
    ('Other_renewable',                  'renewable', NULL),
    ('Fossil_Gas',                       'fossil',    0.49),
    ('Fossil_Hard_coal',                 'fossil',    0.85),
    ('Fossil_Brown_coal_Lignite',        'fossil',    1.0),
    ('Fossil_Oil',                       'fossil',    0.65),
    ('Nuclear',                          'nuclear',   0.012),
    ('Waste',                            'other',     NULL),
    ('Other',                            'other',     NULL)
) AS t(fuel, fuel_group, emission_factor);

CREATE OR REPLACE TABLE gold.fact_energy_15min AS
WITH spine AS (SELECT DISTINCT ts_utc FROM silver.grid_load),
zones AS (SELECT unnest(['DE-LU', 'FR', 'NL', 'AT', 'BE', 'CH']) AS bidding_zone),
gen AS (
    SELECT g.ts_utc, g.bidding_zone,
           sum(g.mw) FILTER (m.fuel_group = 'renewable') AS gen_renewable_mw,
           sum(g.mw) FILTER (m.fuel_group = 'fossil')    AS gen_fossil_mw,
           sum(g.mw) FILTER (m.fuel_group = 'nuclear')   AS gen_nuclear_mw,
           sum(g.mw) FILTER (m.fuel_group = 'other')     AS gen_other_mw,
           sum(g.mw) AS gen_total_mw,
           sum(g.mw * m.emission_factor) FILTER (m.emission_factor IS NOT NULL)
               / nullif(sum(g.mw) FILTER (m.emission_factor IS NOT NULL), 0)
               * 1000 AS carbon_intensity_g_kwh
    FROM silver.grid_generation g
    JOIN _fuel_map m USING (fuel)
    WHERE g.kind = 'aggregated'
    GROUP BY 1, 2),
flows AS (
    SELECT ts_utc, zone AS bidding_zone, sum(mw_out) - sum(mw_in) AS net_export_mw
    FROM (SELECT ts_utc, from_zone AS zone, mw AS mw_out, 0 AS mw_in FROM silver.grid_flow
          UNION ALL
          SELECT ts_utc, to_zone, 0, mw FROM silver.grid_flow)
    GROUP BY 1, 2)
SELECT s.ts_utc, z.bidding_zone,
       p.price_eur_mwh,           -- hourly day-ahead price, constant within hour
       l.load_mw,
       g.gen_renewable_mw, g.gen_fossil_mw, g.gen_nuclear_mw, g.gen_other_mw,
       g.gen_total_mw,
       g.gen_renewable_mw / nullif(g.gen_total_mw, 0) AS renewables_share,
       g.carbon_intensity_g_kwh,
       f.net_export_mw
FROM spine s
CROSS JOIN zones z
LEFT JOIN silver.electricity_price p
       ON p.bidding_zone = z.bidding_zone AND p.ts_utc = date_trunc('hour', s.ts_utc)
LEFT JOIN silver.grid_load l ON l.bidding_zone = z.bidding_zone AND l.ts_utc = s.ts_utc
LEFT JOIN gen g ON g.bidding_zone = z.bidding_zone AND g.ts_utc = s.ts_utc
LEFT JOIN flows f ON f.bidding_zone = z.bidding_zone AND f.ts_utc = s.ts_utc;

-- Weather aggregated to zone x 15 min (country tag from silver, DE feeds DE-LU).
CREATE OR REPLACE TABLE gold.fact_weather_15min AS
SELECT CASE country_approx WHEN 'DE' THEN 'DE-LU' ELSE country_approx END AS bidding_zone,
       time_bucket(INTERVAL 15 MINUTE, observation_time_utc) AS ts_utc,
       avg(temperature_c) AS temp_avg_c,
       min(temperature_c) AS temp_min_c,
       max(temperature_c) AS temp_max_c,
       avg(humidity_pct) AS humidity_avg_pct,
       count(DISTINCT sensor_id) AS sensor_count,
       count(*) AS observation_count
FROM silver.weather_observation
WHERE country_approx IS NOT NULL
GROUP BY 1, 2;
