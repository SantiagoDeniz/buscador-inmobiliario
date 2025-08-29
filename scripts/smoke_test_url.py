import os, sys
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from core.scraper.url_builder import build_mercadolibre_url

filtros = {
    'tipo': 'apartamento',
    'operacion': 'alquiler',
    'departamento': 'Montevideo',
    'ciudad': 'Pocitos',
    'dormitorios_min': 1,
    'dormitorios_max': 2,
    'precio_min': 500,
    'precio_max': 1000,
    'moneda': 'USD',
}

url = build_mercadolibre_url(filtros)
print(url)
with open(os.path.join(os.path.dirname(__file__), 'smoke_url_out.txt'), 'w', encoding='utf-8') as f:
    f.write(url)
