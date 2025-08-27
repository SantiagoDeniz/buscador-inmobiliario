# core/management/commands/enriquecer_datos.py
from django.core.management.base import BaseCommand
from core.models import Propiedad
from core.scraper import scrape_detalle_con_requests # Reutilizamos nuestra función de scrapeo de detalles
import os
import time

class Command(BaseCommand):
    help = 'Recorre las propiedades existentes en la BD y llena los campos que estén vacíos.'

    def handle(self, *args, **kwargs):
        API_KEY = os.getenv('SCRAPER_API_KEY')
        if not API_KEY:
            self.stderr.write(self.style.ERROR('La variable de entorno SCRAPER_API_KEY no está definida.'))
            return

        # Buscamos propiedades que necesiten ser actualizadas
        # (aquellas donde el campo 'departamento' esté vacío, por ejemplo)
        propiedades_a_enriquecer = Propiedad.objects.filter(departamento='')
        total = propiedades_a_enriquecer.count()
        self.stdout.write(self.style.SUCCESS(f'Se encontraron {total} propiedades para enriquecer.'))

        for i, propiedad in enumerate(propiedades_a_enriquecer):
            self.stdout.write(f'Procesando {i+1}/{total}: {propiedad.titulo[:50]}...')
            
            # Usamos la misma función que el scraper principal
            datos_nuevos = scrape_detalle_con_requests(propiedad.url, API_KEY)
            
            if datos_nuevos:
                # Actualizamos el objeto 'propiedad' con los nuevos datos
                propiedad.departamento = datos_nuevos.get('departamento', '')
                propiedad.ciudad_barrio = datos_nuevos.get('ciudad_barrio', '')
                propiedad.dormitorios = datos_nuevos.get('dormitorios')
                propiedad.banos = datos_nuevos.get('banos')
                propiedad.superficie_total = datos_nuevos.get('superficie_total')
                propiedad.superficie_cubierta = datos_nuevos.get('superficie_cubierta')
                propiedad.cocheras = datos_nuevos.get('cocheras')
                propiedad.antiguedad = datos_nuevos.get('antiguedad', '')
                # También actualizamos campos que podrían haber cambiado
                propiedad.descripcion = datos_nuevos.get('descripcion', '')
                propiedad.caracteristicas = datos_nuevos.get('caracteristicas', '')
                
                propiedad.save() # Guardamos los cambios en la base de datos
                self.stdout.write(self.style.SUCCESS('  -> ¡Datos enriquecidos y guardados!'))
            else:
                self.stderr.write(self.style.ERROR('  -> Falló la obtención de detalles.'))
            
            time.sleep(1) # Pausa cortés para no saturar la API

        self.stdout.write(self.style.SUCCESS('Proceso de enriquecimiento finalizado.'))