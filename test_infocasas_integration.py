#!/usr/bin/env python
"""
Script de prueba para la integración InfoCasas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

def test_infocasas_url_builder():
    """Prueba el constructor de URLs de InfoCasas"""
    print("🧪 Probando constructor de URLs de InfoCasas...")
    
    try:
        from core.scraper.url_builder import build_infocasas_url
        
        # Prueba básica
        url1 = build_infocasas_url({'operacion': 'alquiler', 'tipo': 'apartamento'})
        print(f"✅ URL básica: {url1}")
        
        # Prueba con filtros complejos
        filtros_complejos = {
            'operacion': 'alquiler',
            'tipo': 'apartamento',
            'departamento': 'Montevideo',
            'precio_min': 500,
            'precio_max': 1000,
            'dormitorios_min': 2,
            'dormitorios_max': 3,
            'amoblado': True
        }
        url2 = build_infocasas_url(filtros_complejos)
        print(f"✅ URL compleja: {url2}")
        
        # Prueba con keywords
        url3 = build_infocasas_url({'operacion': 'venta'}, keywords=['garage', 'jardín'])
        print(f"✅ URL con keywords: {url3}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test URL builder: {e}")
        return False

def test_infocasas_scraping():
    """Prueba básica del scraping de InfoCasas"""
    print("🧪 Probando scraping básico de InfoCasas...")
    
    try:
        from core.scraper.infocasas import extraer_total_resultados_infocasas
        from core.scraper.url_builder import build_infocasas_url
        
        # URL de prueba simple
        url = build_infocasas_url({'operacion': 'alquiler', 'tipo': 'apartamento'})
        print(f"🔍 Probando URL: {url}")
        
        # Intentar extraer total (solo prueba de conectividad)
        total = extraer_total_resultados_infocasas(url)
        print(f"✅ Total encontrado: {total}")
        
        return total is not None
        
    except Exception as e:
        print(f"❌ Error en test scraping: {e}")
        return False

def test_multi_platform_orchestrator():
    """Prueba el orquestador multi-plataforma"""
    print("🧪 Probando orquestador multi-plataforma...")
    
    try:
        from core.scraper import run_scraper
        
        # Prueba con MercadoLibre
        print("🔍 Probando run_scraper con MercadoLibre...")
        result_ml = run_scraper(
            filters={'operacion': 'alquiler', 'tipo': 'apartamento'}, 
            keywords=[],
            max_paginas=1,
            workers_fase1=1,
            workers_fase2=1,
            plataforma='mercadolibre'
        )
        print(f"✅ MercadoLibre: {len(result_ml) if result_ml else 0} resultados")
        
        # Prueba con InfoCasas
        print("🔍 Probando run_scraper con InfoCasas...")
        result_ic = run_scraper(
            filters={'operacion': 'alquiler', 'tipo': 'apartamento'}, 
            keywords=[],
            max_paginas=1,
            workers_fase1=1,
            workers_fase2=1,
            plataforma='infocasas'
        )
        print(f"✅ InfoCasas: {len(result_ic) if result_ic else 0} resultados")
        
        # Prueba con todas las plataformas
        print("🔍 Probando run_scraper con todas las plataformas...")
        result_all = run_scraper(
            filters={'operacion': 'alquiler', 'tipo': 'apartamento'}, 
            keywords=[],
            max_paginas=1,
            workers_fase1=1,
            workers_fase2=1,
            plataforma='todas'
        )
        print(f"✅ Todas: {len(result_all) if result_all else 0} resultados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test orquestador: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas de integración InfoCasas")
    print("=" * 50)
    
    tests = [
        ("URL Builder", test_infocasas_url_builder),
        ("Scraping Básico", test_infocasas_scraping), 
        ("Orquestador Multi-plataforma", test_multi_platform_orchestrator),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🧪 Test: {name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((name, result))
            print(f"{'✅ PASÓ' if result else '❌ FALLÓ'}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((name, False))
        print("-" * 30)
    
    print(f"\n📊 Resumen de Pruebas:")
    print("=" * 50)
    passed = 0
    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ" 
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎉 ¡Todas las pruebas pasaron! InfoCasas está listo.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar implementación.")

if __name__ == "__main__":
    main()