import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'buscador_inmobiliario.db')
DB_PATH = os.path.abspath(DB_PATH)

print('DB path:', DB_PATH)
print('Exists:', os.path.exists(DB_PATH))
if not os.path.exists(DB_PATH):
    raise SystemExit(1)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
rows = [r[0] for r in cur.fetchall()]
print('Tables count:', len(rows))
for r in rows:
    print(' -', r)
con.close()
