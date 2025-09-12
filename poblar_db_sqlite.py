import sqlite3
import json
import uuid
from datetime import datetime

# Conectar a la base de datos
conn = sqlite3.connect('buscador_inmobiliario.db')
cursor = conn.cursor()

def limpiar_datos():
    """Limpiar tablas principales"""
    print("🧹 Limpiando datos existentes...")
    
    # Limpiar en orden correcto para evitar problemas de foreign keys
    cursor.execute("DELETE FROM palabra_clave_propiedad")
    cursor.execute("DELETE FROM resultado_busqueda")
    cursor.execute("DELETE FROM busqueda_palabra_clave")
    cursor.execute("DELETE FROM propiedad")
    cursor.execute("DELETE FROM busqueda")
    cursor.execute("DELETE FROM palabra_clave")
    
    conn.commit()
    print("   ✅ Datos limpiados")

def crear_palabras_clave():
    """Crear palabras clave de ejemplo"""
    print("🔤 Creando palabras clave...")
    
    keywords = [
        ('apartamento', '["apto", "departamento", "depto", "piso"]'),
        ('casa', '["vivienda", "hogar", "residencia", "chalet"]'),
        ('garage', '["garaje", "cochera", "estacionamiento"]'),
        ('piscina', '["pileta", "alberca", "natatorio"]'),
        ('terraza', '["balcon", "balcón", "azotea", "deck"]'),
        ('amueblado', '["muebles", "mobiliario", "equipado"]'),
        ('seguridad', '["vigilancia", "portero", "alarma"]'),
    ]
    
    for texto, sinonimos in keywords:
        cursor.execute(
            "INSERT INTO palabra_clave (texto, idioma, sinonimos) VALUES (?, ?, ?)",
            (texto, 'es', sinonimos)
        )
        print(f"   ✅ Creada: {texto}")
    
    conn.commit()

def crear_busquedas():
    """Crear búsquedas de ejemplo"""
    print("🔍 Creando búsquedas de ejemplo...")
    
    now = datetime.now().isoformat()
    
    busquedas = [
        {
            'id': str(uuid.uuid4()),
            'nombre': 'Apartamento Pocitos - Alquiler USD',
            'texto': 'apartamento pocitos alquiler garage terraza vista mar',
            'filtros': json.dumps({
                'tipo': 'apartamento',
                'operacion': 'alquiler',
                'departamento': 'Montevideo',
                'ciudad': 'Pocitos',
                'moneda': 'USD',
                'precio_min': 800,
                'precio_max': 1500,
                'dormitorios_min': 2,
                'dormitorios_max': 3
            }),
            'guardado': 1
        },
        {
            'id': str(uuid.uuid4()),
            'nombre': 'Casa Carrasco - Venta Premium',
            'texto': 'casa carrasco venta piscina jardin garage seguridad',
            'filtros': json.dumps({
                'tipo': 'casa',
                'operacion': 'venta',
                'departamento': 'Montevideo',
                'ciudad': 'Carrasco',
                'moneda': 'USD',
                'precio_min': 150000,
                'precio_max': 300000,
                'dormitorios_min': 3,
                'dormitorios_max': 4
            }),
            'guardado': 1
        },
        {
            'id': str(uuid.uuid4()),
            'nombre': 'Apartamento Centro - Alquiler Pesos',
            'texto': 'apartamento centro alquiler amueblado profesional',
            'filtros': json.dumps({
                'tipo': 'apartamento',
                'operacion': 'alquiler',
                'departamento': 'Montevideo',
                'ciudad': 'Centro',
                'moneda': 'UYU',
                'precio_min': 25000,
                'precio_max': 45000,
                'dormitorios_min': 1,
                'dormitorios_max': 2
            }),
            'guardado': 1
        },
        {
            'id': str(uuid.uuid4()),
            'nombre': 'Casa Punta del Este - Vista Mar',
            'texto': 'casa punta del este venta vista mar piscina terraza',
            'filtros': json.dumps({
                'tipo': 'casa',
                'operacion': 'venta',
                'departamento': 'Maldonado',
                'ciudad': 'Punta del Este',
                'moneda': 'USD',
                'precio_min': 200000,
                'precio_max': 500000,
                'dormitorios_min': 3,
                'dormitorios_max': 5
            }),
            'guardado': 1
        },
        {
            'id': str(uuid.uuid4()),
            'nombre': 'Apartamento Cordón - Inversión',
            'texto': 'apartamento cordon inversion alquiler zona comercial',
            'filtros': json.dumps({
                'tipo': 'apartamento',
                'operacion': 'venta',
                'departamento': 'Montevideo',
                'ciudad': 'Cordón',
                'moneda': 'USD',
                'precio_min': 80000,
                'precio_max': 150000,
                'dormitorios_min': 1,
                'dormitorios_max': 2
            }),
            'guardado': 1
        },
        {
            'id': str(uuid.uuid4()),
            'nombre': 'Búsqueda Temporal - No Guardada',
            'texto': 'apartamento alquiler economico cualquier zona',
            'filtros': json.dumps({
                'tipo': 'apartamento',
                'operacion': 'alquiler',
                'departamento': 'Montevideo',
                'moneda': 'USD',
                'precio_max': 1000
            }),
            'guardado': 0
        }
    ]
    
    for busqueda in busquedas:
        cursor.execute(
            """INSERT INTO busqueda (id, nombre_busqueda, texto_original, filtros, guardado, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (busqueda['id'], busqueda['nombre'], busqueda['texto'], busqueda['filtros'], 
             busqueda['guardado'], now, now)
        )
        estado = "💾 Guardada" if busqueda['guardado'] else "📝 Temporal"
        print(f"   ✅ {estado}: {busqueda['nombre']}")
    
    conn.commit()

def crear_propiedades():
    """Crear propiedades de ejemplo"""
    print("🏠 Creando propiedades de ejemplo...")
    
    # Obtener ID de plataforma MercadoLibre (asumiendo que existe)
    cursor.execute("SELECT id FROM plataforma WHERE nombre = 'MercadoLibre' LIMIT 1")
    result = cursor.fetchone()
    plataforma_id = result[0] if result else 1
    
    now = datetime.now().isoformat()
    
    propiedades = [
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo1-pocitos',
            'titulo': 'Apartamento en Pocitos con Vista al Mar',
            'descripcion': 'Hermoso apartamento de 2 dormitorios en Pocitos con vista panorámica al mar. Cuenta con garage, terraza amplia y amenities completos.',
            'metadata': json.dumps({
                'precio': 1200.00,
                'moneda': 'USD',
                'ubicacion': 'Pocitos, Montevideo',
                'dormitorios': 2,
                'banos': 2,
                'metros_cuadrados': 85.0,
                'caracteristicas': {
                    'garage': True,
                    'terraza': True,
                    'vista_mar': True,
                    'amenities': True
                }
            })
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo2-carrasco',
            'titulo': 'Casa en Carrasco con Piscina y Jardín',
            'descripcion': 'Espectacular casa familiar en Carrasco Norte. 4 dormitorios, piscina climatizada, amplio jardín con parrillero.',
            'metadata': json.dumps({
                'precio': 280000.00,
                'moneda': 'USD',
                'ubicacion': 'Carrasco, Montevideo',
                'dormitorios': 4,
                'banos': 3,
                'metros_cuadrados': 250.0,
                'caracteristicas': {
                    'piscina': True,
                    'jardin': True,
                    'garage': True,
                    'parrillero': True,
                    'seguridad': True
                }
            })
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo3-centro',
            'titulo': 'Apartamento Amueblado en Centro',
            'descripcion': 'Apartamento completamente amueblado en el centro de Montevideo. Ideal para profesionales.',
            'metadata': json.dumps({
                'precio': 35000.00,
                'moneda': 'UYU',
                'ubicacion': 'Centro, Montevideo',
                'dormitorios': 1,
                'banos': 1,
                'metros_cuadrados': 45.0,
                'caracteristicas': {
                    'amueblado': True,
                    'electrodomesticos': True,
                    'internet': True,
                    'calefaccion': True
                }
            })
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo4-punta',
            'titulo': 'Casa en Punta del Este con Vista al Mar',
            'descripcion': 'Hermosa casa a 2 cuadras de Playa Brava. Piscina, terraza con deck y vista parcial al mar.',
            'metadata': json.dumps({
                'precio': 350000.00,
                'moneda': 'USD',
                'ubicacion': 'Punta del Este, Maldonado',
                'dormitorios': 3,
                'banos': 2,
                'metros_cuadrados': 180.0,
                'caracteristicas': {
                    'piscina': True,
                    'terraza': True,
                    'vista_mar': True,
                    'cerca_playa': True
                }
            })
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo5-cordon',
            'titulo': 'Apartamento de Inversión en Cordón',
            'descripcion': 'Excelente oportunidad de inversión. Apartamento en muy buen estado en zona de alta demanda.',
            'metadata': json.dumps({
                'precio': 120000.00,
                'moneda': 'USD',
                'ubicacion': 'Cordón, Montevideo',
                'dormitorios': 2,
                'banos': 1,
                'metros_cuadrados': 60.0,
                'caracteristicas': {
                    'inversion': True,
                    'zona_comercial': True,
                    'transporte': True
                }
            })
        },
        {
            'url': 'https://articulo.mercadolibre.com.uy/MLU-ejemplo6-blanqueada',
            'titulo': 'Casa Familiar en La Blanqueada',
            'descripcion': 'Casa de 3 dormitorios con patio, garage y muy buena iluminación. Zona tranquila.',
            'metadata': json.dumps({
                'precio': 180000.00,
                'moneda': 'USD',
                'ubicacion': 'La Blanqueada, Montevideo',
                'dormitorios': 3,
                'banos': 2,
                'metros_cuadrados': 120.0,
                'caracteristicas': {
                    'garage': True,
                    'patio': True,
                    'familia': True,
                    'zona_tranquila': True
                }
            })
        }
    ]
    
    for prop in propiedades:
        cursor.execute(
            """INSERT INTO propiedad (url, titulo, descripcion, metadata, plataforma_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (prop['url'], prop['titulo'], prop['descripcion'], prop['metadata'], 
             plataforma_id, now, now)
        )
        metadata = json.loads(prop['metadata'])
        print(f"   ✅ {prop['titulo']}")
        print(f"      📍 {metadata['ubicacion']} - {metadata['dormitorios']} dorm")
        print(f"      💰 {metadata['moneda']} {metadata['precio']:,.0f}")
    
    conn.commit()

def mostrar_estadisticas():
    """Mostrar estadísticas finales"""
    print("\n📊 Estadísticas finales:")
    
    cursor.execute("SELECT COUNT(*) FROM palabra_clave")
    keywords = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM busqueda WHERE guardado = 1")
    busquedas_guardadas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM busqueda WHERE guardado = 0")
    busquedas_temporales = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM propiedad")
    propiedades = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM palabra_clave_propiedad")
    relaciones = cursor.fetchone()[0]
    
    print(f"   🔤 Palabras clave: {keywords}")
    print(f"   🔍 Búsquedas guardadas: {busquedas_guardadas}")
    print(f"   📝 Búsquedas temporales: {busquedas_temporales}")
    print(f"   🏠 Propiedades: {propiedades}")
    print(f"   🔗 Relaciones keyword-propiedad: {relaciones}")

def main():
    """Función principal"""
    print("🚀 Iniciando limpieza y población de la base de datos...")
    print("=" * 60)
    
    try:
        # Ejecutar en orden
        limpiar_datos()
        crear_palabras_clave()
        crear_busquedas()
        crear_propiedades()
        mostrar_estadisticas()
        
        print("\n✅ ¡Base de datos limpiada y poblada exitosamente!")
        print("=" * 60)
        print("💡 Usa 'python ver_datos_tabla.py --list' para ver el estado actual")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    main()
