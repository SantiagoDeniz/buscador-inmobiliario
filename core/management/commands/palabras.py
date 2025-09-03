from django.core.management.base import BaseCommand
from django.db import transaction
from typing import List

from core.models import PalabraClave, BusquedaPalabraClave


class Command(BaseCommand):
    help = 'Listar y borrar Palabras Clave con filtros. Protege si están asociadas a Búsquedas salvo --force-cascade.'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='Listar palabras (por defecto).')
        parser.add_argument('--delete', action='store_true', help='Borrar palabras coincidentes.')
        parser.add_argument('--all', action='store_true', help='Operar sobre TODAS las palabras.')

        parser.add_argument('--ids', type=str, help='Lista de IDs separadas por coma.')
        parser.add_argument('--texto-contains', type=str, help='Texto contenido en la palabra.')
        parser.add_argument('--idioma', type=str, help='Filtrar por idioma (ej. es).')

        parser.add_argument('--limit', type=int, default=50, help='Límite de filas a listar (0 = sin límite).')
        parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se borraría sin ejecutar cambios.')
        parser.add_argument('--noinput', action='store_true', help='No pedir confirmación.')
        parser.add_argument('--force-cascade', action='store_true', help='Permitir borrado en cascada aunque haya asociaciones.')

    def build_queryset(self, options):
        qs = PalabraClave.objects.all()
        filtros_aplicados = bool(options.get('all'))

        if options.get('ids'):
            filtros_aplicados = True
            id_list: List[str] = [s.strip() for s in options['ids'].split(',') if s.strip()]
            qs = qs.filter(id__in=id_list)

        if options.get('texto_contains'):
            filtros_aplicados = True
            qs = qs.filter(texto__icontains=options['texto_contains'])

        if options.get('idioma'):
            filtros_aplicados = True
            qs = qs.filter(idioma=options['idioma'])

        return qs, filtros_aplicados

    def handle(self, *args, **options):
        do_list = options['list'] or not options['delete']
        do_delete = options['delete']

        qs, filtros_aplicados = self.build_queryset(options)
        if not filtros_aplicados:
            self.stdout.write(self.style.WARNING('Sin filtros: operando sobre TODAS las palabras.'))

        total = qs.distinct().count()
        self.stdout.write(f'Palabras coincidentes: {total}')

        if do_list:
            limite = int(options['limit'] or 50)
            self.stdout.write('\nListado (máx {0}):'.format('SIN LÍMITE' if limite <= 0 else limite))
            iterable = qs.order_by('texto') if limite <= 0 else qs.order_by('texto')[:limite]
            for p in iterable:
                self.stdout.write(f'  - {p.id} | {p.texto} | idioma={p.idioma}')

        if not do_delete:
            return

        if total == 0:
            self.stdout.write('Nada para borrar.')
            return

        deps = BusquedaPalabraClave.objects.filter(palabra_clave__in=qs).count()
        if deps and not options['force_cascade']:
            self.stdout.write(self.style.ERROR(
                f'Hay {deps} asociaciones con búsquedas. Usa --force-cascade para permitir el borrado.'
            ))
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run: no se borrará nada.'))
            return

        if not options['noinput']:
            confirm = input('¿Confirmas el borrado de estas palabras? Escribe "yes" para continuar: ').strip().lower()
            if confirm != 'yes':
                self.stdout.write(self.style.WARNING('Operación cancelada.'))
                return

        with transaction.atomic():
            borradas = qs.delete()

        self.stdout.write(self.style.SUCCESS('✔ Borrado completado.'))
        self.stdout.write(f'   Detalle delete(): {borradas}')
