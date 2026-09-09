"""Acceptance tests for the Saudi retail data batch 2.

Covers Nice One Beauty (4193), Fitaihi Holding (4180) and SACO (4008),
transcribed from their official FY2025 audited financial statements (the full
audited PDFs linked on the Saudi Exchange company-profile "Financial Statements"
tab). This batch adds no engine or catalog changes.
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


class RetailBatch2ManifestTests(unittest.TestCase):
    def test_nice_one_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("nice-one-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)

    def test_fitaihi_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("fitaihi-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)

    def test_saco_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("saco-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)


class RetailBatch2SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "rt2.sqlite3")
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

    def test_all_publish_without_errors(self):
        for cid in ("sa:4193", "sa:4180", "sa:4008"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_nice_one_rough_year_and_bridge(self):
        q = FinancialQueryService(self.dbpath)
        try:
            pre = _v(q.metric_history("SA", "4193", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "4193", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4193", "net_income"), "2025-12-31")
            ni_prev = _v(q.metric_history("SA", "4193", "net_income"), "2024-12-31")
            ta = _v(q.metric_history("SA", "4193", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4193", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4193", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("2980434"))
        self.assertLess(ni, ni_prev)
        self.assertEqual(ta, tl + te)

    def test_fitaihi_operating_loss_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            oi = _v(q.metric_history("SA", "4180", "operating_income"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4180", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "4180", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4180", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4180", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertLess(oi, 0)
        self.assertGreater(ni, 0)
        self.assertEqual(ni, Decimal("4045639"))
        self.assertEqual(ta, tl + te)

    def test_saco_recovery_and_bridge(self):
        q = FinancialQueryService(self.dbpath)
        try:
            pre = _v(q.metric_history("SA", "4008", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "4008", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4008", "net_income"), "2025-12-31")
            ni_prev = _v(q.metric_history("SA", "4008", "net_income"), "2024-12-31")
            ta = _v(q.metric_history("SA", "4008", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4008", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4008", "total_equity"), "2025-12-31")
            cash = _v(q.metric_history("SA", "4008", "cash"), "2025-12-31")
            cash_end = _v(q.metric_history("SA", "4008", "cash_end"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("45587606"))
        self.assertLess(ni_prev, 0)
        self.assertEqual(ta, tl + te)
        self.assertEqual(cash, cash_end)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
