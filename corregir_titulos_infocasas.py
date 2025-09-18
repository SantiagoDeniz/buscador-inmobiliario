#!/usr/bin/env python3
"""
Script para corregir títulos de propiedades InfoCasas existentes
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Propiedad
from core.scraper.run import extraer_titulo_de_url_infocasas
from core.search_manager import normalizar_texto

def corregir_titulos_infocasas():
    """Corregir títulos problemáticos de propiedades InfoCasas"""
    print("=== Corrección de Títulos InfoCasas ===")
    
    # Buscar propiedades InfoCasas con títulos problemáticos
    props_infocasas = Propiedad.objects.filter(url__icontains='infocasas.com')
    props_corregidas = 0
    
    for prop in props_infocasas:
        titulo_actual = prop.titulo or ''
        titulo_norm = normalizar_texto(titulo_actual)
        
        # Si contiene "publicacion", corregir
        if 'publicacion' in titulo_norm:
            print(f"\n🔧 Corrigiendo Propiedad ID {prop.id}")
            print(f"   URL: {prop.url}")
            print(f"   Título anterior: '{titulo_actual}'")
            
            # Extraer nuevo título de la URL
            nuevo_titulo = extraer_titulo_de_url_infocasas(prop.url)
            print(f"   Título nuevo: '{nuevo_titulo}'")
            
            # Actualizar propiedad
            prop.titulo = nuevo_titulo
            prop.save()
            props_corregidas += 1
            print(f"   ✅ Propiedad actualizada")
        else:
            print(f"\n✅ Propiedad ID {prop.id} ya tiene título válido: '{titulo_actual}'")
    
    print(f"\n=== Resumen ===")
    print(f"Propiedades InfoCasas encontradas: {props_infocasas.count()}")
    print(f"Propiedades corregidas: {props_corregidas}")
    
    # Verificación final
    props_restantes = Propiedad.objects.filter(
        url__icontains='infocasas.com',
        titulo__icontains='Publicación InfoCasas'
    )
    print(f"Propiedades con placeholder restantes: {props_restantes.count()}")
    
    return props_corregidas

if __name__ == "__main__":
    props_corregidas = corregir_titulos_infocasas()
    if props_corregidas > 0:
        print(f"\n🎉 ¡{props_corregidas} propiedades corregidas exitosamente!")
    else:
        print(f"\n✨ Todas las propiedades ya tenían títulos válidos")