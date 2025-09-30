#!/usr/bin/env python3
"""
Script para crear búsqueda de prueba para testear actualización
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Busqueda, Usuario, Plataforma, Propiedad, ResultadoBusqueda
from core.search_manager import save_search
import uuid

def crear_busqueda_test():
    """Crear una búsqueda de prueba"""
    
    # Obtener usuario testing
    usuario = Usuario.objects.filter(email="testing@example.com").first()
    if not usuario:
        print("❌ Usuario testing no encontrado. Ejecuta: python manage.py create_testing_user")
        return
    
    # Crear búsqueda
    filtros_test = {
        'tipo': 'apartamento',
        'departamento': 'Montevideo',
        'ciudad': 'Pocitos',
        'precio_min': 500,
        'precio_max': 1500,
        'plataforma': 'MercadoLibre'
    }
    
    busqueda_data = {
        'texto_original': "apartamento luminoso pocitos",
        'keywords': ['apartamento', 'luminoso'],
        'filtros': filtros_test,
        'nombre_busqueda': "🧪 Test Actualización - Apartamento Pocitos",
        'guardado': True,  # Importante: guardado=True para que aparezca en la lista
    }
    
    busqueda_id = save_search(busqueda_data)
    
    # Asignar usuario testing
    busqueda = Busqueda.objects.get(id=busqueda_id)
    busqueda.usuario = usuario
    busqueda.save()
    
    # Crear algunas propiedades de prueba para la búsqueda
    plataforma, _ = Plataforma.objects.get_or_create(
        nombre='MercadoLibre',
        defaults={'descripcion': 'MercadoLibre Uruguay'}
    )
    
    propiedades_test = [
        {
            'url': 'https://apartamento.mercadolibre.com.uy/MLU-test-001',
            'titulo': 'Apartamento luminoso en Pocitos con vista',
            'descripcion': 'Hermoso apartamento luminoso de 2 dormitorios en el corazón de Pocitos',
            'metadata': {
                'precio_valor': 1200,
                'precio_moneda': 'USD',
                'dormitorios': 2,
                'baños': 1
            }
        },
        {
            'url': 'https://apartamento.mercadolibre.com.uy/MLU-test-002', 
            'titulo': 'Moderno apartamento cerca de la rambla',
            'descripcion': 'Apartamento moderno con todas las comodidades',
            'metadata': {
                'precio_valor': 950,
                'precio_moneda': 'USD',
                'dormitorios': 1,
                'baños': 1
            }
        }
    ]
    
    busqueda = Busqueda.objects.get(id=busqueda_id)
    
    for prop_data in propiedades_test:
        propiedad = Propiedad.objects.create(
            url=prop_data['url'],
            titulo=prop_data['titulo'],
            descripcion=prop_data['descripcion'],
            metadata=prop_data['metadata'],
            plataforma=plataforma
        )
        
        # Crear resultado de búsqueda
        ResultadoBusqueda.objects.create(
            busqueda=busqueda,
            propiedad=propiedad,
            coincide=True,
            metadata={'test': True}
        )
    
    print("✅ BÚSQUEDA DE PRUEBA CREADA")
    print(f"ID: {busqueda_id}")
    print(f"Nombre: {busqueda.nombre_busqueda}")
    print(f"Propiedades: {len(propiedades_test)}")
    print(f"Usuario: {usuario.email}")
    print("\n🎯 INSTRUCCIONES:")
    print("1. Ve a http://localhost:10000")
    print("2. Busca la búsqueda '🧪 Test Actualización - Apartamento Pocitos'")
    print("3. Haz clic en 'Actualizar búsqueda'")
    print("4. Abre consola del navegador (F12) para ver logs de debug")
    
    return busqueda_id

if __name__ == "__main__":
    crear_busqueda_test()