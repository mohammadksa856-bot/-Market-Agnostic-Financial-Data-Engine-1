"""Acceptance tests for the Saudi health care data batch 1.

Covers Dr. Sulaiman Al Habib Medical Services Group / HMG (4013), transcribed
from HMG's official FY2025 audited consolidated financial statements. This batch
adds no engine or catalog changes.
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


class HmgManifestTests(unittest.TestCase):
    def test_manifest_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("hmg-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)


class HmgSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "hc.sqlite3")
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

    def test_hmg_publishes_without_errors(self):
        rows = [r for r in self.summary["results"] if r["company_id"] == "sa:4013"]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["status"], {"published", "duplicate"}, row)
            self.assertNotIn("error", row, row)

    def test_hmg_headline_figures_match_the_filing(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "4013", "revenue")
            net_income = q.metric_history("SA", "4013", "net_income")
            assets = q.metric_history("SA", "4013", "total_assets")
        finally:
            q.close()
        self.assertEqual(_value(revenue, "2025-12-31"), Decimal("13706897641"))
        self.assertEqual(_value(net_income, "2025-12-31"), Decimal("2491659541"))
        self.assertEqual(_value(assets, "2025-12-31"), Decimal("23204946364"))

    def test_hmg_profit_split_reconciles(self):
        q = FinancialQueryService(self.dbpath)
        try:
            parent = _value(q.metric_history("SA", "4013", "net_income_parent"), "2025-12-31")
            nci = _value(q.metric_history("SA", "4013", "net_income_noncontrolling"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(parent + nci, Decimal("2491659541"))

    def test_hmg_return_on_equity_is_reasonable(self):
        q = FinancialQueryService(self.dbpath)
        try:
            roe = _value(q.metric_history("SA", "4013", "return_on_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertIsNotNone(roe)
        self.assertTrue(Decimal("0.15") <= roe <= Decimal("0.45"), roe)


def _value(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
