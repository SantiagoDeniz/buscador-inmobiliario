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
from selenium_stealth import stealth

def iniciar_driver():
    """Configura e inicia el driver de Selenium en modo 'stealth' para ser indetectable."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    
    # Algunas opciones que stealth recomienda
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # --- ¡LA MAGIA DE STEALTH! ---
    stealth(driver,
            languages=["es-ES", "es"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    # -----------------------------
    
    return driver

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
    Función principal que simula una visita inicial para obtener cookies
    antes de proceder con el scrapeo por lotes.
    """
    print("Iniciando el scraper...")
    driver = iniciar_driver()
    
    urls_a_visitar = set()
    
    try:
        # --- PASO DE CALENTAMIENTO: OBTENER COOKIES ---
        print("Fase de calentamiento: Visitando página principal para obtener cookies...")
        driver.get("https://www.mercadolibre.com.uy/")
        
        try:
            # Esperamos hasta 5 segundos por el botón de aceptar cookies y hacemos clic si aparece
            boton_cookies = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='action:understood-button']"))
            )
            boton_cookies.click()
            print("Banner de cookies aceptado.")
            time.sleep(2) # Pausa después de aceptar
        except Exception:
            print("No se encontró el banner de cookies o no fue necesario hacer clic.")
        
        # --- FASE 1: RECOLECCIÓN DE URLS (ahora con una sesión más confiable) ---
        urls_por_pagina = []
        url_base = "https://listado.mercadolibre.com.uy/inmuebles/apartamentos/alquiler/montevideo/"
        
        for pagina in range(max_paginas):
            offset = 1 + (pagina * 48)
            url_actual = url_base if pagina == 0 else f"{url_base}_Desde_{offset}_NoIndex_True"
            
            print(f"\n--- Recolectando URLs de la página {pagina + 1} ---")
            driver.get(url_actual)
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ui-search-results"))
                )
                time.sleep(1)
            except Exception:
                print("La página no cargó los resultados, incluso después del calentamiento. Terminando recolección.")
                driver.save_screenshot('debug_screenshot_fase1.png') # Guardamos evidencia si falla
                break

            soup = BeautifulSoup(driver.page_source, 'lxml')
            items = soup.find_all('li', class_='ui-search-layout__item')
            if not items:
                print("No se encontraron más items. Fin de la paginación.")
                break

            urls_de_esta_pagina = []
            for item in items:
                link_tag = item.find('a', class_='poly-component__title') or item.find('a', class_='ui-search-link')
                if link_tag and link_tag.has_attr('href'):
                    url_propiedad = link_tag['href']
                    if not Propiedad.objects.filter(url_publicacion=url_propiedad).exists():
                        urls_de_esta_pagina.append(url_propiedad)
            
            if urls_de_esta_pagina:
                urls_por_pagina.append(urls_de_esta_pagina)
                print(f"Se recolectaron {len(urls_de_esta_pagina)} URLs nuevas.")
    
    except Exception as e:
        print(f"Error en la FASE 1 (Recolección): {e}")
    finally:
        # En esta arquitectura, cerramos el driver al final de todo, no aquí.
        pass

    total_urls_recolectadas = sum(len(p) for p in urls_por_pagina)
    print(f"\n--- FASE 1 COMPLETADA: Se recolectaron {total_urls_recolectadas} URLs únicas en {len(urls_por_pagina)} páginas. ---")
    
    # --- FASE 2: SCRAPEO DE DETALLES ---
    if not urls_por_pagina:
        print("No hay nuevas URLs para scrapear.")
    else:
        print("\n--- Iniciando FASE 2: Scrapeo de detalles de cada propiedad ---")
        
        # Iteramos sobre cada lote de URLs (cada página)
        for i, lote_urls in enumerate(urls_por_pagina):
            print(f"\n--- Procesando LOTE de página {i+1}/{len(urls_por_pagina)} ({len(lote_urls)} propiedades) ---")
            # Ya no reiniciamos el driver, usamos el mismo que tiene las cookies
            try:
                for j, url in enumerate(lote_urls):
                    print(f"Procesando URL {j+1}/{len(lote_urls)} del lote...")
                    datos_propiedad = scrape_propiedad_individual(url, driver)
                    if datos_propiedad:
                        Propiedad.objects.create(**datos_propiedad)
                        print(f"¡Propiedad '{datos_propiedad['titulo'][:30]}...' guardada!")
                    else:
                        print(f"Fallo al obtener detalles para la URL. Saltando.")
            except Exception as e:
                print(f"Ocurrió un error grave en el lote {i+1}: {e}. Continuando con el siguiente lote.")
                # Si el driver crashea, lo reiniciamos para el siguiente lote
                driver.quit()
                driver = iniciar_driver()
                continue

    # --- FINALIZACIÓN ---
    driver.quit()
    print("Scraper finalizado.")