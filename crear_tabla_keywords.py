#!/usr/bin/env python3

import sqlite3

def crear_tabla_palabra_clave_propiedad():
    conn = sqlite3.connect('buscador_inmobiliario.db')
    cursor = conn.cursor()
    
    # SQL para crear la tabla palabra_clave_propiedad
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS palabra_clave_propiedad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        palabra_clave_id INTEGER NOT NULL,
        propiedad_id INTEGER NOT NULL,
        encontrada BOOLEAN NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (palabra_clave_id) REFERENCES palabra_clave (id),
        FOREIGN KEY (propiedad_id) REFERENCES propiedad (id),
        UNIQUE (palabra_clave_id, propiedad_id)
    );
    """
    
    # SQL para crear índices
    sql_index_1 = """
    CREATE INDEX IF NOT EXISTS palabra_cla_palabra_2ec9d2_idx 
    ON palabra_clave_propiedad (palabra_clave_id, encontrada);
    """
    
    sql_index_2 = """
    CREATE INDEX IF NOT EXISTS palabra_cla_propied_af909c_idx 
    ON palabra_clave_propiedad (propiedad_id, encontrada);
    """
    
    try:
        print("🔧 Creando tabla palabra_clave_propiedad...")
        cursor.execute(sql_create_table)
        print("✅ Tabla creada exitosamente")
        
        print("🔧 Creando índices...")
        cursor.execute(sql_index_1)
        cursor.execute(sql_index_2)
        print("✅ Índices creados exitosamente")
        
        conn.commit()
        print("✅ Cambios guardados en la base de datos")
        
        # Verificar que la tabla se creó
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='palabra_clave_propiedad';")
        result = cursor.fetchone()
        if result:
            print("🎉 ¡Tabla palabra_clave_propiedad creada y verificada!")
            
            # Mostrar estructura de la tabla
            cursor.execute("PRAGMA table_info(palabra_clave_propiedad);")
            columns = cursor.fetchall()
            print("📋 Estructura de la tabla:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
        else:
            print("❌ Error: La tabla no se pudo crear")
            
    except Exception as e:
        print(f"❌ Error creando tabla: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    crear_tabla_palabra_clave_propiedad()
