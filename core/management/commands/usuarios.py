from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from typing import List

from core.models import Usuario, Busqueda, ResultadoBusqueda


class Command(BaseCommand):
    help = 'Listar y borrar Usuarios con filtros. Soporta dry-run y confirmación. Protege borrado en cascada salvo --force-cascade.'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='Listar usuarios (por defecto).')
        parser.add_argument('--delete', action='store_true', help='Borrar usuarios coincidentes.')
        parser.add_argument('--all', action='store_true', help='Operar sobre TODOS los usuarios.')

        parser.add_argument('--ids', type=str, help='Lista de IDs separadas por coma.')
        parser.add_argument('--email-contains', type=str, help='Texto contenido en el email.')
        parser.add_argument('--name-contains', type=str, help='Texto contenido en el nombre.')
        parser.add_argument('--inmobiliaria-id', type=int, help='Filtrar por ID de inmobiliaria.')
        parser.add_argument('--older-than', type=int, help='Usuarios más antiguos que N días.')

        parser.add_argument('--limit', type=int, default=20, help='Límite de filas a listar (0 = sin límite).')
        parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se borraría sin ejecutar cambios.')
        parser.add_argument('--noinput', action='store_true', help='No pedir confirmación.')
        parser.add_argument('--force-cascade', action='store_true', help='Permitir borrado en cascada de búsquedas/resultados asociados.')

    def build_queryset(self, options):
        qs = Usuario.objects.all()
        filtros_aplicados = bool(options.get('all'))

        if options.get('ids'):
            filtros_aplicados = True
            id_list: List[str] = [s.strip() for s in options['ids'].split(',') if s.strip()]
            qs = qs.filter(id__in=id_list)

        if options.get('email_contains'):
            filtros_aplicados = True
            qs = qs.filter(email__icontains=options['email_contains'])

        if options.get('name_contains'):
            filtros_aplicados = True
            qs = qs.filter(nombre__icontains=options['name_contains'])

        if options.get('inmobiliaria_id') is not None:
            filtros_aplicados = True
            qs = qs.filter(inmobiliaria_id=int(options['inmobiliaria_id']))

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
            self.stdout.write(self.style.WARNING('Sin filtros: operando sobre TODOS los usuarios.'))

        total = qs.distinct().count()
        self.stdout.write(f'Usuarios coincidentes: {total}')

        if do_list:
            limite = int(options['limit'] or 20)
            self.stdout.write('\nListado (máx {0}):'.format('SIN LÍMITE' if limite <= 0 else limite))
            iterable = qs.order_by('-id') if limite <= 0 else qs.order_by('-id')[:limite]
            for u in iterable:
                created_str = u.created_at.isoformat() if getattr(u, 'created_at', None) else ''
                self.stdout.write(f'  - {u.id} | {u.nombre} | {u.email} | inmob={u.inmobiliaria_id} | {created_str}')

        if not do_delete:
            return

        if total == 0:
            self.stdout.write('Nada para borrar.')
            return

        # Protecciones: contar dependencias
        dep_busquedas = Busqueda.objects.filter(usuario__in=qs).count()
        dep_resultados = ResultadoBusqueda.objects.filter(busqueda__usuario__in=qs).count()
        if (dep_busquedas or dep_resultados) and not options['force_cascade']:
            self.stdout.write(self.style.ERROR(
                f'Hay dependencias: busquedas={dep_busquedas}, resultados={dep_resultados}. Usa --force-cascade para continuar.'
            ))
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run: no se borrará nada.'))
            return

        if not options['noinput']:
            confirm = input('¿Confirmas el borrado de estos usuarios? Escribe "yes" para continuar: ').strip().lower()
            if confirm != 'yes':
                self.stdout.write(self.style.WARNING('Operación cancelada.'))
                return

        with transaction.atomic():
            borradas = qs.delete()

        self.stdout.write(self.style.SUCCESS('✔ Borrado completado.'))
        self.stdout.write(f'   Detalle delete(): {borradas}')
