import re
import requests
from bs4 import BeautifulSoup
from typing import Tuple, Set
from .constants import HEADERS


def parse_rango(texto: str) -> tuple[int | None, int | None]:
    texto = (texto or '').lower()
    if 'monoambiente' in texto:
        return 0, 0
    numeros = [int(n) for n in re.findall(r'\d+', texto)]
    if len(numeros) == 1:
        return numeros[0], numeros[0]
    if len(numeros) >= 2:
        return min(numeros), max(numeros)
    return None, None


def _parse_propiedad_html(soup: BeautifulSoup, url: str):
    if not soup.find('div', class_='ui-pdp-container'):
        return None
    datos = {'url': url}
    datos['titulo'] = (t.text.strip() if (t := soup.find('h1', class_='ui-pdp-title')) else "N/A")
    if pc := soup.find('div', class_='ui-pdp-price__main-container'):
        datos['precio_moneda'] = (m.text.strip() if (m := pc.find('span', 'andes-money-amount__currency-symbol')) else "")
        valor_str = (v.text.strip().replace('.', '') if (v := pc.find('span', 'andes-money-amount__fraction')) else "0")
        import re as _re
        datos['precio_valor'] = int(_re.sub(r'\D', '', valor_str))
    img_tag = (fig.find('img') if (fig := soup.find('figure', 'ui-pdp-gallery__figure')) else None)
    datos['url_imagen'] = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
    datos['descripcion'] = (d.text.strip() if (d := soup.find('p', 'ui-pdp-description__content')) else "")
    caracteristicas_dict = {}
    for row in soup.select('tr.andes-table__row'):
        if (th := row.find('th')) and (td := row.find('td')):
            key = th.text.strip().lower()
            value = td.text.strip()
            caracteristicas_dict[key] = value
    for spec in soup.select('div.ui-vpp-highlighted-specs__key-value'):
        if len(spans := spec.find_all('span')) == 2:
            key = spans[0].text.replace(':', '').strip().lower()
            value = spans[1].text.strip()
            caracteristicas_dict[key] = value
    datos['caracteristicas_texto'] = "\n".join([f"{k.capitalize()}: {v}" for k, v in caracteristicas_dict.items()])
    
    # NUEVO: Guardar el diccionario completo de características para metadata
    datos['caracteristicas_dict'] = caracteristicas_dict.copy()

    def get_int_from_value(value: str):
        try:
            m = re.search(r'\d+', value or '')
            return int(m.group()) if m else None
        except Exception:
            return None

    datos['tipo_inmueble'] = caracteristicas_dict.get('tipo de casa') or caracteristicas_dict.get('tipo de inmueble', 'N/A')
    datos['condicion'] = caracteristicas_dict.get('condición del ítem', '')
    datos['dormitorios_min'], datos['dormitorios_max'] = parse_rango(caracteristicas_dict.get('dormitorios', ''))
    datos['banos_min'], datos['banos_max'] = parse_rango(caracteristicas_dict.get('baños', ''))
    datos['superficie_total_min'], datos['superficie_total_max'] = parse_rango(caracteristicas_dict.get('superficie total', ''))
    datos['superficie_cubierta_min'], datos['superficie_cubierta_max'] = parse_rango(caracteristicas_dict.get('área privada', '') or caracteristicas_dict.get('superficie cubierta', ''))
    datos['cocheras_min'], datos['cocheras_max'] = parse_rango(caracteristicas_dict.get('cocheras', ''))
    antiguedad_str = caracteristicas_dict.get('antigüedad', '')
    datos['antiguedad'] = 0 if 'a estrenar' in antiguedad_str.lower() else get_int_from_value(antiguedad_str)
    datos['es_amoblado'] = caracteristicas_dict.get('amoblado', 'no').lower() == 'sí'
    datos['admite_mascotas'] = caracteristicas_dict.get('admite mascotas', 'no').lower() == 'sí'
    datos['tiene_piscina'] = caracteristicas_dict.get('piscina', 'no').lower() == 'sí'
    datos['tiene_terraza'] = caracteristicas_dict.get('terraza', 'no').lower() == 'sí'
    datos['tiene_jardin'] = caracteristicas_dict.get('jardín', 'no').lower() == 'sí'
    return datos


def scrape_detalle_con_requests(url, api_key=None, use_scrapingbee=False):
    try:
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=90)
        else:
            response = requests.get(url, headers=HEADERS, timeout=90)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        return _parse_propiedad_html(soup, url)
    except Exception:
        return None


def recolectar_urls_de_pagina(url_target, api_key=None, ubicacion=None, use_scrapingbee=False):
    print(f"  [Recolector] Iniciando recolección para: {url_target} (ScrapingBee: {'Sí' if use_scrapingbee else 'No'})")
    try:
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url_target}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, headers=HEADERS, timeout=60)
        else:
            response = requests.get(url_target, headers=HEADERS, timeout=60)
        if response.status_code >= 400:
            print(f"  [Recolector] ERROR: Status {response.status_code} para {url_target}")
            return set(), {}
        soup = BeautifulSoup(response.text, 'lxml')
        items = soup.find_all('li', class_='ui-search-layout__item')
        if not items:
            print(f"  [Recolector] ADVERTENCIA: No se encontraron items en {url_target}")
            return set(), {}
        urls_de_pagina = set()
        titulos_por_url = {}
        for item in items:
            # Buscar el enlace del título de la publicación
            link = item.find('a', class_='poly-component__title') or item.find('a', class_='ui-search-link')
            if not link or not link.has_attr('href'):
                continue
            href = link['href'].split('#')[0]
            titulo = (link.get_text(strip=True) or '').strip()
            # Algunos layouts ponen el texto en el h2 contenedor
            if not titulo:
                h2 = item.find('h2', class_='poly-component__title-wrapper')
                if h2:
                    titulo = h2.get_text(strip=True)
            urls_de_pagina.add(href)
            if titulo:
                # Conservar el primer título visto para una URL
                titulos_por_url.setdefault(href, titulo)
        print(f"  [Recolector] ÉXITO: Se encontraron {len(urls_de_pagina)} URLs en {url_target}")
        # Devolvemos (set(URLs), dict(URL->Título))
        return urls_de_pagina, titulos_por_url
    except Exception as e:
        print(f"  [Recolector] EXCEPCIÓN: Ocurrió un error procesando {url_target}: {e}")
        return set(), {}


# ===== FUNCIONES ESPECÍFICAS PARA INFOCASAS =====

def _parse_propiedad_infocasas_html(soup: BeautifulSoup, url: str):
    """
    Parser específico para propiedades de InfoCasas.
    """
    datos = {'url': url, 'plataforma': 'InfoCasas'}
    
    # Título
    titulo_elem = soup.select_one('h1.property-title') or soup.select_one('h2.lc-title')
    if titulo_elem:
        datos['titulo'] = titulo_elem.get_text(strip=True)
    else:
        datos['titulo'] = "N/A"
    
    # Precio
    precio_elem = soup.select_one('p.main-price')
    if precio_elem:
        precio_texto = precio_elem.get_text(strip=True)
        datos['precio_texto'] = precio_texto
        
        # Extraer moneda y valor
        if 'U$S' in precio_texto:
            datos['precio_moneda'] = 'USD'
            match = re.search(r'U\$S\s*([\d,\.]+)', precio_texto)
            if match:
                try:
                    valor_str = match.group(1).replace(',', '').replace('.', '')
                    datos['precio_valor'] = int(valor_str)
                except ValueError:
                    datos['precio_valor'] = 0
        elif '$' in precio_texto:
            datos['precio_moneda'] = 'UYU'
            match = re.search(r'\$\s*([\d,\.]+)', precio_texto)
            if match:
                try:
                    valor_str = match.group(1).replace(',', '').replace('.', '')
                    datos['precio_valor'] = int(valor_str)
                except ValueError:
                    datos['precio_valor'] = 0
        else:
            datos['precio_moneda'] = ""
            datos['precio_valor'] = 0
    else:
        datos['precio_moneda'] = ""
        datos['precio_valor'] = 0
        datos['precio_texto'] = ""
    
    # Gastos comunes
    gc_elem = soup.select_one('span.commonExpenses')
    if gc_elem:
        datos['gastos_comunes'] = gc_elem.get_text(strip=True)
    
    # Descripción
    desc_elem = soup.select_one('div.property-description')
    if desc_elem:
        datos['descripcion'] = desc_elem.get_text(strip=True)
    else:
        datos['descripcion'] = ""
    
    # Ubicación
    ubicacion_elem = soup.select_one('span.property-location-tag p')
    if ubicacion_elem:
        datos['ubicacion'] = ubicacion_elem.get_text(strip=True)
    
    # Imagen principal
    img_elem = soup.select_one('div.property-image img') or soup.select_one('img[src*="infocasas"]')
    if img_elem and img_elem.get('src'):
        datos['url_imagen'] = img_elem.get('src')
    else:
        datos['url_imagen'] = ""
    
    # Características técnicas (estilo diccionario)
    caracteristicas_dict = {}
    filas_tech = soup.select('div.technical-sheet div.ant-row')
    for fila in filas_tech:
        clave_elem = fila.select_one('div:first-child span.ant-typography')
        valor_elem = fila.select_one('div:last-child strong')
        
        if clave_elem and valor_elem:
            clave = clave_elem.get_text(strip=True).replace('•', '').strip().lower()
            valor = valor_elem.get_text(strip=True)
            caracteristicas_dict[clave] = valor
    
    # Comodidades (estilo lista)
    comodidades = []
    comodidades_elems = soup.select('div.property-facilities span.ant-typography')
    for elem in comodidades_elems:
        texto = elem.get_text(strip=True).replace('•', '').strip()
        if texto and texto not in comodidades:
            comodidades.append(texto)
    
    if comodidades:
        caracteristicas_dict['comodidades'] = ', '.join(comodidades)
    
    # Preparar texto de características
    datos['caracteristicas_texto'] = "\n".join([f"{k.capitalize()}: {v}" for k, v in caracteristicas_dict.items()])
    datos['caracteristicas_dict'] = caracteristicas_dict.copy()
    
    def get_int_from_value(value: str):
        try:
            m = re.search(r'\d+', value or '')
            return int(m.group()) if m else None
        except Exception:
            return None
    
    # Mapear características específicas de InfoCasas
    datos['tipo_inmueble'] = caracteristicas_dict.get('tipo de propiedad', 'N/A')
    datos['condicion'] = caracteristicas_dict.get('estado', '')
    
    # Dormitorios y baños
    datos['dormitorios_min'], datos['dormitorios_max'] = parse_rango(caracteristicas_dict.get('dormitorios', ''))
    datos['banos_min'], datos['banos_max'] = parse_rango(caracteristicas_dict.get('baños', ''))
    
    # Superficie
    superficie_m2 = caracteristicas_dict.get('m² edificados', '')
    datos['superficie_total_min'], datos['superficie_total_max'] = parse_rango(superficie_m2)
    
    # Cocheras/Garajes
    datos['cocheras_min'], datos['cocheras_max'] = parse_rango(caracteristicas_dict.get('garajes', ''))
    
    # Antigüedad (desde año de construcción si está disponible)
    año_construccion = caracteristicas_dict.get('año de construcción', '')
    if año_construccion and año_construccion.isdigit():
        import datetime
        año_actual = datetime.datetime.now().year
        datos['antiguedad'] = año_actual - int(año_construccion)
    else:
        datos['antiguedad'] = None
    
    # Características booleanas basadas en comodidades
    comodidades_text = ' '.join(comodidades).lower()
    datos['es_amoblado'] = 'amoblado' in comodidades_text
    datos['admite_mascotas'] = 'mascotas' in comodidades_text
    datos['tiene_piscina'] = 'piscina' in comodidades_text
    datos['tiene_terraza'] = any(x in comodidades_text for x in ['terraza', 'balcón', 'balcon'])
    datos['tiene_jardin'] = 'jardín' in comodidades_text or 'jardin' in comodidades_text
    
    return datos


def scrape_detalle_infocasas_con_requests(url, api_key=None, use_scrapingbee=False):
    """
    Extrae detalles de una propiedad de InfoCasas usando requests.
    """
    try:
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=90)
        else:
            response = requests.get(url, headers=HEADERS, timeout=90)
        
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        return _parse_propiedad_infocasas_html(soup, url)
    
    except Exception as e:
        print(f"❌ [EXTRACTOR IC] Error al extraer {url}: {e}")
        return None


def recolectar_urls_infocasas_de_pagina(url_target, api_key=None, use_scrapingbee=False):
    """
    Recolecta URLs de propiedades de una página de listado de InfoCasas.
    """
    print(f"  [Recolector IC] Iniciando recolección para: {url_target}")
    
    try:
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url_target}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, headers=HEADERS, timeout=60)
        else:
            response = requests.get(url_target, headers=HEADERS, timeout=60)
        
        if response.status_code >= 400:
            print(f"  [Recolector IC] ERROR: Status {response.status_code} para {url_target}")
            return set(), {}
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Selector específico de InfoCasas para contenedores de propiedades
        contenedores = soup.select('div.lc-dataWrapper')
        
        if not contenedores:
            print(f"  [Recolector IC] ADVERTENCIA: No se encontraron contenedores en {url_target}")
            return set(), {}
        
        urls_de_pagina = set()
        titulos_por_url = {}
        
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
                
                # Extraer título
                titulo_elem = enlace.select_one('h2 span')
                titulo = titulo_elem.get_text(strip=True) if titulo_elem else ""
                
                urls_de_pagina.add(url_completa)
                if titulo:
                    titulos_por_url.setdefault(url_completa, titulo)
        
        print(f"  [Recolector IC] ÉXITO: Se encontraron {len(urls_de_pagina)} URLs en {url_target}")
        return urls_de_pagina, titulos_por_url
    
    except Exception as e:
        print(f"  [Recolector IC] EXCEPCIÓN: Error procesando {url_target}: {e}")
        return set(), {}
