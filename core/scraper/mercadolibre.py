import time
import re
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from typing import List, Dict, Any
from .browser import iniciar_driver, cargar_cookies
from .progress import tomar_captura_debug, send_progress_update
from .url_builder import build_mercadolibre_url
from .utils import extraer_variantes_keywords
from .constants import HEADERS


def extraer_total_resultados_mercadolibre(url_base_con_filtros, api_key=None, use_scrapingbee=False):
    print(f"🔍 [TOTAL ML] Iniciando extracción para URL: {url_base_con_filtros}")
    try:
        print("🌐 [CONECTIVIDAD] Probando acceso básico a MercadoLibre...")
        test_response = requests.get("https://www.mercadolibre.com.uy/", headers=HEADERS, timeout=10)
        print(f"✅ [CONECTIVIDAD] MercadoLibre accesible - Status: {test_response.status_code}")
    except Exception as e:
        print(f"❌ [CONECTIVIDAD] No se puede acceder a MercadoLibre: {e}")
        return None
    try:
        print(f"🌐 [TOTAL ML] Intentando con {'ScrapingBee' if (use_scrapingbee and api_key) else 'requests'} primero...")
        if '_NoIndex_True' in url_base_con_filtros:
            url_primera_pagina = url_base_con_filtros
        else:
            url_primera_pagina = f"{url_base_con_filtros}_NoIndex_True"
        print(f"📡 [TOTAL ML] Solicitando: {url_primera_pagina}")
        if use_scrapingbee and api_key:
            params = {'api_key': api_key, 'url': url_primera_pagina}
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, headers=HEADERS, timeout=60)
        else:
            response = requests.get(url_primera_pagina, headers=HEADERS, timeout=60)
        if response.status_code != 200:
            print(f"❌ [REQUESTS] Status: {response.status_code}")
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml')
            selectores = [
                '.ui-search-search-result__quantity-results',
                '.ui-search-results__quantity-results',
                '.ui-search-breadcrumb__title',
                '.ui-search-results-header__title',
                "[class*='quantity-results']",
                "[class*='results-quantity']",
            ]
            total_text = None
            for selector in selectores:
                el = soup.select_one(selector)
                if el and el.get_text(strip=True):
                    total_text = el.get_text(strip=True)
                    break
            if not total_text:
                m = re.search(r'(\d{1,3}(?:[.,]\d{3})+|\d+)\s*resultados?', soup.get_text(" ", strip=True), re.IGNORECASE)
                if m:
                    total_text = m.group(0)
            if not total_text:
                patterns = [r'"quantity"\s*:\s*(\d+)', r'"total"\s*:\s*(\d+)', r'"numberOfItems"\s*:\s*(\d+)']
                for pattern in patterns:
                    m = re.search(pattern, html_content, re.IGNORECASE)
                    if m:
                        total_text = m.group(1)
                        break
            if total_text:
                numeros = re.findall(r'[\d.,]+', total_text)
                if numeros:
                    total = int(numeros[0].replace('.', '').replace(',', ''))
                    print(f"✅ [TOTAL EXTRAÍDO] {total:,} publicaciones")
                    return total
            items = soup.find_all('li', class_='ui-search-layout__item')
            if items:
                print(f"⚠️ [TOTAL ML] No se halló total explícito; primera página tiene {len(items)} items")
            print("⚠️ [TOTAL ML] Requests/ScrapingBee obtuvo contenido pero no encontró el total")
        else:
            print(f"❌ [TOTAL ML] Requests falló con código: {response.status_code}")
    except Exception as e:
        print(f"❌ [TOTAL ML] Error con requests: {e}")
    print("🔄 [TOTAL ML] Fallback a Chrome...")
    driver = None
    try:
        print("🔍 [TOTAL ML] Iniciando driver...")
        driver = iniciar_driver()
        print("✅ [TOTAL ML] Driver iniciado correctamente")
        if '_NoIndex_True' in url_base_con_filtros:
            url_primera_pagina = url_base_con_filtros
        else:
            url_primera_pagina = f"{url_base_con_filtros}_NoIndex_True"
        print(f"🔍 [TOTAL ML] Accediendo a: {url_primera_pagina}")
        driver.get(url_primera_pagina)
        print("✅ [TOTAL ML] Página cargada, esperando contenido...")
        time.sleep(2)
        try:
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
        except Exception:
            pass
        page_title = driver.title
        current_url = driver.current_url
        page_source_length = len(driver.page_source)
        print(f"📄 [TOTAL ML] Título: {page_title}")
        print(f"🔗 [TOTAL ML] URL: {current_url}")
        print(f"📏 [TOTAL ML] HTML Length: {page_source_length}")
        page_title_l = page_title.lower()
        page_source_sample = driver.page_source[:2000].lower()
        captcha_indicators = [
            "captcha", "robot", "verificaci", "blocked", "security",
            "too many requests", "rate limit", "forbidden"
        ]
        found_captcha_indicators = [ind for ind in captcha_indicators if ind in page_source_sample or ind in page_title_l]
        if found_captcha_indicators:
            print(f"🛑 [CAPTCHA DETECTED] Indicadores encontrados: {found_captcha_indicators}")
            screenshot_path = tomar_captura_debug(driver, f"captcha_detected_{'-'.join(found_captcha_indicators[:2])}")
            send_progress_update(
                current_search_item=f"🛑 CAPTCHA/Bloqueo detectado: {found_captcha_indicators}. Ver captura.",
                debug_screenshot=screenshot_path
            )
            return None
        selectores = [
            ".ui-search-search-result__quantity-results",
            ".ui-search-results__quantity-results",
            ".ui-search-breadcrumb__title",
            ".ui-search-results-header__title",
            "[class*='quantity-results']",
            "[class*='results-quantity']"
        ]
        total_element = None
        for selector in selectores:
            try:
                total_element = driver.find_element(By.CSS_SELECTOR, selector)
                if total_element:
                    break
            except Exception:
                continue
        if total_element:
            total_text = total_element.text
            numeros = re.findall(r'[\d.,]+', total_text)
            if numeros:
                total = int(numeros[0].replace('.', '').replace(',', ''))
                print(f"✅ [TOTAL ML] Total extraído exitosamente: {total:,}")
                return total
            screenshot_path = tomar_captura_debug(driver, "no_numeros_en_texto")
            send_progress_update(
                current_search_item="❌ No se encontraron números en el total. Ver captura debug.",
                debug_screenshot=screenshot_path
            )
            return None
        else:
            print("❌ [TOTAL ML] No se encontró elemento con total de resultados")
            screenshot_path = tomar_captura_debug(driver, "elemento_total_no_encontrado")
            send_progress_update(
                current_search_item="❌ No se encontró elemento de total. Ver captura debug.",
                debug_screenshot=screenshot_path
            )
            try:
                all_text = driver.find_element(By.TAG_NAME, "body").text
                if "resultado" in all_text.lower():
                    matches = re.findall(r'(\d+(?:[.,]\d+)*)\s*resultados?', all_text, re.IGNORECASE)
                    if matches:
                        total = int(matches[0].replace('.', '').replace(',', ''))
                        print(f"✅ [TOTAL ML] Total extraído mediante búsqueda de texto: {total:,}")
                        return total
                    screenshot_path = tomar_captura_debug(driver, "tiene_resultado_sin_numero")
                    send_progress_update(
                        current_search_item="❌ Página tiene 'resultado' pero sin número. Ver captura debug.",
                        debug_screenshot=screenshot_path
                    )
                else:
                    screenshot_path = tomar_captura_debug(driver, "pagina_sin_resultado")
                    send_progress_update(
                        current_search_item="❌ Página sin 'resultado' - posible error. Ver captura debug.",
                        debug_screenshot=screenshot_path
                    )
            except Exception as e:
                screenshot_path = tomar_captura_debug(driver, "error_analizar_pagina")
                send_progress_update(
                    current_search_item=f"❌ Error analizando página: {e}. Ver captura debug.",
                    debug_screenshot=screenshot_path
                )
            return None
    except Exception as e:
        print(f"🛑 [TOTAL ML] Error general en extracción: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
                print("✅ [TOTAL ML] Driver cerrado correctamente")
            except Exception:
                print("⚠️ [TOTAL ML] Error al cerrar driver")


def scrape_mercadolibre(filters: Dict[str, Any], keywords: List[str], max_pages: int = 3, search_id: str = None) -> Dict[str, List[Dict[str, Any]]]:
    import time
    import unicodedata
    import re
    import os
    from selenium.webdriver.common.by import By

    print(f"🚀 [ML SCRAPER] Iniciando búsqueda - {len(keywords)} keywords, {max_pages} páginas")

    def should_stop():
        if search_id:
            try:
                from core.views import is_search_stopped
                return is_search_stopped(search_id)
            except Exception:
                return False
        return False

    from core.search_manager import procesar_keywords
    keywords_filtradas = procesar_keywords(' '.join(keywords))
    keywords_con_variantes = extraer_variantes_keywords(keywords_filtradas)
    base_url = build_mercadolibre_url(filters)
    print(f"[scraper] URL base de búsqueda: {base_url}")
    print(f"[scraper] Palabras clave filtradas: {keywords_filtradas}")

    driver = iniciar_driver()
    cookies_loaded = cargar_cookies(driver, 'mercadolibre_cookies.json')
    if not cookies_loaded:
        print("[scraper] ⚠️ Continuando sin cookies válidas - podría haber limitaciones de acceso")
        tomar_captura_debug(driver, "cookies_fallidas")

    links = []
    all_publications = []
    matched_publications_titles = []
    current_pub_index = 0

    def url_prohibida(url):
        prohibidos = [
            '/jms/',
            '/adn/api',
        ]
        try:
            path = '/' + '/'.join(url.split('/')[3:])
        except Exception:
            path = url
        if path.startswith('/MLU-'):
            return False
        for patron in prohibidos:
            if path.startswith(patron):
                return True
        return False

    for page in range(max_pages):
        if should_stop():
            print(f"[scraper] Búsqueda detenida por el usuario en página {page + 1}")
            send_progress_update(final_message="Búsqueda detenida por el usuario")
            break

        if page == 0:
            url = base_url
        else:
            desde = 1 + 48 * page
            if '_NoIndex_True' in base_url:
                url = f"{base_url}_Desde_{desde}"
            else:
                url = f"{base_url}_Desde_{desde}_NoIndex_True"
        print(f"[scraper] Selenium visitando: {url}")
        send_progress_update(current_search_item=f"Visitando página {page + 1}...")
        driver.get(url)
        time.sleep(3)

        if should_stop():
            print(f"[scraper] Búsqueda detenida por el usuario después de cargar página {page + 1}")
            send_progress_update(final_message="Búsqueda detenida por el usuario")
            break

        items = driver.find_elements(By.CSS_SELECTOR, 'div.poly-card--grid-card')
        print(f"📄 [PÁGINA {page+1}] {len(items)} publicaciones encontradas")
        send_progress_update(current_search_item=f"Página {page+1}: {len(items)} publicaciones encontradas", page_items_found=len(items))
        publicaciones = []
        for idx, item in enumerate(items, 1):
            if should_stop():
                print(f"[scraper] Búsqueda detenida por el usuario en item {idx} de página {page + 1}")
                send_progress_update(final_message="Búsqueda detenida por el usuario")
                break
            try:
                link_tag = item.find_element(By.CSS_SELECTOR, 'h3.poly-component__title-wrapper > a.poly-component__title')
                link = link_tag.get_attribute('href')
                titulo = link_tag.text.strip()
                link_limpio = link.split('#')[0].split('?')[0]
                if not url_prohibida(link_limpio):
                    publicaciones.append({'idx': idx + page*48, 'titulo': titulo, 'url': link_limpio})
                else:
                    print(f"[scraper] Link prohibido por robots.txt: {link_limpio}")
            except Exception as e:
                print(f"[scraper] No se pudo obtener el link/título de la propiedad {idx}: {e}")

        all_publications.extend(publicaciones)

        total_publications_found = len(all_publications)
        estimated_time = total_publications_found * 20
        send_progress_update(total_found=total_publications_found, estimated_time=estimated_time)

        for pub in publicaciones:
            current_pub_index += 1
            send_progress_update(
                current_search_item=f"Búsqueda actual ({current_pub_index}/{total_publications_found}): {pub['titulo']}"
            )
            print(f"➡️  propiedad {pub['idx']}: {pub['titulo']} - {pub['url']}")
            cumple = False
            try:
                if url_prohibida(pub['url']):
                    print(f"[scraper] Saltando análisis de URL prohibida: {pub['url']}")
                    continue
                driver.get(pub['url'])
                time.sleep(2)
                try:
                    titulo_text = driver.find_element(By.CSS_SELECTOR, 'h1').text.lower()
                except Exception:
                    titulo_text = ''
                try:
                    desc_tag = driver.find_element(By.CSS_SELECTOR, 'p.ui-pdp-description__content[data-testid="content"]')
                    descripcion = desc_tag.text.lower()
                except Exception:
                    descripcion = ''
                caracteristicas_kv = []
                try:
                    claves = driver.find_elements(By.CSS_SELECTOR, 'div.andes-table__header__container')
                    valores = driver.find_elements(By.CSS_SELECTOR, 'span.andes-table__column--value')
                    for k, v in zip(claves, valores):
                        caracteristicas_kv.append(f"{k.text.strip().lower()}: {v.text.strip().lower()}")
                except Exception:
                    pass
                caracteristicas_sueltas = []
                try:
                    sueltas = driver.find_elements(By.CSS_SELECTOR, 'span.ui-pdp-color--BLACK.ui-pdp-size--XSMALL.ui-pdp-family--REGULAR')
                    for s in sueltas:
                        caracteristicas_sueltas.append(s.text.strip().lower())
                except Exception:
                    pass
                caracteristicas = ' '.join(caracteristicas_kv + caracteristicas_sueltas)

                def normalizar(texto):
                    return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()

                texto_total_norm = normalizar(f"{titulo_text} {descripcion} {caracteristicas}")
                keywords_norm = [normalizar(kw) for kw in keywords_con_variantes]
                encontrados = [kw for kw in keywords_con_variantes if normalizar(kw) in texto_total_norm]
                no_encontrados = [kw for kw in keywords_con_variantes if normalizar(kw) not in texto_total_norm]
                if not keywords_norm:
                    print("⚠️  No se especificaron palabras clave para filtrar.\n")
                    cumple = True
                elif all(kw in texto_total_norm for kw in keywords_norm):
                    print(f"✅ Cumple todos los requisitos. Palabras encontradas: {encontrados}\n")
                    cumple = True
                else:
                    print(f"❌ No se encontraron todas las palabras clave. Encontradas: {encontrados} | Faltantes: {no_encontrados}\n")
            except Exception as e:
                print(f"[scraper] Error al analizar publicación {pub['url']}: {e}")
            if cumple:
                links.append({'url': pub['url'], 'titulo': pub['titulo']})
                matched_publications_titles.append({'title': pub['titulo'], 'url': pub['url']})
                send_progress_update(matched_publications=matched_publications_titles)
        if len(items) < 48:
            print(f"Última página detectada (menos de 48 propiedades). Se detiene la búsqueda.")
            break
    driver.quit()
    print(f"[scraper] Resultados encontrados: {len(links)}")
    send_progress_update(final_message=f"¡Búsqueda finalizada! Se encontraron {len(links)} publicaciones coincidentes.")
    all_links_with_titles = [{'url': p['url'], 'titulo': p['titulo']} for p in all_publications]
    return {"matched": links, "all": all_links_with_titles}
