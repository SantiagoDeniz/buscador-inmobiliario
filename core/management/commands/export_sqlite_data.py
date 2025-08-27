# core/management/commands/export_sqlite_data.py
"""
Comando para exportar datos desde SQLite a fixtures JSON
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import shutil
from datetime import datetime


class Command(BaseCommand):
    help = 'Exporta datos de SQLite a fixtures JSON para migrar a PostgreSQL'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-first',
            action='store_true',
            help='Hacer backup de SQLite antes de exportar',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('📦 Exportando datos desde SQLite...')
        )
        
        # Verificar que estamos en SQLite
        if not self._verify_sqlite_active():
            return
        
        # Hacer backup si se requiere
        if options['backup_first']:
            self._backup_sqlite()
        
        # Crear directorio para fixtures
        fixtures_dir = 'core/fixtures'
        os.makedirs(fixtures_dir, exist_ok=True)
        
        # Exportar datos por app/modelo
        self._export_data()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Exportación completada')
        )
    
    def _verify_sqlite_active(self):
        """Verificar que SQLite esté activo"""
        database_engine = os.environ.get('DATABASE_ENGINE', 'sqlite')
        
        if database_engine != 'sqlite':
            self.stdout.write(
                self.style.ERROR(
                    '❌ Este comando requiere DATABASE_ENGINE="sqlite" en .env'
                )
            )
            return False
        
        return True
    
    def _backup_sqlite(self):
        """Hacer backup de la base de datos SQLite"""
        self.stdout.write('💾 Creando backup de SQLite...')
        
        sqlite_path = 'buscador_inmobiliario.db'
        if os.path.exists(sqlite_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'backup_sqlite_{timestamp}.db'
            shutil.copy2(sqlite_path, backup_name)
            self.stdout.write(f'✅ Backup creado: {backup_name}')
        else:
            self.stdout.write('⚠️ No se encontró archivo SQLite para backup')
    
    def _export_data(self):
        """Exportar datos a fixtures JSON"""
        self.stdout.write('📄 Exportando datos a fixtures...')
        
        try:
            # Exportar todos los datos de la app core
            fixture_path = 'core/fixtures/exported_data.json'
            
            call_command(
                'dumpdata', 
                'core',
                '--format=json',
                '--indent=2',
                f'--output={fixture_path}',
                verbosity=1
            )
            
            self.stdout.write(f'✅ Datos exportados a: {fixture_path}')
            
            # También exportar usuarios (si existen)
            try:
                users_fixture = 'core/fixtures/users_data.json'
                call_command(
                    'dumpdata',
                    'auth.User',
                    '--format=json',
                    '--indent=2',
                    f'--output={users_fixture}',
                    verbosity=0
                )
                self.stdout.write(f'✅ Usuarios exportados a: {users_fixture}')
            except Exception as e:
                self.stdout.write(f'⚠️ Error exportando usuarios: {e}')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error exportando datos: {e}')
            )
