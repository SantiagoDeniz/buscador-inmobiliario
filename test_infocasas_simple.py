#!/usr/bin/env python
"""
Test rápido del flujo simplificado de InfoCasas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper import run_scraper_infocasas

# Test básico con filtros simples
filtros = {'operacion': 'alquiler', 'tipo': 'apartamento'}
keywords = ['garaje']

print('🧪 Probando flujo simplificado de InfoCasas...')
resultados = run_scraper_infocasas(filtros, keywords, max_paginas=1)
print(f'✅ Resultado: {len(resultados)} propiedades encontradas')

if resultados:
    print('📋 Primeras 3 propiedades:')
    for i, prop in enumerate(resultados[:3], 1):
        titulo = prop.get('title', 'Sin título')
        url = prop.get('url', 'N/A')
        coincide = prop.get('coincide', 'N/A')
        
        print(f'  {i}. {titulo[:80]}...')
        print(f'     URL: {url[:80]}...')
        print(f'     Coincide: {coincide}')
        print()