-- D1 Energy vs market: DE-LU price, renewables share, index level (hourly sample)
SELECT ts_utc, price_eur_mwh, round(renewables_share, 3) AS renewables_share,
       round(carbon_intensity_g_kwh) AS carbon_g_kwh, index_level,
       eq_movers_up, eq_movers_down
FROM gold.mart_zone_pulse
WHERE bidding_zone = 'DE-LU' AND extract(minute FROM ts_utc) = 0
  AND ts_utc BETWEEN TIMESTAMP '2021-11-08 07:00' AND TIMESTAMP '2021-11-08 18:00'
ORDER BY ts_utc;

-- D2 Weather -> load -> price: per-zone correlations over the whole week
SELECT bidding_zone,
       round(corr(temp_avg_c, load_mw), 3) AS corr_temp_load,
       round(corr(load_mw, price_eur_mwh), 3) AS corr_load_price,
       round(corr(renewables_share, price_eur_mwh), 3) AS corr_renewshare_price,
       count(*) FILTER (temp_avg_c IS NOT NULL AND load_mw IS NOT NULL) AS samples
FROM gold.mart_zone_pulse
GROUP BY 1 ORDER BY 1;

-- D3 News pulse: top energy topics by volume with tone, day by day (top 3/day)
SELECT publication_date, topic, doc_count, round(tone_avg, 2) AS tone_avg,
       conflict_event_count
FROM (SELECT *, row_number() OVER (PARTITION BY publication_date
                                  ORDER BY doc_count DESC) AS rnk
      FROM gold.fact_topic_news_day)
WHERE rnk <= 3
ORDER BY publication_date, doc_count DESC;

-- D4 Company profile: TotalEnergies (market + news + fundamentals in one row)
SELECT company_name, sector, country, primary_instrument_id,
       last_close, round(week_return, 4) AS week_return,
       news_docs, round(news_tone_avg, 2) AS news_tone_avg,
       revenue, revenue_unit, net_income, fundamentals_period_end,
       has_fundamentals, has_news
FROM gold.mart_company_profile
WHERE company_name ILIKE '%TotalEnergies%';

-- D5 Feed health: active instruments, price coverage, latest activity per exchange
-- (the movers half of this dashboard needs weekday tick files: weekend price
--  fields are zero placeholders, so bar returns only exist under full replay)
SELECT i.exchange_code, d.sec_type,
       count(DISTINCT d.instrument_id) AS instruments_active,
       count(DISTINCT d.instrument_id) FILTER (d.close IS NOT NULL) AS with_real_price,
       sum(d.tick_count) AS ticks,
       max(d.last_event_time_utc) AS latest_event_utc
FROM gold.fact_instrument_day d
JOIN gold.dim_instrument i USING (instrument_id)
GROUP BY 1, 2 ORDER BY 1, 2;
