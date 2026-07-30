#!/usr/bin/env bash
# Build the EMIP silver layer into a DuckDB database.
# Usage: silver/build.sh [output.duckdb]   (default: silver/emip.duckdb)
# Requires python3 with the duckdb package (pip install duckdb).
set -euo pipefail
cd "$(dirname "$0")/.."

DB=${1:-silver/emip.duckdb}

# GDELT full files are committed zipped; extracted copies are gitignored.
for z in gkg_energy_enriched gkg_energy_event_link; do
    if [ ! -f "data/04-gdelt-news-events/$z.csv" ]; then
        echo "== unzipping $z.zip"
        unzip -q -o "data/04-gdelt-news-events/$z.zip" -d data/04-gdelt-news-events
    fi
done

rm -f "$DB"
python3 - "$DB" <<'EOF'
import glob, sys
import duckdb

con = duckdb.connect(sys.argv[1])
for path in sorted(glob.glob("silver/sql/*.sql")):
    print(f"== {path}", flush=True)
    con.execute(open(path).read())
print("== row counts")
print(con.sql("""
    SELECT table_name, estimated_size AS rows
    FROM duckdb_tables() WHERE schema_name = 'silver'
    ORDER BY table_name"""))
EOF
echo "== silver layer built: $DB"
