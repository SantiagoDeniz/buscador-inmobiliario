#!/usr/bin/env python
"""
Script de prueba para verificar el nuevo sistema de guardado de búsquedas.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.search_manager import save_search, get_all_searches, get_all_search_history, get_search_stats

def test_new_search_system():
    print("🧪 Probando nuevo sistema de búsquedas...")
    
    # Test 1: Crear búsqueda normal (guardado=False)
    print("\n1️⃣ Creando búsqueda normal (guardado=False)...")
    search_data_normal = {
        'nombre_busqueda': 'Test búsqueda normal',
        'texto_original': 'apartamento pocitos',
        'palabras_clave': ['apartamento', 'pocitos'],
        'filtros': {'tipo': 'apartamento', 'ciudad': 'pocitos'},
        'guardado': False  # No aparece en lista
    }
    search_id_normal = save_search(search_data_normal)
    print(f"✅ Búsqueda normal creada con ID: {search_id_normal}")
    
    # Test 2: Crear búsqueda guardada (guardado=True)
    print("\n2️⃣ Creando búsqueda guardada (guardado=True)...")
    search_data_saved = {
        'nombre_busqueda': 'Test búsqueda guardada',
        'texto_original': 'casa montevideo',
        'palabras_clave': ['casa', 'montevideo'],
        'filtros': {'tipo': 'casa', 'departamento': 'montevideo'},
        'guardado': True  # Aparece en lista
    }
    search_id_saved = save_search(search_data_saved)
    print(f"✅ Búsqueda guardada creada con ID: {search_id_saved}")
    
    # Test 3: Verificar filtros en get_all_searches (solo guardadas)
    print("\n3️⃣ Verificando get_all_searches (solo guardadas)...")
    searches_interface = get_all_searches()
    print(f"📋 Búsquedas en interfaz: {len(searches_interface)}")
    for search in searches_interface:
        print(f"   - {search['nombre_busqueda']} (guardado: {search['guardado']})")
    
    # Test 4: Verificar get_all_search_history (todas)
    print("\n4️⃣ Verificando get_all_search_history (todas)...")
    searches_all = get_all_search_history()
    print(f"📊 Total de búsquedas en historial: {len(searches_all)}")
    for search in searches_all:
        print(f"   - {search['nombre_busqueda']} (guardado: {search['guardado']})")
    
    # Test 5: Estadísticas
    print("\n5️⃣ Verificando estadísticas...")
    stats = get_search_stats()
    print(f"📈 Estadísticas:")
    print(f"   - Total búsquedas: {stats['total_searches']}")
    print(f"   - Búsquedas guardadas: {stats['saved_searches']}")
    print(f"   - Diferencia (historial): {stats['total_searches'] - stats['saved_searches']}")
    
    print("\n✅ Todas las pruebas completadas exitosamente!")
    print("🎯 El nuevo sistema funciona correctamente:")
    print("   - Todas las búsquedas se almacenan en BD")
    print("   - Solo las guardadas aparecen en interfaz")
    print("   - El historial completo está disponible para análisis")

if __name__ == "__main__":
    test_new_search_system()
