import unittest

from core.scraper.utils import build_keyword_groups


class TestKeywordGroups(unittest.TestCase):
    def test_groups_from_dicts(self):
        entrada = [
            {'texto': 'piscina', 'sinonimos': ['pileta', 'swimming pool', 'pileta']},
            {'texto': 'terraza', 'sinonimos': []},
        ]
        grupos = build_keyword_groups(entrada)
        self.assertEqual(grupos, [['piscina', 'pileta', 'swimming pool'], ['terraza']])

    def test_groups_from_list(self):
        entrada = ['garage', 'balcon']
        grupos = build_keyword_groups(entrada)
        self.assertEqual(grupos, [['garage'], ['balcon']])


if __name__ == '__main__':
    unittest.main()
