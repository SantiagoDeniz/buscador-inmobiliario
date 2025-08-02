# Reemplaza el contenido de core/management/commands/run_scraper.py

from django.core.management.base import BaseCommand
from core.scraper import run_scraper

class Command(BaseCommand):
    help = 'Ejecuta el scraper de MercadoLibre para poblar la base de datos'

    def add_arguments(self, parser):
        # El usuario PUEDE especificar un máximo, si no, el scraper detectará el total.
        parser.add_argument('--paginas', type=int, default=None, help='(Opcional) Número máximo de páginas a scrapear.')
        parser.add_argument('--tipo', type=str, default='apartamentos', help='Tipo de inmueble (ej: apartamentos, casas).')
        parser.add_argument('--operacion', type=str, default='venta', help='Tipo de operación (venta, alquiler).')
        parser.add_argument('--ubicacion', type=str, default='montevideo', help='Departamento a scrapear.')
        parser.add_argument('--workers', type=int, default=5, help='Número de hilos concurrentes.')

    def handle(self, *args, **kwargs):
        paginas = kwargs['paginas']
        tipo = kwargs['tipo']
        operacion = kwargs['operacion']
        ubicacion = kwargs['ubicacion']
        workers = kwargs['workers']

        if paginas:
            self.stdout.write(self.style.SUCCESS(f"Iniciando scrapeo de MÁXIMO {paginas} páginas de {tipo} en {operacion} en {ubicacion}..."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Iniciando scrapeo de TODAS las páginas de {tipo} en {operacion} en {ubicacion}..."))
        
        try:
            # Pasamos los argumentos con los nombres correctos que espera la función
            run_scraper(
                max_paginas=paginas, 
                tipo_inmueble=tipo, 
                operacion=operacion, 
                ubicacion=ubicacion,
                workers_fase1=workers,
                workers_fase2=workers
            )
            self.stdout.write(self.style.SUCCESS('¡Proceso de scrapeo completado!'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ocurrió un error grave: {e}'))