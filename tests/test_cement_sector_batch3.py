"""Acceptance tests for the Saudi cement data batch 3.

Covers Najran Cement (3002), City Cement (3003) and Umm Al-Qura Cement (3005),
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


class CementBatch3ManifestTests(unittest.TestCase):
    def test_najran_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("najran-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)

    def test_city_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("city-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)

    def test_umm_al_qura_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("umm-al-qura-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)


class CementBatch3SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "cm3.sqlite3")
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
        for cid in ("sa:3002", "sa:3003", "sa:3005"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_najran_weaker_year_and_bridge(self):
        q = FinancialQueryService(self.dbpath)
        try:
            pre = _v(q.metric_history("SA", "3002", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "3002", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "3002", "net_income"), "2025-12-31")
            ni_prev = _v(q.metric_history("SA", "3002", "net_income"), "2024-12-31")
            ta = _v(q.metric_history("SA", "3002", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3002", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3002", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("36746000"))
        self.assertLess(ni, ni_prev)
        self.assertEqual(ta, tl + te)

    def test_city_cement_headline_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "3003", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "3003", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "3003", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3003", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3003", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("519638396"))
        self.assertEqual(ni, Decimal("128925087"))
        self.assertEqual(ta, tl + te)

    def test_umm_al_qura_standalone_headline_and_bridge(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "3005", "revenue"), "2025-12-31")
            pre = _v(q.metric_history("SA", "3005", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "3005", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "3005", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "3005", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3005", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3005", "total_equity"), "2025-12-31")
            cash = _v(q.metric_history("SA", "3005", "cash"), "2025-12-31")
            cash_end = _v(q.metric_history("SA", "3005", "cash_end"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("279057429"))
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("45775125"))
        self.assertEqual(ta, tl + te)
        self.assertEqual(cash, cash_end)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
