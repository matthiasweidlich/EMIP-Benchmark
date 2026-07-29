#!/usr/bin/env python3
"""
Download hourly day-ahead electricity prices from the Fraunhofer ISE
Energy-Charts API and combine them into one time-sorted CSV.

Default period:
    2021-11-08 through 2021-11-14 inclusive

Default bidding zones:
    DE-LU, FR, BE, NL, AT, CH

Output schema:
    timestamp_utc,timestamp_local,bidding_zone,price_eur_mwh
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


API_URL = "https://api.energy-charts.info/price"

DEFAULT_ZONES = ["DE-LU", "FR", "BE", "NL", "AT", "CH"]

ZONE_TIMEZONES = {
    "DE-LU": "Europe/Berlin",
    "FR": "Europe/Paris",
    "BE": "Europe/Brussels",
    "NL": "Europe/Amsterdam",
    "AT": "Europe/Vienna",
    "CH": "Europe/Zurich",
}


def build_session() -> requests.Session:
    retry = Retry(
        total=8,
        connect=8,
        read=8,
        status=8,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "EMIP-Electricity-Price-Downloader/1.0"}
    )
    session.mount("https://", adapter)
    return session


def fetch_zone(
    session: requests.Session,
    zone: str,
    start: str,
    end: str,
    timeout: int,
) -> tuple[list[dict], dict]:
    response = session.get(
        API_URL,
        params={"bzn": zone, "start": start, "end": end},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    timestamps = payload.get("unix_seconds")
    prices = payload.get("price")

    if not isinstance(timestamps, list) or not isinstance(prices, list):
        raise RuntimeError(
            f"Unexpected API response for {zone}: "
            "missing unix_seconds or price arrays"
        )

    if len(timestamps) != len(prices):
        raise RuntimeError(
            f"Length mismatch for {zone}: "
            f"{len(timestamps)} timestamps vs {len(prices)} prices"
        )

    timezone_name = ZONE_TIMEZONES.get(zone, "UTC")
    local_zone = ZoneInfo(timezone_name)
    rows = []

    for unix_seconds, price in zip(timestamps, prices):
        if unix_seconds is None or price is None:
            continue

        timestamp_utc = datetime.fromtimestamp(
            int(unix_seconds), tz=timezone.utc
        )
        timestamp_local = timestamp_utc.astimezone(local_zone)

        rows.append(
            {
                "timestamp_utc": timestamp_utc.isoformat(),
                "timestamp_local": timestamp_local.isoformat(),
                "bidding_zone": zone,
                "price_eur_mwh": price,
            }
        )

    metadata = {
        "bidding_zone": zone,
        "timezone": timezone_name,
        "records": len(rows),
        "unit": payload.get("unit", "EUR/MWh"),
        "license_info": payload.get("license_info"),
        "deprecated": payload.get("deprecated", False),
        "request_url": response.url,
    }
    return rows, metadata


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download and combine Energy-Charts hourly day-ahead "
            "electricity prices."
        )
    )
    parser.add_argument("--start", default="2021-11-08")
    parser.add_argument("--end", default="2021-11-14")
    parser.add_argument(
        "--zones",
        nargs="+",
        default=DEFAULT_ZONES,
        help="Energy-Charts bidding-zone identifiers.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "electricity_day_ahead_prices_"
            "2021-11-08_2021-11-14.csv"
        ),
    )
    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=Path(
            "electricity_day_ahead_prices_"
            "2021-11-08_2021-11-14_metadata.json"
        ),
    )
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    zones = [zone.upper() for zone in args.zones]
    session = build_session()

    all_rows: list[dict] = []
    metadata = {
        "source": "Fraunhofer ISE Energy-Charts API",
        "api_endpoint": API_URL,
        "start": args.start,
        "end": args.end,
        "zones": zones,
        "zone_results": [],
    }

    for zone in zones:
        print(f"Downloading {zone}: {args.start} through {args.end}")
        try:
            rows, zone_metadata = fetch_zone(
                session,
                zone,
                args.start,
                args.end,
                args.timeout,
            )
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            print(f"ERROR for {zone}: {exc}", file=sys.stderr)
            return 1

        all_rows.extend(rows)
        metadata["zone_results"].append(zone_metadata)
        print(f"  received {len(rows):,} hourly records")
        time.sleep(0.5)

    all_rows.sort(
        key=lambda row: (
            row["timestamp_utc"],
            row["bidding_zone"],
        )
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp_utc",
                "timestamp_local",
                "bidding_zone",
                "price_eur_mwh",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    metadata["total_records"] = len(all_rows)
    args.metadata_output.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("")
    print(f"Created: {args.output.resolve()}")
    print(f"Created: {args.metadata_output.resolve()}")
    print(f"Total records: {len(all_rows):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
