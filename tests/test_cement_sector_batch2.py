"""Acceptance tests for the Saudi cement data batch 2.

Covers Arabian Cement (3010), Qassim Cement (3040) and Yanbu Cement (3060),
transcribed from their official FY2025 audited financial statements (the full
audited PDFs linked on the Saudi Exchange company-profile "Financial Statements"
tab). Arabian Cement discloses an IFRS 5 discontinued operation, so this batch
carries one flagged engine change (the continuing + discontinued additive
identity in verification.py).
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


class CementBatch2ManifestTests(unittest.TestCase):
    def test_arabian_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("arabian-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)

    def test_arabian_cement_ifrs5_bridge_fires(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("arabian-cement-")
        checks = {row["check"] for row in report["detail"] if row["status"] == "pass"}
        self.assertIn(
            "income_statement: net income = continuing + discontinued operations",
            checks,
        )

    def test_qassim_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("qassim-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)

    def test_yanbu_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("yanbu-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)


class CementBatch2SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "cm2.sqlite3")
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
        for cid in ("sa:3010", "sa:3040", "sa:3060"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_arabian_cement_discontinued_split_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            cont = _v(q.metric_history("SA", "3010", "continuing_operations_income"), "2025-12-31")
            disc = _v(q.metric_history("SA", "3010", "discontinued_operations_income"), "2025-12-31")
            ni = _v(q.metric_history("SA", "3010", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "3010", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3010", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3010", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(cont + disc, ni)
        self.assertEqual(ni, Decimal("167575000"))
        self.assertEqual(ta, tl + te)

    def test_qassim_cement_headline_and_bridge(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "3040", "revenue"), "2025-12-31")
            pre = _v(q.metric_history("SA", "3040", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "3040", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "3040", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "3040", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3040", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3040", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("1133302818"))
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("259932859"))
        self.assertEqual(ta, tl + te)

    def test_yanbu_cement_weaker_year_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            ni = _v(q.metric_history("SA", "3060", "net_income"), "2025-12-31")
            ni_prev = _v(q.metric_history("SA", "3060", "net_income"), "2024-12-31")
            ta = _v(q.metric_history("SA", "3060", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3060", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3060", "total_equity"), "2025-12-31")
            cash = _v(q.metric_history("SA", "3060", "cash"), "2025-12-31")
            cash_end = _v(q.metric_history("SA", "3060", "cash_end"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(ni, Decimal("104467957"))
        self.assertLess(ni, ni_prev)
        self.assertEqual(ta, tl + te)
        self.assertEqual(cash, cash_end)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
