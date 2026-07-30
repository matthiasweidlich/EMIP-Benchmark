#!/usr/bin/env python3
"""Data-coverage validation plots for the EMIP silver/gold layers.

Draws time series across every dataset for the benchmark week
(2021-11-08 .. 2021-11-14, all UTC) so gaps are visible at a glance:
which hours/zones/days actually contain market ticks, electricity data,
weather observations, and news. Output: gold/plots/*.png

Usage: .venv/bin/python gold/validate_plots.py [db_path]
"""
import os
import sys

import duckdb
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

DB = sys.argv[1] if len(sys.argv) > 1 else "silver/emip.duckdb"
OUT = os.path.join(os.path.dirname(__file__) or ".", "plots")
os.makedirs(OUT, exist_ok=True)

con = duckdb.connect(DB, read_only=True)
con.execute("SET TimeZone='UTC'")

WEEK_LO, WEEK_HI = "2021-11-07 23:00", "2021-11-14 23:00"
ZONES = ["AT", "BE", "CH", "DE-LU", "FR", "NL"]
ZCOL = {z: c for z, c in zip(ZONES, plt.rcParams["axes.prop_cycle"].by_key()["color"])}


def q(sql):
    return con.sql(sql).df()


def on_grid(df, tcol, ycol, freq):
    """Series on the complete week grid: missing buckets become NaN so that
    real coverage gaps show as line breaks instead of bridging segments."""
    idx = pd.date_range(WEEK_LO, WEEK_HI, freq=freq)
    return df.set_index(tcol)[ycol].reindex(idx)


def style_week_axis(ax):
    ax.set_xlim(mdates.datestr2num(WEEK_LO), mdates.datestr2num(WEEK_HI))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d"))
    ax.grid(True, alpha=0.3)
    # shade the weekend (Sat 13 / Sun 14)
    ax.axvspan(mdates.datestr2num("2021-11-13 00:00"),
               mdates.datestr2num("2021-11-14 23:00"), color="gray", alpha=0.08)
    # light shading for workday hours (09:00-17:00 CET = 08:00-16:00 UTC)
    for d in range(8, 13):
        ax.axvspan(mdates.datestr2num(f"2021-11-{d:02d} 08:00"),
                   mdates.datestr2num(f"2021-11-{d:02d} 16:00"),
                   color="tab:orange", alpha=0.06)


def save(fig, name):
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.text(0.01, 0.002, "shading: workday hours 09-17 CET (amber), weekend (gray)",
             fontsize=7, color="gray")
    fig.savefig(os.path.join(OUT, name), dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote gold/plots/{name}")


# ---------------------------------------------------------------- 1 coverage
tick = q("""SELECT time_bucket(INTERVAL 1 HOUR, event_time_utc) h, count(*) n,
                   count(*) FILTER (last IS NOT NULL OR bid IS NOT NULL OR ask IS NOT NULL) n_price
            FROM silver.market_tick GROUP BY 1 ORDER BY 1""")
energy = q("""SELECT time_bucket(INTERVAL 1 HOUR, ts_utc) h,
                     count(price_eur_mwh) n_price, count(load_mw) n_load, count(gen_total_mw) n_gen
              FROM gold.fact_energy_15min GROUP BY 1 ORDER BY 1""")
weather = q("""SELECT time_bucket(INTERVAL 1 HOUR, observation_time_utc) h, count(*) n
               FROM silver.weather_observation GROUP BY 1 ORDER BY 1""")
has_all_docs = q("""SELECT count(*) n FROM information_schema.columns
                    WHERE table_schema = 'silver' AND table_name = 'news_document'
                      AND column_name = 'is_energy'""").n[0] > 0
news = q(f"""SELECT publication_date d, count(*) n,
                    count(*) FILTER ({'is_energy' if has_all_docs else 'true'}) n_energy
             FROM silver.news_document GROUP BY 1 ORDER BY 1""")

fig, axes = plt.subplots(4, 1, figsize=(14, 11), sharex=True)
fig.suptitle("EMIP data coverage by hour, benchmark week 2021-11-08..14 (UTC)", fontsize=14)

ax = axes[0]
for col, lab, c in (("n", "all ticks", "tab:blue"),
                    ("n_price", "ticks with real price", "tab:red")):
    s = on_grid(tick, "h", col, "1h")
    ax.plot(s.index, s.values, drawstyle="steps-post", label=lab, color=c)
ax.set_yscale("symlog")
ax.set_ylabel("DEBS ticks / h")
ax.legend(loc="upper right", fontsize=8)
ax.set_title("01 market ticks (weekend rows are zero-price status updates; "
             "weekday coverage = locally ingested files)", fontsize=9, loc="left")

ax = axes[1]
ax.plot(energy.h, energy.n_price, drawstyle="steps-post", label="price rows (6 zones x 4)")
ax.plot(energy.h, energy.n_load, drawstyle="steps-post", lw=2.5,
        label="load rows (DE-LU/FR/NL only)")
ax.plot(energy.h, energy.n_gen, drawstyle="steps-post", ls="--",
        label="generation rows (same 3 zones)")
ax.set_ylabel("ENTSO-E rows / h")
ax.set_ylim(bottom=0)
ax.legend(loc="upper right", fontsize=8)
ax.set_title("05 electricity: 15-min rows with non-NULL values per hour", fontsize=9, loc="left")

ax = axes[2]
ax.plot(weather.h, weather.n, drawstyle="steps-post", color="tab:green")
ax.set_ylabel("weather obs / h")
ax.set_ylim(bottom=0)
ax.set_title("06 weather: Sensor.Community observations per hour", fontsize=9, loc="left")

ax = axes[3]
ax.bar(news.d, news.n, width=0.8, color="tab:purple", alpha=0.4,
       label="all GKG documents")
ax.bar(news.d, news.n_energy, width=0.8, color="tab:purple", alpha=0.9,
       label="energy-tagged")
ax.set_ylabel("news docs / day")
ax.legend(loc="upper right", fontsize=8)
ax.set_title("04 GDELT: documents per publication day (date granularity only)",
             fontsize=9, loc="left")
for ax in axes:
    style_week_axis(ax)
save(fig, "01_coverage_overview.png")

# ---------------------------------------------------------------- 2 market
bars = q("""SELECT b.bucket_start, i.exchange_code, sum(b.tick_count) n
            FROM gold.fact_market_bar b JOIN gold.dim_instrument i USING (instrument_id)
            GROUP BY 1, 2 ORDER BY 1""")
top_eq = q("""SELECT instrument_id FROM gold.fact_instrument_day
              WHERE sec_type = 'E' AND close IS NOT NULL
              GROUP BY 1 ORDER BY sum(trade_tick_count) DESC LIMIT 4""").instrument_id
top_ix = q("""SELECT DISTINCT ON (i.exchange_code) d.instrument_id
              FROM gold.fact_instrument_day d JOIN gold.dim_instrument i USING (instrument_id)
              WHERE d.sec_type = 'I' AND d.close IS NOT NULL
              GROUP BY i.exchange_code, d.instrument_id
              ORDER BY i.exchange_code, sum(d.trade_tick_count) DESC""").instrument_id

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle("01 DEBS market detail (UTC)", fontsize=14)

ax = axes[0]
for exch, g in bars.groupby("exchange_code"):
    s = on_grid(g, "bucket_start", "n", "5min")
    ax.plot(s.index, s.values, drawstyle="steps-post", label=exch, alpha=0.8)
ax.set_yscale("symlog")
ax.set_ylabel("ticks / 5 min")
ax.legend(loc="upper right", fontsize=8)
ax.set_title("tick volume by exchange", fontsize=9, loc="left")

for ax, ids, kind in ((axes[1], top_eq, "equities"), (axes[2], top_ix, "indices")):
    for iid in ids:
        g = q(f"""SELECT bucket_start, close FROM gold.fact_market_bar
                  WHERE instrument_id = '{iid}' AND close IS NOT NULL ORDER BY 1""")
        s = on_grid(g, "bucket_start", "close", "5min")
        ax.plot(s.index, 100 * s.values / g.close.iloc[0], label=iid, alpha=0.85)
    ax.set_ylabel("close, first bar = 100")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"most-traded {kind}: normalized 5-min close", fontsize=9, loc="left")
for ax in axes:
    style_week_axis(ax)
save(fig, "02_market.png")

# ---------------------------------------------------------------- 3 energy
en = q("SELECT * FROM gold.fact_energy_15min ORDER BY ts_utc")
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle("05 electricity: prices, load, DE-LU generation mix (UTC)", fontsize=14)

ax = axes[0]
for z in ZONES:
    g = en[en.bidding_zone == z]
    ax.plot(g.ts_utc, g.price_eur_mwh, label=z, color=ZCOL[z], alpha=0.8)
ax.set_ylabel("day-ahead EUR/MWh")
ax.legend(loc="upper right", fontsize=8, ncols=6)
ax.set_title("day-ahead price by zone", fontsize=9, loc="left")

ax = axes[1]
for z in ZONES:
    g = en[(en.bidding_zone == z) & en.load_mw.notna()]
    if len(g):
        ax.plot(g.ts_utc, g.load_mw / 1000, label=z, color=ZCOL[z], alpha=0.8)
ax.set_ylabel("load GW")
ax.legend(loc="upper right", fontsize=8)
ax.set_title("actual load (only DE-LU / FR / NL present in the ENTSO-E extract)",
             fontsize=9, loc="left")

ax = axes[2]
g = en[en.bidding_zone == "DE-LU"]
ax.stackplot(g.ts_utc,
             g.gen_renewable_mw.fillna(0) / 1000, g.gen_nuclear_mw.fillna(0) / 1000,
             g.gen_fossil_mw.fillna(0) / 1000, g.gen_other_mw.fillna(0) / 1000,
             labels=["renewable", "nuclear", "fossil", "other"],
             colors=["tab:green", "tab:orange", "tab:gray", "tab:brown"], alpha=0.8)
ax.set_ylabel("DE-LU generation GW")
ax.legend(loc="upper right", fontsize=8, ncols=4)
ax.set_title("DE-LU generation mix", fontsize=9, loc="left")
for ax in axes:
    style_week_axis(ax)
save(fig, "03_energy.png")

# ---------------------------------------------------------------- 4 weather
we = q("SELECT * FROM gold.fact_weather_15min ORDER BY ts_utc")
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
fig.suptitle("06 weather: zone aggregates from Sensor.Community (UTC)", fontsize=14)
for ax, col, lab in ((axes[0], "temp_avg_c", "avg temperature degC"),
                     (axes[1], "sensor_count", "distinct sensors / 15 min")):
    for z in ZONES:
        g = we[we.bidding_zone == z]
        ax.plot(g.ts_utc, g[col], label=z, color=ZCOL[z], alpha=0.8)
    ax.set_ylabel(lab)
    ax.legend(loc="upper right", fontsize=8, ncols=6)
    style_week_axis(ax)
axes[1].set_yscale("log")
save(fig, "04_weather.png")

# ---------------------------------------------------------------- 5 news
topics = q("""SELECT topic FROM gold.fact_topic_news_day
              GROUP BY 1 ORDER BY sum(doc_count) DESC LIMIT 6""").topic.tolist()
tn = q("SELECT * FROM gold.fact_topic_news_day ORDER BY publication_date")
cn = q("""SELECT publication_date d, sum(doc_count) docs, count(DISTINCT company_id) companies
          FROM gold.fact_company_news_day GROUP BY 1 ORDER BY 1""")

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle("04 GDELT news: topics, tone, company mentions (publication day, UTC)", fontsize=14)

ax = axes[0]
bottom = None
for t in topics:
    g = tn[tn.topic == t].set_index("publication_date").doc_count
    g = g.reindex(sorted(tn.publication_date.unique()), fill_value=0)
    ax.bar(g.index, g.values, width=0.8, bottom=bottom, label=t, alpha=0.85)
    bottom = g.values if bottom is None else bottom + g.values
ax.set_ylabel("docs / day")
ax.legend(loc="upper right", fontsize=8, ncols=3)
ax.set_title("documents per day, top topics stacked", fontsize=9, loc="left")

ax = axes[1]
for t in ["ENERGY_GENERAL", "OIL", "COAL", "GAS_NATURAL", "RENEWABLE_GENERAL"]:
    g = tn[tn.topic == t]
    if len(g):
        ax.plot(g.publication_date, g.tone_avg, marker="o", label=t, alpha=0.85)
ax.axhline(0, color="black", lw=0.5)
ax.set_ylabel("avg tone")
ax.margins(y=0.25)
ax.legend(loc="lower center", fontsize=8, ncols=5)
ax.set_title("average document tone by topic", fontsize=9, loc="left")

ax = axes[2]
ax.bar(cn.d, cn.docs, width=0.8, color="tab:cyan", alpha=0.7, label="docs with resolved ticker")
ax.plot(cn.d, cn.companies, color="tab:red", marker="o", label="distinct companies")
ax.set_ylabel("per day")
ax.legend(loc="upper right", fontsize=8)
ax.set_title("company-resolved news mentions", fontsize=9, loc="left")
for ax in axes:
    style_week_axis(ax)
save(fig, "05_news.png")

# ---------------------------------------------------------------- 6 fundamentals
ff = q("""SELECT date_trunc('month', period_end) m, count(*) facts,
                 count(DISTINCT company_id) companies
          FROM silver.financial_fact GROUP BY 1 ORDER BY 1""")
fl = q("""SELECT metric, count(DISTINCT company_id) companies
          FROM gold.fact_fundamentals_latest GROUP BY 1 ORDER BY 2 DESC""")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.5), width_ratios=[2, 1])
fig.suptitle("03 ESEF fundamentals (static in-week; period coverage + metric coverage)",
             fontsize=13)
ax1.bar(ff.m, ff.facts, width=20, color="tab:blue", alpha=0.7, label="facts")
ax1.plot(ff.m, ff.companies, color="tab:red", marker="o", label="companies")
ax1.axvline(mdates.datestr2num("2021-11-08"), color="black", ls="--", lw=1,
            label="benchmark week")
ax1.set_ylabel("per period-end month")
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.3)
ax1.set_title("facts by fiscal period end", fontsize=9, loc="left")
ax2.barh(fl.metric, fl.companies, color="tab:green", alpha=0.7)
ax2.set_xlabel("companies with metric (latest pre-week filing)")
ax2.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "06_fundamentals.png"), dpi=130, bbox_inches="tight")
plt.close(fig)
print("wrote gold/plots/06_fundamentals.png")

# ---------------------------------------------------------------- 7 gold marts
zp = q("SELECT * FROM gold.mart_zone_pulse WHERE bidding_zone = 'DE-LU' ORDER BY ts_utc")
rc = q("""SELECT * FROM gold.mart_rolling_correlation
          WHERE bidding_zone = 'DE-LU' AND samples >= 48 ORDER BY ts_utc""")

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle("gold marts spot check, DE-LU (UTC)", fontsize=14)

ref_ix = q("""SELECT d.instrument_id FROM gold.fact_instrument_day d
              JOIN gold.dim_instrument i USING (instrument_id)
              WHERE i.exchange_code = 'ETR' AND d.sec_type = 'I' AND d.close IS NOT NULL
              GROUP BY 1 ORDER BY sum(d.trade_tick_count) DESC LIMIT 1""").instrument_id[0]

ax = axes[0]
ax.plot(zp.ts_utc, zp.price_eur_mwh, color="tab:blue", label="day-ahead price EUR/MWh")
ax2 = ax.twinx()
s = on_grid(zp, "ts_utc", "index_level", "15min")
ax2.plot(s.index, s.values, color="tab:red", label=f"reference index level ({ref_ix})")
ax.set_ylabel("EUR/MWh", color="tab:blue")
ax2.set_ylabel("index level", color="tab:red")
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8)
ax.set_title("electricity price vs reference equity index (market only on ingested days)",
             fontsize=9, loc="left")

ax = axes[1]
s = on_grid(zp, "ts_utc", "eq_tick_count", "15min")
ax.plot(s.index, s.values, drawstyle="steps-post", color="tab:blue", label="equity ticks")
up = on_grid(zp, "ts_utc", "eq_movers_up", "15min")
dn = on_grid(zp, "ts_utc", "eq_movers_down", "15min")
ax.plot(up.index, up.values, color="tab:green", alpha=0.7, label="movers up")
ax.plot(dn.index, -dn.values, color="tab:red", alpha=0.7, label="movers down (neg)")
ax.set_yscale("symlog")
ax.set_ylabel("per 15 min")
ax.legend(loc="upper right", fontsize=8)
ax.set_title("market activity inside the mart", fontsize=9, loc="left")

ax = axes[2]
for pair, g in rc.groupby("signal_pair"):
    ax.plot(g.ts_utc, g.corr_24h, label=pair, alpha=0.85)
ax.axhline(0, color="black", lw=0.5)
ax.set_ylim(-1.05, 1.05)
ax.set_ylabel("rolling 24h corr")
ax.legend(loc="lower right", fontsize=8, ncols=2)
ax.set_title("mart_rolling_correlation signal pairs (windows with >= 48 samples)",
             fontsize=9, loc="left")
for ax in axes:
    style_week_axis(ax)
save(fig, "07_gold_marts.png")

print("done:", OUT)
