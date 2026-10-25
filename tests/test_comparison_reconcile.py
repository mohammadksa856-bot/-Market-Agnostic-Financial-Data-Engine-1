import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.calculations import Calculator
from finengine.comparisons import reconcile_comparisons
from finengine.database import Database
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument


class ComparisonReconcileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.temp.name) / "cmp.sqlite3"))
        self.db.register_company(Company("sa:TST", Market.SA, "TST", "Test", "SAR", country="SA"))
        for key in ("source:a", "source:b"):
            self.db.save_source(SourceDocument("sa:TST", Market.SA, f"https://example.test/{key}", key, "annual",
                                               "2026-01-01", b"{}"), "domain", None)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def year(self, metric, value, fiscal_year, key):
        return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR", f"{fiscal_year}-01-01", f"{fiscal_year}-12-31",
                    PeriodKind.FY, fiscal_year, None, key, f"https://example.test/{key}", f"{fiscal_year + 1}-03-01")

    def publish(self, *facts):
        # as a sync applies one manifest: the batch with its calculated rows
        history = self.db.calculation_history("sa:TST", Calculator.HISTORY_METRICS)
        self.db.publish_batch([*facts, *Calculator().calculate(list(facts), history)])

    def growth(self):
        return {row[0]: Decimal(row[1]) for row in self.db.conn.execute(
            """SELECT period_end,value_decimal FROM data_points WHERE company_id='sa:TST' AND is_current=1
            AND metric_key='revenue_growth'""")}

    def test_restated_input_supersedes_the_comparison(self):
        self.publish(self.year("revenue", "100", 2023, "source:a"), self.year("revenue", "110", 2024, "source:a"))
        self.publish(self.year("revenue", "88", 2023, "source:b"))
        self.assertEqual(self.growth()["2024-12-31"], Decimal("0.1"))  # computed before the restatement
        result = reconcile_comparisons(self.db, "sa:TST")
        self.assertEqual(self.growth()["2024-12-31"], Decimal("110") / Decimal("88") - 1)
        self.assertEqual(result["superseded"], 1)

    def test_comparison_withheld_by_the_final_inputs_is_retired(self):
        self.publish(self.year("revenue", "140", 2023, "source:a"), self.year("revenue", "118", 2024, "source:a"))
        self.publish(self.year("revenue", "118", 2024, "source:b"),
                     self.year("discontinued_operations_income", "-3", 2024, "source:b"))
        reconcile_comparisons(self.db, "sa:TST")
        self.assertNotIn("2024-12-31", self.growth())

    def test_unchanged_comparisons_are_kept(self):
        self.publish(self.year("revenue", "100", 2023, "source:a"), self.year("revenue", "110", 2024, "source:a"))
        before = self.db.conn.execute("SELECT id FROM data_points WHERE metric_key='revenue_growth' "
                                      "AND is_current=1").fetchall()
        self.assertEqual(reconcile_comparisons(self.db, "sa:TST"), {"retired": 0, "superseded": 0, "added": 0})
        after = self.db.conn.execute("SELECT id FROM data_points WHERE metric_key='revenue_growth' "
                                     "AND is_current=1").fetchall()
        self.assertEqual([tuple(r) for r in before], [tuple(r) for r in after])


if __name__ == "__main__":
    unittest.main()
