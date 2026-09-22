import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.factory_contract import evaluate_factory_contract
from finengine.models import Company, Market, SourceDocument


class FactoryContractRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "contract.sqlite3"
        self.db = Database(self.path)
        self.company = Company(
            "sa:7010", Market.SA, "7010", "Test Telecom", "SAR",
            isin="SA0000000001", exchange="Saudi Exchange", country="SA",
            sector="Communication Services", industry="Telecommunications",
            timezone="Asia/Riyadh",
        )
        self.db.register_company(self.company)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_runtime_evaluates_the_contract_taxonomy_not_legacy_understanding(self):
        result = evaluate_factory_contract(self.db, self.company.company_id)
        keys = {row["category_key"] for row in result["categories"]}
        self.assertEqual(len(keys), 18)
        self.assertIn("company_profile", keys)
        self.assertIn("financial_statements", keys)
        self.assertIn("sources_lineage_freshness", keys)
        self.assertNotIn("identity", keys)
        self.assertFalse(result["legacy_understanding_score_included"])

    def test_telecom_pack_narrows_operational_groups_and_marks_sector_fields_na(self):
        result = evaluate_factory_contract(self.db, self.company.company_id)
        by_key = {row["category_key"]: row for row in result["categories"]}
        self.assertEqual(result["sector_pack"], "telecom")
        self.assertEqual(
            by_key["operational_kpis"]["evidence"]["field_groups"],
            ["telecommunications"],
        )
        self.assertEqual(by_key["sector_specific_fields"]["status"], "not_applicable")
        self.assertEqual(by_key["sector_specific_fields"]["score"], "1")

    def test_prose_hard_gates_never_silently_pass(self):
        result = evaluate_factory_contract(self.db, self.company.company_id)
        self.assertFalse(result["all_hard_gates_evaluated"])
        self.assertEqual(result["readiness_state"], "not_ready")
        self.assertTrue(any(
            reason.startswith("hard_gate_evaluator_required:")
            for reason in result["blocking_reasons"]
        ))

    def test_strict_lineage_needs_document_and_fact_location(self):
        source = SourceDocument(
            self.company.company_id, Market.SA, "https://issuer.example/report.pdf",
            "source:telecom", "annual-report", "2026-03-01", b"document",
        )
        self.db.save_source(source, "pdf", None)
        result = evaluate_factory_contract(self.db, self.company.company_id)
        lineage = next(
            row for row in result["categories"]
            if row["category_key"] == "sources_lineage_freshness"
        )
        self.assertEqual(lineage["score"], "0")
        self.assertFalse(
            lineage["evidence"]["strict_five_field_provenance_certified"]
        )


if __name__ == "__main__":
    unittest.main()
