"""Acceptance tests for the Saudi real estate data batch 1.

Covers Dar Al Arkan Real Estate Development (4300) and Emaar The Economic City
(4220), transcribed from their official FY2025 audited consolidated financial
statements (the full audited PDFs linked on the Saudi Exchange company-profile
"Financial Statements" tab). This batch carries one flagged engine change: a
verification.py ADDITIVE_IDENTITIES entry for the IFRS 5
`net income = continuing + discontinued operations` bridge (Dar Al Arkan FY2024).
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


class RealEstateBatch1ManifestTests(unittest.TestCase):
    def test_dar_al_arkan_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("dar-al-arkan-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)

    def test_emaar_ec_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("emaar-ec-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 14)

    def test_dar_al_arkan_ifrs5_bridge_fires_for_fy2024(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("dar-al-arkan-")
        rows = [
            c for c in report["detail"]
            if c["check"] == "income_statement: net income = continuing + discontinued operations"
        ]
        self.assertEqual(len(rows), 1, report["detail"])
        self.assertEqual(rows[0]["status"], "pass", rows[0])
        self.assertEqual(rows[0]["period"], "2024-12-31 fy")


class RealEstateBatch1SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "re1.sqlite3")
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
        for cid in ("sa:4300", "sa:4220"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_dar_al_arkan_headline_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "4300", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "4300", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "4300", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4300", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4300", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("3899802000"))
        self.assertEqual(ni, Decimal("1133920000"))
        self.assertEqual(ta, tl + te)

    def test_emaar_ec_near_breakeven_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            ni = _v(q.metric_history("SA", "4220", "net_income"), "2025-12-31")
            ni_prev = _v(q.metric_history("SA", "4220", "net_income"), "2024-12-31")
            nin = _v(q.metric_history("SA", "4220", "net_income_noncontrolling"), "2025-12-31")
            ta = _v(q.metric_history("SA", "4220", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "4220", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "4220", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(ni, Decimal("-8898000"))
        self.assertEqual(ni_prev, Decimal("-1134565000"))
        self.assertIsNone(nin)  # Emaar EC has no non-controlling interest
        self.assertEqual(ta, tl + te)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
