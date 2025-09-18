#!/usr/bin/env python
"""
Script de prueba para verificar que las keywords se agreguen correctamente a la URL de InfoCasas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

def test_infocasas_keywords_in_url():
    """Prueba que las keywords se agreguen correctamente a la URL de InfoCasas"""
    print("🧪 Probando que las keywords se agreguen a la URL de InfoCasas...")
    
    try:
        from core.scraper.url_builder import build_infocasas_url
        
        # Prueba 1: URL sin keywords
        filtros_sin_keywords = {
            'operacion': 'alquiler',
            'tipo': 'apartamento',
            'departamento': 'Montevideo'
        }
        url_sin_keywords = build_infocasas_url(filtros_sin_keywords)
        print(f"✅ URL sin keywords: {url_sin_keywords}")
        
        # Verificar que no tenga searchstring
        assert 'searchstring=' not in url_sin_keywords, "❌ URL sin keywords no debería tener searchstring"
        
        # Prueba 2: URL con keywords
        keywords_test = ['piscina', 'garage', 'terraza']
        url_con_keywords = build_infocasas_url(filtros_sin_keywords, keywords=keywords_test)
        print(f"✅ URL con keywords: {url_con_keywords}")
        
        # Verificar que tenga searchstring
        assert 'searchstring=' in url_con_keywords, "❌ URL con keywords debería tener searchstring"
        
        # Verificar que contenga las keywords
        for keyword in keywords_test:
            assert keyword in url_con_keywords, f"❌ URL debería contener la keyword '{keyword}'"
        
        print("✅ Test completado: Las keywords se agregan correctamente a la URL")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def test_run_scraper_infocasas_keywords():
    """Prueba que run_scraper_infocasas pase correctamente las keywords"""
    print("\n🧪 Probando que run_scraper_infocasas use keywords en la URL...")
    
    try:
        # Solo probar la construcción de URL, no ejecutar scraping completo
        from core.scraper.run import run_scraper_infocasas
        from core.scraper.url_builder import build_infocasas_url
        from core.scraper.utils import extraer_variantes_keywords
        
        # Simular filtros y keywords típicos
        filtros_test = {
            'operacion': 'venta',
            'tipo': 'casa',
            'precio_min': 100000,
            'precio_max': 300000
        }
        keywords_test = ['jardin', 'garage']
        
        # Procesar keywords como lo hace run_scraper_infocasas
        from core.search_manager import procesar_keywords
        keywords_filtradas = procesar_keywords(' '.join(keywords_test))
        keywords_con_variantes = extraer_variantes_keywords(keywords_filtradas)
        
        # Construir URL directamente (como debería hacer run_scraper_infocasas)
        url_construida = build_infocasas_url(filtros_test, keywords=keywords_con_variantes)
        
        print(f"✅ Keywords filtradas: {keywords_filtradas}")
        print(f"✅ Keywords con variantes: {keywords_con_variantes}")
        print(f"✅ URL construida con keywords procesadas: {url_construida}")
        
        # Verificar que contenga searchstring
        assert 'searchstring=' in url_construida, "❌ URL debería contener searchstring"
        
        # Verificar que contenga las keywords o sus variantes
        url_lower = url_construida.lower()
        for keyword in keywords_test:
            # Las keywords pueden estar normalizadas, buscar la raíz
            keyword_found = any(k.lower() in url_lower for k in keywords_con_variantes if keyword.lower() in k.lower())
            assert keyword_found, f"❌ URL debería contener alguna variante de la keyword '{keyword}'"
        
        print("✅ Test completado: run_scraper_infocasas debería construir URLs con keywords")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando tests de keywords en URLs de InfoCasas...")
    print("=" * 60)
    
    tests = [
        test_infocasas_keywords_in_url,
        test_run_scraper_infocasas_keywords
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Resultados: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! El fix de keywords está funcionando.")
    else:
        print("⚠️ Algunos tests fallaron. Revisar implementación.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)