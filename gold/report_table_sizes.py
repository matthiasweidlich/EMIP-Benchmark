#!/usr/bin/env python3
"""Generate docs/table-sizes.md: per-table storage breakdown of the EMIP
DuckDB database (exact row counts, column counts, on-disk size from
storage-block usage). Bronze is views over the raw files and occupies no
database storage; silver and gold are materialized.

Usage: .venv/bin/python gold/report_table_sizes.py [db_path]
"""
import datetime
import os
import sys

import duckdb

DB = sys.argv[1] if len(sys.argv) > 1 else "silver/emip.duckdb"
OUT = "docs/table-sizes.md"

con = duckdb.connect(DB, read_only=True)

block_size, used_blocks = con.sql(
    "SELECT block_size, used_blocks FROM pragma_database_size()").fetchone()
db_size = os.path.getsize(DB)

tables = con.sql("""
    SELECT schema_name, table_name, column_count
    FROM duckdb_tables()
    WHERE NOT temporary
    ORDER BY schema_name, table_name""").fetchall()

rows_out = []
for schema, table, ncols in tables:
    n = con.sql(f'SELECT count(*) FROM "{schema}"."{table}"').fetchone()[0]
    blocks = con.sql(f"""SELECT count(DISTINCT block_id)
                         FROM pragma_storage_info('{schema}.{table}')
                         WHERE block_id >= 0""").fetchone()[0]
    rows_out.append((schema, table, n, ncols, blocks * block_size))

rows_out.sort(key=lambda r: -r[4])
total_bytes = sum(r[4] for r in rows_out)


def fmt_bytes(b):
    for unit in ("B", "KiB", "MiB", "GiB"):
        if b < 1024 or unit == "GiB":
            return f"{b:,.1f} {unit}" if unit != "B" else f"{b:,.0f} B"
        b /= 1024


with open(OUT, "w") as f:
    w = f.write
    w("# EMIP DuckDB Table Sizes\n\n")
    w(f"Generated {datetime.date.today()} from `{DB}` by "
      "`gold/report_table_sizes.py` (rerun after a rebuild).\n\n")
    w(f"Database file: **{fmt_bytes(db_size)}** "
      f"({used_blocks:,} blocks x {block_size // 1024} KiB). Bronze is views "
      "over the raw files (no database storage); silver and gold are "
      "materialized tables.\n\n")
    w("| Table | Rows | Columns | On disk | % of stored bytes | Bytes/row |\n")
    w("|---|---:|---:|---:|---:|---:|\n")
    for schema, table, n, ncols, b in rows_out:
        share = 100 * b / total_bytes if total_bytes else 0
        per_row = f"{b / n:,.0f}" if n else "-"
        w(f"| `{schema}.{table}` | {n:,} | {ncols} | {fmt_bytes(b)} "
          f"| {share:.1f}% | {per_row} |\n")
    w(f"| **total** | | | **{fmt_bytes(total_bytes)}** | 100% | |\n\n")
    w("Notes:\n\n")
    w("- On-disk size counts the distinct storage blocks used per table "
      "(`pragma_storage_info`), i.e. compressed size including per-column "
      "metadata; small tables round up to one block.\n")
    w("- The database file can be larger than the sum of table bytes "
      "(free blocks from rebuilds, catalog, WAL checkpointing).\n")
    w("- Row counts are exact (`count(*)` at generation time).\n")

print(f"wrote {OUT}: {len(rows_out)} tables, "
      f"{fmt_bytes(total_bytes)} stored, db file {fmt_bytes(db_size)}")
