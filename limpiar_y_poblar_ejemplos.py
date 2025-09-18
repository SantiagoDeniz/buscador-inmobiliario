#!/usr/bin/env python
"""
Script para limpiar y poblar la base de datos con ejemplos de búsquedas guardadas,
propiedades, palabras clave y tablas relacionadas.
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json
import uuid

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import (
    Inmobiliaria, Usuario, Plataforma, Busqueda, PalabraClave, 
    Propiedad, BusquedaPalabraClave, PalabraClavePropiedad, ResultadoBusqueda
)

def limpiar_base_datos():
    """Vacía todas las tablas en el orden correcto para evitar errores de FK"""
    print("🧹 Limpiando base de datos...")
    
    # Orden de eliminación: primero las tablas dependientes
    ResultadoBusqueda.objects.all().delete()
    print("   ✓ ResultadoBusqueda")
    
    PalabraClavePropiedad.objects.all().delete()
    print("   ✓ PalabraClavePropiedad")
    
    BusquedaPalabraClave.objects.all().delete()
    print("   ✓ BusquedaPalabraClave")
    
    Propiedad.objects.all().delete()
    print("   ✓ Propiedad")
    
    PalabraClave.objects.all().delete()
    print("   ✓ PalabraClave")
    
    Busqueda.objects.all().delete()
    print("   ✓ Busqueda")
    
    Usuario.objects.all().delete()
    print("   ✓ Usuario")
    
    Inmobiliaria.objects.all().delete()
    print("   ✓ Inmobiliaria")
    
    Plataforma.objects.all().delete()
    print("   ✓ Plataforma")
    
    print("🎉 Base de datos limpiada exitosamente\n")

def crear_datos_ejemplo():
    """Crea datos de ejemplo para demostrar el sistema"""
    print("📊 Creando datos de ejemplo...")
    
    # 1. Crear Plataformas
    print("   Creando plataformas...")
    ml_plataforma = Plataforma.objects.create(
        nombre="MercadoLibre",
        descripcion="Portal inmobiliario de MercadoLibre Uruguay",
        url="https://inmuebles.mercadolibre.com.uy"
    )
    
    infocasas_plataforma = Plataforma.objects.create(
        nombre="InfoCasas", 
        descripcion="Portal inmobiliario InfoCasas Uruguay",
        url="https://www.infocasas.com.uy"
    )
    print("   ✓ Plataformas creadas")
    
    # 2. Crear Inmobiliaria y Usuario
    print("   Creando inmobiliaria y usuario...")
    inmobiliaria = Inmobiliaria.objects.create(
        nombre="Inmobiliaria Demo",
        plan="premium"
    )
    
    usuario = Usuario.objects.create(
        nombre="Usuario Demo",
        email="demo@example.com",
        password_hash="hash_demo_123",
        inmobiliaria=inmobiliaria
    )
    print("   ✓ Inmobiliaria y usuario creados")
    
    # 3. Crear Palabras Clave
    print("   Creando palabras clave...")
    palabras_clave = [
        {
            'texto': 'apartamento',
            'sinonimos': ['apto', 'departamento', 'piso', 'flat']
        },
        {
            'texto': 'casa', 
            'sinonimos': ['vivienda', 'hogar', 'residencia', 'chalet']
        },
        {
            'texto': 'garage',
            'sinonimos': ['garaje', 'cochera', 'estacionamiento']
        },
        {
            'texto': 'piscina',
            'sinonimos': ['pileta', 'pool', 'alberca']
        },
        {
            'texto': 'terraza',
            'sinonimos': ['balcón', 'balcon', 'terrasse', 'patio']
        }
    ]
    
    palabras_obj = []
    for pc_data in palabras_clave:
        pc = PalabraClave.objects.create(
            texto=pc_data['texto'],
            idioma='es'
        )
        pc.set_sinonimos(pc_data['sinonimos'])
        pc.save()
        palabras_obj.append(pc)
    print(f"   ✓ {len(palabras_obj)} palabras clave creadas")
    
    # 4. Crear Propiedades
    print("   Creando propiedades...")
    propiedades_data = [
        {
            'url': 'https://inmuebles.mercadolibre.com.uy/MLU-123456-apartamento-pocitos-2-dormitorios',
            'titulo': 'Apartamento en Pocitos - 2 dormitorios con garage',
            'descripcion': 'Hermoso apartamento de 2 dormitorios en zona Pocitos. Cuenta con garage, terraza y excelente ubicación cerca del mar.',
            'metadata': {
                'precio': 1200,
                'moneda': 'USD',
                'operacion': 'alquiler',
                'tipo': 'apartamento',
                'dormitorios': 2,
                'baños': 1,
                'garage': True,
                'terraza': True,
                'zona': 'Pocitos',
                'departamento': 'Montevideo'
            },
            'plataforma': ml_plataforma
        },
        {
            'url': 'https://inmuebles.mercadolibre.com.uy/MLU-789012-casa-carrasco-3-dormitorios-piscina',
            'titulo': 'Casa en Carrasco con piscina - 3 dormitorios',
            'descripcion': 'Amplia casa de 3 dormitorios en Carrasco. Cuenta con piscina, garage doble y jardín. Ideal para familias.',
            'metadata': {
                'precio': 2500,
                'moneda': 'USD', 
                'operacion': 'alquiler',
                'tipo': 'casa',
                'dormitorios': 3,
                'baños': 2,
                'garage': True,
                'piscina': True,
                'zona': 'Carrasco',
                'departamento': 'Montevideo'
            },
            'plataforma': ml_plataforma
        },
        {
            'url': 'https://www.infocasas.com.uy/venta/apartamento-centro-montevideo-345678',
            'titulo': 'Apartamento Centro - 1 dormitorio para inversión',
            'descripcion': 'Apartamento de 1 dormitorio en pleno centro de Montevideo. Ideal para inversión o profesional joven.',
            'metadata': {
                'precio': 85000,
                'moneda': 'USD',
                'operacion': 'venta',
                'tipo': 'apartamento', 
                'dormitorios': 1,
                'baños': 1,
                'garage': False,
                'zona': 'Centro',
                'departamento': 'Montevideo'
            },
            'plataforma': infocasas_plataforma
        },
        {
            'url': 'https://inmuebles.mercadolibre.com.uy/MLU-456789-apartamento-punta-del-este-2-dorm',
            'titulo': 'Apartamento Punta del Este - 2 dormitorios con terraza',
            'descripcion': 'Moderno apartamento de 2 dormitorios en Punta del Este. Terraza con vista al mar, garage y amenities.',
            'metadata': {
                'precio': 1800,
                'moneda': 'USD',
                'operacion': 'alquiler',
                'tipo': 'apartamento',
                'dormitorios': 2,
                'baños': 2,
                'garage': True,
                'terraza': True,
                'zona': 'Peninsula',
                'departamento': 'Maldonado'
            },
            'plataforma': ml_plataforma
        }
    ]
    
    propiedades_obj = []
    for prop_data in propiedades_data:
        prop = Propiedad.objects.create(
            url=prop_data['url'],
            titulo=prop_data['titulo'],
            descripcion=prop_data['descripcion'],
            metadata=prop_data['metadata'],
            plataforma=prop_data['plataforma']
        )
        propiedades_obj.append(prop)
    print(f"   ✓ {len(propiedades_obj)} propiedades creadas")
    
    # 5. Crear Búsquedas Guardadas
    print("   Creando búsquedas guardadas...")
    busquedas_data = [
        {
            'nombre_busqueda': 'Apartamentos Pocitos Alquiler',
            'texto_original': 'apartamento en pocitos para alquiler hasta 1500 usd',
            'filtros': {
                'tipo': 'apartamento',
                'operacion': 'alquiler',
                'departamento': 'Montevideo',
                'zona': 'Pocitos',
                'precio_max': 1500,
                'moneda': 'USD'
            },
            'guardado': True,
            'usuario': usuario,
            'palabras_clave': ['apartamento']
        },
        {
            'nombre_busqueda': 'Casas con Piscina',
            'texto_original': 'casa con piscina en montevideo para alquiler',
            'filtros': {
                'tipo': 'casa',
                'operacion': 'alquiler',
                'departamento': 'Montevideo',
                'caracteristicas': ['piscina']
            },
            'guardado': True,
            'usuario': usuario,
            'palabras_clave': ['casa', 'piscina']
        },
        {
            'nombre_busqueda': 'Inversión Centro',
            'texto_original': 'apartamento centro montevideo venta inversion hasta 100000',
            'filtros': {
                'tipo': 'apartamento',
                'operacion': 'venta',
                'departamento': 'Montevideo',
                'zona': 'Centro',
                'precio_max': 100000,
                'moneda': 'USD'
            },
            'guardado': True,
            'usuario': usuario,
            'palabras_clave': ['apartamento']
        },
        {
            'nombre_busqueda': 'Punta del Este Temporada',
            'texto_original': 'apartamento punta del este alquiler 2 dormitorios con terraza',
            'filtros': {
                'tipo': 'apartamento',
                'operacion': 'alquiler',
                'departamento': 'Maldonado',
                'ciudad': 'Punta del Este',
                'dormitorios': 2,
                'caracteristicas': ['terraza']
            },
            'guardado': True,
            'usuario': usuario,
            'palabras_clave': ['apartamento', 'terraza']
        }
    ]
    
    busquedas_obj = []
    for busq_data in busquedas_data:
        busqueda = Busqueda.objects.create(
            nombre_busqueda=busq_data['nombre_busqueda'],
            texto_original=busq_data['texto_original'],
            filtros=busq_data['filtros'],
            guardado=busq_data['guardado'],
            usuario=busq_data['usuario'],
            ultima_revision=datetime.now() - timedelta(days=1)
        )
        busquedas_obj.append(busqueda)
        
        # Asociar palabras clave a la búsqueda
        for texto_pc in busq_data['palabras_clave']:
            try:
                palabra_clave = next(pc for pc in palabras_obj if pc.texto == texto_pc)
                BusquedaPalabraClave.objects.create(
                    busqueda=busqueda,
                    palabra_clave=palabra_clave
                )
            except StopIteration:
                print(f"     ⚠️  Palabra clave '{texto_pc}' no encontrada")
    
    print(f"   ✓ {len(busquedas_obj)} búsquedas guardadas creadas")
    
    # 6. Crear relaciones Palabra-Propiedad y Resultados de Búsqueda
    print("   Creando relaciones y resultados...")
    
    # Relacionar palabras clave con propiedades (simulando que se encontraron)
    relaciones_creadas = 0
    for propiedad in propiedades_obj:
        for palabra in palabras_obj:
            # Simular si la palabra clave se encuentra en la propiedad
            encontrada = False
            texto_completo = f"{propiedad.titulo} {propiedad.descripcion}".lower()
            
            # Buscar la palabra o sus sinónimos
            if palabra.texto.lower() in texto_completo:
                encontrada = True
            else:
                for sinonimo in palabra.sinonimos_list:
                    if sinonimo.lower() in texto_completo:
                        encontrada = True
                        break
            
            if encontrada:
                PalabraClavePropiedad.objects.create(
                    palabra_clave=palabra,
                    propiedad=propiedad,
                    encontrada=True
                )
                relaciones_creadas += 1
    
    print(f"   ✓ {relaciones_creadas} relaciones palabra-propiedad creadas")
    
    # Crear resultados de búsqueda (asociar propiedades con búsquedas)
    resultados_creados = 0
    for busqueda in busquedas_obj:
        for propiedad in propiedades_obj:
            # Determinar si la propiedad coincide con los filtros de la búsqueda
            coincide = evaluar_coincidencia(busqueda.filtros, propiedad.metadata)
            
            if coincide:
                ResultadoBusqueda.objects.create(
                    busqueda=busqueda,
                    propiedad=propiedad,
                    coincide=True,
                    metadata={'score': 0.85, 'fecha_match': datetime.now().isoformat()},
                    last_seen_at=datetime.now() - timedelta(hours=2),
                    seen_count=1
                )
                resultados_creados += 1
    
    print(f"   ✓ {resultados_creados} resultados de búsqueda creados")
    print("🎉 Datos de ejemplo creados exitosamente\n")

def evaluar_coincidencia(filtros_busqueda, metadata_propiedad):
    """Evalúa si una propiedad coincide con los filtros de una búsqueda"""
    try:
        # Verificar tipo de propiedad
        if 'tipo' in filtros_busqueda and filtros_busqueda['tipo'] != metadata_propiedad.get('tipo'):
            return False
        
        # Verificar operación
        if 'operacion' in filtros_busqueda and filtros_busqueda['operacion'] != metadata_propiedad.get('operacion'):
            return False
        
        # Verificar departamento
        if 'departamento' in filtros_busqueda and filtros_busqueda['departamento'] != metadata_propiedad.get('departamento'):
            return False
        
        # Verificar zona (opcional)
        if 'zona' in filtros_busqueda and filtros_busqueda['zona'] != metadata_propiedad.get('zona'):
            return False
        
        # Verificar precio máximo
        if 'precio_max' in filtros_busqueda:
            precio = metadata_propiedad.get('precio', 0)
            if precio > filtros_busqueda['precio_max']:
                return False
        
        # Verificar dormitorios
        if 'dormitorios' in filtros_busqueda:
            dormitorios = metadata_propiedad.get('dormitorios', 0)
            if dormitorios != filtros_busqueda['dormitorios']:
                return False
        
        # Verificar características especiales
        if 'caracteristicas' in filtros_busqueda:
            for caracteristica in filtros_busqueda['caracteristicas']:
                if not metadata_propiedad.get(caracteristica, False):
                    return False
        
        return True
    except Exception as e:
        print(f"     ⚠️  Error evaluando coincidencia: {e}")
        return False

def mostrar_resumen():
    """Muestra un resumen de los datos creados"""
    print("📋 RESUMEN DE DATOS CREADOS:")
    print(f"   • Inmobiliarias: {Inmobiliaria.objects.count()}")
    print(f"   • Usuarios: {Usuario.objects.count()}")
    print(f"   • Plataformas: {Plataforma.objects.count()}")
    print(f"   • Palabras Clave: {PalabraClave.objects.count()}")
    print(f"   • Propiedades: {Propiedad.objects.count()}")
    print(f"   • Búsquedas Guardadas: {Busqueda.objects.filter(guardado=True).count()}")
    print(f"   • Relaciones Palabra-Propiedad: {PalabraClavePropiedad.objects.count()}")
    print(f"   • Resultados de Búsqueda: {ResultadoBusqueda.objects.count()}")
    print()
    
    print("🔍 BÚSQUEDAS GUARDADAS:")
    for busqueda in Busqueda.objects.filter(guardado=True):
        resultados = ResultadoBusqueda.objects.filter(busqueda=busqueda, coincide=True).count()
        print(f"   • {busqueda.nombre_busqueda}: {resultados} propiedades encontradas")
    print()

def main():
    """Función principal"""
    print("🚀 LIMPIEZA Y POBLACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    try:
        # Limpiar datos existentes
        limpiar_base_datos()
        
        # Crear datos de ejemplo
        crear_datos_ejemplo()
        
        # Mostrar resumen
        mostrar_resumen()
        
        print("✅ Proceso completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()