"""Acceptance tests for the Saudi food & agriculture data batch 2.

Covers Savola Group (2050), SADAFCO (2270) and NADEC (6010), transcribed from
their official FY2025 audited consolidated financial statements (the full audited
PDFs linked on the Saudi Exchange company-profile "Financial Statements" tab).
This batch carries one flagged engine change: a verification.py ADDITIVE_IDENTITIES
entry for the IFRS 5 `net income = continuing + discontinued operations` bridge
(Savola and SADAFCO need it).
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


class FoodBatch2ManifestTests(unittest.TestCase):
    def test_savola_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("savola-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 15)

    def test_sadafco_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("sadafco-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 15)

    def test_nadec_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("nadec-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 16)

    def test_savola_and_sadafco_ifrs5_bridge_fires(self):
        for prefix, n in (("savola-", 2), ("sadafco-", 2)):
            report = ManifestVerifier(REPO_IMPORTS).verify(prefix)
            rows = [
                c for c in report["detail"]
                if c["check"] == "income_statement: net income = continuing + discontinued operations"
            ]
            self.assertEqual(len(rows), n, (prefix, report["detail"]))
            for row in rows:
                self.assertEqual(row["status"], "pass", row)


class FoodBatch2SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "food2.sqlite3")
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
        for cid in ("sa:2050", "sa:2270", "sa:6010"):
            rows = [r for r in self.summary["results"] if r["company_id"] == cid]
            self.assertTrue(rows, cid)
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)

    def test_savola_headline_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "2050", "revenue"), "2025-12-31")
            ni = _v(q.metric_history("SA", "2050", "net_income"), "2025-12-31")
            cont = _v(q.metric_history("SA", "2050", "continuing_operations_income"), "2025-12-31")
            disc = _v(q.metric_history("SA", "2050", "discontinued_operations_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "2050", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "2050", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "2050", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("26081053000"))
        self.assertEqual(ni, Decimal("940499000"))
        self.assertEqual(cont + disc, ni)
        self.assertEqual(ta, tl + te)

    def test_sadafco_no_nci_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            ni = _v(q.metric_history("SA", "2270", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "2270", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "2270", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "2270", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(ni, Decimal("477389000"))
        self.assertEqual(ta, tl + te)

    def test_nadec_standard_bridge_and_balance_sheet(self):
        q = FinancialQueryService(self.dbpath)
        try:
            rev = _v(q.metric_history("SA", "6010", "revenue"), "2025-12-31")
            pre = _v(q.metric_history("SA", "6010", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _v(q.metric_history("SA", "6010", "income_taxes_and_zakat"), "2025-12-31")
            ni = _v(q.metric_history("SA", "6010", "net_income"), "2025-12-31")
            ta = _v(q.metric_history("SA", "6010", "total_assets"), "2025-12-31")
            tl = _v(q.metric_history("SA", "6010", "total_liabilities"), "2025-12-31")
            te = _v(q.metric_history("SA", "6010", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(rev, Decimal("3526978695"))
        self.assertEqual(pre + tax, ni)
        self.assertEqual(ni, Decimal("393348637"))
        self.assertEqual(ta, tl + te)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
