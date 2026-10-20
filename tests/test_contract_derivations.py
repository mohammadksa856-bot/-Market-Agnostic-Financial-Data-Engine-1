import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind


def fact(metric, value, kind, end, year, quarter=None, unit="SAR"):
    start = {PeriodKind.FY: f"{year}-01-01", PeriodKind.QUARTER: None}.get(kind)
    return Fact("sa:9999", metric, Decimal(value), "SAR", unit, start, end, kind, year, quarter,
                f"doc:{metric}:{end}", "https://example.invalid/report.pdf", end)


def annual(year, **values):
    return [fact(metric, value, PeriodKind.FY, f"{year}-12-31", year) for metric, value in values.items()]


def balance(year, **values):
    return [fact(metric, value, PeriodKind.INSTANT, f"{year}-12-31", year) for metric, value in values.items()]


def by_metric(facts):
    return {(item.metric, item.period_end): item for item in facts}


class ContractDerivationTests(unittest.TestCase):
    def setUp(self):
        self.facts = [
            *annual(2024, revenue="1000", ebit="200", operating_income="210",
                    income_taxes_and_zakat="-50", income_before_income_taxes_and_zakat="200",
                    weighted_average_shares_diluted="100", operating_cash_flow="300", capex="-100"),
            *annual(2025, revenue="1200", ebit="300", operating_income="330", net_income="150",
                    income_taxes_and_zakat="-120", income_before_income_taxes_and_zakat="300",
                    weighted_average_shares_diluted="120", operating_cash_flow="400", capex="-160",
                    interest_paid="-20", debt_repaid="-30", finance_costs="-10",
                    short_term_lease_expense="4", low_value_lease_expense="1"),
            *balance(2024, total_equity="800", current_debt="50", long_term_debt="150", cash="100",
                     total_assets="1500", current_liabilities="300", current_assets="500",
                     property_plant_equipment="900"),
            *balance(2025, total_equity="900", current_debt="50", long_term_debt="250", cash="100",
                     total_assets="1700", current_liabilities="300", current_assets="600",
                     property_plant_equipment="1100", inventory="60", goodwill="40", intangible_assets="60"),
        ]

    def calculate(self, facts=None):
        return by_metric(Calculator().calculate(facts or self.facts, []))

    def test_returns_on_capital_average_opening_and_closing_balances(self):
        out = self.calculate()
        nopat = Decimal(300) * (1 - Decimal(120) / Decimal(300))
        self.assertEqual(out["nopat", "2025-12-31"].value, nopat)
        # invested capital: 2024 = 800 + 200 - 100 = 900; 2025 = 900 + 300 - 100 = 1100
        self.assertEqual(out["return_on_invested_capital", "2025-12-31"].value, nopat / Decimal(1000))
        self.assertEqual(out["return_on_capital", "2025-12-31"].value, Decimal(300) / Decimal(1100))
        self.assertEqual(out["return_on_capital_employed", "2025-12-31"].value, Decimal(300) / Decimal(1300))
        self.assertEqual(out["fixed_asset_turnover", "2025-12-31"].value, Decimal(1200) / Decimal(1000))
        self.assertEqual(out["working_capital_turnover", "2025-12-31"].value, Decimal(1200) / Decimal(250))
        prior_nopat = Decimal(200) * (1 - Decimal(50) / Decimal(200))
        self.assertEqual(out["incremental_roic", "2025-12-31"].value, (nopat - prior_nopat) / Decimal(200))
        self.assertTrue(out["return_on_invested_capital", "2025-12-31"].is_calculated)

    def test_margin_turnover_coverage_and_per_share_growth(self):
        out = self.calculate()
        self.assertEqual(out["margin_expansion", "2025-12-31"].value,
                         Decimal(330) / Decimal(1200) - Decimal(210) / Decimal(1000))
        self.assertEqual(out["inventory_to_revenue", "2025-12-31"].value, Decimal(60) / Decimal(1200))
        self.assertEqual(out["return_on_tangible_assets", "2025-12-31"].value, Decimal(150) / Decimal(1600))
        self.assertEqual(out["cfo_interest_coverage", "2025-12-31"].value, Decimal(20))
        self.assertEqual(out["debt_service_coverage_proxy", "2025-12-31"].value, Decimal(400) / Decimal(50))
        self.assertEqual(out["fixed_charge_coverage", "2025-12-31"].value, Decimal(305) / Decimal(15))
        self.assertEqual(out["revenue_per_share_growth", "2025-12-31"].value, Decimal(0))
        fcf_now, fcf_prior = Decimal(240) / 120, Decimal(200) / 100
        self.assertEqual(out["free_cash_flow_per_share_growth", "2025-12-31"].value, (fcf_now - fcf_prior) / fcf_prior)

    def test_metrics_are_not_emitted_without_every_input(self):
        out = self.calculate([item for item in self.facts if item.metric not in ("cash", "goodwill", "interest_paid")])
        for metric in ("return_on_invested_capital", "incremental_roic", "return_on_tangible_assets",
                       "cfo_interest_coverage", "debt_service_coverage_proxy"):
            self.assertNotIn((metric, "2025-12-31"), out)
        # Inputs without the opening balance never produce an average-based return.
        out = self.calculate([item for item in self.facts if item.period_end != "2024-12-31"])
        for metric in ("return_on_capital", "return_on_capital_employed", "fixed_asset_turnover", "margin_expansion"):
            self.assertNotIn((metric, "2025-12-31"), out)

    def test_loss_year_emits_no_nopat_or_after_tax_returns(self):
        facts = [item for item in self.facts if not (item.metric == "income_before_income_taxes_and_zakat"
                                                     and item.period_end == "2025-12-31")]
        facts.append(fact("income_before_income_taxes_and_zakat", "-50", PeriodKind.FY, "2025-12-31", 2025))
        out = self.calculate(facts)
        for metric in ("nopat", "return_on_invested_capital", "incremental_roic"):
            self.assertNotIn((metric, "2025-12-31"), out)
        self.assertIn(("return_on_capital_employed", "2025-12-31"), out)  # pre-tax returns are still defined

    def test_quarter_on_quarter_uses_the_previous_fiscal_quarter(self):
        quarters = [
            fact("revenue", "100", PeriodKind.QUARTER, "2026-03-31", 2026, 1),
            fact("revenue", "110", PeriodKind.QUARTER, "2026-06-30", 2026, 2),
            fact("net_income", "-20", PeriodKind.QUARTER, "2026-03-31", 2026, 1),
            fact("net_income", "10", PeriodKind.QUARTER, "2026-06-30", 2026, 2),
            fact("operating_cash_flow", "50", PeriodKind.QUARTER, "2026-03-31", 2026, 1),
            fact("capex", "-30", PeriodKind.QUARTER, "2026-03-31", 2026, 1),
            fact("operating_cash_flow", "60", PeriodKind.QUARTER, "2026-06-30", 2026, 2),
            fact("capex", "-30", PeriodKind.QUARTER, "2026-06-30", 2026, 2),
            # A fiscal-year row in the same year must not stand in for the prior quarter.
            fact("revenue", "400", PeriodKind.FY, "2025-12-31", 2025),
        ]
        out = by_metric(Calculator().calculate(quarters, []))
        self.assertEqual(out["revenue_qoq", "2026-06-30"].value, Decimal("0.1"))
        self.assertEqual(out["net_income_qoq", "2026-06-30"].value, Decimal("1.5"))  # (10 - -20) / abs(-20)
        self.assertEqual(out["free_cash_flow_qoq", "2026-06-30"].value, Decimal("0.5"))  # 30 vs 20
        self.assertNotIn(("revenue_qoq", "2026-03-31"), out)  # no Q4 2025 discrete quarter

    def test_quarter_on_quarter_bridges_fiscal_years(self):
        quarters = [fact("revenue", "80", PeriodKind.QUARTER, "2025-12-31", 2025, 4),
                    fact("revenue", "100", PeriodKind.QUARTER, "2026-03-31", 2026, 1)]
        out = by_metric(Calculator().calculate([quarters[1]], [quarters[0]]))
        self.assertEqual(out["revenue_qoq", "2026-03-31"].value, Decimal("0.25"))


if __name__ == "__main__":
    unittest.main()
