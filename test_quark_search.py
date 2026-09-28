import ast
import gc
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.core.database import Database
from app.services.search.quark import QuarkSearchProvider, parse_iqs_results
from app.services.search.registry import search_provider_registry
from app.ui.main_window import MainWindow


class QuarkApiTests(unittest.TestCase):
    def test_parse_results(self):
        items = [
            {"title": "<em>作品</em>标题", "link": "https://example.com/a?utm_source=x",
             "snippet": "一段<em>摘要</em>"},
            {"title": "重复", "link": "https://example.com/a"},
            {"title": "非法", "link": "javascript:alert(1)"},
        ]
        self.assertEqual(parse_iqs_results(items), [{
            "title": "作品标题", "url": "https://example.com/a",
            "domain": "example.com", "snippet": "一段摘要",
        }])

    def test_credentials_required(self):
        with self.assertRaisesRegex(RuntimeError, "AccessKey"):
            QuarkSearchProvider().search("作品名")

    def test_sdk_request_and_response(self):
        provider = QuarkSearchProvider("id", "secret")
        response = Mock()
        response.body.page_items = [Mock(
            title="作品", link="https://example.com/book", snippet="摘要", summary=None
        )]
        with patch("alibabacloud_iqs20241111.client.Client.unified_search",
                   return_value=response) as call:
            results = provider.search("作品名")
        self.assertEqual(results[0]["url"], "https://example.com/book")
        request = call.call_args.args[0]
        self.assertEqual(request.body.query, "作品名")
        self.assertEqual(request.body.engine_type, "Generic")
        self.assertEqual(request.body.advanced_params["numResults"], "50")
        self.assertFalse(request.body.contents.main_text)

    def test_registry_uses_bound_iqs_service(self):
        db = Mock()
        db.list_search_sources.return_value = [{
            "name": "夸克", "api_service_id": 7, "enabled": 1,
        }]
        db.get_api_service.return_value = {
            "id": 7, "provider_type": "quark_iqs", "enabled": 1,
            "api_key": "id", "api_secret": "secret", "endpoint": "",
        }
        provider = search_provider_registry.get("夸克", db)
        self.assertIsInstance(provider, QuarkSearchProvider)
        self.assertEqual(provider.access_key_id, "id")
        self.assertEqual(provider.access_key_secret, "secret")

    def test_database_secret_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "test.db")
            service_id = db.add_api_service({
                "name": "Quark", "provider_type": "quark_iqs",
                "api_key": "id", "api_secret": "secret", "enabled": True,
            })
            self.assertEqual(db.get_api_service(service_id)["api_secret"], "secret")
            del db
            gc.collect()

    def test_ui_starts(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "test.db")
            window = MainWindow(db)
            self.assertIn("夸克", window.search.engine_checks)
            window.close()
            window.deleteLater()
            app.processEvents()
            del db
            gc.collect()

    def test_syntax(self):
        for path in (Path(__file__).parent / "app").rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


if __name__ == "__main__":
    unittest.main()
