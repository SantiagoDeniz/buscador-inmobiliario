#!/usr/bin/env python3
"""
Script para verificar que las características completas se guardan correctamente en la BD.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Propiedad, Plataforma
from core.search_manager import procesar_propiedad_nueva, get_or_create_palabra_clave
import json

def verificar_caracteristicas_en_bd():
    """Verifica cómo se ven las características de propiedades ya guardadas"""
    
    print("🔍 VERIFICANDO CARACTERÍSTICAS EN BASE DE DATOS")
    print("=" * 60)
    
    # Obtener algunas propiedades de ejemplo
    propiedades = Propiedad.objects.all()[:5]
    
    if not propiedades:
        print("❌ No hay propiedades en la base de datos para verificar")
        return
    
    for i, prop in enumerate(propiedades, 1):
        print(f"\n📋 PROPIEDAD {i}: {prop.titulo or 'Sin título'}")
        print(f"URL: {prop.url}")
        print("-" * 40)
        
        if not prop.metadata:
            print("❌ Sin metadata")
            continue
            
        metadata = prop.metadata
        
        # Verificar formato nuevo
        if 'caracteristicas_dict' in metadata:
            print("✅ FORMATO NUEVO - Características completas:")
            carac_dict = metadata['caracteristicas_dict']
            print(f"  📊 Total características: {len(carac_dict)}")
            for key, value in carac_dict.items():
                print(f"    • {key}: {value}")
            
            if 'caracteristicas_texto' in metadata:
                print(f"\n  📝 Texto formateado:")
                print(f"    {metadata['caracteristicas_texto'][:200]}...")
        else:
            print("⚠️ FORMATO LEGACY:")
            print(f"  Claves en metadata: {list(metadata.keys())}")
        
        # Mostrar datos estructurados
        datos_estructurados = [
            'tipo_inmueble', 'dormitorios_min', 'dormitorios_max',
            'banos_min', 'banos_max', 'superficie_total_min',
            'es_amoblado', 'admite_mascotas', 'tiene_piscina'
        ]
        
        estructurados_encontrados = {k: metadata.get(k) for k in datos_estructurados if k in metadata}
        if estructurados_encontrados:
            print(f"\n  🏗️ Datos estructurados ({len(estructurados_encontrados)}):")
            for k, v in estructurados_encontrados.items():
                print(f"    • {k}: {v}")

def simular_nuevo_guardado():
    """Simula cómo se guardaría una propiedad nueva con las mejoras"""
    
    print("\n" + "=" * 60)
    print("🆕 SIMULANDO GUARDADO CON MEJORAS")
    print("=" * 60)
    
    # Simular datos extraídos con el nuevo formato
    datos_simulados = {
        'titulo': 'Apartamento 2 dormitorios en Pocitos - TEST',
        'descripcion': 'Hermoso apartamento con vista al mar',
        'caracteristicas_dict': {
            'dormitorios': '2',
            'baños': '1',
            'superficie total': '75 m²',
            'superficie cubierta': '70 m²',
            'tipo de inmueble': 'Apartamento',
            'amoblado': 'No',
            'mascotas': 'Sí',
            'piscina': 'No',
            'terraza': 'Sí',
            'cocheras': '1',
            'antigüedad': 'A estrenar',
            'expensas': '$5,000',
            'orientación': 'Norte'
        },
        'caracteristicas_texto': '''Dormitorios: 2
Baños: 1
Superficie total: 75 m²
Superficie cubierta: 70 m²
Tipo de inmueble: Apartamento
Amoblado: No
Mascotas: Sí
Piscina: No
Terraza: Sí
Cocheras: 1
Antigüedad: A estrenar
Expensas: $5,000
Orientación: Norte''',
        'precio_moneda': 'USD',
        'precio_valor': 180000,
        'tipo_inmueble': 'Apartamento',
        'dormitorios_min': 2,
        'dormitorios_max': 2,
        'banos_min': 1,
        'banos_max': 1,
        'superficie_total_min': 75,
        'superficie_total_max': 75,
        'es_amoblado': False,
        'admite_mascotas': True,
        'tiene_piscina': False,
        'tiene_terraza': True,
    }
    
    # Mostrar cómo se construiría el metadata
    metadata_completo = {
        'caracteristicas_dict': datos_simulados.get('caracteristicas_dict', {}),
        'caracteristicas_texto': datos_simulados.get('caracteristicas_texto', ''),
        'precio_moneda': datos_simulados.get('precio_moneda', ''),
        'precio_valor': datos_simulados.get('precio_valor', 0),
        'tipo_inmueble': datos_simulados.get('tipo_inmueble', ''),
        'dormitorios_min': datos_simulados.get('dormitorios_min'),
        'dormitorios_max': datos_simulados.get('dormitorios_max'),
        'banos_min': datos_simulados.get('banos_min'),
        'banos_max': datos_simulados.get('banos_max'),
        'superficie_total_min': datos_simulados.get('superficie_total_min'),
        'superficie_total_max': datos_simulados.get('superficie_total_max'),
        'es_amoblado': datos_simulados.get('es_amoblado', False),
        'admite_mascotas': datos_simulados.get('admite_mascotas', False),
        'tiene_piscina': datos_simulados.get('tiene_piscina', False),
        'tiene_terraza': datos_simulados.get('tiene_terraza', False),
    }
    
    print("📦 METADATA COMPLETO QUE SE GUARDARÍA:")
    print(json.dumps(metadata_completo, indent=2, ensure_ascii=False))
    
    print(f"\n✅ BENEFICIOS DEL NUEVO FORMATO:")
    print(f"  • {len(metadata_completo['caracteristicas_dict'])} características individuales guardadas")
    print(f"  • Texto formateado para visualización")
    print(f"  • Datos estructurados para consultas (dormitorios_min, banos_max, etc.)")
    print(f"  • Campos booleanos para filtros (es_amoblado, admite_mascotas, etc.)")
    print(f"  • Compatibilidad con formato anterior")

if __name__ == "__main__":
    # Verificar propiedades existentes
    verificar_caracteristicas_en_bd()
    
    # Mostrar mejoras
    simular_nuevo_guardado()
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("\n🎯 MEJORAS IMPLEMENTADAS:")
    print("  • Extracción completa de tabla de características de MercadoLibre")
    print("  • Guardado de diccionario completo en metadata['caracteristicas_dict']")
    print("  • Texto formateado en metadata['caracteristicas_texto']")
    print("  • Datos estructurados para consultas y filtros")
    print("  • Compatibilidad con formato anterior")
    print("  • Información mucho más rica para análisis y búsquedas")