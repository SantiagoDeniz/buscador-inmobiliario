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
    """
    Scrapea TODOS los detalles de una única página de propiedad.
    Ahora devuelve un diccionario completo o None si falla.
    """
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-pdp-container"))) # Contenedor principal de la página
        
        soup = BeautifulSoup(driver.page_source, 'lxml')

        # --- Extracción de todos los datos desde la página de detalle ---
        
        # Título
        titulo_tag = soup.find('h1', class_='ui-pdp-title')
        titulo = titulo_tag.text.strip() if titulo_tag else "Título no encontrado"

        # Precio
        precio_container = soup.find('div', class_='ui-pdp-price__main-container')
        moneda = precio_container.find('span', class_='andes-money-amount__currency-symbol').text.strip()
        valor_str = precio_container.find('span', class_='andes-money-amount__fraction').text.strip().replace('.', '')
        valor = int(re.sub(r'\D', '', valor_str))

        # Imagen Principal
        img_container = soup.find('figure', class_='ui-pdp-gallery__figure')
        img_tag = img_container.find('img') if img_container else None
        imagen_url = img_tag['src'] if img_tag else ""

        # Descripción
        descripcion_tag = soup.find('p', class_='ui-pdp-description__content')
        descripcion = descripcion_tag.text.strip() if descripcion_tag else ""

        # Características
        caracteristicas = []
        tabla_features = soup.find('div', class_='ui-pdp-specs__table')
        if tabla_features:
            for row in tabla_features.find_all('tr', class_='andes-table__row'):
                celda_titulo = row.find('th', class_='andes-table__header--left')
                celda_valor = row.find('td', class_='andes-table__column--value')
                if celda_titulo and celda_valor:
                    caracteristicas.append(f"{celda_titulo.text.strip()}: {celda_valor.text.strip()}")
        
        # Devolvemos un diccionario con todos los datos
        return {
            'titulo': titulo,
            'precio_moneda': moneda,
            'precio_valor': valor,
            'url_publicacion': url,
            'url_imagen': imagen_url,
            'descripcion': descripcion,
            'caracteristicas': "\n".join(caracteristicas)
        }

    except Exception as e:
        print(f"Error scrapeando URL individual {url}: {e}")
        return None

def run_scraper(max_paginas=5):
    """
    Función principal refactorizada en dos fases:
    1. Recolectar todas las URLs.
    2. Scrapear los detalles de cada URL.
    """
    print("Iniciando el scraper...")
    driver = iniciar_driver()
    
    urls_a_visitar = []
    
    # --- FASE 1: RECOLECCIÓN DE URLS (sin cambios, sigue igual) ---
    try:
        url_actual = "https://listado.mercadolibre.com.uy/inmuebles/apartamentos/alquiler/montevideo/"
        pagina_actual = 1
        
        while pagina_actual <= max_paginas and url_actual:
            print(f"\n--- Recolectando URLs de la página {pagina_actual} ---")
            driver.get(url_actual)
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.ui-search-layout__item"))
            )
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'lxml')
            items = soup.find_all('li', class_='ui-search-layout__item')

            if not items: break

            for item in items:
                link_tag = item.find('a', class_='poly-component__title') or item.find('a', class_='ui-search-link')
                if link_tag and link_tag.has_attr('href'):
                    url_propiedad = link_tag['href']
                    if not Propiedad.objects.filter(url_publicacion=url_propiedad).exists():
                        urls_a_visitar.append(url_propiedad)
            
            print(f"Recolectadas {len(items)} URLs. Total acumulado: {len(urls_a_visitar)}")

            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                selector_css = "a.andes-pagination__link[title='Siguiente']"
                boton_siguiente = driver.find_element(By.CSS_SELECTOR, selector_css)
                url_actual = boton_siguiente.get_attribute('href')
                pagina_actual += 1
            except Exception:
                print("Fin de la paginación.")
                url_actual = None

    except Exception as e:
        print(f"Error en la FASE 1 (Recolección): {e}")
    
    print(f"\n--- FASE 1 COMPLETADA: Se recolectaron {len(urls_a_visitar)} URLs únicas. ---")

    # --- FASE 2: SCRAPEO DE DETALLES (ahora es más simple) ---
    if not urls_a_visitar:
        print("No hay nuevas URLs para scrapear.")
    else:
        print("\n--- Iniciando FASE 2: Scrapeo de detalles de cada propiedad ---")
        
        for i, url in enumerate(urls_a_visitar):
            print(f"Procesando URL {i+1}/{len(urls_a_visitar)}...")
            
            # La función de scrapeo individual ahora nos da todos los datos
            datos_propiedad = scrape_propiedad_individual(url, driver)
            
            if datos_propiedad:
                Propiedad.objects.create(**datos_propiedad)
                print(f"¡Propiedad '{datos_propiedad['titulo'][:30]}...' guardada!")
            else:
                print(f"Fallo al obtener detalles para la URL. Saltando.")

    # --- FINALIZACIÓN ---
    driver.quit()
    print("Scraper finalizado.")