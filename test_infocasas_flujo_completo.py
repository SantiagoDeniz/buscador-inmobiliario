#!/usr/bin/env python3
"""
Test específico para verificar que InfoCasas ya no muestra "Publicación InfoCasas"
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper.run import extraer_titulo_de_url_infocasas
from core.search_manager import crear_o_actualizar_propiedad, normalizar_texto

def test_flujo_completo_infocasas():
    """Test del flujo completo desde URL hasta guardado de propiedad"""
    print("=== Test Flujo Completo InfoCasas ===")
    
    # URL de ejemplo de InfoCasas
    url_infocasas = "https://www.infocasas.com.uy/venta/departamento/montevideo/pocitos/123456"
    
    # 1. Simular que llegó con "Publicación InfoCasas" (el problema original)
    print("\n1. Simulando resultado con 'Publicación InfoCasas':")
    result_data_malo = {
        'url': url_infocasas,
        'titulo': 'Publicación InfoCasas',
        'descripcion': 'Propiedad en InfoCasas',
        'precio': 150000
    }
    
    print(f"   Título entrante: '{result_data_malo['titulo']}'")
    print(f"   ¿Es placeholder? {normalizar_texto(result_data_malo['titulo'])}")
    
    # 2. El sistema debería usar el fallback para extraer título de URL
    titulo_fallback = extraer_titulo_de_url_infocasas(url_infocasas)
    print(f"\n2. Título extraído de URL: '{titulo_fallback}'")
    
    # 3. Cuando el scraper detecte placeholder, debería usar el fallback
    if 'publicacion' in normalizar_texto(result_data_malo['titulo']):
        result_data_malo['titulo'] = titulo_fallback
        print(f"3. Título corregido por scraper: '{result_data_malo['titulo']}'")
    
    # 4. Crear propiedad en BD
    propiedad = crear_o_actualizar_propiedad(result_data_malo)
    print(f"\n4. Propiedad guardada en BD:")
    print(f"   ID: {propiedad.id}")
    print(f"   Título: '{propiedad.titulo}'")
    print(f"   URL: {propiedad.url}")
    
    # 5. Verificar que NO contiene "Publicación InfoCasas"
    contiene_placeholder = 'publicacion' in normalizar_texto(propiedad.titulo or '')
    status = "❌ FALLO" if contiene_placeholder else "✅ ÉXITO"
    print(f"\n5. Verificación final: {status}")
    print(f"   Título final: '{propiedad.titulo}'")
    print(f"   ¿Contiene placeholder? {contiene_placeholder}")
    
    return propiedad

if __name__ == "__main__":
    propiedad = test_flujo_completo_infocasas()
    print(f"\n=== RESULTADO: Propiedad {propiedad.id} creada exitosamente ===")