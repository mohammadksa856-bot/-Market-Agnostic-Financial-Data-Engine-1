"""Extraction + calculation checks for the Saudi banking-sector data batch.

Covers the ten listed Saudi banks (1010, 1020, 1030, 1050, 1060, 1080, 1120,
1140, 1150, 1180): the hand-read / supplement manifests must satisfy every
accounting identity, and the engine's bank ratios must reconcile to figures the
issuers disclose themselves (a cross-check, never an ingested value).
"""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind
from finengine.verification import ManifestVerifier

_IMPORTS = Path(__file__).resolve().parent.parent / "data" / "imports"
_BANK_MANIFESTS = [
    "riyad-2025-fy.json", "aljazira-2025-fy.json", "saib-2025-fy.json",
    "bsf-2025-fy.json", "sab-2025-fy.json", "anb-2025-fy.json",
    "alrajhi-2025-fy.json", "alrajhi-supplement.json",
    "albilad-2025-fy.json", "alinma-supplement.json", "alinma-notes-2025.json",
    "snb-2025-fy.json",
]


class BankingManifestVerifyTests(unittest.TestCase):
    def test_every_bank_manifest_present(self):
        for name in _BANK_MANIFESTS:
            self.assertTrue((_IMPORTS / name).exists(), f"missing manifest: {name}")

    def test_bank_manifests_pass_all_accounting_identities(self):
        with tempfile.TemporaryDirectory() as name:
            staged = Path(name) / "imports"
            staged.mkdir()
            for manifest in _BANK_MANIFESTS:
                (staged / manifest).write_bytes((_IMPORTS / manifest).read_bytes())
            report = ManifestVerifier(staged).verify()
        failures = [c for c in report["detail"] if c["status"] == "fail"]
        self.assertEqual(failures, [], failures)

    def test_banking_identities_actually_fire(self):
        """Guard against a silent no-op: the bank-specific checks must run."""
        with tempfile.TemporaryDirectory() as name:
            staged = Path(name) / "imports"
            staged.mkdir()
            (staged / "snb-2025-fy.json").write_bytes((_IMPORTS / "snb-2025-fy.json").read_bytes())
            report = ManifestVerifier(staged).verify()
        checks = {c["check"] for c in report["detail"] if c["status"] == "pass"}
        self.assertIn("banking: net financing income = income - expense", checks)
        self.assertIn(
            "banking: total operating expenses = ex-provision expense + provision", checks)


def _bank_fact(metric, value, kind=PeriodKind.INSTANT):
    return Fact("sa:TST", metric, Decimal(str(value)), "SAR", "SAR",
                "2025-01-01" if kind is not PeriodKind.INSTANT else None,
                "2025-12-31", kind, 2025, None, "src", "url", "2026-02-01")


class BankRatioCalculationTests(unittest.TestCase):
    def _calc(self, facts):
        out = {f.metric: f for f in Calculator().calculate(facts)}
        return out

    def test_credit_loss_allowance_derived_from_gross_minus_net(self):
        facts = [
            _bank_fact("gross_loans", 232_955_242_000),
            _bank_fact("net_loans", 229_746_838_000),
            _bank_fact("customer_deposits", 227_373_930_000),
        ]
        out = self._calc(facts)
        self.assertIn("credit_loss_allowance", out)
        self.assertEqual(out["credit_loss_allowance"].value, Decimal("3208404000"))

    def test_npl_coverage_is_positive_regardless_of_allowance_sign(self):
        base = [
            _bank_fact("gross_loans", 100_000),
            _bank_fact("nonperforming_loans", 2_000),
            _bank_fact("net_loans", 97_000),
        ]
        signed = self._calc(base + [_bank_fact("credit_loss_allowance", -3_000)])
        unsigned = self._calc(base + [_bank_fact("credit_loss_allowance", 3_000)])
        self.assertEqual(signed["nonperforming_loans_coverage"].value,
                         unsigned["nonperforming_loans_coverage"].value)
        self.assertEqual(signed["nonperforming_loans_coverage"].value, Decimal("1.5"))

    def test_casa_ratio_fires_on_a_single_combined_current_account_line(self):
        out = self._calc([
            _bank_fact("demand_deposits", 463_255_347),   # "current and call accounts"
            _bank_fact("customer_deposits", 636_094_377),
        ])
        self.assertIn("casa_ratio", out)
        self.assertAlmostEqual(float(out["casa_ratio"].value), 0.728, places=3)

    def test_capital_adequacy_ratio_reconciles_to_disclosure(self):
        # SNB note 37: regulatory capital 175,635,176 / RWA 830,157,896 = 21.2%
        out = self._calc([
            _bank_fact("regulatory_capital", 175_635_176_000),
            _bank_fact("risk_weighted_assets", 830_157_896_000),
        ])
        self.assertAlmostEqual(float(out["capital_adequacy_ratio"].value), 0.2116, places=4)


class SupplementScaleTests(unittest.TestCase):
    def test_per_share_rows_ignore_the_sheet_scale(self):
        try:
            import openpyxl
        except ImportError:  # pragma: no cover
            self.skipTest("needs openpyxl")
        from finengine.reading_xlsx import SupplementReader
        with tempfile.TemporaryDirectory() as name:
            d = Path(name)
            wb = openpyxl.Workbook()
            sh = wb.active
            sh.title = "IS"
            sh.append(["SAR (mn)", "FY 2025"])
            sh.append(["Net income for the year", 24_000])
            sh.append(["Earnings per share (SAR)", 5.853702])
            sh.append(["Dividends per share (SAR)", 2.5])
            xlsx = d / "s.xlsx"
            wb.save(xlsx)
            mapping = d / "m.json"
            mapping.write_text(json.dumps({
                "company_id": "sa:9999", "source_url": "u", "scale": "1000000",
                "sheets": {"IS": {
                    "Net income for the year": ["net_income", "fy"],
                    "Earnings per share (SAR)": ["eps_diluted", "fy"],
                    "Dividends per share (SAR)": ["dividends_per_share", "fy"],
                }},
            }), encoding="utf-8")
            manifest = SupplementReader(xlsx, mapping).read(
                market="SA", symbol="9999", currency="SAR", filed_at="2026-02-04")
        by = {f["metric"]: f for f in manifest["facts"]}
        self.assertEqual(by["net_income"]["scale"], "1000000")
        self.assertEqual(by["eps_diluted"]["scale"], "1")
        self.assertEqual(by["eps_diluted"]["value"], "5.853702")
        self.assertEqual(by["dividends_per_share"]["scale"], "1")


if __name__ == "__main__":
    unittest.main()
