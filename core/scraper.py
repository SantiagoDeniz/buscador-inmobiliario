# --- Función iniciar_driver restaurada para uso externo ---
def iniciar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    stealth(driver, languages=["es-ES", "es"], vendor="Google Inc.", platform="Win32",
        webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return driver

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
from core.models import Propiedad
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_progress_update(total_found=None, estimated_time=None, current_search_item=None, matched_publications=None, final_message=None, page_items_found=None):
    # Log en servidor con formato más legible
    if current_search_item:
        print(f'🔄 [PROGRESO] {current_search_item}')
    if total_found:
        print(f'📊 [PROGRESO] Total encontrado: {total_found:,} publicaciones')
    if final_message:
        print(f'✅ [PROGRESO] FINAL: {final_message}')
    
    channel_layer = get_channel_layer()
    if channel_layer is None:
        print("Warning: Channel layer is not available. Skipping real-time update.")
        return
    async_to_sync(channel_layer.group_send)(
        "search_progress",
        {
            "type": "send_progress",
            "message": {
                "total_found": total_found,
                "estimated_time": estimated_time,
                "current_search_item": current_search_item,
                "matched_publications": matched_publications,
                "final_message": final_message,
                "page_items_found": page_items_found, # Nuevo parámetro
            }
        }
    )

try:
    from selenium_stealth import stealth
except ImportError:
    # Si selenium-stealth no está instalado, define un stub
    def stealth(*args, **kwargs):
        pass
# HEADERS para requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

def normalizar_para_url(texto: str) -> str:
    if not texto: return ''
    # Quita tildes y caracteres especiales
    nfkd_form = unicodedata.normalize('NFKD', texto)
    texto_sin_tildes = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Reemplaza espacios y otros separadores por guiones y convierte a minúsculas
    return re.sub(r'[\s_]+', '-', texto_sin_tildes).lower()

def build_mercadolibre_url(filters: Dict[str, Any]) -> str:
    base = 'https://listado.mercadolibre.com.uy/inmuebles/'
    path_parts = []
    filter_segments = []

    # --- 1. Segmentos de Path --- 
    if tipo := filters.get('tipo'):
        # Salvedad: si el tipo es 'apartamento', usar 'apartamentos/', lo mismo con 'casa'
        if tipo.strip().lower() == 'apartamento':
            path_parts.append('apartamentos')
        elif tipo.strip().lower() == 'casa':
            path_parts.append('casas')
        else:
            path_parts.append(normalizar_para_url(tipo))

    if operacion := filters.get('operacion'):
        path_parts.append(normalizar_para_url(operacion))

    # Lógica para dormitorios como parte del path
    dormitorios_min = filters.get('dormitorios_min')
    dormitorios_max = filters.get('dormitorios_max')
    if dormitorios_min and dormitorios_max:
        if str(dormitorios_min) == str(dormitorios_max):
            path_parts.append(f'{dormitorios_min}-dormitorios')
        else:
            path_parts.append(f'{dormitorios_min}-a-{dormitorios_max}-dormitorios')
    elif dormitorios_min:
        path_parts.append(f'{dormitorios_min}-o-mas-dormitorios')
    elif dormitorios_max:
        # MercadoLibre no parece tener un formato claro para "hasta X dormitorios" en el path
        # Se omite del path y se podría manejar como filtro si se descubre el formato
        pass

    if departamento := filters.get('departamento'):
        path_parts.append(normalizar_para_url(departamento))
    
    if filters.get('departamento') == 'Montevideo' and (ciudad := filters.get('ciudad')):
        path_parts.append(normalizar_para_url(ciudad))

    # --- 2. Segmentos de Filtro (estilo _Clave_Valor) ---
    def add_range_filter(param_name, min_key, max_key, unit=''):
        min_val = filters.get(min_key, '')
        max_val = filters.get(max_key, '')
        # Si ambos son 0, agregar el filtro explícitamente
        if str(min_val) == '0' and str(max_val) == '0':
            filter_segments.append(f'_{param_name}_0{unit}-0{unit}')
            return
        # Agregar el filtro si alguno de los dos está presente (no solo si ambos)
        if min_val != '' or max_val != '':
            min_str = str(min_val) if min_val != '' else '0'
            max_str = str(max_val) if max_val != '' else '0'
            # Solo números, sin texto extra
            filter_segments.append(f'_{param_name}_{min_str}{unit}-{max_str}{unit}')

    moneda = filters.get('moneda', 'USD').upper()
    add_range_filter('PriceRange', 'precio_min', 'precio_max', unit=moneda)
    add_range_filter('FULL*BATHROOMS', 'banos_min', 'banos_max')

    if filters.get('amoblado'):
        filter_segments.append('_FURNISHED_242085')
    if filters.get('terraza'):
        filter_segments.append('_HAS*TERRACE_242085')
    if filters.get('aire_acondicionado'):
        filter_segments.append('_HAS*AIR*CONDITIONING_242085')
    if filters.get('piscina'):
        filter_segments.append('_HAS*SWIMMING*POOL_242085')
    if filters.get('jardin'):
        filter_segments.append('_HAS*GARDEN_242085')
    if filters.get('ascensor'):
        filter_segments.append('_HAS*LIFT_242085')

    # Añadir _NoIndex_True una sola vez después de filtros booleanos
    filter_segments.append('_NoIndex_True')

    add_range_filter('PARKING*LOTS', 'cocheras_min', 'cocheras_max')
    add_range_filter('PROPERTY*AGE', 'antiguedad_min', 'antiguedad_max')
    add_range_filter('TOTAL*AREA', 'superficie_total_min', 'superficie_total_max')
    add_range_filter('COVERED*AREA', 'superficie_cubierta_min', 'superficie_cubierta_max')

    if condicion := filters.get('condicion'):
        if condicion == 'Nuevo':
            filter_segments.append('_ITEM*CONDITION_2230284')
        elif condicion == 'Usado':
            filter_segments.append('_ITEM*CONDITION_2230581')

    # --- 3. Ensamblaje Final --- 
    path_str = '/'.join(filter(None, path_parts))
    # Asegurarse de que siempre haya un / al final del path si hay partes
    if path_str:
        path_str += '/'

    filter_str = ''.join(filter_segments)

    return base + path_str + filter_str


def scrape_mercadolibre(filters: Dict[str, Any], keywords: List[str], max_pages: int = 3, search_id: str = None) -> Dict[str, List[Dict[str, Any]]]:
    print(f"[DEPURACIÓN] Iniciando scraping MercadoLibre con filtros: {filters} y keywords: {keywords}")
    
    # Función para verificar si la búsqueda debe detenerse
    def should_stop():
        if search_id:
            try:
                from core.views import is_search_stopped
                return is_search_stopped(search_id)
            except:
                return False
        return False
    def cargar_cookies(driver, cookies_path):
        if not os.path.exists(cookies_path):
            print(f"[scraper] Archivo de cookies no encontrado: {cookies_path}")
            return
        with open(cookies_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        driver.get('https://www.mercadolibre.com.uy')
        for cookie in cookies:
            # Selenium espera 'expiry' como int, no float
            if 'expiry' in cookie:
                try:
                    cookie['expiry'] = int(cookie['expiry'])
                except:
                    del cookie['expiry']
            # Elimina campos incompatibles
            for k in ['sameSite', 'storeId']:
                cookie.pop(k, None)
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"[scraper] Error al agregar cookie: {e}")

    # Importar aquí para evitar dependencias cruzadas
    from core.search_manager import procesar_keywords
    keywords_filtradas = procesar_keywords(' '.join(keywords))
    base_url = build_mercadolibre_url(filters)
    print(f"[scraper] URL base de búsqueda: {base_url}")
    print(f"[scraper] Palabras clave filtradas: {keywords_filtradas}")


    # Usar la función centralizada para iniciar el driver
    driver = iniciar_driver()

    # Cargar cookies de sesión si existen
    cargar_cookies(driver, 'mercadolibre_cookies.json')

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
        print(f"\nSe han encontrado {len(items)} propiedades en la página {page+1}\n")
        send_progress_update(current_search_item=f"Página {page+1}: Se encontraron {len(items)} publicaciones.", page_items_found=len(items))
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
                    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII').lower()
                texto_total_norm = normalizar(f"{titulo_text} {descripcion} {caracteristicas}")
                keywords_norm = [normalizar(kw) for kw in keywords_filtradas]
                encontrados = [kw for kw in keywords_filtradas if normalizar(kw) in texto_total_norm]
                no_encontrados = [kw for kw in keywords_filtradas if normalizar(kw) not in texto_total_norm]
                if not keywords_filtradas:
                    print("⚠️  No se especificaron palabras clave para filtrar.\n")
                    cumple = True
                elif all(normalizar(kw) in texto_total_norm for kw in keywords_filtradas):
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
        if not soup.find('div', class_='ui-pdp-container'): return None

        datos = {'url_publicacion': url}
        
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

        def get_int(key):
            try: return int(re.search(r'\d+', caracteristicas_dict.get(key, '')).group())
            except: return None

        # --- Mapeo a campos estructurados (usando el diccionario unificado) ---
        datos['tipo_inmueble'] = caracteristicas_dict.get('tipo de casa') or caracteristicas_dict.get('tipo de inmueble', 'N/A')
        datos['condicion'] = caracteristicas_dict.get('condición del ítem', '')
        
        datos['dormitorios_min'], datos['dormitorios_max'] = parse_rango(caracteristicas_dict.get('dormitorios', ''))
        datos['banos_min'], datos['banos_max'] = parse_rango(caracteristicas_dict.get('baños', ''))
        datos['superficie_total_min'], datos['superficie_total_max'] = parse_rango(caracteristicas_dict.get('superficie total', ''))
        datos['superficie_cubierta_min'], datos['superficie_cubierta_max'] = parse_rango(caracteristicas_dict.get('área privada', '') or caracteristicas_dict.get('superficie cubierta', ''))
        datos['cocheras_min'], datos['cocheras_max'] = parse_rango(caracteristicas_dict.get('cocheras', ''))
        
        antiguedad_str = caracteristicas_dict.get('antigüedad', '')
        datos['antiguedad'] = 0 if 'a estrenar' in antiguedad_str.lower() else get_int(antiguedad_str)
        
        # Mapeo de booleanos
        datos['es_amoblado'] = caracteristicas_dict.get('amoblado', 'no').lower() == 'sí'
        datos['admite_mascotas'] = caracteristicas_dict.get('admite mascotas', 'no').lower() == 'sí'
        datos['tiene_piscina'] = caracteristicas_dict.get('piscina', 'no').lower() == 'sí'
        datos['tiene_terraza'] = caracteristicas_dict.get('terraza', 'no').lower() == 'sí'
        datos['tiene_jardin'] = caracteristicas_dict.get('jardín', 'no').lower() == 'sí'
        
        return datos
    except Exception as e:
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



def extraer_total_resultados_mercadolibre(url_base_con_filtros):
    """
    Extrae el número total de resultados de MercadoLibre desde la primera página de resultados
    """
    driver = iniciar_driver()
    try:
        # No duplicar _NoIndex_True si ya está en la URL base
        if '_NoIndex_True' in url_base_con_filtros:
            url_primera_pagina = url_base_con_filtros
        else:
            url_primera_pagina = f"{url_base_con_filtros}_NoIndex_True"
        print(f"🔍 [TOTAL ML] Accediendo a: {url_primera_pagina}")
        driver.get(url_primera_pagina)
        time.sleep(3)
        
        # Buscar el elemento que contiene el total de resultados
        try:
            # Múltiples selectores para diferentes versiones de MercadoLibre
            selectores = [
                ".ui-search-search-result__quantity-results",
                ".ui-search-results__quantity-results", 
                ".ui-search-breadcrumb__title",
                ".ui-search-results-header__title"
            ]
            
            total_element = None
            for selector in selectores:
                try:
                    total_element = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"🔍 [TOTAL ML] Elemento encontrado con selector '{selector}'")
                    if total_element:
                        break
                except:
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
                    print("❌ [TOTAL ML] No se encontraron números en el texto")
                    return None
            else:
                print("❌ [TOTAL ML] No se encontró elemento con total de resultados")
                return None
        except Exception as e:
            print(f"🛑 [TOTAL ML] Error al extraer total de resultados: {e}")
            return None
    finally:
        driver.quit()

def run_scraper(filters: dict, keywords: list = None, max_paginas: int = 3, workers_fase1: int = 1, workers_fase2: int = 1):
    """
    Ejecuta el scraper con todos los filtros posibles usando build_mercadolibre_url
    """
    print(f"🚀 [RUN_SCRAPER] Iniciando scraper con filtros completos: {filters}")
    print(f"🚀 [RUN_SCRAPER] Keywords: {keywords}")
    print(f"⚠️  [MODO SECUENCIAL] Usando {workers_fase1} worker(s) por fase")
    
    # Procesar keywords usando la función centralizada
    from core.search_manager import procesar_keywords
    keywords_filtradas = procesar_keywords(' '.join(keywords)) if keywords else []
    print(f"🚀 [RUN_SCRAPER] Keywords filtradas: {keywords_filtradas}")
    
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
    print("\n🔗 [URL BUILD] Construyendo URL con build_mercadolibre_url...")
    try:
        url_base_con_filtros = build_mercadolibre_url(filters)
        print(f"🔗 [URL GENERADA] {url_base_con_filtros}")
        send_progress_update(current_search_item=f"🏠 URL generada con filtros: {url_base_con_filtros[:100]}{'...' if len(url_base_con_filtros) > 100 else ''}")
    except Exception as e:
        print(f"❌ [URL BUILD] Error construyendo URL: {e}")
        send_progress_update(final_message=f"❌ Error construyendo URL: {e}")
        return
    
    # --- EXTRACCIÓN DEL TOTAL DE RESULTADOS ---
    print("\n[Principal] Extrayendo total de resultados desde MercadoLibre...")
    send_progress_update(current_search_item="🔍 Extrayendo total de resultados de MercadoLibre...")
    total_ml = extraer_total_resultados_mercadolibre(url_base_con_filtros)
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
    if urls_recolectadas_bruto:
        # Consultamos a la BD una sola vez por todas las URLs encontradas
        urls_existentes = set(Propiedad.objects.filter(url_publicacion__in=list(urls_recolectadas_bruto)).values_list('url_publicacion', flat=True))
        propiedades_omitidas = len(urls_existentes)
        
        # Las URLs a visitar son las que recolectamos MENOS las que ya existen
        urls_a_visitar_final = urls_recolectadas_bruto - urls_existentes
        
        print(f"[Principal] URLs existentes en BD: {propiedades_omitidas}")
        print(f"[Principal] URLs nuevas para procesar: {len(urls_a_visitar_final)}")
        send_progress_update(current_search_item=f"Publicaciones ya existentes: {propiedades_omitidas}. Nuevas publicaciones a procesar: {len(urls_a_visitar_final)}.")
    else:
        print("[Principal] No se recolectaron URLs para chequear.")
        send_progress_update(current_search_item="No se encontraron URLs para procesar.")

    if urls_a_visitar_final:
        print(f"\n--- FASE 2: Scrapeo de detalles en paralelo (hasta {workers_fase2} hilos)... ---")
        send_progress_update(current_search_item=f"FASE 2: Scrapeando detalles de {len(urls_a_visitar_final)} publicaciones...")
        # ... (inicio FASE 2)
        urls_lista = list(urls_a_visitar_final)
        matched_publications_titles = [] # New: To store titles of matched publications
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
                        if keywords_filtradas:
                            # Normaliza y verifica si todas las keywords están presentes
                            import unicodedata
                            def normalizar(texto):
                                return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII').lower()
                            keywords_norm = [normalizar(kw) for kw in keywords_filtradas]
                            texto_total_norm = normalizar(texto_total)
                            cumple = all(kw in texto_total_norm for kw in keywords_norm)
                            if cumple:
                                print(f"✅ Coincide: {titulo_propiedad}")
                                send_progress_update(current_search_item=f"✅ Coincide: {titulo_propiedad}")
                            else:
                                print(f"❌ No coincide: {titulo_propiedad}")
                                send_progress_update(current_search_item=f"❌ No coincide: {titulo_propiedad}")
                        else:
                            # Mostrar progreso con formato "Búsqueda actual (a/total_ml): Título" 
                            if total_ml:
                                send_progress_update(current_search_item=f"Búsqueda actual ({i+1}/{total_ml:,}): {titulo_propiedad}")
                            else:
                                send_progress_update(current_search_item=f"Procesando publicación {i+1}/{len(urls_lista)}: {titulo_propiedad}")

                        if cumple:
                            # --- MEJORAR CON DATOS DE LOS FILTROS ---
                            # Pre-rellenamos con los datos que ya conocemos de los filtros
                            datos_propiedad['operacion'] = filters.get('operacion', 'venta')
                            datos_propiedad['departamento'] = filters.get('departamento', filters.get('ciudad', 'N/A'))
                            
                            # Si el scraper no encontró un tipo de inmueble, usamos el de los filtros
                            if not datos_propiedad.get('tipo_inmueble'):
                               datos_propiedad['tipo_inmueble'] = filters.get('tipo', 'N/A')
                            
                            Propiedad.objects.create(**datos_propiedad)
                            nuevas_propiedades_guardadas += 1
                            matched_publications_titles.append({'title': datos_propiedad.get('titulo', url_original), 'url': url_original})
                            
                            # Enviar actualización con las publicaciones coincidentes actuales
                            send_progress_update(matched_publications=matched_publications_titles)
                    else:
                        # Cuando no se pueden extraer datos, aún mostrar progreso
                        if total_ml:
                            send_progress_update(current_search_item=f"Búsqueda actual ({i+1}/{total_ml:,}): Error al procesar")
                        else:
                            send_progress_update(current_search_item=f"Procesando publicación {i+1}/{len(urls_lista)}: Error al procesar")
                except Exception as exc:
                    print(f'URL {url_original[:50]}... generó una excepción al guardar: {exc}')

    print("\n--- RESUMEN ---")
    send_progress_update(
        final_message=f"✅ Búsqueda completada. Resumen: {nuevas_propiedades_guardadas} nuevas propiedades guardadas.",
        matched_publications=matched_publications_titles
    )