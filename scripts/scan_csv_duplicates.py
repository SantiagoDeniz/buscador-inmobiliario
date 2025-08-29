import csv
import os
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'exports', 'latest'))

def scan_file(path: str):
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        r = csv.reader(f)
        headers = next(r, [])
        cnt = Counter(tuple(row) for row in r)
    dups = [(row, n) for row, n in cnt.items() if n > 1]
    return headers, dups

def main():
    if not os.path.exists(BASE):
        print(f"No existe: {BASE}")
        return
    any_dups = False
    for name in sorted(os.listdir(BASE)):
        if not name.endswith('.csv'):
            continue
        path = os.path.join(BASE, name)
        headers, dups = scan_file(path)
        if dups:
            any_dups = True
            print(f"[DUP] {name} -> {len(dups)} filas repetidas")
        else:
            print(f"[OK ] {name}")
    if not any_dups:
        print("Sin duplicados en exports/latest")

if __name__ == '__main__':
    main()
