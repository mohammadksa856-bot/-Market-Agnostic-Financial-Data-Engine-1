"""Acceptance tests for the Saudi health care data batch 2.

Covers Mouwasat Medical Services (4002), Dallah Healthcare (4004) and National
Medical Care / Care (4005), transcribed from their official FY2025 audited
consolidated financial statements (the full audited PDFs linked on the Saudi
Exchange company-profile "Financial Statements" tab). This batch adds no engine
or catalog changes.
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


class HealthcareBatch2ManifestTests(unittest.TestCase):
    def test_mouwasat_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("mouwasat-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)

    def test_dallah_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("dallah-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)

    def test_care_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("care-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 15)


class HealthcareBatch2SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "hc2.sqlite3")
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
        for cid in ("sa:4002", "sa:4004", "sa:4005"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_mouwasat_headline_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "4002", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4002", "net_income"), "2025-12-31")
            nip = _v(q.metric_history("SA", "4002", "net_income_parent"), "2025-12-31")
            nin = _v(q.metric_history("SA", "4002", "net_income_noncontrolling"), "2025-12-31")
            ta = _v(q.metric_history("SA", "4002", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4002", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4002", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("3222580029"))
        self.assertEqual(ni, Decimal("852038895"))
        self.assertEqual(nip + nin, ni)
        self.assertEqual(ta, tl + te)

    def test_dallah_headline_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "4004", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4004", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "4004", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4004", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4004", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("4066888893"))
        self.assertEqual(ni, Decimal("540536397"))
        self.assertEqual(ta, tl + te)

    def test_care_has_no_nci_and_balance_sheet_ties(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "4005", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4005", "net_income"), "2025-12-31")
            nin = _v(q.metric_history("SA", "4005", "net_income_noncontrolling"), "2025-12-31")
            ta = _v(q.metric_history("SA", "4005", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4005", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4005", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("1600361606"))
        self.assertEqual(ni, Decimal("318469575"))
        self.assertIsNone(nin)  # Care has no non-controlling interest
        self.assertEqual(ta, tl + te)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
