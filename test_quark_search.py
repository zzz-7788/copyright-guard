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
        with self.assertRaisesRegex(RuntimeError, "API Key"):
            QuarkSearchProvider().search("作品名")

    def test_legacy_endpoint_migrates_to_http_api(self):
        provider = QuarkSearchProvider("api-key", "iqs.cn-zhangjiakou.aliyuncs.com")
        self.assertEqual(provider.endpoint, "https://cloud-iqs.aliyuncs.com/search/unified")

    def test_http_request_and_response(self):
        provider = QuarkSearchProvider("api-key")
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"pageItems": [{
            "title": "作品", "link": "https://example.com/book", "snippet": "摘要"
        }]}
        with patch("app.services.search.quark.requests.post", return_value=response) as call:
            results = provider.search("作品名")
        self.assertEqual(results[0]["url"], "https://example.com/book")
        self.assertEqual(call.call_args.args[0], "https://cloud-iqs.aliyuncs.com/search/unified")
        self.assertEqual(call.call_args.kwargs["headers"]["Authorization"], "Bearer api-key")
        payload = call.call_args.kwargs["json"]
        self.assertEqual(payload["query"], "作品名")
        self.assertEqual(payload["engineType"], "GenericAdvanced")
        self.assertEqual(payload["advancedParams"]["numResults"], "50")
        self.assertFalse(payload["contents"]["mainText"])
        self.assertFalse(payload["contents"]["summary"])

    def test_registry_uses_bound_iqs_service(self):
        db = Mock()
        db.list_search_sources.return_value = [{
            "name": "夸克", "api_service_id": 7, "enabled": 1,
        }]
        db.get_api_service.return_value = {
            "id": 7, "provider_type": "quark_iqs", "enabled": 1,
            "api_key": "api-key", "api_secret": "", "endpoint": "",
        }
        provider = search_provider_registry.get("夸克", db)
        self.assertIsInstance(provider, QuarkSearchProvider)
        self.assertEqual(provider.api_key, "api-key")
        self.assertEqual(provider.endpoint, "https://cloud-iqs.aliyuncs.com/search/unified")

    def test_database_api_key_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "test.db")
            service_id = db.add_api_service({
                "name": "Quark", "provider_type": "quark_iqs",
                "api_key": "api-key", "api_secret": "", "enabled": True,
            })
            self.assertEqual(db.get_api_service(service_id)["api_key"], "api-key")
            del db
            gc.collect()

    def test_ui_starts(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "test.db")
            window = MainWindow(db)
            self.assertIn("夸克", window.search.engine_checks)
            self.assertFalse(hasattr(window.search, "quark_browser_btn"))
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
