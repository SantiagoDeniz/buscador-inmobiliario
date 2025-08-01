# core/management/commands/run_scraper.py

from django.core.management.base import BaseCommand
from core.scraper import run_scraper # Importamos nuestra función principal del scraper

class Command(BaseCommand):
    help = 'Ejecuta el scraper de MercadoLibre para poblar la base de datos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando el proceso de scrapeo...'))
        try:
            run_scraper()
            self.stdout.write(self.style.SUCCESS('¡Proceso de scrapeo completado exitosamente!'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ocurrió un error durante el scrapeo: {e}'))