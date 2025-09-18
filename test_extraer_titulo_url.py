#!/usr/bin/env python3
"""
Test para la función extraer_titulo_de_url_infocasas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper.run import extraer_titulo_de_url_infocasas

def test_extraer_titulo():
    """Test de la función extraer_titulo_de_url_infocasas"""
    
    print("🧪 Test de extraer_titulo_de_url_infocasas")
    
    # URLs de prueba
    test_urls = [
        "/alquiler-apartamento-2-dormitorios-puerto-buceo-garage/192693037",
        "/lindo-apartamento-de-2-dormitorios-en-pocitos/192868335", 
        "/alquiler-pocitos-apartamento-2-dormitorios-todo-al-frente/192800282",
        "/alquiler-amueblado-1-dormitorio-piso-4-more-buceo/192584270",
        "https://www.infocasas.com.uy/juncal-1-dorm/192524823",
        "/excelente-planta/192788565",
        "",
        None
    ]
    
    expected_results = [
        "Alquiler apartamento 2 dormitorios puerto buceo garage",
        "Lindo apartamento de 2 dormitorios en pocitos",
        "Alquiler pocitos apartamento 2 dormitorios todo al frente", 
        "Alquiler amueblado 1 dormitorio piso 4 more buceo",
        "Juncal 1 dorm",
        "Excelente planta",
        "Propiedad InfoCasas",  # fallback para cadena vacía
        "Propiedad InfoCasas"   # fallback para None
    ]
    
    print(f"\n📋 Ejecutando {len(test_urls)} tests...")
    
    todos_ok = True
    for i, (url, expected) in enumerate(zip(test_urls, expected_results)):
        resultado = extraer_titulo_de_url_infocasas(url)
        es_correcto = resultado == expected
        
        if es_correcto:
            status = "✅"
        else:
            status = "❌"
            todos_ok = False
        
        print(f"{status} Test {i+1}: {url}")
        print(f"    Esperado: '{expected}'")
        print(f"    Obtenido: '{resultado}'")
        if not es_correcto:
            print(f"    ⚠️  DIFERENCIA DETECTADA")
        print()
    
    if todos_ok:
        print("🎉 ¡Todos los tests pasaron correctamente!")
        return True
    else:
        print("❌ Algunos tests fallaron. Revisar la función.")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test de extracción de títulos desde URL...")
    success = test_extraer_titulo()
    print(f"\n✨ Test completado.")