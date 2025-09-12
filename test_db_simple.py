#!/usr/bin/env python
"""
Script para limpiar y poblar base de datos usando Django management command
"""

import os
import sys

# Configurar path y Django
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')

import django
django.setup()

# Ahora importar modelos
from core.models import Busqueda, PalabraClave, Propiedad

print("🚀 Iniciando script de limpieza y población...")

try:
    # Test basic connectivity
    print(f"📊 Búsquedas actuales: {Busqueda.objects.count()}")
    print(f"📊 Keywords actuales: {PalabraClave.objects.count()}")
    print(f"📊 Propiedades actuales: {Propiedad.objects.count()}")
    
    # Limpiar
    print("🧹 Limpiando datos...")
    Busqueda.objects.all().delete()
    PalabraClave.objects.all().delete() 
    Propiedad.objects.all().delete()
    print("   ✅ Datos limpiados")
    
    # Crear keyword de prueba
    print("🔤 Creando palabra clave de prueba...")
    keyword = PalabraClave.objects.create(
        texto='apartamento',
        sinonimos='["apto", "depto"]'
    )
    print(f"   ✅ Creada: {keyword.texto}")
    
    # Crear búsqueda de prueba
    print("🔍 Creando búsqueda de prueba...")
    busqueda = Busqueda.objects.create(
        nombre_busqueda='Test Apartamento',
        texto_original='apartamento alquiler',
        filtros={'tipo': 'apartamento'},
        guardado=True
    )
    print(f"   ✅ Creada: {busqueda.nombre_busqueda}")
    
    # Verificar
    print("\n📊 Resultados:")
    print(f"   🔤 Palabras clave: {PalabraClave.objects.count()}")
    print(f"   🔍 Búsquedas: {Busqueda.objects.count()}")
    
    print("✅ Script completado exitosamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
