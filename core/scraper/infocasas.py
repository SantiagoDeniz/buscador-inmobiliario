import time
import re
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from typing import List, Dict, Any
from .browser import iniciar_driver, cargar_cookies
from .progress import tomar_captura_debug, send_progress_update
from .url_builder import build_infocasas_url
from .utils import extraer_variantes_keywords, build_keyword_groups, stemming_basico
from .constants import HEADERS


def extraer_total_resultados_infocasas(url_base_con_filtros, api_key=None, use_scrapingbee=False):
    """
    Extrae el total de resultados de InfoCasas desde la página de búsqueda.
    """
    print(f"🔍 [TOTAL IC] Iniciando extracción para URL: {url_base_con_filtros}")
    
    try:
        print("🌐 [CONECTIVIDAD] Probando acceso básico a InfoCasas...")
        test_response = requests.get("https://www.infocasas.com.uy/", headers=HEADERS, timeout=10)
        print(f"✅ [CONECTIVIDAD] InfoCasas accesible - Status: {test_response.status_code}")
    except Exception as e:
        print(f"❌ [CONECTIVIDAD] No se puede acceder a InfoCasas: {e}")
        return None
    
    try:
        print(f"🌐 [TOTAL IC] Intentando con {'ScrapingBee' if (use_scrapingbee and api_key) else 'requests'} primero...")
        print(f"📡 [TOTAL IC] Solicitando: {url_base_con_filtros}")
        
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url_base_con_filtros}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, headers=HEADERS, timeout=60)
        else:
            response = requests.get(url_base_con_filtros, headers=HEADERS, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ [REQUESTS] Status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Selector específico de InfoCasas para cantidad de resultados
            selector = 'div.search-result-display'
            el = soup.select_one(selector)
            
            if el:
                total_text = el.get_text(strip=True)
                print(f"✅ [TOTAL IC] Texto encontrado: '{total_text}'")
                
                # Extraer número del texto
                # Ejemplo: "Mostrando 1 - 21 de 54 resultados" -> 54
                # Ejemplo: "Mostrando1 - 21demás de 400resultados" -> "más de 400" (sin espacios)
                # Manejar tanto con espacios como sin espacios
                match = re.search(r'de\s*(más\s*de\s*\d+|\d+(?:\.\d+)*)\s*resultado', total_text)
                if match:
                    numero_str = match.group(1)
                    if 'más' in numero_str and 'de' in numero_str:
                        # Extraer el número base cuando dice "más de X"
                        numero_match = re.search(r'más\s*de\s*(\d+)', numero_str)
                        if numero_match:
                            return f"más de {numero_match.group(1)}"
                    else:
                        # Limpiar puntos de separación de miles
                        numero_limpio = numero_str.replace('.', '')
                        try:
                            return int(numero_limpio)
                        except ValueError:
                            pass
                
                print(f"❌ [TOTAL IC] No se pudo extraer número de: '{total_text}'")
                return None
            
            print(f"❌ [TOTAL IC] No se encontró el selector '{selector}'")
            return None
    
    except Exception as e:
        print(f"❌ [REQUESTS] Error al extraer total: {e}")
    
    # Fallback con Selenium
    print("🔄 [TOTAL IC] Fallback: intentando con Selenium...")
    driver = None
    try:
        driver = iniciar_driver()
        driver.get(url_base_con_filtros)
        time.sleep(3)
        
        # Intentar encontrar el elemento con Selenium
        try:
            element = driver.find_element(By.CSS_SELECTOR, 'div.search-result-display')
            total_text = element.text.strip()
            print(f"✅ [SELENIUM IC] Texto encontrado: '{total_text}'")
            
            match = re.search(r'de\s*(más\s*de\s*\d+|\d+(?:\.\d+)*)\s*resultado', total_text)
            if match:
                numero_str = match.group(1)
                if 'más' in numero_str and 'de' in numero_str:
                    numero_match = re.search(r'más\s*de\s*(\d+)', numero_str)
                    if numero_match:
                        return f"más de {numero_match.group(1)}"
                else:
                    numero_limpio = numero_str.replace('.', '')
                    try:
                        return int(numero_limpio)
                    except ValueError:
                        pass
        
        except Exception as e:
            print(f"❌ [SELENIUM IC] No se encontró elemento de resultados: {e}")
            return None
    
    except Exception as e:
        print(f"❌ [SELENIUM IC] Error general: {e}")
        return None
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return None


def scrape_infocasas(filtros, keywords=None, max_paginas=3, workers_fase1=1, workers_fase2=1, use_scrapingbee=False, api_key=None):
    """
    Función principal de scraping para InfoCasas.
    """
    print(f"🏠 [INFOCASAS] Iniciando scraping - Filtros: {filtros}")
    
    # Construir URL base
    url_base = build_infocasas_url(filtros)
    print(f"🔗 [INFOCASAS] URL construida: {url_base}")
    
    # Extraer total de resultados
    total_resultados = extraer_total_resultados_infocasas(url_base, api_key, use_scrapingbee)
    if total_resultados is None:
        print("❌ [INFOCASAS] No se pudo extraer el total de resultados")
        return {
            'total_resultados': 0,
            'urls_propiedades': [],
            'propiedades_detalladas': [],
            'keywords_no_encontradas': keywords or []
        }
    
    print(f"📊 [INFOCASAS] Total de resultados: {total_resultados}")
    
    # Preparar keywords
    keywords_filtradas = []
    if keywords:
        from .utils import stemming_basico
        keywords_filtradas = [k.strip().lower() for k in keywords if k.strip()]
    
    keyword_groups = build_keyword_groups(keywords_filtradas)
    print(f"🔍 [INFOCASAS] Keywords preparadas: {keywords_filtradas}")
    
    # Recolectar URLs de propiedades
    urls_propiedades = []
    pagina_actual = 1
    
    while pagina_actual <= max_paginas:
        print(f"📄 [INFOCASAS] Procesando página {pagina_actual}/{max_paginas}")
        
        # Construir URL de la página
        if pagina_actual == 1:
            url_pagina = url_base
        else:
            # InfoCasas usa paginación con parámetro 'pagina'
            separator = '&' if '?' in url_base else '?'
            url_pagina = f"{url_base}{separator}pagina={pagina_actual}"
        
        # Extraer URLs de esta página
        urls_pagina = extraer_urls_propiedades_infocasas(url_pagina, use_scrapingbee, api_key)
        
        if not urls_pagina:
            print(f"❌ [INFOCASAS] No se encontraron URLs en página {pagina_actual}")
            break
        
        urls_propiedades.extend(urls_pagina)
        print(f"✅ [INFOCASAS] Página {pagina_actual}: {len(urls_pagina)} URLs encontradas")
        
        pagina_actual += 1
        time.sleep(1)  # Pausa entre páginas
    
    print(f"📋 [INFOCASAS] Total URLs recolectadas: {len(urls_propiedades)}")
    
    # Filtrar por keywords si están presentes
    urls_filtradas = []
    if keyword_groups:
        print(f"🔍 [INFOCASAS] Filtrando {len(urls_propiedades)} URLs por keywords...")
        for url in urls_propiedades:
            # Para InfoCasas, podríamos implementar filtrado por título si está disponible
            # Por ahora, agregamos todas las URLs
            urls_filtradas.append(url)
    else:
        urls_filtradas = urls_propiedades
    
    print(f"✅ [INFOCASAS] URLs después de filtrar: {len(urls_filtradas)}")
    
    # Extraer detalles de propiedades
    propiedades_detalladas = []
    keywords_no_encontradas = list(keywords_filtradas) if keywords_filtradas else []
    
    if urls_filtradas:
        print(f"📊 [INFOCASAS] Extrayendo detalles de {len(urls_filtradas)} propiedades...")
        
        for i, url in enumerate(urls_filtradas[:50]):  # Limitar a 50 por ahora
            try:
                print(f"🏠 [INFOCASAS] Extrayendo detalles {i+1}/{len(urls_filtradas[:50])}: {url}")
                
                detalle = extraer_detalle_propiedad_infocasas(url, use_scrapingbee, api_key)
                if detalle:
                    # Verificar keywords en el contenido si están presentes
                    cumple_keywords = True
                    if keyword_groups:
                        cumple_keywords = verificar_keywords_en_contenido_infocasas(detalle, keyword_groups)
                    
                    if cumple_keywords:
                        propiedades_detalladas.append(detalle)
                        print(f"✅ [INFOCASAS] Propiedad agregada: {detalle.get('titulo', 'Sin título')}")
                    else:
                        print(f"❌ [INFOCASAS] Propiedad no cumple keywords: {detalle.get('titulo', 'Sin título')}")
                
                time.sleep(0.5)  # Pausa entre requests
                
            except Exception as e:
                print(f"❌ [INFOCASAS] Error al extraer detalles de {url}: {e}")
                continue
    
    resultado = {
        'total_resultados': total_resultados,
        'urls_propiedades': urls_filtradas,
        'propiedades_detalladas': propiedades_detalladas,
        'keywords_no_encontradas': keywords_no_encontradas
    }
    
    print(f"🎯 [INFOCASAS] Scraping completado: {len(propiedades_detalladas)} propiedades extraídas")
    return resultado


def extraer_urls_propiedades_infocasas(url_pagina, use_scrapingbee=False, api_key=None):
    """
    Extrae URLs de propiedades de una página de listado de InfoCasas.
    """
    print(f"🔗 [URLS IC] Extrayendo URLs de: {url_pagina}")
    
    try:
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url_pagina}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, headers=HEADERS, timeout=60)
        else:
            response = requests.get(url_pagina, headers=HEADERS, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ [URLS IC] Status: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Selector específico de InfoCasas para contenedores de propiedades
        contenedores = soup.select('div.lc-dataWrapper')
        
        urls = []
        for contenedor in contenedores:
            # Buscar el enlace principal de la propiedad
            enlace = contenedor.select_one('a.lc-data')
            if enlace and enlace.get('href'):
                href = enlace.get('href')
                # Construir URL completa
                if href.startswith('/'):
                    url_completa = f"https://www.infocasas.com.uy{href}"
                else:
                    url_completa = href
                urls.append(url_completa)
        
        print(f"✅ [URLS IC] {len(urls)} URLs extraídas")
        return urls
    
    except Exception as e:
        print(f"❌ [URLS IC] Error al extraer URLs: {e}")
        return []


def extraer_detalle_propiedad_infocasas(url_propiedad, use_scrapingbee=False, api_key=None):
    """
    Extrae detalles completos de una propiedad específica de InfoCasas.
    """
    try:
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url_propiedad}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, headers=HEADERS, timeout=60)
        else:
            response = requests.get(url_propiedad, headers=HEADERS, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ [DETALLE IC] Status {response.status_code} para {url_propiedad}")
            return None
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extraer información básica
        detalle = {
            'url': url_propiedad,
            'plataforma': 'InfoCasas'
        }
        
        # Título
        titulo_elem = soup.select_one('h1.property-title') or soup.select_one('h2.lc-title')
        if titulo_elem:
            detalle['titulo'] = titulo_elem.get_text(strip=True)
        
        # Precio
        precio_elem = soup.select_one('p.main-price')
        if precio_elem:
            precio_texto = precio_elem.get_text(strip=True)
            detalle['precio_texto'] = precio_texto
            
            # Extraer moneda y valor
            if 'U$S' in precio_texto:
                detalle['moneda'] = 'USD'
                match = re.search(r'U\$S\s*([\d,\.]+)', precio_texto)
                if match:
                    try:
                        valor = float(match.group(1).replace(',', '').replace('.', ''))
                        detalle['precio'] = valor
                    except ValueError:
                        pass
            elif '$' in precio_texto:
                detalle['moneda'] = 'UYU'
                match = re.search(r'\$\s*([\d,\.]+)', precio_texto)
                if match:
                    try:
                        valor = float(match.group(1).replace(',', '').replace('.', ''))
                        detalle['precio'] = valor
                    except ValueError:
                        pass
        
        # Gastos comunes
        gc_elem = soup.select_one('span.commonExpenses')
        if gc_elem:
            detalle['gastos_comunes'] = gc_elem.get_text(strip=True)
        
        # Descripción
        desc_elem = soup.select_one('div.property-description')
        if desc_elem:
            detalle['descripcion'] = desc_elem.get_text(strip=True)
        
        # Ubicación
        ubicacion_elem = soup.select_one('span.property-location-tag p')
        if ubicacion_elem:
            detalle['ubicacion'] = ubicacion_elem.get_text(strip=True)
        
        # Características técnicas (estilo diccionario)
        caracteristicas = {}
        filas_tech = soup.select('div.technical-sheet div.ant-row')
        for fila in filas_tech:
            clave_elem = fila.select_one('div:first-child span.ant-typography')
            valor_elem = fila.select_one('div:last-child strong')
            
            if clave_elem and valor_elem:
                clave = clave_elem.get_text(strip=True).replace('•', '').strip()
                valor = valor_elem.get_text(strip=True)
                caracteristicas[clave] = valor
        
        if caracteristicas:
            detalle['caracteristicas'] = caracteristicas
        
        # Comodidades (estilo lista)
        comodidades = []
        comodidades_elems = soup.select('div.property-facilities span.ant-typography')
        for elem in comodidades_elems:
            texto = elem.get_text(strip=True).replace('•', '').strip()
            if texto and texto not in comodidades:
                comodidades.append(texto)
        
        if comodidades:
            detalle['comodidades'] = comodidades
        
        return detalle
    
    except Exception as e:
        print(f"❌ [DETALLE IC] Error al extraer detalles de {url_propiedad}: {e}")
        return None


def verificar_keywords_en_contenido_infocasas(detalle, keyword_groups):
    """
    Verifica si el contenido de la propiedad contiene las keywords requeridas.
    """
    if not keyword_groups:
        return True
    
    # Construir texto completo
    titulo = detalle.get('titulo', '')
    descripcion = detalle.get('descripcion', '')
    ubicacion = detalle.get('ubicacion', '')
    caracteristicas = ' '.join([f"{k} {v}" for k, v in detalle.get('caracteristicas', {}).items()])
    comodidades = ' '.join(detalle.get('comodidades', []))
    
    texto_completo = f"{titulo} {descripcion} {ubicacion} {caracteristicas} {comodidades}".lower()
    
    # Verificar cada grupo de keywords
    for grupo in keyword_groups:
        grupo_encontrado = False
        for keyword in grupo:
            if keyword.lower() in texto_completo:
                grupo_encontrado = True
                break
            # También verificar con stemming
            keyword_stem = stemming_basico(keyword.lower())
            if keyword_stem and keyword_stem in texto_completo:
                grupo_encontrado = True
                break
        
        if not grupo_encontrado:
            return False
    
    return True