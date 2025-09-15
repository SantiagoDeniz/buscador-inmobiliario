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
