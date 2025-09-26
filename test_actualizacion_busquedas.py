#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de actualización de búsquedas
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Busqueda, Inmobiliaria, Usuario, Plataforma, Propiedad, ResultadoBusqueda
from core.limits import puede_realizar_accion, get_limites_usuario, puede_actualizar_busqueda_especifica
from core.plans import aplicar_configuracion_plan, PLANES
from django.utils import timezone

def test_sistema_limites():
    """Prueba el sistema de límites"""
    print("🧪 TESTING - Sistema de Límites")
    print("=" * 50)
    
    # Crear inmobiliaria de prueba
    inmobiliaria_test = Inmobiliaria.objects.create(
        nombre="Test Limits Corp",
        plan="basico"
    )
    aplicar_configuracion_plan(inmobiliaria_test, "basico")
    inmobiliaria_test.save()
    
    # Crear usuario de prueba
    usuario_test = Usuario.objects.create(
        nombre="Test User",
        email="test@limits.com", 
        password_hash="test123",
        inmobiliaria=inmobiliaria_test
    )
    
    print(f"✓ Inmobiliaria creada: {inmobiliaria_test.nombre} (Plan: {inmobiliaria_test.plan})")
    print(f"✓ Usuario creado: {usuario_test.email}")
    print(f"  Límites: {inmobiliaria_test.intervalo_actualizacion_horas}h, {inmobiliaria_test.max_actualizaciones_por_dia} act/día, {inmobiliaria_test.max_busquedas_nuevas_por_dia} búsq/día")
    
    # Test 1: Nueva búsqueda
    puede, mensaje = puede_realizar_accion(usuario_test, 'nueva_busqueda')
    print(f"\n📋 Test 1 - Nueva búsqueda: {'✓' if puede else '✗'} - {mensaje}")
    
    # Test 2: Verificar límites del usuario
    limites = get_limites_usuario(usuario_test)
    print(f"\n📊 Test 2 - Límites usuario:")
    print(f"  Búsquedas nuevas: {limites['busquedas_nuevas']['usadas']}/{limites['busquedas_nuevas']['limite']} (restantes: {limites['busquedas_nuevas']['restantes']})")
    print(f"  Actualizaciones: {limites['actualizaciones']['usadas']}/{limites['actualizaciones']['limite']} (restantes: {limites['actualizaciones']['restantes']})")
    
    # Test 3: Crear búsqueda y probar actualización
    plataforma, _ = Plataforma.objects.get_or_create(
        nombre="MercadoLibre",
        defaults={'descripcion': 'MercadoLibre Uruguay'}
    )
    
    busqueda_test = Busqueda.objects.create(
        nombre_busqueda="Test Actualización",
        texto_original="apartamento montevideo",
        filtros={"tipo": "apartamento", "departamento": "Montevideo"},
        guardado=True,
        usuario=usuario_test
    )
    
    print(f"\n🔍 Test 3 - Búsqueda creada: {busqueda_test.nombre_busqueda}")
    
    # Probar actualización inmediata (debería funcionar)
    puede, mensaje, tiempo_restante = puede_actualizar_busqueda_especifica(busqueda_test)
    print(f"  Puede actualizar inmediatamente: {'✓' if puede else '✗'} - {mensaje}")
    
    # Simular actualización reciente
    busqueda_test.ultima_revision = timezone.now()
    busqueda_test.save()
    
    puede, mensaje, tiempo_restante = puede_actualizar_busqueda_especifica(busqueda_test)
    print(f"  Después de actualizar: {'✓' if puede else '✗'} - {mensaje}")
    if tiempo_restante:
        print(f"    Tiempo restante: {tiempo_restante:.1f} horas")
    
    # Test 4: Usuario de testing
    print(f"\n🧪 Test 4 - Usuario Testing:")
    usuario_testing = Usuario.objects.filter(email="testing@example.com").first()
    if usuario_testing:
        puede, mensaje = puede_realizar_accion(usuario_testing, 'nueva_busqueda')
        print(f"  Nueva búsqueda (testing): {'✓' if puede else '✗'} - {mensaje}")
        
        limites_testing = get_limites_usuario(usuario_testing)
        print(f"  Modo testing: {limites_testing['modo_testing']}")
    else:
        print("  ⚠ Usuario de testing no encontrado")
    
    # Cleanup
    print(f"\n🧹 Limpieza:")
    busqueda_test.delete()
    usuario_test.delete()
    inmobiliaria_test.delete()
    print("  ✓ Datos de prueba eliminados")

def test_planes_configuracion():
    """Prueba la configuración de planes"""
    print(f"\n📋 TESTING - Configuración de Planes")
    print("=" * 50)
    
    for plan_nombre, config in PLANES.items():
        print(f"\n🏷️  Plan: {plan_nombre}")
        print(f"   Intervalo actualización: {config['intervalo_actualizacion_horas']}h")
        print(f"   Max actualizaciones/día: {config['max_actualizaciones_por_dia']}")
        print(f"   Max búsquedas nuevas/día: {config['max_busquedas_nuevas_por_dia']}")

def main():
    """Función principal"""
    print("🚀 SISTEMA DE ACTUALIZACIÓN DE BÚSQUEDAS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    try:
        test_planes_configuracion()
        test_sistema_limites()
        
        print(f"\n✅ TODOS LOS TESTS COMPLETADOS")
        print("=" * 60)
        
        # Mostrar endpoints disponibles
        print(f"\n🌐 ENDPOINTS DISPONIBLES:")
        print("  GET  /verificar_limites/              - Verificar límites del usuario")
        print("  POST /actualizar/<busqueda_id>/       - Actualizar búsqueda específica") 
        print("  GET  /verificar_actualizable/<id>/    - Verificar si búsqueda puede actualizarse")
        print("  GET  /estado_actualizaciones/         - Estado de todas las búsquedas")
        
        print(f"\n🎯 PRUEBA MANUAL:")
        print("  1. Ejecuta: .\.venv\Scripts\activate ; daphne -b 0.0.0.0 -p 10000 buscador.asgi:application")
        print("  2. Ve a http://localhost:10000")
        print("  3. Crea una búsqueda con 'Buscar y Guardar'")
        print("  4. Verifica que aparece el botón 'Actualizar búsqueda'")
        print("  5. Haz clic para probar la funcionalidad")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()