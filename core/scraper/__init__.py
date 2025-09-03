"""Fachada del paquete scraper con wrappers ligeros.

Evita importar módulos pesados (Django, Selenium) en import-time.
Cada función aquí es un wrapper que importa bajo demanda el destino real
cuando se invoca. Así, `from core.scraper import *` no rompe en entornos
sin Django configurado mientras no se llame a funciones pesadas.
"""

__all__ = [
	# url builder
	'build_mercadolibre_url', 'normalizar_para_url',
	# progress
	'send_progress_update', 'tomar_captura_debug',
	# browser
	'iniciar_driver', 'manejar_popups_cookies', 'verificar_necesita_login', 'cargar_cookies',
	# extractors
	'parse_rango', 'scrape_detalle_con_requests', 'recolectar_urls_de_pagina',
	# mercadolibre
	'extraer_total_resultados_mercadolibre', 'scrape_mercadolibre',
	# orchestration
	'run_scraper',
	# utils
	'stemming_basico', 'extraer_variantes_keywords',
]

# --- URL Builder ---
def build_mercadolibre_url(*args, **kwargs):
	from .url_builder import build_mercadolibre_url as _impl
	return _impl(*args, **kwargs)

def normalizar_para_url(*args, **kwargs):
	from .url_builder import normalizar_para_url as _impl
	return _impl(*args, **kwargs)

# --- Progreso / Debug ---
def send_progress_update(*args, **kwargs):
	from .progress import send_progress_update as _impl
	return _impl(*args, **kwargs)

def tomar_captura_debug(*args, **kwargs):
	from .progress import tomar_captura_debug as _impl
	return _impl(*args, **kwargs)

# --- Browser / Selenium ---
def iniciar_driver(*args, **kwargs):
	from .browser import iniciar_driver as _impl
	return _impl(*args, **kwargs)

def manejar_popups_cookies(*args, **kwargs):
	from .browser import manejar_popups_cookies as _impl
	return _impl(*args, **kwargs)

def verificar_necesita_login(*args, **kwargs):
	from .browser import verificar_necesita_login as _impl
	return _impl(*args, **kwargs)

def cargar_cookies(*args, **kwargs):
	from .browser import cargar_cookies as _impl
	return _impl(*args, **kwargs)

# --- Extractores ---
def parse_rango(*args, **kwargs):
	from .extractors import parse_rango as _impl
	return _impl(*args, **kwargs)

def scrape_detalle_con_requests(*args, **kwargs):
	from .extractors import scrape_detalle_con_requests as _impl
	return _impl(*args, **kwargs)

def recolectar_urls_de_pagina(*args, **kwargs):
	from .extractors import recolectar_urls_de_pagina as _impl
	return _impl(*args, **kwargs)

# --- MercadoLibre ---
def extraer_total_resultados_mercadolibre(*args, **kwargs):
	from .mercadolibre import extraer_total_resultados_mercadolibre as _impl
	return _impl(*args, **kwargs)

def scrape_mercadolibre(*args, **kwargs):
	from .mercadolibre import scrape_mercadolibre as _impl
	return _impl(*args, **kwargs)

# --- Orquestación ---
def run_scraper(*args, **kwargs):
	from .run import run_scraper as _impl
	return _impl(*args, **kwargs)

# --- Utils ---
def stemming_basico(*args, **kwargs):
	from .utils import stemming_basico as _impl
	return _impl(*args, **kwargs)

def extraer_variantes_keywords(*args, **kwargs):
	from .utils import extraer_variantes_keywords as _impl
	return _impl(*args, **kwargs)

# Fallback para cualquier acceso no envuelto explícitamente
def __getattr__(name):
	try:
		# Intentar resolver atributos de submódulos de forma perezosa
		import importlib
		mapping = {
			# url_builder
			'build_mercadolibre_url': ('core.scraper.url_builder', 'build_mercadolibre_url'),
			'normalizar_para_url': ('core.scraper.url_builder', 'normalizar_para_url'),
			# progress
			'send_progress_update': ('core.scraper.progress', 'send_progress_update'),
			'tomar_captura_debug': ('core.scraper.progress', 'tomar_captura_debug'),
			# browser
			'iniciar_driver': ('core.scraper.browser', 'iniciar_driver'),
			'manejar_popups_cookies': ('core.scraper.browser', 'manejar_popups_cookies'),
			'verificar_necesita_login': ('core.scraper.browser', 'verificar_necesita_login'),
			'cargar_cookies': ('core.scraper.browser', 'cargar_cookies'),
			# extractors
			'parse_rango': ('core.scraper.extractors', 'parse_rango'),
			'scrape_detalle_con_requests': ('core.scraper.extractors', 'scrape_detalle_con_requests'),
			'recolectar_urls_de_pagina': ('core.scraper.extractors', 'recolectar_urls_de_pagina'),
			# mercadolibre
			'extraer_total_resultados_mercadolibre': ('core.scraper.mercadolibre', 'extraer_total_resultados_mercadolibre'),
			'scrape_mercadolibre': ('core.scraper.mercadolibre', 'scrape_mercadolibre'),
			# orchestration
			'run_scraper': ('core.scraper.run', 'run_scraper'),
			# utils
			'stemming_basico': ('core.scraper.utils', 'stemming_basico'),
			'extraer_variantes_keywords': ('core.scraper.utils', 'extraer_variantes_keywords'),
		}
		if name in mapping:
			mod_name, attr = mapping[name]
			mod = importlib.import_module(mod_name)
			return getattr(mod, attr)
	except Exception:
		pass
	raise AttributeError(f"module 'core.scraper' has no attribute '{name}'")

