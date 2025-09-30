#!/usr/bin/env python3
"""
Script para verificar usuarios y búsquedas en la BD
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.models import Usuario, Busqueda

def verificar_estado():
    print("🔍 VERIFICACIÓN DEL ESTADO ACTUAL")
    print("=" * 50)
    
    # Usuarios
    usuarios = Usuario.objects.all()
    print(f"\n👥 USUARIOS ({usuarios.count()}):")
    for usuario in usuarios:
        print(f"  • {usuario.email} - {usuario.nombre} (ID: {usuario.id})")
        print(f"    Inmobiliaria: {usuario.inmobiliaria.nombre} (Plan: {usuario.inmobiliaria.plan})")
    
    # Usuario testing específico
    usuario_testing = Usuario.objects.filter(email="testing@example.com").first()
    print(f"\n🧪 USUARIO TESTING:")
    if usuario_testing:
        print(f"  ✅ Encontrado: {usuario_testing.email}")
        print(f"  Plan: {usuario_testing.inmobiliaria.plan}")
        print(f"  Límites: {usuario_testing.inmobiliaria.intervalo_actualizacion_horas}h, {usuario_testing.inmobiliaria.max_actualizaciones_por_dia} act/día")
    else:
        print("  ❌ No encontrado")
    
    # Búsquedas
    busquedas = Busqueda.objects.filter(guardado=True)
    print(f"\n🔍 BÚSQUEDAS GUARDADAS ({busquedas.count()}):")
    for busqueda in busquedas:
        usuario_str = f"{busqueda.usuario.email}" if busqueda.usuario else "Sin usuario"
        print(f"  • {busqueda.nombre_busqueda} (ID: {busqueda.id})")
        print(f"    Usuario: {usuario_str}")
        print(f"    Guardado: {busqueda.guardado}")
        if busqueda.ultima_revision:
            print(f"    Última revisión: {busqueda.ultima_revision}")
        else:
            print(f"    Última revisión: Nunca")
    
    # Búsqueda de prueba específica
    busqueda_test = Busqueda.objects.filter(nombre_busqueda__contains="Test Actualización").first()
    print(f"\n🧪 BÚSQUEDA DE PRUEBA:")
    if busqueda_test:
        print(f"  ✅ Encontrada: {busqueda_test.nombre_busqueda}")
        print(f"  ID: {busqueda_test.id}")
        print(f"  Usuario asignado: {busqueda_test.usuario.email if busqueda_test.usuario else 'None'}")
        print(f"  Guardado: {busqueda_test.guardado}")
        
        # Verificar coincidencia de usuarios
        if usuario_testing and busqueda_test.usuario:
            if usuario_testing.id == busqueda_test.usuario.id:
                print(f"  ✅ Usuario coincide con testing")
            else:
                print(f"  ❌ Usuario NO coincide:")
                print(f"     Testing: {usuario_testing.id} ({usuario_testing.email})")
                print(f"     Búsqueda: {busqueda_test.usuario.id} ({busqueda_test.usuario.email})")
    else:
        print("  ❌ No encontrada")

if __name__ == "__main__":
    verificar_estado()