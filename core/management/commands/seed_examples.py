from django.core.management.base import BaseCommand
from django.db import transaction, connection
from psycopg2.extras import Json
from django.utils import timezone
from core.models import Plataforma, Propiedad, Busqueda, ResultadoBusqueda, Usuario, Inmobiliaria
import uuid


class Command(BaseCommand):
    help = 'Poblar datos de ejemplo: plataformas, propiedades, búsquedas y resultados mínimos.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Cantidad de propiedades de ejemplo (por defecto 5).')

    def handle(self, *args, **options):
        count = int(options['count'] or 5)

        with transaction.atomic():
            # Asegurar plataforma base
            pl, _ = Plataforma.objects.get_or_create(nombre='MercadoLibre', defaults={
                'descripcion': 'Ejemplo',
                'url': 'https://www.mercadolibre.com.uy',
            })

            # Asegurar un usuario para las búsquedas (reutiliza el Default si existe)
            inmob, _ = Inmobiliaria.objects.get_or_create(nombre='Inmobiliaria Default', defaults={'plan': 'basico'})
            user, _ = Usuario.objects.get_or_create(email='default@example.com', defaults={
                'nombre': 'Usuario Default',
                'password_hash': '!',
                'inmobiliaria': inmob,
            })

            # Crear propiedades
            props = []
            for i in range(count):
                p, _ = Propiedad.objects.get_or_create(
                    url=f'https://example.com/prop{uuid.uuid4().hex[:8]}',
                    defaults={
                        'titulo': f'Propiedad de ejemplo #{i+1}',
                        'descripcion': 'Descripción de ejemplo',
                        'metadata': {'ambientes': 3+i, 'moneda': 'USD', 'precio': 100000 + i*1000},
                        'plataforma': pl,
                    }
                )
                props.append(p)

            # Crear una búsqueda y resultados asociados a las propiedades
            b = Busqueda.objects.create(
                nombre_busqueda='Busqueda de ejemplo',
                texto_original='apartamento 2 dormitorios pocitos',
                filtros={'tipo': 'apartamento', 'operacion': 'venta'},
                guardado=True,
                usuario=user,
            )
            # Insertar resultados respetando columnas adicionales del esquema (ej. seen_count)
            now = timezone.now()
            with connection.cursor() as cur:
                # Detectar columnas disponibles en la tabla
                cols_info = connection.introspection.get_table_description(cur, 'resultado_busqueda')
                col_names = {c.name for c in cols_info}

                base_cols = ['busqueda_id', 'propiedad_id', 'coincide', 'metadata', 'created_at']
                base_vals = lambda pid: [str(b.id), pid, True, Json({'fuente': 'seed'}), now]

                extra_cols = []
                extra_vals = []
                if 'seen_count' in col_names:
                    extra_cols.append('seen_count')
                    extra_vals.append(0)
                if 'seen_last_at' in col_names:
                    extra_cols.append('seen_last_at')
                    extra_vals.append(now)

                all_cols = base_cols + extra_cols
                placeholders = ', '.join(['%s'] * len(all_cols))
                cols_sql = ', '.join(all_cols)
                sql = f"""
                    INSERT INTO resultado_busqueda ({cols_sql})
                    VALUES ({placeholders})
                    ON CONFLICT (busqueda_id, propiedad_id) DO NOTHING
                """

                for p in props:
                    values = base_vals(p.id) + list(extra_vals)
                    cur.execute(sql, values)

        self.stdout.write(self.style.SUCCESS(f'✔ Seed completado: {len(props)} propiedades, 1 búsqueda y resultados creados.'))
