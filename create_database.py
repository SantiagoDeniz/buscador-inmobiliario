#!/usr/bin/env python3
"""
Script para crear la base de datos PostgreSQL
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def create_database():
    try:
        # Conectar a PostgreSQL (base de datos por defecto)
        print("🔗 Conectando a PostgreSQL...")
        conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            password='postgres',
            port='5432'
        )
        
        # Configurar para autocommit
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Crear cursor
        cursor = conn.cursor()
        
        # Verificar si la base de datos ya existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='buscador_inmobiliario_DB'")
        exists = cursor.fetchone()
        
        if exists:
            print("✅ La base de datos 'buscador_inmobiliario_DB' ya existe")
        else:
            # Crear la base de datos
            print("🔨 Creando base de datos 'buscador_inmobiliario_DB'...")
            cursor.execute("CREATE DATABASE buscador_inmobiliario_DB")
            print("✅ Base de datos creada exitosamente")
        
        # Cerrar conexiones
        cursor.close()
        conn.close()
        
        print("🎉 ¡Proceso completado!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
