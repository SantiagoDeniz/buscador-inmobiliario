#!/usr/bin/env python3

import sqlite3
import sys

def ver_contenido_tabla(nombre_tabla, limite=10):
    """Muestra el contenido de una tabla específica"""
    conn = sqlite3.connect('buscador_inmobiliario.db')
    cursor = conn.cursor()
    
    try:
        # Verificar que la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (nombre_tabla,))
        if not cursor.fetchone():
            print(f"❌ La tabla '{nombre_tabla}' no existe")
            return
        
        # Obtener información de columnas
        cursor.execute(f"PRAGMA table_info({nombre_tabla});")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Tabla: {nombre_tabla}")
        print(f"📊 Columnas: {', '.join(column_names)}")
        
        # Contar total de registros
        cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla};")
        total = cursor.fetchone()[0]
        print(f"📈 Total de registros: {total}")
        
        if total == 0:
            print("📝 La tabla está vacía")
            return
        
        # Mostrar datos
        print(f"\n🔍 Mostrando primeros {min(limite, total)} registros:")
        cursor.execute(f"SELECT * FROM {nombre_tabla} LIMIT ?;", (limite,))
        rows = cursor.fetchall()
        
        # Mostrar encabezados
        print("=" * 80)
        for i, col_name in enumerate(column_names):
            print(f"{col_name:15}", end=" | " if i < len(column_names)-1 else "\n")
        print("=" * 80)
        
        # Mostrar datos
        for row in rows:
            for i, value in enumerate(row):
                # Truncar valores largos
                str_value = str(value)
                if len(str_value) > 15:
                    str_value = str_value[:12] + "..."
                print(f"{str_value:15}", end=" | " if i < len(row)-1 else "\n")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error consultando la tabla: {e}")
    finally:
        conn.close()

def listar_todas_las_tablas():
    """Lista todas las tablas disponibles"""
    conn = sqlite3.connect('buscador_inmobiliario.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    print("🗄️ Tablas disponibles:")
    for i, table in enumerate(tables, 1):
        if not table[0].startswith('sqlite_'):
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"  {i:2}. {table[0]:25} ({count:3} registros)")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🔍 Uso del script:")
        print("  python ver_datos_tabla.py <nombre_tabla> [limite]")
        print("  python ver_datos_tabla.py --list  (para ver todas las tablas)")
        print("\n📋 Ejemplos:")
        print("  python ver_datos_tabla.py busqueda")
        print("  python ver_datos_tabla.py propiedad 5")
        print("  python ver_datos_tabla.py palabra_clave_propiedad")
        print()
        listar_todas_las_tablas()
    elif sys.argv[1] == "--list":
        listar_todas_las_tablas()
    else:
        tabla = sys.argv[1]
        limite = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        ver_contenido_tabla(tabla, limite)
