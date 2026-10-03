import json
import tempfile
import unittest
from pathlib import Path

from finengine.audit_consistency import (
    definition_drift,
    dimension_reconciliation,
    filing_date_before_exchange_upload,
    label_signature,
    load_manifests,
    run_all,
)

REPO_IMPORTS = Path(__file__).resolve().parents[1] / "data" / "imports"


def _fact(metric, label, value, period_end, kind="fy", scale="1000", dimensions=None):
    fact = {
        "metric": metric, "source_label": label, "value": str(value),
        "period_end": period_end, "period_kind": kind, "scale": scale,
        "currency": "SAR", "unit": "SAR", "page": 1,
    }
    if dimensions:
        fact["dimensions"] = dimensions
    return fact


def _manifest(facts, **header):
    payload = {"company_id": "sa:9999", "market": "SA", "symbol": "9999",
               "filed_at": "2026-03-01", "source_url": "https://example.test/x.pdf",
               "facts": facts}
    payload.update(header)
    return payload


class DefinitionDriftTests(unittest.TestCase):
    def test_label_signature_ignores_punctuation_plurals_and_restated(self):
        self.assertEqual(
            label_signature("Purchase of property, plant and equipment (restated)"),
            label_signature("Purchases of Property plant and equipment"),
        )

    def test_capex_that_adds_intangibles_in_one_year_is_flagged(self):
        manifests = [("a.json", _manifest([
            _fact("capex", "Purchase of property, plant and equipment", -8750, "2025-12-31"),
            _fact("capex", "Purchase of property plant and equipment and intangible assets",
                  -10200, "2024-12-31"),
        ]))]
        findings = definition_drift(manifests)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["metric"], "capex")
        self.assertEqual(len(findings[0]["variants"]), 2)

    def test_same_label_in_every_year_is_clean(self):
        manifests = [("a.json", _manifest([
            _fact("capex", "Additions to property, plant and equipment", -1, "2025-12-31"),
            _fact("capex", "Additions to property plant and equipment (restated)", -2, "2024-12-31"),
        ]))]
        self.assertEqual(definition_drift(manifests), [])

    def test_non_sensitive_metrics_and_dimensioned_facts_are_ignored(self):
        manifests = [("a.json", _manifest([
            _fact("revenue", "Revenue", 1, "2025-12-31"),
            _fact("revenue", "Sales of goods and services", 1, "2024-12-31"),
            _fact("capex", "Capex - segment A", 1, "2025-12-31", dimensions={"segment": "A"}),
            _fact("capex", "Capex - segment B plus other", 1, "2024-12-31", dimensions={"segment": "B"}),
        ]))]
        self.assertEqual(definition_drift(manifests), [])


class DimensionReconciliationTests(unittest.TestCase):
    def _debt(self, murabaha):
        return [
            _fact("long_term_debt", "Non-current debt", 21000, "2025-12-31", "instant"),
            _fact("current_debt", "Current debt", 12000, "2025-12-31", "instant"),
            _fact("borrowings_by_instrument", "Bonds", 7000, "2025-12-31", "instant",
                  dimensions={"instrument": "Bonds"}),
            _fact("borrowings_by_instrument", "Murabaha", murabaha, "2025-12-31", "instant",
                  dimensions={"instrument": "Murabaha"}),
            _fact("borrowings_by_instrument", "Overdraft", 600, "2025-12-31", "instant",
                  dimensions={"instrument": "Bank overdraft"}),
            _fact("borrowings_by_instrument", "Loans", 18400, "2025-12-31", "instant",
                  dimensions={"instrument": "Loans"}),
        ]

    def test_component_counted_twice_breaks_the_reconciliation(self):
        # 7000 + 7000 + 600 + 18400 = 33000 reconciles; Murabaha carrying the
        # overdraft as well (7000 + 599.. style double count) must not.
        findings = dimension_reconciliation([("a.json", _manifest(self._debt(7000)))])
        self.assertEqual(findings, [])
        findings = dimension_reconciliation([("a.json", _manifest(self._debt(7600)))])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["component_metric"], "borrowings_by_instrument")
        self.assertEqual(findings[0]["difference"], "600000")

    def test_rounding_inside_half_a_unit_per_component_passes(self):
        facts = [
            _fact("revenue", "Revenue", 100, "2025-12-31"),
            _fact("revenue_by_geography", "KSA", 40, "2025-12-31", dimensions={"geography": "KSA"}),
            _fact("revenue_by_geography", "Other", 61, "2025-12-31", dimensions={"geography": "Other"}),
        ]
        # 101 vs 100 differs by one unit; tolerance is 2 components * 1 / 2 = 1 unit.
        self.assertEqual(dimension_reconciliation([("a.json", _manifest(facts))]), [])
        facts[2] = _fact("revenue_by_geography", "Other", 62, "2025-12-31", dimensions={"geography": "Other"})
        self.assertEqual(len(dimension_reconciliation([("a.json", _manifest(facts))])), 1)

    def test_missing_total_cannot_prove_anything(self):
        facts = [
            _fact("revenue_by_geography", "KSA", 40, "2025-12-31", dimensions={"geography": "KSA"}),
            _fact("revenue_by_geography", "Other", 99, "2025-12-31", dimensions={"geography": "Other"}),
        ]
        self.assertEqual(dimension_reconciliation([("a.json", _manifest(facts))]), [])


class FilingDateTests(unittest.TestCase):
    URL = "https://www.saudiexchange.sa/Resources/fsPdf/423_0_2026-02-23_11-20-33_En.pdf"

    def test_board_approval_date_before_upload_is_flagged(self):
        findings = filing_date_before_exchange_upload(
            [("a.json", _manifest([], filed_at="2026-02-15", source_url=self.URL))])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["days_early"], 8)

    def test_declared_basis_or_same_day_or_other_hosts_are_clean(self):
        self.assertEqual(filing_date_before_exchange_upload([
            ("a.json", _manifest([], filed_at="2026-02-15", source_url=self.URL,
                                 filed_at_basis="official_exchange_url_upload_timestamp")),
            ("b.json", _manifest([], filed_at="2026-02-23", source_url=self.URL)),
            ("c.json", _manifest([], filed_at="2026-01-01", source_url="https://issuer.example/a.pdf")),
        ]), [])


class LoaderAndBundledDataTests(unittest.TestCase):
    def test_loader_skips_non_flat_and_unreadable_files(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            (directory / "flat.json").write_text(json.dumps(_manifest([])), encoding="utf-8")
            (directory / "nested.json").write_text(json.dumps({"facts": {"x": 1}}), encoding="utf-8")
            (directory / "broken.json").write_text("{", encoding="utf-8")
            self.assertEqual([n for n, _ in load_manifests(directory)], ["flat.json"])

    def test_report_only_run_over_bundled_manifests_is_well_formed(self):
        report = run_all(REPO_IMPORTS, "arabian-cement")
        self.assertEqual(report["manifests"], 1)
        for key in ("definition_drift", "dimension_reconciliation", "filing_date_before_exchange_upload"):
            self.assertIsInstance(report[key], list)


if __name__ == "__main__":
    unittest.main()
