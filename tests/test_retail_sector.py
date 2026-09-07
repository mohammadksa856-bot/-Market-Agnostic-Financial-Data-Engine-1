"""Acceptance tests for the Saudi retail data batch 1.

Covers Jarir Marketing Company (4190), transcribed by hand from Jarir's official
FY2025 audited consolidated financial statements (the full audited PDF linked on
the Saudi Exchange company-profile "Financial Statements" tab). This batch adds
no engine or catalog changes.
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


class JarirManifestTests(unittest.TestCase):
    def test_manifest_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("jarir-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 15)


class ExtraManifestTests(unittest.TestCase):
    def test_manifest_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("extra-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 18)


class JarirSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "retail.sqlite3")
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

    def test_jarir_publishes_without_errors(self):
        rows = [r for r in self.summary["results"] if r["company_id"] == "sa:4190"]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["status"], {"published", "duplicate"}, row)
            self.assertNotIn("error", row, row)

    def test_jarir_headline_figures_match_the_filing(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "4190", "revenue")
            net_income = q.metric_history("SA", "4190", "net_income")
            assets = q.metric_history("SA", "4190", "total_assets")
        finally:
            q.close()
        self.assertEqual(_value(revenue, "2025-12-31"), Decimal("11365153000"))
        self.assertEqual(_value(net_income, "2025-12-31"), Decimal("1049192000"))
        self.assertEqual(_value(assets, "2025-12-31"), Decimal("4416028000"))

    def test_jarir_balance_sheet_balances(self):
        q = FinancialQueryService(self.dbpath)
        try:
            assets = _value(q.metric_history("SA", "4190", "total_assets"), "2025-12-31")
            liabilities = _value(q.metric_history("SA", "4190", "total_liabilities"), "2025-12-31")
            equity = _value(q.metric_history("SA", "4190", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(assets, liabilities + equity)

    def test_jarir_pretax_bridge_reconciles(self):
        q = FinancialQueryService(self.dbpath)
        try:
            pretax = _value(q.metric_history("SA", "4190", "income_before_income_taxes_and_zakat"), "2025-12-31")
            tax = _value(q.metric_history("SA", "4190", "income_taxes_and_zakat"), "2025-12-31")
            net_income = _value(q.metric_history("SA", "4190", "net_income"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(pretax + tax, net_income)

    def test_jarir_is_debt_free_at_year_end(self):
        q = FinancialQueryService(self.dbpath)
        try:
            history = q.metric_history("SA", "4190", "current_debt")
        finally:
            q.close()
        # 2024 carried a SAR 39,696k current portion; 2025 reports none.
        self.assertEqual(_value(history, "2024-12-31"), Decimal("39696000"))
        self.assertIsNone(_value(history, "2025-12-31"))

    def test_jarir_margins_are_in_a_reasonable_range(self):
        q = FinancialQueryService(self.dbpath)
        try:
            net_margin = _value(q.metric_history("SA", "4190", "net_margin"), "2025-12-31")
        finally:
            q.close()
        self.assertIsNotNone(net_margin)
        self.assertTrue(Decimal("0.05") <= net_margin <= Decimal("0.15"), net_margin)

    def test_extra_publishes_without_errors(self):
        rows = [r for r in self.summary["results"] if r["company_id"] == "sa:4003"]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["status"], {"published", "duplicate"}, row)
            self.assertNotIn("error", row, row)

    def test_extra_headline_figures_match_the_filing(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = _value(q.metric_history("SA", "4003", "revenue"), "2025-12-31")
            net_income = _value(q.metric_history("SA", "4003", "net_income"), "2025-12-31")
            assets = _value(q.metric_history("SA", "4003", "total_assets"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(revenue, Decimal("7446115000"))
        self.assertEqual(net_income, Decimal("575989000"))
        self.assertEqual(assets, Decimal("5924092000"))

    def test_extra_profit_split_and_balance_sheet_reconcile(self):
        q = FinancialQueryService(self.dbpath)
        try:
            parent = _value(q.metric_history("SA", "4003", "net_income_parent"), "2025-12-31")
            nci = _value(q.metric_history("SA", "4003", "net_income_noncontrolling"), "2025-12-31")
            assets = _value(q.metric_history("SA", "4003", "total_assets"), "2025-12-31")
            liabilities = _value(q.metric_history("SA", "4003", "total_liabilities"), "2025-12-31")
            equity = _value(q.metric_history("SA", "4003", "total_equity"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(parent + nci, Decimal("575989000"))
        self.assertEqual(assets, liabilities + equity)


def _value(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
