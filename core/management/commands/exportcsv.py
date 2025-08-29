from django.core.management.base import BaseCommand
from django.conf import settings
import os
from core.export_utils import export_all, prune_old_exports


class Command(BaseCommand):
    help = "Exporta todas las tablas y modelos a CSV en ./exports/(latest y con timestamp)."

    def add_arguments(self, parser):
        parser.add_argument('--out', default='exports', help='Directorio base de salida')

    def handle(self, *args, **options):
        out_dir = options['out']
        base_dir = os.path.abspath(os.path.join(settings.BASE_DIR, out_dir))
        self.stdout.write(f"Exportando a: {base_dir}")
        export_all(base_dir)
        # Eliminar snapshots antiguos (conservar 0 para evitar acumulación)
        prune_old_exports(base_dir, keep=0)
        self.stdout.write(self.style.SUCCESS("Exportación completada"))
