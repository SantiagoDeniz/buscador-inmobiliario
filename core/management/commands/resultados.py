from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from typing import List

from core.models import ResultadoBusqueda


class Command(BaseCommand):
    help = 'Listar y borrar Resultados de Búsqueda con filtros. Soporta dry-run y confirmación.'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='Listar resultados (por defecto).')
        parser.add_argument('--delete', action='store_true', help='Borrar resultados coincidentes.')
        parser.add_argument('--all', action='store_true', help='Operar sobre TODOS los resultados.')

        parser.add_argument('--ids', type=str, help='Lista de IDs separadas por coma.')
        parser.add_argument('--busqueda-ids', type=str, help='IDs de búsquedas separados por coma.')
        parser.add_argument('--propiedad-ids', type=str, help='IDs de propiedades separados por coma.')
        parser.add_argument('--coincide', type=str, choices=['true', 'false'], help='Filtrar por coincide.')
        parser.add_argument('--older-than', type=int, help='Más antiguos que N días (por created_at).')

        parser.add_argument('--limit', type=int, default=50, help='Límite de filas a listar (0 = sin límite).')
        parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se borraría sin ejecutar cambios.')
        parser.add_argument('--noinput', action='store_true', help='No pedir confirmación.')

    def build_queryset(self, options):
        qs = ResultadoBusqueda.objects.all()
        filtros_aplicados = bool(options.get('all'))

        if options.get('ids'):
            filtros_aplicados = True
            id_list: List[str] = [s.strip() for s in options['ids'].split(',') if s.strip()]
            qs = qs.filter(id__in=id_list)

        if options.get('busqueda_ids'):
            filtros_aplicados = True
            bid_list: List[str] = [s.strip() for s in options['busqueda_ids'].split(',') if s.strip()]
            qs = qs.filter(busqueda_id__in=bid_list)

        if options.get('propiedad_ids'):
            filtros_aplicados = True
            pid_list: List[str] = [s.strip() for s in options['propiedad_ids'].split(',') if s.strip()]
            qs = qs.filter(propiedad_id__in=pid_list)

        if options.get('coincide'):
            filtros_aplicados = True
            val = options['coincide'].lower() == 'true'
            qs = qs.filter(coincide=val)

        if options.get('older_than') is not None:
            filtros_aplicados = True
            limite = timezone.now() - timedelta(days=int(options['older_than']))
            qs = qs.filter(created_at__lt=limite)

        return qs, filtros_aplicados

    def handle(self, *args, **options):
        do_list = options['list'] or not options['delete']
        do_delete = options['delete']

        qs, filtros_aplicados = self.build_queryset(options)
        if not filtros_aplicados:
            self.stdout.write(self.style.WARNING('Sin filtros: operando sobre TODOS los resultados.'))

        total = qs.distinct().count()
        self.stdout.write(f'Resultados coincidentes: {total}')

        if do_list:
            limite = int(options['limit'] or 50)
            self.stdout.write('\nListado (máx {0}):'.format('SIN LÍMITE' if limite <= 0 else limite))
            iterable = qs.order_by('-id') if limite <= 0 else qs.order_by('-id')[:limite]
            for r in iterable:
                self.stdout.write(f'  - {r.id} | busqueda={r.busqueda_id} | propiedad={r.propiedad_id} | coincide={r.coincide} | {r.created_at.isoformat()}')

        if not do_delete:
            return

        if total == 0:
            self.stdout.write('Nada para borrar.')
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run: no se borrará nada.'))
            return

        if not options['noinput']:
            confirm = input('¿Confirmas el borrado de estos resultados? Escribe "yes" para continuar: ').strip().lower()
            if confirm != 'yes':
                self.stdout.write(self.style.WARNING('Operación cancelada.'))
                return

        with transaction.atomic():
            borradas = qs.delete()

        self.stdout.write(self.style.SUCCESS('✔ Borrado completado.'))
        self.stdout.write(f'   Detalle delete(): {borradas}')
