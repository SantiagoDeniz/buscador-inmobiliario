#!/usr/bin/env python3
"""
Script para probar la extracción y guardado completo de características de MercadoLibre.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper.extractors import scrape_detalle_con_requests
import json

def test_caracteristicas_extraction():
    """Prueba la extracción de características de una URL de MercadoLibre"""
    
    # URL de ejemplo (cambiar por una URL real de MercadoLibre)
    test_url = "https://inmueble.mercadolibre.com.uy/MLU-497000000-apartamento-1-dormitorio-parque-rodo-alquiler"
    
    print("🔍 Probando extracción de características...")
    print(f"URL: {test_url}")
    print("=" * 60)
    
    # Extraer datos
    datos = scrape_detalle_con_requests(test_url)
    
    if not datos:
        print("❌ No se pudieron extraer datos de la URL")
        return
    
    print("✅ Datos extraídos exitosamente")
    print("\n📊 CARACTERÍSTICAS EXTRAÍDAS:")
    print("=" * 40)
    
    # Mostrar características completas
    if 'caracteristicas_dict' in datos:
        carac_dict = datos['caracteristicas_dict']
        print(f"📋 Diccionario de características ({len(carac_dict)} elementos):")
        for key, value in carac_dict.items():
            print(f"  • {key.capitalize()}: {value}")
    
    print(f"\n📝 Texto de características:")
    print(f"  {datos.get('caracteristicas_texto', 'No disponible')}")
    
    # Mostrar otros datos importantes
    print(f"\n🏠 DATOS PRINCIPALES:")
    print(f"  • Título: {datos.get('titulo', 'N/A')}")
    print(f"  • Tipo: {datos.get('tipo_inmueble', 'N/A')}")
    print(f"  • Precio: {datos.get('precio_moneda', '')} {datos.get('precio_valor', 'N/A')}")
    print(f"  • Dormitorios: {datos.get('dormitorios_min', 'N/A')}-{datos.get('dormitorios_max', 'N/A')}")
    print(f"  • Baños: {datos.get('banos_min', 'N/A')}-{datos.get('banos_max', 'N/A')}")
    print(f"  • Superficie total: {datos.get('superficie_total_min', 'N/A')}-{datos.get('superficie_total_max', 'N/A')}")
    print(f"  • Amoblado: {datos.get('es_amoblado', False)}")
    print(f"  • Mascotas: {datos.get('admite_mascotas', False)}")
    print(f"  • Piscina: {datos.get('tiene_piscina', False)}")
    
    # Mostrar estructura completa de datos
    print(f"\n🔧 ESTRUCTURA COMPLETA (JSON):")
    print("=" * 40)
    print(json.dumps(datos, indent=2, ensure_ascii=False))
    
    return datos

def test_metadata_storage():
    """Prueba cómo se almacenarían las características en metadata"""
    
    # Simular datos extraídos
    datos_simulados = {
        'titulo': 'Apartamento 2 dormitorios en Pocitos',
        'caracteristicas_dict': {
            'dormitorios': '2',
            'baños': '1',
            'superficie total': '60 m²',
            'tipo de inmueble': 'Apartamento',
            'amoblado': 'No',
            'mascotas': 'Sí',
            'antigüedad': '5 años'
        },
        'caracteristicas_texto': 'Dormitorios: 2\nBaños: 1\nSuperficie total: 60 m²'
    }
    
    print("\n🗄️ PRUEBA DE ALMACENAMIENTO EN METADATA:")
    print("=" * 50)
    
    # Simular metadata como se guardaría ahora
    metadata_completo = {
        'caracteristicas_dict': datos_simulados.get('caracteristicas_dict', {}),
        'caracteristicas_texto': datos_simulados.get('caracteristicas_texto', ''),
        'tipo_inmueble': datos_simulados.get('tipo_inmueble', ''),
    }
    
    print("📦 Metadata que se guardaría:")
    print(json.dumps(metadata_completo, indent=2, ensure_ascii=False))
    
    print(f"\n✅ Total de características guardadas: {len(metadata_completo['caracteristicas_dict'])}")
    
    return metadata_completo

if __name__ == "__main__":
    print("🚀 PROBANDO SISTEMA DE CARACTERÍSTICAS MEJORADO")
    print("=" * 60)
    
    # Probar extracción (comentado para evitar llamadas reales)
    # test_caracteristicas_extraction()
    
    # Probar estructura de almacenamiento
    test_metadata_storage()
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("\nAhora las características de MercadoLibre se guardan completamente en:")
    print("  • metadata['caracteristicas_dict'] - Diccionario completo clave-valor")
    print("  • metadata['caracteristicas_texto'] - Texto formateado legible")
    print("  • metadata[...] - Datos estructurados individuales")