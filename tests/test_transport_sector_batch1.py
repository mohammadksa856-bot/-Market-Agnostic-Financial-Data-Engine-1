"""Acceptance tests for the Saudi transport & logistics data batch 1.

Covers Bahri / The National Shipping Company (4030) and SAL Saudi Logistics
Services (4263), transcribed from their official FY2025 audited consolidated
financial statements (the full audited PDFs linked on the Saudi Exchange
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


class TransportBatch1ManifestTests(unittest.TestCase):
    def test_bahri_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("bahri-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)

    def test_sal_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("sal-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)


class TransportBatch1SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "tr1.sqlite3")
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
        for cid in ("sa:4030", "sa:4263"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_bahri_headline_and_profit_split(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "4030", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4030", "net_income"), "2025-12-31")
            nip = _v(q.metric_history("SA", "4030", "net_income_parent"), "2025-12-31")
            nin = _v(q.metric_history("SA", "4030", "net_income_noncontrolling"), "2025-12-31")
            ta = _v(q.metric_history("SA", "4030", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4030", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4030", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("10346721000"))
        self.assertEqual(ni, Decimal("2559469000"))
        self.assertEqual(nip + nin, ni)
        self.assertEqual(ta, tl + te)

    def test_sal_headline_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "4263", "revenue"), "2025-12-31")
            pre = _v(q.metric_history("SA", "4263", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "4263", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4263", "net_income"), "2025-12-31")
            nin = _v(q.metric_history("SA", "4263", "net_income_noncontrolling"), "2025-12-31")
            ta = _v(q.metric_history("SA", "4263", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4263", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4263", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("1708430000"))
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("697890000"))
        self.assertIsNone(nin)  # SAL has no non-controlling interest
        self.assertEqual(ta, tl + te)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
