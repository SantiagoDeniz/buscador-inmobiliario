import unittest

from core.scraper.extractors import parse_rango


class TestExtractors(unittest.TestCase):
    def test_parse_rango_monoambiente(self):
        self.assertEqual(parse_rango('Monoambiente'), (0, 0))

    def test_parse_rango_single_number(self):
        self.assertEqual(parse_rango('2 baños'), (2, 2))

    def test_parse_rango_range(self):
        self.assertEqual(parse_rango('1 a 3 dormitorios'), (1, 3))

    def test_parse_rango_none(self):
        self.assertEqual(parse_rango('sin datos'), (None, None))


if __name__ == '__main__':
    unittest.main()
