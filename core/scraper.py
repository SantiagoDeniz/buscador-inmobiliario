# Importar helpers movidos a submódulos
from core.scraper.url_builder import build_mercadolibre_url, normalizar_para_url
from core.scraper.progress import send_progress_update, tomar_captura_debug
from core.scraper.browser import manejar_popups_cookies, verificar_necesita_login, cargar_cookies
from core.scraper.constants import HEADERS
from core.scraper.extractors import parse_rango, scrape_detalle_con_requests, recolectar_urls_de_pagina
from core.scraper.mercadolibre import extraer_total_resultados_mercadolibre, scrape_mercadolibre
from core.scraper.run import run_scraper

# --- Función iniciar_driver mejorada para contenedores ---
def iniciar_driver():
    chrome_options = Options()

    # Configuraciones básicas para headless
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # Configuraciones adicionales para contenedores/Render
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Acelera carga
    chrome_options.add_argument("--disable-javascript")  # Solo necesitamos HTML
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-crash-reporter")
    chrome_options.add_argument("--disable-oopr-debug-crash-dump")
    chrome_options.add_argument("--no-crash-upload")
    chrome_options.add_argument("--disable-low-res-tiling")
    chrome_options.add_argument("--memory-pressure-off")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        stealth(driver, languages=["es-ES", "es"], vendor="Google Inc.", platform="Win32",
                webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)

        # Verificar que el driver funciona
        driver.set_page_load_timeout(30)
        print("✅ [CHROME] Driver iniciado correctamente")
        return driver

    except Exception as e:
        print(f"❌ [CHROME] Error iniciando driver: {e}")
        raise

# --- Scraper con Selenium y filtrado detallado para MercadoLibre ---
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json
import unicodedata
import os
import re
import concurrent.futures
from core.models import Propiedad, Plataforma
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService

from django.conf import settings

try:
    from selenium_stealth import stealth
except ImportError:
    print("⚠️ selenium-stealth no está instalado, funcionará sin stealth")
    def stealth(driver, **kwargs):
        pass  # Función dummy si no está instalado

# --- Utilidades compartidas ---
def stemming_basico(palabra: str) -> str:
    """Stemming básico para español. Remueve sufijos comunes.
    No es perfecto pero ayuda a aproximar coincidencias.
    """
    try:
        palabra = str(palabra)
    except Exception:
        return ""
    sufijos = ['oso', 'osa', 'idad', 'cion', 'sion', 'ero', 'era', 'ado', 'ada']
    for sufijo in sufijos:
        if palabra.endswith(sufijo) and len(palabra) > len(sufijo) + 3:
            return palabra[:-len(sufijo)]
    return palabra

def extraer_variantes_keywords(keywords_filtradas):
    """Acepta lista de strings o de dicts {'texto','sinonimos',...} y devuelve lista de variantes de texto."""
    variantes = []
    if not keywords_filtradas:
        return variantes
    for kw in keywords_filtradas:
        if isinstance(kw, dict):
            t = kw.get('texto')
            if t:
                variantes.append(str(t))
            for s in kw.get('sinonimos', []) or []:
                if s:
                    variantes.append(str(s))
        else:
            variantes.append(str(kw))
    # Quitar duplicados preservando orden
    seen = set()
    unicos = []
    for v in variantes:
        if v not in seen:
            seen.add(v)
            unicos.append(v)
    return unicos

from datetime import datetime

try:
    from selenium_stealth import stealth
except ImportError:
    # Si selenium-stealth no está instalado, define un stub
    def stealth(*args, **kwargs):
        pass
# HEADERS ahora viven en core.scraper.constants

from core.scraper.url_builder import build_mercadolibre_url, normalizar_para_url

def manejar_popups_cookies(driver):
    """
    Maneja popups de cookies y avisos de MercadoLibre
    """
    popups_manejados = 0
    
    try:
        # Esperar un momento para que aparezcan los popups
        time.sleep(2)
        
        # Lista de selectores para cerrar popups de cookies
        selectores_popup_cookies = [
            "button[data-testid='action:understood-button']",  # ML nuevo
            "button[data-testid='cookies-policy-banner-accept']",  # ML cookies
            ".cookie-consent-banner-opt-out__action button",  # ML cookies alternativo
            "[data-testid='action:understood-button']",  # ML general
            ".ui-cookie-consent__accept",  # ML viejo
            "button:contains('Entendido')",  # Texto genérico
            "button:contains('Aceptar cookies')",  # Texto genérico
            "button:contains('Continuar')",  # Texto genérico
            ".cookie-banner button",  # Banner genérico
        ]
        
        for selector in selectores_popup_cookies:
            try:
                from selenium.common.exceptions import TimeoutException, NoSuchElementException
                elemento = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                elemento.click()
                popups_manejados += 1
                print(f"[scraper] Popup de cookies cerrado: {selector}")
                time.sleep(1)
                break  # Solo cerrar un popup por vez
            except (TimeoutException, NoSuchElementException):
                continue
        
        # Manejar popup de localización si aparece
        try:
            location_popup = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='action:modal-dismissed']"))
            )
            location_popup.click()
            popups_manejados += 1
            print(f"[scraper] Popup de localización cerrado")
            time.sleep(1)
        except (TimeoutException, NoSuchElementException):
            pass
            
    except Exception as e:
        print(f"[scraper] Error manejando popups: {e}")
    
    return popups_manejados > 0


def verificar_necesita_login(driver):
    """
    Verifica si MercadoLibre está pidiendo login/registro
    """
    try:
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        
        # Selectores que indican necesidad de login
        selectores_login = [
            ".nav-menu-item-link[href*='registration']",  # Link de registro
            "[data-testid='action:login-button']",  # Botón de login
            "a[href*='login']",  # Links de login
            "button:contains('Iniciar sesión')",  # Texto de login
            ".login-button",  # Clase de login
        ]
        
        for selector in selectores_login:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                if elemento.is_displayed():
                    print(f"[scraper] ⚠️ Detectado requerimiento de login: {selector}")
                    return True
            except (NoSuchElementException, TimeoutException):
                continue
        
        # Verificar por URL
        current_url = driver.current_url
        if any(path in current_url.lower() for path in ['login', 'registration', 'signin', 'signup']):
            print(f"[scraper] ⚠️ Detectado requerimiento de login por URL: {current_url}")
            return True
        
        # Verificar por título de página
        title = driver.title.lower()
        if any(word in title for word in ['login', 'iniciar', 'registr', 'ingresar']):
            print(f"[scraper] ⚠️ Detectado requerimiento de login por título: {driver.title}")
            return True
        
        return False
        
    except Exception as e:
        print(f"[scraper] Error verificando necesidad de login: {e}")
        return False


def cargar_cookies(driver, cookies_path):
    """
    Carga cookies desde archivo local o variable de entorno para producción
    Con manejo mejorado de popups y verificación de login
    """
    cookies_data = None
    
    # Primero intentar cargar desde variable de entorno (para producción)
    mercadolibre_cookies_env = os.environ.get('MERCADOLIBRE_COOKIES')
    if mercadolibre_cookies_env:
        try:
            cookies_data = json.loads(mercadolibre_cookies_env)
            print(f"[scraper] Cookies cargadas desde variable de entorno ({len(cookies_data)} cookies)")
        except json.JSONDecodeError as e:
            print(f"[scraper] Error decodificando cookies de variable de entorno: {e}")
    
    # Si no hay cookies en variable de entorno, intentar archivo local
    if not cookies_data:
        if not os.path.exists(cookies_path):
            print(f"[scraper] Archivo de cookies no encontrado: {cookies_path}")
            print(f"[scraper] Tip: Para producción, configura la variable MERCADOLIBRE_COOKIES")
            return False
        try:
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            print(f"[scraper] Cookies cargadas desde archivo local: {cookies_path} ({len(cookies_data)} cookies)")
        except Exception as e:
            print(f"[scraper] Error leyendo archivo de cookies: {e}")
            return False
    
    if not cookies_data:
        print(f"[scraper] No se pudieron cargar las cookies")
        return False
    
    # Navegar a la página principal antes de agregar cookies
    print(f"[scraper] Navegando a MercadoLibre...")
    driver.get('https://www.mercadolibre.com.uy')
    time.sleep(3)  # Esperar a que cargue completamente
    
    # Manejar popups iniciales ANTES de cargar cookies
    print(f"[scraper] Manejando popups iniciales...")
    manejar_popups_cookies(driver)
    
    # Filtrar cookies válidas (no expiradas)
    import time as time_module
    current_timestamp = time_module.time()
    cookies_validas = []
    
    for cookie in cookies_data:
        # Verificar si la cookie ha expirado
        if 'expirationDate' in cookie:
            if cookie['expirationDate'] < current_timestamp:
                continue  # Cookie expirada, saltar
        elif 'expiry' in cookie:
            if cookie['expiry'] < current_timestamp:
                continue  # Cookie expirada, saltar
        
        cookies_validas.append(cookie)
    
    print(f"[scraper] {len(cookies_validas)}/{len(cookies_data)} cookies válidas (no expiradas)")
    
    # Agregar cookies válidas
    cookies_agregadas = 0
    cookies_fallidas = 0
    
    for cookie in cookies_validas:
        try:
            # Preparar cookie para Selenium
            cookie_selenium = cookie.copy()
            
            # Manejar campo de expiración
            if 'expirationDate' in cookie_selenium:
                try:
                    cookie_selenium['expiry'] = int(cookie_selenium['expirationDate'])
                    del cookie_selenium['expirationDate']
                except:
                    cookie_selenium.pop('expirationDate', None)
            elif 'expiry' in cookie_selenium:
                try:
                    cookie_selenium['expiry'] = int(cookie_selenium['expiry'])
                except:
                    del cookie_selenium['expiry']
            
            # Eliminar campos incompatibles con Selenium
            for k in ['sameSite', 'storeId', 'id', 'priority']:
                cookie_selenium.pop(k, None)
            
            # Intentar agregar la cookie
            driver.add_cookie(cookie_selenium)
            cookies_agregadas += 1
            
        except Exception as e:
            cookies_fallidas += 1
            cookie_name = cookie.get('name', 'sin_nombre')
            if cookies_fallidas <= 3:  # Solo mostrar primeros 3 errores
                print(f"[scraper] Error agregando cookie '{cookie_name}': {e}")
    
    print(f"[scraper] Cookies agregadas: {cookies_agregadas}, fallidas: {cookies_fallidas}")
    
    # Recargar página para aplicar cookies
    print(f"[scraper] Recargando página para aplicar cookies...")
    driver.refresh()
    time.sleep(3)
    
    # Manejar popups después de recargar
    manejar_popups_cookies(driver)
    
    # Verificar si todavía necesita login
    necesita_login = verificar_necesita_login(driver)
    if necesita_login:
        print(f"[scraper] ⚠️ Las cookies no fueron suficientes, MercadoLibre sigue pidiendo login")
        return False
    else:
        print(f"[scraper] ✅ Cookies aplicadas correctamente, no se requiere login")
        return True


def scrape_mercadolibre(filters: Dict[str, Any], keywords: List[str], max_pages: int = 3, search_id: str = None) -> Dict[str, List[Dict[str, Any]]]:
    print(f"🚀 [ML SCRAPER] Iniciando búsqueda - {len(keywords)} keywords, {max_pages} páginas")
    
    # Función para verificar si la búsqueda debe detenerse
    def should_stop():
        if search_id:
            try:
                from core.views import is_search_stopped
                return is_search_stopped(search_id)
            except:
                return False
        return False

    # Importar aquí para evitar dependencias cruzadas
    from core.search_manager import procesar_keywords
    keywords_filtradas = procesar_keywords(' '.join(keywords))
    # Adaptar a lista de variantes de texto (strings)
    keywords_variantes = extraer_variantes_keywords(keywords_filtradas)
    base_url = build_mercadolibre_url(filters)
    print(f"[scraper] URL base de búsqueda: {base_url}")
    print(f"[scraper] Palabras clave filtradas: {keywords_filtradas}")


    # Usar la función centralizada para iniciar el driver
    driver = iniciar_driver()

    # Cargar cookies de sesión si existen
    cookies_loaded = cargar_cookies(driver, 'mercadolibre_cookies.json')
    
    if not cookies_loaded:
        print("[scraper] ⚠️ Continuando sin cookies válidas - podría haber limitaciones de acceso")
        # Tomar captura de debug para ver qué está pasando
        tomar_captura_debug(driver, "cookies_fallidas")

    links = []
    all_publications = []
    matched_publications_titles = [] # New: To store titles of matched publications
    matched_publications_links = [] # New: To store links of matched publications
    current_pub_index = 0  # Contador global para las publicaciones procesadas
    # Patrones prohibidos por robots.txt
    def url_prohibida(url):
        # Solo bloquear si el path después del dominio coincide exactamente con los patrones prohibidos
        prohibidos = [
            '/jms/',
            '/adn/api',
        ]
        # Extraer solo el path después del dominio
        try:
            path = '/' + '/'.join(url.split('/')[3:])
        except Exception:
            path = url
        # Permitir links de publicaciones normales (que suelen ser /MLU-...)
        if path.startswith('/MLU-'):
            return False
        # Bloquear solo si el path empieza por los patrones prohibidos
        for patron in prohibidos:
            if path.startswith(patron):
                return True
        return False

    for page in range(max_pages):
        # Verificar si debe detenerse antes de cada página
        if should_stop():
            print(f"[scraper] Búsqueda detenida por el usuario en página {page + 1}")
            send_progress_update(final_message="Búsqueda detenida por el usuario")
            break

        if page == 0:
            url = base_url
        else:
            desde = 1 + 48 * page
            # No duplicar _NoIndex_True si ya está en base_url
            if '_NoIndex_True' in base_url:
                url = f"{base_url}_Desde_{desde}"
            else:
                url = f"{base_url}_Desde_{desde}_NoIndex_True"
        print(f"[scraper] Selenium visitando: {url}")
        send_progress_update(current_search_item=f"Visitando página {page + 1}...")
        driver.get(url)
        time.sleep(3)
        
        # Verificar parada después de cargar la página
        if should_stop():
            print(f"[scraper] Búsqueda detenida por el usuario después de cargar página {page + 1}")
            send_progress_update(final_message="Búsqueda detenida por el usuario")
            break
            
        items = driver.find_elements(By.CSS_SELECTOR, 'div.poly-card--grid-card')
        # Consolidar logs de páginas
        print(f"📄 [PÁGINA {page+1}] {len(items)} publicaciones encontradas")
        send_progress_update(current_search_item=f"Página {page+1}: {len(items)} publicaciones encontradas", page_items_found=len(items))
        publicaciones = []
        for idx, item in enumerate(items, 1):
            # Verificar parada durante el procesamiento de cada item
            if should_stop():
                print(f"[scraper] Búsqueda detenida por el usuario en item {idx} de página {page + 1}")
                send_progress_update(final_message="Búsqueda detenida por el usuario")
                break
                
            try:
                link_tag = item.find_element(By.CSS_SELECTOR, 'h3.poly-component__title-wrapper > a.poly-component__title')
                link = link_tag.get_attribute('href')
                titulo = link_tag.text.strip()
                link_limpio = link.split('#')[0].split('?')[0]
                # Filtrar links prohibidos
                if not url_prohibida(link_limpio):
                    publicaciones.append({'idx': idx + page*48, 'titulo': titulo, 'url': link_limpio})
                else:
                    print(f"[scraper] Link prohibido por robots.txt: {link_limpio}")
            except Exception as e:
                print(f"[scraper] No se pudo obtener el link/título de la propiedad {idx}: {e}")
        
        all_publications.extend(publicaciones)

        total_publications_found = len(all_publications)
        estimated_time = total_publications_found * 20
        send_progress_update(total_found=total_publications_found, estimated_time=estimated_time)

        # Procesar cada publicación individualmente
        for pub in publicaciones:
            current_pub_index += 1
            
            # Enviar progreso con formato "x/y"
            send_progress_update(
                current_search_item=f"Búsqueda actual ({current_pub_index}/{total_publications_found}): {pub['titulo']}"
            )
            print(f"➡️  propiedad {pub['idx']}: {pub['titulo']} - {pub['url']}")
            cumple = False
            try:
                if url_prohibida(pub['url']):
                    print(f"[scraper] Saltando análisis de URL prohibida: {pub['url']}")
                    continue
                driver.get(pub['url'])
                time.sleep(2)
                # Título
                try:
                    titulo_text = driver.find_element(By.CSS_SELECTOR, 'h1').text.lower()
                except:
                    titulo_text = ''
                # Descripción
                try:
                    desc_tag = driver.find_element(By.CSS_SELECTOR, 'p.ui-pdp-description__content[data-testid="content"]')
                    descripcion = desc_tag.text.lower()
                except:
                    descripcion = ''
                # Características clave-valor
                caracteristicas_kv = []
                try:
                    claves = driver.find_elements(By.CSS_SELECTOR, 'div.andes-table__header__container')
                    valores = driver.find_elements(By.CSS_SELECTOR, 'span.andes-table__column--value')
                    for k, v in zip(claves, valores):
                        caracteristicas_kv.append(f"{k.text.strip().lower()}: {v.text.strip().lower()}")
                except:
                    pass
                # Características sueltas
                caracteristicas_sueltas = []
                try:
                    sueltas = driver.find_elements(By.CSS_SELECTOR, 'span.ui-pdp-color--BLACK.ui-pdp-size--XSMALL.ui-pdp-family--REGULAR')
                    for s in sueltas:
                        caracteristicas_sueltas.append(s.text.strip().lower())
                except:
                    pass
                caracteristicas = ' '.join(caracteristicas_kv + caracteristicas_sueltas)
                def normalizar(texto):
                    return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()
                texto_total_norm = normalizar(f"{titulo_text} {descripcion} {caracteristicas}")
                keywords_norm = [normalizar(kw) for kw in keywords_variantes]
                encontrados = [kw for kw in keywords_variantes if normalizar(kw) in texto_total_norm]
                no_encontrados = [kw for kw in keywords_variantes if normalizar(kw) not in texto_total_norm]
                if not keywords_norm:
                    print("⚠️  No se especificaron palabras clave para filtrar.\n")
                    cumple = True
                elif all(kw in texto_total_norm for kw in keywords_norm):
                    print(f"✅ Cumple todos los requisitos. Palabras encontradas: {encontrados}\n")
                    cumple = True
                else:
                    print(f"❌ No se encontraron todas las palabras clave. Encontradas: {encontrados} | Faltantes: {no_encontrados}\n")
            except Exception as e:
                print(f"[scraper] Error al analizar publicación {pub['url']}: {e}")
            if cumple:
                links.append({'url': pub['url'], 'titulo': pub['titulo']})
                matched_publications_titles.append({'title': pub['titulo'], 'url': pub['url']}) # New: Add matched title and URL
                send_progress_update(matched_publications=matched_publications_titles) # New: Send updated matched publications
        if len(items) < 48:
            print(f"Última página detectada (menos de 48 propiedades). Se detiene la búsqueda.")
            break
    driver.quit()
    print(f"[scraper] Resultados encontrados: {len(links)}")
    send_progress_update(final_message=f"¡Búsqueda finalizada! Se encontraron {len(links)} publicaciones coincidentes.")
    all_links_with_titles = [{'url': p['url'], 'titulo': p['titulo']} for p in all_publications]
    return {"matched": links, "all": all_links_with_titles}




def parse_rango(texto):
    texto = texto.lower()
    if 'monoambiente' in texto: return 0, 0
    numeros = [int(n) for n in re.findall(r'\d+', texto)]
    if len(numeros) == 1: return numeros[0], numeros[0]
    if len(numeros) >= 2: return min(numeros), max(numeros)
    return None, None

def scrape_detalle_con_requests(url, api_key=None, use_scrapingbee=False):
    """
    Scrapea detalles usando ScrapingBee o requests directo según la configuración.
    """
    try:
        if use_scrapingbee and api_key:
            # Usar ScrapingBee
            params = {'api_key': api_key, 'url': url}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=90)
        else:
            # Usar requests directo
            response = requests.get(url, headers=HEADERS, timeout=90)

        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        if not soup.find('div', class_='ui-pdp-container'):
            return None

        datos = {'url': url}

        # --- Extracción de Datos Principales (sin cambios) ---
        datos['titulo'] = (t.text.strip() if (t := soup.find('h1', class_='ui-pdp-title')) else "N/A")
        if pc := soup.find('div', class_='ui-pdp-price__main-container'):
            datos['precio_moneda'] = (m.text.strip() if (m := pc.find('span', 'andes-money-amount__currency-symbol')) else "")
            valor_str = (v.text.strip().replace('.', '') if (v := pc.find('span', 'andes-money-amount__fraction')) else "0")
            datos['precio_valor'] = int(re.sub(r'\D', '', valor_str))

        img_tag = (fig.find('img') if (fig := soup.find('figure', 'ui-pdp-gallery__figure')) else None)
        datos['url_imagen'] = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
        datos['descripcion'] = (d.text.strip() if (d := soup.find('p', 'ui-pdp-description__content')) else "")

        # --- LÓGICA DE EXTRACCIÓN DE CARACTERÍSTICAS CORREGIDA ---
        caracteristicas_dict = {}

        # 1. Extraer de las tablas "Principales", "Ambientes", etc.
        for row in soup.select('tr.andes-table__row'):
            if (th := row.find('th')) and (td := row.find('td')):
                key = th.text.strip().lower()
                value = td.text.strip()
                caracteristicas_dict[key] = value

        # 2. Extraer de la sección de íconos "highlighted"
        for spec in soup.select('div.ui-vpp-highlighted-specs__key-value'):
            if len(spans := spec.find_all('span')) == 2:
                key = spans[0].text.replace(':', '').strip().lower()
                value = spans[1].text.strip()
                caracteristicas_dict[key] = value

        datos['caracteristicas_texto'] = "\n".join([f"{k.capitalize()}: {v}" for k, v in caracteristicas_dict.items()])

        def get_int_from_value(value: str):
            try:
                m = re.search(r'\d+', value or '')
                return int(m.group()) if m else None
            except:
                return None

        # --- Mapeo a campos estructurados (usando el diccionario unificado) ---
        datos['tipo_inmueble'] = caracteristicas_dict.get('tipo de casa') or caracteristicas_dict.get('tipo de inmueble', 'N/A')
        datos['condicion'] = caracteristicas_dict.get('condición del ítem', '')

        datos['dormitorios_min'], datos['dormitorios_max'] = parse_rango(caracteristicas_dict.get('dormitorios', ''))
        datos['banos_min'], datos['banos_max'] = parse_rango(caracteristicas_dict.get('baños', ''))
        datos['superficie_total_min'], datos['superficie_total_max'] = parse_rango(caracteristicas_dict.get('superficie total', ''))
        datos['superficie_cubierta_min'], datos['superficie_cubierta_max'] = parse_rango(caracteristicas_dict.get('área privada', '') or caracteristicas_dict.get('superficie cubierta', ''))
        datos['cocheras_min'], datos['cocheras_max'] = parse_rango(caracteristicas_dict.get('cocheras', ''))

        antiguedad_str = caracteristicas_dict.get('antigüedad', '')
        datos['antiguedad'] = 0 if 'a estrenar' in antiguedad_str.lower() else get_int_from_value(antiguedad_str)

        # Mapeo de booleanos
        datos['es_amoblado'] = caracteristicas_dict.get('amoblado', 'no').lower() == 'sí'
        datos['admite_mascotas'] = caracteristicas_dict.get('admite mascotas', 'no').lower() == 'sí'
        datos['tiene_piscina'] = caracteristicas_dict.get('piscina', 'no').lower() == 'sí'
        datos['tiene_terraza'] = caracteristicas_dict.get('terraza', 'no').lower() == 'sí'
        datos['tiene_jardin'] = caracteristicas_dict.get('jardín', 'no').lower() == 'sí'

        return datos
    except Exception:
        return None


def recolectar_urls_de_pagina(url_target, api_key=None, ubicacion=None, use_scrapingbee=False):
    """
    Función de recolección que usa ScrapingBee o requests directo según la configuración.
    """
    print(f"  [Recolector] Iniciando recolección para: {url_target} (ScrapingBee: {'Sí' if use_scrapingbee else 'No'})")
    try:
        if use_scrapingbee and api_key:
            # Usar ScrapingBee
            params = {'api_key': api_key, 'url': url_target}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, headers=HEADERS, timeout=60)
        else:
            # Usar requests directo
            response = requests.get(url_target, headers=HEADERS, timeout=60)
        
        if response.status_code >= 400:
            print(f"  [Recolector] ERROR: Status {response.status_code} para {url_target}")
            return set(), 0

        soup = BeautifulSoup(response.text, 'lxml')
        items = soup.find_all('li', class_='ui-search-layout__item')
        if not items:
            print(f"  [Recolector] ADVERTENCIA: No se encontraron items en {url_target}")
            return set(), 0

        urls_de_pagina = {link['href'].split('#')[0] for item in items if (link := item.find('a', class_='poly-component__title') or item.find('a', class_='ui-search-link')) and link.has_attr('href')}
        print(f"  [Recolector] ÉXITO: Se encontraron {len(urls_de_pagina)} URLs en {url_target}")
        return urls_de_pagina, len(items)
    except Exception as e:
        print(f"  [Recolector] EXCEPCIÓN: Ocurrió un error procesando {url_target}: {e}")
        return set(), 0



def extraer_total_resultados_mercadolibre(url_base_con_filtros, api_key=None, use_scrapingbee=False):
    """
    Extrae el número total de resultados de MercadoLibre desde la primera página de resultados
    Primero intenta con requests, si falla usa Chrome como fallback
    """
    print(f"🔍 [TOTAL ML] Iniciando extracción para URL: {url_base_con_filtros}")
    
    # Remover logs excesivos de conectividad y tests
    try:
        print("🌐 [CONECTIVIDAD] Probando acceso básico a MercadoLibre...")
        test_response = requests.get("https://www.mercadolibre.com.uy/", headers=HEADERS, timeout=10)
        print(f"✅ [CONECTIVIDAD] MercadoLibre accesible - Status: {test_response.status_code}")
    except Exception as e:
        print(f"❌ [CONECTIVIDAD] No se puede acceder a MercadoLibre: {e}")
        return None
    
    # Primera tentativa: Usar requests/ScrapingBee (idéntico flujo que el recolector de URLs)
    try:
        print(f"🌐 [TOTAL ML] Intentando con {'ScrapingBee' if (use_scrapingbee and api_key) else 'requests'} primero...")
        
        if '_NoIndex_True' in url_base_con_filtros:
            url_primera_pagina = url_base_con_filtros
        else:
            url_primera_pagina = f"{url_base_con_filtros}_NoIndex_True"
        
        print(f"📡 [TOTAL ML] Solicitando: {url_primera_pagina}")

        # Reutilizar exactamente el mismo patrón que recolectar_urls_de_pagina
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url_primera_pagina}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, headers=HEADERS, timeout=60)
        else:
            response = requests.get(url_primera_pagina, headers=HEADERS, timeout=60)
        
        # Solo mostrar status si hay error
        if response.status_code != 200:
            print(f"❌ [REQUESTS] Status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text

            # Primero: intentar con selectores concretos como en Selenium
            soup = BeautifulSoup(html_content, 'lxml')
            # Conjunto de selectores amplio, similar al fallback Selenium
            selectores = [
                '.ui-search-search-result__quantity-results',
                '.ui-search-results__quantity-results',
                '.ui-search-breadcrumb__title',
                '.ui-search-results-header__title',
                "[class*='quantity-results']",
                "[class*='results-quantity']",
            ]
            total_text = None
            for selector in selectores:
                el = soup.select_one(selector)
                if el and el.get_text(strip=True):
                    total_text = el.get_text(strip=True)
                    break

            # Si no se encontró por selectores, intentar por regex global (fallback)
            import re
            if not total_text:
                # Buscar la forma "123 resultados" o similares
                m = re.search(r'(\d{1,3}(?:[.,]\d{3})+|\d+)\s*resultados?', soup.get_text(" ", strip=True), re.IGNORECASE)
                if m:
                    total_text = m.group(0)

            # Último intento: buscar valores típicos en JSON embebido
            if not total_text:
                patterns = [
                    r'"quantity"\s*:\s*(\d+)',
                    r'"total"\s*:\s*(\d+)',
                    r'"numberOfItems"\s*:\s*(\d+)',
                ]
                for pattern in patterns:
                    m = re.search(pattern, html_content, re.IGNORECASE)
                    if m:
                        total_text = m.group(1)
                        break

            if total_text:
                # Extraer dígitos y normalizar
                numeros = re.findall(r'[\d.,]+', total_text)
                if numeros:
                    total = int(numeros[0].replace('.', '').replace(',', ''))
                    print(f"✅ [TOTAL EXTRAÍDO] {total:,} publicaciones")
                    return total

            # Si aún no hay total, como mínimo contemos items de la primera página (no es el total)
            items = soup.find_all('li', class_='ui-search-layout__item')
            if items:
                print(f"⚠️ [TOTAL ML] No se halló total explícito; primera página tiene {len(items)} items")
                # No devolvemos esto como total para no confundir, pero lo registramos
            print("⚠️ [TOTAL ML] Requests/ScrapingBee obtuvo contenido pero no encontró el total")
        else:
            print(f"❌ [TOTAL ML] Requests falló con código: {response.status_code}")
            
    except Exception as e:
        print(f"❌ [TOTAL ML] Error con requests: {e}")
    
    # Fallback: Usar Chrome si requests falla
    print("🔄 [TOTAL ML] Fallback a Chrome...")
    
    driver = None
    try:
        print("🔍 [TOTAL ML] Iniciando driver...")
        driver = iniciar_driver()
        print("✅ [TOTAL ML] Driver iniciado correctamente")
        
        # No duplicar _NoIndex_True si ya está en la URL base
        if '_NoIndex_True' in url_base_con_filtros:
            url_primera_pagina = url_base_con_filtros
        else:
            url_primera_pagina = f"{url_base_con_filtros}_NoIndex_True"
        print(f"🔍 [TOTAL ML] Accediendo a: {url_primera_pagina}")
        
        driver.get(url_primera_pagina)
        print("✅ [TOTAL ML] Página cargada, esperando contenido...")
        
        # Simular comportamiento humano más realista
        time.sleep(2)
        
        # Scroll para simular usuario real
        try:
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
        except:
            pass
        
        # Verificar que la página se cargó correctamente
        page_title = driver.title
        current_url = driver.current_url
        page_source_length = len(driver.page_source)
        print(f"📄 [TOTAL ML] Título: {page_title}")
        print(f"🔗 [TOTAL ML] URL: {current_url}")
        print(f"📏 [TOTAL ML] HTML Length: {page_source_length}")
        
        # Solo mostrar preview si hay error para reducir spam
        if "mercadolibre" not in page_title.lower() and "mercadolibre" not in current_url.lower():
            page_preview = driver.page_source[:1000]
            print(f"📄 [DEBUG] HTML Preview: {page_preview}")
            print("❌ [TOTAL ML] La página no parece ser de MercadoLibre")
            return None
        
        # Buscar el elemento que contiene el total de resultados
        try:
            # Múltiples selectores para diferentes versiones de MercadoLibre
            selectores = [
                ".ui-search-search-result__quantity-results",
                ".ui-search-results__quantity-results", 
                ".ui-search-breadcrumb__title",
                ".ui-search-results-header__title",
                "[class*='quantity-results']",
                "[class*='results-quantity']"
            ]
            
            print(f"🔍 [TOTAL ML] Probando {len(selectores)} selectores...")
            
            # Primero verificar si es una página de captcha o error
            page_title = driver.title.lower()
            page_source_sample = driver.page_source[:2000].lower()
            
            captcha_indicators = [
                "captcha", "robot", "verificaci", "blocked", "security",
                "too many requests", "rate limit", "forbidden"
            ]
            
            found_captcha_indicators = [ind for ind in captcha_indicators if ind in page_source_sample or ind in page_title]
            if found_captcha_indicators:
                print(f"🛑 [CAPTCHA DETECTED] Indicadores encontrados: {found_captcha_indicators}")
                screenshot_path = tomar_captura_debug(driver, f"captcha_detected_{'-'.join(found_captcha_indicators[:2])}")
                send_progress_update(
                    current_search_item=f"🛑 CAPTCHA/Bloqueo detectado: {found_captcha_indicators}. Ver captura.",
                    debug_screenshot=screenshot_path
                )
                return None
            total_element = None
            for i, selector in enumerate(selectores, 1):
                try:
                    print(f"🔍 [TOTAL ML] Probando selector {i}/{len(selectores)}: {selector}")
                    total_element = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ [TOTAL ML] Elemento encontrado con selector '{selector}'")
                    if total_element:
                        break
                except Exception as e:
                    print(f"❌ [TOTAL ML] Selector {selector} falló: {e}")
                    continue
            
            if total_element:
                total_text = total_element.text
                print(f"📊 [TOTAL ML] Texto encontrado: '{total_text}'")
                
                # Extraer número del texto (ej: "212.158 resultados" -> 212158)
                import re
                numeros = re.findall(r'[\d.,]+', total_text)
                if numeros:
                    # Quitar puntos y comas de los números y convertir
                    total_str = numeros[0].replace('.', '').replace(',', '')
                    total = int(total_str)
                    print(f"✅ [TOTAL ML] Total extraído exitosamente: {total:,}")
                    return total
                else:
                    print(f"❌ [TOTAL ML] No se encontraron números en el texto: '{total_text}'")
                    # Tomar captura para debugging
                    screenshot_path = tomar_captura_debug(driver, "no_numeros_en_texto")
                    send_progress_update(
                        current_search_item="❌ No se encontraron números en el total. Ver captura debug.",
                        debug_screenshot=screenshot_path
                    )
                    return None
            else:
                print("❌ [TOTAL ML] No se encontró elemento con total de resultados")
                
                # DEBUGGING MEJORADO: Capturar más información
                try:
                    print("🔍 [DEBUG] Analizando qué hay en la página...")
                    
                    # Verificar si hay elementos de búsqueda
                    search_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='search'], [class*='result']")
                    print(f"🔍 [DEBUG] Elementos con 'search' o 'result': {len(search_elements)}")
                    
                    # Verificar si hay números en el HTML
                    page_text = driver.find_element(By.TAG_NAME, "body").text[:500]
                    import re
                    numbers = re.findall(r'\d{1,3}[.,]?\d{3}', page_text)
                    print(f"🔍 [DEBUG] Números encontrados en página: {numbers[:5]}")
                    
                    # Verificar si es página de error o captcha
                    error_indicators = [
                        "captcha", "robot", "blocked", "error", "forbidden", 
                        "not found", "maintenance", "temporarily unavailable"
                    ]
                    page_text_lower = page_text.lower()
                    found_indicators = [ind for ind in error_indicators if ind in page_text_lower]
                    if found_indicators:
                        print(f"⚠️ [DEBUG] Indicadores de error/captcha: {found_indicators}")
                    
                except Exception as debug_e:
                    print(f"❌ [DEBUG] Error en análisis debug: {debug_e}")
                
                # Tomar captura para debugging
                screenshot_path = tomar_captura_debug(driver, "elemento_total_no_encontrado")
                send_progress_update(
                    current_search_item="❌ No se encontró elemento de total. Ver captura debug.",
                    debug_screenshot=screenshot_path
                )
                # Intentar encontrar cualquier elemento que contenga "resultado"
                try:
                    all_text = driver.find_element(By.TAG_NAME, "body").text
                    if "resultado" in all_text.lower():
                        print("📄 [TOTAL ML] La página contiene 'resultado', pero no se encontró el selector específico")
                        # Buscar manualmente en el texto
                        import re
                        matches = re.findall(r'(\d+(?:[.,]\d+)*)\s*resultados?', all_text, re.IGNORECASE)
                        if matches:
                            total_str = matches[0].replace('.', '').replace(',', '')
                            total = int(total_str)
                            print(f"✅ [TOTAL ML] Total extraído mediante búsqueda de texto: {total:,}")
                            return total
                        else:
                            # Tomar captura - tiene la palabra "resultado" pero no encuentra el número
                            screenshot_path = tomar_captura_debug(driver, "tiene_resultado_sin_numero")
                            send_progress_update(
                                current_search_item="❌ Página tiene 'resultado' pero sin número. Ver captura debug.",
                                debug_screenshot=screenshot_path
                            )
                    else:
                        print("📄 [TOTAL ML] La página no contiene 'resultado' - puede ser una página de error")
                        # Tomar captura - página sin "resultado"
                        screenshot_path = tomar_captura_debug(driver, "pagina_sin_resultado")
                        send_progress_update(
                            current_search_item="❌ Página sin 'resultado' - posible error. Ver captura debug.",
                            debug_screenshot=screenshot_path
                        )
                except Exception as e:
                    print(f"❌ [TOTAL ML] Error al analizar contenido de página: {e}")
                    # Tomar captura - error al analizar
                    screenshot_path = tomar_captura_debug(driver, "error_analizar_pagina")
                    send_progress_update(
                        current_search_item=f"❌ Error analizando página: {e}. Ver captura debug.",
                        debug_screenshot=screenshot_path
                    )
                
                return None
                
        except Exception as e:
            print(f"🛑 [TOTAL ML] Error al extraer total de resultados: {e}")
            print(f"🛑 [TOTAL ML] Tipo de error: {type(e).__name__}")
            import traceback
            print(f"🛑 [TOTAL ML] Traceback: {traceback.format_exc()}")
            return None
            
    except Exception as e:
        print(f"🛑 [TOTAL ML] Error general en extracción: {e}")
        print(f"🛑 [TOTAL ML] Tipo de error: {type(e).__name__}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
                print("✅ [TOTAL ML] Driver cerrado correctamente")
            except:
                print("⚠️ [TOTAL ML] Error al cerrar driver")
        else:
            print("⚠️ [TOTAL ML] Driver era None, no se pudo cerrar")

def run_scraper(filters: dict, keywords: list = None, max_paginas: int = 3, workers_fase1: int = 1, workers_fase2: int = 1):
    """
    Ejecuta el scraper con todos los filtros posibles usando build_mercadolibre_url
    """
    # Consolidar logs iniciales
    print(f"🚀 [SCRAPER] Iniciando búsqueda - Filtros: {len(filters)} | Keywords: {len(keywords) if keywords else 0}")
    
    # Inicializar lista de publicaciones coincidentes al inicio
    matched_publications_titles = []
    
    # Procesar keywords usando la función centralizada
    from core.search_manager import procesar_keywords
    keywords_filtradas = procesar_keywords(' '.join(keywords)) if keywords else []
    keywords_variantes = extraer_variantes_keywords(keywords_filtradas)
    print(f"🔍 [SCRAPER] Keywords filtradas: {keywords_filtradas}")

    USE_THREADS = False  # Cambia a True para habilitar hilos y ScrapingBee
    
    # Solo verificar API key si se van a usar hilos (ScrapingBee)
    API_KEY = None
    if USE_THREADS:
        API_KEY = os.getenv('SCRAPINGBEE_API_KEY')
        if not API_KEY: 
            print("❌ ERROR: SCRAPINGBEE_API_KEY no definida pero USE_THREADS=True.")
            send_progress_update(final_message="❌ Error: API key no configurada")
            return
        print("🔧 [CONFIG] Modo concurrente activado - usando ScrapingBee")
    else:
        print("🔧 [CONFIG] Modo secuencial activado - usando requests directo")
    
    propiedades_omitidas = 0
    nuevas_propiedades_guardadas = 0
    urls_a_visitar_final = set()
    
    # --- CONSTRUCCIÓN DE URL COMPLETA CON TODOS LOS FILTROS ---
    # Consolidar logs de construcción de URL
    try:
        url_base_con_filtros = build_mercadolibre_url(filters)
        print(f"🔗 [URL GENERADA] {url_base_con_filtros}")
        
        # Validar que la URL no sea la genérica (indica error en construcción)
        if url_base_con_filtros.endswith('_NoIndex_True') and 'inmuebles/_NoIndex_True' in url_base_con_filtros:
            print("⚠️ [URL BUILD] URL generada es demasiado genérica, puede indicar problema en filtros")
        
        send_progress_update(current_search_item=f"🏠 URL generada con filtros: {url_base_con_filtros[:100]}{'...' if len(url_base_con_filtros) > 100 else ''}")
    except Exception as e:
        print(f"❌ [URL BUILD] Error construyendo URL: {e}")
        print(f"❌ [URL BUILD] Tipo de error: {type(e).__name__}")
        import traceback
        print(f"❌ [URL BUILD] Traceback: {traceback.format_exc()}")
        send_progress_update(final_message=f"❌ Error construyendo URL: {e}")
        return
    
    # --- EXTRACCIÓN DEL TOTAL DE RESULTADOS ---
    print("\n[Principal] Extrayendo total de resultados desde MercadoLibre...")
    send_progress_update(current_search_item="🔍 Extrayendo total de resultados de MercadoLibre...")
    total_ml = extraer_total_resultados_mercadolibre(
        url_base_con_filtros,
        api_key=API_KEY,
        use_scrapingbee=USE_THREADS and bool(API_KEY)
    )
    if total_ml:
        print(f"[Principal] Total de publicaciones en MercadoLibre: {total_ml:,}")
        send_progress_update(total_found=total_ml, current_search_item=f"📊 Total de publicaciones encontradas: {total_ml:,}")
    else:
        print("[Principal] No se pudo extraer el total de MercadoLibre")
        send_progress_update(current_search_item="❌ No se pudo obtener el total de resultados")
    
    # --- FASE 1: RECOLECCIÓN ---
    # Calcular cantidad de páginas según total_ml y 48 por página
    if total_ml:
        paginas_a_buscar = min(max_paginas, (total_ml // 48) + (1 if total_ml % 48 else 0))
    else:
        paginas_a_buscar = max_paginas
    # Construir URLs de páginas sin duplicar '_NoIndex_True'
    paginas_de_resultados = []
    for i in range(paginas_a_buscar):
        if i == 0:
            page_url = url_base_con_filtros
        else:
            desde = 1 + (i * 48)
            page_url = f"{url_base_con_filtros}_Desde_{desde}"
        paginas_de_resultados.append(page_url)

    modo = 'concurrencia (ScrapingBee)' if USE_THREADS else 'secuencial (requests)'
    print(f"\n--- FASE 1: Se intentarán recolectar {len(paginas_de_resultados)} páginas (modo: {modo}, workers: {workers_fase1 if USE_THREADS else 1}) ---")
    send_progress_update(current_search_item=f"FASE 1: Recolectando URLs de {len(paginas_de_resultados)} páginas ({modo})...")
    urls_recolectadas_bruto = set()
    ubicacion_param = filters.get('ciudad', filters.get('departamento', 'montevideo'))
    if USE_THREADS:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase1) as executor:
            mapa_futuros = {executor.submit(recolectar_urls_de_pagina, url, API_KEY, ubicacion_param, True): url for url in paginas_de_resultados}
            for futuro in concurrent.futures.as_completed(mapa_futuros):
                urls_nuevas, _ = futuro.result()
                urls_recolectadas_bruto.update(urls_nuevas)
    else:
        for url in paginas_de_resultados:
            urls_nuevas, _ = recolectar_urls_de_pagina(url, API_KEY, ubicacion_param, False)
            urls_recolectadas_bruto.update(urls_nuevas)

    print(f"\n[Principal] FASE 1 Recolección Bruta Finalizada. Se obtuvieron {len(urls_recolectadas_bruto)} URLs en total.")
    send_progress_update(current_search_item=f"FASE 1 completada. Se encontraron {len(urls_recolectadas_bruto)} URLs de publicaciones.")

    # --- LÓGICA DE DEDUPLICACIÓN (con logs) ---
    print("\n[Principal] Iniciando chequeo de duplicados contra la base de datos...")
    send_progress_update(current_search_item="Chequeando publicaciones existentes en la base de datos...")
    existing_publications_titles = []  # Lista para propiedades existentes que coinciden

    if urls_recolectadas_bruto:
        # Consultamos a la BD una sola vez por todas las URLs encontradas
        urls_existentes = set(Propiedad.objects.filter(url__in=list(urls_recolectadas_bruto)).values_list('url', flat=True))
        propiedades_omitidas = len(urls_existentes)
        urls_a_visitar_final = urls_recolectadas_bruto - urls_existentes

        # Obtener propiedades existentes y verificar si coinciden con keywords
        if urls_existentes and keywords_variantes:
            existing_properties = Propiedad.objects.filter(url__in=urls_existentes)

            import unicodedata
            def normalizar(texto):
                return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()

            keywords_norm = [normalizar(kw) for kw in keywords_variantes]

            for prop in existing_properties:
                titulo_propiedad = prop.titulo or ''
                descripcion = prop.descripcion or ''
                # caracteristicas_texto ya no es campo del modelo; intentar desde metadata
                meta = prop.metadata or {}
                caracteristicas = meta.get('caracteristicas', '') or meta.get('caracteristicas_texto', '') or ''
                texto_total = f"{titulo_propiedad.lower()} {descripcion.lower()} {caracteristicas.lower()}"
                texto_total_norm = normalizar(texto_total)

                # Usar la misma lógica flexible para propiedades existentes
                keywords_encontradas = 0
                for kw in keywords_norm:
                    encontrada = False

                    # 1. Coincidencia exacta
                    if kw in texto_total_norm:
                        encontrada = True

                    # 2. Coincidencia con stemming básico
                    elif not encontrada:
                        kw_stem = stemming_basico(kw)
                        if kw_stem in texto_total_norm:
                            encontrada = True

                    # 3. Buscar raíz de la keyword en el texto
                    elif not encontrada and len(kw) > 4:
                        raiz = kw[:len(kw)-2]
                        if raiz in texto_total_norm:
                            encontrada = True

                    if encontrada:
                        keywords_encontradas += 1

                # Aplicar el mismo criterio del 70%
                porcentaje_requerido = 0.7
                if keywords_encontradas >= len(keywords_norm) * porcentaje_requerido:
                    existing_publications_titles.append({
                        'title': titulo_propiedad,
                        'url': prop.url
                    })
        elif urls_existentes and not keywords_variantes:
            # Si no hay keywords, todas las existentes coinciden
            existing_properties = Propiedad.objects.filter(url__in=urls_existentes)
            for prop in existing_properties:
                existing_publications_titles.append({
                    'title': prop.titulo or 'Sin título',
                    'url': prop.url
                })

        print(f"🗃️  [DEDUP] Existentes: {propiedades_omitidas} | Nuevas: {len(urls_a_visitar_final)}")
        print(f"🗃️  [DEDUP] Coincidentes existentes: {len(existing_publications_titles)}")
        send_progress_update(current_search_item=f"Existentes: {propiedades_omitidas} | Nuevas: {len(urls_a_visitar_final)}")
    else:
        print("❌ [RECOLECCIÓN] No se obtuvieron URLs")
        send_progress_update(current_search_item="No se encontraron URLs para procesar.")

    if urls_a_visitar_final:
        print(f"\n--- FASE 2: Scrapeo de detalles en paralelo (hasta {workers_fase2} hilos)... ---")
        send_progress_update(current_search_item=f"FASE 2: Scrapeando detalles de {len(urls_a_visitar_final)} publicaciones...")
        # ... (inicio FASE 2)
        urls_lista = list(urls_a_visitar_final)
        # matched_publications_titles ya está definida al inicio de la función
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase2) as executor:
            mapa_futuros = {executor.submit(scrape_detalle_con_requests, url, API_KEY, USE_THREADS): url for url in urls_lista}
            for i, futuro in enumerate(concurrent.futures.as_completed(mapa_futuros)):
                url_original = mapa_futuros[futuro]
                print(f"Procesando resultado {i+1}/{len(urls_lista)}: {url_original}")

                try:
                    if datos_propiedad := futuro.result():
                        # Extraer título para mostrar en progreso
                        titulo_propiedad = datos_propiedad.get('titulo', 'Sin título')
                        descripcion = datos_propiedad.get('descripcion', '').lower()
                        caracteristicas = datos_propiedad.get('caracteristicas_texto', '').lower()
                        texto_total = f"{titulo_propiedad.lower()} {descripcion} {caracteristicas}"

                        cumple = True
                        if keywords_variantes:
                            # Normaliza y verifica keywords con lógica más flexible
                            import unicodedata
                            def normalizar(texto):
                                return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()
                            
                            keywords_norm = [normalizar(kw) for kw in keywords_variantes]
                            texto_total_norm = normalizar(texto_total)
                            
                            # Verificar cada keyword con múltiples estrategias
                            keywords_encontradas = 0
                            for kw in keywords_norm:
                                encontrada = False
                                
                                # 1. Coincidencia exacta
                                if kw in texto_total_norm:
                                    encontrada = True
                                
                                # 2. Coincidencia con stemming básico
                                elif not encontrada:
                                    kw_stem = stemming_basico(kw)
                                    if kw_stem in texto_total_norm:
                                        encontrada = True
                                
                                # 3. Buscar raíz de la keyword en el texto
                                elif not encontrada and len(kw) > 4:
                                    raiz = kw[:len(kw)-2]  # Tomar los primeros n-2 caracteres
                                    if raiz in texto_total_norm:
                                        encontrada = True
                                
                                if encontrada:
                                    keywords_encontradas += 1
                            
                            # Ser más permisivo: requerir al menos 70% de las keywords
                            porcentaje_requerido = 0.7
                            cumple = keywords_encontradas >= len(keywords_norm) * porcentaje_requerido
                            
                            if cumple:
                                print(f"({i+1}/{len(urls_a_visitar_final)}) ✅ Coincide: {titulo_propiedad} ({keywords_encontradas}/{len(keywords_norm)} keywords)")
                                send_progress_update(current_search_item=f"({i+1}/{len(mapa_futuros)}) ✅ Coincide: {titulo_propiedad}")
                            else:
                                print(f"({i+1}/{len(urls_a_visitar_final)}) ❌ No coincide: {titulo_propiedad} ({keywords_encontradas}/{len(keywords_norm)} keywords)")
                                send_progress_update(current_search_item=f"({i+1}/{len(mapa_futuros)}) ❌ No coincide: {titulo_propiedad}")
                        else:
                            # Mostrar progreso con formato "Búsqueda actual (a/total_ml): Título" 
                            if total_ml:
                                send_progress_update(current_search_item=f"Búsqueda actual ({i+1}/{total_ml:,}): {titulo_propiedad}")
                            else:
                                send_progress_update(current_search_item=f"Procesando publicación {i+1}/{len(urls_lista)}: {titulo_propiedad}")

                        if cumple:
                            print(f"✅ [GUARDADO] {titulo_propiedad[:60]}...")
                            try:
                                # --- MEJORAR CON DATOS DE LOS FILTROS ---
                                # Pre-rellenamos con los datos que ya conocemos de los filtros
                                datos_propiedad['operacion'] = filters.get('operacion', 'venta')
                                datos_propiedad['departamento'] = filters.get('departamento', filters.get('ciudad', 'N/A'))
                                
                                # Si el scraper no encontró un tipo de inmueble válido, usamos el de los filtros
                                if not datos_propiedad.get('tipo_inmueble') or datos_propiedad.get('tipo_inmueble') == 'N/A':
                                   datos_propiedad['tipo_inmueble'] = filters.get('tipo', 'apartamento')
                                
                                # Verificar campos críticos antes del guardado
                                if not datos_propiedad.get('titulo'):
                                    print(f"⚠️ [GUARDADO] Advertencia: título vacío para {url_original}")
                                    datos_propiedad['titulo'] = f"Propiedad en {datos_propiedad.get('departamento', 'N/A')}"
                                
                                # Debug: mostrar datos antes del guardado
                                print(f"📝 [DEBUG] Guardando: {datos_propiedad.get('titulo')} - {datos_propiedad.get('precio_valor')} {datos_propiedad.get('precio_moneda', '')}")
                                
                                # Mapear campos del scraper a campos del modelo PostgreSQL
                                def mapear_datos_propiedad(datos):
                                    # Obtener plataforma MercadoLibre
                                    try:
                                        plataforma_ml = Plataforma.objects.get(nombre='MercadoLibre')
                                    except Plataforma.DoesNotExist:
                                        plataforma_ml = Plataforma.objects.create(
                                            nombre='MercadoLibre',
                                            url='https://www.mercadolibre.com.uy'
                                        )
                                    
                                    # Mapear campos válidos del modelo
                                    datos_mapeados = {
                                        'url': datos.get('url'),
                                        'titulo': datos.get('titulo'),
                                        'descripcion': datos.get('descripcion', ''),
                                        'plataforma': plataforma_ml,
                                        'metadata': {
                                            'precio_valor': datos.get('precio_valor'),
                                            'precio_moneda': datos.get('precio_moneda'),
                                            'operacion': datos.get('operacion'),
                                            'tipo_inmueble': datos.get('tipo_inmueble'),
                                            'departamento': datos.get('departamento'),
                                            'caracteristicas': datos.get('caracteristicas_texto', ''),
                                            'dormitorios': datos.get('dormitorios'),
                                            'banos': datos.get('banos'),
                                            'superficie': datos.get('superficie_total'),
                                            'direccion': datos.get('direccion')
                                        }
                                    }
                                    
                                    # Limpiar campos None del metadata
                                    datos_mapeados['metadata'] = {k: v for k, v in datos_mapeados['metadata'].items() if v is not None}
                                    
                                    return datos_mapeados
                                
                                # Mapear los datos antes de crear la propiedad
                                datos_mapeados = mapear_datos_propiedad(datos_propiedad)
                                
                                # Crear la propiedad en la base de datos
                                propiedad_creada = Propiedad.objects.create(**datos_mapeados)
                                nuevas_propiedades_guardadas += 1
                                matched_publications_titles.append({
                                    'title': propiedad_creada.titulo, 
                                    'url': propiedad_creada.url
                                })
                                
                                print(f"✅ [GUARDADO] Éxito - ID: {propiedad_creada.id}")
                                
                                # Enviar actualización con las publicaciones coincidentes actuales
                                send_progress_update(matched_publications=matched_publications_titles)
                                
                            except Exception as save_error:
                                print(f"❌ [GUARDADO] Error guardando propiedad: {save_error}")
                                print(f"❌ [GUARDADO] Datos originales: {datos_propiedad}")
                                print(f"❌ [GUARDADO] Datos mapeados: {datos_mapeados}")
                                import traceback
                                print(f"❌ [GUARDADO] Traceback: {traceback.format_exc()}")
                    else:
                        # Cuando no se pueden extraer datos, aún mostrar progreso
                        print(f"⚠️ [SCRAPING] No se pudieron extraer datos de: {url_original}")
                        if total_ml:
                            send_progress_update(current_search_item=f"Búsqueda actual ({i+1}/{total_ml:,}): Error al procesar")
                        else:
                            send_progress_update(current_search_item=f"Procesando publicación {i+1}/{len(urls_lista)}: Error al procesar")
                except Exception as exc:
                    print(f'❌ [SCRAPER] URL {url_original[:100]}... generó excepción: {exc}')
                    print(f'❌ [SCRAPER] Tipo de excepción: {type(exc).__name__}')
                    import traceback
                    print(f'❌ [SCRAPER] Traceback: {traceback.format_exc()[:500]}...')

    # Consolidar resumen final
    print(f"✅ [COMPLETADO] {nuevas_propiedades_guardadas} nuevas propiedades guardadas")
    
    # Enviar todas las propiedades coincidentes (nuevas y existentes) al frontend
    all_matched_properties = {
        'nuevas': matched_publications_titles,
        'existentes': existing_publications_titles
    }
    
    total_coincidentes = len(matched_publications_titles) + len(existing_publications_titles)
    print(f"📊 [RESUMEN FINAL] Nuevas: {len(matched_publications_titles)} | Existentes: {len(existing_publications_titles)} | Total: {total_coincidentes}")
    
    send_progress_update(
        final_message=f"✅ Búsqueda completada. {nuevas_propiedades_guardadas} nuevas propiedades guardadas.",
        matched_publications=matched_publications_titles,
        all_matched_properties=all_matched_properties
    )