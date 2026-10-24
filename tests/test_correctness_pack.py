import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind


def fact(metric, value, kind, end, year, quarter=None, unit="SAR", currency="SAR", start=None):
    if start is None and kind == PeriodKind.FY:
        start = f"{year}-01-01"
    return Fact("sa:9999", metric, Decimal(value), currency, unit, start, end, kind, year, quarter,
                f"doc:{metric}:{end}", "https://example.invalid/report.pdf", end)


def quarter(metric, value, end, start, year, q, **kw):
    return fact(metric, value, PeriodKind.QUARTER, end, year, q, start=start, **kw)


def by_metric(facts):
    return {(item.metric, item.period_end, item.period_kind): item for item in facts}


QUARTERS = [("2025-01-01", "2025-03-31", 2025, 1), ("2025-04-01", "2025-06-30", 2025, 2),
            ("2025-07-01", "2025-09-30", 2025, 3), ("2025-10-01", "2025-12-31", 2025, 4),
            ("2026-01-01", "2026-03-31", 2026, 1)]


class TrailingTwelveMonthTests(unittest.TestCase):
    def ttm(self, values, quarters=QUARTERS[:4], annual=None):
        facts = [quarter("revenue", value, end, start, year, q) for (start, end, year, q), value in zip(quarters, values)]
        end = quarters[-1][1]
        if annual is not None:
            facts.append(fact("revenue", annual, PeriodKind.FY, end, int(end[:4])))
        batch = [item for item in facts if item.period_end == end and item.period_kind == PeriodKind.QUARTER]
        history = [item for item in facts if item not in batch]
        return by_metric(Calculator().calculate(batch, history)).get(("revenue_ttm", end, PeriodKind.TTM))

    def test_four_contiguous_quarters_are_summed(self):
        result = self.ttm(["100"] * 4, QUARTERS[1:])
        self.assertEqual(result.value, Decimal("400"))
        self.assertEqual(result.period_start, "2025-04-01")

    def test_a_missing_quarter_is_never_bridged(self):
        gap = [row for row in QUARTERS if row[1] != "2025-09-30"]
        self.assertIsNone(self.ttm(["100"] * 4, gap))

    def test_a_fiscal_year_window_must_agree_with_the_reported_year_within_rounding(self):
        quarters = ["80104", "80112", "80113", "80118"]  # sum 320447; five whole figures: bound 2.5
        self.assertIsNotNone(self.ttm(quarters, annual="320447"))
        self.assertIsNotNone(self.ttm(quarters, annual="320449"))
        self.assertIsNone(self.ttm(quarters, annual="320451"))
        self.assertIsNotNone(self.ttm(["0.33"] * 4, annual="1.3248"))  # two-decimal quarters
        self.assertIsNone(self.ttm(["0", "0.48", "0", "0"], annual="0.96"))
        self.assertIsNotNone(self.ttm(["0", "0.48", "0", "0"]))  # no fiscal year: nothing to contradict

    def test_rounding_bound_reads_the_stated_precision(self):
        self.assertEqual(Calculator._rounding_half_unit(Decimal("0.3312")), Decimal("0.00005"))
        self.assertEqual(Calculator._rounding_half_unit(Decimal("80104000000")), Decimal("500000"))
        self.assertEqual(Calculator._rounding_half_unit(Decimal("17720000000.00")), Decimal("5000000"))
        self.assertEqual(Calculator._rounding_half_unit(Decimal("0.30")), Decimal("0.005"))
        self.assertEqual(Calculator._rounding_bound([Decimal("0"), Decimal("0.48"), Decimal("0.96")]),
                         Decimal("0.015"))


class FiscalYearViewTests(unittest.TestCase):
    def test_a_fourth_quarter_never_stands_in_for_the_fiscal_year(self):
        batch = [fact("revenue", "400", PeriodKind.FY, "2025-12-31", 2025),
                 fact("net_income", "40", PeriodKind.FY, "2025-12-31", 2025),
                 fact("dividends_paid", "30", PeriodKind.FY, "2025-12-31", 2025),
                 quarter("revenue", "100", "2025-12-31", "2025-10-01", 2025, 4),
                 quarter("dividends_paid", "8", "2025-12-31", "2025-10-01", 2025, 4)]
        out = by_metric(Calculator().calculate(batch, []))
        self.assertEqual(out["net_margin", "2025-12-31", PeriodKind.FY].value, Decimal("0.1"))
        quarter_rows = {metric for metric, _, kind in out if kind == PeriodKind.QUARTER}
        self.assertNotIn("net_margin", quarter_rows)   # no Q4 net income: nothing to divide
        self.assertNotIn("payout_ratio", quarter_rows)  # never Q4 dividends over annual income

    def test_balance_growth_is_annual_only(self):
        def balance(end, year, equity):
            return fact("total_equity", equity, PeriodKind.INSTANT, end, year)
        history = [balance("2024-12-31", 2024, "1000"), fact("revenue", "500", PeriodKind.FY, "2024-12-31", 2024),
                   fact("revenue", "550", PeriodKind.FY, "2025-12-31", 2025)]
        year_end = [balance("2025-12-31", 2025, "1100")]
        out = by_metric(Calculator().calculate(year_end, history))
        self.assertEqual(out["equity_growth", "2025-12-31", PeriodKind.INSTANT].value, Decimal("0.1"))
        interim = [balance("2026-03-31", 2026, "1120")]
        out = by_metric(Calculator().calculate(interim, [*history, *year_end]))
        self.assertNotIn(("equity_growth", "2026-03-31", PeriodKind.INSTANT), out)

    def test_a_year_end_point_in_time_value_stays_in_the_annual_view(self):
        batch = [fact("revenue", "400", PeriodKind.FY, "2025-12-31", 2025),
                 fact("market_cap", "2000", PeriodKind.AS_OF, "2025-12-31", 2025)]
        out = by_metric(Calculator().calculate(batch, []))
        self.assertIn("price_to_sales", {metric for metric, _, _ in out})


if __name__ == "__main__":
    unittest.main()
