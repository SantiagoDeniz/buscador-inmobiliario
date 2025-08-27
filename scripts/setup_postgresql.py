# scripts/setup_postgresql.py
"""
Script para configurar PostgreSQL usando Docker
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def run_command(command, description, check=True, capture=True):
    """Ejecutar comando con descripción"""
    print(f"\n🔧 {description}")
    print(f"Comando: {command}")
    
    if capture:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0 and check:
            print(f"❌ Error: {result.stderr}")
            return False
        
        if result.stdout:
            print(result.stdout)
    else:
        result = subprocess.run(command, shell=True)
        if result.returncode != 0 and check:
            return False
    
    return True

def check_docker():
    """Verificar si Docker está instalado y funcionando"""
    print("🐳 Verificando Docker...")
    
    # Verificar si docker está instalado
    result = subprocess.run('docker --version', shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Docker no está instalado")
        print("📥 Instalando Docker Desktop...")
        print("Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop/")
        return False
    
    print(f"✅ {result.stdout.strip()}")
    
    # Verificar si Docker está funcionando
    result = subprocess.run('docker info', shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Docker no está funcionando")
        print("🔄 Inicia Docker Desktop e inténtalo de nuevo")
        return False
    
    print("✅ Docker está funcionando correctamente")
    return True

def setup_docker_compose():
    """Configurar y ejecutar Docker Compose"""
    print("🐘 Configurando PostgreSQL con Docker...")
    
    # Verificar si docker-compose.yml existe
    if not Path('docker-compose.yml').exists():
        print("❌ No se encontró docker-compose.yml")
        return False
    
    # Detener contenedores existentes
    run_command('docker-compose down', "Deteniendo contenedores existentes", check=False)
    
    # Iniciar PostgreSQL
    if not run_command('docker-compose up -d db', "Iniciando PostgreSQL"):
        return False
    
    # Esperar a que PostgreSQL esté listo
    print("⏳ Esperando a que PostgreSQL esté listo...")
    max_attempts = 30
    attempts = 0
    
    while attempts < max_attempts:
        result = subprocess.run(
            'docker-compose exec -T db pg_isready -U postgres',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ PostgreSQL está listo")
            break
        
        attempts += 1
        print(f"⏳ Intento {attempts}/{max_attempts}...")
        time.sleep(2)
    
    if attempts >= max_attempts:
        print("❌ Timeout esperando PostgreSQL")
        return False
    
    return True

def setup_environment():
    """Configurar variables de entorno"""
    print("⚙️ Configurando variables de entorno...")
    
    env_path = Path('.env')
    env_vars = {
        'DATABASE_ENGINE': 'postgresql',
        'DB_NAME': 'buscador_inmobiliario',
        'DB_USER': 'postgres',
        'DB_PASSWORD': 'postgres123',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432'
    }
    
    # Leer archivo .env existente
    existing_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    existing_vars[key] = value
    
    # Actualizar variables
    existing_vars.update(env_vars)
    
    # Escribir archivo .env
    with open(env_path, 'w') as f:
        for key, value in existing_vars.items():
            f.write(f'{key}={value}\n')
    
    print("✅ Variables de entorno configuradas")
    return True

def main():
    print("🐘 CONFIGURACIÓN DE PostgreSQL CON DOCKER")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Este script debe ejecutarse desde el directorio raíz del proyecto Django")
        sys.exit(1)
    
    # Paso 1: Verificar Docker
    if not check_docker():
        print("\n❌ No se puede continuar sin Docker")
        print("📥 Opciones:")
        print("1. Instalar Docker Desktop: https://www.docker.com/products/docker-desktop/")
        print("2. Instalar PostgreSQL manualmente")
        print("3. Usar PostgreSQL en la nube (Heroku, AWS RDS, etc.)")
        sys.exit(1)
    
    # Paso 2: Configurar variables de entorno
    if not setup_environment():
        sys.exit(1)
    
    # Paso 3: Configurar Docker Compose
    if not setup_docker_compose():
        sys.exit(1)
    
    # Paso 4: Verificar conexión
    print("\n🔌 Verificando conexión a PostgreSQL...")
    if not run_command(
        'python manage.py migrate --check',
        "Verificando migraciones"
    ):
        print("❌ Error verificando migraciones")
        sys.exit(1)
    
    print("\n✅ CONFIGURACIÓN COMPLETADA")
    print("=" * 50)
    print("🐘 PostgreSQL está funcionando en:")
    print("   Host: localhost")
    print("   Puerto: 5432")
    print("   Base de datos: buscador_inmobiliario")
    print("   Usuario: postgres")
    print("")
    print("🚀 Próximos pasos:")
    print("1. Migrar datos: python scripts/migrate_to_postgresql.py")
    print("2. Crear superusuario: python manage.py createsuperuser")
    print("3. Iniciar servidor: python manage.py runserver")
    print("")
    print("🛠️ Comandos útiles:")
    print("   Ver logs PostgreSQL: docker-compose logs db")
    print("   Conectar a PostgreSQL: docker-compose exec db psql -U postgres -d buscador_inmobiliario")
    print("   Detener servicios: docker-compose down")

if __name__ == '__main__':
    main()
