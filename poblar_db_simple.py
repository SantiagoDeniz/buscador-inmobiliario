#!/usr/bin/env python
"""
Script simplificado para limpiar y poblar la base de datos
"""

import os
import sys
import json
from datetime import datetime, timedelta
import django
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import (
    Busqueda, Propiedad, PalabraClave, ResultadoBusqueda, 
    PalabraClavePropiedad, Plataforma, Inmobiliaria, Usuario
)
from django.db import transaction


def main():
    print("🚀 Iniciando limpieza y población de la base de datos...")
    
    try:
        # Limpiar datos principales
        print("🧹 Limpiando datos existentes...")
        PalabraClavePropiedad.objects.all().delete()
        ResultadoBusqueda.objects.all().delete() 
        Propiedad.objects.all().delete()
        Busqueda.objects.all().delete()
        PalabraClave.objects.all().delete()
        print("   ✅ Datos limpiados")
        
        # Crear palabras clave
        print("🔤 Creando palabras clave...")
        keywords_data = [
            {'texto': 'apartamento', 'sinonimos': '["apto", "departamento", "depto", "piso"]'},
            {'texto': 'casa', 'sinonimos': '["vivienda", "hogar", "residencia", "chalet"]'},
            {'texto': 'garage', 'sinonimos': '["garaje", "cochera", "estacionamiento"]'},
            {'texto': 'piscina', 'sinonimos': '["pileta", "alberca", "natatorio"]'},
            {'texto': 'terraza', 'sinonimos': '["balcon", "balcón", "azotea"]'},
        ]
        
        for data in keywords_data:
            PalabraClave.objects.create(**data)
            print(f"   ✅ Creada: {data['texto']}")
        
        # Crear búsquedas
        print("🔍 Creando búsquedas de ejemplo...")
        busquedas_data = [
            {
                'nombre_busqueda': 'Apartamento Pocitos - Alquiler USD',
                'texto_original': 'apartamento pocitos alquiler garage terraza',
                'filtros': {
                    'tipo': 'apartamento',
                    'operacion': 'alquiler', 
                    'departamento': 'Montevideo',
                    'ciudad': 'Pocitos',
                    'moneda': 'USD',
                    'precio_min': 800,
                    'precio_max': 1500
                },
                'guardado': True
            },
            {
                'nombre_busqueda': 'Casa Carrasco - Venta',
                'texto_original': 'casa carrasco venta piscina jardin',
                'filtros': {
                    'tipo': 'casa',
                    'operacion': 'venta',
                    'departamento': 'Montevideo', 
                    'ciudad': 'Carrasco',
                    'moneda': 'USD',
                    'precio_min': 150000,
                    'precio_max': 300000
                },
                'guardado': True
            },
            {
                'nombre_busqueda': 'Apartamento Centro - Alquiler Pesos',
                'texto_original': 'apartamento centro alquiler amueblado',
                'filtros': {
                    'tipo': 'apartamento',
                    'operacion': 'alquiler',
                    'departamento': 'Montevideo',
                    'ciudad': 'Centro', 
                    'moneda': 'UYU',
                    'precio_min': 25000,
                    'precio_max': 45000
                },
                'guardado': True
            },
            {
                'nombre_busqueda': 'Casa Punta del Este - Venta',
                'texto_original': 'casa punta del este venta vista mar',
                'filtros': {
                    'tipo': 'casa',
                    'operacion': 'venta',
                    'departamento': 'Maldonado',
                    'ciudad': 'Punta del Este',
                    'moneda': 'USD',
                    'precio_min': 200000,
                    'precio_max': 500000
                },
                'guardado': True
            },
            {
                'nombre_busqueda': 'Búsqueda Temporal',
                'texto_original': 'apartamento alquiler economico',
                'filtros': {
                    'tipo': 'apartamento',
                    'operacion': 'alquiler',
                    'moneda': 'USD',
                    'precio_max': 1000
                },
                'guardado': False
            }
        ]
        
        for data in busquedas_data:
            busqueda = Busqueda.objects.create(**data)
            estado = "💾 Guardada" if data['guardado'] else "📝 Temporal"
            print(f"   ✅ {estado}: {data['nombre_busqueda']}")
        
        # Crear propiedades
        print("🏠 Creando propiedades de ejemplo...")
        propiedades_data = [
            {
                'titulo': 'Apartamento en Pocitos con Vista al Mar',
                'descripcion': 'Hermoso apartamento de 2 dormitorios en Pocitos con vista al mar, garage y terraza.',
                'precio': 1200.00,
                'moneda': 'USD',
                'ubicacion': 'Pocitos, Montevideo',
                'dormitorios': 2,
                'banos': 2,
                'metros_cuadrados': 85.0,
                'url_detalle': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo1'
            },
            {
                'titulo': 'Casa en Carrasco con Piscina',
                'descripcion': 'Casa familiar en Carrasco con 4 dormitorios, piscina y amplio jardín.',
                'precio': 280000.00,
                'moneda': 'USD',
                'ubicacion': 'Carrasco, Montevideo',
                'dormitorios': 4,
                'banos': 3,
                'metros_cuadrados': 250.0,
                'url_detalle': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo2'
            },
            {
                'titulo': 'Apartamento Amueblado en Centro',
                'descripcion': 'Apartamento completamente amueblado en el centro, ideal para profesionales.',
                'precio': 35000.00,
                'moneda': 'UYU',
                'ubicacion': 'Centro, Montevideo',
                'dormitorios': 1,
                'banos': 1,
                'metros_cuadrados': 45.0,
                'url_detalle': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo3'
            }
        ]
        
        for data in propiedades_data:
            propiedad = Propiedad.objects.create(**data)
            print(f"   ✅ {data['titulo']}")
            print(f"      📍 {data['ubicacion']} - {data['dormitorios']} dorm")
            print(f"      💰 {data['moneda']} {data['precio']:,.0f}")
        
        # Mostrar estadísticas
        print("\n📊 Estadísticas finales:")
        print(f"   🔤 Palabras clave: {PalabraClave.objects.count()}")
        print(f"   🔍 Búsquedas guardadas: {Busqueda.objects.filter(guardado=True).count()}")
        print(f"   📝 Búsquedas temporales: {Busqueda.objects.filter(guardado=False).count()}")
        print(f"   🏠 Propiedades: {Propiedad.objects.count()}")
        
        print("\n✅ ¡Base de datos poblada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
