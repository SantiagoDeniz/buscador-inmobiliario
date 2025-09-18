#!/usr/bin/env python3
"""
Script para debuggear los títulos de InfoCasas
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper.extractors import recolectar_urls_infocasas_de_pagina
from core.scraper.url_builder import build_infocasas_url

def test_infocasas_titles():
    """Test para verificar la extracción de títulos de InfoCasas"""
    print("🧪 Testeando extracción de títulos de InfoCasas...")
    
    # Crear una URL de prueba simple
    filtros_test = {
        'operacion': 'alquiler',
        'tipo': 'apartamento',
        'departamento': 'Montevideo'
    }
    
    url_test = build_infocasas_url(filtros_test)
    print(f"🔗 URL de prueba: {url_test}")
    
    # Extraer URLs y títulos
    urls_de_pagina, titulos_por_url = recolectar_urls_infocasas_de_pagina(url_test)
    
    print(f"📊 Resultados:")
    print(f"   URLs encontradas: {len(urls_de_pagina)}")
    print(f"   Títulos extraídos: {len(titulos_por_url)}")
    
    # Mostrar algunos ejemplos
    print(f"\n📋 Primeros 5 títulos encontrados:")
    for i, (url, titulo) in enumerate(list(titulos_por_url.items())[:5], 1):
        print(f"   {i}. URL: {url}")
        print(f"      Título: '{titulo}'")
        print()
    
    # Verificar si hay URLs sin título
    urls_sin_titulo = [url for url in urls_de_pagina if url not in titulos_por_url]
    print(f"❌ URLs sin título: {len(urls_sin_titulo)}")
    
    if urls_sin_titulo:
        print("   Ejemplos de URLs sin título:")
        for url in urls_sin_titulo[:3]:
            print(f"   - {url}")
    
    return len(urls_de_pagina), len(titulos_por_url)

if __name__ == "__main__":
    try:
        total_urls, total_titulos = test_infocasas_titles()
        
        if total_titulos == 0:
            print("❌ PROBLEMA: No se extrajo ningún título!")
        elif total_urls > total_titulos:
            print(f"⚠️ ADVERTENCIA: Se extrajeron {total_urls} URLs pero solo {total_titulos} títulos")
        else:
            print("✅ Extracción de títulos funcionando correctamente")
            
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()