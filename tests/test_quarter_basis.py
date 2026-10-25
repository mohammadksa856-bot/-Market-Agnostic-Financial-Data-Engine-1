import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind


def row(metric, value, start, end, kind, quarter, unit="SAR"):
    return Fact("sa:TST", metric, Decimal(value), "SAR", unit, start, end, kind, 2025, quarter,
                "source:test", "https://example.test", "2025-08-01")


Q1 = ("2025-01-01", "2025-03-31", PeriodKind.QUARTER, 1)
Q2 = ("2025-04-01", "2025-06-30", PeriodKind.QUARTER, 2)
H1 = ("2025-01-01", "2025-06-30", PeriodKind.YTD, 2)


class QuarterBasisTests(unittest.TestCase):
    def qoq(self, facts):
        return {(f.metric, f.period_end): f.value for f in Calculator().calculate(facts)
                if f.metric == "revenue_qoq"}

    def test_quarters_that_add_up_to_the_year_to_date_are_compared(self):
        out = self.qoq([row("revenue", "100", *Q1), row("revenue", "120", *Q2), row("revenue", "220", *H1)])
        self.assertEqual(out[("revenue_qoq", "2025-06-30")], Decimal("0.2"))

    def test_re_presented_quarters_are_not_compared(self):
        # Q1 as first reported; Q2 and the half year after a business moved to discontinued operations
        out = self.qoq([row("revenue", "100", *Q1), row("revenue", "80", *Q2), row("revenue", "170", *H1)])
        self.assertNotIn(("revenue_qoq", "2025-06-30"), out)

    def test_rounding_of_printed_figures_is_not_a_basis_change(self):
        out = self.qoq([row("revenue", "100", *Q1), row("revenue", "120", *Q2), row("revenue", "221", *H1)])
        self.assertIn(("revenue_qoq", "2025-06-30"), out)

    def test_without_a_year_to_date_figure_the_change_is_kept(self):
        out = self.qoq([row("revenue", "100", *Q1), row("revenue", "120", *Q2)])
        self.assertEqual(out[("revenue_qoq", "2025-06-30")], Decimal("0.2"))

    def test_per_share_figures_are_not_held_to_additivity(self):
        facts = [row("eps_diluted", "0.20", *Q1, "SAR/share"), row("eps_diluted", "0.25", *Q2, "SAR/share"),
                 row("eps_diluted", "0.50", *H1, "SAR/share")]
        out = {f.metric for f in Calculator().calculate(facts)}
        self.assertIn("eps_qoq", out)


if __name__ == "__main__":
    unittest.main()
