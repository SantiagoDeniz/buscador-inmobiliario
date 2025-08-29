"""Scraper package facade with lazy exports.

Avoids importing heavy modules (Django, Selenium) at import time.
Use attribute access to import on demand.
"""

from importlib import import_module

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

_EXPORTS = {
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


def __getattr__(name):
	if name in _EXPORTS:
		mod_name, attr = _EXPORTS[name]
		mod = import_module(mod_name)
		return getattr(mod, attr)
	raise AttributeError(f"module 'core.scraper' has no attribute '{name}'")

