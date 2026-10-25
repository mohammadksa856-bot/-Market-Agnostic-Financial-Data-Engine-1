import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind


def year(metric, value, fiscal_year, unit="SAR"):
    return Fact("sa:TST", metric, Decimal(value), "SAR", unit, f"{fiscal_year}-01-01", f"{fiscal_year}-12-31",
                PeriodKind.FY, fiscal_year, None, "source:test", "https://example.test", f"{fiscal_year + 1}-03-01")


class CagrHorizonTests(unittest.TestCase):
    def derived(self, facts):
        return {(f.metric, f.period_end): f.value for f in Calculator().calculate(facts)}

    def test_ten_year_compound_growth(self):
        out = self.derived([year("dividends_per_share", "1", 2015, "SAR/share"),
                            year("dividends_per_share", "2", 2025, "SAR/share"),
                            year("operating_cash_flow", "100", 2015), year("operating_cash_flow", "200", 2025)])
        expected = Decimal(2) ** (Decimal(1) / Decimal(10)) - 1
        self.assertAlmostEqual(out[("dividend_cagr_10y", "2025-12-31")], expected)
        self.assertAlmostEqual(out[("operating_cash_flow_cagr_10y", "2025-12-31")], expected)

    def test_only_catalog_horizons_are_emitted(self):
        out = {metric for metric, _ in self.derived([year("operating_cash_flow", "100", 2022),
                                                     year("operating_cash_flow", "120", 2025)])}
        self.assertNotIn("operating_cash_flow_cagr_3y", out)

    def test_ten_years_needs_the_year_ten_years_back(self):
        out = {metric for metric, _ in self.derived([year("revenue", "100", 2016), year("revenue", "150", 2025)])}
        self.assertNotIn("revenue_cagr_10y", out)


if __name__ == "__main__":
    unittest.main()
