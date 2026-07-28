#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import requests
from shapely.geometry import Point, box, shape
from shapely.ops import unary_union
from shapely.prepared import prep

NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/"
    "natural-earth-vector/master/geojson/ne_10m_admin_0_countries.geojson"
)

DEFAULT_ISO3 = {"AUT", "BEL", "CHE", "DEU", "FRA", "LIE", "LUX", "MCO", "NLD"}

MICROSTATE_FALLBACKS = {
    "LIE": box(9.45, 47.02, 9.66, 47.30),
    "MCO": box(7.40, 43.72, 7.45, 43.76),
}

def open_text(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="")
    return path.open("r", encoding="utf-8", errors="replace", newline="")

def load_geojson(cache: Path) -> dict:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        print(f"Downloading boundaries: {NE_URL}")
        r = requests.get(NE_URL, timeout=180)
        r.raise_for_status()
        cache.write_bytes(r.content)
    return json.loads(cache.read_text(encoding="utf-8"))

def country_geometries(geojson: dict, wanted: set[str]):
    geoms = defaultdict(list)
    names = {}
    code_fields = ("ADM0_A3", "ISO_A3", "ISO_A3_EH", "SOV_A3", "GU_A3", "SU_A3", "BRK_A3")

    for feature in geojson["features"]:
        props = feature.get("properties", {})
        codes = {str(props.get(k, "")).upper() for k in code_fields}
        matches = wanted.intersection(codes)
        for iso3 in matches:
            geoms[iso3].append(shape(feature["geometry"]))
            names[iso3] = (
                props.get("NAME_EN")
                or props.get("ADMIN")
                or props.get("NAME")
                or iso3
            )

    for iso3, fallback in MICROSTATE_FALLBACKS.items():
        if iso3 in wanted and not geoms.get(iso3):
            geoms[iso3].append(fallback)
            names[iso3] = {"LIE": "Liechtenstein", "MCO": "Monaco"}[iso3]

    missing = wanted - set(geoms)
    if missing:
        raise RuntimeError("No geometry for: " + ", ".join(sorted(missing)))

    return {iso3: prep(unary_union(parts)) for iso3, parts in geoms.items()}, names

def first_location(path: Path):
    try:
        with open_text(path) as fh:
            reader = csv.DictReader(fh, delimiter=";")
            row = next(reader)
        return (
            int(row["sensor_id"]),
            row.get("sensor_type", "unknown"),
            float(row["lat"]),
            float(row["lon"]),
        )
    except Exception:
        return None

def detect_country(lat: float, lon: float, prepared):
    p = Point(lon, lat)
    for iso3, geom in prepared.items():
        if geom.contains(p) or geom.covers(p):
            return iso3
    return None

def merge_group(paths: list[Path], destination: Path):
    # Two passes allow heterogeneous columns within a sensor type.
    fields = []
    seen = set()
    delimiter = ";"
    for p in paths:
        try:
            with open_text(p) as fh:
                reader = csv.DictReader(fh, delimiter=delimiter)
                for f in reader.fieldnames or []:
                    if f not in seen:
                        seen.add(f)
                        fields.append(f)
        except Exception:
            continue

    destination.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(destination, "wt", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        for p in paths:
            try:
                with open_text(p) as fh:
                    reader = csv.DictReader(fh, delimiter=delimiter)
                    for row in reader:
                        writer.writerow(row)
            except Exception as exc:
                print(f"WARNING: could not merge {p}: {exc}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path("sensor_community_raw_days"))
    ap.add_argument("--output", type=Path,
                    default=Path("sensor_community_western_europe_2021-11-08_2021-11-14"))
    ap.add_argument("--countries", nargs="+", default=sorted(DEFAULT_ISO3))
    ap.add_argument("--merge-by-sensor-type", action="store_true")
    ap.add_argument("--zip", action="store_true", dest="make_zip")
    ap.add_argument("--copy", action="store_true",
                    help="Copy files instead of using hard links where possible.")
    args = ap.parse_args()

    wanted = {x.upper() for x in args.countries}
    geojson = load_geojson(args.output / "_cache" / "countries.geojson")
    prepared, names = country_geometries(geojson, wanted)

    selected = []
    grouped = defaultdict(list)
    files = sorted(
        p for p in args.input.rglob("*")
        if p.is_file() and (p.name.endswith(".csv") or p.name.endswith(".csv.gz"))
        and "_indexes" not in p.parts
    )
    print(f"Inspecting {len(files):,} local files")

    raw_out = args.output / "raw"
    raw_out.mkdir(parents=True, exist_ok=True)

    for i, src in enumerate(files, 1):
        loc = first_location(src)
        if loc is None:
            continue
        sensor_id, sensor_type, lat, lon = loc
        iso3 = detect_country(lat, lon, prepared)
        if iso3 is None:
            continue

        day = next((part for part in src.parts if re.fullmatch(r"\d{4}-\d{2}-\d{2}", part)), "unknown")
        dest = raw_out / iso3 / day / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            if args.copy:
                shutil.copy2(src, dest)
            else:
                try:
                    dest.hardlink_to(src.resolve())
                except OSError:
                    shutil.copy2(src, dest)

        record = {
            "day": day,
            "filename": src.name,
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "lat": lat,
            "lon": lon,
            "country_iso3": iso3,
            "country": names[iso3],
            "relative_path": str(dest.relative_to(args.output)),
        }
        selected.append(record)
        grouped[sensor_type.lower()].append(dest)

        if i % 1000 == 0 or i == len(files):
            print(f"{i:,}/{len(files):,}; selected={len(selected):,}")

    meta = args.output / "metadata"
    meta.mkdir(parents=True, exist_ok=True)
    with (meta / "manifest.csv").open("w", encoding="utf-8", newline="") as fh:
        fields = list(selected[0].keys()) if selected else [
            "day", "filename", "sensor_id", "sensor_type", "lat", "lon",
            "country_iso3", "country", "relative_path"
        ]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)

    (meta / "selection.json").write_text(json.dumps({
        "countries": sorted(wanted),
        "selected_files": len(selected),
        "sensor_types": sorted(grouped),
    }, indent=2), encoding="utf-8")

    if args.merge_by_sensor_type:
        for sensor_type, paths in sorted(grouped.items()):
            print(f"Merging {sensor_type}: {len(paths):,} files")
            merge_group(paths, args.output / "merged" / f"{sensor_type}.csv.gz")

    cache = args.output / "_cache"
    if cache.exists():
        shutil.rmtree(cache)

    if args.make_zip:
        zip_path = args.output.with_suffix(".zip")
        print(f"Creating {zip_path}")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for p in sorted(args.output.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(args.output))
        print(f"Created {zip_path}")

    print(f"Selected {len(selected):,} files into {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
