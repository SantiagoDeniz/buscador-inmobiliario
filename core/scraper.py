


# --- Scraper con Selenium y filtrado detallado para MercadoLibre ---
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
# Imports faltantes y definiciones globales
import os
import re
import concurrent.futures
from core.models import Propiedad
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService

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

def build_mercadolibre_url(filters: Dict[str, Any]) -> str:
    base = 'https://listado.mercadolibre.com.uy/inmuebles/'
    tipo = filters.get('tipo', '').replace(' ', '-').lower()
    operacion = filters.get('operacion', '').lower()
    departamento = filters.get('departamento', '').replace(' ', '-').lower()
    ciudad = filters.get('ciudad', '').replace(' ', '-').lower()
    precio_min = filters.get('precio_min', '')
    precio_max = filters.get('precio_max', '')
    moneda = filters.get('moneda', 'USD').upper()  # USD por defecto

    url = base
    if tipo:
        url += f'{tipo}/'
    if operacion:
        url += f'{operacion}/'
    if departamento:
        url += f'{departamento}/'
    if departamento == 'montevideo' and ciudad:
        url += f'{ciudad}/'

    # El segmento de rango de precios se agrega después de la ruta principal
    price_segment = ''
    if precio_min or precio_max:
        min_val = str(precio_min) if precio_min else '0'
        max_val = str(precio_max) if precio_max else '0'
        price_segment = f'_PriceRange_{min_val}{moneda}-{max_val}{moneda}'
    url += price_segment
    return url


def scrape_mercadolibre(filters: Dict[str, Any], keywords: List[str], max_pages: int = 3) -> List[Dict[str, Any]]:
    def cargar_cookies(driver, cookies_path):
        import json
        import os
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

    import re
    # Importar aquí para evitar dependencias cruzadas
    from core.search_manager import procesar_keywords
    keywords_filtradas = procesar_keywords(' '.join(keywords))
    base_url = build_mercadolibre_url(filters)
    print(f"[scraper] URL base de búsqueda: {base_url}")
    print(f"[scraper] Palabras clave filtradas: {keywords_filtradas}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Usar el servicio de Chrome sin especificar un ejecutable,
    # para que Selenium lo busque en el PATH del sistema.
    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    stealth(driver, languages=["es-ES", "es"], vendor="Google Inc.", platform="Win32",
            webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)

    # Cargar cookies de sesión si existen
    cargar_cookies(driver, 'mercadolibre_cookies.json')

    links = []
    # Patrones prohibidos por robots.txt
    import fnmatch
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
        if page == 0:
            url = base_url
        else:
            desde = 1 + 48 * page
            url = f"{base_url}_Desde_{desde}_NoIndex_True"
        print(f"[scraper] Selenium visitando: {url}")
        driver.get(url)
        time.sleep(3)
        items = driver.find_elements(By.CSS_SELECTOR, 'div.poly-card--grid-card')
        print(f"Se han encontrado {len(items)} propiedades en la página {page+1}")
        publicaciones = []
        for idx, item in enumerate(items, 1):
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
        for pub in publicaciones:
            print(f"propiedad {pub['idx']}: {pub['titulo']} - {pub['url']}")
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
                import unicodedata
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
                links.append({'url': pub['url']})
        if len(items) < 48:
            print(f"Última página detectada (menos de 48 propiedades). Se detiene la búsqueda.")
            break
    driver.quit()
    print(f"[scraper] Resultados encontrados: {len(links)}")
    return links

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
    
    # Usar el servicio de Chrome sin especificar un ejecutable,
    # para que Selenium lo busque en el PATH del sistema.
    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    stealth(driver, languages=["es-ES", "es"], vendor="Google Inc.", platform="Win32",
            webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return driver


def parse_rango(texto):
    texto = texto.lower()
    if 'monoambiente' in texto: return 0, 0
    numeros = [int(n) for n in re.findall(r'\d+', texto)]
    if len(numeros) == 1: return numeros[0], numeros[0]
    if len(numeros) >= 2: return min(numeros), max(numeros)
    return None, None

def scrape_detalle_con_requests(url, api_key):
    """
    Scrapea detalles con una lógica de extracción de características renovada y robusta.
    """
    try:
        params = {'api_key': api_key, 'url': url}
        response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=90)
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


def recolectar_urls_de_pagina(url_target, api_key, ubicacion):
    """
    Función de recolección para un hilo, AHORA CON LOGS DETALLADOS.
    """
    print(f"  [Hilo] Iniciando recolección para: {url_target}")
    try:
        url_proxy = f'https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={url_target}'
        response = requests.get(url_proxy, headers=HEADERS, timeout=60)
        
        if response.status_code >= 400:
            print(f"  [Hilo] ERROR: Status {response.status_code} para {url_proxy}")
            return set(), 0

        soup = BeautifulSoup(response.text, 'lxml')
        items = soup.find_all('li', class_='ui-search-layout__item')
        if not items:
            print(f"  [Hilo] ADVERTENCIA: No se encontraron items en {url_target}")
            return set(), 0

        urls_de_pagina = {link['href'].split('#')[0] for item in items if (link := item.find('a', class_='poly-component__title') or item.find('a', class_='ui-search-link')) and link.has_attr('href')}
        print(f"  [Hilo] ÉXITO: Se encontraron {len(urls_de_pagina)} URLs en {url_target}")
        return urls_de_pagina, len(items)
    except Exception as e:
        print(f"  [Hilo] EXCEPCIÓN: Ocurrió un error procesando {url_target}: {e}")
        return set(), 0

def recolectar_urls_selenium(paginas_de_resultados):
    # (Esta función no cambia, es idéntica a la que me pasaste)
    urls_encontradas = set()
    driver = iniciar_driver()
    try:
        for i, url in enumerate(paginas_de_resultados):
            print(f"  Procesando página {i+1}/{len(paginas_de_resultados)} con Selenium...")
            driver.get(url)
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "ui-search-results")))
            except:
                break
            soup = BeautifulSoup(driver.page_source, 'lxml')
            items = soup.find_all('li', class_='ui-search-layout__item')
            if not items:
                break
            urls_encontradas.update({link['href'].split('#')[0] for item in items if (link := item.find('a', 'ui-search-link')) and link.has_attr('href')})
    finally:
        driver.quit()
    return urls_encontradas

def run_scraper(tipo_inmueble=None, operacion='venta', ubicacion='montevideo', max_paginas=42, precio_min=None, precio_max=None, workers_fase1=5, workers_fase2=5):
    API_KEY = os.getenv('SCRAPINGBEE_API_KEY')
    if not API_KEY: print("ERROR: SCRAPINGBEE_API_KEY no definida."); return
    
    propiedades_omitidas = 0
    nuevas_propiedades_guardadas = 0
    urls_a_visitar_final = set()
    
    # --- CONSTRUCCIÓN DE URL BASE ---
    path_segment = f"inmuebles/{tipo_inmueble}" if tipo_inmueble else "inmuebles"
    base_path = f"https://listado.mercadolibre.com.uy/{path_segment}/{operacion}/{ubicacion.lower().replace(' ', '-')}/"
    price_filter = f"_PriceRange_{(precio_min or 0)}USD-{(precio_max or '*')}USD" if precio_min is not None or precio_max is not None else ""
    url_base_con_filtros = f"{base_path}{price_filter}"
    
    print(f"\n[Principal] URL Base construida: {url_base_con_filtros}")
    
    # --- FASE 1: RECOLECCIÓN ---
    paginas_de_resultados = [f"{url_base_con_filtros}_Desde_{1 + (i * 48)}_NoIndex_True" if i > 0 else f"{url_base_con_filtros}_NoIndex_True" for i in range(max_paginas)]
    
    print(f"\n--- FASE 1: Se intentarán recolectar {len(paginas_de_resultados)} páginas con {workers_fase1} hilos... ---")
    
    urls_recolectadas_bruto = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase1) as executor:
        # (La lógica de hilos no cambia)
        mapa_futuros = {executor.submit(recolectar_urls_de_pagina, url, API_KEY, ubicacion): url for url in paginas_de_resultados}
        for futuro in concurrent.futures.as_completed(mapa_futuros):
            urls_nuevas, _ = futuro.result()
            urls_recolectadas_bruto.update(urls_nuevas)

    print(f"\n[Principal] FASE 1 Recolección Bruta Finalizada. Se obtuvieron {len(urls_recolectadas_bruto)} URLs en total.")

    # --- LÓGICA DE DEDUPLICACIÓN (con logs) ---
    print("\n[Principal] Iniciando chequeo de duplicados contra la base de datos...")
    if urls_recolectadas_bruto:
        # Consultamos a la BD una sola vez por todas las URLs encontradas
        urls_existentes = set(Propiedad.objects.filter(url_publicacion__in=list(urls_recolectadas_bruto)).values_list('url_publicacion', flat=True))
        propiedades_omitidas = len(urls_existentes)
        
        # Las URLs a visitar son las que recolectamos MENOS las que ya existen
        urls_a_visitar_final = urls_recolectadas_bruto - urls_existentes
        
        print(f"[Principal] URLs existentes en BD: {propiedades_omitidas}")
        print(f"[Principal] URLs nuevas para procesar: {len(urls_a_visitar_final)}")
    else:
        print("[Principal] No se recolectaron URLs para chequear.")

    if urls_a_visitar_final:
        print(f"\n--- FASE 2: Scrapeo de detalles en paralelo (hasta {workers_fase2} hilos)... ---")
        # ... (inicio FASE 2)
        urls_lista = list(urls_a_visitar_final)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase2) as executor:
            mapa_futuros = {executor.submit(scrape_detalle_con_requests, url, API_KEY): url for url in urls_lista}
            for i, futuro in enumerate(concurrent.futures.as_completed(mapa_futuros)):
                url_original = mapa_futuros[futuro]
                print(f"Procesando resultado {i+1}/{len(urls_lista)}...")
                try:
                    if datos_propiedad := futuro.result():
                        # --- ¡AQUÍ ESTÁ LA MEJORA! ---
                        # Pre-rellenamos con los datos que ya conocemos de la búsqueda
                        datos_propiedad['operacion'] = operacion
                        datos_propiedad['departamento'] = ubicacion.replace('-', ' ').title() # Capitalizamos
                        
                        # Si el scraper no encontró un tipo de inmueble, usamos el de la búsqueda
                        if not datos_propiedad.get('tipo_inmueble'):
                           datos_propiedad['tipo_inmueble'] = tipo_inmueble if tipo_inmueble else 'N/A'
                        
                        Propiedad.objects.create(**datos_propiedad)
                        nuevas_propiedades_guardadas += 1
                except Exception as exc:
                    print(f'URL {url_original[:50]}... generó una excepción al guardar: {exc}')

    print("\n--- RESUMEN ---")
    print(f"Propiedades omitidas (ya en BD): {propiedades_omitidas}")
    print(f"Nuevas propiedades guardadas: {nuevas_propiedades_guardadas}")
    print(f"Total de propiedades en la base de datos: {Propiedad.objects.count()}")