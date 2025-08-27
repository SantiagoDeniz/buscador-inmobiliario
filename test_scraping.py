#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper import scrape_detalle_con_requests

def test_scraping_real():
    """Test del scraping con una URL real de MercadoLibre"""
    print("🧪 [TEST] Probando scraping de una propiedad real...")
    
    # URL de test (una propiedad de MercadoLibre)
    test_url = "https://apartamento.mercadolibre.com.uy/MLU-753430228-cordon-pre-venta-apartamento-1-dormitorio-amenities-_JM"
    
    try:
        print(f"🔍 [TEST] Scrapeando URL: {test_url}")
        datos = scrape_detalle_con_requests(test_url)
        
        if datos:
            print("✅ [TEST] Datos extraídos exitosamente:")
            for key, value in datos.items():
                if value:  # Solo mostrar campos que tienen valor
                    print(f"  {key}: {value}")
            
            # Verificar campos críticos
            campos_criticos = ['titulo', 'url_publicacion', 'precio_valor']
            for campo in campos_criticos:
                if campo in datos and datos[campo]:
                    print(f"✅ [TEST] Campo crítico '{campo}': OK")
                else:
                    print(f"❌ [TEST] Campo crítico '{campo}': FALTA")
            
            return True
        else:
            print("❌ [TEST] No se pudieron extraer datos de la URL")
            return False
            
    except Exception as e:
        print(f"❌ [TEST] Error durante el scraping: {e}")
        import traceback
        print(f"❌ [TEST] Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    print("🚀 [TEST] Iniciando prueba de scraping real...\n")
    
    scraping_ok = test_scraping_real()
    
    print(f"\n📊 [RESUMEN]")
    print(f"Scraping real: {'✅ OK' if scraping_ok else '❌ FALLO'}")
