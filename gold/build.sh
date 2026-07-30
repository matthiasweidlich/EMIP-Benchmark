#!/usr/bin/env bash
# Full rebuild of the EMIP analytical database: silver layer, then gold layer,
# then the dashboard smoke queries.
# Usage: gold/build.sh [output.duckdb]   (default: silver/emip.duckdb)
# Requires python3 with the duckdb package (pip install duckdb).
set -euo pipefail
cd "$(dirname "$0")/.."

DB=${1:-silver/emip.duckdb}

silver/build.sh "$DB"

python3 - "$DB" <<'EOF'
import glob, sys
import duckdb

con = duckdb.connect(sys.argv[1])
for path in sorted(glob.glob("gold/sql/*.sql")):
    print(f"== {path}", flush=True)
    con.execute(open(path).read())
print("== gold row counts")
print(con.sql("""
    SELECT table_name, estimated_size AS rows
    FROM duckdb_tables() WHERE schema_name = 'gold'
    ORDER BY table_name"""))
print("== dashboard smoke queries")
sql = open("gold/dashboard_queries.sql").read()
for block in sql.split(";"):
    block = block.strip()
    if not block:
        continue
    title = block.splitlines()[0].lstrip("- ").strip()
    result = con.sql(block)
    if result is not None:
        print(f"\n---- {title}")
        print(result)
EOF
echo "== gold layer built: $DB"
