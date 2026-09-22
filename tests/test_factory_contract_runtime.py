import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.factory_contract import (
    contract_category_ready,
    evaluate_factory_contract,
    seed_factory_contract_categories,
)
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
        strategies = {row["category_key"]: row["job_strategy"] for row in result["categories"]}
        self.assertEqual(strategies["market_data"], "periodic_market_data_sync")
        self.assertEqual(strategies["valuation"], "calculated_no_network")

    def test_contract_categories_are_seeded_without_replacing_legacy_taxonomy(self):
        keys = seed_factory_contract_categories(self.db)
        self.assertEqual(len(keys), 18)
        stored = {row[0] for row in self.db.conn.execute(
            "SELECT category_key FROM knowledge_categories"
        )}
        self.assertIn("company_profile", stored)
        self.assertIn("identity", stored)

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

    def test_every_hard_gate_is_evaluated_and_failures_block_readiness(self):
        result = evaluate_factory_contract(self.db, self.company.company_id)
        self.assertTrue(result["all_hard_gates_evaluated"])
        self.assertFalse(result["all_hard_gates_passed"])
        self.assertEqual(result["readiness_state"], "not_ready")
        self.assertFalse(any(
            reason.startswith("hard_gate_evaluator_required:")
            for reason in result["blocking_reasons"]
        ))
        self.assertTrue(any(
            reason.startswith("hard_gate_failed:") for reason in result["blocking_reasons"]
        ))
        financial = next(
            row for row in result["categories"] if row["category_key"] == "financial_statements"
        )
        self.assertFalse(contract_category_ready(financial))

    def test_machine_evaluable_gates_report_pass_or_failure_with_evidence(self):
        result = evaluate_factory_contract(self.db, self.company.company_id)
        by_key = {row["category_key"]: row for row in result["categories"]}
        financial_gates = by_key["financial_statements"]["hard_gates"]
        self.assertEqual([gate["status"] for gate in financial_gates], ["failed", "passed"])
        self.assertEqual(financial_gates[0]["annual_periods"], 0)
        self.assertEqual(financial_gates[0]["quarter_periods"], 0)
        self.assertEqual(by_key["market_data"]["hard_gates"][0]["status"], "failed")
        self.assertEqual(
            by_key["sector_specific_fields"]["hard_gates"][0]["status"], "passed"
        )
        self.assertFalse(result["all_hard_gates_passed"])

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
        self.assertEqual(len(lineage["hard_gates"]), 2)
        self.assertEqual(lineage["hard_gates"][1]["status"], "failed")
        self.assertIn("market_data", lineage["hard_gates"][1]["stale_categories"])


if __name__ == "__main__":
    unittest.main()
