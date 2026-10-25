import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind

AR2024 = "https://example.test/annual-report-2024.pdf"
AR2025 = "https://example.test/annual-report-2025.pdf"


def year(metric, value, fiscal_year, url):
    return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR", f"{fiscal_year}-01-01", f"{fiscal_year}-12-31",
                PeriodKind.FY, fiscal_year, None, "source:test", url, f"{fiscal_year + 1}-03-01")


class PresentationBasisTests(unittest.TestCase):
    def derived(self, facts):
        return {(f.metric, f.period_end): f.value for f in Calculator().calculate(facts)}

    def test_line_re_presented_for_discontinued_operations_is_not_compared_across_filings(self):
        # 2024 as re-presented in the 2025 report; 2023 still as first published
        out = self.derived([year("revenue", "140", 2023, AR2024), year("revenue", "118", 2024, AR2025),
                            year("discontinued_operations_income", "-3", 2024, AR2025)])
        self.assertNotIn(("revenue_growth", "2024-12-31"), out)

    def test_comparative_from_the_same_filing_is_compared(self):
        out = self.derived([year("revenue", "118", 2024, AR2025), year("revenue", "116", 2025, AR2025),
                            year("discontinued_operations_income", "-24", 2025, AR2025)])
        self.assertAlmostEqual(out[("revenue_growth", "2025-12-31")], Decimal("116") / Decimal("118") - 1)

    def test_totals_are_not_re_presented(self):
        out = self.derived([year("net_income", "100", 2023, AR2024), year("net_income", "80", 2024, AR2025),
                            year("discontinued_operations_income", "-3", 2024, AR2025)])
        self.assertEqual(out[("net_income_growth", "2024-12-31")], Decimal("-0.2"))

    def test_without_discontinued_operations_filings_are_compared(self):
        out = self.derived([year("revenue", "100", 2023, AR2024), year("revenue", "110", 2024, AR2025)])
        self.assertEqual(out[("revenue_growth", "2024-12-31")], Decimal("0.1"))

    def test_compound_growth_spanning_a_discontinued_operation_is_withheld(self):
        facts = [year("revenue", "100", 2021, AR2024), year("revenue", "90", 2022, AR2024),
                 year("discontinued_operations_income", "1", 2022, AR2024),
                 year("revenue", "120", 2024, AR2025), year("eps_diluted", "2", 2021, AR2024),
                 year("eps_diluted", "3", 2024, AR2025)]
        out = self.derived(facts)
        self.assertNotIn(("revenue_cagr_3y", "2024-12-31"), out)
        self.assertIn(("eps_cagr_3y", "2024-12-31"), out)


if __name__ == "__main__":
    unittest.main()
