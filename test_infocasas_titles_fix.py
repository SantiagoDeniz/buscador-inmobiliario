#!/usr/bin/env python3
"""
Test para verificar que los títulos de InfoCasas se extraen correctamente
después de la corrección del selector CSS.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper.extractors import recolectar_urls_de_pagina
import requests
from bs4 import BeautifulSoup

def test_infocasas_title_extraction():
    """Test para verificar la extracción de títulos de InfoCasas"""
    
    # URL de ejemplo de InfoCasas para apartamentos en alquiler
    test_url = "https://www.infocasas.com.uy/alquiler/apartamento"
    
    print(f"🔍 Probando extracción de títulos de InfoCasas desde: {test_url}")
    
    try:
        # Realizar petición
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"✅ Respuesta HTTP recibida: {response.status_code}")
        
        # Usar la función actualizada
        urls_encontradas, titulos_por_url = recolectar_urls_de_pagina(test_url, response.content)
        
        print(f"📊 Resultados de la prueba:")
        print(f"   - URLs encontradas: {len(urls_encontradas)}")
        print(f"   - Títulos extraídos: {len(titulos_por_url)}")
        
        # Mostrar algunos ejemplos de títulos extraídos
        print(f"\n📋 Primeros títulos extraídos:")
        for i, (url, titulo) in enumerate(list(titulos_por_url.items())[:5]):
            print(f"   {i+1}. {titulo}")
            print(f"      URL: {url[:60]}...")
        
        # Verificar si encontramos títulos válidos (no el fallback)
        titulos_validos = [t for t in titulos_por_url.values() if t and not t.startswith("Publicación InfoCasas")]
        
        if titulos_validos:
            print(f"\n✅ ¡ÉXITO! Se extrajeron {len(titulos_validos)} títulos válidos")
            return True
        else:
            print(f"\n❌ PROBLEMA: No se encontraron títulos válidos. Todos son fallbacks.")
            
            # Debug: mostrar estructura HTML para análisis
            soup = BeautifulSoup(response.content, 'html.parser')
            enlaces = soup.select('a[href*="/ficha/"]')[:3]
            
            print(f"\n🔧 Debug - Estructura HTML de los primeros enlaces:")
            for i, enlace in enumerate(enlaces):
                print(f"\nEnlace {i+1}:")
                print(f"HTML: {str(enlace)[:200]}...")
                
                # Probar diferentes selectores
                h2_lc_title = enlace.select_one('h2.lc-title')
                h2_any = enlace.select_one('h2')
                span_any = enlace.select_one('span')
                
                print(f"h2.lc-title: {h2_lc_title.get_text(strip=True) if h2_lc_title else 'No encontrado'}")
                print(f"h2 cualquiera: {h2_any.get_text(strip=True) if h2_any else 'No encontrado'}")
                print(f"span cualquiera: {span_any.get_text(strip=True) if span_any else 'No encontrado'}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test de extracción de títulos InfoCasas...")
    success = test_infocasas_title_extraction()
    
    if success:
        print(f"\n🎉 ¡La corrección funciona correctamente!")
        print(f"   Los títulos de InfoCasas ahora se extraen con el nombre real de las propiedades.")
    else:
        print(f"\n⚠️  Es necesario revisar y ajustar más el selector CSS.")
        
    print(f"\n✨ Test completado.")