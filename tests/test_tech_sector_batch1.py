"""Acceptance tests for the Saudi technology data batch 1.

Covers Elm Company (7203) and Arabian Internet and Communication Services
Company / Solutions by stc (7202), transcribed from their official FY2025
audited financial statements (the full audited PDFs linked on the Saudi Exchange
company-profile "Financial Statements" tab). This batch adds no engine or
catalog changes.
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


class TechBatch1ManifestTests(unittest.TestCase):
    def test_elm_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("elm-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)

    def test_stc_solutions_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("stc-solutions-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)


class TechBatch1SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "tech1.sqlite3")
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
        for cid in ("sa:7203", "sa:7202"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_elm_headline_bridge_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "7203", "revenue"), "2025-12-31")
            pre = _v(q.metric_history("SA", "7203", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "7203", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "7203", "net_income"), "2025-12-31")
            owners = _v(q.metric_history("SA", "7203", "net_income_parent"), "2025-12-31")
            nci = _v(q.metric_history("SA", "7203", "net_income_noncontrolling"), "2025-12-31")
            ta = _v(q.metric_history("SA", "7203", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "7203", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "7203", "total_equity"), "2025-12-31")
            cash = _v(q.metric_history("SA", "7203", "cash"), "2025-12-31")
            cash_end = _v(q.metric_history("SA", "7203", "cash_end"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("9464884988"))
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("2090324893"))
        self.assertEqual(owners + nci, ni)
        self.assertEqual(ta, tl + te)
        self.assertEqual(cash, cash_end)

    def test_stc_solutions_headline_bridge_and_negative_operating_cash_flow(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "7202", "revenue"), "2025-12-31")
            pre = _v(q.metric_history("SA", "7202", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "7202", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "7202", "net_income"), "2025-12-31")
            ocf = _v(q.metric_history("SA", "7202", "operating_cash_flow"), "2025-12-31")
            ocf_prev = _v(q.metric_history("SA", "7202", "operating_cash_flow"), "2024-12-31")
            ta = _v(q.metric_history("SA", "7202", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "7202", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "7202", "total_equity"), "2025-12-31")
            cash = _v(q.metric_history("SA", "7202", "cash"), "2025-12-31")
            cash_end = _v(q.metric_history("SA", "7202", "cash_end"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("12730189000"))
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("1512414000"))
        self.assertLess(ocf, 0)
        self.assertGreater(ocf_prev, 0)
        self.assertEqual(ta, tl + te)
        self.assertEqual(cash, cash_end)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
