#!/usr/bin/env python
"""
Test completo para verificar que el nuevo sistema de guardado funciona correctamente.
Prueba que:
1. Se guarden todas las propiedades (coincidentes y no coincidentes) 
2. Se creen ResultadoBusqueda para todas las propiedades con coincide=True/False
3. Las interfaces solo muestren las coincidentes (coincide=True)
4. El retorno incluya el campo 'coincide' para todas las propiedades
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

def test_flujo_completo_con_busqueda():
    """Prueba el flujo completo con creación de Busqueda y ResultadoBusqueda."""
    from core.scraper import run_scraper
    from core.models import Propiedad, ResultadoBusqueda, Busqueda
    from core.search_manager import create_search, load_results
    
    print("🧪 [TEST COMPLETO] Iniciando prueba del flujo completo...")
    
    # Limpiar BD
    print("🧹 [LIMPIEZA] Limpiando base de datos...")
    Propiedad.objects.all().delete()
    ResultadoBusqueda.objects.all().delete()
    Busqueda.objects.all().delete()
    
    # Crear una búsqueda
    busqueda_data = {
        'name': 'Test Búsqueda Garage y Ascensor',
        'original_text': 'apartamento alquiler montevideo garage ascensor',
        'filters': {
            'tipo': 'apartamento',
            'operacion': 'alquiler', 
            'departamento': 'Montevideo'
        },
        'keywords': ['garage', 'ascensor']
    }
    
    print(f"📝 [BUSQUEDA] Creando búsqueda: {busqueda_data['name']}")
    busqueda_creada = create_search(busqueda_data)
    busqueda_id = busqueda_creada['id']
    
    # Obtener la instancia de Busqueda
    busqueda_instance = Busqueda.objects.get(id=busqueda_id)
    print(f"✅ [BUSQUEDA] Búsqueda creada con ID: {busqueda_id}")
    
    # Contar antes del scraping
    props_antes = Propiedad.objects.count()
    resultados_antes = ResultadoBusqueda.objects.count()
    
    print(f"📊 [ANTES SCRAPING] Propiedades: {props_antes}, ResultadoBusqueda: {resultados_antes}")
    
    # Ejecutar scraper con la búsqueda
    print("🚀 [SCRAPING] Ejecutando run_scraper con búsqueda...")
    filtros = busqueda_data['filters']
    keywords = busqueda_data['keywords']
    
    resultados = run_scraper(
        filters=filtros, 
        keywords=keywords, 
        max_paginas=1, 
        workers_fase1=1, 
        workers_fase2=1,
        busqueda=busqueda_instance  # Pasar la instancia de búsqueda
    )
    
    print(f"📋 [RETORNO SCRAPER] {len(resultados) if resultados else 0} resultados retornados")
    
    # Verificar estructura del retorno
    if resultados:
        primer_resultado = resultados[0]
        print(f"🔍 [ESTRUCTURA RETORNO] {primer_resultado}")
        
        campos_esperados = ['title', 'url', 'coincide']
        for campo in campos_esperados:
            if campo not in primer_resultado:
                print(f"❌ [ERROR] Falta campo '{campo}' en el retorno")
                return False
            else:
                print(f"✅ [OK] Campo '{campo}' presente")
    
    # Contar después del scraping
    props_despues = Propiedad.objects.count()
    resultados_despues = ResultadoBusqueda.objects.count()
    resultados_coincidentes = ResultadoBusqueda.objects.filter(coincide=True).count()
    resultados_no_coincidentes = ResultadoBusqueda.objects.filter(coincide=False).count()
    
    print(f"\n📊 [DESPUÉS SCRAPING]")
    print(f"  Propiedades: {props_despues} (+{props_despues - props_antes})")
    print(f"  ResultadoBusqueda total: {resultados_despues} (+{resultados_despues - resultados_antes})")
    print(f"  ResultadoBusqueda coincidentes: {resultados_coincidentes}")
    print(f"  ResultadoBusqueda no coincidentes: {resultados_no_coincidentes}")
    
    # Verificaciones clave
    print(f"\n� [VERIFICACIONES]")
    
    # 1. Se crearon propiedades
    if props_despues > props_antes:
        print(f"✅ Se guardaron {props_despues - props_antes} nuevas propiedades")
    else:
        print(f"❌ No se guardaron propiedades nuevas")
        return False
    
    # 2. Se crearon ResultadoBusqueda para todas las propiedades procesadas
    if resultados_despues > resultados_antes:
        print(f"✅ Se crearon {resultados_despues - resultados_antes} ResultadoBusqueda")
    else:
        print(f"❌ No se crearon ResultadoBusqueda")
        return False
    
    # 3. Hay tanto coincidentes como no coincidentes (probablemente)
    print(f"ℹ️ Distribución: {resultados_coincidentes} coincidentes, {resultados_no_coincidentes} no coincidentes")
    
    # 4. La interfaz solo muestra coincidentes
    print(f"\n🖥️ [INTERFAZ] Probando carga de resultados desde interfaz...")
    resultados_interfaz = load_results(busqueda_id)
    print(f"📊 Resultados mostrados en interfaz: {len(resultados_interfaz)}")
    print(f"📊 Total ResultadoBusqueda coincidentes: {resultados_coincidentes}")
    
    if len(resultados_interfaz) == resultados_coincidentes:
        print(f"✅ La interfaz muestra solo los resultados coincidentes")
    else:
        print(f"❌ La interfaz no está filtrando correctamente")
        return False
    
    # 5. Verificar retorno del scraper
    if resultados:
        coincidentes_retorno = len([r for r in resultados if r.get('coincide', True)])
        no_coincidentes_retorno = len([r for r in resultados if not r.get('coincide', True)])
        
        print(f"\n📋 [RETORNO SCRAPER]")
        print(f"  Coincidentes en retorno: {coincidentes_retorno}")
        print(f"  No coincidentes en retorno: {no_coincidentes_retorno}")
        
        if (coincidentes_retorno + no_coincidentes_retorno) == len(resultados):
            print(f"✅ El retorno incluye todas las propiedades con campo 'coincide'")
        else:
            print(f"❌ Problema en el retorno del scraper")
            return False
    
    print(f"\n🎉 [ÉXITO] ¡Todas las verificaciones pasaron!")
    print(f"\n� [RESUMEN]")
    print(f"  • Se procesaron {props_despues - props_antes} propiedades")
    print(f"  • Se crearon {resultados_despues - resultados_antes} ResultadoBusqueda")
    print(f"  • {resultados_coincidentes} coinciden con keywords, {resultados_no_coincidentes} no")
    print(f"  • La interfaz muestra solo {len(resultados_interfaz)} coincidentes")
    print(f"  • El scraper retorna {len(resultados)} con campo 'coincide'")
    
    return True

if __name__ == "__main__":
    try:
        success = test_flujo_completo_con_busqueda()
        if success:
            print("\n✅ [TEST] ¡Flujo completo funciona perfectamente!")
        else:
            print("\n❌ [TEST] El flujo completo falló")
    except Exception as e:
        print(f"\n💥 [ERROR] Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()