"""Script de prueba para llamar al endpoint http_search_fallback y verificar guardado"""
import os
import sys
import json

# Asegurar que la raíz del proyecto esté en sys.path para poder importar 'buscador.settings'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Configurar settings antes de importar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
import django
django.setup()

from django.test import Client
from core.search_manager import get_all_searches, get_search, load_results
from core.models import Busqueda, ResultadoBusqueda, Propiedad

client = Client()

# Filtros usados en el smoke
filtros = {
    'tipo': 'apartamento',
    'operacion': 'alquiler',
    'departamento': 'Montevideo',
    'ciudad': 'Pocitos',
    'moneda': 'USD',
    'precio_min': 500,
    'precio_max': 1000
}

payload = {
    'texto': '',
    'filtros': filtros,
    'guardar': True,
    'name': 'Smoke test save'
}

resp = client.post('/http_search_fallback/', data=json.dumps(payload), content_type='application/json', HTTP_HOST='localhost')
print('HTTP status:', resp.status_code)
try:
    data = resp.json()
except Exception:
    data = {'raw': resp.content}
print('Response json:', data)

# Buscar la última búsqueda creada
searches = get_all_searches()
print('Total searches after call:', len(searches))
created = None
for s in searches:
    if s['nombre_busqueda'].startswith('Smoke test save'):
        created = s
        break

if not created:
    print('No se encontró la búsqueda guardada')
else:
    print('Found saved search ID:', created['id'])
    results = load_results(created['id'])
    print('Loaded results count for saved search:', len(results))
    if len(results) > 0:
        print('Example result url:', results[0].get('url'))

# Mostrar Propiedades relacionadas recientes
props = Propiedad.objects.order_by('-id')[:10]
print('Recent properties count:', props.count())
for p in props:
    print('-', p.url)
