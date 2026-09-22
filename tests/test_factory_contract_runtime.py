import json
import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.factory_contract import (
    contract_category_ready,
    evaluate_factory_contract,
    load_field_availability_assessments,
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

    def test_reviewed_unavailable_field_changes_denominator_with_archived_evidence(self):
        before = evaluate_factory_contract(self.db, self.company.company_id)
        profile_before = next(
            row for row in before["categories"] if row["category_key"] == "company_profile"
        )
        missing = next(iter(profile_before["evidence"]["missing_fields"].values()))[0]
        source = SourceDocument(
            self.company.company_id, Market.SA, "https://issuer.example/report.pdf",
            "source:availability", "annual-report", "2026-03-01", b"document",
        )
        self.db.save_source(source, "pdf", None)
        self.db.upsert_field_availability(
            self.company.company_id, missing, "unavailable",
            reason_code="not_disclosed", reason="Reviewed report does not disclose the field",
            assessed_by="test-reviewer", evidence_source_key=source.source_key,
            evidence_note="Annual report and notes searched; no disclosure found.",
        )
        after = evaluate_factory_contract(self.db, self.company.company_id)
        profile_after = next(
            row for row in after["categories"] if row["category_key"] == "company_profile"
        )
        self.assertEqual(
            profile_after["evidence"]["expected_fields"],
            profile_before["evidence"]["expected_fields"] - 1,
        )
        self.assertEqual(
            profile_after["evidence"]["reviewed_unavailable_or_not_applicable"][0]["field_key"],
            missing,
        )

    def test_negative_evidence_cannot_be_recorded_without_required_proof(self):
        field = self.db.conn.execute(
            "SELECT field_key FROM data_catalog_fields WHERE enabled=1 LIMIT 1"
        ).fetchone()[0]
        with self.assertRaisesRegex(ValueError, "archived company source"):
            self.db.upsert_field_availability(
                self.company.company_id, field, "unavailable",
                reason_code="not_disclosed", reason="Not found", assessed_by="reviewer",
            )
        with self.assertRaisesRegex(ValueError, "structural rule"):
            self.db.upsert_field_availability(
                self.company.company_id, field, "not_applicable",
                reason_code="not_applicable", reason="Wrong business model",
                assessed_by="reviewer",
            )

    def test_expired_negative_evidence_does_not_change_contract_score(self):
        before = evaluate_factory_contract(self.db, self.company.company_id)
        profile = next(
            row for row in before["categories"] if row["category_key"] == "company_profile"
        )
        missing = next(iter(profile["evidence"]["missing_fields"].values()))[0]
        source = SourceDocument(
            self.company.company_id, Market.SA, "https://issuer.example/old.pdf",
            "source:expired", "annual-report", "2025-03-01", b"old document",
        )
        self.db.save_source(source, "pdf", None)
        self.db.upsert_field_availability(
            self.company.company_id, missing, "unavailable",
            reason_code="not_disclosed", reason="Old review", assessed_by="reviewer",
            evidence_source_key=source.source_key, evidence_note="Old report searched.",
            expires_at="2020-01-01T00:00:00+00:00",
        )
        after = evaluate_factory_contract(self.db, self.company.company_id)
        profile_after = next(
            row for row in after["categories"] if row["category_key"] == "company_profile"
        )
        self.assertEqual(profile_after["score"], profile["score"])
        self.assertEqual(profile_after["evidence"]["expected_fields"],
                         profile["evidence"]["expected_fields"])

    def test_reviewed_assessment_artifact_survives_snapshot_style_reload(self):
        result = evaluate_factory_contract(self.db, self.company.company_id)
        profile = next(
            row for row in result["categories"] if row["category_key"] == "company_profile"
        )
        fields = next(iter(profile["evidence"]["missing_fields"].values()))[:2]
        source_url = "https://issuer.example/availability-report.pdf"
        source = SourceDocument(
            self.company.company_id, Market.SA, source_url,
            "source:artifact", "annual-report", "2026-03-01", b"document",
        )
        self.db.save_source(source, "pdf", None)
        directory = Path(self.temp.name) / "availability"
        directory.mkdir()
        (directory / "sa-7010.json").write_text(json.dumps({
            "company_id": self.company.company_id,
            "assessments": [
                {
                    "field_key": fields[0], "status": "unavailable",
                    "reason_code": "not_disclosed", "reason": "Not disclosed",
                    "assessed_by": "reviewer", "evidence_source_url": source_url,
                    "evidence_note": "Annual report and notes searched.",
                },
                {
                    "field_key": fields[1], "status": "not_applicable",
                    "reason_code": "not_applicable", "reason": "Structural exclusion",
                    "assessed_by": "reviewer", "rule_reference": "telecom-pack:no-field",
                },
            ],
        }), encoding="utf-8")
        loaded = load_field_availability_assessments(self.db, directory)
        self.assertEqual(loaded, {"files": 1, "assessments": 2})
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM company_field_availability"
        ).fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
