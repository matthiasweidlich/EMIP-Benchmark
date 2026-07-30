#!/usr/bin/env python3
"""Extract the instrument universe from all available DEBS tick files.

Scans every `debs2022-gc-trading-day-*.csv` in ../01-debs-tick-stream/
(weekend files are committed; weekday files are downloaded from Zenodo, see
dataset-01 doc) and writes:

  symbols_week.txt    symbol,type      (type: E equity / I index; mode over files)
  sym_isin_week.txt   symbol,ISIN      (most frequent non-null ISIN per symbol)

The original `symbols_weekend.txt` / `sym_isin.txt` (weekend-only extraction)
are kept for provenance.
"""

import glob
import os

import duckdb

BASE = os.path.dirname(os.path.abspath(__file__))
TICK_DIR = os.path.join(BASE, "..", "01-debs-tick-stream")

files = sorted(glob.glob(os.path.join(TICK_DIR, "debs2022-gc-trading-day-*.csv")))
files = [f for f in files if "sample" not in f or len(files) == 1]
print(f"scanning {len(files)} tick files")

con = duckdb.connect()
# Parse without header/comment detection: DuckDB's comment handling eats the
# first byte of the first data row after an in-line comment line, and default
# quote handling can glue lines. One physical line = one row; preamble,
# header, and description rows are filtered out below.
NAMES = ["ID", "SecType", "Date", "Time", "Ask", "Ask volume", "Bid",
         "Bid volume", "Ask time", "Day's high ask", "Close", "Currency",
         "Day's high ask time", "Day's high", "ISIN", "Auction price",
         "Day's low ask", "Day's low", "Day's low ask time", "Open",
         "Nominal value", "Last", "Last volume", "Trading time",
         "Total volume", "Mid price", "Trading date", "Profit",
         "Current price", "Related indices", "Day high bid time",
         "Day low bid time", "Open Time", "Last trade time", "Close Time",
         "Day high Time", "Day low Time", "Bid time", "Auction Time"]
names_sql = "[" + ", ".join("'" + n.replace("'", "''") + "'" for n in NAMES) + "]"
parts = []
for f in files:
    parts.append(f"""
        SELECT ID AS symbol, SecType AS sec_type, nullif(ISIN, '') AS isin
        FROM read_csv('{f}', header=false, names={names_sql}, all_varchar=true,
                      quote='', strict_mode=false, null_padding=true, sample_size=-1, parallel=false)
        WHERE ID IS NOT NULL AND ID NOT LIKE '#%' AND ID <> 'ID'""")
union = " UNION ALL ".join(parts)

uni = con.sql(f"""
    SELECT symbol,
           mode(sec_type) AS sec_type,
           mode(isin) FILTER (isin IS NOT NULL) AS isin
    FROM ({union})
    WHERE sec_type IN ('E', 'I')
      AND regexp_matches(symbol, '^[A-Za-z0-9]+\\.(ETR|FR|NL)$')
    GROUP BY symbol
    ORDER BY symbol""").fetchall()

with open(os.path.join(BASE, "symbols_week.txt"), "w") as fh:
    for sym, sec_type, _ in uni:
        fh.write(f"{sym},{sec_type}\n")
with open(os.path.join(BASE, "sym_isin_week.txt"), "w") as fh:
    for sym, _, isin in uni:
        if isin:
            fh.write(f"{sym},{isin}\n")

n_e = sum(1 for _, t, _ in uni if t == "E")
n_i = sum(1 for _, t, _ in uni if t == "I")
n_isin = sum(1 for _, _, i in uni if i)
print(f"symbols: {len(uni)} (E: {n_e}, I: {n_i}); with ISIN: {n_isin}")
