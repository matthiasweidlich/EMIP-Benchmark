#!/usr/bin/env bash
# Run the EMIP benchmark queries with per-query timing.
# Usage: gold/run_benchmark_queries.sh [db.duckdb]   (default: silver/emip.duckdb)
set -euo pipefail
cd "$(dirname "$0")/.."

DB=${1:-silver/emip.duckdb}

python3 - "$DB" <<'EOF'
import sys, time
import duckdb

con = duckdb.connect(sys.argv[1], read_only=True)
con.execute("SET TimeZone='UTC'")
sql = open("gold/benchmark_queries.sql").read()
for block in sql.split(";"):
    block = block.strip()
    if not block:
        continue
    title = next((l for l in block.splitlines() if l.startswith("-- B")),
                 block.splitlines()[0]).lstrip("- ").strip()
    t0 = time.time()
    result = con.sql(block)
    if result is not None:
        rows = result.fetchall()
        print(f"\n---- {title}  [{time.time() - t0:.2f}s, {len(rows)} rows]")
        con.sql(block).show(max_rows=40, max_width=170)
EOF
