import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind

INDUSTRY = "Integrated Oil & Gas"


def fact(metric, value, kind, end, year, quarter=None, unit="SAR", currency="SAR", start=None):
    if start is None and kind == PeriodKind.FY:
        start = f"{year}-01-01"
    return Fact("sa:9999", metric, Decimal(value), currency, unit, start, end, kind, year, quarter,
                f"doc:{metric}:{end}", "https://example.invalid/report.pdf", end)


def annual(year, **values):
    shares = {"weighted_average_shares_diluted", "weighted_average_shares_basic"}
    return [fact(metric, value, PeriodKind.FY, f"{year}-12-31", year, unit="shares" if metric in shares else "SAR")
            for metric, value in values.items()]


def balance(year, end=None, **values):
    return [fact(metric, value, PeriodKind.INSTANT, end or f"{year}-12-31", year) for metric, value in values.items()]


def quarter(metric, value, end, start, year, q, **kw):
    return fact(metric, value, PeriodKind.QUARTER, end, year, q, start=start, **kw)


def by_metric(facts):
    return {(item.metric, item.period_end): item for item in facts}


def without(facts, metric, end):
    return [item for item in facts if not (item.metric == metric and item.period_end == end)]


def replaced(facts, metric, end, value, **kw):
    original = next(item for item in facts if item.metric == metric and item.period_end == end)
    return [*without(facts, metric, end),
            fact(metric, value, original.period_kind, end, original.fiscal_year, unit=kw.get("unit", original.unit),
                 currency=kw.get("currency", original.currency), start=original.period_start)]


FY_METRICS = ("nopat", "return_on_invested_capital", "return_on_capital_employed",
              "fixed_asset_turnover", "working_capital_turnover", "incremental_roic", "margin_expansion",
              "inventory_to_revenue", "return_on_tangible_assets", "cfo_interest_coverage",
              "debt_service_coverage_proxy", "revenue_per_share_growth", "free_cash_flow_per_share_growth")


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
            *balance(2023, total_equity="700", current_debt="50", long_term_debt="150", cash="100",
                     total_assets="1400", current_liabilities="300", current_assets="450",
                     property_plant_equipment="800"),
            *balance(2024, total_equity="800", current_debt="50", long_term_debt="150", cash="100",
                     total_assets="1500", current_liabilities="300", current_assets="500",
                     property_plant_equipment="900"),
            *balance(2025, total_equity="900", current_debt="50", long_term_debt="250", cash="100",
                     total_assets="1700", current_liabilities="300", current_assets="600",
                     property_plant_equipment="1100", inventory="60", goodwill="40", intangible_assets="60"),
        ]

    def calculate(self, facts=None, industry=INDUSTRY):
        return by_metric(Calculator().calculate(self.facts if facts is None else facts, [], industry=industry))

    def assertNone(self, out, *metrics, end="2025-12-31"):
        for metric in metrics:
            self.assertNotIn((metric, end), out, metric)

    # ── positive path

    def test_returns_use_opening_and_closing_fiscal_year_balances(self):
        out = self.calculate()
        nopat = Decimal(300) * (1 - Decimal(120) / Decimal(300))
        self.assertEqual(out["nopat", "2025-12-31"].value, nopat)
        # invested capital: opening 2024-12-31 = 800 + 200 - 100 = 900; closing = 900 + 300 - 100 = 1100
        self.assertEqual(out["return_on_invested_capital", "2025-12-31"].value, nopat / Decimal(1000))
        self.assertEqual(out["return_on_capital_employed", "2025-12-31"].value, Decimal(300) / Decimal(1300))
        self.assertEqual(out["fixed_asset_turnover", "2025-12-31"].value, Decimal(1200) / Decimal(1000))
        self.assertEqual(out["working_capital_turnover", "2025-12-31"].value, Decimal(1200) / Decimal(250))
        prior_nopat = Decimal(200) * (1 - Decimal(50) / Decimal(200))
        self.assertEqual(out["incremental_roic", "2025-12-31"].value, (nopat - prior_nopat) / Decimal(200))
        self.assertEqual(out["margin_expansion", "2025-12-31"].value,
                         Decimal(330) / Decimal(1200) - Decimal(210) / Decimal(1000))
        self.assertEqual(out["inventory_to_revenue", "2025-12-31"].value, Decimal(60) / Decimal(1200))
        self.assertEqual(out["return_on_tangible_assets", "2025-12-31"].value, Decimal(150) / Decimal(1600))
        self.assertEqual(out["cfo_interest_coverage", "2025-12-31"].value, Decimal(20))
        self.assertEqual(out["debt_service_coverage_proxy", "2025-12-31"].value, Decimal(400) / Decimal(50))
        self.assertEqual(out["revenue_per_share_growth", "2025-12-31"].value, Decimal(0))
        self.assertEqual(out["free_cash_flow_per_share_growth", "2025-12-31"].value,
                         (Decimal(240) / 120) / (Decimal(200) / 100) - 1)
        self.assertIn("proxy, not the lender DSCR", out["debt_service_coverage_proxy", "2025-12-31"].calculation)

    # ── 1. opening/closing balances, never an interim balance

    def test_interim_balance_never_replaces_a_year_end_balance(self):
        interim = balance(2025, end="2025-06-30", total_equity="5000", current_debt="5000", long_term_debt="5000",
                          cash="1", total_assets="99999", current_liabilities="1", current_assets="99999",
                          property_plant_equipment="99999")
        out = self.calculate([*self.facts, *interim])
        self.assertEqual(out["return_on_capital_employed", "2025-12-31"].value, Decimal(300) / Decimal(1300))
        # Without the opening year-end balance the interim one is not used as a substitute.
        opening_removed = [item for item in [*self.facts, *interim] if item.period_end != "2024-12-31"
                           or item.period_kind != PeriodKind.INSTANT]
        self.assertNone(self.calculate(opening_removed), "return_on_invested_capital",
                        "return_on_capital_employed", "fixed_asset_turnover", "working_capital_turnover")

    # ── 2. currencies, units and scopes are never mixed

    def test_a_balance_in_another_currency_blocks_the_average(self):
        facts = replaced(self.facts, "total_equity", "2024-12-31", "800", unit="USD", currency="USD")
        out = self.calculate(facts)
        self.assertNone(out, "return_on_invested_capital", "incremental_roic")
        self.assertIn(("return_on_capital_employed", "2025-12-31"), out)
        facts = replaced(self.facts, "revenue", "2024-12-31", "1000", unit="SAR thousands")
        self.assertNone(self.calculate(facts), "margin_expansion", "revenue_per_share_growth")

    # ── 3. a missing debt line is not a zero; a reported zero is

    def test_missing_debt_component_is_not_zero(self):
        out = self.calculate(without(self.facts, "long_term_debt", "2024-12-31"))
        self.assertNone(out, "return_on_invested_capital", "incremental_roic")
        out = self.calculate(replaced(self.facts, "long_term_debt", "2024-12-31", "0"))
        nopat = Decimal(300) * (1 - Decimal(120) / Decimal(300))
        self.assertEqual(out["return_on_invested_capital", "2025-12-31"].value, nopat / ((Decimal(750) + 1100) / 2))

    # ── 4. tax keeps its sign; loss years and implausible rates withhold after-tax metrics

    def test_tax_benefit_loss_year_and_implausible_rate_withhold_nopat(self):
        for label, facts in (
            ("benefit", replaced(self.facts, "income_taxes_and_zakat", "2025-12-31", "120")),
            ("loss", replaced(self.facts, "income_before_income_taxes_and_zakat", "2025-12-31", "-50")),
            ("rate >= 1", replaced(self.facts, "income_taxes_and_zakat", "2025-12-31", "-300")),
        ):
            with self.subTest(label):
                out = self.calculate(facts)
                self.assertNone(out, "nopat", "return_on_invested_capital", "incremental_roic")
                self.assertIn(("return_on_capital_employed", "2025-12-31"), out)  # pre-tax return stays defined
        out = self.calculate(replaced(self.facts, "income_taxes_and_zakat", "2025-12-31", "0"))
        self.assertEqual(out["nopat", "2025-12-31"].value, Decimal(300))  # a reported zero tax is a real rate

    # ── 5. explicit sector eligibility

    def test_banks_insurers_and_unclassified_issuers_are_excluded(self):
        for industry in ("Banks", "Insurance", "Reinsurance", "Takaful Insurance", None, ""):
            with self.subTest(industry):
                self.assertNone(self.calculate(industry=industry), *FY_METRICS)

    # ── 6. working-capital turnover needs positive, material working capital

    def test_working_capital_turnover_withheld_for_negative_or_near_zero_balance(self):
        negative = replaced(self.facts, "current_assets", "2025-12-31", "250")  # closing WC = -50
        tiny = replaced(replaced(self.facts, "current_assets", "2024-12-31", "330"),
                        "current_assets", "2025-12-31", "330")  # average WC 30 < 5% of 1200
        for facts in (negative, tiny):
            self.assertNone(self.calculate(facts), "working_capital_turnover")

    # ── 7. one share basis across years

    def test_per_share_growth_never_mixes_share_bases(self):
        mixed = [*without(self.facts, "weighted_average_shares_diluted", "2024-12-31"),
                 *annual(2024, weighted_average_shares_basic="100")]
        self.assertNone(self.calculate(mixed), "revenue_per_share_growth", "free_cash_flow_per_share_growth")
        basic = [item for item in self.facts if item.metric != "weighted_average_shares_diluted"]
        basic += [*annual(2024, weighted_average_shares_basic="100"), *annual(2025, weighted_average_shares_basic="125")]
        out = self.calculate(basic)
        self.assertEqual(out["revenue_per_share_growth", "2025-12-31"].value,
                         (Decimal(1200) / 125) / (Decimal(1000) / 100) - 1)
        self.assertIn("weighted_average_shares_basic", out["revenue_per_share_growth", "2025-12-31"].calculation)
        negative_prior = replaced(self.facts, "operating_cash_flow", "2024-12-31", "50")  # prior FCF = -50
        self.assertNone(self.calculate(negative_prior), "free_cash_flow_per_share_growth")

    # ── 8. debt-service proxy keeps principal when interest is zero

    def test_debt_service_proxy_with_zero_interest_keeps_principal(self):
        out = self.calculate(replaced(self.facts, "interest_paid", "2025-12-31", "0"))
        self.assertEqual(out["debt_service_coverage_proxy", "2025-12-31"].value, Decimal(400) / Decimal(30))
        self.assertNone(out, "cfo_interest_coverage")
        self.assertNone(self.calculate(without(self.facts, "debt_repaid", "2025-12-31")), "debt_service_coverage_proxy")

    # ── 10. definitions that need an accounting decision are never emitted

    def test_definition_pending_metrics_are_never_emitted(self):
        out = self.calculate()
        for metric in Calculator.DEFINITION_PENDING:
            self.assertNotIn((metric, "2025-12-31"), out)

    def test_missing_inputs_emit_nothing(self):
        out = self.calculate([item for item in self.facts if item.metric not in ("cash", "goodwill", "interest_paid")])
        self.assertNone(out, "return_on_invested_capital", "incremental_roic", "return_on_tangible_assets",
                        "cfo_interest_coverage", "debt_service_coverage_proxy")

    # ── quarter on quarter

    def test_quarter_change_uses_the_contiguous_previous_quarter(self):
        rows = [
            quarter("revenue", "100", "2026-03-31", "2026-01-01", 2026, 1),
            quarter("revenue", "110", "2026-06-30", "2026-04-01", 2026, 2),
            quarter("operating_cash_flow", "50", "2026-03-31", "2026-01-01", 2026, 1),
            quarter("capex", "-30", "2026-03-31", "2026-01-01", 2026, 1),
            quarter("operating_cash_flow", "60", "2026-06-30", "2026-04-01", 2026, 2),
            quarter("capex", "-30", "2026-06-30", "2026-04-01", 2026, 2),
            quarter("net_income", "-20", "2026-03-31", "2026-01-01", 2026, 1),
            quarter("net_income", "10", "2026-06-30", "2026-04-01", 2026, 2),
            fact("revenue", "400", PeriodKind.FY, "2025-12-31", 2025),
        ]
        out = by_metric(Calculator().calculate(rows, []))
        self.assertEqual(out["revenue_qoq", "2026-06-30"].value, Decimal("0.1"))
        self.assertEqual(out["free_cash_flow_qoq", "2026-06-30"].value, Decimal("0.5"))  # 30 vs 20
        self.assertNotIn(("net_income_qoq", "2026-06-30"), out)  # non-positive base: DEFINITION_PENDING
        self.assertNotIn(("revenue_qoq", "2026-03-31"), out)  # no Q4 2025 discrete quarter

    def test_quarter_change_rejects_gaps_and_currency_mixing(self):
        gap = [quarter("revenue", "100", "2025-12-31", "2025-10-01", 2025, 4),
               quarter("revenue", "110", "2026-06-30", "2026-04-01", 2026, 2)]
        self.assertNotIn(("revenue_qoq", "2026-06-30"), by_metric(Calculator().calculate(gap, [])))
        mixed = [quarter("revenue", "100", "2026-03-31", "2026-01-01", 2026, 1, unit="USD", currency="USD"),
                 quarter("revenue", "110", "2026-06-30", "2026-04-01", 2026, 2)]
        self.assertNotIn(("revenue_qoq", "2026-06-30"), by_metric(Calculator().calculate(mixed, [])))
        bridge = [quarter("revenue", "80", "2025-12-31", "2025-10-01", 2025, 4)]
        out = by_metric(Calculator().calculate([quarter("revenue", "100", "2026-03-31", "2026-01-01", 2026, 1)], bridge))
        self.assertEqual(out["revenue_qoq", "2026-03-31"].value, Decimal("0.25"))


class TrailingTwelveMonthTests(unittest.TestCase):
    QUARTERS = [("2025-01-01", "2025-03-31", 2025, 1), ("2025-04-01", "2025-06-30", 2025, 2),
                ("2025-07-01", "2025-09-30", 2025, 3), ("2025-10-01", "2025-12-31", 2025, 4),
                ("2026-01-01", "2026-03-31", 2026, 1)]

    def ttm(self, quarters, batch_end):
        facts = [quarter("revenue", "100", end, start, year, q) for start, end, year, q in quarters]
        batch = [item for item in facts if item.period_end == batch_end]
        history = [item for item in facts if item.period_end != batch_end]
        out = by_metric(Calculator().calculate(batch, history, industry=INDUSTRY))
        return out.get(("revenue_ttm", batch_end))

    def test_ttm_sums_the_last_four_contiguous_quarters(self):
        result = self.ttm(self.QUARTERS, "2026-03-31")
        self.assertEqual(result.value, Decimal("400"))
        self.assertEqual(result.period_start, "2025-04-01")
        self.assertEqual(result.period_kind, PeriodKind.TTM)

    def dividend_ttm(self, quarterly, annual=None, metric="dividends_per_share", unit="SAR/share"):
        facts = [quarter(metric, value, end, start, 2025, q, unit=unit)
                 for (start, end, _, q), value in zip(self.QUARTERS[:4], quarterly)]
        if annual is not None:
            facts.append(fact(metric, annual, PeriodKind.FY, "2025-12-31", 2025, unit=unit))
        batch = [item for item in facts if item.period_end == "2025-12-31" and item.period_kind == PeriodKind.QUARTER]
        history = [item for item in facts if item not in batch]
        out = by_metric(Calculator().calculate(batch, history, industry=INDUSTRY))
        return {key: value for key, value in out.items() if value.period_kind == PeriodKind.TTM}

    def test_quarterly_dividends_produce_the_named_ttm_keys(self):
        per_share = self.dividend_ttm(["0.3312"] * 4, annual="1.3248")
        self.assertEqual(set(per_share), {("dividend_per_share_ttm", "2025-12-31")})
        self.assertEqual(per_share["dividend_per_share_ttm", "2025-12-31"].value, Decimal("1.3248"))
        self.assertEqual(per_share["dividend_per_share_ttm", "2025-12-31"].unit, "SAR/share")
        paid = self.dividend_ttm(["80104", "80112", "80113", "80118"], annual="320447",
                                 metric="dividends_paid", unit="SAR")
        self.assertEqual(paid["total_dividend_paid_ttm", "2025-12-31"].value, Decimal("320447"))

    def test_ttm_contradicting_the_same_fiscal_year_is_withheld(self):
        self.assertEqual(self.dividend_ttm(["0", "0.48", "0", "0"], annual="0.96"), {})
        # Rounding inside the tolerance still agrees; no fiscal-year value means nothing to contradict.
        self.assertTrue(self.dividend_ttm(["0.33", "0.33", "0.33", "0.33"], annual="1.3248"))
        self.assertTrue(self.dividend_ttm(["0", "0.48", "0", "0"]))

    def test_a_fourth_quarter_never_stands_in_for_the_fiscal_year(self):
        history = [fact("dividends_per_share", "1.3112", PeriodKind.FY, "2022-12-31", 2022, unit="SAR/share")]
        batch = [*annual(2025, net_income="350210", dividends_paid="320447"),
                 fact("dividends_per_share", "1.3248", PeriodKind.FY, "2025-12-31", 2025, unit="SAR/share"),
                 quarter("dividends_paid", "80118", "2025-12-31", "2025-10-01", 2025, 4),
                 quarter("dividends_per_share", "0.3312", "2025-12-31", "2025-10-01", 2025, 4, unit="SAR/share")]
        out = Calculator().calculate(batch, history, industry=INDUSTRY)
        mixed = [(item.metric, item.period_kind) for item in out
                 if item.period_kind == PeriodKind.QUARTER and item.metric in ("payout_ratio", "dividend_cagr_3y")]
        self.assertEqual(mixed, [])
        annual_out = by_metric(item for item in out if item.period_kind == PeriodKind.FY)
        self.assertEqual(annual_out["payout_ratio", "2025-12-31"].value, Decimal("320447") / Decimal("350210"))
        self.assertEqual(annual_out["dividend_cagr_3y", "2025-12-31"].value,
                         (Decimal("1.3248") / Decimal("1.3112")) ** (Decimal(1) / Decimal(3)) - 1)

    def test_ttm_is_withheld_when_a_quarter_is_missing(self):
        gap = [row for row in self.QUARTERS if row[1] != "2025-09-30"]
        self.assertIsNone(self.ttm(gap, "2026-03-31"))


if __name__ == "__main__":
    unittest.main()
