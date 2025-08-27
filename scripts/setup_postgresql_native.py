# scripts/setup_postgresql_native.py
"""
Script para instalar PostgreSQL directamente en Windows (sin Docker)
"""

import os
import sys
import subprocess
import requests
import tempfile
from pathlib import Path

def check_postgresql_installed():
    """Verificar si PostgreSQL ya está instalado"""
    # Rutas comunes de PostgreSQL en Windows
    possible_paths = [
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\13\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\14\bin\psql.exe",
    ]
    
    # Primero intentar con PATH
    try:
        result = subprocess.run('psql --version', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL encontrado en PATH: {result.stdout.strip()}")
            return True, 'psql'
    except:
        pass
    
    # Buscar en rutas específicas
    for path in possible_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run(f'"{path}" --version', shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ PostgreSQL encontrado: {result.stdout.strip()}")
                    print(f"   📍 Ubicación: {path}")
                    return True, os.path.dirname(path)
            except:
                continue
    
    return False, None

def install_postgresql_windows():
    """Instalar PostgreSQL en Windows usando winget"""
    print("📥 Intentando instalar PostgreSQL con winget...")
    
    # Verificar si winget está disponible
    result = subprocess.run('winget --version', shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ winget no está disponible")
        return False
    
    # Instalar PostgreSQL
    cmd = 'winget install --id PostgreSQL.PostgreSQL --silent --accept-package-agreements --accept-source-agreements'
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("✅ PostgreSQL instalado con winget")
        return True
    else:
        print("❌ Error instalando con winget")
        return False

def download_postgresql_installer():
    """Descargar instalador de PostgreSQL manualmente"""
    print("📥 Descargando instalador de PostgreSQL...")
    
    # URL del instalador PostgreSQL 15 para Windows x64
    url = "https://get.enterprisedb.com/postgresql/postgresql-15.7-1-windows-x64.exe"
    
    # Crear directorio temporal
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "postgresql-installer.exe")
    
    try:
        print("⏳ Descargando... (esto puede tomar varios minutos)")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(installer_path, 'wb') as f:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r📥 Descargado: {percent:.1f}%", end="")
        
        print(f"\n✅ Descarga completada: {installer_path}")
        return installer_path
        
    except Exception as e:
        print(f"❌ Error descargando: {e}")
        return None

def setup_postgresql_service():
    """Configurar servicio PostgreSQL"""
    print("⚙️ Configurando servicio PostgreSQL...")
    
    # Verificar servicio
    result = subprocess.run('sc query postgresql-x64-15', shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ Servicio PostgreSQL no encontrado")
        return False
    
    # Iniciar servicio
    result = subprocess.run('net start postgresql-x64-15', shell=True)
    if result.returncode == 0:
        print("✅ Servicio PostgreSQL iniciado")
        return True
    else:
        print("⚠️ Error iniciando servicio (puede que ya esté corriendo)")
        return True  # Podría estar ya corriendo

def create_database(pg_bin_path):
    """Crear base de datos para el proyecto"""
    print("🗄️ Creando base de datos...")
    
    # Usar ruta completa si no está en PATH
    if pg_bin_path != 'psql':
        createdb_cmd = f'"{os.path.join(pg_bin_path, "createdb.exe")}"'
        psql_cmd = f'"{os.path.join(pg_bin_path, "psql.exe")}"'
    else:
        createdb_cmd = 'createdb'
        psql_cmd = 'psql'
    
    # Comandos para crear DB
    commands = [
        f'{createdb_cmd} -U postgres buscador_inmobiliario',
        f'{psql_cmd} -U postgres -c "ALTER USER postgres PASSWORD \'postgres123\';"'
    ]
    
    for cmd in commands:
        print(f"Ejecutando: {cmd}")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"⚠️ Error ejecutando: {cmd}")
            print("   (Es posible que la base de datos ya exista)")

def test_connection(pg_bin_path):
    """Probar conexión a PostgreSQL"""
    print("🔌 Probando conexión...")
    
    # Usar ruta completa si no está en PATH
    if pg_bin_path != 'psql':
        psql_cmd = f'"{os.path.join(pg_bin_path, "psql.exe")}"'
    else:
        psql_cmd = 'psql'
    
    # Test de conexión
    test_cmd = f'{psql_cmd} -U postgres -d buscador_inmobiliario -c "SELECT version();" -t'
    
    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Conexión exitosa a PostgreSQL")
        return True
    else:
        print("❌ Error de conexión")
        print(f"Error: {result.stderr}")
        return False

def update_env_file():
    """Actualizar archivo .env con configuración PostgreSQL"""
    print("📝 Actualizando archivo .env...")
    
    env_path = Path('.env')
    env_vars = {
        'DATABASE_ENGINE': 'postgresql',
        'DB_NAME': 'buscador_inmobiliario',
        'DB_USER': 'postgres',
        'DB_PASSWORD': 'postgres123',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432'
    }
    
    # Leer variables existentes
    existing_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    existing_vars[key] = value
    
    # Actualizar con nuevas variables
    existing_vars.update(env_vars)
    
    # Escribir archivo
    with open(env_path, 'w') as f:
        f.write('# Configuración Base de Datos\n')
        for key, value in env_vars.items():
            f.write(f'{key}={value}\n')
        f.write('\n# Otras configuraciones\n')
        for key, value in existing_vars.items():
            if key not in env_vars:
                f.write(f'{key}={value}\n')
    
    print("✅ Archivo .env actualizado")

def main():
    print("🐘 INSTALACIÓN POSTGRESQL NATIVO PARA WINDOWS")
    print("=" * 55)
    
    # Verificar si ya está instalado
    is_installed, pg_path = check_postgresql_installed()
    
    if is_installed:
        print("PostgreSQL está disponible")
        
        # Configurar servicio
        setup_postgresql_service()
        
        # Crear base de datos
        create_database(pg_path)
        
        # Probar conexión
        if test_connection(pg_path):
            # Actualizar .env
            update_env_file()
            
            print("\n✅ CONFIGURACIÓN COMPLETADA")
            print("=" * 30)
            print("🚀 Próximos pasos:")
            print("1. python manage.py migrate")
            print("2. python manage.py create_sample_data") 
            print("3. python manage.py runserver")
        else:
            print("\n❌ Error de configuración")
            print("🔧 Soluciones:")
            print("1. Verificar que PostgreSQL esté ejecutándose")
            print("2. Verificar credenciales (usuario: postgres)")
            print("3. Reiniciar el servicio PostgreSQL")
    
    else:
        print("PostgreSQL no está instalado")
        
        # Intentar instalación con winget primero
        if not install_postgresql_windows():
            print("\n📥 Instalación automática falló")
            print("🔗 Opciones manuales:")
            print("1. Descargar desde: https://www.postgresql.org/download/windows/")
            print("2. Ejecutar el instalador")
            print("3. Configurar usuario 'postgres' con contraseña 'postgres123'")
            print("4. Ejecutar este script de nuevo")
            
            # Opción de descarga automática
            response = input("\n¿Descargar instalador automáticamente? (y/n): ")
            if response.lower() == 'y':
                installer_path = download_postgresql_installer()
                if installer_path:
                    print(f"\n🚀 Ejecuta el instalador: {installer_path}")
                    print("Configuración recomendada:")
                    print("  - Usuario: postgres")
                    print("  - Contraseña: postgres123")
                    print("  - Puerto: 5432")
                    print("  - Instalar todos los componentes")
            
            return

if __name__ == '__main__':
    main()
