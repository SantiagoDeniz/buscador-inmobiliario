from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from typing import List

from core.models import Busqueda, ResultadoBusqueda, Propiedad


class Command(BaseCommand):
    help = 'Borra búsquedas y sus datos relacionados (resultados, relaciones). Opcionalmente elimina propiedades huérfanas.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Borrar TODAS las búsquedas.')
        parser.add_argument('--ids', type=str, help='Lista de IDs de búsquedas separadas por coma.')
        parser.add_argument('--name-contains', type=str, help='Texto contenido en nombre_busqueda.')
        parser.add_argument('--older-than', type=int, help='Borrar búsquedas más antiguas que N días.')
        parser.add_argument('--list', action='store_true', help='Listar búsquedas coincidentes y salir (no borra).')
        parser.add_argument('--delete-orphan-properties', action='store_true',
                            help='Eliminar propiedades que queden sin resultados luego del borrado.')
        parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se borraría sin ejecutar cambios.')
        parser.add_argument('--noinput', action='store_true', help='No pedir confirmación.')

    def handle(self, *args, **options):
        qs = Busqueda.objects.all()

        if not options['all']:
            filtros_aplicados = False

            if options.get('ids'):
                filtros_aplicados = True
                id_list: List[str] = [s.strip() for s in options['ids'].split(',') if s.strip()]
                qs = qs.filter(id__in=id_list)

            if options.get('name_contains'):
                filtros_aplicados = True
                qs = qs.filter(nombre_busqueda__icontains=options['name_contains'])

            if options.get('older_than') is not None:
                filtros_aplicados = True
                limite = timezone.now() - timedelta(days=int(options['older_than']))
                qs = qs.filter(created_at__lt=limite)

            if not filtros_aplicados:
                self.stdout.write(self.style.ERROR('Debes especificar al menos un filtro o usar --all.'))
                return

        total_busquedas = qs.count()
        if total_busquedas == 0:
            self.stdout.write('No se encontraron búsquedas para borrar.')
            return

        # Calcular impactos
        total_resultados = ResultadoBusqueda.objects.filter(busqueda__in=qs).count()

        # Propiedades potencialmente afectadas (las relacionadas a estas búsquedas)
        prop_ids_afectadas = set(
            Propiedad.objects.filter(resultadobusqueda__busqueda__in=qs)
            .values_list('id', flat=True).distinct()
        )

        orphan_prop_ids = set()
        if options['delete_orphan_properties'] and prop_ids_afectadas:
            # Propiedades que también aparecen en resultados de búsquedas QUE NO están en la selección
            restantes_ids_busqueda = set(
                Busqueda.objects.exclude(id__in=list(qs.values_list('id', flat=True)))
                .values_list('id', flat=True)
            )
            if restantes_ids_busqueda:
                prop_ids_con_otras_busquedas = set(
                    Propiedad.objects.filter(resultadobusqueda__busqueda__in=restantes_ids_busqueda)
                    .values_list('id', flat=True).distinct()
                )
            else:
                prop_ids_con_otras_busquedas = set()

            orphan_prop_ids = prop_ids_afectadas - prop_ids_con_otras_busquedas

        # Resumen
        self.stdout.write('Resumen de borrado:')
        self.stdout.write(f'  • Búsquedas a borrar: {total_busquedas}')
        self.stdout.write(f'  • Resultados a borrar (cascade): {total_resultados}')
        self.stdout.write(f'  • Propiedades afectadas (relacionadas): {len(prop_ids_afectadas)}')
        if options['delete_orphan_properties']:
            self.stdout.write(f'  • Propiedades huérfanas a borrar: {len(orphan_prop_ids)}')
        else:
            self.stdout.write('  • Propiedades huérfanas a borrar: 0 (usa --delete-orphan-properties para incluirlas)')

        # Modo listado
        if options['list']:
            # Conteo de resultados por búsqueda
            res_counts = {
                row['busqueda']: row['c']
                for row in ResultadoBusqueda.objects.filter(busqueda__in=qs)
                .values('busqueda').annotate(c=Count('id'))
            }
            self.stdout.write('\nListado de búsquedas:')
            for b in qs.order_by('-created_at'):
                nombre = b.nombre_busqueda or '(sin nombre)'
                fecha = b.created_at.isoformat() if b.created_at else ''
                self.stdout.write(f"  - {b.id} | {nombre} | {fecha} | resultados={res_counts.get(b.id, 0)}")
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run activo: no se aplicaron cambios.'))
            return

        if not options['noinput']:
            confirm = input('¿Confirmas el borrado? Escribe "yes" para continuar: ').strip().lower()
            if confirm != 'yes':
                self.stdout.write(self.style.WARNING('Operación cancelada.'))
                return

        with transaction.atomic():
            # Borrar búsquedas (cascade borra ResultadoBusqueda y relaciones intermedias)
            borradas = qs.delete()
            # Borrar propiedades huérfanas si corresponde
            props_borradas = 0
            if orphan_prop_ids:
                props_borradas, _ = Propiedad.objects.filter(id__in=list(orphan_prop_ids)).delete()

        self.stdout.write(self.style.SUCCESS('✔ Borrado completado.'))
        self.stdout.write(f'   Detalle delete(): {borradas}')
        if orphan_prop_ids:
            self.stdout.write(f'   Propiedades huérfanas borradas: {props_borradas}')
