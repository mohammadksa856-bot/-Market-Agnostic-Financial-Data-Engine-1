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

    def test_a_derived_quarter_follows_the_restated_cumulative_figure(self):
        nine = Fact("sa:TST", "capex", Decimal("-60"), "SAR", "SAR", "2025-01-01", "2025-09-30", PeriodKind.YTD,
                    2025, 3, "source:a", "https://example.test/source:a", "2025-11-01")
        self.publish(self.year("capex", "-80", 2025, "source:a"), nine)
        self.publish(self.year("capex", "-85", 2025, "source:b"))  # the year restated (e.g. intangibles added)
        reconcile_comparisons(self.db, "sa:TST")
        rows = self.db.conn.execute(
            """SELECT value_decimal FROM data_points WHERE company_id='sa:TST' AND is_current=1 AND metric_key='capex'
            AND period_kind='quarter' AND period_end='2025-12-31'""").fetchall()
        self.assertEqual([Decimal(row[0]) for row in rows], [Decimal("-25")])

    def test_calculated_free_cash_flow_follows_a_restated_capex(self):
        self.publish(self.year("operating_cash_flow", "100", 2025, "source:a"), self.year("capex", "-80", 2025, "source:a"))
        self.publish(self.year("capex", "-85", 2025, "source:b"))  # filed alone: the batch cannot recompute it
        reconcile_comparisons(self.db, "sa:TST")
        rows = self.db.conn.execute(
            """SELECT value_decimal FROM data_points WHERE company_id='sa:TST' AND is_current=1
            AND metric_key='free_cash_flow' AND period_kind='fy'""").fetchall()
        self.assertEqual([Decimal(row[0]) for row in rows], [Decimal("15")])

    def test_free_cash_flow_growth_survives_the_recomputation_of_free_cash_flow(self):
        self.publish(self.year("operating_cash_flow", "100", 2024, "source:a"), self.year("capex", "-80", 2024, "source:a"),
                     self.year("operating_cash_flow", "120", 2025, "source:a"), self.year("capex", "-90", 2025, "source:a"))
        result = reconcile_comparisons(self.db, "sa:TST")
        self.assertEqual(result["retired"], 0)
        self.assertEqual(self.current("free_cash_flow_growth"), [Decimal("30") / Decimal("20") - 1])

    def current(self, metric):
        return [Decimal(row[0]) for row in self.db.conn.execute(
            "SELECT value_decimal FROM data_points WHERE company_id='sa:TST' AND is_current=1 AND metric_key=?",
            (metric,))]

    def test_a_ratio_on_a_restated_input_is_refreshed(self):
        self.publish(self.year("revenue", "200", 2025, "source:a"), self.year("operating_cash_flow", "100", 2025, "source:a"),
                     self.year("capex", "-80", 2025, "source:a"))
        self.assertEqual(self.current("fcf_margin"), [Decimal("0.1")])
        self.publish(self.year("capex", "-85", 2025, "source:b"))
        self.assertEqual(reconcile_comparisons(self.db, "sa:TST")["refreshed"] >= 1, True)
        self.assertEqual(self.current("fcf_margin"), [Decimal("15") / Decimal("200")])

    def test_a_margin_across_two_filings_of_re_presented_lines_is_kept(self):
        self.publish(self.year("revenue", "200", 2025, "source:a"), self.year("gross_profit", "50", 2025, "source:a"))
        self.publish(self.year("revenue", "180", 2025, "source:b"))  # a later filing re-presents revenue only
        # the margin as computed within the first filing
        self.db.conn.execute("UPDATE data_points SET value_decimal='0.25' WHERE metric_key='gross_margin' AND is_current=1")
        reconcile_comparisons(self.db, "sa:TST")
        self.assertEqual(self.current("gross_margin"), [Decimal("0.25")])

    def test_unchanged_comparisons_are_kept(self):
        self.publish(self.year("revenue", "100", 2023, "source:a"), self.year("revenue", "110", 2024, "source:a"))
        before = self.db.conn.execute("SELECT id FROM data_points WHERE metric_key='revenue_growth' "
                                      "AND is_current=1").fetchall()
        self.assertEqual(reconcile_comparisons(self.db, "sa:TST"), {"retired": 0, "superseded": 0, "added": 0, "refreshed": 0})
        after = self.db.conn.execute("SELECT id FROM data_points WHERE metric_key='revenue_growth' "
                                     "AND is_current=1").fetchall()
        self.assertEqual([tuple(r) for r in before], [tuple(r) for r in after])


if __name__ == "__main__":
    unittest.main()
