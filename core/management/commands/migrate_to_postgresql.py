# core/management/commands/migrate_to_postgresql.py
"""
Comando para migrar datos de SQLite a PostgreSQL
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from django.conf import settings
import os
import sys


class Command(BaseCommand):
    help = 'Migra datos de SQLite a PostgreSQL'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-backup',
            action='store_true',
            help='Omitir backup de datos SQLite',
        )
        parser.add_argument(
            '--drop-tables',
            action='store_true',
            help='Eliminar tablas existentes en PostgreSQL',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🐘 Iniciando migración de SQLite a PostgreSQL')
        )
        
        # Verificar configuración
        if not self._verify_postgresql_config():
            return
        
        # Hacer backup de SQLite si se requiere
        if not options['skip_backup']:
            self._backup_sqlite()
        
        # Verificar conexión PostgreSQL
        if not self._test_postgresql_connection():
            return
        
        # Limpiar tablas si se requiere
        if options['drop_tables']:
            self._drop_postgresql_tables()
        
        # Aplicar migraciones
        self._apply_migrations()
        
        # Migrar datos
        self._migrate_data()
        
        # Verificar migración
        self._verify_migration()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Migración completada exitosamente')
        )
    
    def _verify_postgresql_config(self):
        """Verificar que PostgreSQL esté configurado"""
        database_engine = os.environ.get('DATABASE_ENGINE', 'sqlite')
        
        if database_engine != 'postgresql':
            self.stdout.write(
                self.style.ERROR(
                    '❌ DATABASE_ENGINE debe ser "postgresql" en .env'
                )
            )
            return False
        
        required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST']
        missing = [var for var in required_vars if not os.environ.get(var)]
        
        if missing:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Variables faltantes en .env: {", ".join(missing)}'
                )
            )
            return False
        
        return True
    
    def _backup_sqlite(self):
        """Hacer backup de la base de datos SQLite"""
        self.stdout.write('📦 Creando backup de SQLite...')
        
        import shutil
        from datetime import datetime
        
        sqlite_path = 'buscador_inmobiliario.db'
        if os.path.exists(sqlite_path):
            backup_name = f'backup_sqlite_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(sqlite_path, backup_name)
            self.stdout.write(f'✅ Backup creado: {backup_name}')
    
    def _test_postgresql_connection(self):
        """Probar conexión a PostgreSQL"""
        self.stdout.write('🔌 Probando conexión PostgreSQL...')
        
        try:
            connection = connections['default']
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result[0] == 1:
                    self.stdout.write('✅ Conexión PostgreSQL exitosa')
                    return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error conectando PostgreSQL: {e}')
            )
            self.stdout.write(
                self.style.WARNING(
                    'Asegúrate de que PostgreSQL esté ejecutándose y las '
                    'credenciales en .env sean correctas'
                )
            )
            return False
    
    def _drop_postgresql_tables(self):
        """Eliminar tablas existentes en PostgreSQL"""
        self.stdout.write('🗑️ Eliminando tablas PostgreSQL...')
        
        try:
            call_command('migrate', 'core', 'zero', verbosity=0)
            self.stdout.write('✅ Tablas eliminadas')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Error eliminando tablas: {e}')
            )
    
    def _apply_migrations(self):
        """Aplicar migraciones en PostgreSQL"""
        self.stdout.write('📋 Aplicando migraciones PostgreSQL...')
        
        try:
            call_command('migrate', verbosity=0)
            self.stdout.write('✅ Migraciones aplicadas')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error en migraciones: {e}')
            )
            sys.exit(1)
    
    def _migrate_data(self):
        """Migrar datos usando fixtures"""
        self.stdout.write('📊 Migrando datos...')
        
        try:
            # Cargar datos iniciales
            call_command('loaddata', 'core/fixtures/initial_data.json', verbosity=0)
            self.stdout.write('✅ Datos iniciales cargados')
            
            # Crear datos de ejemplo si no existen
            call_command('create_sample_data', verbosity=0)
            self.stdout.write('✅ Datos de ejemplo creados')
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Error migrando datos: {e}')
            )
    
    def _verify_migration(self):
        """Verificar que la migración fue exitosa"""
        self.stdout.write('🔍 Verificando migración...')
        
        try:
            from core.search_manager import get_search_stats
            stats = get_search_stats()
            
            self.stdout.write(f"📊 Estadísticas PostgreSQL:")
            self.stdout.write(f"   - Búsquedas: {stats['total_searches']}")
            self.stdout.write(f"   - Palabras clave: {stats['total_keywords']}")
            self.stdout.write(f"   - Propiedades: {stats['total_properties']}")
            self.stdout.write(f"   - Resultados: {stats['total_results']}")
            
            if stats['total_searches'] > 0:
                self.stdout.write('✅ Verificación exitosa')
            else:
                self.stdout.write('⚠️ No se encontraron datos migrados')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error verificando migración: {e}')
            )
