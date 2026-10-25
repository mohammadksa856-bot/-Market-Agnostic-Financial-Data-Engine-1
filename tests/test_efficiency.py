import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind


def fact(metric, value, year, kind=PeriodKind.FY):
    start = f"{year}-01-01" if kind == PeriodKind.FY else None
    return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR", start, f"{year}-12-31", kind, year, None,
                "source:test", "https://example.test", f"{year + 1}-03-01")


def balances(year, inventory, payables, receivables):
    return [fact("inventory", inventory, year, PeriodKind.INSTANT),
            fact("accounts_payable", payables, year, PeriodKind.INSTANT),
            fact("accounts_receivable", receivables, year, PeriodKind.INSTANT)]


class EfficiencyTests(unittest.TestCase):
    def derived(self, facts):
        return {f.metric: f.value for f in Calculator().calculate(facts) if f.period_end == "2025-12-31"}

    def base(self):
        return [*balances(2024, "90", "45", "100"), *balances(2025, "110", "55", "100"),
                fact("revenue", "1000", 2025), fact("cost_of_revenue", "-730", 2025)]

    def test_turnover_and_days_on_average_balances(self):
        out = self.derived(self.base())
        self.assertEqual(out["inventory_turnover"], Decimal("7.3"))
        self.assertEqual(out["days_inventory"], Decimal("50"))
        self.assertEqual(out["payables_turnover"], Decimal("14.6"))
        self.assertEqual(out["days_payables"], Decimal("25"))
        self.assertEqual(out["cash_conversion_cycle"], Decimal("36.5") + Decimal("50") - Decimal("25"))

    def test_without_the_opening_balance_nothing_is_averaged(self):
        out = self.derived([*balances(2025, "110", "55", "100"), fact("cost_of_revenue", "-730", 2025)])
        self.assertNotIn("inventory_turnover", out)

    def test_a_year_with_discontinued_operations_is_withheld(self):
        out = self.derived([*self.base(), fact("discontinued_operations_income", "-5", 2025)])
        self.assertFalse({"inventory_turnover", "days_payables", "receivables_turnover",
                          "cash_conversion_cycle"} & out.keys())

    def test_selling_general_administrative_from_the_catalog_line_names(self):
        out = self.derived([fact("revenue", "1000", 2025), fact("general_and_administrative_expense", "-60", 2025),
                            fact("selling_and_distribution_expense", "-40", 2025)])
        self.assertEqual(out["selling_general_administrative_expense"], Decimal("100"))
        self.assertEqual(out["selling_general_administrative_to_revenue"], Decimal("0.1"))


if __name__ == "__main__":
    unittest.main()


class CapexToDepreciationTests(unittest.TestCase):
    def test_cash_flow_add_back_when_no_income_statement_depreciation(self):
        out = {f.metric: f.value for f in Calculator().calculate(
            [fact("capex", "-90", 2025), fact("depreciation_amortization_cash_flow", "120", 2025)])}
        self.assertEqual(out["capex_to_depreciation_amortization"], Decimal("0.75"))

    def test_income_statement_depreciation_is_preferred(self):
        out = {f.metric: f.value for f in Calculator().calculate(
            [fact("capex", "-90", 2025), fact("depreciation_amortization", "100", 2025),
             fact("depreciation_amortization_cash_flow", "120", 2025)])}
        self.assertEqual(out["capex_to_depreciation"], Decimal("0.9"))


class CapitalReturnBasisTests(unittest.TestCase):
    def run_year(self, discontinued):
        facts = [fact("ebit", "100", 2025), fact("income_before_income_taxes_and_zakat", "100", 2025),
                 fact("income_taxes_and_zakat", "-20", 2025), fact("revenue", "1000", 2025)]
        for year, equity in ((2024, "900"), (2025, "1100")):
            facts += [fact("total_equity", equity, year, PeriodKind.INSTANT),
                      fact("current_debt", "0", year, PeriodKind.INSTANT),
                      fact("long_term_debt", "0", year, PeriodKind.INSTANT),
                      fact("cash", "0", year, PeriodKind.INSTANT)]
        if discontinued:
            facts.append(fact("discontinued_operations_income", "-5", 2025))
        return {f.metric: f.value for f in Calculator().calculate(facts, industry="Chemicals")
                if f.period_end == "2025-12-31"}

    def test_return_on_invested_capital_on_one_basis(self):
        out = self.run_year(False)
        self.assertEqual(out["nopat"], Decimal("80"))
        self.assertEqual(out["return_on_invested_capital"], Decimal("0.08"))

    def test_withheld_when_the_year_reports_discontinued_operations(self):
        out = self.run_year(True)
        self.assertEqual(out["nopat"], Decimal("80"))
        self.assertNotIn("return_on_invested_capital", out)
