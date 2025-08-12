from django.test import TestCase, Client
from .search_manager import get_all_searches, create_search
from .scraper import build_mercadolibre_url

class FiltrosBusquedaTest(TestCase):
	def setUp(self):
		self.client = Client()

	def test_formulario_filtros(self):
		# Simulación: Montevideo, ciudad Pocitos, Venta, Apartamento
		data = {
			'name': 'Test Montevideo',
			'departamento': 'Montevideo',
			'ciudad': 'Pocitos',
			'operacion': 'Venta',
			'tipo': 'Apartamento',
			'keywords': 'terraza,garaje',
		}
		response = self.client.post('/nueva/', data)
		self.assertEqual(response.status_code, 302)
		busquedas = get_all_searches()
		self.assertTrue(any(b['filters']['departamento'] == 'Montevideo' and b['filters']['ciudad'] == 'Pocitos' for b in busquedas))

	def test_url_mercadolibre(self):
		# Simulación: Maldonado, sin ciudad, Alquiler, Casas
		filtros = {
			'departamento': 'Maldonado',
			'ciudad': '',
			'operacion': 'Alquiler',
			'tipo': 'Casas',
		}
		url = build_mercadolibre_url(filtros)
		self.assertIn('maldonado/', url)
		self.assertIn('alquiler/', url)
		self.assertIn('casas/', url)
		self.assertNotIn('pocitos', url)

	def test_ciudad_solo_montevideo(self):
		# Simulación: Canelones, ciudad debería ser ignorada
		filtros = {
			'departamento': 'Canelones',
			'ciudad': 'Pocitos',
			'operacion': 'Venta',
			'tipo': 'Casas',
		}
		url = build_mercadolibre_url(filtros)
		self.assertIn('canelones/', url)
		self.assertNotIn('pocitos', url)
from django.test import TestCase

# Create your tests here.
