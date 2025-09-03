from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from typing import List

from core.models import Propiedad


class Command(BaseCommand):
    help = 'Listar y borrar Propiedades con filtros. Soporta dry-run y confirmación.'

    def add_arguments(self, parser):
        # Modo
        parser.add_argument('--list', action='store_true', help='Listar propiedades coincidentes (por defecto).')
        parser.add_argument('--delete', action='store_true', help='Borrar propiedades coincidentes.')
        parser.add_argument('--all', action='store_true', help='Operar sobre TODAS las propiedades.')

        # Filtros
        parser.add_argument('--ids', type=str, help='Lista de IDs separadas por coma.')
        parser.add_argument('--url-contains', type=str, help='Texto contenido en la URL.')
        parser.add_argument('--title-contains', type=str, help='Texto contenido en el título.')
        parser.add_argument('--older-than', type=int, help='Propiedades más antiguas que N días.')
        parser.add_argument('--orphan-only', action='store_true', help='Solo propiedades sin resultados asociados.')

        # Salida/seguridad
        parser.add_argument('--limit', type=int, default=20, help='Límite de filas a listar (por defecto 20).')
        parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se borraría sin ejecutar cambios.')
        parser.add_argument('--noinput', action='store_true', help='No pedir confirmación.')

    def build_queryset(self, options):
        qs = Propiedad.objects.all()

        filtros_aplicados = bool(options.get('all'))
        if options.get('ids'):
            filtros_aplicados = True
            id_list: List[str] = [s.strip() for s in options['ids'].split(',') if s.strip()]
            qs = qs.filter(id__in=id_list)

        if options.get('url_contains'):
            filtros_aplicados = True
            qs = qs.filter(url__icontains=options['url_contains'])

        if options.get('title_contains'):
            filtros_aplicados = True
            qs = qs.filter(titulo__icontains=options['title_contains'])

        if options.get('older_than') is not None:
            filtros_aplicados = True
            limite = timezone.now() - timedelta(days=int(options['older_than']))
            # Intenta usar created_at si existe, si no, updated_at
            try:
                qs.model._meta.get_field('created_at')
                qs = qs.filter(created_at__lt=limite)
            except Exception:
                try:
                    qs.model._meta.get_field('updated_at')
                    qs = qs.filter(updated_at__lt=limite)
                except Exception:
                    pass

        if options.get('orphan_only'):
            filtros_aplicados = True
            qs = qs.filter(resultadobusqueda__isnull=True)

        return qs, filtros_aplicados

    def handle(self, *args, **options):
        # Por defecto, si no se especifica modo, listar
        do_list = options['list'] or not options['delete']
        do_delete = options['delete']

        qs, filtros_aplicados = self.build_queryset(options)

        if not filtros_aplicados:
            self.stdout.write(self.style.WARNING('Sin filtros: operando sobre TODAS las propiedades.'))

        total = qs.distinct().count()
        self.stdout.write(f'Propiedades coincidentes: {total}')

        if do_list:
            limite = int(options['limit'] or 20)
            self.stdout.write('\nListado (máx {0}):'.format('SIN LÍMITE' if limite <= 0 else limite))
            iterable = qs.order_by('-id') if limite <= 0 else qs.order_by('-id')[:limite]
            for p in iterable:
                titulo = (p.titulo or '').strip()
                if len(titulo) > 60:
                    titulo = titulo[:57] + '...'
                created = getattr(p, 'created_at', None)
                created_str = created.isoformat() if created else ''
                self.stdout.write(f'  - {p.id} | {titulo} | {p.url} | {created_str}')

        if not do_delete:
            return

        if total == 0:
            self.stdout.write('Nada para borrar.')
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run: no se borrará nada.'))
            return

        if not options['noinput']:
            confirm = input('¿Confirmas el borrado de estas propiedades? Escribe "yes" para continuar: ').strip().lower()
            if confirm != 'yes':
                self.stdout.write(self.style.WARNING('Operación cancelada.'))
                return

        with transaction.atomic():
            borradas = qs.delete()

        self.stdout.write(self.style.SUCCESS('✔ Borrado completado.'))
        self.stdout.write(f'   Detalle delete(): {borradas}')
