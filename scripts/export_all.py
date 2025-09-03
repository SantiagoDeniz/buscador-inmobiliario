#!/usr/bin/env python
"""
Exporta todos los modelos del dominio y tablas a CSV.
- Genera exports/<timestamp>/ y exports/latest/
- Crea _manifest.json y _manifest.csv con auditoría básica

Uso:
  python scripts/export_all.py [--base-dir exports] [--keep 1]

Ejemplos:
  python scripts/export_all.py
  python scripts/export_all.py --base-dir exports --keep 0
"""
import os
import sys
import argparse

# Ajustar path para poder importar el proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
import django  # noqa

def main():
    parser = argparse.ArgumentParser(description='Exportar datos a CSV')
    parser.add_argument('--base-dir', default=os.path.join(BASE_DIR, 'exports'), help='Directorio base de salida (por defecto: ./exports)')
    parser.add_argument('--keep', type=int, default=1, help='Cuántos snapshots con timestamp conservar (por defecto: 1)')
    args = parser.parse_args()

    django.setup()

    from core.export_utils import export_all, prune_old_exports, audit_exports

    base_dir = args.base_dir
    os.makedirs(base_dir, exist_ok=True)

    print(f"[EXPORT] Exportando a: {base_dir}")
    export_all(base_dir)

    if args.keep is not None and args.keep >= 0:
        print(f"[EXPORT] Podando snapshots antiguos, mantener: {args.keep}")
        prune_old_exports(base_dir, keep=args.keep)

    print("[EXPORT] Generando manifiesto y auditoría...")
    manifest = audit_exports(base_dir)
    print(f"[EXPORT] Archivos: {manifest['summary'].get('files')} | Filas totales: {manifest['summary'].get('rows_total_csv')}")
    print("[EXPORT] Listo.")

if __name__ == '__main__':
    main()
