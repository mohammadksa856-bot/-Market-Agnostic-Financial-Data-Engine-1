import json
import tempfile
import unittest
from pathlib import Path

from finengine.verification import ManifestVerifier

REPO_IMPORTS = Path(__file__).resolve().parents[1] / "data" / "imports"


def _write(directory: Path, name: str, facts: list[dict]) -> None:
    (directory / name).write_text(json.dumps({
        "filing_type": "annual-results", "filed_at": "2026-03-01",
        "period_end": "2025-12-31", "source_url": "https://example.test/report.pdf",
        "facts": facts,
    }), encoding="utf-8")


def _fy(label, value):
    return {"label": label, "value": value, "scale": 1000000,
            "period_start": "2025-01-01", "period_end": "2025-12-31",
            "period_kind": "fy", "fiscal_year": 2025}


def _instant(label, value):
    return {"label": label, "value": value, "scale": 1000000,
            "period_end": "2025-12-31", "period_kind": "instant", "fiscal_year": 2025}


class ManifestVerificationTests(unittest.TestCase):
    def test_bundled_aramco_manifests_have_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("aramco-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 20)

    def test_balance_sheet_that_does_not_balance_fails(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            _write(directory, "acme-2025-fy.json", [
                _instant("total assets", 1000),
                _instant("total liabilities", 600),
                _instant("total equity", 300),  # 600 + 300 != 1000
            ])
            report = ManifestVerifier(directory).verify()
            self.assertFalse(report["ok"])
            self.assertTrue(any(
                c["check"].startswith("balance_sheet: assets = liabilities + equity")
                and c["status"] == "fail" for c in report["detail"]))

    def test_conflicting_value_across_manifests_is_flagged(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            _write(directory, "acme-2025-a.json", [_fy("revenue", 1000)])
            _write(directory, "acme-2025-b.json", [_fy("revenue", 1400)])
            report = ManifestVerifier(directory).verify()
            self.assertFalse(report["ok"])
            self.assertTrue(any(
                c["check"] == "cross-manifest value conflict" and c["status"] == "fail"
                for c in report["detail"]))

    def test_clean_income_statement_passes(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            _write(directory, "acme-2025-fy.json", [
                _fy("revenue", 900),
                _fy("other income related to sales", 100),
                _fy("revenue and other income related to sales", 1000),
                _fy("income before income taxes and zakat", 400),
                _fy("income taxes and zakat", -100),
                _fy("net income", 300),
            ])
            report = ManifestVerifier(directory).verify()
            self.assertTrue(report["ok"], report["detail"])
            self.assertEqual(report["failures"], 0)


if __name__ == "__main__":
    unittest.main()
