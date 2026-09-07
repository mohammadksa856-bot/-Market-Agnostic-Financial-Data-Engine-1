"""Extraction + calculation checks for the Saudi insurance-sector batch 1.

Covers Tawuniya (8010), Bupa Arabia (8210), Saudi Re (8200) and Walaa (8060):
every hand-read IFRS 17 manifest must satisfy the accounting identities, and the
engine's insurance ratios must be internally consistent.
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
_MANIFESTS = [
    "tawuniya-2025-fy.json", "bupa-arabia-2025-fy.json",
    "saudi-re-2025-fy.json", "walaa-2025-fy.json",
]


class InsuranceManifestTests(unittest.TestCase):
    def test_manifests_present(self):
        for name in _MANIFESTS:
            self.assertTrue((_IMPORTS / name).exists(), name)

    def test_manifests_pass_all_accounting_identities(self):
        with tempfile.TemporaryDirectory() as name:
            staged = Path(name) / "imports"
            staged.mkdir()
            for m in _MANIFESTS:
                (staged / m).write_bytes((_IMPORTS / m).read_bytes())
            report = ManifestVerifier(staged).verify()
        failures = [c for c in report["detail"] if c["status"] == "fail"]
        self.assertEqual(failures, [], failures)

    def test_ifrs17_identities_fire(self):
        with tempfile.TemporaryDirectory() as name:
            staged = Path(name) / "imports"
            staged.mkdir()
            (staged / "tawuniya-2025-fy.json").write_bytes(
                (_IMPORTS / "tawuniya-2025-fy.json").read_bytes())
            report = ManifestVerifier(staged).verify()
        passed = {c["check"] for c in report["detail"] if c["status"] == "pass"}
        self.assertIn("insurance: service result = revenue - service expense", passed)
        self.assertIn(
            "insurance: underwriting result = service result + net reinsurance result", passed)


def _fact(metric, value, kind=PeriodKind.FY):
    return Fact("sa:TST", metric, Decimal(str(value)), "SAR", "SAR", "2025-01-01",
                "2025-12-31", kind, 2025, None, "s", "u", "2026-02-01")


class InsuranceRatioCalcTests(unittest.TestCase):
    def _calc(self, facts):
        return {f.metric: f for f in Calculator().calculate(facts)}

    def test_insurance_service_result_is_derived_when_not_reported(self):
        out = self._calc([
            _fact("insurance_revenue", 21_403_177),
            _fact("insurance_service_expense", -18_016_361),
        ])
        self.assertEqual(out["insurance_service_result"].value, Decimal("3386816"))

    def test_combined_and_expense_ratio(self):
        out = self._calc([
            _fact("insurance_revenue", 21_403_177),
            _fact("underwriting_result", 1_116_251),
            _fact("operating_expenses", -691_665),
        ])
        # combined = (rev - underwriting_result + opex) / rev
        self.assertAlmostEqual(float(out["combined_ratio"].value), 0.9802, places=4)
        self.assertAlmostEqual(float(out["expense_ratio"].value), 0.0323, places=4)

    def test_ratios_are_no_op_without_insurer_lines(self):
        out = self._calc([_fact("revenue", 1000), _fact("net_income", 100)])
        self.assertNotIn("combined_ratio", out)
        self.assertNotIn("expense_ratio", out)


if __name__ == "__main__":
    unittest.main()
