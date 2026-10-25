import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.domains import CompanyDomainStore
from finengine.factory_contract import _deterministic_gates
from finengine.models import Company, Market, SourceDocument


class OwnershipGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.temp.name) / "own.sqlite3"))
        self.db.register_company(Company("sa:TST", Market.SA, "TST", "Test", "SAR", country="SA"))
        source = SourceDocument("sa:TST", Market.SA, "https://example.test/ar", "source:ar", "annual", "2026-03-01", b"{}")
        self.db.save_source(source, "domain", None)
        self.store = CompanyDomainStore(self.db)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def holder(self, key, kind, pct, holder_type="public"):
        self.store.publish_ownership_position("sa:TST", key, key, kind, "2025-12-31", "source:ar",
                                              ownership_pct=pct, holder_type=holder_type)

    def gate(self):
        return _deterministic_gates(self.db, "sa:TST", "ownership", {}, category_not_applicable=False,
                                    freshness_audit={})[0]

    def test_class_total_inside_the_free_float_is_not_added_to_the_holders(self):
        self.holder("strategic", "direct", "0.70", "corporate_strategic")
        self.holder("float", "free_float", "0.30")
        self.holder("foreign", "aggregate", "0.0621", "foreign")
        result = self.gate()
        self.assertEqual(result["status"], "passed")
        self.assertAlmostEqual(float(result["ownership_percentage_sum"]), 1.0)

    def test_holders_above_one_hundred_percent_still_fail(self):
        self.holder("strategic", "direct", "0.70", "corporate_strategic")
        self.holder("float", "free_float", "0.35")
        self.assertEqual(self.gate()["status"], "failed")


if __name__ == "__main__":
    unittest.main()
