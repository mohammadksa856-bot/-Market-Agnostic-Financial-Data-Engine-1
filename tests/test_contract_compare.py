import copy
import unittest
from decimal import Decimal

from finengine.contract_compare import BUNDLE_VERSION, compare_bundles, contract_score


def field(key, unit="currency", definition=None, period="flow"):
    return {"key": key, "definition": definition or key.title(), "unit": unit, "period_behavior": period,
            "value_type": "decimal"}


def observation(value, end="2025-12-31", kind="fy", unit="SAR", currency="SAR", source="https://x.test/ar2025",
                start="2025-01-01"):
    return {"period_kind": kind, "period_start": start, "period_end": end, "dimensions": "", "value": value,
            "unit": unit, "currency": currency, "source_url": source}


def bundle(label, categories, records):
    return {"bundle_version": BUNDLE_VERSION, "label": label, "company_id": "sa:TST",
            "contract": {"categories": categories},
            "records": [{"key": key, "status": status, "observations": observations}
                        for key, (status, observations) in records.items()]}


class ContractCompareTests(unittest.TestCase):
    def setUp(self):
        self.a = bundle("pipeline-a", [
            {"key": "statements", "weight": "60", "fields": [field("revenue"), field("ebit"), field("capex")]},
            {"key": "segments", "weight": "20", "fields": [field("segment_revenue")]},
            {"key": "sector", "weight": "20", "fields": [field("segment_revenue"), field("refinery_runs", "mbpd")]},
        ], {
            "revenue": ("closed", [observation("100")]),
            "ebit": ("closed", [observation("40")]),
            "capex": ("missing", []),
            "segment_revenue": ("closed", [observation("60")]),
            "refinery_runs": ("missing", []),
        })
        self.b = bundle("pipeline-b", [
            {"key": "statements", "weight": "50", "fields": [field("revenue"), field("ebit", definition="Operating income"),
                                                            field("capex"), field("gross_profit")]},
            {"key": "segments", "weight": "50", "fields": [field("segment_revenue")]},
        ], {
            "revenue": ("closed", [observation("100", source="https://x.test/ar2025-financials")]),
            "ebit": ("closed", [observation("41")]),
            "capex": ("closed", [observation("-30")]),
            "gross_profit": ("missing", []),
            "segment_revenue": ("closed", [observation("60", kind="quarter", end="2025-12-31", start="2025-10-01")]),
        })

    def compare(self):
        return compare_bundles(self.a, self.b)

    def test_common_and_extra_keys(self):
        keys = self.compare()["keys"]
        self.assertEqual(keys["common"], ["capex", "ebit", "revenue", "segment_revenue"])
        self.assertEqual(keys["only_in_a"], ["refinery_runs"])
        self.assertEqual(keys["only_in_b"], ["gross_profit"])

    def test_weights_definitions_and_placement_differences(self):
        result = self.compare()
        self.assertEqual({row["category"] for row in result["weight_diffs"]}, {"statements", "segments"})
        self.assertEqual(result["definition_diffs"], [{"key": "ebit", "definition": ["Ebit", "Operating income"]}])
        self.assertEqual(result["category_placement_diffs"],
                         [{"key": "segment_revenue", "a_categories": ["sector", "segments"], "b_categories": ["segments"]}])

    def test_value_source_and_period_conflicts(self):
        conflicts = {(row["key"], row["type"]) for row in self.compare()["conflicts"]}
        self.assertIn(("ebit", "value"), conflicts)
        self.assertIn(("revenue", "source_differs_same_value"), conflicts)
        self.assertIn(("segment_revenue", "period_mismatch"), conflicts)
        self.assertNotIn(("capex", "value"), conflicts)  # closed only in b: nothing to compare
        self.assertEqual(self.compare()["conflicted_keys"], ["ebit", "segment_revenue"])

    def test_unit_conflict_is_not_reported_as_a_value_conflict(self):
        self.b["records"][1]["observations"] = [observation("40000", unit="SAR_thousands")]
        conflicts = [row for row in self.compare()["conflicts"] if row["key"] == "ebit"]
        self.assertEqual([row["type"] for row in conflicts], ["unit_or_currency"])

    def test_union_closure_counts_each_key_once(self):
        closure = self.compare()["closure"]["on_contract_a"]
        self.assertEqual(closure["keys"], 5)
        self.assertEqual(closure["slots"], 6)
        self.assertEqual(closure["closed_both"], 3)       # revenue, ebit, segment_revenue
        self.assertEqual(closure["closed_only_b"], 1)     # capex
        self.assertEqual(closure["closed_union"], 4)      # never 3 + 3 + 1
        self.assertEqual(closure["slots_closed_union"], 5)

    def test_scores_follow_each_contract_and_union_never_exceeds_the_contract(self):
        scores = {key: Decimal(value) for key, value in self.compare()["scores"].items()}
        self.assertEqual(scores["a_on_a"], Decimal("60") * 2 / 3 + Decimal("20") + Decimal("20") / 2)
        self.assertEqual(scores["union_on_a"], Decimal("60") + Decimal("20") + Decimal("20") / 2)
        self.assertEqual(scores["b_on_b"], Decimal("50") * 3 / 4 + Decimal("50"))
        self.assertLessEqual(scores["union_on_b"], Decimal("100"))

    def test_excluded_fields_leave_the_denominator_and_bundles_must_match(self):
        excluded = copy.deepcopy(self.a)
        excluded["records"][2]["status"] = "excluded"  # capex
        self.assertEqual(contract_score(excluded, {"revenue", "ebit"}), Decimal("60"))
        other = copy.deepcopy(self.b); other["company_id"] = "sa:OTHER"
        with self.assertRaises(ValueError):
            compare_bundles(self.a, other)


if __name__ == "__main__":
    unittest.main()
