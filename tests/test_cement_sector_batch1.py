"""Acceptance tests for the Saudi cement data batch 1.

Covers Saudi Cement (3030), Southern Province Cement (3050) and Yamama Cement
(3020), transcribed from their official FY2025 audited financial statements (the
full audited PDFs linked on the Saudi Exchange company-profile "Financial
Statements" tab). This batch adds no engine or catalog changes.
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


class CementBatch1ManifestTests(unittest.TestCase):
    def test_saudi_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("saudi-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)

    def test_southern_province_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("southern-province-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 15)

    def test_yamama_cement_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("yamama-cement-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)


class CementBatch1SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "cm1.sqlite3")
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
        for cid in ("sa:3030", "sa:3050", "sa:3020"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_saudi_cement_balance_sheet_and_bridge(self):
        q = FinancialQueryService(self.dbpath)
        try:
            pre = _v(q.metric_history("SA", "3030", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "3030", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "3030", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "3030", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3030", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3030", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("363683000"))
        self.assertEqual(ta, tl + te)

    def test_southern_province_reports_a_2025_loss(self):
        q = FinancialQueryService(self.dbpath)
        try:
            ni = _v(q.metric_history("SA", "3050", "net_income"), "2025-12-31")
            ni_prev = _v(q.metric_history("SA", "3050", "net_income"), "2024-12-31")
            oi = _v(q.metric_history("SA", "3050", "operating_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "3050", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3050", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3050", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(ni, Decimal("-48512243"))
        self.assertGreater(ni_prev, 0)
        self.assertLess(oi, 0)
        self.assertEqual(ta, tl + te)

    def test_yamama_headline_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "3020", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "3020", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "3020", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "3020", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "3020", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("1423215257"))
        self.assertEqual(ni, Decimal("482877524"))
        self.assertEqual(ta, tl + te)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
