#!/usr/bin/env python
"""
Prueba de la interfaz web con diferentes plataformas
"""

import requests
import json
import time

def test_web_interface():
    """Prueba la interfaz web con diferentes plataformas"""
    base_url = "http://localhost:10000"
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(base_url)
        if response.status_code != 200:
            print(f"❌ Servidor no accesible: {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está corriendo en localhost:10000?")
        return False
    
    print("✅ Servidor web accesible")
    
    # Verificar que la página incluye el selector de plataforma
    content = response.text
    if 'id="plataforma"' in content:
        print("✅ Selector de plataforma encontrado en la página")
    else:
        print("❌ Selector de plataforma NO encontrado")
        return False
    
    # Verificar opciones del selector
    if 'Todas las plataformas' in content:
        print("✅ Opción 'Todas las plataformas' encontrada")
    else:
        print("❌ Opción 'Todas las plataformas' NO encontrada")
        return False
        
    if 'InfoCasas' in content:
        print("✅ Opción 'InfoCasas' encontrada")
    else:
        print("❌ Opción 'InfoCasas' NO encontrada")
        return False
    
    print("✅ Interface web configurada correctamente")
    return True

def test_fallback_search():
    """Prueba el endpoint HTTP fallback con diferentes plataformas"""
    fallback_url = "http://localhost:10000/http_search_fallback/"
    
    # Test con MercadoLibre
    print("\n🔍 Probando HTTP fallback con MercadoLibre...")
    payload_ml = {
        "texto": "apartamento 2 dormitorios",
        "filtros": {"operacion": "alquiler", "tipo": "apartamento"},
        "guardar": False,
        "name": "Test MercadoLibre",
        "plataforma": "mercadolibre"
    }
    
    try:
        response = requests.post(
            fallback_url, 
            data=json.dumps(payload_ml),
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ MercadoLibre: {len(data.get('results', []))} resultados")
            else:
                print(f"❌ MercadoLibre falló: {data.get('message', 'Error desconocido')}")
        else:
            print(f"❌ MercadoLibre error HTTP: {response.status_code}")
    except requests.Timeout:
        print("⏰ MercadoLibre: timeout (esto es normal en pruebas rápidas)")
    except Exception as e:
        print(f"❌ MercadoLibre error: {e}")
    
    # Test con InfoCasas
    print("\n🔍 Probando HTTP fallback con InfoCasas...")
    payload_ic = {
        "texto": "apartamento 2 dormitorios",
        "filtros": {"operacion": "alquiler", "tipo": "apartamento"},
        "guardar": False,
        "name": "Test InfoCasas",
        "plataforma": "infocasas"
    }
    
    try:
        response = requests.post(
            fallback_url, 
            data=json.dumps(payload_ic),
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ InfoCasas: {len(data.get('results', []))} resultados")
            else:
                print(f"❌ InfoCasas falló: {data.get('message', 'Error desconocido')}")
        else:
            print(f"❌ InfoCasas error HTTP: {response.status_code}")
    except requests.Timeout:
        print("⏰ InfoCasas: timeout (esto es normal en pruebas rápidas)")
    except Exception as e:
        print(f"❌ InfoCasas error: {e}")
    
    return True

def main():
    print("🌐 Probando integración web de InfoCasas")
    print("=" * 50)
    
    # Test 1: Interface web
    print("📱 Test 1: Interface web")
    web_ok = test_web_interface()
    
    if not web_ok:
        print("❌ La interface web tiene problemas. Abortando.")
        return
    
    # Test 2: HTTP Fallback (opcional, puede ser lento)
    print("\n🔄 Test 2: HTTP Fallback (puede ser lento)")
    choice = input("¿Ejecutar pruebas HTTP? Puede tomar 1-2 minutos (y/n): ").lower()
    if choice == 'y':
        test_fallback_search()
    else:
        print("⏭️  Saltando pruebas HTTP")
    
    print(f"\n🎉 Integración web completada!")
    print("💡 Puedes probar manualmente en: http://localhost:10000")

if __name__ == "__main__":
    main()