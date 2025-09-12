#!/usr/bin/env python
"""
Script simple para poblar la base de datos con datos de ejemplo
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Busqueda, PalabraClave, Propiedad, Plataforma

def main():
    print("🚀 Poblando base de datos con ejemplos...")
    
    # Crear palabras clave
    print("🔤 Creando palabras clave...")
    keywords = [
        {'texto': 'apartamento', 'sinonimos': '["apto", "departamento", "depto", "piso"]'},
        {'texto': 'casa', 'sinonimos': '["vivienda", "hogar", "residencia", "chalet"]'},
        {'texto': 'garage', 'sinonimos': '["garaje", "cochera", "estacionamiento"]'},
        {'texto': 'piscina', 'sinonimos': '["pileta", "alberca", "natatorio"]'},
        {'texto': 'terraza', 'sinonimos': '["balcon", "balcón", "azotea", "deck"]'},
        {'texto': 'amueblado', 'sinonimos': '["muebles", "mobiliario", "equipado"]'},
        {'texto': 'seguridad', 'sinonimos': '["vigilancia", "portero", "alarma"]'},
    ]
    
    for data in keywords:
        PalabraClave.objects.create(**data)
        print(f"   ✅ {data['texto']}")
    
    # Crear búsquedas
    print("🔍 Creando búsquedas...")
    busquedas = [
        {
            'nombre_busqueda': 'Apartamento Pocitos - Alquiler USD',
            'texto_original': 'apartamento pocitos alquiler garage terraza vista mar',
            'filtros': {'tipo': 'apartamento', 'operacion': 'alquiler', 'ciudad': 'Pocitos', 'moneda': 'USD', 'precio_max': 1500},
            'guardado': True
        },
        {
            'nombre_busqueda': 'Casa Carrasco - Venta Premium',
            'texto_original': 'casa carrasco venta piscina jardin garage seguridad',
            'filtros': {'tipo': 'casa', 'operacion': 'venta', 'ciudad': 'Carrasco', 'moneda': 'USD', 'precio_max': 300000},
            'guardado': True
        },
        {
            'nombre_busqueda': 'Apartamento Centro - Alquiler Pesos',
            'texto_original': 'apartamento centro alquiler amueblado profesional',
            'filtros': {'tipo': 'apartamento', 'operacion': 'alquiler', 'ciudad': 'Centro', 'moneda': 'UYU', 'precio_max': 45000},
            'guardado': True
        },
        {
            'nombre_busqueda': 'Casa Punta del Este - Vista Mar',
            'texto_original': 'casa punta del este venta vista mar piscina terraza',
            'filtros': {'tipo': 'casa', 'operacion': 'venta', 'ciudad': 'Punta del Este', 'moneda': 'USD', 'precio_max': 500000},
            'guardado': True
        },
        {
            'nombre_busqueda': 'Apartamento Cordón - Inversión',
            'texto_original': 'apartamento cordon inversion alquiler zona comercial',
            'filtros': {'tipo': 'apartamento', 'operacion': 'venta', 'ciudad': 'Cordón', 'moneda': 'USD', 'precio_max': 150000},
            'guardado': True
        },
        {
            'nombre_busqueda': 'Búsqueda Temporal',
            'texto_original': 'apartamento alquiler economico',
            'filtros': {'tipo': 'apartamento', 'operacion': 'alquiler', 'moneda': 'USD', 'precio_max': 1000},
            'guardado': False
        }
    ]
    
    for data in busquedas:
        Busqueda.objects.create(**data)
        estado = "💾 Guardada" if data['guardado'] else "📝 Temporal"
        print(f"   ✅ {estado}: {data['nombre_busqueda']}")
    
    # Obtener plataforma
    plataforma_ml, created = Plataforma.objects.get_or_create(
        nombre='MercadoLibre',
        defaults={'descripcion': 'Portal de clasificados', 'url': 'https://mercadolibre.com.uy'}
    )
    
    # Crear propiedades
    print("🏠 Creando propiedades...")
    propiedades = [
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo1-pocitos',
            'titulo': 'Apartamento en Pocitos con Vista al Mar',
            'descripcion': 'Hermoso apartamento de 2 dormitorios en Pocitos con vista al mar, garage y terraza.',
            'metadata': {'precio': 1200, 'moneda': 'USD', 'ubicacion': 'Pocitos', 'dormitorios': 2, 'garage': True, 'terraza': True},
            'plataforma': plataforma_ml
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo2-carrasco',
            'titulo': 'Casa en Carrasco con Piscina',
            'descripcion': 'Casa familiar en Carrasco con 4 dormitorios, piscina y jardín.',
            'metadata': {'precio': 280000, 'moneda': 'USD', 'ubicacion': 'Carrasco', 'dormitorios': 4, 'piscina': True, 'jardin': True},
            'plataforma': plataforma_ml
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo3-centro',
            'titulo': 'Apartamento Amueblado en Centro',
            'descripcion': 'Apartamento amueblado en el centro, ideal para profesionales.',
            'metadata': {'precio': 35000, 'moneda': 'UYU', 'ubicacion': 'Centro', 'dormitorios': 1, 'amueblado': True},
            'plataforma': plataforma_ml
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo4-punta',
            'titulo': 'Casa en Punta del Este con Vista al Mar',
            'descripcion': 'Casa a 2 cuadras de la playa con piscina y terraza.',
            'metadata': {'precio': 350000, 'moneda': 'USD', 'ubicacion': 'Punta del Este', 'dormitorios': 3, 'piscina': True, 'vista_mar': True},
            'plataforma': plataforma_ml
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo5-cordon',
            'titulo': 'Apartamento de Inversión en Cordón',
            'descripcion': 'Apartamento en muy buen estado para inversión en zona comercial.',
            'metadata': {'precio': 120000, 'moneda': 'USD', 'ubicacion': 'Cordón', 'dormitorios': 2, 'inversion': True},
            'plataforma': plataforma_ml
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo6-blanqueada',
            'titulo': 'Casa Familiar en La Blanqueada',
            'descripcion': 'Casa de 3 dormitorios con patio y garage en zona tranquila.',
            'metadata': {'precio': 180000, 'moneda': 'USD', 'ubicacion': 'La Blanqueada', 'dormitorios': 3, 'garage': True, 'patio': True},
            'plataforma': plataforma_ml
        }
    ]
    
    for data in propiedades:
        Propiedad.objects.create(**data)
        meta = data['metadata']
        print(f"   ✅ {data['titulo']}")
        print(f"      📍 {meta['ubicacion']} - {meta['dormitorios']} dorm - {meta['moneda']} {meta['precio']:,}")
    
    # Estadísticas
    print(f"\n📊 Resultados:")
    print(f"   🔤 Palabras clave: {PalabraClave.objects.count()}")
    print(f"   🔍 Búsquedas guardadas: {Busqueda.objects.filter(guardado=True).count()}")
    print(f"   📝 Búsquedas temporales: {Busqueda.objects.filter(guardado=False).count()}")
    print(f"   🏠 Propiedades: {Propiedad.objects.count()}")
    print("✅ ¡Base de datos poblada exitosamente!")

if __name__ == '__main__':
    main()
