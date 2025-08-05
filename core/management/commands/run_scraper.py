# Reemplaza el archivo completo en core/management/commands/run_scraper.py

from django.core.management.base import BaseCommand
from core.scraper import run_scraper

class Command(BaseCommand):
    help = 'Ejecuta el scraper de MercadoLibre para poblar la base de datos'

    def add_arguments(self, parser):
        parser.add_argument('--paginas', type=int, default=42)
        # CORRECCIÓN: default=None es la forma correcta de manejar un argumento opcional
        parser.add_argument('--tipo', type=str, default=None, help='(casas, apartamentos). Omitir para todos los inmuebles.')
        parser.add_argument('--operacion', type=str, default='venta')
        parser.add_argument('--ubicacion', type=str, default='montevideo')
        parser.add_argument('--precio-min', type=int, default=None)
        parser.add_argument('--precio-max', type=int, default=None)
        parser.add_argument('--workers', type=int, default=5)
        parser.add_argument('--limpiar', action='store_true', help='Borra las propiedades existentes para esta búsqueda.')

    def handle(self, *args, **kwargs):
        paginas = kwargs['paginas']
        tipo = kwargs['tipo']
        operacion = kwargs['operacion']
        ubicacion = kwargs['ubicacion']
        precio_min = kwargs['precio_min']
        precio_max = kwargs['precio_max']
        workers = kwargs['workers']

        self.stdout.write(self.style.SUCCESS(f"Iniciando scrapeo de MÁXIMO {paginas} páginas..."))
        
        try:
            run_scraper(
                max_paginas=paginas, 
                tipo_inmueble=tipo, 
                operacion=operacion, 
                ubicacion=ubicacion,
                precio_min=precio_min,
                precio_max=precio_max,
                workers_fase1=workers,
                workers_fase2=workers
            )
            self.stdout.write(self.style.SUCCESS('¡Proceso de scrapeo completado!'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ocurrió un error grave: {e}'))