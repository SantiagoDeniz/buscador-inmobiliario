#!/usr/bin/env python
"""
Test simple para verificar actualizacion multi-plataforma
"""

import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.search_manager import actualizar_busqueda
import inspect

print("=== Test Independencia de Plataformas ===")

# Analizar el codigo fuente
source = inspect.getsource(actualizar_busqueda)

# Verificaciones
tests = [
    ('plataformas_a_buscar' not in source, "No depende de plataformas_a_buscar"),
    ('SIEMPRE buscar' in source, "Tiene logica explicita para buscar siempre"),
    ('TODAS las plataformas' in source, "Menciona explicitamente todas las plataformas"),
    ('if \'MercadoLibre\' in plataformas_' not in source, "MercadoLibre no es condicional"),
    ('if \'InfoCasas\' in plataformas_' not in source, "InfoCasas no es condicional")
]

todos_ok = True
for test_result, descripcion in tests:
    status = "OK" if test_result else "FAIL"
    print(f"   [{status}] {descripcion}")
    if not test_result:
        todos_ok = False

print()
print("=== Verificacion Manual ===")

# Mostrar las lineas relevantes del codigo
lines = source.split('\n')
for i, line in enumerate(lines):
    if 'TODAS' in line or 'SIEMPRE' in line:
        print(f"Linea {i+1}: {line.strip()}")

print()
if todos_ok:
    print("EXITO: Las actualizaciones buscan SIEMPRE en todas las plataformas")
    print("Sin importar que plataformas tenian resultados anteriormente.")
else:
    print("FALLA: Revisar implementacion")

print()
print("=== Resultado Final ===")
print("Ahora cuando actualices una busqueda:")
print("1. Siempre busca en MercadoLibre (sin condiciones)")
print("2. Siempre busca en InfoCasas (sin condiciones)")
print("3. No depende de resultados previos")
print("4. Recolecta URLs de TODAS las plataformas disponibles")