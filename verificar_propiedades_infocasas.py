#!/usr/bin/env python3
"""
Verificar propiedades InfoCasas existentes en BD
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Propiedad
from core.search_manager import normalizar_texto

def verificar_propiedades_infocasas():
    """Verificar propiedades InfoCasas en la base de datos"""
    print("=== Verificación de Propiedades InfoCasas ===")
    
    # Buscar propiedades con "Publicación InfoCasas"
    props_placeholder = Propiedad.objects.filter(titulo__icontains='Publicación InfoCasas')
    print(f"\n1. Propiedades con 'Publicación InfoCasas': {props_placeholder.count()}")
    
    for prop in props_placeholder[:5]:
        print(f"   - ID {prop.id}: '{prop.titulo}' | {prop.url}")
    
    # Buscar todas las propiedades de InfoCasas (por URL)
    props_infocasas = Propiedad.objects.filter(url__icontains='infocasas.com')
    print(f"\n2. Total propiedades InfoCasas: {props_infocasas.count()}")
    
    # Analizar títulos problemáticos
    titles_problematicos = []
    for prop in props_infocasas:
        titulo_norm = normalizar_texto(prop.titulo or '')
        if 'publicacion' in titulo_norm:
            titles_problematicos.append(prop)
    
    print(f"\n3. Propiedades InfoCasas con título problemático: {len(titles_problematicos)}")
    for prop in titles_problematicos[:10]:
        print(f"   - ID {prop.id}: '{prop.titulo}' | {prop.url}")
    
    # Mostrar algunos títulos buenos de InfoCasas
    props_buenos = props_infocasas.exclude(id__in=[p.id for p in titles_problematicos])
    print(f"\n4. Propiedades InfoCasas con título válido: {props_buenos.count()}")
    for prop in props_buenos[:5]:
        print(f"   - ID {prop.id}: '{prop.titulo}' | {prop.url}")

if __name__ == "__main__":
    verificar_propiedades_infocasas()