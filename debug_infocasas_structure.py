#!/usr/bin/env python3
"""
Test directo para ver la estructura HTML de InfoCasas y depurar selectores
"""

import requests
from bs4 import BeautifulSoup

def debug_infocasas_structure():
    """Debug directo de la estructura HTML de InfoCasas"""
    
    test_url = "https://www.infocasas.com.uy/alquiler/apartamento"
    
    print(f"🔍 Analizando estructura HTML de: {test_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(test_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"✅ Respuesta HTTP: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Buscar diferentes patrones de contenedores
        print(f"\n🔍 Buscando diferentes selectores...")
        
        # 1. Selector actual del código
        contenedores_lc = soup.select('div.lc-dataWrapper')
        print(f"1. div.lc-dataWrapper: {len(contenedores_lc)} encontrados")
        
        # 2. Buscar enlaces directos de ficha
        enlaces_ficha = soup.select('a[href*="/ficha/"]')
        print(f"2. a[href*=\"/ficha/\"]: {len(enlaces_ficha)} encontrados")
        
        # 3. Buscar h2 con clase lc-title
        titulos_lc = soup.select('h2.lc-title')
        print(f"3. h2.lc-title: {len(titulos_lc)} encontrados")
        
        # 4. Buscar todos los h2
        todos_h2 = soup.select('h2')
        print(f"4. h2 (todos): {len(todos_h2)} encontrados")
        
        # Mostrar ejemplos de cada tipo encontrado
        if titulos_lc:
            print(f"\n📋 Ejemplos de h2.lc-title encontrados:")
            for i, titulo in enumerate(titulos_lc[:3]):
                print(f"   {i+1}. {titulo.get_text(strip=True)}")
                print(f"      HTML: {str(titulo)[:100]}...")
        
        if enlaces_ficha:
            print(f"\n📋 Ejemplos de enlaces /ficha/ encontrados:")
            for i, enlace in enumerate(enlaces_ficha[:3]):
                print(f"   {i+1}. href: {enlace.get('href')}")
                # Buscar título dentro del enlace
                titulo_en_enlace = enlace.select_one('h2.lc-title')
                if titulo_en_enlace:
                    print(f"      título: {titulo_en_enlace.get_text(strip=True)}")
                else:
                    print(f"      título: No encontrado con h2.lc-title")
                print(f"      HTML: {str(enlace)[:150]}...")
        
        # Buscar estructura general
        print(f"\n🔍 Estructura general de la página:")
        contenido_principal = soup.select('main, #content, .content, [class*=\"listing\"], [class*=\"result\"]')
        print(f"   Contenedores principales: {len(contenido_principal)}")
        for i, cont in enumerate(contenido_principal[:3]):
            print(f"   {i+1}. {cont.name} - clases: {cont.get('class', [])}")
        
        # Guardar HTML para análisis manual si es necesario
        with open('debug_infocasas_html.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n💾 HTML completo guardado en: debug_infocasas_html.html")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando análisis de estructura HTML de InfoCasas...")
    debug_infocasas_structure()
    print(f"\n✨ Análisis completado.")