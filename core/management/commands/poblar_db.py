from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    Busqueda, PalabraClave, Propiedad, ResultadoBusqueda, 
    PalabraClavePropiedad
)
import json


class Command(BaseCommand):
    help = 'Limpia y puebla la base de datos con búsquedas y propiedades de ejemplo'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando limpieza y población de la base de datos...")
        
        try:
            with transaction.atomic():
                # Limpiar datos
                self.stdout.write("🧹 Limpiando datos existentes...")
                PalabraClavePropiedad.objects.all().delete()
                ResultadoBusqueda.objects.all().delete()
                Propiedad.objects.all().delete()
                Busqueda.objects.all().delete()
                PalabraClave.objects.all().delete()
                self.stdout.write("   ✅ Datos limpiados")
                
                # Crear palabras clave
                self.stdout.write("🔤 Creando palabras clave...")
                keywords_data = [
                    {'texto': 'apartamento', 'sinonimos': '["apto", "departamento", "depto", "piso"]'},
                    {'texto': 'casa', 'sinonimos': '["vivienda", "hogar", "residencia", "chalet"]'},
                    {'texto': 'garage', 'sinonimos': '["garaje", "cochera", "estacionamiento"]'},
                    {'texto': 'piscina', 'sinonimos': '["pileta", "alberca", "natatorio"]'},
                    {'texto': 'terraza', 'sinonimos': '["balcon", "balcón", "azotea", "deck"]'},
                    {'texto': 'amueblado', 'sinonimos': '["muebles", "mobiliario", "equipado"]'},
                    {'texto': 'seguridad', 'sinonimos': '["vigilancia", "portero", "alarma"]'},
                ]
                
                for data in keywords_data:
                    PalabraClave.objects.create(**data)
                    self.stdout.write(f"   ✅ Creada: {data['texto']}")
                
                # Crear búsquedas
                self.stdout.write("🔍 Creando búsquedas de ejemplo...")
                busquedas_data = [
                    {
                        'nombre_busqueda': 'Apartamento Pocitos - Alquiler USD',
                        'texto_original': 'apartamento pocitos alquiler garage terraza vista mar',
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
                        'guardado': True
                    },
                    {
                        'nombre_busqueda': 'Casa Carrasco - Venta Premium',
                        'texto_original': 'casa carrasco venta piscina jardin garage seguridad',
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
                        'guardado': True
                    },
                    {
                        'nombre_busqueda': 'Apartamento Centro - Alquiler Pesos',
                        'texto_original': 'apartamento centro alquiler amueblado profesional',
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
                        'guardado': True
                    },
                    {
                        'nombre_busqueda': 'Casa Punta del Este - Vista Mar',
                        'texto_original': 'casa punta del este venta vista mar piscina terraza',
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
                        'guardado': True
                    },
                    {
                        'nombre_busqueda': 'Apartamento Cordón - Inversión',
                        'texto_original': 'apartamento cordon inversion alquiler zona comercial',
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
                        'guardado': True
                    },
                    {
                        'nombre_busqueda': 'Búsqueda Temporal - No Guardada',
                        'texto_original': 'apartamento alquiler economico cualquier zona',
                        'filtros': {
                            'tipo': 'apartamento',
                            'operacion': 'alquiler',
                            'departamento': 'Montevideo',
                            'moneda': 'USD',
                            'precio_max': 1000
                        },
                        'guardado': False
                    }
                ]
                
                for data in busquedas_data:
                    busqueda = Busqueda.objects.create(**data)
                    estado = "💾 Guardada" if data['guardado'] else "📝 Temporal"
                    ciudad = data['filtros'].get('ciudad', 'Sin especificar')
                    precio_max = data['filtros'].get('precio_max', 0)
                    moneda = data['filtros'].get('moneda', '')
                    self.stdout.write(f"   ✅ {estado}: {data['nombre_busqueda']}")
                    self.stdout.write(f"      📍 {ciudad} - Max: {moneda} {precio_max:,}")
                
                # Obtener o crear plataforma MercadoLibre
                try:
                    from core.models import Plataforma
                    plataforma_ml, created = Plataforma.objects.get_or_create(
                        nombre='MercadoLibre',
                        defaults={'descripcion': 'Portal de clasificados', 'url': 'https://mercadolibre.com.uy'}
                    )
                except:
                    # Si no existe la tabla plataforma, crear una referencia básica
                    plataforma_ml = None
                
                # Crear propiedades de ejemplo
                self.stdout.write("🏠 Creando propiedades de ejemplo...")
                propiedades_data = [
                    {
                        'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo1-pocitos',
                        'titulo': 'Apartamento en Pocitos con Vista al Mar',
                        'descripcion': 'Hermoso apartamento de 2 dormitorios en Pocitos con vista panorámica al mar. Cuenta con garage, terraza amplia y amenities completos. Excelente ubicación a 2 cuadras de la rambla.',
                        'metadata': {
                            'precio': 1200.00,
                            'moneda': 'USD',
                            'ubicacion': 'Pocitos, Montevideo',
                            'dormitorios': 2,
                            'banos': 2,
                            'metros_cuadrados': 85.0,
                            'caracteristicas': {"garage": True, "terraza": True, "vista_mar": True, "amenities": True}
                        },
                        'plataforma': plataforma_ml
                    },
                    {
                        'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo2-carrasco',
                        'titulo': 'Casa en Carrasco con Piscina y Jardín',
                        'descripcion': 'Espectacular casa familiar en Carrasco Norte. 4 dormitorios, 3 baños, piscina climatizada, amplio jardín con parrillero y garage para 2 autos. Zona residencial exclusiva.',
                        'metadata': {
                            'precio': 280000.00,
                            'moneda': 'USD',
                            'ubicacion': 'Carrasco, Montevideo',
                            'dormitorios': 4,
                            'banos': 3,
                            'metros_cuadrados': 250.0,
                            'caracteristicas': {"piscina": True, "jardin": True, "garage": True, "parrillero": True, "seguridad": True}
                        },
                        'plataforma': plataforma_ml
                    },
                    {
                        'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo3-centro',
                        'titulo': 'Apartamento Amueblado en Centro',
                        'descripcion': 'Apartamento completamente amueblado en el centro de Montevideo. Ideal para profesionales. Incluye todos los electrodomésticos, internet fibra óptica y calefacción central.',
                        'metadata': {
                            'precio': 35000.00,
                            'moneda': 'UYU',
                            'ubicacion': 'Centro, Montevideo',
                            'dormitorios': 1,
                            'banos': 1,
                            'metros_cuadrados': 45.0,
                            'caracteristicas': {"amueblado": True, "electrodomesticos": True, "internet": True, "calefaccion": True}
                        },
                        'plataforma': plataforma_ml
                    },
                    {
                        'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo4-puntadeleste',
                        'titulo': 'Casa en Punta del Este con Vista al Mar',
                        'descripcion': 'Hermosa casa a 2 cuadras de Playa Brava. 3 dormitorios, 2 baños, piscina, terraza con deck y vista parcial al mar. Ideal para vacaciones o inversión.',
                        'metadata': {
                            'precio': 350000.00,
                            'moneda': 'USD',
                            'ubicacion': 'Punta del Este, Maldonado',
                            'dormitorios': 3,
                            'banos': 2,
                            'metros_cuadrados': 180.0,
                            'caracteristicas': {"piscina": True, "terraza": True, "vista_mar": True, "cerca_playa": True}
                        },
                        'plataforma': plataforma_ml
                    },
                    {
                        'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo5-cordon',
                        'titulo': 'Apartamento de Inversión en Cordón',
                        'descripcion': 'Excelente oportunidad de inversión. Apartamento en muy buen estado en zona de alta demanda para alquiler. Cerca de facultades y centros comerciales.',
                        'metadata': {
                            'precio': 120000.00,
                            'moneda': 'USD',
                            'ubicacion': 'Cordón, Montevideo',
                            'dormitorios': 2,
                            'banos': 1,
                            'metros_cuadrados': 60.0,
                            'caracteristicas': {"inversion": True, "zona_comercial": True, "transporte": True, "estudiantes": True}
                        },
                        'plataforma': plataforma_ml
                    },
                    {
                        'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo6-blanqueada',
                        'titulo': 'Casa Familiar en La Blanqueada',
                        'descripcion': 'Casa de 3 dormitorios en La Blanqueada, con patio, garage y muy buena iluminación. Ideal para familia, en zona tranquila con todos los servicios.',
                        'metadata': {
                            'precio': 180000.00,
                            'moneda': 'USD',
                            'ubicacion': 'La Blanqueada, Montevideo',
                            'dormitorios': 3,
                            'banos': 2,
                            'metros_cuadrados': 120.0,
                            'caracteristicas': {"garage": True, "patio": True, "familia": True, "zona_tranquila": True}
                        },
                        'plataforma': plataforma_ml
                    }
                ]
                
                for data in propiedades_data:
                    propiedad = Propiedad.objects.create(**data)
                    metadata = data['metadata']
                    self.stdout.write(f"   ✅ {data['titulo']}")
                    self.stdout.write(f"      📍 {metadata['ubicacion']} - {metadata['dormitorios']} dorm, {metadata['banos']} baños")
                    self.stdout.write(f"      💰 {metadata['moneda']} {metadata['precio']:,.0f} - {metadata['metros_cuadrados']} m²")
                
                # Mostrar estadísticas finales
                self.stdout.write("\n📊 Estadísticas de la base de datos:")
                self.stdout.write(f"   🔤 Palabras clave: {PalabraClave.objects.count()}")
                self.stdout.write(f"   🔍 Búsquedas guardadas: {Busqueda.objects.filter(guardado=True).count()}")
                self.stdout.write(f"   📝 Búsquedas temporales: {Busqueda.objects.filter(guardado=False).count()}")
                self.stdout.write(f"   🏠 Propiedades: {Propiedad.objects.count()}")
                self.stdout.write(f"   🔗 Relaciones keyword-propiedad: {PalabraClavePropiedad.objects.count()}")
                
            self.stdout.write(self.style.SUCCESS("\n✅ ¡Base de datos limpiada y poblada exitosamente!"))
            self.stdout.write("💡 Usa 'python ver_datos_tabla.py --list' para ver el estado actual")
            self.stdout.write("💡 Usa 'python ver_datos_tabla.py busqueda' para ver las búsquedas")
            self.stdout.write("💡 Usa 'python ver_datos_tabla.py propiedad' para ver las propiedades")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error durante la ejecución: {e}"))
            import traceback
            traceback.print_exc()
            raise e
