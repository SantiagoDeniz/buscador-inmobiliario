from django.core.management.base import BaseCommand
from core.models import (Busqueda, PalabraClave, Propiedad, ResultadoBusqueda, 
                        Usuario, BusquedaPalabraClave, Plataforma, Inmobiliaria)
from datetime import datetime, timedelta
import random
import json


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para testing'
    
    def handle(self, *args, **options):
        self.stdout.write('🏠 Creando datos de ejemplo...')
        
        # Crear inmobiliaria primero
        inmobiliaria, created = Inmobiliaria.objects.get_or_create(
            nombre='Inmobiliaria Ejemplo',
            defaults={
                'plan': 'basico'
            }
        )
        if created:
            self.stdout.write('✅ Inmobiliaria de ejemplo creada')
        
        # Crear usuario de ejemplo si no existe
        user, created = Usuario.objects.get_or_create(
            nombre='test_user',
            defaults={
                'email': 'test@example.com',
                'password_hash': '!',
                'inmobiliaria': inmobiliaria
            }
        )
        
        if created:
            self.stdout.write('✅ Usuario de prueba creado')
        
        # Palabras clave de ejemplo
        keywords_data = [
            ('apartamento', 'es'),
            ('casa', 'es'),
            ('alquiler', 'es'),
            ('venta', 'es'),
            ('Montevideo', 'es'),
            ('Pocitos', 'es'),
            ('Punta Carretas', 'es'),
            ('3 dormitorios', 'es'),
            ('garage', 'es'),
            ('terraza', 'es'),
        ]
        
        keywords = []
        for texto, idioma in keywords_data:
            keyword, created = PalabraClave.objects.get_or_create(
                texto=texto,
                idioma=idioma
            )
            keywords.append(keyword)
        
        self.stdout.write(f'✅ {len(keywords)} palabras clave creadas')
        
        # Crear búsquedas de ejemplo
        searches = []
        for i in range(5):
            busqueda = Busqueda.objects.create(
                usuario=user,
                nombre_busqueda=f'Búsqueda Ejemplo {i+1}',
                texto_original=f'Búsqueda de prueba número {i+1}',
                guardado=i % 2 == 0,  # Intercaladas guardadas
                filtros={"tipo": "ejemplo", "numero": i+1}
            )
            
            # Asociar palabras clave aleatorias usando tabla intermedia
            selected_keywords = random.sample(keywords, random.randint(2, 4))
            for keyword in selected_keywords:
                BusquedaPalabraClave.objects.get_or_create(
                    busqueda=busqueda,
                    palabra_clave=keyword
                )
            
            searches.append(busqueda)
        
        self.stdout.write(f'✅ {len(searches)} búsquedas creadas')
        
        # Crear o obtener plataforma
        plataforma, created = Plataforma.objects.get_or_create(
            nombre='MercadoLibre',
            defaults={'url': 'https://www.mercadolibre.com.uy'}
        )
        if created:
            self.stdout.write('✅ Plataforma MercadoLibre creada')
        
        # Crear propiedades de ejemplo
        propiedades_data = [
            {
                'titulo': 'Apartamento 3 dormitorios Pocitos',
                'descripcion': 'Hermoso apartamento con vista al mar',
                'url': 'https://example.com/prop1',
                'metadata': {'dormitorios': 3, 'baños': 2, 'garage': True, 'precio': 350000}
            },
            {
                'titulo': 'Casa en Punta Carretas',
                'descripcion': 'Casa con jardín y parrillero',
                'url': 'https://example.com/prop2',
                'metadata': {'dormitorios': 4, 'baños': 3, 'garage': True, 'precio': 4500, 'jardin': True}
            },
            {
                'titulo': 'Apartamento en alquiler Centro',
                'descripcion': 'Moderno apartamento céntrico',
                'url': 'https://example.com/prop3',
                'metadata': {'dormitorios': 2, 'baños': 1, 'precio': 25000, 'amueblado': True}
            },
        ]
        
        propiedades = []
        for prop_data in propiedades_data:
            prop_data['plataforma'] = plataforma
            propiedad = Propiedad.objects.create(**prop_data)
            propiedades.append(propiedad)
        
        self.stdout.write(f'✅ {len(propiedades)} propiedades creadas')
        
        # Crear resultados de búsqueda
        resultados = []
        for busqueda in searches:
            # Cada búsqueda encuentra 1-3 propiedades
            found_props = random.sample(propiedades, random.randint(1, len(propiedades)))
            
            for prop in found_props:
                resultado = ResultadoBusqueda.objects.create(
                    busqueda=busqueda,
                    propiedad=prop,
                    coincide=random.choice([True, False]),
                    metadata={'relevancia': random.uniform(0.5, 1.0)}
                )
                resultados.append(resultado)
        
        self.stdout.write(f'✅ {len(resultados)} resultados creados')
        
        # Mostrar estadísticas
        self.stdout.write('\n📊 Resumen datos creados:')
        self.stdout.write(f'   👤 Usuarios: {Usuario.objects.count()}')
        self.stdout.write(f'   🔍 Búsquedas: {Busqueda.objects.count()}')
        self.stdout.write(f'   🏷️ Palabras clave: {PalabraClave.objects.count()}')
        self.stdout.write(f'   🏠 Propiedades: {Propiedad.objects.count()}')
        self.stdout.write(f'   📋 Resultados: {ResultadoBusqueda.objects.count()}')
        
        self.stdout.write('\n✅ Datos de ejemplo creados exitosamente')
