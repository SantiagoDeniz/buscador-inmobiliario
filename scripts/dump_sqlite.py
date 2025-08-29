import argparse
import csv
import os
import sqlite3
import sys


def detect_db_path(default_name: str = "buscador_inmobiliario.db") -> str:
    # repo root assumed as two levels up from this script
    here = os.path.abspath(os.path.dirname(__file__))
    candidates = [
        os.path.abspath(os.path.join(here, "..", default_name)),
        os.path.abspath(os.path.join(here, default_name)),
        os.path.abspath(default_name),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def list_tables(con: sqlite3.Connection) -> list[str]:
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [r[0] for r in cur.fetchall()]


def dump_table(con: sqlite3.Connection, table: str, limit: int | None) -> None:
    cur = con.cursor()
    q = f"SELECT * FROM {table}"
    if limit and limit > 0:
        q += f" LIMIT {int(limit)}"
    try:
        cur.execute(q)
    except sqlite3.Error as e:
        print(f"[ERROR] Query failed for table {table}: {e}", file=sys.stderr)
        return
    cols = [d[0] for d in cur.description]
    w = csv.writer(sys.stdout)
    print(f"\n-- {table} --")
    w.writerow(cols)
    for row in cur.fetchall():
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser(description="Dump SQLite tables (CSV to stdout)")
    ap.add_argument("--db", help="Path to SQLite DB file (defaults to buscador_inmobiliario.db)")
    ap.add_argument("--table", help="Single table to dump")
    ap.add_argument("--all", action="store_true", help="Dump all tables")
    ap.add_argument("--limit", type=int, default=20, help="Max rows per table (default 20)")
    args = ap.parse_args()

    db_path = args.db or detect_db_path()
    if not os.path.exists(db_path):
        print(f"[ERROR] DB not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(db_path)
    try:
        if args.table and args.all:
            print("[ERROR] Use either --table or --all, not both", file=sys.stderr)
            sys.exit(2)

        if args.table:
            dump_table(con, args.table, args.limit)
        else:
            tables = list_tables(con)
            # skip SQLite internals unless explicitly requested
            if not args.all and not args.table:
                print("[INFO] Tables:")
                for t in tables:
                    print(f" - {t}")
                print("\nTip: pass --table <name> or --all to dump rows.")
            else:
                for t in tables:
                    dump_table(con, t, args.limit)
    finally:
        con.close()


if __name__ == "__main__":
    main()
