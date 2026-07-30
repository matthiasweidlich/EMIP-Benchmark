#!/usr/bin/env python3
"""Regenerate the full (unfiltered) two-week GDELT tables documented in
data/dataset-04-gdelt-news-events.md from GDELT's public 1.0 feeds.

The dataset doc describes a zip (gdelt_gkg_energy_nov1-14_2021.zip, Git LFS)
whose LFS object is not available; every file in its manifest is mechanically
derivable from the public archive, which is what this script does:

  raw_gdelt/YYYYMMDD.export.zip  (events, 58 cols, no header)
  raw_gdelt/YYYYMMDD.gkg.zip     (GKG 1.0, 11 cols, header)
      -> gdelt_20211101-07_merged.CSV / gdelt_20211108-14_merged.CSV
      -> gkg_all_enriched_nov1-7.csv.gz / gkg_all_enriched_nov8-14.csv.gz
      -> gkg_all_event_link_nov1-7.csv.gz / gkg_all_event_link_nov8-14.csv.gz

Known deviation: ENERGY_SECTORS / ENERGY_TICKERS / ENERGY_ENTITIES come from
the committed energy-classifier output (gkg_energy_enriched*.csv), which the
repo has only for Nov 8-14 - the Nov 1-7 energy columns stay empty here.
Row counts are validated against the dataset doc's manifest.
"""
import glob
import os
import sys
import zipfile

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw_gdelt")

EVENT_COLS = (
    ["GlobalEventID", "SQLDATE", "MonthYear", "Year", "FractionDate"]
    + [f"Actor{n}{part}" for n in (1, 2) for part in
       ("Code", "Name", "CountryCode", "KnownGroupCode", "EthnicCode",
        "Religion1Code", "Religion2Code", "Type1Code", "Type2Code", "Type3Code")]
    + ["IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
       "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone"]
    + [f"{p}Geo_{part}" for p in ("Actor1", "Actor2", "Action") for part in
       ("Type", "FullName", "CountryCode", "ADM1Code", "Lat", "Long", "FeatureID")]
    + ["DATEADDED", "SOURCEURL"]
)
assert len(EVENT_COLS) == 58

WEEKS = {  # suffixes and expected row counts from the dataset doc
    "nov1-7":  {"days": [f"202111{d:02d}" for d in range(1, 8)],
                "events_name": "gdelt_20211101-07_merged.CSV",
                "expect": {"events": 725_518, "docs": 430_664, "links": 1_857_813},
                "energy_csv": "gkg_energy_enriched_nov1-7.csv"},
    "nov8-14": {"days": [f"202111{d:02d}" for d in range(8, 15)],
                "events_name": "gdelt_20211108-14_merged.CSV",
                "expect": {"events": 777_481, "docs": 430_918, "links": 1_917_264},
                "energy_csv": "gkg_energy_enriched.csv"},
}


def unzip_all():
    for z in sorted(glob.glob(os.path.join(RAW, "*.zip"))):
        with zipfile.ZipFile(z) as zf:
            for name in zf.namelist():
                out = os.path.join(RAW, name)
                if not os.path.exists(out):
                    zf.extract(name, RAW)


def main():
    unzip_all()
    con = duckdb.connect()
    names_sql = "[" + ", ".join(f"'{c}'" for c in EVENT_COLS) + "]"

    for week, cfg in WEEKS.items():
        ev_files = ", ".join(f"'{RAW}/{d}.export.CSV'" for d in cfg["days"])
        gkg_files = ", ".join(f"'{RAW}/{d}.gkg.csv'" for d in cfg["days"])

        con.execute(f"""CREATE OR REPLACE TABLE events AS
            SELECT * FROM read_csv([{ev_files}], delim='\t', header=false,
                quote='', names={names_sql}, all_varchar=true, sample_size=-1)""")
        out_events = os.path.join(HERE, cfg["events_name"])
        con.execute(f"""COPY events TO '{out_events}'
            (FORMAT csv, DELIMITER '\t', HEADER true)""")

        con.execute(f"""CREATE OR REPLACE TABLE gkg AS
            SELECT * FROM read_csv([{gkg_files}], delim='\t', header=true,
                quote='', all_varchar=true, sample_size=-1)""")

        energy_path = os.path.join(HERE, cfg["energy_csv"])
        if os.path.exists(energy_path):
            con.execute(f"""CREATE OR REPLACE TABLE energy AS
                SELECT DATE, SOURCEURL,
                       any_value(ENERGY_SECTORS) AS ENERGY_SECTORS,
                       any_value(ENERGY_TICKERS) AS ENERGY_TICKERS,
                       any_value(ENERGY_ENTITIES) AS ENERGY_ENTITIES
                FROM read_csv('{energy_path}', delim='\t', header=true,
                              quote='', all_varchar=true, sample_size=-1)
                GROUP BY 1, 2""")
        else:
            print(f"!! {cfg['energy_csv']} missing - energy tags stay empty for {week}")
            con.execute("""CREATE OR REPLACE TABLE energy
                (DATE VARCHAR, SOURCEURL VARCHAR, ENERGY_SECTORS VARCHAR,
                 ENERGY_TICKERS VARCHAR, ENERGY_ENTITIES VARCHAR)""")

        # Table C: unfiltered document table (energy tags grafted where known).
        con.execute("""CREATE OR REPLACE TABLE docs AS
            SELECT g.DATE, g.SOURCES AS SOURCE, g.SOURCEURLS AS SOURCEURL,
                   g.NUMARTS,
                   rtrim(coalesce(g.THEMES, ''), ';') AS THEMES,
                   CASE WHEN coalesce(g.THEMES, '') = '' THEN 0
                        ELSE len(string_split(rtrim(g.THEMES, ';'), ';')) END AS THEME_COUNT,
                   round(try_cast(string_split(g.TONE, ',')[1] AS DOUBLE), 8) AS TONE_AVG,
                   try_cast(string_split(g.TONE, ',')[2] AS DOUBLE) AS TONE_POS,
                   try_cast(string_split(g.TONE, ',')[3] AS DOUBLE) AS TONE_NEG,
                   try_cast(string_split(g.TONE, ',')[4] AS DOUBLE) AS TONE_POLARITY,
                   try_cast(string_split(g.TONE, ',')[5] AS DOUBLE) AS TONE_ACTIVITY,
                   try_cast(string_split(g.TONE, ',')[6] AS DOUBLE) AS TONE_SELFREF,
                   rtrim(coalesce(g.ORGANIZATIONS, ''), ';') AS ORGANIZATIONS,
                   rtrim(coalesce(g.PERSONS, ''), ';') AS PERSONS,
                   array_to_string(list_distinct(
                       [string_split(loc, '#')[3]
                        FOR loc IN string_split(coalesce(g.LOCATIONS, ''), ';')
                        IF len(string_split(loc, '#')) >= 3]), '|') AS COUNTRY_CODES,
                   array_to_string(
                       [string_split(loc, '#')[2] || '|' || string_split(loc, '#')[3]
                        || '|' || string_split(loc, '#')[5] || '|' || string_split(loc, '#')[6]
                        FOR loc IN string_split(coalesce(g.LOCATIONS, ''), ';')
                        IF len(string_split(loc, '#')) >= 6][1:3], ' ;; ') AS TOP_LOCATIONS,
                   coalesce(g.CAMEOEVENTIDS, '') AS CAMEO_EVENT_IDS,
                   coalesce(e.ENERGY_SECTORS, '') AS ENERGY_SECTORS,
                   coalesce(e.ENERGY_TICKERS, '') AS ENERGY_TICKERS,
                   coalesce(e.ENERGY_ENTITIES, '') AS ENERGY_ENTITIES
            FROM gkg g
            LEFT JOIN energy e ON e.DATE = g.DATE AND e.SOURCEURL = g.SOURCEURLS""")
        out_docs = os.path.join(HERE, f"gkg_all_enriched_{week}.csv.gz")
        con.execute(f"""COPY docs TO '{out_docs}'
            (FORMAT csv, DELIMITER '\t', HEADER true, COMPRESSION gzip)""")

        # Table D: unfiltered doc x event bridge (matched within the week).
        con.execute("""CREATE OR REPLACE TABLE links AS
            WITH refs AS (
                SELECT DATE, SOURCEURL, ENERGY_SECTORS, TONE_AVG, ENERGY_TICKERS,
                       try_cast(unnest(string_split(nullif(CAMEO_EVENT_IDS, ''), ','))
                                AS BIGINT) AS GlobalEventID
                FROM docs)
            SELECT r.GlobalEventID, r.DATE, ev.EventRootCode,
                   ev.QuadClass,
                   CASE ev.QuadClass WHEN '1' THEN 'VerbalCoop'
                        WHEN '2' THEN 'MaterialCoop' WHEN '3' THEN 'VerbalConflict'
                        WHEN '4' THEN 'MaterialConflict' END AS QuadClassName,
                   ev.GoldsteinScale, ev.AvgTone AS Event_AvgTone,
                   ev.ActionGeo_FullName, ev.ActionGeo_CountryCode AS ActionGeo_CC,
                   r.ENERGY_SECTORS AS Energy_Sectors, r.TONE_AVG AS Doc_Tone,
                   r.ENERGY_TICKERS AS Doc_Tickers, r.SOURCEURL AS SourceURL
            FROM refs r
            JOIN events ev ON try_cast(ev.GlobalEventID AS BIGINT) = r.GlobalEventID
            WHERE r.GlobalEventID IS NOT NULL""")
        out_links = os.path.join(HERE, f"gkg_all_event_link_{week}.csv.gz")
        con.execute(f"""COPY links TO '{out_links}'
            (FORMAT csv, DELIMITER '\t', HEADER true, COMPRESSION gzip)""")

        got = {t: con.sql(f"SELECT count(*) FROM {t}").fetchone()[0]
               for t in ("events", "docs", "links")}
        for k in got:
            mark = "OK" if got[k] == cfg["expect"][k] else \
                   f"MISMATCH expected {cfg['expect'][k]:,}"
            print(f"{week} {k}: {got[k]:,}  [{mark}]", flush=True)


if __name__ == "__main__":
    sys.exit(main())
