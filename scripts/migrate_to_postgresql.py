# scripts/migrate_to_postgresql.py
"""
Script completo para migrar de SQLite a PostgreSQL
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description, check=True):
    """Ejecutar comando con descripción"""
    print(f"\n🔧 {description}")
    print(f"Comando: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0 and check:
        print(f"❌ Error: {result.stderr}")
        sys.exit(1)
    
    if result.stdout:
        print(result.stdout)
    
    return result

def main():
    print("🐘 MIGRACIÓN DE SQLite A PostgreSQL")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Este script debe ejecutarse desde el directorio raíz del proyecto Django")
        sys.exit(1)
    
    # Paso 1: Verificar configuración actual
    print("\n📋 PASO 1: Verificación de configuración")
    current_engine = os.environ.get('DATABASE_ENGINE', 'sqlite')
    print(f"Base de datos actual: {current_engine}")
    
    if current_engine == 'postgresql':
        print("⚠️ DATABASE_ENGINE ya está configurado como postgresql")
        choice = input("¿Continuar con la migración? (s/n): ")
        if choice.lower() != 's':
            sys.exit(0)
    
    # Paso 2: Exportar datos desde SQLite
    print("\n📦 PASO 2: Exportar datos desde SQLite")
    if current_engine == 'sqlite':
        run_command(
            "python manage.py export_sqlite_data --backup-first",
            "Exportando datos desde SQLite"
        )
    else:
        print("⚠️ No se puede exportar desde SQLite (no está activo)")
    
    # Paso 3: Cambiar configuración a PostgreSQL
    print("\n⚙️ PASO 3: Cambiar configuración a PostgreSQL")
    
    # Leer archivo .env
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Cambiar DATABASE_ENGINE
        if 'DATABASE_ENGINE=' in env_content:
            env_content = env_content.replace(
                'DATABASE_ENGINE=sqlite',
                'DATABASE_ENGINE=postgresql'
            )
        else:
            env_content += '\nDATABASE_ENGINE=postgresql\n'
        
        # Escribir archivo actualizado
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("✅ Configuración cambiada a PostgreSQL")
    else:
        print("❌ No se encontró archivo .env")
        sys.exit(1)
    
    # Paso 4: Verificar conexión PostgreSQL
    print("\n🔌 PASO 4: Verificar conexión PostgreSQL")
    result = run_command(
        "python manage.py migrate_to_postgresql --drop-tables",
        "Migrando a PostgreSQL",
        check=False
    )
    
    if result.returncode != 0:
        print("❌ Error en la migración. Revirtiendo configuración...")
        # Revertir cambios
        with open(env_path, 'r') as f:
            env_content = f.read()
        env_content = env_content.replace(
            'DATABASE_ENGINE=postgresql',
            'DATABASE_ENGINE=sqlite'
        )
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("⚠️ Configuración revertida a SQLite")
        sys.exit(1)
    
    # Paso 5: Verificación final
    print("\n✅ PASO 5: Verificación final")
    run_command(
        "python manage.py migrate --run-syncdb",
        "Sincronizando base de datos"
    )
    
    print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 50)
    print("📊 Para verificar la migración:")
    print("   python manage.py shell -c \"from core.models import *; print(f'Búsquedas: {Busqueda.objects.count()}')\"")
    print("\n🔧 Para crear datos de ejemplo:")
    print("   python manage.py create_sample_data")
    print("\n🚀 Para iniciar el servidor:")
    print("   .\\.venv\\Scripts\\activate ; daphne -b 0.0.0.0 -p 10000 buscador.asgi:application")

if __name__ == '__main__':
    main()
