import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService

try:
    from selenium_stealth import stealth
except Exception:
    def stealth(*args, **kwargs):
        pass

from .progress import tomar_captura_debug


def iniciar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-crash-reporter")
    chrome_options.add_argument("--disable-oopr-debug-crash-dump")
    chrome_options.add_argument("--no-crash-upload")
    chrome_options.add_argument("--disable-low-res-tiling")
    chrome_options.add_argument("--memory-pressure-off")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # Speed up page loads; content can be interacted with sooner
    chrome_options.page_load_strategy = 'eager'

    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        stealth(driver, languages=["es-ES", "es"], vendor="Google Inc.", platform="Win32",
                webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    except Exception:
        pass
    driver.set_page_load_timeout(30)
    print("✅ [CHROME] Driver iniciado correctamente")
    return driver


def manejar_popups_cookies(driver):
    popups_manejados = 0
    try:
        time.sleep(2)
        from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidSelectorException
        # Valid CSS selectors only
        selectores_popup_cookies = [
            "button[data-testid='action:understood-button']",
            "button[data-testid='cookies-policy-banner-accept']",
            ".cookie-consent-banner-opt-out__action button",
            "[data-testid='action:understood-button']",
            ".ui-cookie-consent__accept",
            ".cookie-banner button",
        ]
        # XPath fallbacks that search for common button texts
        xpaths_popup_cookies = [
            "//button[contains(., 'Entendido') or contains(., 'Aceptar') or contains(., 'Continuar') or contains(., 'Aceptar cookies')]",
            "//div[contains(@class,'cookie') or contains(@class,'consent')]//button[contains(., 'Aceptar') or contains(., 'Entendido')]",
        ]
        for selector in selectores_popup_cookies:
            try:
                elemento = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                elemento.click()
                popups_manejados += 1
                print(f"[scraper] Popup de cookies cerrado: {selector}")
                time.sleep(1)
                break
            except (TimeoutException, NoSuchElementException, InvalidSelectorException):
                continue
        if popups_manejados == 0:
            for xp in xpaths_popup_cookies:
                try:
                    elemento = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, xp))
                    )
                    elemento.click()
                    popups_manejados += 1
                    print(f"[scraper] Popup de cookies cerrado (XPath): {xp}")
                    time.sleep(1)
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
        try:
            location_popup = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='action:modal-dismissed']"))
            )
            location_popup.click()
            popups_manejados += 1
            print(f"[scraper] Popup de localización cerrado")
            time.sleep(1)
        except Exception:
            pass
    except Exception as e:
        print(f"[scraper] Error manejando popups: {e}")
    return popups_manejados > 0


def verificar_necesita_login(driver):
    try:
        from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidSelectorException
        # Valid CSS checks
        selectores_login = [
            ".nav-menu-item-link[href*='registration']",
            "[data-testid='action:login-button']",
            "a[href*='login']",
            ".login-button",
        ]
        for selector in selectores_login:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                if elemento.is_displayed():
                    print(f"[scraper] ⚠️ Detectado requerimiento de login: {selector}")
                    return True
            except (NoSuchElementException, TimeoutException, InvalidSelectorException):
                continue
        # XPath fallback using text contains
        try:
            xpath = "//button[contains(., 'Iniciar') or contains(., 'Ingresar') or contains(., 'Login')]"
            elemento = driver.find_element(By.XPATH, xpath)
            if elemento.is_displayed():
                print(f"[scraper] ⚠️ Detectado requerimiento de login por XPath")
                return True
        except (NoSuchElementException, TimeoutException):
            pass
        current_url = driver.current_url
        if any(path in current_url.lower() for path in ['login', 'registration', 'signin', 'signup']):
            print(f"[scraper] ⚠️ Detectado requerimiento de login por URL: {current_url}")
            return True
        title = driver.title.lower()
        if any(word in title for word in ['login', 'iniciar', 'registr', 'ingresar']):
            print(f"[scraper] ⚠️ Detectado requerimiento de login por título: {driver.title}")
            return True
        return False
    except Exception as e:
        print(f"[scraper] Error verificando necesidad de login: {e}")
        return False


def cargar_cookies(driver, cookies_path):
    cookies_data = None
    mercadolibre_cookies_env = os.environ.get('MERCADOLIBRE_COOKIES')
    if mercadolibre_cookies_env:
        try:
            cookies_data = json.loads(mercadolibre_cookies_env)
            print(f"[scraper] Cookies cargadas desde variable de entorno ({len(cookies_data)} cookies)")
        except json.JSONDecodeError as e:
            print(f"[scraper] Error decodificando cookies de variable de entorno: {e}")
    if not cookies_data:
        if not os.path.exists(cookies_path):
            print(f"[scraper] Archivo de cookies no encontrado: {cookies_path}")
            print(f"[scraper] Tip: Para producción, configura la variable MERCADOLIBRE_COOKIES")
            return False
        try:
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            print(f"[scraper] Cookies cargadas desde archivo local: {cookies_path} ({len(cookies_data)} cookies)")
        except Exception as e:
            print(f"[scraper] Error leyendo archivo de cookies: {e}")
            return False
    if not cookies_data:
        print(f"[scraper] No se pudieron cargar las cookies")
        return False
    print(f"[scraper] Navegando a MercadoLibre...")
    driver.get('https://www.mercadolibre.com.uy')
    time.sleep(3)
    print(f"[scraper] Manejando popups iniciales...")
    manejar_popups_cookies(driver)
    import time as time_module
    current_timestamp = time_module.time()
    cookies_validas = []
    for cookie in cookies_data:
        if 'expirationDate' in cookie:
            if cookie['expirationDate'] < current_timestamp:
                continue
        elif 'expiry' in cookie:
            if cookie['expiry'] < current_timestamp:
                continue
        cookies_validas.append(cookie)
    print(f"[scraper] {len(cookies_validas)}/{len(cookies_data)} cookies válidas (no expiradas)")
    cookies_agregadas = 0
    cookies_fallidas = 0
    for cookie in cookies_validas:
        try:
            cookie_selenium = cookie.copy()
            if 'expirationDate' in cookie_selenium:
                try:
                    cookie_selenium['expiry'] = int(cookie_selenium['expirationDate'])
                    del cookie_selenium['expirationDate']
                except Exception:
                    cookie_selenium.pop('expirationDate', None)
            elif 'expiry' in cookie_selenium:
                try:
                    cookie_selenium['expiry'] = int(cookie_selenium['expiry'])
                except Exception:
                    del cookie_selenium['expiry']
            for k in ['sameSite', 'storeId', 'id', 'priority']:
                cookie_selenium.pop(k, None)
            driver.add_cookie(cookie_selenium)
            cookies_agregadas += 1
        except Exception as e:
            cookies_fallidas += 1
            cookie_name = cookie.get('name', 'sin_nombre')
            if cookies_fallidas <= 3:
                print(f"[scraper] Error agregando cookie '{cookie_name}': {e}")
    print(f"[scraper] Cookies agregadas: {cookies_agregadas}, fallidas: {cookies_fallidas}")
    print(f"[scraper] Recargando página para aplicar cookies...")
    driver.refresh()
    time.sleep(3)
    manejar_popups_cookies(driver)
    necesita_login = verificar_necesita_login(driver)
    if necesita_login:
        print(f"[scraper] ⚠️ Las cookies no fueron suficientes, MercadoLibre sigue pidiendo login")
        return False
    else:
        print(f"[scraper] ✅ Cookies aplicadas correctamente, no se requiere login")
        return True
