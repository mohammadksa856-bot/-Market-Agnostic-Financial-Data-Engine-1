"""Acceptance tests for the Saudi food & agriculture data batch 1.

Covers Almarai (2280), transcribed from Almarai's official FY2025 audited
consolidated financial statements. This batch adds no engine or catalog changes.
"""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.bootstrap import rebuild_snapshot
from finengine.query import FinancialQueryService
from finengine.verification import ManifestVerifier

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_IMPORTS = REPO_ROOT / "data" / "imports"


class AlmaraiManifestTests(unittest.TestCase):
    def test_manifest_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("almarai-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)


class AlmaraiSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "food.sqlite3")
        cls.summary = rebuild_snapshot(
            cls.dbpath,
            imports_dir=REPO_IMPORTS,
            registry_path=REPO_ROOT / "config" / "companies.json",
            raw_dir=REPO_ROOT / "data" / "raw",
            replace=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_almarai_publishes_without_errors(self):
        rows = [r for r in self.summary["results"] if r["company_id"] == "sa:2280"]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["status"], {"published", "duplicate"}, row)
            self.assertNotIn("error", row, row)

    def test_almarai_headline_figures_match_the_filing(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "2280", "revenue")
            net_income = q.metric_history("SA", "2280", "net_income")
            equity = q.metric_history("SA", "2280", "total_equity")
        finally:
            q.close()
        self.assertEqual(_value(revenue, "2025-12-31"), Decimal("22064876000"))
        self.assertEqual(_value(net_income, "2025-12-31"), Decimal("2456673000"))
        self.assertEqual(_value(equity, "2025-12-31"), Decimal("20527236000"))

    def test_almarai_profit_split_reconciles(self):
        q = FinancialQueryService(self.dbpath)
        try:
            parent = _value(q.metric_history("SA", "2280", "net_income_parent"), "2025-12-31")
            nci = _value(q.metric_history("SA", "2280", "net_income_noncontrolling"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(parent, Decimal("2456093000"))
        self.assertEqual(nci, Decimal("580000"))
        self.assertEqual(parent + nci, Decimal("2456673000"))

    def test_almarai_net_margin_is_reasonable(self):
        q = FinancialQueryService(self.dbpath)
        try:
            margin = _value(q.metric_history("SA", "2280", "net_margin"), "2025-12-31")
        finally:
            q.close()
        self.assertIsNotNone(margin)
        self.assertTrue(Decimal("0.07") <= margin <= Decimal("0.16"), margin)


def _value(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
