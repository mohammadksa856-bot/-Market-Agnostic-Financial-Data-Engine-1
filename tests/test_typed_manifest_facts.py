import tempfile
import unittest
from pathlib import Path

from finengine.bootstrap import _publish_manifest_domains
from finengine.database import Database
from finengine.models import Company, Market, SourceDocument


class TypedManifestFactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.temp.name) / "typed.sqlite3"))
        self.company = Company("sa:TST", Market.SA, "TST", "Test Energy", "SAR", isin="SA0000000001",
                               exchange="Saudi Exchange", country="SA", sector="Energy",
                               industry="Integrated Oil & Gas", timezone="Asia/Riyadh")
        self.db.register_company(self.company)
        self.source = SourceDocument("sa:TST", Market.SA, "https://example.test/ar2025", "file:typed",
                                     "annual-report", "2026-03-09", b"{}")
        self.db.save_source(self.source, "typed", None)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def publish(self, **overrides):
        item = {"metric": "dividend_payment_frequency", "value": "quarterly", "value_type": "text",
                "period_start": "2025-01-01", "period_end": "2025-12-31", "period_kind": "fy",
                "fiscal_year": 2025, "page": 235, "table": "note 37 dividends"}
        item.update(overrides)
        payload = {"source_url": self.source.source_url, "filed_at": "2026-03-09", "typed_facts": [item]}
        return _publish_manifest_domains(self.db, self.company, payload, self.source.source_key)

    def stored(self):
        return self.db.conn.execute(
            """SELECT value_text,value_type,period_kind,period_start,source_key FROM data_points
            WHERE company_id='sa:TST' AND metric_key='dividend_payment_frequency' AND is_current=1""").fetchall()

    def test_a_reviewed_text_value_is_published_with_its_source(self):
        self.assertEqual(self.publish()["typed_facts"]["inserted"], 1)
        self.assertEqual([tuple(row) for row in self.stored()],
                         [("quarterly", "text", "fy", "2025-01-01", "file:typed")])
        self.assertEqual(self.publish()["typed_facts"]["duplicate"], 1)

    def test_numbers_and_catalog_type_mismatches_are_refused(self):
        with self.assertRaises(ValueError):
            self.publish(value=4)
        with self.assertRaises(ValueError):
            self.publish(metric="dividend_installments_count", value="4")  # decimal field: numeric pipeline only
        with self.assertRaises(ValueError):
            self.publish(value_type="boolean", value=True)
        self.assertEqual(self.stored(), [])

    def test_provenance_and_period_are_required(self):
        with self.assertRaises(ValueError):
            self.publish(page=None)
        with self.assertRaises(ValueError):
            self.publish(period_start=None)
        with self.assertRaises(ValueError):
            self.publish(value="  ")
        self.assertEqual(self.stored(), [])


if __name__ == "__main__":
    unittest.main()
