import os, sys
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
import django
django.setup()

from core.scraper import run_scraper

filters = {
    'tipo': 'apartamento',
    'operacion': 'alquiler',
    'departamento': 'Montevideo',
    'ciudad': 'Pocitos',
    'precio_min': 500,
    'precio_max': 1000,
    'moneda': 'USD',
}

# Nota: esto guardará en la base si encuentra coincidencias.
run_scraper(filters, keywords=[], max_paginas=1, workers_fase1=1, workers_fase2=1)
print("Run scraper finalizado (smoke)")
