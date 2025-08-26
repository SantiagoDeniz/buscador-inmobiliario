#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de cookies mejorado
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper import iniciar_driver, cargar_cookies

def test_cookies_local():
    """Probar carga de cookies desde archivo local"""
    print("🧪 Probando carga de cookies desde archivo local...")
    
    driver = iniciar_driver()
    try:
        cargar_cookies(driver, 'mercadolibre_cookies.json')
        
        # Verificar que se cargaron las cookies
        cookies_cargadas = driver.get_cookies()
        print(f"✅ Cookies cargadas desde archivo: {len(cookies_cargadas)}")
        
        # Buscar cookies importantes
        cookie_names = [c['name'] for c in cookies_cargadas]
        important_found = []
        for important in ['_d2id', 'ssid', 'orguseridp']:
            if important in cookie_names:
                important_found.append(important)
        
        if important_found:
            print(f"🔑 Cookies importantes encontradas: {', '.join(important_found)}")
        
        return len(cookies_cargadas) > 0
        
    except Exception as e:
        print(f"❌ Error en test local: {e}")
        return False
    finally:
        driver.quit()

def test_cookies_env():
    """Probar carga de cookies desde variable de entorno"""
    print("\n🧪 Probando carga de cookies desde variable de entorno...")
    
    # Leer cookies del archivo y simular variable de entorno
    try:
        with open('cookies_env.txt', 'r') as f:
            cookies_env = f.read().strip()
        
        # Establecer temporalmente la variable de entorno
        os.environ['MERCADOLIBRE_COOKIES'] = cookies_env
        
        driver = iniciar_driver()
        try:
            cargar_cookies(driver, 'archivo_inexistente.json')  # Esto debería usar la variable de entorno
            
            # Verificar que se cargaron las cookies
            cookies_cargadas = driver.get_cookies()
            print(f"✅ Cookies cargadas desde variable de entorno: {len(cookies_cargadas)}")
            
            # Buscar cookies importantes
            cookie_names = [c['name'] for c in cookies_cargadas]
            important_found = []
            for important in ['_d2id', 'ssid', 'orguseridp']:
                if important in cookie_names:
                    important_found.append(important)
            
            if important_found:
                print(f"🔑 Cookies importantes encontradas: {', '.join(important_found)}")
            
            return len(cookies_cargadas) > 0
            
        except Exception as e:
            print(f"❌ Error en test con variable de entorno: {e}")
            return False
        finally:
            driver.quit()
            # Limpiar variable de entorno
            if 'MERCADOLIBRE_COOKIES' in os.environ:
                del os.environ['MERCADOLIBRE_COOKIES']
                
    except Exception as e:
        print(f"❌ Error preparando test con variable de entorno: {e}")
        return False

def main():
    print("🚀 Iniciando pruebas del sistema de cookies mejorado")
    print("=" * 60)
    
    # Test 1: Cookies desde archivo local
    test1_ok = test_cookies_local()
    
    # Test 2: Cookies desde variable de entorno
    test2_ok = test_cookies_env()
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"{'✅' if test1_ok else '❌'} Carga desde archivo local: {'OK' if test1_ok else 'FALLO'}")
    print(f"{'✅' if test2_ok else '❌'} Carga desde variable de entorno: {'OK' if test2_ok else 'FALLO'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 ¡Todos los tests pasaron! El sistema está listo para producción.")
        print("\n📋 PASOS PARA CONFIGURAR EN RENDER:")
        print("1. Ve a tu dashboard de Render")
        print("2. Selecciona tu servicio web")
        print("3. Ve a 'Environment'")
        print("4. Agrega una nueva variable:")
        print("   - Nombre: MERCADOLIBRE_COOKIES")
        print("   - Valor: (copia el contenido de cookies_env.txt)")
        print("5. Guarda y redespliega")
    else:
        print("\n❌ Algunos tests fallaron. Revisa la configuración.")
    
    return test1_ok and test2_ok

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)
