#!/usr/bin/env python3
"""
Script para verificar el estado de las cookies de MercadoLibre
y generar nuevas si es necesario
"""

import os
import sys
import json
import time
import django
from django.conf import settings

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper import iniciar_driver, cargar_cookies, manejar_popups_cookies, verificar_necesita_login

def verificar_cookies_actuales():
    """
    Verifica si las cookies actuales funcionan correctamente
    """
    print("🔍 Verificando cookies actuales...")
    
    if not os.path.exists('mercadolibre_cookies.json'):
        print("❌ No se encontró el archivo mercadolibre_cookies.json")
        return False
    
    driver = iniciar_driver()
    try:
        # Intentar cargar cookies y verificar si funcionan
        cookies_ok = cargar_cookies(driver, 'mercadolibre_cookies.json')
        
        if not cookies_ok:
            print("❌ Las cookies no funcionan correctamente")
            return False
        
        # Hacer una búsqueda de prueba
        print("🧪 Probando búsqueda para verificar funcionalidad...")
        driver.get("https://listado.mercadolibre.com.uy/inmuebles/apartamentos/venta/montevideo")
        time.sleep(5)
        
        # Verificar si todavía pide login después de la navegación
        if verificar_necesita_login(driver):
            print("❌ MercadoLibre sigue pidiendo login después de cargar cookies")
            return False
        
        # Verificar si puede encontrar resultados
        try:
            resultados = driver.find_elements("css selector", ".ui-search-result")
            if len(resultados) > 0:
                print(f"✅ Cookies funcionando correctamente - encontrados {len(resultados)} resultados")
                return True
            else:
                print("⚠️ No se encontraron resultados, pero no se requiere login")
                return True
        except Exception as e:
            print(f"⚠️ Error verificando resultados: {e}")
            return True  # Si no hay error de login, consideramos que funciona
        
    except Exception as e:
        print(f"❌ Error verificando cookies: {e}")
        return False
    finally:
        driver.quit()

def obtener_nuevas_cookies():
    """
    Guía al usuario para obtener nuevas cookies manualmente
    """
    print("\n" + "="*60)
    print("🍪 GUÍA PARA OBTENER NUEVAS COOKIES")
    print("="*60)
    print("Las cookies actuales han expirado o no funcionan.")
    print("Para obtener nuevas cookies, sigue estos pasos:")
    print()
    print("1. Abre Chrome y ve a https://www.mercadolibre.com.uy")
    print("2. Inicia sesión con tu cuenta (si tienes una)")
    print("3. Acepta todos los popups de cookies")
    print("4. Navega a la sección de inmuebles")
    print("5. Presiona F12 para abrir DevTools")
    print("6. Ve a la pestaña 'Application' > 'Cookies' > 'https://www.mercadolibre.com.uy'")
    print("7. Haz clic derecho en cualquier cookie y selecciona 'Copy all'")
    print()
    print("Alternativamente, usa una extensión de Chrome como:")
    print("- 'Cookie Editor' o 'EditThisCookie'")
    print("- Exporta las cookies en formato JSON")
    print()
    print("8. Guarda las cookies en 'mercadolibre_cookies.json'")
    print("9. Ejecuta este script nuevamente para verificar")
    print("="*60)

def mostrar_info_cookies():
    """
    Muestra información sobre las cookies actuales
    """
    if not os.path.exists('mercadolibre_cookies.json'):
        print("❌ No se encontró el archivo mercadolibre_cookies.json")
        return
    
    try:
        with open('mercadolibre_cookies.json', 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        print(f"\n📊 INFORMACIÓN DE COOKIES ACTUALES:")
        print(f"Total de cookies: {len(cookies)}")
        
        # Analizar cookies por tipo
        session_cookies = []
        persistent_cookies = []
        expired_cookies = []
        important_cookies = []
        
        current_time = time.time()
        
        important_names = ['ssid', '_d2id', 'orguseridp', 'nsa_rotok', 'ftid']
        
        for cookie in cookies:
            name = cookie.get('name', 'sin_nombre')
            
            # Verificar si es importante
            if name in important_names:
                important_cookies.append(name)
            
            # Verificar expiración
            if 'expirationDate' in cookie:
                if cookie['expirationDate'] < current_time:
                    expired_cookies.append(name)
                else:
                    persistent_cookies.append(name)
            elif 'session' in cookie and cookie['session']:
                session_cookies.append(name)
            else:
                persistent_cookies.append(name)
        
        print(f"Cookies de sesión: {len(session_cookies)}")
        print(f"Cookies persistentes: {len(persistent_cookies)}")
        print(f"Cookies expiradas: {len(expired_cookies)}")
        print(f"Cookies importantes encontradas: {important_cookies}")
        
        if expired_cookies:
            print(f"\n⚠️ Cookies expiradas: {expired_cookies[:5]}{'...' if len(expired_cookies) > 5 else ''}")
        
        if len(expired_cookies) > len(cookies) * 0.3:  # Más del 30% expiradas
            print(f"\n❌ Muchas cookies han expirado ({len(expired_cookies)}/{len(cookies)})")
            print(f"Se recomienda obtener nuevas cookies")
        elif important_cookies:
            print(f"\n✅ Cookies importantes presentes: {', '.join(important_cookies)}")
        else:
            print(f"\n⚠️ No se encontraron cookies importantes")
            
    except Exception as e:
        print(f"❌ Error analizando cookies: {e}")

def main():
    print("🍪 VERIFICADOR DE COOKIES DE MERCADOLIBRE")
    print("="*50)
    
    # Mostrar información actual
    mostrar_info_cookies()
    
    # Verificar si funcionan
    cookies_funcionan = verificar_cookies_actuales()
    
    if cookies_funcionan:
        print("\n✅ ¡Las cookies funcionan correctamente!")
        
        # Generar variable de entorno si no existe
        if not os.path.exists('cookies_env.txt'):
            print("\n🔧 Generando variable de entorno para Render...")
            os.system('python convert_cookies_to_env.py')
        
        print("\n📋 CONFIGURACIÓN PARA RENDER:")
        print("1. Ve a tu dashboard de Render")
        print("2. Environment > Add Environment Variable")
        print("3. Name: MERCADOLIBRE_COOKIES")
        print("4. Value: (copia el contenido de cookies_env.txt)")
        print("5. Save y redeploy")
        
    else:
        print("\n❌ Las cookies no funcionan correctamente")
        obtener_nuevas_cookies()
    
    return cookies_funcionan

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Verificación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)
import django
from datetime import datetime
from django.conf import settings

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.scraper import iniciar_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def verificar_cookies_actuales():
    """Verifica si las cookies actuales funcionan"""
    try:
        print("🔍 Verificando cookies actuales...")
        
        driver = iniciar_driver()
        
        # Cargar cookies si existen
        if os.path.exists('mercadolibre_cookies.json'):
            with open('mercadolibre_cookies.json', 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            driver.get('https://www.mercadolibre.com.uy')
            time.sleep(2)
            
            for cookie in cookies_data:
                try:
                    # Limpiar campos incompatibles
                    clean_cookie = {k: v for k, v in cookie.items() 
                                  if k not in ['sameSite', 'storeId', 'id']}
                    if 'expirationDate' in clean_cookie:
                        clean_cookie['expiry'] = int(clean_cookie['expirationDate'])
                        del clean_cookie['expirationDate']
                    elif 'expiry' in clean_cookie:
                        clean_cookie['expiry'] = int(clean_cookie['expiry'])
                    
                    driver.add_cookie(clean_cookie)
                except:
                    continue
            
            # Refrescar y probar
            driver.refresh()
            time.sleep(3)
            
            # Verificar si hay redirección a login
            current_url = driver.current_url.lower()
            if 'login' in current_url or 'registro' in current_url:
                print("❌ Las cookies actuales no funcionan - redirección a login")
                driver.quit()
                return False
            
            # Verificar si podemos acceder a una página de búsqueda
            try:
                driver.get('https://listado.mercadolibre.com.uy/inmuebles/departamentos/')
                time.sleep(3)
                
                # Verificar si aparece popup de login
                login_indicators = [
                    'Iniciar sesión',
                    'Ingresa tu email',
                    'Crear cuenta',
                    'login-form'
                ]
                
                page_source = driver.page_source.lower()
                for indicator in login_indicators:
                    if indicator.lower() in page_source:
                        print(f"❌ Detectado indicador de login: {indicator}")
                        driver.quit()
                        return False
                
                print("✅ Las cookies actuales funcionan correctamente")
                driver.quit()
                return True
                
            except Exception as e:
                print(f"❌ Error verificando funcionalidad: {e}")
                driver.quit()
                return False
        else:
            print("❌ No se encontró archivo de cookies")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando cookies: {e}")
        return False

def obtener_nuevas_cookies():
    """Obtiene nuevas cookies interactivamente"""
    print("\n🔄 Necesitas obtener nuevas cookies...")
    print("\nPASOS PARA OBTENER COOKIES ACTUALIZADAS:")
    print("="*60)
    print("1. Abre Chrome en modo normal (no headless)")
    print("2. Ve a https://www.mercadolibre.com.uy")
    print("3. Inicia sesión con tu cuenta")
    print("4. Navega a una búsqueda de inmuebles")
    print("5. Abre Developer Tools (F12)")
    print("6. Ve a la pestaña 'Application' > 'Cookies'")
    print("7. Selecciona el dominio .mercadolibre.com.uy")
    print("8. Usa una extensión como 'Cookie-Editor' para exportar")
    print("9. Guarda las cookies en 'mercadolibre_cookies.json'")
    print("="*60)
    
    # Alternativa automatizada (sin implementar completamente)
    print("\n💡 ALTERNATIVA AUTOMATIZADA:")
    print("Se podría implementar un modo interactivo donde:")
    print("- Se abre Chrome visible")
    print("- Te permite hacer login manualmente") 
    print("- Extrae las cookies automáticamente")
    print("¿Te interesa esta funcionalidad? (s/n): ", end="")
    
    respuesta = input().lower()
    if respuesta == 's':
        print("\n🚧 Esta funcionalidad se puede implementar...")
        print("Por ahora, sigue los pasos manuales descritos arriba.")
    
    return False

def main():
    print("🍪 VERIFICADOR Y ACTUALIZADOR DE COOKIES DE MERCADOLIBRE")
    print("="*65)
    
    # Verificar si las cookies actuales funcionan
    cookies_funcionan = verificar_cookies_actuales()
    
    if cookies_funcionan:
        print("\n🎉 ¡Las cookies están funcionando correctamente!")
        print("\n📋 PARA CONFIGURAR EN RENDER:")
        print("1. Ejecuta: python convert_cookies_to_env.py")
        print("2. Copia el contenido de cookies_env.txt")
        print("3. En Render, agrega variable MERCADOLIBRE_COOKIES con ese valor")
        
        # Mostrar información sobre las cookies
        try:
            with open('mercadolibre_cookies.json', 'r') as f:
                cookies = json.load(f)
            
            print(f"\n📊 Información de cookies:")
            print(f"   Total de cookies: {len(cookies)}")
            
            # Contar cookies importantes
            important = ['_d2id', 'ssid', 'orguseridp', '_csrf']
            found_important = []
            for cookie in cookies:
                if cookie.get('name') in important:
                    found_important.append(cookie.get('name'))
            
            if found_important:
                print(f"   Cookies importantes: {', '.join(found_important)}")
            
            # Verificar fechas de expiración
            current_time = time.time()
            expired_count = 0
            for cookie in cookies:
                if 'expirationDate' in cookie and cookie['expirationDate'] < current_time:
                    expired_count += 1
            
            if expired_count > 0:
                print(f"   ⚠️  Cookies expiradas: {expired_count}")
            else:
                print("   ✅ Todas las cookies vigentes")
                
        except Exception as e:
            print(f"   Error leyendo cookies: {e}")
    else:
        print("\n❌ Las cookies no están funcionando")
        obtener_nuevas_cookies()
        return False
    
    return cookies_funcionan

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)
