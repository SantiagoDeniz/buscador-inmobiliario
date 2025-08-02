# core/scraper.py

from bs4 import BeautifulSoup
import requests 
import re
import time
from .models import Propiedad
import concurrent.futures
import os
from dotenv import load_dotenv
import math

# Cargamos las variables de entorno desde el archivo .env
load_dotenv()

def scrape_detalle_con_requests(url, api_key):
    try:
        url_proxy = f'http://api.scraperapi.com?api_key={api_key}&url={url}'
        response = requests.get(url_proxy, timeout=60) # Aumentamos el timeout
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')

        titulo_tag = soup.find('h1', class_='ui-pdp-title')
        titulo = titulo_tag.text.strip() if titulo_tag else "Título no encontrado"

        precio_container = soup.find('div', class_='ui-pdp-price__main-container')
        moneda = precio_container.find('span', class_='andes-money-amount__currency-symbol').text.strip()
        valor_str = precio_container.find('span', class_='andes-money-amount__fraction').text.strip().replace('.', '')
        valor = int(re.sub(r'\D', '', valor_str))

        img_container = soup.find('figure', class_='ui-pdp-gallery__figure')
        img_tag = img_container.find('img') if img_container else None
        imagen_url = img_tag['src'] if img_tag else ""

        descripcion_tag = soup.find('p', class_='ui-pdp-description__content')
        descripcion = descripcion_tag.text.strip() if descripcion_tag else ""

        caracteristicas_tags = soup.find_all('tr', class_='andes-table__row')
        caracteristicas = "\n".join([f"{row.find('th').text.strip()}: {row.find('td').text.strip()}" for row in caracteristicas_tags if row.find('th') and row.find('td')])
        
        return {
            'titulo': titulo, 'precio_moneda': moneda, 'precio_valor': valor,
            'url_publicacion': url, 'url_imagen': imagen_url,
            'descripcion': descripcion, 'caracteristicas': caracteristicas
        }

    except Exception as e:
        print(f"Error en scrape_detalle_con_requests para {url}: {e}")
        return None





def run_scraper(tipo_inmueble='apartamentos', operacion='venta', ubicacion='montevideo', max_paginas=None, workers_fase1=5, workers_fase2=5):
    """
    Versión con detección matemática de páginas y concurrencia adaptativa.
    """
    print(f"Iniciando scraper para {tipo_inmueble} en {operacion} en {ubicacion}...")
    
    API_KEY = os.getenv('SCRAPER_API_KEY')
    if not API_KEY:
        print("ERROR: La variable de entorno SCRAPER_API_KEY no está definida.")
        return

    # Contadores
    urls_recolectadas_total = 0
    propiedades_omitidas = 0
    nuevas_propiedades_guardadas = 0
    
    # --- FASE 0: DETECCIÓN MATEMÁTICA DE PÁGINAS ---
    url_base = f"https://listado.mercadolibre.com.uy/inmuebles/{tipo_inmueble}/{operacion}/{ubicacion.lower().replace(' ', '-')}/"
    paginas_a_scrapear = 1
    
    print("\n--- Iniciando FASE 0: Detección de número total de resultados ---")
    try:
        url_proxy_inicial = f'http://api.scraperapi.com?api_key={API_KEY}&url={url_base}'
        response = requests.get(url_proxy_inicial, timeout=60)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Buscamos el span que contiene el número de resultados
            results_span = soup.find('span', class_='ui-search-search-result__quantity-results')
            if results_span:
                # Extraemos el texto, limpiamos puntos y buscamos el primer número
                results_text = results_span.text.replace('.', '')
                match = re.search(r'(\d+)', results_text)
                if match:
                    total_resultados = int(match.group(1))
                    # Calculamos el número de páginas, 48 resultados por página
                    paginas_calculadas = math.ceil(total_resultados / 48)
                    paginas_a_scrapear = paginas_calculadas
                    print(f"Se encontraron {total_resultados} resultados. Calculando {paginas_a_scrapear} páginas.")
                else:
                    print("No se pudo extraer el número de resultados. Asumiendo 1 página.")
            else:
                # Si no hay span de resultados, probablemente no hay publicaciones
                print("No se encontró el contador de resultados. Probablemente no hay publicaciones. Se asume 0 páginas.")
                paginas_a_scrapear = 0
        else:
             print(f"Respuesta no exitosa ({response.status_code}) al detectar páginas. Se asume 0 páginas.")
             paginas_a_scrapear = 0
    except Exception as e:
        print(f"Error detectando páginas: {e}. Asumiendo 0 páginas.")
        paginas_a_scrapear = 0
    
    # Aplicamos el límite manual del usuario si existe
    if max_paginas is not None:
        paginas_finales = min(paginas_a_scrapear, max_paginas)
        print(f"Límite manual de --paginas={max_paginas} establecido. Se scrapearán {paginas_finales} páginas.")
        paginas_a_scrapear = paginas_finales

    # --- FASE 1: RECOLECCIÓN CONCURRENTE ---
    if paginas_a_scrapear == 0:
        print("No hay páginas para scrapear.")
    else:
        workers_recoleccion = min(paginas_a_scrapear, workers_fase1)
        print(f"\n--- Iniciando FASE 1: Recolectando {paginas_a_scrapear} páginas con {workers_recoleccion} hilos... ---")
        
        paginas_de_resultados = []
        for pagina in range(paginas_a_scrapear):
            offset = 1 + (pagina * 48)
            url_target = url_base if pagina == 0 else f"{url_base}_Desde_{offset}_NoIndex_True"
            paginas_de_resultados.append(url_target)
        
        # ... (código de la FASE 1 concurrente)
        urls_a_visitar = set()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_recoleccion) as executor:
            mapa_futuros_f1 = {executor.submit(recolectar_urls_de_pagina, url, API_KEY, ubicacion): url for url in paginas_de_resultados}
            for futuro in concurrent.futures.as_completed(mapa_futuros_f1):
                urls_nuevas, conteo_items = futuro.result()
                urls_recolectadas_total += conteo_items
                urls_a_visitar.update(urls_nuevas)
        
        # ... (código de chequeo de duplicados y Fase 2)
        urls_existentes = set(Propiedad.objects.filter(url_publicacion__in=list(urls_a_visitar)).values_list('url_publicacion', flat=True))
        propiedades_omitidas = len(urls_existentes)
        urls_a_visitar = urls_a_visitar - urls_existentes
        print(f"\n--- FASE 1 COMPLETADA: Se encontraron {len(urls_a_visitar)} URLs únicas y nuevas. ---")
        
        if urls_a_visitar:
            print(f"\n--- Iniciando FASE 2: Scrapeo de detalles en paralelo (hasta {workers_fase2} hilos)... ---")
            urls_lista = list(urls_a_visitar)
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase2) as executor:
                mapa_futuros_f2 = {executor.submit(scrape_detalle_con_requests, url, API_KEY): url for url in urls_lista}
                for i, futuro in enumerate(concurrent.futures.as_completed(mapa_futuros_f2)):
                    url_original = mapa_futuros_f2[futuro]
                    print(f"Procesando resultado {i+1}/{len(urls_lista)}...")
                    try:
                        datos_propiedad = futuro.result()
                        if datos_propiedad:
                            Propiedad.objects.create(**datos_propiedad)
                            nuevas_propiedades_guardadas += 1
                            print(f"¡Propiedad '{datos_propiedad['titulo'][:30]}...' guardada!")
                    except Exception as exc:
                        print(f'URL {url_original[:50]}... generó una excepción: {exc}')

    # --- Resumen Final ---
    print("\n--------------------")
    print("SCRAPEO FINALIZADO - RESUMEN")
    print("--------------------")
    print(f"Total de propiedades vistas: {urls_recolectadas_total}")
    print(f"Propiedades omitidas (ya en BD): {propiedades_omitidas}")
    print(f"Nuevas propiedades guardadas: {nuevas_propiedades_guardadas}")
    print(f"Total de propiedades en la base de datos: {Propiedad.objects.count()}")
    print("--------------------")

# También necesitamos actualizar la función interna para que reciba la API key y la ubicación
def recolectar_urls_de_pagina(url_target, api_key, ubicacion):
    try:
        url_proxy = f'http://api.scraperapi.com?api_key={api_key}&url={url_target}'
        response = requests.get(url_proxy, timeout=60)
        
        # Chequeo de redirección mejorado
        final_url_text = response.request.url.lower()
        if ubicacion.lower().replace('-', ' ') not in final_url_text.replace('-', ' '):
            print(f"  -> Redirección detectada. Omitiendo página.")
            return set(), 0
        
        if response.status_code >= 400:
            print(f"  -> Error {response.status_code} en {url_target}. Omitiendo página.")
            return set(), 0
            
        soup = BeautifulSoup(response.text, 'lxml')
        items = soup.find_all('li', class_='ui-search-layout__item')
        if not items: return set(), 0
        urls_de_pagina = {link['href'].split('#')[0] for item in items if (link := item.find('a', class_='poly-component__title') or item.find('a', class_='ui-search-link')) and link.has_attr('href')}
        return urls_de_pagina, len(items)
    except Exception as e:
        print(f"Error recolectando {url_target}: {e}")
        return set(), 0