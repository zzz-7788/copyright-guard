import gc
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.core.database import Database
from app.ui.main_window import MainWindow


class SearchRolloverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")
        self.work = self.db.list_works()[0]

    def tearDown(self):
        del self.db
        gc.collect()
        self.tmp.cleanup()

    def add_result(self, suffix):
        return self.db.add_result({
            "work_id": self.work["id"],
            "title": suffix,
            "url": f"https://example.com/{suffix}",
            "domain": "example.com",
            "sources": ["夸克"],
        })

    def test_only_unpooled_results_are_ignored(self):
        unpooled = self.add_result("unpooled")
        pooled = self.add_result("pooled")
        already_ignored = self.add_result("ignored")
        self.db.add_result_to_report_pool(pooled)
        self.db.update_result_status(already_ignored, "ignored")

        self.assertEqual(self.db.ignore_unpooled_results(self.work["id"]), 1)
        rows = {row["id"]: row for row in self.db.list_results(self.work["id"])}
        self.assertEqual(rows[unpooled]["status"], "ignored")
        self.assertEqual(rows[pooled]["status"], "confirmed")
        self.assertEqual(rows[already_ignored]["status"], "ignored")

    def test_other_work_is_untouched(self):
        current = self.add_result("current")
        other_work = self.db.save_work({"title": "另一个作品"})
        other = self.db.add_result({
            "work_id": other_work,
            "title": "other",
            "url": "https://other.example/page",
            "domain": "other.example",
            "sources": ["夸克"],
        })
        self.db.ignore_unpooled_results(self.work["id"])
        rows = {row["id"]: row for row in self.db.list_results()}
        self.assertEqual(rows[current]["status"], "ignored")
        self.assertEqual(rows[other]["status"], "potential")

    def test_rediscovered_ignored_result_stays_ignored(self):
        result_id = self.add_result("rediscovered")
        self.db.update_result_status(result_id, "ignored")

        existing = self.db.get_result_by_url(
            self.work["id"],
            "https://example.com/rediscovered",
        )
        returned_id = self.db.add_result({
            "work_id": self.work["id"],
            "title": "rediscovered",
            "url": "https://example.com/rediscovered",
            "domain": "example.com",
            "sources": ["夸克"],
        })

        rows = {row["id"]: row for row in self.db.list_results(self.work["id"])}
        self.assertIsNotNone(existing)
        self.assertEqual(existing["status"], "ignored")
        self.assertEqual(returned_id, result_id)
        self.assertEqual(rows[result_id]["status"], "ignored")

    def test_search_page_defaults_to_potential(self):
        window = MainWindow(self.db)
        self.assertEqual(window.search.status_filter.currentData(), "potential")
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_report_pool_status_updates_search_result(self):
        result_id = self.add_result("reported")
        pool_id = self.db.add_result_to_report_pool(result_id)
        rows = {row["id"]: row for row in self.db.list_results(self.work["id"])}
        self.assertEqual(rows[result_id]["status"], "confirmed")

        self.db.update_report_pool_status(pool_id, "submitted")
        rows = {row["id"]: row for row in self.db.list_results(self.work["id"])}
        self.assertEqual(rows[result_id]["status"], "reported")


if __name__ == "__main__":
    unittest.main()
