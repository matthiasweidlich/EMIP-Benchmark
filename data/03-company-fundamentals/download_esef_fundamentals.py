#!/usr/bin/env python3
"""Build the ESEF fundamentals dataset for the DEBS 2022 equity universe.

Pipeline (each step cached in --cache-dir, safe to re-run / resume):

1. GLEIF ISIN->LEI: download the latest bulk mapping file from
   mapping.gleif.org and filter it to the ISINs of the DEBS equity universe
   (from ../02-instrument-company-metadata/).
2. filings.xbrl.org index: page through /api/filings (all ESEF/UKSEF etc.
   filings known to the XBRL International filings repository) and
   /api/entities (LEI -> entity name).
3. Select filings whose entity LEI matches the DEBS universe and whose
   reporting period ends between 2020-01-01 and 2022-12-31 (FY2020 voluntary
   adopters, the first mandatory FY2021 wave, and shifted fiscal years).
4. Download each selected filing's xBRL-JSON fact file and extract
   consolidated (dimensionless) facts for a whitelist of IFRS concepts.

Outputs (written next to this script):
  esef_company_match.csv        LEI <-> ISIN <-> DEBS symbol crosswalk
  esef_filings.csv              selected filing metadata
  esef_fundamentals.csv         long-format facts (one row per filing/concept/period)
  esef_fundamentals_sample100.csv

Requires only the Python standard library. Please be polite to the public
APIs (the script sleeps between requests; a full run takes ~30-60 min).
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
META_DIR = os.path.join(BASE, "..", "02-instrument-company-metadata")
FILINGS_API = "https://filings.xbrl.org/api"
FILINGS_HOST = "https://filings.xbrl.org"
GLEIF_LATEST = "https://mapping.gleif.org/api/v2/isin-lei/latest"
USER_AGENT = "EMIP-Benchmark data pipeline (leis@in.tum.de)"

PERIOD_MIN = date(2020, 1, 1)
PERIOD_MAX = date(2022, 12, 31)

# IFRS concepts extracted as consolidated, dimensionless facts.
CONCEPTS = {
    "ifrs-full:Revenue": "revenue",
    "ifrs-full:RevenueFromContractsWithCustomers": "revenue",
    "ifrs-full:ProfitLoss": "net_income",
    "ifrs-full:ProfitLossAttributableToOwnersOfParent": "net_income_owners",
    "ifrs-full:ProfitLossFromOperatingActivities": "operating_income",
    "ifrs-full:Assets": "total_assets",
    "ifrs-full:CurrentAssets": "current_assets",
    "ifrs-full:NoncurrentAssets": "noncurrent_assets",
    "ifrs-full:Liabilities": "total_liabilities",
    "ifrs-full:CurrentLiabilities": "current_liabilities",
    "ifrs-full:NoncurrentLiabilities": "noncurrent_liabilities",
    "ifrs-full:Equity": "total_equity",
    "ifrs-full:EquityAttributableToOwnersOfParent": "equity_owners",
    "ifrs-full:CashFlowsFromUsedInOperatingActivities": "operating_cash_flow",
    "ifrs-full:CashAndCashEquivalents": "cash_and_equivalents",
    "ifrs-full:BasicEarningsLossPerShare": "eps_basic",
    "ifrs-full:DilutedEarningsLossPerShare": "eps_diluted",
}

CORE_DIMS = {"concept", "entity", "period", "unit", "language"}
LEI_RE = re.compile(r"^([A-Z0-9]{20})-")


def fetch(url, timeout=90, retries=5, sleep=5, accept="application/vnd.api+json"):
    url = urllib.parse.quote(url, safe=":/?&=%[]{}\"',")  # some report names contain spaces
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            print(f"  retry {attempt + 1} for {url}: {e}", file=sys.stderr)
            time.sleep(sleep * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}")


# ---------------------------------------------------------------- step 1
def load_universe():
    """DEBS equity symbols with ISIN, plus Yahoo metadata where resolved."""
    types = {}
    with open(os.path.join(META_DIR, "symbols_weekend.txt")) as fh:
        for line in fh:
            sym, _, typ = line.strip().partition(",")
            types[sym] = typ
    sym_isin = []
    with open(os.path.join(META_DIR, "sym_isin.txt")) as fh:
        for line in fh:
            sym, _, isin = line.strip().partition(",")
            if types.get(sym) == "E" and isin:
                sym_isin.append((sym, isin))
    meta = {}
    with open(os.path.join(META_DIR, "table1_equities_metadata.csv")) as fh:
        for row in csv.DictReader(fh):
            meta[row["debs_symbol"]] = row
    return sym_isin, meta


def step1_isin_lei(cache):
    out = os.path.join(cache, "isin_lei_filtered.csv")
    if os.path.exists(out):
        print("step 1: cached")
        return out
    zip_path = os.path.join(cache, "isin-lei.zip")
    if not os.path.exists(zip_path):
        latest = json.loads(fetch(GLEIF_LATEST, accept="application/json"))
        link = latest["data"]["attributes"]["downloadLink"]
        print(f"step 1: downloading GLEIF mapping {latest['data']['attributes']['fileName']}")
        with open(zip_path, "wb") as fh:
            fh.write(fetch(link, timeout=600, accept="*/*"))
    sym_isin, _ = load_universe()
    wanted = {isin for _, isin in sym_isin}
    pairs = set()
    with zipfile.ZipFile(zip_path) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8")):
                if row["ISIN"] in wanted:
                    pairs.add((row["LEI"], row["ISIN"]))
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["lei", "isin"])
        w.writerows(sorted(pairs))
    print(f"step 1: {len(pairs)} ISIN->LEI pairs for {len(wanted)} equity ISINs")
    return out


# ---------------------------------------------------------------- step 2
def paged(endpoint, page_size=200):
    page = 1
    while True:
        url = f"{FILINGS_API}/{endpoint}?page%5Bsize%5D={page_size}&page%5Bnumber%5D={page}"
        d = json.loads(fetch(url))
        yield page, d
        if not d["data"] or not d.get("links", {}).get("next"):
            return
        page += 1
        time.sleep(0.3)


def step2_filings_index(cache):
    out = os.path.join(cache, "filings_index.jsonl")
    done = os.path.join(cache, "filings_index.done")
    if os.path.exists(done):
        print("step 2: cached")
        return out
    done_pages = set()
    if os.path.exists(out):
        with open(out) as fh:
            for line in fh:
                try:
                    done_pages.add(json.loads(line)["_page"])
                except Exception:
                    pass
    with open(out, "a") as fh:
        for page, d in paged("filings"):
            if page in done_pages:
                continue
            for f in d["data"]:
                a = f["attributes"]
                rec = {k: a.get(k) for k in ("fxo_id", "country", "period_end",
                                             "date_added", "json_url",
                                             "package_url", "error_count")}
                rec["filing_api_id"] = f["id"]
                rec["_page"] = page
                fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if page % 10 == 0:
                print(f"step 2: filings page {page} ({d['meta']['count']} total)")
    open(done, "w").close()
    return out


def step2_entities(cache):
    out = os.path.join(cache, "entities.json")
    if os.path.exists(out):
        print("step 2: entities cached")
        return out
    names = {}
    for page, d in paged("entities"):
        for e in d["data"]:
            names[e["attributes"]["identifier"]] = e["attributes"]["name"]
        if page % 10 == 0:
            print(f"step 2: entities page {page}")
    with open(out, "w") as fh:
        json.dump(names, fh)
    return out


# ---------------------------------------------------------------- step 3
def step3_select(cache, isin_lei_path, index_path):
    leis = set()
    with open(isin_lei_path) as fh:
        for row in csv.DictReader(fh):
            leis.add(row["lei"])
    selected = {}
    with open(index_path) as fh:
        for line in fh:
            rec = json.loads(line)
            m = LEI_RE.match(rec["fxo_id"] or "")
            if not m or m.group(1) not in leis:
                continue
            try:
                pe = date.fromisoformat(rec["period_end"])
            except (TypeError, ValueError):
                continue
            if PERIOD_MIN <= pe <= PERIOD_MAX and rec["json_url"]:
                rec["lei"] = m.group(1)
                selected[rec["fxo_id"]] = rec
    print(f"step 3: {len(selected)} filings for {len({r['lei'] for r in selected.values()})} LEIs")
    return selected


# ---------------------------------------------------------------- step 4
def parse_period(period):
    """OIM periods: 'inst' or 'start/end', midnight T00:00:00 = end of previous day."""
    def parse_one(p, is_end):
        p = p.strip()
        dt = datetime.fromisoformat(p) if "T" in p else datetime.combine(date.fromisoformat(p), datetime.min.time())
        d = dt.date()
        if is_end and dt.time() == datetime.min.time():
            d = d - timedelta(days=1)
        return d
    if not period:
        return None, None
    if "/" in period:
        s, e = period.split("/", 1)
        return parse_one(s, False), parse_one(e, True)
    d = parse_one(period, True)
    return None, d


def clean_unit(unit):
    if not unit:
        return ""
    return unit.replace("iso4217:", "").replace("xbrli:shares", "share").replace("xbrli:pure", "pure")


def step4_facts(cache, selected, entity_names):
    facts_dir = os.path.join(cache, "facts")
    os.makedirs(facts_dir, exist_ok=True)
    rows = []
    n = 0
    for fxo_id, rec in sorted(selected.items()):
        n += 1
        local = os.path.join(facts_dir, fxo_id + ".json")
        if not os.path.exists(local):
            try:
                data = fetch(FILINGS_HOST + rec["json_url"], timeout=180, accept="*/*")
            except RuntimeError as e:
                print(f"  skipping {fxo_id}: {e}", file=sys.stderr)
                open(local + ".failed", "w").close()
                continue
            with open(local, "wb") as fh:
                fh.write(data)
            time.sleep(0.2)
        try:
            with open(local) as fh:
                doc = json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  bad JSON for {fxo_id}: {e}", file=sys.stderr)
            continue
        seen = {}
        for f in doc.get("facts", {}).values():
            dims = f.get("dimensions", {})
            concept = dims.get("concept", "")
            if concept not in CONCEPTS or set(dims) - CORE_DIMS:
                continue
            start, end = parse_period(dims.get("period"))
            key = (concept, start, end, dims.get("unit"))
            if key in seen:
                continue
            seen[key] = True
            rows.append({
                "source": "esef_filings_xbrl_org",
                "lei": rec["lei"],
                "company_name": entity_names.get(rec["lei"], ""),
                "filing_id": fxo_id,
                "country": rec["country"],
                "filing_period_end": rec["period_end"],
                "filing_published": (rec["date_added"] or "")[:10],
                "concept": concept,
                "metric": CONCEPTS[concept],
                "value": f.get("value"),
                "unit": clean_unit(dims.get("unit")),
                "period_start": start.isoformat() if start else "",
                "period_end": end.isoformat() if end else "",
                "source_json_url": FILINGS_HOST + rec["json_url"],
            })
        if n % 50 == 0:
            print(f"step 4: {n}/{len(selected)} filings processed, {len(rows)} facts")
    return rows


# ---------------------------------------------------------------- outputs
def write_outputs(selected, rows, isin_lei_path, entity_names):
    sym_isin, meta = load_universe()
    isin_syms = {}
    for sym, isin in sym_isin:
        isin_syms.setdefault(isin, []).append(sym)
    lei_isins = {}
    with open(isin_lei_path) as fh:
        for row in csv.DictReader(fh):
            lei_isins.setdefault(row["lei"], []).append(row["isin"])
    leis_with_filing = {r["lei"] for r in selected.values()}

    with open(os.path.join(BASE, "esef_company_match.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["lei", "isin", "debs_symbol", "yahoo_ticker", "company_name", "has_esef_filing"])
        for lei, isins in sorted(lei_isins.items()):
            for isin in sorted(isins):
                for sym in sorted(isin_syms.get(isin, [""])):
                    m = meta.get(sym, {})
                    name = entity_names.get(lei) or m.get("longName", "")
                    w.writerow([lei, isin, sym, m.get("yahoo_ticker", ""), name,
                                "true" if lei in leis_with_filing else "false"])

    with open(os.path.join(BASE, "esef_filings.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["filing_id", "lei", "company_name", "country", "period_end",
                    "date_added", "json_url", "package_url", "error_count"])
        for fxo_id, r in sorted(selected.items()):
            w.writerow([fxo_id, r["lei"], entity_names.get(r["lei"], ""), r["country"],
                        r["period_end"], r["date_added"], FILINGS_HOST + r["json_url"],
                        (FILINGS_HOST + r["package_url"]) if r.get("package_url") else "",
                        r["error_count"]])

    cols = ["source", "lei", "company_name", "filing_id", "country", "filing_period_end",
            "filing_published", "concept", "metric", "value", "unit",
            "period_start", "period_end", "source_json_url"]
    rows.sort(key=lambda r: (r["lei"], r["filing_id"], r["concept"], r["period_end"]))
    with open(os.path.join(BASE, "esef_fundamentals.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(BASE, "esef_fundamentals_sample100.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows[:100])
    print(f"outputs: {len(rows)} facts, {len(selected)} filings, "
          f"{len(leis_with_filing)} companies with filings")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-dir", default=os.path.join(BASE, "cache"))
    args = ap.parse_args()
    os.makedirs(args.cache_dir, exist_ok=True)

    isin_lei_path = step1_isin_lei(args.cache_dir)
    index_path = step2_filings_index(args.cache_dir)
    entities_path = step2_entities(args.cache_dir)
    with open(entities_path) as fh:
        entity_names = json.load(fh)
    selected = step3_select(args.cache_dir, isin_lei_path, index_path)
    rows = step4_facts(args.cache_dir, selected, entity_names)
    write_outputs(selected, rows, isin_lei_path, entity_names)


if __name__ == "__main__":
    main()
