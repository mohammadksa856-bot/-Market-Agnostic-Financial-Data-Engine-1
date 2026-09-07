"""Acceptance tests for the Saudi utilities-sector data batch.

Covers Saudi Energy Company / SECO (5110), ACWA Power (2082) and Marafiq (2083),
all transcribed from the issuers' official FY2025 audited consolidated financial
statements. This batch adds no engine or catalog changes.
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


class UtilitiesManifestVerificationTests(unittest.TestCase):
    def test_each_utility_manifest_has_no_identity_failures(self):
        for prefix in ("seco-", "acwa-power-", "marafiq-"):
            report = ManifestVerifier(REPO_IMPORTS).verify(prefix)
            self.assertEqual(report["failures"], 0, (prefix, report["detail"]))
            self.assertEqual(report["unmapped_labels"], [], prefix)
            self.assertGreater(report["passed"], 15, prefix)

    def test_seco_balance_sheet_includes_the_mudaraba_instrument_in_equity(self):
        # SEC classifies the government Mudaraba instrument within equity, so
        # total_equity (~257.7bn) must still satisfy assets = liabilities + equity.
        report = ManifestVerifier(REPO_IMPORTS).verify("seco-")
        bs = [c for c in report["detail"]
              if c["check"].startswith("balance_sheet: assets = liabilities + equity")]
        self.assertTrue(bs, report["detail"])
        self.assertTrue(all(c["status"] == "pass" for c in bs), bs)


class UtilitiesSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "utilities.sqlite3")
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

    def test_all_three_utilities_publish_without_errors(self):
        for company_id in ("sa:5110", "sa:2082", "sa:2083"):
            rows = self._rows(company_id)
            self.assertTrue(rows, f"no manifest published for {company_id}")
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)
                self.assertNotIn("error", row, row)

    def test_headline_figures_match_the_filings(self):
        expected = {
            "5110": {"revenue": "102217782000", "net_income": "12974811000"},
            "2082": {"revenue": "7413501000", "net_income": "2060604000"},
            "2083": {"revenue": "6945620000", "net_income": "449428000"},
        }
        q = FinancialQueryService(self.dbpath)
        try:
            for symbol, metrics in expected.items():
                for metric, value in metrics.items():
                    hist = q.metric_history("SA", symbol, metric)
                    self.assertEqual(
                        _value(hist, "2025-12-31"), Decimal(value),
                        f"{symbol} {metric}")
        finally:
            q.close()

    def test_acwa_power_profit_splits_between_parent_and_nci(self):
        q = FinancialQueryService(self.dbpath)
        try:
            parent = _value(q.metric_history("SA", "2082", "net_income_parent"), "2025-12-31")
            nci = _value(q.metric_history("SA", "2082", "net_income_noncontrolling"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(parent, Decimal("1852225000"))
        self.assertEqual(nci, Decimal("208379000"))
        self.assertEqual(parent + nci, Decimal("2060604000"))

    def test_derived_net_margin_is_reasonable_for_each_utility(self):
        bounds = {"5110": (Decimal("0.08"), Decimal("0.20")),
                  "2082": (Decimal("0.18"), Decimal("0.40")),
                  "2083": (Decimal("0.02"), Decimal("0.12"))}
        q = FinancialQueryService(self.dbpath)
        try:
            for symbol, (lo, hi) in bounds.items():
                margin = _value(q.metric_history("SA", symbol, "net_margin"), "2025-12-31")
                self.assertIsNotNone(margin, f"{symbol} net_margin missing")
                self.assertTrue(lo <= margin <= hi, f"{symbol} net_margin {margin}")
        finally:
            q.close()


def _value(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
