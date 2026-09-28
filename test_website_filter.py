import ast
import unittest
from pathlib import Path
from app.services.search.website_filter import WebsiteFilter, parse_whitelist


class WebsiteFilterTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_whitelist('https://EXAMPLE.com/path，example.com;\nsub.example.org'),
                         ('example.com', 'sub.example.org'))
        self.assertEqual(parse_whitelist('https://例子.中国'), ('xn--fsqu00a.xn--fiqs8s',))

    def test_boundaries(self):
        f = WebsiteFilter(True, ('example.com',))
        for url in ('https://example.com', 'https://a.example.com/path', 'https://EXAMPLE.COM.:443'):
            self.assertTrue(f.allows(url), url)
        for url in ('https://otherexample.com', 'https://example.com.evil.org',
                    'https://evil.org/?url=example.com', 'https://example.com@evil.org',
                    'javascript:example.com', 'https://[broken'):
            self.assertFalse(f.allows(url), url)

    def test_invalid_settings(self):
        for entry in ('*', '*.example.com', 'https://', 'bad_domain.com', 'https://example.com:abc'):
            with self.assertRaises(ValueError):
                parse_whitelist(entry)
        self.assertFalse(WebsiteFilter(True).allows('https://example.com'))
        self.assertTrue(WebsiteFilter().allows('https://anything.org'))

    def test_setting_roundtrip(self):
        import tempfile
        from app.core.database import Database
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / 'test.db')
            self.assertTrue(WebsiteFilter.from_database(db).allows('https://other.org'))
            db.set_setting('whitelist', 'example.com')
            db.set_setting('whitelist_enabled', '1')
            f = WebsiteFilter.from_database(Database(db.path))
            self.assertTrue(f.allows('https://sub.example.com'))
            self.assertFalse(f.allows('https://other.org'))
            import gc
            gc.collect()  # Existing Database context managers leave connections for GC.

    def test_syntax(self):
        for path in (Path(__file__).parent / 'app').rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))


if __name__ == '__main__':
    unittest.main()
