"""Acceptance tests for the Saudi materials / petrochemicals data batch 2.

Covers SABIC Agri-Nutrients (2020) and SIPCHEM (2310), transcribed from their
official FY2025 audited consolidated financial statements (the full audited PDFs
linked on the Saudi Exchange company-profile "Financial Statements" tab). This
batch also carries one flagged engine change to bootstrap._manifest_company.
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


class MaterialsBatch2ManifestTests(unittest.TestCase):
    def test_sabic_agri_nutrients_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("sabic-agri-nutrients-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)

    def test_sipchem_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("sipchem-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)

    def test_saudi_kayan_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("saudi-kayan-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 14)


class MaterialsBatch2SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "materials2.sqlite3")
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

    def test_both_publish_without_errors(self):
        for cid in ("sa:2020", "sa:2310"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_aramco_historical_manifest_still_resolves(self):
        # bootstrap._manifest_company must still pick Aramco for
        # "aramco-2020-fy-historical.json" now that an issuer with ticker 2020
        # (SABIC Agri-Nutrients) is in the registry.
        rows = [r for r in self.summary["results"] if r["company_id"] == "sa:2222"]
        self.assertTrue(rows)

    def test_sabic_agri_nutrients_headline_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "2020", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "2020", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "2020", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "2020", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "2020", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("13076878000"))
        self.assertEqual(ni, Decimal("4467933000"))
        self.assertEqual(ta, tl + te)

    def test_sipchem_reports_a_2025_loss(self):
        q = FinancialQueryService(self.dbpath)
        try:
            ni = _v(q.metric_history("SA", "2310", "net_income"), "2025-12-31")
            ni_prev = _v(q.metric_history("SA", "2310", "net_income"), "2024-12-31")
        finally:
            q.close()
        self.assertEqual(ni, Decimal("-772434000"))
        self.assertGreater(ni_prev, 0)

    def test_saudi_kayan_loss_and_balance_sheet(self):
        rows = [r for r in self.summary["results"] if r["company_id"] == "sa:2350"]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["status"], {"published", "duplicate"}, row)
        q = FinancialQueryService(self.dbpath)
        try:
            ni = _v(q.metric_history("SA", "2350", "net_income"), "2025-12-31")
            gp = _v(q.metric_history("SA", "2350", "gross_profit"), "2025-12-31")
            ta = _v(q.metric_history("SA", "2350", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "2350", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "2350", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(ni, Decimal("-2293883000"))
        self.assertLess(gp, 0)  # gross LOSS - cost of sales exceeded revenue
        self.assertEqual(ta, tl + te)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
