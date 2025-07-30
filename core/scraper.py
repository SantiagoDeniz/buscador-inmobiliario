# core/scraper.py

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# Reemplaza la función scrape_mercadolibre en core/scraper.py

def scrape_mercadolibre(params):
    base_url = "https://listado.mercadolibre.com.uy/inmuebles/"
    
    # ... (Toda la primera parte de construcción de la ruta se mantiene igual) ...
    tipo_inmueble = params.get('tipo_inmueble', 'apartamento') + 's'
    operacion = params.get('operacion', 'alquiler')
    ubicacion_slug = params.get('ubicacion', 'montevideo').lower().replace(" ", "-")
    barrio_slug = params.get('barrio', '').lower().replace(" ", "-")
    
    ubicacion_completa_slug = f"{ubicacion_slug}/{barrio_slug}" if barrio_slug else ubicacion_slug
    
    dormitorios = params.get('dormitorios')
    dormitorios_path = ""
    if dormitorios:
        dormitorios_path = f"{dormitorios}-dormitorios/" if dormitorios != "1" else "1-dormitorio/"
    
    # --- Parte 2: Construcción SEGURA del string de filtros (con checkboxes) ---
    filtros = []
    
    # ... (Todos los filtros anteriores se mantienen igual) ...
    precio_min = params.get('precio_min')
    precio_max = params.get('precio_max')
    if precio_min or precio_max:
        min_p = f"{precio_min}USD" if precio_min else "0"
        max_p = f"{precio_max}USD" if precio_max else "*"
        filtros.append(f"_PriceRange_{min_p}-{max_p}")

    banos = params.get('banos')
    if banos:
        if banos == '3':
            filtros.append("_FULL*BATHROOMS_3-*")
        else:
            filtros.append(f"_FULL*BATHROOMS_{banos}-{banos}")

    cochera = params.get('cochera')
    if cochera:
        if cochera == '1':
            filtros.append("_PARKING*LOTS_1-*")
        elif cochera == '0':
            filtros.append("_PARKING*LOTS_0-0")
            
    condicion = params.get('condicion')
    if condicion:
        if condicion == 'nuevo':
            filtros.append("_ITEM*CONDITION_2230284")
        elif condicion == 'usado':
            filtros.append("_ITEM*CONDITION_2230581")

    superficie = params.get('superficie')
    if superficie:
        min_s, max_s = superficie.split('-')
        filtros.append(f"_TOTAL*AREA_{min_s}m%C2%B2-{max_s}m%C2%B2")
    
    antiguedad = params.get('antiguedad')
    if antiguedad:
        min_a, max_a = antiguedad.split('-')
        filtros.append(f"_PROPERTY*AGE_{min_a}a%C3%B1os-{max_a}a%C3%B1os")

    # --- LÓGICA PARA CHECKBOXES ---
    if params.get('amueblado') == 'true':
        filtros.append("_FURNISHED_242085")
    if params.get('mascotas') == 'true':
        filtros.append("_IS*SUITABLE*FOR*PETS_242085")
    if params.get('aire') == 'true':
        filtros.append("_HAS*AIR*CONDITIONING_242085")
    if params.get('piscina') == 'true':
        filtros.append("_HAS*SWIMMING*POOL_242085")
    if params.get('terraza') == 'true':
        filtros.append("_HAS*TERRACE_242085")
    if params.get('jardin') == 'true':
        filtros.append("_HAS*GARDEN_242085")

    filtros.append("_NoIndex_True")
    final_filters = "".join(filtros)
    
    # --- Parte 3: Construcción de la URL final ---
    full_url = f"{base_url}{tipo_inmueble}/{operacion}/{dormitorios_path}{ubicacion_completa_slug}/{final_filters}"

    print(f"URL FINAL PARA SCRAPING CON SELENIUM: {full_url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    html_content = ""
    try:
        driver.get(full_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-search-results"))
        )
        html_content = driver.page_source
    except Exception as e:
        print(f"Error durante el scraping con Selenium: {e}")
    finally:
        driver.quit()

    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'lxml')
    resultados = []
    
    # Buscamos el <li> que es el contenedor de cada item
    items = soup.find_all('li', class_='ui-search-layout__item')
    print(f"Se encontraron {len(items)} items en la página.")

    for item in items:
        try:
            # --- SECCIÓN CORREGIDA CON LOS SELECTORES NUEVOS ---

            # El título y la URL están en la misma etiqueta <a>
            link_tag = item.find('a', class_='poly-component__title')
            url = link_tag['href']
            titulo = link_tag.text.strip()
            
            # El precio y la moneda están dentro de este contenedor
            precio_container = item.find('div', class_='poly-component__price')
            moneda = precio_container.find('span', class_='andes-money-amount__currency-symbol').text.strip()
            valor = precio_container.find('span', class_='andes-money-amount__fraction').text.strip()
            precio = f"{moneda} {valor}"

            # La imagen ahora se busca por esta clase y priorizamos 'data-src'
            img_tag = item.find('img', class_='poly-component__picture')
            imagen_url = img_tag.get('data-src', img_tag.get('src', '')) # Usa data-src si existe, sino src
            
            # Si logramos extraer todo, lo agregamos a la lista
            resultados.append({
                'titulo': titulo,
                'precio': precio,
                'url': url,
                'imagen_url': imagen_url,
            })
        except AttributeError as e:
            # Este error ocurre si a un item le falta alguna de las etiquetas que buscamos.
            # Lo ignoramos para que el scraper no se detenga por un solo aviso mal formateado.
            # print(f"Item ignorado por falta de un atributo: {e}") # Descomentar para depurar si es necesario
            continue
            
    print(f"Se procesaron exitosamente {len(resultados)} resultados.")
    return resultados