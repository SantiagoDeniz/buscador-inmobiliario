
import threading
import time
from datetime import datetime
from .search_manager import get_all_searches
from .scraper import scrape_mercadolibre
from .storage import save_results, load_results

def run_periodic_searches():
	while True:
		now = datetime.now()
		# Ejecutar solo a las 8:00 y 14:00
		if now.hour in (8, 14) and now.minute == 0:
			searches = get_all_searches()
			for search in searches:
				if not search.get('enabled', True):
					continue
				if 'mercadolibre' in search.get('platforms', []):
					results = scrape_mercadolibre(search.get('filters', {}), search.get('keywords', []))
					prev_results = load_results(search['id'])
					# Solo guardar si hay nuevos links
					new_links = [r for r in results if r not in prev_results]
					if new_links:
						save_results(search['id'], results)
						# Aquí se podría notificar al usuario
			# Esperar 61 segundos para evitar doble ejecución
			time.sleep(61)
		else:
			# Revisar cada minuto
			time.sleep(60)

def start_scheduler():
	t = threading.Thread(target=run_periodic_searches, daemon=True)
	t.start()
