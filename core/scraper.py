import math, concurrent.futures, requests, re, time, os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from .models import Propiedad
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth

load_dotenv()

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
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    stealth(driver, languages=["es-ES", "es"], vendor="Google Inc.", platform="Win32",
            webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return driver

def scrape_detalle_con_requests(url, api_key):
    """
    Scrapea los detalles de una página individual usando requests y el proxy.
    Extrae datos estructurados (dormitorios, baños, etc.) y los devuelve en un diccionario.
    """
    try:
        url_proxy = f'http://api.scraperapi.com?api_key={api_key}&url={url}'
        response = requests.get(url_proxy, headers=HEADERS, timeout=60)

        # Manejo de errores de API (Too Many Requests / Forbidden)
        if response.status_code in [429, 403]:
            print(f"  -> Recibido error {response.status_code}. Reintentando en unos segundos...")
            # Aquí podrías añadir una lógica de reintento más formal si quisieras
            return None
        
        response.raise_for_status() # Lanza error para otros códigos HTTP (404, 500)
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # --- Diccionario para guardar los datos ---
        datos = { 'url_publicacion': url, 'operacion': 'venta' if '/venta/' in url else 'alquiler' }


        # Título
        titulo_tag = soup.find('h1', class_='ui-pdp-title')
        datos['titulo'] = titulo_tag.text.strip() if titulo_tag else "Título no encontrado"

        # Precio
        precio_container = soup.find('div', class_='ui-pdp-price__main-container')
        datos['precio_moneda'] = "N/A"
        datos['precio_valor'] = 0
        if precio_container:
            moneda_tag = precio_container.find('span', class_='andes-money-amount__currency-symbol')
            valor_tag = precio_container.find('span', class_='andes-money-amount__fraction')
            if moneda_tag and valor_tag:
                datos['precio_moneda'] = moneda_tag.text.strip()
                valor_str = valor_tag.text.strip().replace('.', '')
                datos['precio_valor'] = int(re.sub(r'\D', '', valor_str))

        # Imagen Principal
        img_container = soup.find('figure', class_='ui-pdp-gallery__figure')
        img_tag = img_container.find('img') if img_container else None
        datos['url_imagen'] = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""

        # Descripción
        descripcion_tag = soup.find('p', class_='ui-pdp-description__content')
        datos['descripcion'] = descripcion_tag.text.strip() if descripcion_tag else ""

        # --- Extracción ESTRUCTURADA de TODOS los campos ---
        datos['departamento'] = ''
        datos['ciudad_barrio'] = ''
        datos['dormitorios'] = None
        datos['banos'] = None
        datos['superficie_total'] = None
        datos['superficie_cubierta'] = None
        datos['cocheras'] = None
        datos['antiguedad'] = ''
        
        caracteristicas_lista_texto = []
        tabla_features = soup.find('div', class_='ui-pdp-specs__table')
        if tabla_features:
            filas = tabla_features.find_all('tr', class_='andes-table__row')
            for row in filas:
                titulo_th = row.find('th')
                valor_td = row.find('td')
                if titulo_th and valor_td:
                    key = titulo_th.text.strip().lower()
                    value = valor_td.text.strip()
                    caracteristicas_lista_texto.append(f"{key.capitalize()}: {value}")

                    # Mapeo a campos estructurados
                    try:
                        if 'departamento' in key: datos['departamento'] = value
                        if 'ciudad' in key or 'barrio' in key: datos['ciudad_barrio'] = value
                        if 'antigüedad' in key: datos['antiguedad'] = value
                        
                        # Para campos numéricos, extraemos solo el número
                        if 'dormitorios' in key: datos['dormitorios'] = int(re.search(r'\d+', value).group())
                        if 'baños' in key: datos['banos'] = int(re.search(r'\d+', value).group())
                        if 'superficie total' in key: datos['superficie_total'] = int(re.search(r'\d+', value).group())
                        if 'superficie cubierta' in key: datos['superficie_cubierta'] = int(re.search(r'\d+', value).group())
                        if 'cocheras' in key: datos['cocheras'] = int(re.search(r'\d+', value).group())
                    except:
                        pass # Si falla la conversión a número, lo dejamos en None
        
        datos['caracteristicas'] = "\n".join(caracteristicas_lista_texto)
        return datos

    except requests.exceptions.RequestException as e:
        print(f"  -> Error de red para {url[:60]}...: {e}")
        return None
    except Exception as e:
        print(f"  -> Fallo general en scrape_detalle para {url[:60]}... : {e}")
        return None

def recolectar_urls_requests(paginas_de_resultados, api_key, workers):
    urls_encontradas = set()
    def recolectar_una_pagina(url):
        try:
            url_proxy = f'http://api.scraperapi.com?api_key={api_key}&url={url}'
            response = requests.get(url_proxy, timeout=60)
            if response.status_code >= 400: return set()
            soup = BeautifulSoup(response.text, 'lxml')
            items = soup.find_all('li', class_='ui-search-layout__item')
            return {link['href'].split('#')[0] for item in items if (link := item.find('a', 'ui-search-link')) and link.has_attr('href')}
        except: return set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for urls_de_pagina in executor.map(recolectar_una_pagina, paginas_de_resultados):
            urls_encontradas.update(urls_de_pagina)
    return urls_encontradas

def recolectar_urls_selenium(paginas_de_resultados):
    urls_encontradas = set()
    driver = iniciar_driver()
    try:
        for i, url in enumerate(paginas_de_resultados):
            print(f"  Procesando página {i+1}/{len(paginas_de_resultados)} con Selenium...")
            driver.get(url)
            try: WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "ui-search-results")))
            except: break
            soup = BeautifulSoup(driver.page_source, 'lxml')
            items = soup.find_all('li', class_='ui-search-layout__item')
            if not items: break
            urls_encontradas.update({link['href'].split('#')[0] for item in items if (link := item.find('a', 'ui-search-link')) and link.has_attr('href')})
    finally: driver.quit()
    return urls_encontradas

def run_scraper(tipo_inmueble='inmuebles', operacion='venta', ubicacion='montevideo', max_paginas=42, precio_min=None, precio_max=None, workers_fase1=5, workers_fase2=5):
    API_KEY = os.getenv('SCRAPER_API_KEY')
    if not API_KEY: print("ERROR: SCRAPER_API_KEY no definida."); return
    
    urls_recolectadas_total, propiedades_omitidas, nuevas_propiedades_guardadas, urls_a_visitar = 0, 0, 0, set()
    
    base_path = f"https://listado.mercadolibre.com.uy/inmuebles/{tipo_inmueble}/{operacion}/{ubicacion.lower().replace(' ', '-')}/"
    price_filter = f"_PriceRange_{(precio_min or 0)}USD-{(precio_max or '*')}USD" if precio_min is not None or precio_max is not None else ""
    url_base_para_paginacion = f"{base_path}{price_filter}"
    
    paginas_de_resultados = [f"{url_base_para_paginacion}_Desde_{1 + (i * 48)}_NoIndex_True" if i > 0 else f"{url_base_para_paginacion}_NoIndex_True" for i in range(max_paginas)]

    print("\n--- FASE 1: Recolección de URLs ---")
    print("-> Intentando Modo Turbo (rápido con Requests)...")
    urls_a_visitar = recolectar_urls_requests(paginas_de_resultados, API_KEY, workers_fase1)

    if not urls_a_visitar:
        print("-> Modo Turbo falló. Cambiando a Modo Seguro (lento con Selenium)...")
        urls_a_visitar = recolectar_urls_selenium(paginas_de_resultados)

    urls_existentes = set(Propiedad.objects.filter(url_publicacion__in=list(urls_a_visitar)).values_list('url_publicacion', flat=True))
    propiedades_omitidas = len(urls_existentes)
    urls_a_visitar -= urls_existentes
    
    print(f"\n--- FASE 1 COMPLETADA: Se encontraron {len(urls_a_visitar)} URLs únicas y nuevas para procesar. ---")

    if urls_a_visitar:
        print(f"\n--- FASE 2: Scrapeo de detalles en paralelo (hasta {workers_fase2} hilos)... ---")
        urls_lista = list(urls_a_visitar)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase2) as executor:
            mapa_futuros = {executor.submit(scrape_detalle_con_requests, url, API_KEY): url for url in urls_lista}
            for i, futuro in enumerate(concurrent.futures.as_completed(mapa_futuros)):
                url_original = mapa_futuros[futuro]
                try:
                    if datos_propiedad := futuro.result():
                        Propiedad.objects.create(**datos_propiedad)
                        nuevas_propiedades_guardadas += 1
                except Exception as exc:
                    print(f'URL {url_original[:50]}... generó una excepción al guardar: {exc}')

    print("\n--- RESUMEN ---")
    print(f"Propiedades omitidas (ya en BD): {propiedades_omitidas}")
    print(f"Nuevas propiedades guardadas: {nuevas_propiedades_guardadas}")
    print(f"Total de propiedades en la base de datos: {Propiedad.objects.count()}")