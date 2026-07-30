#!/usr/bin/env python3
"""
Download actual imbalance settlement prices (A85) from the ENTSO-E
Transparency Platform for DE-LU, FR, and NL bidding zones and write
them to a time-sorted CSV compatible with the gold electricity_price
table schema.

Imbalance prices are actual post-delivery settlement prices applied to
market parties who were long or short in the balancing timeframe.  They
are more volatile than day-ahead auction prices and reflect real-time
supply/demand stress.  For Germany this corresponds to the reBAP price.

ENTSO-E document type A85, 15-minute resolution.

Usage:
    python3 download_imbalance_prices.py <ENTSOE_API_KEY>
    python3 download_imbalance_prices.py --start 2021-11-08 --end 2021-11-14 <ENTSOE_API_KEY>

Output schema (appends price_type column to match gold table):
    timestamp_utc,timestamp_local,bidding_zone,price_eur_mwh,price_type
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError


# EIC codes for the three DEBS-relevant bidding zones
ZONES = {
    "DE-LU": "10Y1001A1001A82H",
    "FR":    "10YFR-RTE------C",
    "NL":    "10YNL----------L",
}

ZONE_TIMEZONES = {
    "DE-LU": "Europe/Berlin",
    "FR":    "Europe/Paris",
    "NL":    "Europe/Amsterdam",
}


def fetch_imbalance(
    client: EntsoePandasClient,
    zone_label: str,
    eic: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> list[dict]:
    """Fetch imbalance prices for one zone; return list of row dicts."""
    print(f"  Fetching imbalance prices for {zone_label} ({eic}) ...")
    try:
        result = client.query_imbalance_prices(
            country_code=eic,
            start=start,
            end=end,
        )
    except NoMatchingDataError:
        print(f"  WARNING: no imbalance data for {zone_label} in this window")
        return []
    except Exception as exc:
        print(f"  ERROR for {zone_label}: {exc}", file=sys.stderr)
        return []

    if result is None or (hasattr(result, "empty") and result.empty):
        print(f"  WARNING: empty result for {zone_label}")
        return []

    # result may be a Series (single price column) or DataFrame
    # (Long/Short imbalance prices).  Normalise to DataFrame.
    if isinstance(result, pd.Series):
        df = result.to_frame(name="imbalance_price")
    else:
        df = result

    tz_name = ZONE_TIMEZONES.get(zone_label, "UTC")
    rows = []

    for ts, row in df.iterrows():
        ts_utc = pd.Timestamp(ts).tz_convert("UTC")
        ts_local = ts_utc.tz_convert(tz_name)

        if isinstance(row, pd.Series):
            # Multiple columns (Long / Short)
            for col_name, value in row.items():
                if pd.isna(value):
                    continue
                rows.append({
                    "timestamp_utc":   ts_utc.isoformat(),
                    "timestamp_local": ts_local.isoformat(),
                    "bidding_zone":    zone_label,
                    "price_eur_mwh":   float(value),
                    "price_type":      f"imbalance_{col_name.lower().replace(' ', '_')}",
                })
        else:
            if pd.isna(row):
                continue
            rows.append({
                "timestamp_utc":   ts_utc.isoformat(),
                "timestamp_local": ts_local.isoformat(),
                "bidding_zone":    zone_label,
                "price_eur_mwh":   float(row),
                "price_type":      "imbalance",
            })

    print(f"  received {len(rows):,} records")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download ENTSO-E imbalance settlement prices (A85)."
    )
    parser.add_argument("api_key", help="ENTSO-E Transparency Platform API key")
    parser.add_argument("--start", default="2021-11-08",
                        help="Start date inclusive (YYYY-MM-DD)")
    parser.add_argument("--end",   default="2021-11-14",
                        help="End date inclusive (YYYY-MM-DD)")
    parser.add_argument(
        "--output", type=Path,
        default=Path("electricity_imbalance_prices_2021-11-08_2021-11-14.csv"),
    )
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between zone requests")
    args = parser.parse_args()

    client = EntsoePandasClient(api_key=args.api_key)

    # ENTSO-E API requires tz-aware timestamps
    tz = "Europe/Brussels"
    start = pd.Timestamp(args.start, tz=tz)
    end   = pd.Timestamp(args.end,   tz=tz) + pd.Timedelta(days=1)

    all_rows: list[dict] = []
    for zone_label, eic in ZONES.items():
        rows = fetch_imbalance(client, zone_label, eic, start, end)
        all_rows.extend(rows)
        time.sleep(args.delay)

    if not all_rows:
        print("No data retrieved — check API key and date range.", file=sys.stderr)
        return 1

    all_rows.sort(key=lambda r: (r["timestamp_utc"], r["bidding_zone"], r["price_type"]))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["timestamp_utc", "timestamp_local", "bidding_zone",
                  "price_eur_mwh", "price_type"]
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print()
    print(f"Created: {args.output.resolve()}")
    print(f"Total records: {len(all_rows):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
