import copy
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.contract_compare import (BUNDLE_VERSION, InvalidBundle, compare_bundles, contract_score,
                                        engine_impact, normalize_bundle, validate_bundle)
from finengine.database import Database
from finengine.domains import CompanyDomainStore
from finengine.contract_compare import export_bundle
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument

ROOT = Path(__file__).resolve().parents[1]


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


class SnapshotValidationTests(unittest.TestCase):
    def setUp(self):
        self.valid = bundle("snapshot", [
            {"key": "statements", "weight": "70", "fields": [field("revenue"), field("ebit")]},
            {"key": "lineage", "weight": "30", "score_only": "0.5"},
        ], {"revenue": ("closed", [observation("100")]), "ebit": ("missing", [])})

    def errors(self, snapshot):
        return validate_bundle(normalize_bundle(snapshot))["errors"]

    def test_a_valid_snapshot_has_no_errors(self):
        self.assertEqual(validate_bundle(self.valid), {"errors": [], "warnings": []})

    def test_each_structural_problem_is_named(self):
        broken = copy.deepcopy(self.valid)
        broken["bundle_version"] = 2
        broken["contract"]["categories"].append({"key": "statements", "weight": "-1", "fields": [field("x"), field("x")]})
        broken["records"] += [{"key": "revenue", "status": "closed", "observations": []},
                              {"key": "ghost", "status": "done",
                               "observations": [{"period_kind": "annual", "period_end": "31/12/2025"}]}]
        errors = " | ".join(self.errors(broken))
        for expected in ("bundle_version must be 1", "category 'statements' appears twice",
                         "weight must be a non-negative number", "key 'x' appears twice",
                         "record 'revenue' appears twice", "status must be one of",
                         "period_kind must be one of", "period_end must be an ISO date", "has no value",
                         "records are not contract keys: ghost", "contract keys have no record"):
            self.assertIn(expected, errors)

    def test_compare_refuses_an_invalid_snapshot_and_lists_why(self):
        broken = copy.deepcopy(self.valid); broken["records"].pop()
        with self.assertRaises(InvalidBundle) as caught:
            compare_bundles(self.valid, broken)
        self.assertTrue(any("no record" in error for error in caught.exception.errors))
        with self.assertRaises(InvalidBundle):
            compare_bundles(self.valid, ["not", "a", "bundle"])

    def test_a_minimal_snapshot_lists_keys_only_and_declares_absence_as_missing(self):
        minimal = {"bundle_version": BUNDLE_VERSION, "label": "codex", "company_id": "sa:TST",
                   "record_default": "missing",
                   "contract": {"categories": [{"key": "statements", "weight": "70", "fields": ["revenue", "ebit"]},
                                               {"key": "lineage", "weight": "30", "score_only": "0.5"}]},
                   "records": [{"key": "ebit", "status": "closed", "observations": [observation("40")]}]}
        self.assertEqual(self.errors(minimal), [])
        result = compare_bundles(self.valid, minimal)
        self.assertEqual(result["definition_diffs"], [])
        self.assertEqual(result["definition_not_provided"], ["ebit", "revenue"])
        self.assertEqual(result["closure"]["on_contract_a"]["closed_union"], 2)
        self.assertEqual(Decimal(result["scores"]["union_on_a"]), Decimal("70") + Decimal("15"))

    def test_weights_not_summing_to_100_are_a_warning(self):
        light = copy.deepcopy(self.valid); light["contract"]["categories"][1]["weight"] = "20"
        self.assertEqual(validate_bundle(light)["warnings"], ["category weights sum to 90, not 100"])


class EngineCorrectionTests(unittest.TestCase):
    def test_conflicts_on_a_corrected_key_are_flagged_not_hidden(self):
        a = bundle("a", [{"key": "statements", "weight": "100", "fields": [field("revenue_ttm"), field("ebit")]}],
                   {"revenue_ttm": ("closed", [observation("400", kind="ttm")]), "ebit": ("closed", [observation("40")])})
        b = copy.deepcopy(a); b["label"] = "b"
        b["records"][0]["observations"][0]["value"] = "390"
        b["records"][1]["observations"][0]["value"] = "41"
        b["engine_corrections"] = [{"id": "ttm-contiguity", "keys": ["revenue_ttm"]}]
        result = compare_bundles(a, b)
        flagged = {item["key"]: item.get("engine_corrections") for item in result["conflicts"]}
        self.assertEqual(flagged, {"revenue_ttm": ["b:ttm-contiguity"], "ebit": None})
        self.assertEqual(result["conflicts_touched_by_engine_corrections"], ["revenue_ttm"])
        self.assertEqual(result["conflicted_keys"], ["ebit", "revenue_ttm"])

    def test_engine_impact_reports_rows_and_scores_without_touching_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = []
            for name, publish in (("before", False), ("after", True)):
                path = Path(temp) / f"{name}.sqlite3"
                db = Database(str(path))
                db.register_company(Company("sa:TST", Market.SA, "TST", "Test Energy", "SAR", isin="SA0000000001",
                                            exchange="Saudi Exchange", country="SA", sector="Energy",
                                            industry="Integrated Oil & Gas", timezone="Asia/Riyadh"))
                source = SourceDocument("sa:TST", Market.SA, "https://example.test/ar", "file:ar", "annual-report",
                                        "2026-03-01", b"{}")
                db.save_source(source, "ar", None)
                db.publish(Fact("sa:TST", "net_income", Decimal("40"), "SAR", "SAR", "2025-01-01", "2025-12-31",
                                PeriodKind.FY, 2025, None, source.source_key, source.source_url, source.filed_at))
                if publish:
                    db.publish(Fact("sa:TST", "revenue", Decimal("400"), "SAR", "SAR", "2025-01-01", "2025-12-31",
                                    PeriodKind.FY, 2025, None, source.source_key, source.source_url, source.filed_at))
                db.close()
                paths.append(path)
            digest = [path.read_bytes() for path in paths]
            result = engine_impact(*paths, label="fix-pack", contract_path=ROOT / "config/factory/18-category-contract.json",
                                   sector_pack_dir=ROOT / "config/factory/sector-packs")
            self.assertEqual(result["rows"], {"removed": 0, "added": 1, "changed": 0})
            self.assertEqual(result["by_metric"], {"revenue": {"removed": 0, "added": 1, "changed": 0}})
            self.assertEqual(result["engine_corrections"], [{"id": "fix-pack", "keys": ["revenue"]}])
            company = result["companies"][0]
            self.assertGreater(Decimal(company["delta"]), 0)
            self.assertIn("financial_statements:revenue", company["keys_closed"])
            self.assertEqual([path.read_bytes() for path in paths], digest)
            unchanged = engine_impact(paths[1], paths[1], label="no-op",
                                      contract_path=ROOT / "config/factory/18-category-contract.json",
                                      sector_pack_dir=ROOT / "config/factory/sector-packs")
            # Companies are scored even when no row changed, so an evaluator-only change is visible.
            self.assertEqual([c["company_id"] for c in unchanged["companies"]], ["sa:TST"])
            self.assertEqual(unchanged["rows"], {"removed": 0, "added": 0, "changed": 0})


class ExportTests(unittest.TestCase):
    def test_export_carries_values_from_every_domain_and_reproduces_the_score(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Database(str(Path(temp) / "export.sqlite3"))
            db.register_company(Company("sa:TST", Market.SA, "TST", "Test Energy", "SAR", isin="SA0000000001",
                                        exchange="Saudi Exchange", country="SA", sector="Energy",
                                        industry="Integrated Oil & Gas", timezone="Asia/Riyadh"))
            source = SourceDocument("sa:TST", Market.SA, "https://example.test/ar", "file:ar", "annual-report",
                                    "2026-03-01", b"{}")
            db.save_source(source, "ar", None)
            db.publish(Fact("sa:TST", "revenue", Decimal("400"), "SAR", "SAR", "2025-01-01", "2025-12-31",
                            PeriodKind.FY, 2025, None, source.source_key, source.source_url, source.filed_at))
            db.publish_company_attribute("sa:TST", "auditor", "PwC", "2025-12-31", source.source_key)
            CompanyDomainStore(db).publish_corporate_action(
                "sa:TST:bonus:2023", "sa:TST", "bonus_shares", "bonus issue", "2023-05-08", source.source_key,
                effective_date="2023-05-08", ratio_numerator=1, ratio_denominator=10, status="completed")
            bundle = export_bundle(db, "sa:TST", label="t", contract_path=ROOT / "config/factory/18-category-contract.json",
                                   sector_pack_dir=ROOT / "config/factory/sector-packs")
            db.close()
        records = {record["key"]: record for record in bundle["records"]}
        self.assertEqual(records["revenue"]["observations"][0]["value"], "400")
        self.assertEqual(records["auditor"]["observations"][0]["value"], '"PwC"')
        action = records["bonus_shares"]["observations"][0]
        self.assertEqual((action["period_end"], action["dimensions"]), ("2023-05-08", "sa:TST:bonus:2023"))
        self.assertIn('"ratio_denominator": "10"', action["value"])
        self.assertEqual(records["isin"]["observations"][0]["value"], "SA0000000001")
        self.assertEqual(validate_bundle(bundle)["errors"], [])
        self.assertEqual(contract_score(bundle, {k for k, r in records.items() if r["status"] == "closed"}),
                         Decimal(bundle["engine_total_score"]))


if __name__ == "__main__":
    unittest.main()
