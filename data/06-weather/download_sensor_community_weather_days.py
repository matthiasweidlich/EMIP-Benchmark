#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ARCHIVE_YEAR_ROOT = "https://archive.sensor.community/2021/"
DEFAULT_START = date(2021, 11, 8)
DEFAULT_END = date(2021, 11, 14)
USER_AGENT = "SensorCommunity-WeatherDownloader/1.4"

# Temperature, humidity, and/or pressure sensors.
# Particulate-matter sensors such as SDS011, PMSx003, SPS30, HPM, and PPD42NS
# are intentionally excluded.
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

def parse_date(value: str) -> date:
    return date.fromisoformat(value)

def dates(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def build_session() -> requests.Session:
    retry = Retry(
        total=12,
        connect=12,
        read=12,
        status=12,
        backoff_factor=2.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Connection": "close"})
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

def fetch_index(session: requests.Session, day: str, cache_dir: Path, timeout: int) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"{day}.html"
    if cache.exists() and cache.stat().st_size > 100:
        return cache.read_text(encoding="utf-8", errors="replace")

    url = urljoin(ARCHIVE_YEAR_ROOT, f"{day}/")
    for attempt in range(1, 13):
        try:
            print(f"[{day}] Reading index (attempt {attempt}): {url}")
            r = session.get(url, timeout=(30, timeout))
            r.raise_for_status()
            if len(r.content) < 100:
                raise RuntimeError("Archive index response was unexpectedly small")
            cache.write_bytes(r.content)
            return r.text
        except Exception as exc:
            if attempt == 12:
                raise
            delay = min(120, 2 ** attempt)
            print(f"[{day}] Index failed: {exc}; retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)
    raise RuntimeError("unreachable")

def sensor_type_from_filename(filename: str) -> str:
    # Typical archive name:
    # 2021-11-08_bme280_sensor_12345.csv
    match = re.match(
        r"\d{4}-\d{2}-\d{2}_([^_]+)_sensor_",
        filename,
        flags=re.IGNORECASE,
    )
    return match.group(1).lower() if match else "unknown"

def list_files(
    index_html: str,
    day: str,
    selected_sensor_types: set[str],
) -> list[tuple[str, str]]:
    base = urljoin(ARCHIVE_YEAR_ROOT, f"{day}/")
    soup = BeautifulSoup(index_html, "html.parser")
    seen = set()
    out = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        name = href.rsplit("/", 1)[-1]
        if not (name.endswith(".csv") or name.endswith(".csv.gz")):
            continue
        if name in seen:
            continue

        sensor_type = sensor_type_from_filename(name)
        if sensor_type not in selected_sensor_types:
            continue

        seen.add(name)
        out.append((urljoin(base, href), name))

    return out

def download_one(url: str, dest: Path, timeout: int) -> tuple[str, bool, str | None]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest.name, True, None

    part = dest.with_suffix(dest.suffix + ".part")
    existing = part.stat().st_size if part.exists() else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}
    session = build_session()

    for attempt in range(1, 9):
        try:
            with session.get(url, headers=headers, stream=True, timeout=(30, timeout)) as r:
                if existing and r.status_code == 200:
                    existing = 0
                    headers = {}
                    if part.exists():
                        part.unlink()
                r.raise_for_status()
                mode = "ab" if existing and r.status_code == 206 else "wb"
                with part.open(mode) as fh:
                    for chunk in r.iter_content(1024 * 1024):
                        if chunk:
                            fh.write(chunk)
            part.replace(dest)
            return dest.name, False, None
        except Exception as exc:
            if attempt == 8:
                return dest.name, False, str(exc)
            delay = min(90, 2 ** attempt)
            print(f"Retry {attempt}/8 for {url}: {exc}; {delay}s", file=sys.stderr)
            time.sleep(delay)
            existing = part.stat().st_size if part.exists() else 0
            headers = {"Range": f"bytes={existing}-"} if existing else {}

    return dest.name, False, "unknown failure"

def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Download only temperature, humidity, and pressure sensor files "
            "from Sensor.Community."
        )
    )
    ap.add_argument("--start", type=parse_date, default=DEFAULT_START)
    ap.add_argument("--end", type=parse_date, default=DEFAULT_END)
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("sensor_community_weather_raw_days"),
    )
    ap.add_argument(
        "--sensor-types",
        nargs="+",
        default=sorted(DEFAULT_WEATHER_SENSOR_TYPES),
        help=(
            "Sensor types to download. Defaults to weather-related devices "
            "and excludes particulate-matter sensors."
        ),
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Keep this low; the archive may close aggressive connections.",
    )
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()

    if args.end < args.start:
        ap.error("--end must be >= --start")

    selected_sensor_types = {value.lower() for value in args.sensor_types}
    print("Included sensor types:")
    print("  " + ", ".join(sorted(selected_sensor_types)))

    session = build_session()
    cache_dir = args.output / "_indexes"

    total_errors = 0
    total_selected = 0

    for d in dates(args.start, args.end):
        day = d.isoformat()
        html = fetch_index(session, day, cache_dir, args.timeout)
        files = list_files(html, day, selected_sensor_types)
        total_selected += len(files)
        print(f"[{day}] Found {len(files):,} weather-sensor files")

        day_dir = args.output / day
        failures = []

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {
                pool.submit(download_one, url, day_dir / name, args.timeout): name
                for url, name in files
            }
            for i, fut in enumerate(as_completed(futs), 1):
                name, skipped, error = fut.result()
                if error:
                    failures.append((name, error))
                if i % 250 == 0 or i == len(futs):
                    print(
                        f"[{day}] {i:,}/{len(futs):,} processed; "
                        f"failures={len(failures)}"
                    )

        if failures:
            total_errors += len(failures)
            fail_path = args.output / f"failures_{day}.txt"
            fail_path.write_text(
                "\n".join(f"{name}\t{err}" for name, err in failures),
                encoding="utf-8",
            )
            print(f"[{day}] Wrote {fail_path}", file=sys.stderr)

    print(f"Selected weather files across all days: {total_selected:,}")
    print(f"Finished. Total unrecovered failures: {total_errors}")
    print("Re-run the same command to resume or retry missing files.")
    return 1 if total_errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
