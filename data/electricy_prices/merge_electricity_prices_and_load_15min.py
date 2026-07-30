#!/usr/bin/env python3
"""Create a 15-minute electricity price and load dataset.

The script uses the long schema of the Energy-Charts day-ahead price file and
adds actual load from the ENTSO-E enrichment file.

Final schema:
    timestamp_utc,timestamp_local,bidding_zone,price_eur_mwh,load_actual_mw

Behavior:
- Each hourly day-ahead price is repeated for its four 15-minute intervals.
- Actual load is joined for DE-LU, FR, and NL.
- AT, BE, and CH retain their prices and receive an empty load value.
- The ENTSO-E price columns are used to validate the repeated price values for
  DE-LU, FR, and NL; they are not duplicated in the output.
- Output is sorted by UTC timestamp and bidding zone.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path


ZONE_COLUMNS = {
    "DE-LU": {
        "price": "price_dayahead_DE_LU_EUR_MWh",
        "load": "load_actual_DE_LU_MW",
    },
    "FR": {
        "price": "price_dayahead_FR_EUR_MWh",
        "load": "load_actual_FR_MW",
    },
    "NL": {
        "price": "price_dayahead_NL_EUR_MWh",
        "load": "load_actual_NL_MW",
    },
}

OUTPUT_COLUMNS = [
    "timestamp_utc",
    "timestamp_local",
    "bidding_zone",
    "price_eur_mwh",
    "load_actual_mw",
]


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO timestamp, accepting either a space or T separator."""
    return datetime.fromisoformat(value.strip())


def parse_number(value: str) -> float | None:
    value = value.strip()
    if value == "":
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    return format(value, ".15g")


def load_entsoe_rows(path: Path) -> dict[datetime, dict[str, str]]:
    rows: dict[datetime, dict[str, str]] = {}

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "timestamp_berlin" not in reader.fieldnames:
            raise ValueError(
                "ENTSO-E input must contain a 'timestamp_berlin' column."
            )

        required = {
            spec[column_type]
            for spec in ZONE_COLUMNS.values()
            for column_type in ("price", "load")
        }
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(
                "ENTSO-E input is missing columns: " + ", ".join(sorted(missing))
            )

        for row_number, row in enumerate(reader, start=2):
            timestamp = parse_timestamp(row["timestamp_berlin"])
            if timestamp in rows:
                raise ValueError(
                    f"Duplicate ENTSO-E timestamp at row {row_number}: {timestamp}"
                )
            rows[timestamp] = row

    return rows


def validate_price(
    base_price: float,
    entsoe_price_text: str,
    zone: str,
    timestamp: datetime,
    tolerance: float,
) -> None:
    entsoe_price = parse_number(entsoe_price_text)
    if entsoe_price is None:
        raise ValueError(
            f"Missing ENTSO-E price for {zone} at {timestamp.isoformat()}"
        )

    if abs(base_price - entsoe_price) > tolerance:
        raise ValueError(
            "Price mismatch for "
            f"{zone} at {timestamp.isoformat()}: "
            f"base={base_price}, ENTSO-E={entsoe_price}"
        )


def create_dataset(
    price_path: Path,
    entsoe_path: Path,
    output_path: Path,
    tolerance: float,
    allow_missing_load: bool,
) -> dict[str, int]:
    entsoe_rows = load_entsoe_rows(entsoe_path)
    output_rows: list[dict[str, str]] = []
    seen_keys: set[tuple[datetime, str]] = set()

    hourly_price_rows = 0
    price_validations = 0
    rows_with_load = 0
    rows_without_load = 0

    with price_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "timestamp_utc",
            "timestamp_local",
            "bidding_zone",
            "price_eur_mwh",
        }
        if reader.fieldnames is None:
            raise ValueError("Price input has no header.")
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(
                "Price input is missing columns: " + ", ".join(sorted(missing))
            )

        for row_number, row in enumerate(reader, start=2):
            hourly_price_rows += 1
            base_utc = parse_timestamp(row["timestamp_utc"])
            base_local = parse_timestamp(row["timestamp_local"])
            zone = row["bidding_zone"].strip().upper()
            price = parse_number(row["price_eur_mwh"])

            if price is None:
                raise ValueError(f"Invalid price at row {row_number}")

            for quarter in range(4):
                delta = timedelta(minutes=15 * quarter)
                timestamp_utc = base_utc + delta
                timestamp_local = base_local + delta
                key = (timestamp_utc, zone)

                if key in seen_keys:
                    raise ValueError(
                        "Duplicate output key: "
                        f"{timestamp_utc.isoformat()}, {zone}"
                    )
                seen_keys.add(key)

                load_value: float | None = None

                if zone in ZONE_COLUMNS:
                    entsoe_row = entsoe_rows.get(timestamp_local)
                    if entsoe_row is None:
                        if not allow_missing_load:
                            raise ValueError(
                                "Missing ENTSO-E timestamp for "
                                f"{zone}: {timestamp_local.isoformat()}"
                            )
                    else:
                        spec = ZONE_COLUMNS[zone]
                        validate_price(
                            price,
                            entsoe_row[spec["price"]],
                            zone,
                            timestamp_local,
                            tolerance,
                        )
                        price_validations += 1
                        load_value = parse_number(entsoe_row[spec["load"]])

                        if load_value is None and not allow_missing_load:
                            raise ValueError(
                                "Missing actual load for "
                                f"{zone} at {timestamp_local.isoformat()}"
                            )

                if load_value is None:
                    rows_without_load += 1
                else:
                    rows_with_load += 1

                output_rows.append(
                    {
                        "timestamp_utc": timestamp_utc.isoformat(),
                        "timestamp_local": timestamp_local.isoformat(),
                        "bidding_zone": zone,
                        "price_eur_mwh": format_number(price),
                        "load_actual_mw": format_number(load_value),
                    }
                )

    output_rows.sort(
        key=lambda row: (
            parse_timestamp(row["timestamp_utc"]),
            row["bidding_zone"],
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    return {
        "hourly_price_rows": hourly_price_rows,
        "output_rows": len(output_rows),
        "price_validations": price_validations,
        "rows_with_load": rows_with_load,
        "rows_without_load": rows_without_load,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Expand hourly day-ahead prices to 15-minute resolution and "
            "attach actual ENTSO-E load."
        )
    )
    parser.add_argument(
        "--prices",
        type=Path,
        default=Path(
            "electricity_day_ahead_prices_2021-11-08_2021-11-14.csv"
        ),
        help="Hourly long-format price CSV.",
    )
    parser.add_argument(
        "--entsoe",
        type=Path,
        default=Path("entsoe_debs2022_nov2021.csv"),
        help="Wide 15-minute ENTSO-E CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "electricity_prices_and_load_15min_"
            "2021-11-08_2021-11-14.csv"
        ),
    )
    parser.add_argument(
        "--price-tolerance",
        type=float,
        default=1e-6,
        help="Maximum allowed price difference during source validation.",
    )
    parser.add_argument(
        "--allow-missing-load",
        action="store_true",
        help=(
            "Keep rows with an empty load instead of failing when DE-LU, FR, "
            "or NL load data is missing."
        ),
    )
    args = parser.parse_args()

    try:
        stats = create_dataset(
            args.prices,
            args.entsoe,
            args.output,
            args.price_tolerance,
            args.allow_missing_load,
        )
    except (OSError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {args.output.resolve()}")
    print(f"Hourly source rows: {stats['hourly_price_rows']:,}")
    print(f"15-minute output rows: {stats['output_rows']:,}")
    print(f"Validated price values: {stats['price_validations']:,}")
    print(f"Rows with load: {stats['rows_with_load']:,}")
    print(f"Rows without load: {stats['rows_without_load']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
