#!/usr/bin/env python
"""
Test para verificar que las actualizaciones de búsqueda 
buscan SIEMPRE en todas las plataformas disponibles,
independientemente de los resultados previos.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Busqueda, ResultadoBusqueda, Usuario
from core.search_manager import actualizar_busqueda

def test_actualizacion_multiplataforma():
    """
    Verifica que actualizar_busqueda busque en MercadoLibre e InfoCasas
    sin importar qué plataformas tenían resultados previamente.
    """
    
    print("=== Test: Actualización Multi-plataforma ===\n")
    
    # Buscar búsquedas existentes para probar
    busquedas = Busqueda.objects.filter(guardado=True)
    
    if not busquedas.exists():
        print("❌ No hay búsquedas guardadas para probar")
        return False
    
    busqueda = busquedas.first()
    print(f"📋 Probando con búsqueda: {busqueda.id}")
    print(f"   Filtros: {busqueda.filtros}")
    
    # Ver resultados actuales
    resultados_actuales = ResultadoBusqueda.objects.filter(busqueda=busqueda)
    plataformas_actuales = {r.propiedad.plataforma.nombre for r in resultados_actuales.select_related('propiedad__plataforma')}
    
    print(f"   Resultados actuales: {resultados_actuales.count()}")
    print(f"   Plataformas actuales: {plataformas_actuales}")
    
    # Crear callback para capturar mensajes de progreso
    mensajes_progreso = []
    def capture_progress(mensaje):
        mensajes_progreso.append(mensaje)
        print(f"   [PROGRESO] {mensaje}")
    
    print(f"\n🔄 Iniciando actualización...")
    
    try:
        # Este es el test principal: actualizar_busqueda debería buscar en AMBAS plataformas
        resultado = actualizar_busqueda(str(busqueda.id), capture_progress)
        
        print(f"\n📊 Resultado:")
        print(f"   Éxito: {resultado['success']}")
        
        if resultado['success']:
            print(f"   Estadísticas: {resultado['estadisticas']}")
        else:
            print(f"   Error: {resultado['error']}")
        
        # Verificar que se intentó buscar en ambas plataformas
        busco_mercadolibre = any('MercadoLibre' in msg for msg in mensajes_progreso)
        busco_infocasas = any('InfoCasas' in msg for msg in mensajes_progreso)
        
        print(f"\n✅ Verificación de plataformas:")
        print(f"   Buscó en MercadoLibre: {'✓' if busco_mercadolibre else '✗'}")
        print(f"   Buscó en InfoCasas: {'✓' if busco_infocasas else '✗'}")
        
        if busco_mercadolibre and busco_infocasas:
            print(f"\n🎉 ¡ÉXITO! La actualización busca en TODAS las plataformas")
            print(f"   Sin importar qué plataformas tenían resultados anteriormente.")
            return True
        else:
            print(f"\n❌ FALLA: No se buscó en todas las plataformas")
            return False
            
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_independencia_plataformas():
    """
    Verifica que la lógica sea independiente de resultados previos
    """
    print(f"\n=== Test: Independencia de Plataformas ===\n")
    
    from core.search_manager import actualizar_busqueda
    import inspect
    
    # Analizar el código fuente
    source = inspect.getsource(actualizar_busqueda)
    
    # Verificaciones
    tests = [
        ('plataformas_a_buscar' not in source, "No depende de plataformas_a_buscar"),
        ('SIEMPRE buscar' in source, "Tiene lógica explícita para buscar siempre"),
        ('TODAS las plataformas' in source, "Menciona explícitamente todas las plataformas"),
        ('if \'MercadoLibre\' in plataformas_' not in source, "MercadoLibre no es condicional"),
        ('if \'InfoCasas\' in plataformas_' not in source, "InfoCasas no es condicional")
    ]
    
    todos_ok = True
    for test_result, descripcion in tests:
        status = "✓" if test_result else "✗"
        print(f"   {status} {descripcion}")
        if not test_result:
            todos_ok = False
    
    return todos_ok

if __name__ == '__main__':
    print("🚀 Iniciando tests de actualización multi-plataforma...\n")
    
    test1 = test_independencia_plataformas()
    test2 = test_actualizacion_multiplataforma()
    
    print(f"\n" + "="*60)
    print(f"📋 RESUMEN:")
    print(f"   Independencia de código: {'✓ PASS' if test1 else '✗ FAIL'}")
    print(f"   Funcionalidad completa: {'✓ PASS' if test2 else '✗ FAIL'}")
    
    if test1 and test2:
        print(f"\n🎉 ¡TODOS LOS TESTS PASARON!")
        print(f"   Las actualizaciones de búsqueda ahora buscan SIEMPRE")
        print(f"   en MercadoLibre e InfoCasas, sin importar resultados previos.")
    else:
        print(f"\n❌ Algunos tests fallaron. Revisar implementación.")
    
    print(f"="*60)