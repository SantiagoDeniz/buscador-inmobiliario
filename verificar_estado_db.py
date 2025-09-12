#!/usr/bin/env python3

import sqlite3

def verificar_tablas():
    conn = sqlite3.connect('buscador_inmobiliario.db')
    cursor = conn.cursor()
    
    print("🗄️ Tablas en la base de datos:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    for table in tables:
        if not table[0].startswith('sqlite_'):
            print(f"  • {table[0]}")
    
    # Verificar específicamente si existe palabra_clave_propiedad
    print(f"\n🔍 Verificando tabla 'palabra_clave_propiedad':")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='palabra_clave_propiedad';")
    result = cursor.fetchone()
    if result:
        print("  ✅ La tabla palabra_clave_propiedad existe")
        cursor.execute("PRAGMA table_info(palabra_clave_propiedad);")
        columns = cursor.fetchall()
        print("  📋 Columnas:")
        for col in columns:
            print(f"    - {col[1]} ({col[2]})")
    else:
        print("  ❌ La tabla palabra_clave_propiedad NO existe")
    
    conn.close()

if __name__ == "__main__":
    verificar_tablas()
