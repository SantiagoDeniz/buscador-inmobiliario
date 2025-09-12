#!/usr/bin/env python
"""
Script para limpiar y poblar la base de datos con búsquedas de ejemplo mejoradas
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


def limpiar_datos():
    """Limpia las tablas principales manteniendo datos de configuración"""
    print("🧹 Limpiando datos existentes...")
    
    # Limpiar en orden para evitar problemas de foreign keys
    PalabraClavePropiedad.objects.all().delete()
    ResultadoBusqueda.objects.all().delete()
    Propiedad.objects.all().delete()
    Busqueda.objects.all().delete()
    PalabraClave.objects.all().delete()
    
    print("   ✅ Datos limpiados correctamente")


def crear_keywords_ejemplo():
    """Crea palabras clave de ejemplo con sinónimos"""
    print("🔤 Creando palabras clave de ejemplo...")
    
    keywords_data = [
        {
            'palabra': 'apartamento',
            'sinonimos': ['apto', 'departamento', 'depto', 'piso', 'unidad']
        },
        {
            'palabra': 'casa',
            'sinonimos': ['vivienda', 'hogar', 'residencia', 'chalet']
        },
        {
            'palabra': 'garage',
            'sinonimos': ['garaje', 'cochera', 'estacionamiento', 'parking']
        },
        {
            'palabra': 'piscina',
            'sinonimos': ['pileta', 'alberca', 'natatorio']
        },
        {
            'palabra': 'jardin',
            'sinonimos': ['jardín', 'patio', 'verde', 'exterior']
        },
        {
            'palabra': 'terraza',
            'sinonimos': ['balcon', 'balcón', 'azotea', 'deck']
        },
        {
            'palabra': 'amueblado',
            'sinonimos': ['muebles', 'mobiliario', 'equipado', 'furnished']
        },
        {
            'palabra': 'seguridad',
            'sinonimos': ['vigilancia', 'portero', 'alarma', 'cámaras']
        }
    ]
    
    keywords_creadas = []
    for data in keywords_data:
        keyword = PalabraClave.objects.create(
            palabra=data['palabra']
        )
        keyword.set_sinonimos(data['sinonimos'])
        keyword.save()
        keywords_creadas.append(keyword)
        print(f"   ✅ Creada: {data['palabra']} con {len(data['sinonimos'])} sinónimos")
    
    return keywords_creadas


def crear_busquedas_ejemplo():
    """Crea búsquedas de ejemplo variadas y realistas"""
    print("🔍 Creando búsquedas de ejemplo...")
    
    # Obtener plataforma de MercadoLibre
    try:
        plataforma_ml = Plataforma.objects.get(nombre='MercadoLibre')
    except Plataforma.DoesNotExist:
        plataforma_ml = Plataforma.objects.create(
            nombre='MercadoLibre',
            url_base='https://listado.mercadolibre.com.uy'
        )
    
    busquedas_data = [
        {
            'titulo': 'Apartamento en Pocitos - Alquiler USD',
            'filtros': {
                'tipo': 'apartamento',
                'operacion': 'alquiler',
                'departamento': 'Montevideo',
                'ciudad': 'Pocitos',
                'moneda': 'USD',
                'precio_min': 800,
                'precio_max': 1500,
                'dormitorios_min': 2,
                'dormitorios_max': 3
            },
            'keywords': 'apartamento pocitos alquiler garage terraza',
            'guardado': True,
            'descripcion': 'Búsqueda de apartamento para alquilar en Pocitos con garage y terraza'
        },
        {
            'titulo': 'Casa en Carrasco - Venta',
            'filtros': {
                'tipo': 'casa',
                'operacion': 'venta',
                'departamento': 'Montevideo',
                'ciudad': 'Carrasco',
                'moneda': 'USD',
                'precio_min': 150000,
                'precio_max': 300000,
                'dormitorios_min': 3,
                'dormitorios_max': 4
            },
            'keywords': 'casa carrasco venta piscina jardin garage',
            'guardado': True,
            'descripcion': 'Casa familiar en Carrasco con piscina y jardín amplio'
        },
        {
            'titulo': 'Apartamento Centro - Alquiler Pesos',
            'filtros': {
                'tipo': 'apartamento',
                'operacion': 'alquiler',
                'departamento': 'Montevideo',
                'ciudad': 'Centro',
                'moneda': 'UYU',
                'precio_min': 25000,
                'precio_max': 45000,
                'dormitorios_min': 1,
                'dormitorios_max': 2
            },
            'keywords': 'apartamento centro alquiler amueblado',
            'guardado': True,
            'descripcion': 'Apartamento en el centro, ideal para profesionales'
        },
        {
            'titulo': 'Casa en Maldonado - Venta',
            'filtros': {
                'tipo': 'casa',
                'operacion': 'venta',
                'departamento': 'Maldonado',
                'ciudad': 'Punta del Este',
                'moneda': 'USD',
                'precio_min': 200000,
                'precio_max': 500000,
                'dormitorios_min': 3,
                'dormitorios_max': 5
            },
            'keywords': 'casa punta del este venta piscina terraza vista mar',
            'guardado': True,
            'descripcion': 'Casa en Punta del Este con vista al mar'
        },
        {
            'titulo': 'Apartamento Cordón - Inversión',
            'filtros': {
                'tipo': 'apartamento',
                'operacion': 'venta',
                'departamento': 'Montevideo',
                'ciudad': 'Cordón',
                'moneda': 'USD',
                'precio_min': 80000,
                'precio_max': 150000,
                'dormitorios_min': 1,
                'dormitorios_max': 2
            },
            'keywords': 'apartamento cordon inversion alquiler seguridad',
            'guardado': True,
            'descripcion': 'Apartamento para inversión en zona de alta demanda'
        },
        {
            'titulo': 'Búsqueda Temporal - No Guardada',
            'filtros': {
                'tipo': 'apartamento',
                'operacion': 'alquiler',
                'departamento': 'Montevideo',
                'ciudad': 'Montevideo',
                'moneda': 'USD',
                'precio_max': 1000
            },
            'keywords': 'apartamento alquiler economico',
            'guardado': False,
            'descripcion': 'Búsqueda temporal de prueba - aparece solo en historial'
        }
    ]
    
    busquedas_creadas = []
    for i, data in enumerate(busquedas_data):
        # Crear fecha variada (últimos 30 días)
        fecha_creacion = timezone.now() - timedelta(days=30-i*5)
        
        busqueda = Busqueda.objects.create(
            filtros=data['filtros'],
            keywords=data['keywords'],
            guardado=data['guardado'],
            plataforma=plataforma_ml,
            total_resultados=0,  # Se actualizará si se ejecuta scraping
            tiempo_ejecucion=0.0,
            created_at=fecha_creacion,
            updated_at=fecha_creacion
        )
        busquedas_creadas.append(busqueda)
        
        estado = "💾 Guardada" if data['guardado'] else "📝 Temporal"
        print(f"   ✅ {estado}: {data['titulo']}")
        print(f"      📍 {data['filtros'].get('departamento', '')} - {data['filtros'].get('ciudad', '')}")
        print(f"      💰 {data['filtros'].get('moneda', '')} {data['filtros'].get('precio_min', 0):,} - {data['filtros'].get('precio_max', 0):,}")
    
    return busquedas_creadas


def crear_propiedades_ejemplo():
    """Crea propiedades de ejemplo"""
    print("🏠 Creando propiedades de ejemplo...")
    
    # Obtener o crear inmobiliaria
    try:
        inmobiliaria = Inmobiliaria.objects.first()
        if not inmobiliaria:
            inmobiliaria = Inmobiliaria.objects.create(
                nombre='Inmobiliaria Ejemplo',
                telefono='099123456',
                email='info@ejemplo.com'
            )
    except:
        inmobiliaria = None
    
    propiedades_data = [
        {
            'titulo': 'Apartamento en Pocitos con Vista al Mar',
            'descripcion': 'Hermoso apartamento de 2 dormitorios en Pocitos con vista panorámica al mar. Cuenta con garage, terraza y amenities completos.',
            'precio': 1200.00,
            'moneda': 'USD',
            'ubicacion': 'Pocitos, Montevideo',
            'dormitorios': 2,
            'banos': 2,
            'metros_cuadrados': 85,
            'url_detalle': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo1',
            'caracteristicas': {
                'garage': True,
                'terraza': True,
                'vista_mar': True,
                'amenities': True,
                'seguridad': True
            }
        },
        {
            'titulo': 'Casa en Carrasco con Piscina y Jardín',
            'descripcion': 'Espectacular casa familiar en Carrasco Norte. 4 dormitorios, piscina climatizada, amplio jardín y garage para 2 autos.',
            'precio': 280000.00,
            'moneda': 'USD',
            'ubicacion': 'Carrasco, Montevideo',
            'dormitorios': 4,
            'banos': 3,
            'metros_cuadrados': 250,
            'url_detalle': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo2',
            'caracteristicas': {
                'piscina': True,
                'jardin': True,
                'garage': True,
                'barbacoa': True,
                'seguridad': True
            }
        },
        {
            'titulo': 'Apartamento Amueblado en Centro',
            'descripcion': 'Apartamento completamente amueblado en el centro de Montevideo. Ideal para profesionales. Incluye todos los electrodomésticos.',
            'precio': 35000.00,
            'moneda': 'UYU',
            'ubicacion': 'Centro, Montevideo',
            'dormitorios': 1,
            'banos': 1,
            'metros_cuadrados': 45,
            'url_detalle': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo3',
            'caracteristicas': {
                'amueblado': True,
                'electrodomesticos': True,
                'calefaccion': True,
                'internet': True
            }
        },
        {
            'titulo': 'Casa en Punta del Este con Vista al Mar',
            'descripcion': 'Hermosa casa a 2 cuadras de Playa Brava. 3 dormitorios, piscina, terraza con parrillero y vista parcial al mar.',
            'precio': 350000.00,
            'moneda': 'USD',
            'ubicacion': 'Punta del Este, Maldonado',
            'dormitorios': 3,
            'banos': 2,
            'metros_cuadrados': 180,
            'url_detalle': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo4',
            'caracteristicas': {
                'piscina': True,
                'terraza': True,
                'parrillero': True,
                'vista_mar': True,
                'cerca_playa': True
            }
        },
        {
            'titulo': 'Apartamento de Inversión en Cordón',
            'descripcion': 'Excelente oportunidad de inversión. Apartamento en muy buen estado, zona de alta demanda para alquiler.',
            'precio': 120000.00,
            'moneda': 'USD',
            'ubicacion': 'Cordón, Montevideo',
            'dormitorios': 2,
            'banos': 1,
            'metros_cuadrados': 60,
            'url_detalle': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo5',
            'caracteristicas': {
                'inversion': True,
                'buen_estado': True,
                'zona_comercial': True,
                'transporte': True
            }
        }
    ]
    
    propiedades_creadas = []
    for data in propiedades_data:
        propiedad = Propiedad.objects.create(
            titulo=data['titulo'],
            descripcion=data['descripcion'],
            precio=data['precio'],
            moneda=data['moneda'],
            ubicacion=data['ubicacion'],
            dormitorios=data['dormitorios'],
            banos=data['banos'],
            metros_cuadrados=data['metros_cuadrados'],
            url_detalle=data['url_detalle'],
            imagen_principal='',  # Se llenarían con scraping real
            caracteristicas=json.dumps(data['caracteristicas']),
            inmobiliaria=inmobiliaria
        )
        propiedades_creadas.append(propiedad)
        print(f"   ✅ {data['titulo']}")
        print(f"      📍 {data['ubicacion']} - {data['dormitorios']} dorm, {data['banos']} baños")
        print(f"      💰 {data['moneda']} {data['precio']:,.0f}")
    
    return propiedades_creadas


def mostrar_estadisticas():
    """Muestra estadísticas de los datos creados"""
    print("\n📊 Estadísticas de la base de datos:")
    print(f"   🔤 Palabras clave: {PalabraClave.objects.count()}")
    print(f"   🔍 Búsquedas guardadas: {Busqueda.objects.filter(guardado=True).count()}")
    print(f"   📝 Búsquedas temporales: {Busqueda.objects.filter(guardado=False).count()}")
    print(f"   🏠 Propiedades: {Propiedad.objects.count()}")
    print(f"   🔗 Relaciones keyword-propiedad: {PalabraClavePropiedad.objects.count()}")


def main():
    """Función principal"""
    print("🚀 Iniciando limpieza y población de la base de datos...")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # Paso 1: Limpiar datos existentes
            limpiar_datos()
            
            # Paso 2: Crear palabras clave
            keywords = crear_keywords_ejemplo()
            
            # Paso 3: Crear búsquedas de ejemplo
            busquedas = crear_busquedas_ejemplo()
            
            # Paso 4: Crear propiedades de ejemplo
            propiedades = crear_propiedades_ejemplo()
            
            # Paso 5: Mostrar estadísticas
            mostrar_estadisticas()
            
        print("\n✅ ¡Base de datos limpiada y poblada exitosamente!")
        print("=" * 60)
        print("💡 Usa 'python ver_datos_tabla.py --list' para ver el estado actual")
        print("💡 Usa 'python ver_datos_tabla.py busqueda' para ver las búsquedas")
        print("💡 Usa 'python ver_datos_tabla.py propiedad' para ver las propiedades")
        
    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
