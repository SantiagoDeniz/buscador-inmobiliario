from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os


class Command(BaseCommand):
    help = "List database tables using Django introspection (and SQLite details if applicable)."

    def handle(self, *args, **options):
        out_lines = []
        def out(msg):
            self.stdout.write(msg)
            out_lines.append(msg)

        engine = settings.DATABASES['default']['ENGINE']
        name = settings.DATABASES['default']['NAME']
        out(f"Engine: {engine}")
        out(f"Name: {name}")

        try:
            tables = connection.introspection.table_names()
            out(f"\n[Django] Tables ({len(tables)}):")
            for t in sorted(tables):
                out(f" - {t}")
        except Exception as e:
            out(f"[ERROR] Introspection failed: {e}")

        if engine.endswith('sqlite3'):
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
                    out(f"[SQLite] Tables ({len(rows)}):")
                    for r in rows:
                        out(f" - {r}")
                    con.close()
            except Exception as e:
                out(f"[ERROR] SQLite direct check failed: {e}")

        # also write to file for retrieval
        try:
            with open("tables_mgmt.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(out_lines))
        except Exception as e:
            self.stderr.write(f"[WARN] Could not write tables_mgmt.txt: {e}")
