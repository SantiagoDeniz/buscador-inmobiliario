import unittest

from core.scraper.url_builder import build_mercadolibre_url, normalizar_para_url


class TestUrlBuilder(unittest.TestCase):
    def test_normalizar_para_url_basic(self):
        self.assertEqual(normalizar_para_url('Pocitos Nuevo'), 'pocitos-nuevo')
        self.assertEqual(normalizar_para_url('José  Artigas'), 'jose-artigas')
        self.assertEqual(normalizar_para_url(''), '')

    def test_build_url_basic_segments(self):
        filtros = {
            'tipo': 'Apartamento',
            'operacion': 'alquiler',
            'departamento': 'Montevideo',
            'ciudad': 'Pocitos',
        }
        url = build_mercadolibre_url(filtros)
        self.assertIn('/inmuebles/apartamentos/alquiler/montevideo/pocitos/', url)
        self.assertTrue(url.endswith('_NoIndex_True'))

    def test_montevideo_city_only(self):
        filtros = {
            'tipo': 'Casas',
            'operacion': 'Venta',
            'departamento': 'Canelones',
            'ciudad': 'Pocitos',  # debe ignorarse al no ser Montevideo
        }
        url = build_mercadolibre_url(filtros)
        self.assertIn('/inmuebles/casas/venta/canelones/', url)
        self.assertNotIn('pocitos', url)

    def test_dormitorios_in_path(self):
        url = build_mercadolibre_url({
            'tipo': 'Apartamento',
            'operacion': 'alquiler',
            'departamento': 'Montevideo',
            'dormitorios_min': 1,
            'dormitorios_max': 2,
        })
        self.assertIn('/1-a-2-dormitorios/', url)

    def test_price_range_in_filters_once(self):
        url = build_mercadolibre_url({
            'tipo': 'Apartamento',
            'operacion': 'alquiler',
            'departamento': 'Montevideo',
            'precio_min': 500,
            'precio_max': 1000,
            'moneda': 'USD'
        })
        self.assertIn('_PriceRange_500USD-1000USD', url)
        self.assertEqual(url.count('_NoIndex_True'), 1)


if __name__ == '__main__':
    unittest.main()
