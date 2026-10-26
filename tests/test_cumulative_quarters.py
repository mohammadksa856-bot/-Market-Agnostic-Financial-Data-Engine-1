import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind

ENDS = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}


def cumulative(metric, value, year, quarter, source="https://example.test/q"):
    kind = PeriodKind.FY if quarter == 4 else PeriodKind.QUARTER if quarter == 1 else PeriodKind.YTD
    return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR", f"{year}-01-01", f"{year}-{ENDS[quarter]}", kind,
                year, None if quarter == 4 else quarter, "source:test", f"{source}{year}{quarter}",
                f"{year}-{ENDS[quarter]}")


def quarter(metric, value, year, number):
    start = {1: "01-01", 2: "04-01", 3: "07-01", 4: "10-01"}[number]
    return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR", f"{year}-{start}", f"{year}-{ENDS[number]}",
                PeriodKind.QUARTER, year, number, "source:test", "https://example.test/reported", f"{year}-12-31")


def year_of(year, ocf, capex):
    return [cumulative(metric, value, year, q) for metric, values in (("operating_cash_flow", ocf), ("capex", capex))
            for q, value in zip((1, 2, 3, 4), values)]


class CumulativeQuarterTests(unittest.TestCase):
    def rows(self, facts):
        return {(f.metric, f.period_end): f for f in Calculator().calculate(facts)}

    def test_discrete_quarters_are_differences_of_cumulative_figures(self):
        out = self.rows(year_of(2025, ("100", "250", "450", "700"), ("-40", "-90", "-150", "-200")))
        self.assertEqual(out[("operating_cash_flow", "2025-06-30")].value, Decimal("150"))
        self.assertEqual(out[("operating_cash_flow", "2025-06-30")].period_start, "2025-04-01")
        self.assertEqual(out[("operating_cash_flow", "2025-12-31")].value, Decimal("250"))
        self.assertEqual(out[("operating_cash_flow", "2025-12-31")].fiscal_quarter, 4)
        self.assertEqual(out[("capex", "2025-09-30")].value, Decimal("-60"))
        self.assertTrue(out[("operating_cash_flow", "2025-09-30")].is_calculated)
        # free cash flow and quarter-on-quarter change follow from the derived quarters
        self.assertEqual(out[("free_cash_flow", "2025-06-30")].value, Decimal("100"))
        self.assertEqual(out[("operating_cash_flow_qoq", "2025-09-30")].value, Decimal("200") / Decimal("150") - 1)

    def test_trailing_twelve_months_and_growth_from_derived_quarters(self):
        out = self.rows([*year_of(2024, ("80", "200", "330", "500"), ("-30", "-60", "-90", "-120")),
                         *year_of(2025, ("100", "250", "450", "700"), ("-40", "-90", "-150", "-200"))])
        self.assertEqual(out[("operating_cash_flow_ttm", "2025-06-30")].value, Decimal("130") + 170 + 100 + 150)
        self.assertEqual(out[("operating_cash_flow_ttm_growth", "2025-12-31")].value, Decimal("700") / 500 - 1)

    def test_a_reported_quarter_is_kept_and_a_gap_is_not_bridged(self):
        facts = [cumulative("operating_cash_flow", "100", 2025, 1), cumulative("operating_cash_flow", "250", 2025, 2),
                 quarter("operating_cash_flow", "149", 2025, 2), cumulative("operating_cash_flow", "700", 2025, 4)]
        calculated = [f for f in Calculator().calculate(facts) if f.metric == "operating_cash_flow"]
        self.assertFalse(any(f.period_end == "2025-06-30" for f in calculated))  # reported 149 stands
        self.assertFalse(any(f.period_end == "2025-12-31" for f in calculated))  # six months is not a quarter

    def test_income_statement_lines_are_not_derived(self):
        facts = [cumulative("revenue", "100", 2025, 1), cumulative("revenue", "250", 2025, 2)]
        self.assertFalse([f for f in Calculator().calculate(facts) if f.metric == "revenue"])

    def test_ttm_growth_on_a_non_positive_base_is_withheld(self):
        out = self.rows([*year_of(2024, ("-80", "-200", "-330", "-500"), ("-30", "-60", "-90", "-120")),
                         *year_of(2025, ("100", "250", "450", "700"), ("-40", "-90", "-150", "-200"))])
        self.assertIn(("operating_cash_flow_ttm", "2025-12-31"), out)
        self.assertNotIn(("operating_cash_flow_ttm_growth", "2025-12-31"), out)


if __name__ == "__main__":
    unittest.main()
