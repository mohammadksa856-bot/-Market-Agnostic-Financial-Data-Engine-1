"""Local review only. Synthetic evidence is not a real issuer exemption."""
import json
import unittest
from copy import deepcopy
from decimal import Decimal
from finengine.factory_contract import DEFAULT_CONTRACT
from finengine.factory_policy_review import apply_review_policy, normalized_score


def fixture():
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    return {"categories": [{"category_key": c["category_key"], "weight": str(c["weight"]),
                            "threshold": str(c["completeness_threshold"]), "score": "1",
                            "weighted_score": str(c["weight"]), "status": "complete",
                            "evidence": {"expected_fields": 1, "missing_field_groups": []}}
                           for c in contract["categories"]], "total_score": "100", "target_score": "95",
            "readiness_state": "ready", "coverage_thresholds_passed": True}


class PolicyReviewTests(unittest.TestCase):
    def decision(self):
        return {"kind": "structural_exclusion", "reviewed": True,
                "evidence_reference": "synthetic-test-only", "evidence_sha256": "a" * 64}

    def row(self, value, key="operational_kpis"):
        return next(r for r in value["categories"] if r["category_key"] == key)

    def test_proven_exclusion_no_credit_and_no_penalty(self):
        out = apply_review_policy(fixture(), {"operational_kpis": self.decision()})
        self.assertEqual(out["applicable_weight"], "93")
        self.assertEqual(out["total_score"], "100")
        self.assertIsNone(self.row(out)["weighted_score"])
        self.assertIsNone(self.row(out)["score"])
        self.assertNotEqual(out["readiness_state"], "ready")

    def test_catalog_gap_blocks_final_score(self):
        out = apply_review_policy(fixture(), {"operational_kpis": {"kind": "catalog_gap"}})
        self.assertIsNone(out["total_score"])
        self.assertEqual(out["applicable_weight"], "100")
        self.assertFalse(out["coverage_thresholds_passed"])

    def test_pack_na_alone_not_proof(self):
        original = fixture()
        self.row(original)["status"] = "not_applicable"
        out = apply_review_policy(original)
        self.assertIsNone(out["total_score"])

    def test_unreviewed_or_unbound_exclusion_not_accepted(self):
        for broken in ({"reviewed": False}, {"evidence_reference": ""}, {"evidence_sha256": "x" * 64}):
            decision = self.decision() | broken
            original = fixture()
            self.row(original)["status"] = "not_applicable"
            self.assertIsNone(apply_review_policy(original, {"operational_kpis": decision})["total_score"])

    def test_empty_definition_blocks_final_score(self):
        original = fixture()
        self.row(original)["evidence"]["expected_fields"] = 0
        self.assertIsNone(apply_review_policy(original)["total_score"])

    def test_missing_extraction_stays_in_denominator(self):
        original = fixture()
        self.row(original).update(score="0", status="missing")
        out = apply_review_policy(original)
        self.assertEqual(out["applicable_weight"], "100")
        self.assertEqual(out["total_score"], "93")
        self.assertFalse(out["applicable_thresholds_passed"])

    def test_telecom_valid_exclusion_uses_same_policy(self):
        out = apply_review_policy(fixture(), {"sector_specific_fields": self.decision()})
        self.assertEqual(out["applicable_weight"], "93")
        self.assertEqual(out["total_score"], "100")

    def test_no_exclusion_preserves_other_sector_score(self):
        original = fixture()
        for row in original["categories"]:
            row["score"] = "0.8"
        out = apply_review_policy(original)
        self.assertEqual(out["total_score"], "80.0")
        self.assertEqual(out["applicable_weight"], "100")

    def test_zero_denominator_not_measured(self):
        self.assertIsNone(normalized_score(Decimal(0), Decimal(0)))

    def test_universal_categories_cannot_be_excluded(self):
        original = fixture()
        decisions = {r["category_key"]: self.decision() for r in original["categories"]}
        out = apply_review_policy(original, decisions)
        self.assertIsNone(out["total_score"])
        self.assertIn("forbidden_category_exclusion:financial_statements", out["policy_blocking_reasons"])
        self.assertIn("forbidden_category_exclusion:sources_lineage_freshness", out["policy_blocking_reasons"])

    def test_thresholds_weights_and_target_cannot_be_lowered(self):
        for field, value in (("weight", "0"), ("threshold", "0")):
            original = fixture()
            self.row(original)[field] = value
            self.assertIsNone(apply_review_policy(original)["total_score"])
        original = fixture()
        original["target_score"] = "90"
        self.assertIsNone(apply_review_policy(original)["total_score"])

    def test_missing_category_and_duplicate_block_score(self):
        original = fixture()
        original["categories"].pop()
        self.assertIsNone(apply_review_policy(original)["total_score"])
        original = fixture()
        original["categories"].append(deepcopy(original["categories"][0]))
        self.assertIsNone(apply_review_policy(original)["total_score"])

    def test_original_measurement_immutable(self):
        original = fixture()
        before = deepcopy(original)
        apply_review_policy(original, {"operational_kpis": self.decision()})
        self.assertEqual(original, before)


if __name__ == "__main__":
    unittest.main()
