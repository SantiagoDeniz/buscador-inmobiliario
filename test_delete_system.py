#!/usr/bin/env python
"""
Script para probar el nuevo sistema de "eliminación" de búsquedas.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.search_manager import (
    save_search, get_all_searches, get_all_search_history, 
    delete_search, restore_search_from_history, get_search_stats
)

def test_delete_system():
    print("🧪 Probando nuevo sistema de 'eliminación' de búsquedas...")
    
    # Test 1: Crear una búsqueda guardada
    print("\n1️⃣ Creando búsqueda guardada...")
    search_data = {
        'nombre_busqueda': 'Test búsqueda para eliminar',
        'texto_original': 'apartamento centro',
        'palabras_clave': ['apartamento', 'centro'],
        'filtros': {'tipo': 'apartamento', 'ciudad': 'centro'},
        'guardado': True
    }
    search_id = save_search(search_data)
    print(f"✅ Búsqueda creada con ID: {search_id}")
    
    # Test 2: Verificar que aparece en la lista
    print("\n2️⃣ Verificando que aparece en lista...")
    searches_before = get_all_searches()
    found_in_list = any(s['id'] == search_id for s in searches_before)
    print(f"📋 Búsqueda en lista: {found_in_list}")
    print(f"📋 Total búsquedas en lista: {len(searches_before)}")
    
    # Test 3: Verificar estadísticas antes
    print("\n3️⃣ Estadísticas antes de 'eliminar'...")
    stats_before = get_search_stats()
    print(f"📊 Total búsquedas: {stats_before['total_searches']}")
    print(f"📊 Búsquedas guardadas: {stats_before['saved_searches']}")
    
    # Test 4: "Eliminar" la búsqueda (mover a historial)
    print(f"\n4️⃣ 'Eliminando' búsqueda {search_id}...")
    success = delete_search(search_id)
    print(f"✅ Eliminación exitosa: {success}")
    
    # Test 5: Verificar que ya no aparece en la lista
    print("\n5️⃣ Verificando que ya no aparece en lista...")
    searches_after = get_all_searches()
    found_in_list_after = any(s['id'] == search_id for s in searches_after)
    print(f"📋 Búsqueda en lista después: {found_in_list_after}")
    print(f"📋 Total búsquedas en lista después: {len(searches_after)}")
    
    # Test 6: Verificar que sigue en el historial completo
    print("\n6️⃣ Verificando que sigue en historial completo...")
    all_searches = get_all_search_history()
    found_in_history = any(s['id'] == search_id for s in all_searches)
    guardado_status = None
    for s in all_searches:
        if s['id'] == search_id:
            guardado_status = s['guardado']
            break
    print(f"📚 Búsqueda en historial: {found_in_history}")
    print(f"📚 Estado guardado: {guardado_status}")
    
    # Test 7: Verificar estadísticas después
    print("\n7️⃣ Estadísticas después de 'eliminar'...")
    stats_after = get_search_stats()
    print(f"📊 Total búsquedas: {stats_after['total_searches']}")
    print(f"📊 Búsquedas guardadas: {stats_after['saved_searches']}")
    print(f"📊 Diferencia en total: {stats_after['total_searches'] - stats_before['total_searches']}")
    print(f"📊 Diferencia en guardadas: {stats_after['saved_searches'] - stats_before['saved_searches']}")
    
    # Test 8: Probar restauración
    print(f"\n8️⃣ Restaurando búsqueda {search_id}...")
    restore_success = restore_search_from_history(search_id)
    print(f"✅ Restauración exitosa: {restore_success}")
    
    # Test 9: Verificar que vuelve a aparecer en la lista
    print("\n9️⃣ Verificando que vuelve a aparecer en lista...")
    searches_restored = get_all_searches()
    found_after_restore = any(s['id'] == search_id for s in searches_restored)
    print(f"📋 Búsqueda restaurada en lista: {found_after_restore}")
    
    print("\n✅ Pruebas completadas!")
    print("🎯 Resumen del nuevo comportamiento:")
    print("   - 'Eliminar' mueve búsqueda a historial (guardado=False)")
    print("   - La búsqueda se mantiene en BD para análisis")
    print("   - Se puede restaurar desde historial si es necesario")
    print("   - No se pierde información ni resultados")

if __name__ == "__main__":
    test_delete_system()
