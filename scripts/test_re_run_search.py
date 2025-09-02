import os
import sys
import json
import traceback
from datetime import datetime

# Configurar Django
print('[TEST] Iniciando test_re_run_search.py')
print('[TEST] CWD:', os.getcwd())
print('[TEST] PYTHONPATH has manage.py?', os.path.exists('manage.py'))
# Insertar raíz del proyecto en sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
print('[TEST] sys.path[0]:', sys.path[0])
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
print('[TEST] DJANGO_SETTINGS_MODULE =', os.environ.get('DJANGO_SETTINGS_MODULE'))
import django
try:
    django.setup()
    print('[TEST] django.setup() OK')
except Exception as e:
    print('[TEST][ERROR] django.setup() falló:', e)
    traceback.print_exc()
    sys.exit(1)

from django.test import RequestFactory, Client
from django.http import HttpRequest
from core.models import Busqueda


def main():
    title = os.environ.get('TEST_SEARCH_TITLE', 'asd5')
    print('[TEST] main() iniciado, título objetivo =', title)
    try:
        count = Busqueda.objects.count()
        print('[TEST] Busquedas en DB:', count)
        b = Busqueda.objects.get(nombre_busqueda=title)
        print('[TEST] Encontrada búsqueda:', b.id)
    except Busqueda.DoesNotExist:
        print(f"ERROR: No se encontró una búsqueda con título '{title}'.")
        from core.models import Busqueda as B
        titulos = list(B.objects.values_list('nombre_busqueda', flat=True)[:20])
        print("Disponibles (primeros 20):", titulos)
        sys.exit(2)
    except Exception as e:
        print('[TEST][ERROR] Al consultar búsquedas:', e)
        traceback.print_exc()
        sys.exit(2)

    path = f"/re_run_search/{b.id}/?max_paginas=0&limit=20"
    print(f"[TEST] POST {path} @ {datetime.now().isoformat(timespec='seconds')}")
    mode = os.environ.get('TEST_MODE', 'rf')
    if mode == 'client':
        print('[TEST] Usando Django Test Client')
        client = Client(enforce_csrf_checks=False)
        resp = client.post(path)
    else:
        print('[TEST] Usando RequestFactory + llamada directa a la vista')
        from core.views import re_run_search as view_re_run
        rf = RequestFactory()
        request = rf.post(path)
        resp = view_re_run(request, str(b.id))
    print('[TEST] Respuesta recibida')
    print("HTTP STATUS:", getattr(resp, 'status_code', 'sin status_code'))
    try:
        data = resp.json()
        print('[TEST] JSON decodificado')
    except Exception as e:
        print("ERROR: Respuesta no es JSON válido:", e)
        try:
            content = resp.content.decode('utf-8', errors='ignore')
            print(content[:4000])
        except Exception:
            print('[TEST] No se pudo decodificar contenido de respuesta')
        sys.exit(3)

    print("JSON success:", data.get('success'))
    if not data.get('success'):
        print("ERROR:", data.get('error'))
        sys.exit(4)

    print("search_id:", data.get('search_id'))
    print("name:", data.get('name'))
    print("results_count:", data.get('results_count'))
    print("ultima_revision:", data.get('ultima_revision'))

    # Muestra un fragmento del HTML resultante para verificar contenido
    html = data.get('html', '')
    print("HTML fragment:")
    print(html[:800])

    # Éxito si llegó aquí
    print('[TEST] OK')
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('[TEST][ERROR] Excepción no controlada:', e)
        traceback.print_exc()
        sys.exit(1)
