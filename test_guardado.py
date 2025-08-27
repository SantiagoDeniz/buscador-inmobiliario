#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Propiedad

def test_guardado_propiedad():
    """Test simple para verificar el guardado de propiedades"""
    print("🧪 [TEST] Probando guardado de propiedad...")
    
    # Datos de prueba
    datos_test = {
        'titulo': f'Test Propiedad {datetime.now().strftime("%H:%M:%S")}',
        'url_publicacion': f'https://test.com/test-{datetime.now().timestamp()}',
        'portal': 'mercadolibre',
        'precio_moneda': 'USD',
        'precio_valor': 150000,
        'operacion': 'venta',
        'tipo_inmueble': 'apartamento',
        'departamento': 'Montevideo',
        'dormitorios_min': 2,
        'dormitorios_max': 2,
        'banos_min': 1,
        'banos_max': 1,
        'descripcion': 'Propiedad de prueba',
    }
    
    try:
        # Intentar crear la propiedad
        propiedad = Propiedad.objects.create(**datos_test)
        print(f"✅ [TEST] Propiedad guardada exitosamente con ID: {propiedad.id}")
        print(f"✅ [TEST] Título: {propiedad.titulo}")
        
        # Verificar que se puede consultar
        propiedades_test = Propiedad.objects.filter(titulo__contains='Test Propiedad')
        print(f"✅ [TEST] Total de propiedades de prueba encontradas: {propiedades_test.count()}")
        
        # Eliminar la propiedad de prueba
        propiedad.delete()
        print("🗑️ [TEST] Propiedad de prueba eliminada")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Error guardando propiedad: {e}")
        print(f"❌ [TEST] Tipo de error: {type(e).__name__}")
        import traceback
        print(f"❌ [TEST] Traceback: {traceback.format_exc()}")
        return False

def test_campos_modelo():
    """Test para verificar que los campos del modelo están correctos"""
    print("\n🧪 [TEST] Verificando campos del modelo Propiedad...")
    
    try:
        # Obtener todos los campos del modelo
        campos = [field.name for field in Propiedad._meta.get_fields()]
        print(f"✅ [TEST] Campos del modelo: {campos}")
        
        # Verificar campos críticos
        campos_criticos = ['titulo', 'url_publicacion', 'precio_valor', 'operacion', 'tipo_inmueble']
        for campo in campos_criticos:
            if campo in campos:
                print(f"✅ [TEST] Campo '{campo}' encontrado")
            else:
                print(f"❌ [TEST] Campo '{campo}' NO encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Error verificando campos: {e}")
        return False

if __name__ == '__main__':
    print("🚀 [TEST] Iniciando pruebas de guardado de propiedades...\n")
    
    # Test 1: Verificar campos del modelo
    campos_ok = test_campos_modelo()
    
    # Test 2: Probar guardado
    guardado_ok = test_guardado_propiedad()
    
    print(f"\n📊 [RESUMEN]")
    print(f"Campos del modelo: {'✅ OK' if campos_ok else '❌ FALLO'}")
    print(f"Guardado de propiedades: {'✅ OK' if guardado_ok else '❌ FALLO'}")
    
    if campos_ok and guardado_ok:
        print("🎉 [TEST] Todos los tests pasaron - El guardado funciona correctamente")
    else:
        print("⚠️ [TEST] Algunos tests fallaron - Revisar problemas")
