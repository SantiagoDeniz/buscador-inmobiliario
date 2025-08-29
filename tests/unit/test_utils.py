import unittest

from core.scraper.utils import stemming_basico, extraer_variantes_keywords


class TestUtils(unittest.TestCase):
    def test_stemming_basico(self):
        self.assertEqual(stemming_basico('hermoso'), 'herm')  # quita 'oso'
        self.assertEqual(stemming_basico('calidad'), 'cal')   # quita 'idad'
        self.assertEqual(stemming_basico('simple'), 'simple') # sin cambio

    def test_extraer_variantes_keywords_list(self):
        v = extraer_variantes_keywords(['terraza', 'garage', 'terraza'])
        self.assertEqual(v, ['terraza', 'garage'])

    def test_extraer_variantes_keywords_dict(self):
        entrada = [
            {'texto': 'piscina', 'sinonimos': ['pileta', 'swimming pool']},
            {'texto': 'terraza', 'sinonimos': []},
        ]
        v = extraer_variantes_keywords(entrada)
        self.assertEqual(v, ['piscina', 'pileta', 'swimming pool', 'terraza'])


if __name__ == '__main__':
    unittest.main()
