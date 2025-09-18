#!/usr/bin/env python3
"""
Test específico con selectores directos para InfoCasas
"""

import requests
from bs4 import BeautifulSoup

def test_direct_selectors():
    """Test directo de selectores con el HTML real"""
    
    test_url = "https://www.infocasas.com.uy/alquiler/apartamento"
    
    print(f"🔍 Test directo de selectores para: {test_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(test_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        print(f"✅ Respuesta HTTP: {response.status_code}")
        
        # Test 1: El selector actual del código
        print(f"\n1️⃣ Test selector actual: 'div.lc-dataWrapper'")
        contenedores_lc = soup.select('div.lc-dataWrapper')
        print(f"   Encontrados: {len(contenedores_lc)}")
        
        if contenedores_lc:
            for i, cont in enumerate(contenedores_lc[:3]):
                print(f"\n   Contenedor {i+1}:")
                # Buscar enlace lc-data
                enlace = cont.select_one('a.lc-data')
                if enlace:
                    href = enlace.get('href')
                    print(f"     - Enlace: {href}")
                    
                    # Buscar título
                    titulo_elem = enlace.select_one('h2.lc-title')
                    if titulo_elem:
                        titulo = titulo_elem.get_text(strip=True)
                        print(f"     - Título: {titulo}")
                    else:
                        print(f"     - Título: NO ENCONTRADO con h2.lc-title")
                        # Probar alternativas
                        h2_any = enlace.select_one('h2')
                        if h2_any:
                            print(f"     - Título alternativo (h2): {h2_any.get_text(strip=True)}")
                else:
                    print(f"     - Enlace: NO ENCONTRADO con a.lc-data")
        
        # Test 2: Selector directo de títulos
        print(f"\n2️⃣ Test selector directo: 'h2.lc-title'")
        titulos_directos = soup.select('h2.lc-title')
        print(f"   Encontrados: {len(titulos_directos)}")
        
        if titulos_directos:
            print(f"   Primeros 3 títulos:")
            for i, titulo in enumerate(titulos_directos[:3]):
                print(f"     {i+1}. {titulo.get_text(strip=True)}")
        
        # Test 3: Buscar enlaces que contengan títulos
        print(f"\n3️⃣ Test enlace + título combinado")
        enlaces_con_titulo = soup.select('a.lc-data h2.lc-title')
        print(f"   Enlaces con título: {len(enlaces_con_titulo)}")
        
        if enlaces_con_titulo:
            print(f"   Primeros 3 títulos de enlaces:")
            for i, titulo in enumerate(enlaces_con_titulo[:3]):
                print(f"     {i+1}. {titulo.get_text(strip=True)}")
                # Obtener el enlace padre
                enlace_padre = titulo.find_parent('a')
                if enlace_padre:
                    href = enlace_padre.get('href')
                    print(f"         URL: {href}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test directo de selectores InfoCasas...")
    test_direct_selectors()
    print(f"\n✨ Test completado.")