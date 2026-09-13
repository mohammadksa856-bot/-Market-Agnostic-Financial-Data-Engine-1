import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.models import Company, Market, SourceDocument
from finengine.query import FinancialQueryService
from finengine.understanding import refresh_all_understanding, refresh_company_understanding


class UnderstandingModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "understanding.sqlite3")
        self.db = Database(self.path)
        self.db.register_company(Company(
            "sa:TST", Market.SA, "TST", "Test Company", "SAR",
            isin="SA0000000001", exchange="Saudi Exchange", country="SA",
            sector="Materials", industry="Chemicals", timezone="Asia/Riyadh",
        ))
        self.db.save_source(SourceDocument(
            "sa:TST", Market.SA, "https://example.test/annual.pdf", "src:annual",
            "annual-report", "2026-03-01", b"annual report",
            "application/pdf", {"source_authority": "issuer_ir"},
        ), "annual", None)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_18_categories_and_governed_sources_are_seeded(self):
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM knowledge_categories").fetchone()[0], 18)
        self.assertEqual(self.db.conn.execute(
            "SELECT sum(weight) FROM knowledge_categories").fetchone()[0], 100)
        classes = {r[0] for r in self.db.conn.execute(
            "SELECT DISTINCT source_class FROM source_authorities")}
        self.assertEqual(classes, {"P", "C", "O", "S"})
        self.assertGreater(self.db.conn.execute(
            "SELECT count(*) FROM category_source_rules").fetchone()[0], 18)

    def test_refresh_is_honest_about_missing_data_and_queryable(self):
        result = refresh_company_understanding(self.db.conn, "sa:TST")
        self.assertEqual(len(result["categories"]), 18)
        self.assertEqual(result["readiness_state"], "not_ready")
        self.assertIn("five_annual_periods", result["blocking_reasons"])
        self.db.close()
        query = FinancialQueryService(self.path)
        try:
            payload = query.understanding("SA", "TST")
            self.assertEqual(len(payload["categories"]), 18)
            self.assertFalse(payload["hard_gates"]["five_annual_periods"]["passed"])
            governance = query.source_governance()
            self.assertEqual(len(governance["sources"]), 9)
        finally:
            query.close()
        self.db = Database(self.path)

    def test_refresh_all_reports_market_states(self):
        result = refresh_all_understanding(self.db.conn, "SA")
        self.assertEqual(result["companies"], 1)
        self.assertEqual(result["states"], {"not_ready": 1})


if __name__ == "__main__":
    unittest.main()
