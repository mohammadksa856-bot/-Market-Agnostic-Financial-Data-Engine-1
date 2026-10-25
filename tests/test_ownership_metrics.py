import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.database import Database
from finengine.domains import CompanyDomainStore
from finengine.models import Company, Market, SourceDocument
from finengine.ownership_metrics import ownership_metrics

IMPORTS = Path(__file__).resolve().parents[1] / "data" / "imports"


def row(key, pct, ownership_type="direct", holder_type="corporate", date="2025-12-31", shares=None, **metadata):
    return {"holder_key": key, "holder_name": key, "holder_type": holder_type, "ownership_type": ownership_type,
            "as_of_date": date, "shares": shares, "ownership_pct": None if pct is None else str(pct),
            "country": None, "metadata_json": json.dumps(metadata)}


def values(rows):
    return {key: [item["value"] for item in items] for key, items in ownership_metrics(rows).items()}


def manifest_rows(name):
    return [{**item, "metadata_json": json.dumps(item.get("metadata", {}))}
            for item in json.loads((IMPORTS / name).read_text(encoding="utf-8"))["ownership_positions"]]


class OwnershipMetricTests(unittest.TestCase):
    def test_named_holders_of_a_class_are_not_a_class_total(self):
        rows = [row("fund_a", "0.10", holder_type="institutional"), row("fund_b", "0.05", holder_type="institutional"),
                row("public", "0.85", "free_float", "public")]
        self.assertNotIn("institutional_ownership", values(rows))

    def test_class_total_row_overlaps_the_partition(self):
        rows = [row("parent", "0.7", holder_type="corporate_strategic"), row("public", "0.3", "free_float", "public"),
                row("foreign", "0.06", "aggregate", "foreign")]
        result = values(rows)
        self.assertEqual(result["foreign_ownership"], [Decimal("0.06")])
        self.assertEqual(result["strategic_ownership"], [Decimal("0.7")])  # the overlay is not in the partition

    def test_complete_holder_list_is_a_class_total_only_when_every_row_says_so(self):
        insiders = [row("ceo", "0.004", holder_type="insider", class_complete=True),
                    row("director", "0.001", holder_type="insider", class_complete=True)]
        self.assertEqual(values(insiders)["insider_ownership"], [Decimal("0.005")])
        insiders[1] = row("director", "0.001", holder_type="insider")
        self.assertNotIn("insider_ownership", values(insiders))
        # shares without a percentage do not give a ratio
        self.assertNotIn("insider_ownership", values([row("ceo", None, holder_type="insider", shares="80000",
                                                          class_complete=True)]))

    def test_strategic_ownership_needs_a_reconciled_partition(self):
        rows = [row("pif", "0.62", holder_type="sovereign_and_strategic"), row("public", "0.38", "free_float", "public")]
        self.assertEqual(values(rows)["strategic_ownership"], [Decimal("0.62")])
        self.assertNotIn("strategic_ownership", values(rows[:1]))  # 62% of a partition that is not 100%
        # a pooled row that is neither free float nor treasury may hide a strategic stake
        rows[1] = row("other", "0.38", "other_holders", "mixed")
        self.assertNotIn("strategic_ownership", values(rows))

    def test_government_is_not_counted_as_strategic(self):
        rows = [row("state", "0.80", holder_type="government"),
                row("other_strategic", "0.18", "indirect_and_other", "sovereign_and_strategic"),
                row("public", "0.02", "free_float", "public")]
        result = values(rows)
        self.assertEqual(result["strategic_ownership"], [Decimal("0.18")])
        self.assertEqual(result["government_ownership"], [Decimal("0.80")])

    def test_top_n_needs_n_named_holders_that_no_pooled_holder_can_outrank(self):
        named = [row(f"h{i}", pct) for i, pct in enumerate(["0.30", "0.20", "0.15", "0.10", "0.08", "0.05"])]
        rows = named + [row("public", "0.12", "free_float", "public")]
        self.assertNotIn("top_5_shareholder_concentration", values(rows))  # one public holder could hold 12% > 8%
        rows = named + [row("public", "0.07", "free_float", "public"), row("treasury", "0.05", "treasury", "company")]
        result = values(rows)
        self.assertEqual(result["top_5_shareholder_concentration"], [Decimal("0.83")])
        self.assertNotIn("top_10_shareholder_concentration", result)  # six named holders only
        self.assertEqual(values(named[:5] + [row("h5", "0.17")])["top_10_shareholder_concentration"],
                         [Decimal("1.00")])  # every holder is named
        self.assertNotIn("top_5_shareholder_concentration", values(named[:5]))  # 83% is not a full partition

    def test_major_holder_change_compares_the_same_holder_across_two_dates(self):
        rows = [row("pif", "0.62", date="2025-12-31"), row("pif", "0.60", date="2025-06-30"),
                row("small", "0.02", date="2025-12-31"), row("small", "0.03", date="2025-06-30"),
                row("new", "0.10", date="2025-12-31")]
        changes = ownership_metrics(rows)["major_holder_change"]
        self.assertEqual([(item["holder_key"], item["value"]) for item in changes], [("pif", Decimal("0.02"))])
        self.assertNotIn("major_holder_change", values(rows[:1]))

    def test_controlling_stake_moving_between_holders_in_reconciled_partitions(self):
        rows = [row("pif", "0.7", holder_type="government", date="2019-12-31"),
                row("public", "0.3", "free_float", "public", date="2019-12-31"),
                row("aramco", "0.7", holder_type="corporate_strategic"), row("public", "0.3", "free_float", "public")]
        changes = {item["holder_key"]: item["value"] for item in ownership_metrics(rows)["major_holder_change"]}
        self.assertEqual(changes, {"aramco": Decimal("0.7"), "pif": Decimal("-0.7"), "public": Decimal("0")})

    def test_ownership_concentration_is_never_emitted_until_defined(self):
        rows = [row("only", "1")]
        self.assertNotIn("ownership_concentration", values(rows))
        self.assertIn("top_5_shareholder_concentration", values(rows))

    def test_aramco_and_sabic_archived_holders(self):
        aramco = values(manifest_rows("aramco-2025-annual-metrics.json"))
        self.assertEqual(aramco["strategic_ownership"], [Decimal("0.16")])
        self.assertEqual(aramco["government_ownership"], [Decimal("0.8148")])
        for key in ("institutional_ownership", "retail_ownership", "insider_ownership", "foreign_ownership",
                    "top_5_shareholder_concentration", "top_10_shareholder_concentration", "major_holder_change"):
            self.assertNotIn(key, aramco)  # one named holder plus pooled rows determine none of these
        sabic = values(manifest_rows("sabic-2025-company-esg-market.json"))
        self.assertEqual((sabic["foreign_ownership"], sabic["strategic_ownership"]),
                         ([Decimal("0.0621")], [Decimal("0.7")]))
        self.assertNotIn("top_5_shareholder_concentration", sabic)


class OwnershipCompletenessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.temp.name) / "ownership.sqlite3"))
        self.db.register_company(Company("sa:TST", Market.SA, "TST", "Test", "SAR", country="SA"))
        self.source = SourceDocument("sa:TST", Market.SA, "https://example.test/holders", "source:holders",
                                     "annual-results", "2026-03-01", b"{}")
        self.db.save_source(self.source, "domain", None)
        self.store = CompanyDomainStore(self.db)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def missing(self):
        result = self.store.refresh_catalog_completeness("sa:TST")
        return set(next(row for row in result["categories"] if row["category"] == "ownership")["missing"])

    def test_completeness_counts_only_determined_keys(self):
        publish = lambda key, pct, kind, holder_type: self.store.publish_ownership_position(
            "sa:TST", key, key, kind, "2025-12-31", self.source.source_key, ownership_pct=pct, holder_type=holder_type)
        for index, pct in enumerate(["0.40", "0.20", "0.10", "0.08", "0.06"]):
            publish(f"holder_{index}", pct, "direct", "strategic" if index == 0 else "institutional")
        publish("public", "0.16", "free_float", "public")
        missing = self.missing()
        self.assertNotIn("strategic_ownership", missing)
        self.assertIn("top_5_shareholder_concentration", missing)  # 16% public float could hold a 6%+ holder
        self.assertIn("institutional_ownership", missing)  # named institutions are not the class total
        publish("public", "0.05", "free_float", "public")  # restated float
        publish("holder_5", "0.11", "direct", "corporate")
        missing = self.missing()
        self.assertNotIn("top_5_shareholder_concentration", missing)
        self.assertIn("ownership_concentration", missing)


if __name__ == "__main__":
    unittest.main()
