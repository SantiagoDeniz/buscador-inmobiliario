#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime
from unittest.mock import patch

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Propiedad

def test_guardado_completo():
    """Test que simula el flujo completo de guardado"""
    print("🧪 [TEST INTEGRADO] Simulando flujo completo de guardado...\n")
    
    # Datos de prueba que simulan lo que devolvería el scraper
    datos_test = {
        'url_publicacion': f'https://test-{datetime.now().timestamp()}.com/test',
        'titulo': f'Test Apartamento {datetime.now().strftime("%H:%M:%S")}',
        'precio_moneda': 'US$',
        'precio_valor': 153000,
        'url_imagen': 'https://test.com/image.jpg',
        'descripcion': 'Apartamento de prueba con amenities',
        'caracteristicas_texto': 'Superficie total: 49 m²\nDormitorios: 1\nBaños: 1',
        'tipo_inmueble': 'N/A',  # Esto debería ser corregido por la lógica
        'dormitorios_min': 1,
        'dormitorios_max': 1,
        'banos_min': 1,
        'banos_max': 1,
        'superficie_total_min': 49,
        'superficie_total_max': 49,
        'admite_mascotas': True,
        'tiene_piscina': True,
        'tiene_terraza': True,
    }
    
    # Simulamos los filtros que vienen del usuario
    filters = {
        'operacion': 'venta',
        'departamento': 'Montevideo',
        'tipo': 'apartamento'
    }
    
    print(f"📝 [TEST] Datos originales:")
    print(f"  - Título: {datos_test.get('titulo')}")
    print(f"  - Tipo inmueble: {datos_test.get('tipo_inmueble')}")
    print(f"  - Precio: {datos_test.get('precio_valor')} {datos_test.get('precio_moneda')}")
    
    try:
        # Simular la lógica del scraper para mejorar datos
        datos_test['operacion'] = filters.get('operacion', 'venta')
        datos_test['departamento'] = filters.get('departamento', filters.get('ciudad', 'N/A'))
        
        # Si el scraper no encontró un tipo de inmueble válido, usamos el de los filtros
        if not datos_test.get('tipo_inmueble') or datos_test.get('tipo_inmueble') == 'N/A':
           datos_test['tipo_inmueble'] = filters.get('tipo', 'apartamento')
        
        print(f"\n📝 [TEST] Datos corregidos:")
        print(f"  - Operación: {datos_test.get('operacion')}")
        print(f"  - Departamento: {datos_test.get('departamento')}")
        print(f"  - Tipo inmueble: {datos_test.get('tipo_inmueble')}")
        
        # Verificar campos críticos antes del guardado
        if not datos_test.get('titulo'):
            print(f"⚠️ [TEST] Advertencia: título vacío")
            datos_test['titulo'] = f"Propiedad en {datos_test.get('departamento', 'N/A')}"
        
        print(f"\n💾 [TEST] Intentando guardar en la base de datos...")
        
        # Crear la propiedad en la base de datos
        propiedad_creada = Propiedad.objects.create(**datos_test)
        print(f"✅ [TEST] Propiedad guardada exitosamente con ID: {propiedad_creada.id}")
        print(f"✅ [TEST] Título final: {propiedad_creada.titulo}")
        print(f"✅ [TEST] Tipo final: {propiedad_creada.tipo_inmueble}")
        
        # Verificar que se puede consultar
        propiedad_consultada = Propiedad.objects.get(id=propiedad_creada.id)
        print(f"✅ [TEST] Consulta exitosa: {propiedad_consultada.titulo}")
        
        # Limpiar
        propiedad_creada.delete()
        print(f"🗑️ [TEST] Propiedad de prueba eliminada")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Error en flujo completo: {e}")
        print(f"❌ [TEST] Tipo de error: {type(e).__name__}")
        import traceback
        print(f"❌ [TEST] Traceback: {traceback.format_exc()}")
        return False

def contar_propiedades():
    """Contar propiedades existentes en la base de datos"""
    try:
        total = Propiedad.objects.count()
        print(f"📊 [STATS] Total de propiedades en la base de datos: {total}")
        
        # Mostrar algunas estadísticas
        if total > 0:
            recientes = Propiedad.objects.order_by('-fecha_scrapeo')[:5]
            print(f"📊 [STATS] Últimas 5 propiedades:")
            for prop in recientes:
                print(f"  - {prop.titulo[:50]}... (ID: {prop.id})")
        
        return total
    except Exception as e:
        print(f"❌ [STATS] Error contando propiedades: {e}")
        return 0

if __name__ == '__main__':
    print("🚀 [TEST INTEGRADO] Iniciando pruebas completas de guardado...\n")
    
    # Mostrar estado inicial
    total_inicial = contar_propiedades()
    
    # Test principal
    test_ok = test_guardado_completo()
    
    # Mostrar estado final
    print(f"\n📊 [RESUMEN FINAL]")
    total_final = contar_propiedades()
    
    print(f"Test integrado: {'✅ OK' if test_ok else '❌ FALLO'}")
    print(f"Propiedades al inicio: {total_inicial}")
    print(f"Propiedades al final: {total_final}")
    
    if test_ok:
        print("🎉 [TEST] El guardado funciona correctamente en el flujo completo")
    else:
        print("⚠️ [TEST] Hay problemas en el flujo de guardado")
