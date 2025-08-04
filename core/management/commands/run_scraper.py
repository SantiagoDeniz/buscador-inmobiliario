from django.core.management.base import BaseCommand
from core.scraper import run_scraper

class Command(BaseCommand):
    help = 'Ejecuta el scraper de MercadoLibre para poblar la base de datos'

    def add_arguments(self, parser):
        # Límite de 42 páginas por defecto
        parser.add_argument('--paginas', type=int, default=42, help='Número máximo de páginas a scrapear (límite de ML: 42).')
        parser.add_argument('--tipo', type=str, default='inmuebles', help='Tipo (inmuebles, casas, apartamentos).')
        parser.add_argument('--operacion', type=str, default='venta', help='Operación (venta, alquiler).')
        parser.add_argument('--ubicacion', type=str, default='montevideo', help='Departamento.')
        # Nuevos argumentos de precio
        parser.add_argument('--precio-min', type=int, default=None, help='Precio mínimo en USD.')
        parser.add_argument('--precio-max', type=int, default=None, help='Precio máximo en USD.')
        
        parser.add_argument('--workers', type=int, default=5, help='Número de hilos concurrentes.')

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