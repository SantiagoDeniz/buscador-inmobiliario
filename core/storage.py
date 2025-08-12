
import json
import os
from typing import Any, List, Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCHES_PATH = os.path.join(BASE_DIR, 'user_data', 'searches.json')
RESULTS_DIR = os.path.join(BASE_DIR, 'user_data', 'results')

def load_searches() -> List[Dict[str, Any]]:
	if not os.path.exists(SEARCHES_PATH):
		return []
	with open(SEARCHES_PATH, 'r', encoding='utf-8') as f:
		return json.load(f)

def save_searches(searches: List[Dict[str, Any]]):
	with open(SEARCHES_PATH, 'w', encoding='utf-8') as f:
		json.dump(searches, f, ensure_ascii=False, indent=2)

def load_results(search_id: str) -> List[Dict[str, Any]]:
	path = os.path.join(RESULTS_DIR, f'{search_id}.json')
	if not os.path.exists(path):
		return []
	with open(path, 'r', encoding='utf-8') as f:
		return json.load(f)

def save_results(search_id: str, results: List[Dict[str, Any]]):
	os.makedirs(RESULTS_DIR, exist_ok=True)
	path = os.path.join(RESULTS_DIR, f'{search_id}.json')
	with open(path, 'w', encoding='utf-8') as f:
		json.dump(results, f, ensure_ascii=False, indent=2)
