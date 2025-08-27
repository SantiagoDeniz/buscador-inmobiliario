
import uuid
from typing import List, Dict, Any, Optional
from .storage import load_searches, save_searches

def get_all_searches() -> List[Dict[str, Any]]:
	return load_searches()

def get_search(search_id: str) -> Optional[Dict[str, Any]]:
	for s in load_searches():
		if s['id'] == search_id:
			return s
	return None


# --- Procesamiento de palabras clave ---
import unicodedata
import re

_SINONIMOS = {
	'apto': 'apartamento',
	'apto.': 'apartamento',
	'apartamentos': 'apartamento',
	'dorm': 'dormitorio',
	'dormitorios': 'dormitorio',
	'dorms': 'dormitorio',
	'ph': 'ph',
	'balcon': 'balcón',
	'garage': 'garaje',
	'habitacion': 'habitación',
	'habitaciones': 'habitación',
	'pozo': 'pozo',
	'gastos': 'gastos',
	'comunes': 'comunes',
	'bajos': 'bajos',
	'pet': 'pet',
	'friendly': 'friendly',
	'monoambiente': 'monoambiente',
	'lujo': 'lujo',
	'esquina': 'esquina',
	'jardin': 'jardín',
	'jardines': 'jardín',
	'chacra': 'chacra',
	'casa': 'casa',
	'casas': 'casa',
	'terreno': 'terreno',
	'terrenos': 'terreno',
	'oficina': 'oficina',
	'oficinas': 'oficina',
	'local': 'local',
	'locales': 'local',
	'galpon': 'galpón',
	'galpones': 'galpón',
	'duplex': 'dúplex',
	'duplexs': 'dúplex',
	'penthouse': 'penthouse',
	'amueblado': 'amueblado',
	'equipado': 'equipado',
	'colonial': 'colonial',
	'minimalista': 'minimalista',
	'industrial': 'industrial',
	'temporal': 'temporal',
	'vista': 'vista',
	'frente': 'frente',
	'nuevo': 'nuevo',
	'nueva': 'nuevo',
	'parrillero': 'parrillero',
	'balcón': 'balcón',
	'balcon': 'balcón',
	'pozo': 'pozo',
	'inversion': 'inversión',
	'inversión': 'inversión',
	'barato': 'barato',
	'barata': 'barato',
	'lujo': 'lujo',
	'equipado': 'equipado',
	'amueblado': 'amueblado',
	'compartida': 'compartida',
	'habitacion': 'habitación',
	'habitaciones': 'habitación',
	'ph': 'ph',
	'loft': 'loft',
	'chacra': 'chacra',
	'esquina': 'esquina',
	'parque': 'parque',
	'rambla': 'rambla',
	'sur': 'sur',
	'norte': 'norte',
	'este': 'este',
	'oeste': 'oeste',
	'centro': 'centro',
	'cordon': 'cordon',
	'cordón': 'cordon',
	'malvin': 'malvin',
	'pocitos': 'pocitos',
	'carrasco': 'carrasco',
	'buceo': 'buceo',
	'parque': 'parque',
	'batlle': 'batlle',
	'rodo': 'rodo',
	'rodó': 'rodo',
	'blanqueada': 'blanqueada',
	'tres': 'tres',
	'cruces': 'cruces',
	'sayago': 'sayago',
	'florida': 'florida',
	'canelones': 'canelones',
	'piriapolis': 'piriapolis',
	'piriápolis': 'piriapolis',
	'punta': 'punta',
	'gorda': 'gorda',
	'carretas': 'carretas',
	'vieja': 'vieja',
	'ciudad': 'ciudad',
	'barrio': 'barrio',
	'sur': 'sur',
	'mar': 'mar',
	'enero': 'enero',
	'pozo': 'pozo',
	'inversion': 'inversión',
	'inversión': 'inversión',
	'pet': 'pet',
	'friendly': 'friendly',
	'minimalista': 'minimalista',
	'colonial': 'colonial',
	'industrial': 'industrial',
	'temporal': 'temporal',
	'equipado': 'equipado',
	'amueblado': 'amueblado',
	'compartida': 'compartida',
	'habitacion': 'habitación',
	'habitaciones': 'habitación',
	'ph': 'ph',
	'loft': 'loft',
	'chacra': 'chacra',
	'esquina': 'esquina',
	'parque': 'parque',
	'rambla': 'rambla',
	'sur': 'sur',
	'norte': 'norte',
	'este': 'este',
	'oeste': 'oeste',
	'centro': 'centro',
	'cordon': 'cordon',
	'cordón': 'cordon',
	'malvin': 'malvin',
	'pocitos': 'pocitos',
	'carrasco': 'carrasco',
	'buceo': 'buceo',
	'parque': 'parque',
	'batlle': 'batlle',
	'rodo': 'rodo',
	'rodó': 'rodo',
	'blanqueada': 'blanqueada',
	'tres': 'tres',
	'cruces': 'cruces',
	'sayago': 'sayago',
	'florida': 'florida',
	'canelones': 'canelones',
	'piriapolis': 'piriapolis',
	'piriápolis': 'piriapolis',
	'punta': 'punta',
	'gorda': 'gorda',
	'carretas': 'carretas',
	'vieja': 'vieja',
	'ciudad': 'ciudad',
	'barrio': 'barrio',
	'sur': 'sur',
	'mar': 'mar',
	'enero': 'enero',
}

_STOPWORDS = set([
	'de', 'la', 'el', 'en', 'y', 'a', 'con', 'del', 'para', 'por', 'un', 'una', 'los', 'las', 'o', 'u', 'al', 'que', 'es', 'su', 'se', 'lo', 'como', 'más', 'menos', 'sin', 'sobre', 'entre', 'ya', 'pero', 'si', 'no', 'ni', 'también', 'muy', 'fue', 'son', 'ha', 'han', 'ser', 'esta', 'este', 'estas', 'estos', 'esa', 'ese', 'esas', 'esos', 'el', 'la', 'las', 'los', 'de', 'del', 'y', 'en', 'con', 'por', 'para', 'a', 'al', 'un', 'una', 'o', 'u', 'que', 'es', 'su', 'se', 'lo', 'como', 'más', 'menos', 'sin', 'sobre', 'entre', 'ya', 'pero', 'si', 'no', 'ni', 'también', 'muy', 'fue', 'son', 'ha', 'han', 'ser', 'esta', 'este', 'estas', 'estos', 'esa', 'ese', 'esas', 'esos'
])

def normalizar_token(token):
	token = token.lower()
	token = ''.join(c for c in unicodedata.normalize('NFD', token) if unicodedata.category(c) != 'Mn')
	token = re.sub(r'[^a-z0-9áéíóúüñ]+', '', token)
	return _SINONIMOS.get(token, token)

def procesar_keywords(texto: str) -> list:
	# Elimina comas y tokeniza solo por espacios
	texto = texto.replace(',', ' ')
	raw_tokens = texto.split()
	tokens = [normalizar_token(t) for t in raw_tokens if t]
	tokens = [t for t in tokens if t and t not in _STOPWORDS]
	# Devuelve todos los tokens por separado, sin asociaciones
	resultado = []
	seen = set()
	for t in tokens:
		if t not in seen:
			resultado.append(t)
			seen.add(t)
	return resultado

def create_search(data: Dict[str, Any]) -> Dict[str, Any]:
	import datetime
	print(f"[DEPURACIÓN] Creando nueva búsqueda con datos: {data}")
	searches = load_searches()
	raw_keywords = data.get('keywords', [])
	if isinstance(raw_keywords, list):
		raw_keywords = ' '.join(raw_keywords)
	keywords = procesar_keywords(raw_keywords)
	print(f"[DEPURACIÓN] Palabras clave procesadas: {keywords}")
	# Los resultados y links visitados se inicializan vacíos
	new_search = {
		'id': str(uuid.uuid4()),
		'nombre': data.get('name', ''),
		'busqueda': raw_keywords,
		'filtros': data.get('filters', {}),
		'resultados': [],  # títulos de publicaciones coincidentes
		'links_visitados': [],
		'ultima_revision': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		'enabled': data.get('enabled', True),
		'platforms': data.get('platforms', ['mercadolibre']),
	}
	print(f"[DEPURACIÓN] Nueva búsqueda creada: {new_search}")
	searches.append(new_search)
	save_searches(searches)
	print(f"[DEPURACIÓN] Búsqueda guardada. Total búsquedas: {len(searches)}")
	return new_search

def update_search(search_id: str, data: Dict[str, Any]) -> bool:
	searches = load_searches()
	for s in searches:
		if s['id'] == search_id:
			s.update(data)
			save_searches(searches)
			return True
	return False

def delete_search(search_id: str) -> bool:
	searches = load_searches()
	new_searches = [s for s in searches if s['id'] != search_id]
	if len(new_searches) != len(searches):
		save_searches(new_searches)
		return True
	return False
