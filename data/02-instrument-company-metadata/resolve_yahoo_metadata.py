#!/usr/bin/env python3
"""Entity resolution: DEBS equity symbols -> Yahoo Finance company metadata.

Re-runs the two-pass resolution described in README.md for every equity in
the current symbol universe that is not yet in table1_equities_metadata.csv
(new symbols from the weekday files plus previously unresolved ones):

  pass 1  direct ticker mapping (.ETR -> .DE, .FR -> .PA, .NL -> .AS)
          for mnemonic (non-WKN) symbols;
  pass 2  ISIN search on Yahoo for everything pass 1 missed.

Results are cached per symbol in cache_yahoo_resolution.jsonl (safe to
re-run; delete the cache to force fresh lookups). Then rewrites:

  table1_equities_metadata.csv   old rows + newly resolved rows
  table2_sector_by_exchange.csv  regenerated pivot
  table3_unresolved_symbols.csv  recomputed from the new universe

Uses symbols_week.txt / sym_isin_week.txt when present (full-week universe,
see extract_symbol_universe.py), else the weekend files.
"""

import csv
import json
import os
import re
import time

import yfinance as yf

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "cache_yahoo_resolution.jsonl")
SLEEP = 0.6
SUFFIX = {"ETR": ".DE", "FR": ".PA", "NL": ".AS"}
COLS = ["debs_symbol", "yahoo_ticker", "exchange", "resolved_via", "shortName",
        "longName", "sector", "industry", "country", "city", "currency",
        "quoteType", "marketCap", "fullTimeEmployees", "website", "isin_yf"]


def read_universe():
    sym_file = "symbols_week.txt" if os.path.exists(os.path.join(BASE, "symbols_week.txt")) else "symbols_weekend.txt"
    isin_file = "sym_isin_week.txt" if sym_file == "symbols_week.txt" else "sym_isin.txt"
    print(f"universe from {sym_file} / {isin_file}")
    symbols = {}
    with open(os.path.join(BASE, sym_file)) as fh:
        for line in fh:
            sym, _, typ = line.strip().partition(",")
            if sym:
                symbols[sym] = typ
    isins = {}
    with open(os.path.join(BASE, isin_file)) as fh:
        for line in fh:
            sym, _, isin = line.strip().partition(",")
            if isin:
                isins[sym] = isin
    return symbols, isins


def load_csv(name):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return list(csv.DictReader(fh))


def info_row(sym, ticker, via, info, isin_search=""):
    isin_yf = isin_search
    return {
        "debs_symbol": sym,
        "yahoo_ticker": ticker,
        "exchange": sym.rsplit(".", 1)[-1],
        "resolved_via": via,
        "shortName": info.get("shortName", ""),
        "longName": info.get("longName", ""),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "country": info.get("country", ""),
        "city": info.get("city", ""),
        "currency": info.get("currency", ""),
        "quoteType": info.get("quoteType", ""),
        "marketCap": info.get("marketCap", ""),
        "fullTimeEmployees": info.get("fullTimeEmployees", ""),
        "website": info.get("website", ""),
        "isin_yf": isin_yf,
    }


def get_info(ticker):
    try:
        info = yf.Ticker(ticker).get_info()
        time.sleep(SLEEP)
        if info and (info.get("longName") or info.get("shortName")):
            return info
        return None
    except Exception as e:
        time.sleep(SLEEP)
        if "429" in str(e) or "Rate" in type(e).__name__:
            print("  rate limited, backing off 60s")
            time.sleep(60)
        return None


def search_isin(isin):
    try:
        s = yf.Search(isin, max_results=1)
        time.sleep(SLEEP)
        quotes = s.quotes or []
        return quotes[0].get("symbol") if quotes else None
    except Exception as e:
        time.sleep(SLEEP)
        if "429" in str(e) or "Rate" in type(e).__name__:
            print("  rate limited, backing off 60s")
            time.sleep(60)
        return None


def main():
    symbols, isins = read_universe()
    table1 = load_csv("table1_equities_metadata.csv")
    resolved = {r["debs_symbol"] for r in table1}
    equities = [s for s, t in symbols.items() if t == "E"]
    targets = sorted(s for s in equities if s not in resolved)
    print(f"universe: {len(symbols)} symbols, {len(equities)} equities, "
          f"{len(resolved)} already resolved, {len(targets)} to try")

    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE) as fh:
            for line in fh:
                rec = json.loads(line)
                cache[rec["debs_symbol"]] = rec

    with open(CACHE, "a") as cfh:
        for n, sym in enumerate(targets, 1):
            if sym in cache:
                continue
            base, _, exch = sym.rpartition(".")
            rec = {"debs_symbol": sym, "status": "no_isin", "row": None}
            # pass 1: mnemonic ticker mapping
            if exch in SUFFIX and not re.fullmatch(r"[0-9]+|[A-Z0-9]{6}", base):
                ticker = base + SUFFIX[exch]
                info = get_info(ticker)
                if info:
                    rec = {"debs_symbol": sym, "status": "ok",
                           "row": info_row(sym, ticker, "ticker", info)}
            # pass 2: ISIN search
            if rec["status"] != "ok" and sym in isins:
                ticker = search_isin(isins[sym])
                if ticker:
                    info = get_info(ticker)
                    if info:
                        rec = {"debs_symbol": sym, "status": "ok",
                               "row": info_row(sym, ticker, "isin", info, isins[sym])}
                    else:
                        rec = {"debs_symbol": sym, "status": "no_data",
                               "row": {"yahoo_ticker": ticker}}
                else:
                    rec = {"debs_symbol": sym, "status": "isin_not_found",
                           "row": {"yahoo_ticker": ""}}
            cache[sym] = rec
            cfh.write(json.dumps(rec) + "\n")
            cfh.flush()
            if n % 25 == 0:
                ok = sum(1 for r in cache.values() if r["status"] == "ok")
                print(f"{n}/{len(targets)} tried, {ok} newly resolved", flush=True)

    new_rows = [cache[s]["row"] for s in targets
                if s in cache and cache[s]["status"] == "ok"]
    all_rows = sorted(table1 + new_rows, key=lambda r: r["debs_symbol"])
    with open(os.path.join(BASE, "table1_equities_metadata.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows({c: r.get(c, "") for c in COLS} for r in all_rows)

    resolved = {r["debs_symbol"] for r in all_rows}
    with open(os.path.join(BASE, "table3_unresolved_symbols.csv"), "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["debs_symbol", "yahoo_ticker", "exchange", "status"])
        for sym in sorted(s for s in equities if s not in resolved):
            rec = cache.get(sym, {"status": "not_attempted", "row": {}})
            row = rec.get("row") or {}
            w.writerow([sym, row.get("yahoo_ticker", ""),
                        sym.rsplit(".", 1)[-1], rec["status"]])

    sectors = {}
    for r in all_rows:
        if r.get("sector"):
            key = r["sector"]
            sectors.setdefault(key, {"ETR": 0, "FR": 0, "NL": 0})
            if r["exchange"] in sectors[key]:
                sectors[key][r["exchange"]] += 1
    with open(os.path.join(BASE, "table2_sector_by_exchange.csv"), "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["sector", "ETR", "FR", "NL", "Total"])
        for sec, c in sorted(sectors.items(), key=lambda kv: -sum(kv[1].values())):
            w.writerow([sec, c["ETR"], c["FR"], c["NL"], sum(c.values())])

    print(f"table1: {len(all_rows)} resolved ({len(new_rows)} new); "
          f"unresolved: {len(equities) - len(resolved)}")


if __name__ == "__main__":
    main()
