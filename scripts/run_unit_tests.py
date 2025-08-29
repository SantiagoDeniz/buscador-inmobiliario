import unittest, sys, os

if __name__ == '__main__':
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    print('Repo root:', repo_root)
    print('Sys.path[0:3]:', sys.path[:3])
    try:
        import core  # noqa: F401
        print('Import core: OK')
    except Exception as e:
        print('Import core FAILED:', e)
    suite = unittest.defaultTestLoader.discover('tests/unit', pattern='test_*.py')
    total = suite.countTestCases()
    print('Collected tests:', total)
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)
