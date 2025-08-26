#!/usr/bin/env python3
"""
Test simple para verificar funciones de cookies
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

def test_imports():
    """Probar que todos los imports funcionan"""
    try:
        from core.scraper import iniciar_driver, cargar_cookies, manejar_popups_cookies, verificar_necesita_login
        print("✅ Todos los imports funcionan correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False

def test_cookies_info():
    """Mostrar información sobre las cookies actuales"""
    import json
    import time
    
    if not os.path.exists('mercadolibre_cookies.json'):
        print("❌ No se encontró mercadolibre_cookies.json")
        return False
    
    try:
        with open('mercadolibre_cookies.json', 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        print(f"📊 Total de cookies: {len(cookies)}")
        
        current_time = time.time()
        expired_count = 0
        important_cookies = []
        
        important_names = ['ssid', '_d2id', 'orguseridp', 'nsa_rotok', 'ftid']
        
        for cookie in cookies:
            name = cookie.get('name', 'sin_nombre')
            
            if name in important_names:
                important_cookies.append(name)
            
            if 'expirationDate' in cookie:
                if cookie['expirationDate'] < current_time:
                    expired_count += 1
        
        print(f"📅 Cookies expiradas: {expired_count}/{len(cookies)}")
        print(f"🔑 Cookies importantes encontradas: {important_cookies}")
        
        return len(important_cookies) > 0
        
    except Exception as e:
        print(f"❌ Error analizando cookies: {e}")
        return False

def main():
    print("🧪 TEST SIMPLE DEL SISTEMA DE COOKIES")
    print("=" * 50)
    
    # Test 1: Imports
    print("\n1. Verificando imports...")
    imports_ok = test_imports()
    
    # Test 2: Info de cookies
    print("\n2. Analizando cookies actuales...")
    cookies_info_ok = test_cookies_info()
    
    print("\n" + "=" * 50)
    print("📋 RESUMEN:")
    print(f"{'✅' if imports_ok else '❌'} Imports: {'OK' if imports_ok else 'FALLO'}")
    print(f"{'✅' if cookies_info_ok else '❌'} Cookies: {'OK' if cookies_info_ok else 'FALLO'}")
    
    if imports_ok and cookies_info_ok:
        print("\n🎉 Tests básicos pasaron. El sistema debería funcionar.")
        print("\n💡 PRÓXIMOS PASOS:")
        print("1. Prueba una búsqueda simple para verificar funcionalidad")
        print("2. Si hay problemas de login, actualiza las cookies")
        print("3. Para producción, configura MERCADOLIBRE_COOKIES en Render")
    else:
        print("\n❌ Algunos tests fallaron. Revisa la configuración.")

if __name__ == "__main__":
    main()
