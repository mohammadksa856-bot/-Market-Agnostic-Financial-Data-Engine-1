"""Acceptance tests for the Saudi materials / petrochemicals data batch 1.

Covers YANSAB (2290) and Advanced Petrochemical (2330), transcribed from the
issuers' official FY2025 audited financial statements. This batch adds no engine
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


class MaterialsManifestVerificationTests(unittest.TestCase):
    def test_manifests_have_no_identity_failures(self):
        for prefix in ("yansab-", "advanced-petrochemical-"):
            report = ManifestVerifier(REPO_IMPORTS).verify(prefix)
            self.assertEqual(report["failures"], 0, (prefix, report["detail"]))
            self.assertEqual(report["unmapped_labels"], [], prefix)
            self.assertGreater(report["passed"], 15, prefix)

    def test_advanced_petrochemical_fy2024_loss_still_closes_the_bridges(self):
        # FY2024 was a loss year; net income = pre-tax - tax and
        # net income = owners + NCI must still hold.
        report = ManifestVerifier(REPO_IMPORTS).verify("advanced-petrochemical-")
        bridges = [c for c in report["detail"]
                   if c["check"].startswith("income_statement:")
                   and c["period"].startswith("2024")]
        self.assertTrue(bridges, report["detail"])
        self.assertTrue(all(c["status"] == "pass" for c in bridges), bridges)


class MaterialsSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "materials.sqlite3")
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

    def _rows(self, company_id):
        return [r for r in self.summary["results"] if r["company_id"] == company_id]

    def test_both_publish_without_errors(self):
        for company_id in ("sa:2290", "sa:2330"):
            rows = self._rows(company_id)
            self.assertTrue(rows, f"no manifest published for {company_id}")
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)
                self.assertNotIn("error", row, row)

    def test_headline_figures_match_the_filings(self):
        expected = {
            "2290": {"revenue": "5601167000", "net_income": "79098000",
                     "total_assets": "13259624000"},
            "2330": {"revenue": "3501939000", "net_income": "231918000",
                     "total_assets": "14356479000"},
        }
        q = FinancialQueryService(self.dbpath)
        try:
            for symbol, metrics in expected.items():
                for metric, value in metrics.items():
                    hist = q.metric_history("SA", symbol, metric)
                    self.assertEqual(_value(hist, "2025-12-31"), Decimal(value),
                                     f"{symbol} {metric}")
        finally:
            q.close()

    def test_advanced_petrochemical_fy2024_net_loss_is_stored_negative(self):
        q = FinancialQueryService(self.dbpath)
        try:
            ni = _value(q.metric_history("SA", "2330", "net_income"), "2024-12-31")
        finally:
            q.close()
        self.assertEqual(ni, Decimal("-264972000"))


def _value(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
