import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "buscador.settings")
    try:
        import django
        django.setup()
    except Exception as e:
        print(f"[ERROR] Django setup failed: {e}")
        sys.exit(1)

    from django.conf import settings
    from django.db import connection

    db_cfg = settings.DATABASES.get("default", {})
    engine = db_cfg.get("ENGINE")
    name = db_cfg.get("NAME")
    lines = []
    def out(*args):
        print(*args)
        lines.append(" ".join(str(a) for a in args))

    out("Engine:", engine)
    out("Name:", name)

    # List tables via Django (works for any backend)
    try:
        tables = connection.introspection.table_names()
        out("\n[Django introspection] Tables (", len(tables), "):")
        for t in sorted(tables):
            out(" -", t)
    except Exception as e:
        out("[ERROR] Introspection failed:", e)

    # If SQLite, also check the file and query sqlite_master for clarity
    if engine and engine.endswith("sqlite3"):
        try:
            import sqlite3
            exists = os.path.exists(name)
            size = os.path.getsize(name) if exists else 0
            out(f"\n[SQLite] File exists: {exists} | size: {size} bytes")
            if exists:
                con = sqlite3.connect(name)
                cur = con.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                rows = [r[0] for r in cur.fetchall()]
                out("[SQLite] Tables (", len(rows), "):")
                for r in rows:
                    out(" -", r)
                con.close()
        except Exception as e:
            out("[ERROR] SQLite direct check failed:", e)

    # Write to file for reliable viewing
    try:
        with open("tables_out.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as e:
        print("[WARN] Could not write tables_out.txt:", e)


if __name__ == "__main__":
    main()
