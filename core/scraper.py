# core/scraper.py

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
import time

# ¡Importante! Importamos nuestro modelo de la base de datos
from .models import Propiedad

def iniciar_driver():
    """Configura e inicia el driver de Selenium con opciones de estabilidad."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # --- NUEVOS ARGUMENTOS PARA ESTABILIDAD ---
    chrome_options.add_argument("--disable-gpu") # Desactiva la aceleración por hardware, a veces causa problemas en headless.
    chrome_options.add_argument("--window-size=1920x1080") # Define un tamaño de ventana virtual.
    chrome_options.add_argument("--disable-extensions") # Desactiva extensiones que puedan interferir.
    chrome_options.add_argument("--log-level=3") # Reduce la cantidad de "ruido" en la terminal.

    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_propiedad_individual(url, driver):
    """Scrapea los detalles de una única página de propiedad USANDO EL DRIVER EXISTENTE."""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-pdp-description"))
        )
        soup = BeautifulSoup(driver.page_source, 'lxml')

        descripcion_tag = soup.find('p', class_='ui-pdp-description__content')
        descripcion = descripcion_tag.text.strip() if descripcion_tag else ""

        caracteristicas = []
        tabla_features = soup.find('div', class_='ui-pdp-specs__table')
        if tabla_features:
            for row in tabla_features.find_all('tr', class_='andes-table__row'):
                celda_titulo = row.find('th', class_='andes-table__header--left')
                celda_valor = row.find('td', class_='andes-table__column--value')
                if celda_titulo and celda_valor:
                    titulo_caracteristica = celda_titulo.text.strip()
                    valor_caracteristica = celda_valor.text.strip()
                    caracteristicas.append(f"{titulo_caracteristica}: {valor_caracteristica}")
        
        return descripcion, "\n".join(caracteristicas)
    except Exception as e:
        print(f"Error scrapeando URL individual {url}: {e}")
        return None, None

# Reemplaza SOLO la función run_scraper en core/scraper.py

def run_scraper(max_paginas=5):
    """
    Función principal que orquesta el scrapeo con una URL base robusta y paginación.
    """
    print("Iniciando el scraper...")
    driver = iniciar_driver()
    
    # --- URL CORREGIDA Y MEJORADA ---
    # Parámetros de la búsqueda que queremos realizar.
    # Más adelante, podremos pasar estos parámetros a la función.
    params = {
        'tipo_inmueble': 'apartamentos',
        'operacion': 'alquiler',
        'ubicacion': 'montevideo'
    }
    
    # Construimos una URL base limpia y garantizada para funcionar
    url_actual = f"https://listado.mercadolibre.com.uy/inmuebles/{params['tipo_inmueble']}/{params['operacion']}/{params['ubicacion']}/"
    
    pagina_actual = 1
    
    try:
        while pagina_actual <= max_paginas and url_actual:
            print(f"\n--- Scrapeando página de resultados {pagina_actual}: {url_actual[:70]}... ---")
            driver.get(url_actual)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui-search-results"))
            )
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'lxml')
            items = soup.find_all('li', class_='ui-search-layout__item')
            
            if not items:
                print("No se encontraron propiedades. Terminando.")
                break

            propiedades_a_visitar = []
            for item in items:
                try:
                    link_tag = item.find('a', class_='poly-component__title') or item.find('a', class_='ui-search-link')
                    if not link_tag: continue
                    
                    url_propiedad = link_tag['href']
                    if Propiedad.objects.filter(url_publicacion=url_propiedad).exists():
                        print(f"Propiedad ya existe, saltando: {link_tag.text.strip()[:30]}...")
                        continue

                    # ... (el resto de la lógica de extracción de datos del item es igual)
                    precio_container = item.find('div', class_='poly-component__price')
                    moneda = precio_container.find('span', class_='andes-money-amount__currency-symbol').text.strip()
                    valor_str = precio_container.find('span', class_='andes-money-amount__fraction').text.strip().replace('.', '')
                    valor = int(re.sub(r'\D', '', valor_str))
                    img_tag = item.find('img', class_='poly-component__picture')
                    
                    propiedades_a_visitar.append({
                        'titulo': link_tag.text.strip(),
                        'precio_moneda': moneda,
                        'precio_valor': valor,
                        'url_publicacion': url_propiedad,
                        'url_imagen': img_tag.get('data-src', img_tag.get('src', ''))
                    })
                except Exception:
                    continue
            
            print(f"Se recolectaron {len(propiedades_a_visitar)} nuevas propiedades para visitar.")

            for prop_data in propiedades_a_visitar:
                print(f"Scrapeando detalles de: {prop_data['titulo'][:30]}...")
                descripcion, caracteristicas = scrape_propiedad_individual(prop_data['url_publicacion'], driver)
                
                if descripcion is None and caracteristicas is None:
                    print(f"Fallo al obtener detalles para {prop_data['titulo'][:30]}. Saltando.")
                    continue

                Propiedad.objects.create(
                    **prop_data,
                    descripcion=descripcion,
                    caracteristicas=caracteristicas
                )
                print(f"¡Propiedad '{prop_data['titulo'][:30]}...' guardada!")

            # Lógica de Paginación
            try:
                selector_css = "a.andes-pagination__link[title='Siguiente']"
                boton_siguiente = driver.find_element(By.CSS_SELECTOR, selector_css)
                url_actual = boton_siguiente.get_attribute('href')
                pagina_actual += 1
            except Exception:
                print("No se encontró el botón 'Siguiente'. Fin de la paginación.")
                url_actual = None

    finally:
        driver.quit()
        print("Scraper finalizado.")