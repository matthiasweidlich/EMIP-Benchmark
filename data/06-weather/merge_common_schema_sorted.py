#!/usr/bin/env python3
"""
Merge Sensor.Community weather CSV files into one globally time-sorted CSV.

Output schema:
    sensorID,lat,lon,timestamp,temperature,humidity

Particulate-matter sensor files are excluded by an explicit weather-sensor
allowlist. Missing humidity values use the value supplied through
--default-humidity; the default is an empty CSV field.

The script uses an external merge sort and therefore does not require the
complete dataset to fit in memory.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import heapq
import math
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, TextIO


OUTPUT_COLUMNS = [
    "sensorID",
    "lat",
    "lon",
    "timestamp",
    "temperature",
    "humidity",
]

TEMP_COLUMNS = [
    "__sort_timestamp",
    "__sort_sensor_id",
    *OUTPUT_COLUMNS,
]

DEFAULT_WEATHER_SENSOR_TYPES = {
    "bme280",
    "bme680",
    "bmp180",
    "bmp280",
    "bmp388",
    "dht11",
    "dht22",
    "ds18b20",
    "htu21d",
    "sht30",
    "sht31",
    "sht35",
    "sht3x",
    "sht85",
}


def open_input(path: Path) -> TextIO:
    if path.name.lower().endswith(".gz"):
        return gzip.open(
            path,
            mode="rt",
            encoding="utf-8",
            errors="replace",
            newline="",
        )
    return path.open(
        mode="r",
        encoding="utf-8",
        errors="replace",
        newline="",
    )


def open_output(path: Path, compressed: bool) -> TextIO:
    if compressed:
        return gzip.open(
            path,
            mode="wt",
            encoding="utf-8",
            newline="",
            compresslevel=6,
        )
    return path.open(
        mode="w",
        encoding="utf-8",
        newline="",
    )


def discover_files(input_dir: Path) -> list[Path]:
    return sorted(
        path.resolve()
        for path in input_dir.rglob("*")
        if path.is_file()
        and (
            path.name.lower().endswith(".csv")
            or path.name.lower().endswith(".csv.gz")
        )
        and "_indexes" not in path.parts
        and "metadata" not in path.parts
        and "merged" not in path.parts
    )


def infer_sensor_type(path: Path) -> str | None:
    match = re.match(
        r"\d{4}-\d{2}-\d{2}_([^_]+)_sensor_",
        path.name,
        flags=re.IGNORECASE,
    )
    return match.group(1).lower() if match else None


def first_value(
    row: dict[str, str],
    aliases: tuple[str, ...],
) -> str:
    normalized = {
        str(key).strip().lower(): value
        for key, value in row.items()
        if key is not None
    }

    for alias in aliases:
        value = normalized.get(alias)
        if value is not None and str(value).strip() != "":
            return str(value).strip()

    return ""


def normalize_float(value: str) -> str:
    value = value.strip()
    if not value:
        return ""

    try:
        number = float(value.replace(",", "."))
    except ValueError:
        return ""

    if not math.isfinite(number):
        return ""

    return format(number, ".15g")


def normalize_integer(value: str) -> str:
    value = value.strip()
    if not value:
        return ""

    try:
        return str(int(float(value)))
    except ValueError:
        return ""


def normalize_timestamp(value: str) -> tuple[str, str] | None:
    raw = value.strip()
    if not raw:
        return None

    candidate = raw
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    parsed: datetime | None = None

    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        for timestamp_format in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f",
        ):
            try:
                parsed = datetime.strptime(raw, timestamp_format)
                break
            except ValueError:
                continue

    if parsed is None:
        return None

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
        output_value = (
            parsed.isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
    else:
        output_value = parsed.isoformat(timespec="microseconds")

    return output_value, output_value


def normalize_row(
    row: dict[str, str],
    filename_sensor_type: str | None,
    allowed_sensor_types: set[str],
    default_humidity: str,
) -> dict[str, str] | None:
    row_sensor_type = first_value(
        row,
        ("sensor_type", "sensortype", "type"),
    ).lower()

    sensor_type = row_sensor_type or filename_sensor_type or ""
    if sensor_type not in allowed_sensor_types:
        return None

    normalized_timestamp = normalize_timestamp(
        first_value(
            row,
            ("timestamp", "event_time", "datetime", "time"),
        )
    )
    if normalized_timestamp is None:
        return None

    sort_timestamp, output_timestamp = normalized_timestamp

    sensor_id = normalize_integer(
        first_value(row, ("sensor_id", "sensorid", "id"))
    )
    latitude = normalize_float(
        first_value(row, ("lat", "latitude"))
    )
    longitude = normalize_float(
        first_value(row, ("lon", "lng", "longitude"))
    )
    temperature = normalize_float(
        first_value(
            row,
            ("temperature", "temperature_c", "temp"),
        )
    )
    humidity = normalize_float(
        first_value(
            row,
            (
                "humidity",
                "humidity_percent",
                "relative_humidity",
            ),
        )
    )

    if not humidity:
        humidity = default_humidity

    return {
        "__sort_timestamp": sort_timestamp,
        "__sort_sensor_id": sensor_id.zfill(20) if sensor_id else "9" * 20,
        "sensorID": sensor_id,
        "lat": latitude,
        "lon": longitude,
        "timestamp": output_timestamp,
        "temperature": temperature,
        "humidity": humidity,
    }


def row_sort_key(row: dict[str, str]) -> tuple[str, str]:
    return row["__sort_timestamp"], row["__sort_sensor_id"]


def write_chunk(
    rows: list[dict[str, str]],
    chunk_dir: Path,
    chunk_number: int,
) -> Path:
    rows.sort(key=row_sort_key)
    path = chunk_dir / f"chunk_{chunk_number:06d}.csv.gz"

    with gzip.open(
        path,
        mode="wt",
        encoding="utf-8",
        newline="",
        compresslevel=3,
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=TEMP_COLUMNS,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    return path


def read_chunk(
    path: Path,
) -> tuple[TextIO, csv.DictReader]:
    handle = gzip.open(
        path,
        mode="rt",
        encoding="utf-8",
        newline="",
    )
    return handle, csv.DictReader(handle)


def merge_chunks(
    chunk_paths: list[Path],
    output_path: Path,
    compressed: bool,
) -> int:
    handles: list[TextIO] = []
    readers: list[csv.DictReader] = []
    heap: list[
        tuple[
            tuple[str, str],
            int,
            dict[str, str],
        ]
    ] = []

    try:
        for index, path in enumerate(chunk_paths):
            handle, reader = read_chunk(path)
            handles.append(handle)
            readers.append(reader)

            first_row = next(reader, None)
            if first_row is not None:
                heapq.heappush(
                    heap,
                    (
                        row_sort_key(first_row),
                        index,
                        first_row,
                    ),
                )

        written = 0

        with open_output(output_path, compressed) as output_handle:
            writer = csv.DictWriter(
                output_handle,
                fieldnames=OUTPUT_COLUMNS,
                extrasaction="ignore",
            )
            writer.writeheader()

            while heap:
                _, reader_index, row = heapq.heappop(heap)
                writer.writerow(row)
                written += 1

                next_row = next(readers[reader_index], None)
                if next_row is not None:
                    heapq.heappush(
                        heap,
                        (
                            row_sort_key(next_row),
                            reader_index,
                            next_row,
                        ),
                    )

                if written % 1_000_000 == 0:
                    print(f"Merged {written:,} rows")

        return written

    finally:
        for handle in handles:
            handle.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create one globally time-sorted Sensor.Community weather CSV "
            "with a common six-column schema."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help=(
            "Directory containing Sensor.Community CSV or CSV.GZ files. "
            "Use the Western-Europe-filtered raw directory when available."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "sensor_community_weather_western_europe_"
            "2021-11-08_2021-11-14_sorted.csv"
        ),
    )
    parser.add_argument(
        "--default-humidity",
        default="",
        help=(
            "Value written when humidity is unavailable. "
            "Default: empty CSV field. Example: --default-humidity -1"
        ),
    )
    parser.add_argument(
        "--sensor-types",
        nargs="+",
        default=sorted(DEFAULT_WEATHER_SENSOR_TYPES),
        help=(
            "Weather sensor types to include. "
            "Particulate-matter sensors are excluded by default."
        ),
    )
    parser.add_argument(
        "--chunk-rows",
        type=int,
        default=250_000,
        help=(
            "Number of rows sorted in memory at once. "
            "Lower this when memory is limited."
        ),
    )
    parser.add_argument(
        "--temp-directory",
        type=Path,
        default=Path("sensor_community_sort_tmp"),
        help="Temporary directory used by the external sort.",
    )
    parser.add_argument(
        "--gzip",
        action="store_true",
        help="Write a compressed .csv.gz file.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary sorted chunks after completion.",
    )

    args = parser.parse_args()

    input_dir = args.input.expanduser().resolve()
    if not input_dir.is_dir():
        parser.error(f"Input directory not found: {input_dir}")

    if args.chunk_rows < 1:
        parser.error("--chunk-rows must be at least 1")

    output_path = args.output.expanduser().resolve()
    compressed = (
        args.gzip
        or output_path.name.lower().endswith(".gz")
    )

    if args.gzip and not output_path.name.lower().endswith(".gz"):
        output_path = output_path.with_name(
            output_path.name + ".gz"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_dir = args.temp_directory.expanduser().resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)

    allowed_sensor_types = {
        value.lower()
        for value in args.sensor_types
    }

    all_files = discover_files(input_dir)
    if not all_files:
        parser.error(
            f"No CSV or CSV.GZ files found below {input_dir}"
        )

    selected_files = []
    unknown_files = []

    for path in all_files:
        sensor_type = infer_sensor_type(path)
        if sensor_type is None:
            unknown_files.append(path)
        elif sensor_type in allowed_sensor_types:
            selected_files.append(path)

    selected_files.extend(unknown_files)
    selected_files = sorted(set(selected_files))

    if not selected_files:
        parser.error(
            "No weather sensor files matched the configured sensor types."
        )

    print(f"Discovered files: {len(all_files):,}")
    print(f"Potential weather files: {len(selected_files):,}")
    print(f"Humidity default: {args.default_humidity!r}")
    print(f"Output: {output_path}")

    chunk_paths: list[Path] = []
    rows_buffer: list[dict[str, str]] = []
    valid_rows = 0
    ignored_rows = 0
    failed_files = 0
    chunk_number = 0

    for file_number, path in enumerate(selected_files, 1):
        filename_sensor_type = infer_sensor_type(path)

        try:
            with open_input(path) as handle:
                reader = csv.DictReader(handle, delimiter=";")

                for source_row in reader:
                    normalized = normalize_row(
                        source_row,
                        filename_sensor_type,
                        allowed_sensor_types,
                        args.default_humidity,
                    )

                    if normalized is None:
                        ignored_rows += 1
                        continue

                    rows_buffer.append(normalized)
                    valid_rows += 1

                    if len(rows_buffer) >= args.chunk_rows:
                        chunk_number += 1
                        chunk_paths.append(
                            write_chunk(
                                rows_buffer,
                                temp_dir,
                                chunk_number,
                            )
                        )
                        rows_buffer = []
                        print(
                            f"Wrote chunk {chunk_number:,}; "
                            f"accepted rows={valid_rows:,}"
                        )

        except (OSError, csv.Error, UnicodeError) as exc:
            failed_files += 1
            print(
                f"WARNING: skipped {path}: {exc}",
                file=sys.stderr,
            )

        if (
            file_number % 500 == 0
            or file_number == len(selected_files)
        ):
            print(
                f"Processed files "
                f"{file_number:,}/{len(selected_files):,}; "
                f"accepted rows={valid_rows:,}"
            )

    if rows_buffer:
        chunk_number += 1
        chunk_paths.append(
            write_chunk(
                rows_buffer,
                temp_dir,
                chunk_number,
            )
        )

    if not chunk_paths:
        parser.error(
            "No valid weather rows were found in the input files."
        )

    print(
        f"Merging {len(chunk_paths):,} sorted chunks "
        "into the final CSV..."
    )

    written_rows = merge_chunks(
        chunk_paths,
        output_path,
        compressed,
    )

    if not args.keep_temp:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("")
    print("Finished")
    print(f"Rows written: {written_rows:,}")
    print(f"Rows ignored: {ignored_rows:,}")
    print(f"Unreadable files: {failed_files:,}")
    print(f"Created: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
