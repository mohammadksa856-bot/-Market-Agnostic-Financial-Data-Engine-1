from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from .models import Fact, PeriodKind


class Calculator:
    """Deterministic, source-traceable calculations; AI never calculates production facts."""

    TTM_FLOWS = {"revenue", "net_income", "operating_cash_flow", "capex", "free_cash_flow", "ebitda"}
    # Quarterly dividends whose trailing-twelve-month sum has its own catalog key. Cash paid only:
    # dividend_per_share_ttm is filed for SABIC as DPS declared for the year, so a sum of DPS paid in the
    # window is a different basis and stays withheld until that basis is decided.
    TTM_NAMED = {"dividends_paid": "total_dividend_paid_ttm"}
    # Interim cash-flow statements are cumulative from the start of the fiscal year, so a discrete quarter of these
    # lines is the difference of two cumulative figures with the same start. Cash-flow totals include discontinued
    # operations, so IFRS 5 does not re-present them between filings.
    CUMULATIVE_QUARTER_FLOWS = ("operating_cash_flow", "capex")
    # Trailing-twelve-month sums compared with the same window one year earlier.
    TTM_GROWTH = {
        "revenue": "revenue_ttm_growth", "net_income": "net_income_ttm_growth", "ebitda": "ebitda_ttm_growth",
        "operating_cash_flow": "operating_cash_flow_ttm_growth", "free_cash_flow": "free_cash_flow_ttm_growth",
    }
    HISTORY_METRICS = {
        "revenue", "gross_profit", "operating_income", "income_before_income_taxes_and_zakat",
        "income_taxes_and_zakat",
        "net_income", "operating_cash_flow", "capex", "free_cash_flow", "total_assets",
        "total_equity", "total_liabilities", "current_assets", "current_liabilities",
        "cash", "inventory", "accounts_receivable", "property_plant_equipment",
        "current_debt", "long_term_debt", "shares_outstanding", "eps_diluted",
        "short_term_investments", "current_assets", "current_liabilities", "intangible_assets",
        "net_debt", "ebit", "ebitda", "depreciation_amortization", "finance_costs",
        "weighted_average_shares_basic", "weighted_average_shares_diluted",
        "adjusted_net_income", "dividends_paid", "market_cap",
        "dividends_per_share", "discontinued_operations_income", "book_value_per_share",
        "cost_of_revenue", "accounts_payable", "general_and_administrative_expense",
        "depreciation_amortization_cash_flow",
        "selling_and_distribution_expense",
        "selling_general_administrative_expense", "research_and_development_expense",
        "share_based_compensation",
        # return-on-capital and coverage inputs (_capital_returns)
        "goodwill", "interest_paid", "debt_repaid",
        "total_hydrocarbon_production", "total_hydrocarbon_reserves",
        "upstream_ebit", "downstream_ebit", "corporate_ebit",
        "upstream_depreciation_amortization", "downstream_depreciation_amortization",
        "corporate_depreciation_amortization",
        # banking + composite-score inputs that live in their own manifests
        "net_financing_income", "total_operating_income", "operating_expense_banking",
        "total_operating_expenses", "provision_expense", "net_loans", "gross_loans", "credit_loss_allowance",
        "customer_deposits", "demand_deposits", "savings_deposits", "bank_investments",
        "due_from_banks", "nonperforming_loans", "credit_loss_allowance", "risk_weighted_assets",
        "regulatory_capital", "retained_earnings", "working_capital", "return_on_equity",
        "cost_to_income_ratio", "nonperforming_loans_ratio",
    }
    GROWTH_METRICS = {
        "revenue": "revenue_growth", "gross_profit": "gross_profit_growth",
        "operating_income": "operating_income_growth", "net_income": "net_income_growth",
        "eps_diluted": "eps_growth", "total_assets": "asset_growth",
        "total_equity": "equity_growth", "operating_cash_flow": "operating_cash_flow_growth",
        "free_cash_flow": "free_cash_flow_growth",
        "ebitda": "ebitda_growth", "dividends_paid": "dividend_growth",
        "dividends_per_share": "dividend_per_share_growth", "book_value_per_share": "book_value_growth",
    }
    QOQ_METRICS = {
        "revenue": "revenue_qoq", "gross_profit": "gross_profit_qoq",
        "operating_income": "operating_income_qoq", "net_income": "net_income_qoq",
        "eps_diluted": "eps_qoq", "ebitda": "ebitda_qoq",
        "operating_cash_flow": "operating_cash_flow_qoq", "free_cash_flow": "free_cash_flow_qoq",
    }
    # source metric -> (output stem, horizons in years); only the horizons the catalog defines
    CAGR_METRICS = {
        "revenue": ("revenue", (3, 5, 10)), "net_income": ("net_income", (3, 5, 10)),
        "eps_diluted": ("eps", (3, 5, 10)), "dividends_per_share": ("dividend", (3, 5, 10)),
        "operating_cash_flow": ("operating_cash_flow", (10,)), "free_cash_flow": ("free_cash_flow", (10,)),
    }
    # Turnover on average balances; recomputed by the build-end reconciliation like the comparisons.
    TURNOVER_METRICS = {"receivables_turnover", "days_sales_outstanding", "inventory_turnover", "days_inventory",
                        "payables_turnover", "days_payables", "cash_conversion_cycle",
                        "return_on_invested_capital", "return_on_capital_employed", "fixed_asset_turnover",
                        "working_capital_turnover", "incremental_roic", "asset_turnover"}
    # IFRS 5 re-presents the income statement above net income when an operation is discontinued, so
    # these lines from an earlier filing may exclude a different set of businesses than a later one.
    RE_PRESENTED_LINES = {
        "revenue", "cost_of_revenue", "gross_profit", "operating_income", "ebit", "ebitda", "adjusted_ebitda",
        "income_before_income_taxes_and_zakat", "income_taxes_and_zakat", "continuing_operations_income",
    }

    # Industries whose balance sheet is not an operating-capital structure (matched case-insensitively).
    CAPITAL_RETURN_EXCLUDED_INDUSTRIES = ("bank", "insurance", "reinsurance", "takaful")
    # Contract keys whose definition needs an accounting decision; never emitted until it is made.
    DEFINITION_PENDING = {
        "fixed_charge_coverage": "fixed charges under IFRS 16 (which lease costs count) are not defined",
        "return_on_capital": "capital base not defined: debt + equity, or net working capital + net fixed assets",
    }

    def calculate(self, facts: list[Fact], history: list[Fact] | None = None,
                  industry: str | None = None) -> list[Fact]:
        derived_quarters = self._cumulative_quarters([*(history or []), *facts], facts)
        facts = [*facts, *derived_quarters]
        all_facts = [*(history or []), *facts]
        out: list[Fact] = list(derived_quarters)
        groups = defaultdict(dict)
        # `combined` is the fiscal-year view of a period end: FY flows with year-end balances and
        # point-in-time values (e.g. a reported year-end market cap). A quarter, YTD or TTM row ending
        # on the same date is a different quantity and never stands in for them.
        annual_view = {PeriodKind.FY, PeriodKind.INSTANT, PeriodKind.AS_OF}
        combined = defaultdict(dict)
        for fact in all_facts:
            if fact.scope == "consolidated" and not fact.dimensions and fact.period_kind in annual_view:
                combined[(fact.company_id, fact.period_end)].setdefault(fact.metric, fact)
        for fact in facts:
            if fact.scope == "consolidated" and not fact.dimensions:
                groups[(fact.company_id, fact.period_end, fact.period_kind,
                        fact.fiscal_year, fact.fiscal_quarter)][fact.metric] = fact
                if fact.period_kind in annual_view:
                    combined[(fact.company_id, fact.period_end)][fact.metric] = fact
        historical = defaultdict(dict)
        for fact in all_facts:
            if fact.scope == "consolidated" and not fact.dimensions:
                historical[(fact.company_id, fact.fiscal_year, fact.period_kind)][fact.metric] = fact
        # Discrete quarters and instants keyed by their exact period end: `historical` keeps one
        # row set per fiscal year, so it cannot tell Q1 from Q2 or a year end from an interim balance.
        quarterly = defaultdict(dict)
        instants = defaultdict(dict)
        year_to_date = defaultdict(dict)
        for fact in all_facts:
            if fact.scope == "consolidated" and not fact.dimensions:
                if fact.period_kind == PeriodKind.QUARTER:
                    quarterly[(fact.company_id, fact.period_end)][fact.metric] = fact
                elif fact.period_kind == PeriodKind.YTD and fact.period_start:
                    year_to_date[(fact.company_id, fact.period_start, fact.period_end)][fact.metric] = fact
                elif fact.period_kind == PeriodKind.INSTANT:
                    instants[(fact.company_id, fact.period_end)][fact.metric] = fact
        # A balance date is a fiscal year end only if some fiscal-year flow ends on it.
        fiscal_year_starts = {(fact.company_id, fact.period_end): fact.period_start for fact in all_facts
                              if fact.period_kind == PeriodKind.FY and fact.period_start}

        for (company_id, _, _, _, _), group in groups.items():
            base = next(iter(group.values()))
            lookup = combined[(company_id, base.period_end)] if base.period_kind in {PeriodKind.FY, PeriodKind.INSTANT} else group

            def add(metric, value, formula, reference=None, unit="ratio", currency=""):
                if metric in group or metric in self.DEFINITION_PENDING:
                    return
                source = reference or base
                calculated = Fact(
                    source.company_id, metric, value, currency, unit, source.period_start,
                    source.period_end, source.period_kind, source.fiscal_year, source.fiscal_quarter,
                    source.source_key, source.source_url, source.filed_at, is_calculated=True,
                    calculation=formula, scope=source.scope, dimensions=source.dimensions,
                )
                out.append(calculated)
                group[metric] = calculated
                lookup[metric] = calculated

            def ratio(metric, numerator, denominator, formula=None, absolute=False):
                if numerator in lookup and denominator in lookup and lookup[denominator].value:
                    value = lookup[numerator].value / lookup[denominator].value
                    add(metric, abs(value) if absolute else value,
                        formula or f"{numerator} / {denominator}", lookup[numerator])

            if base.period_kind in {PeriodKind.FY, PeriodKind.QUARTER, PeriodKind.YTD, PeriodKind.TTM}:
                if "insurance_revenue" in group and "revenue" not in group:
                    insurance_revenue = group["insurance_revenue"]
                    add("revenue", insurance_revenue.value,
                        "insurance_revenue (IFRS 17 universal revenue alias)",
                        insurance_revenue, insurance_revenue.unit,
                        insurance_revenue.currency)
                if "operating_cash_flow" in group and "capex" in group:
                    add("free_cash_flow", group["operating_cash_flow"].value - abs(group["capex"].value),
                        "operating_cash_flow - abs(capex)", group["operating_cash_flow"],
                        group["operating_cash_flow"].unit, group["operating_cash_flow"].currency)
                ratio("net_margin", "net_income", "revenue")
                ratio("gross_margin", "gross_profit", "revenue")
                ratio("operating_margin", "operating_income", "revenue")
                ratio("pretax_margin", "income_before_income_taxes_and_zakat", "revenue")
                ratio("effective_tax_rate", "income_taxes_and_zakat",
                      "income_before_income_taxes_and_zakat",
                      "abs(income_taxes_and_zakat) / income_before_income_taxes_and_zakat", True)
                ratio("cfo_margin", "operating_cash_flow", "revenue")
                ratio("fcf_margin", "free_cash_flow", "revenue")
                ratio("capex_to_revenue", "capex", "revenue", "abs(capex) / revenue", True)
                ratio("capex_to_cfo", "capex", "operating_cash_flow", "abs(capex) / operating_cash_flow", True)
                ratio("income_quality", "operating_cash_flow", "net_income")
                ratio("cash_conversion_of_earnings", "operating_cash_flow", "net_income")
                ratio("fcf_conversion", "free_cash_flow", "ebitda")
                ratio("payout_ratio", "dividends_paid", "net_income", "abs(dividends_paid) / net_income", True)
                ratio("dividend_coverage_ratio", "net_income", "dividends_paid",
                      "net_income / abs(dividends_paid)", True)
                ratio("fcf_payout_ratio", "dividends_paid", "free_cash_flow",
                      "abs(dividends_paid) / free_cash_flow", True)
                ratio("fcf_dividend_coverage_ratio", "free_cash_flow", "dividends_paid",
                      "free_cash_flow / abs(dividends_paid)", True)
                # D&A as the income statement reports it, else the cash-flow add-back (the statement capex is on)
                depreciation = next((key for key in ("depreciation_amortization", "depreciation_amortization_cash_flow")
                                     if key in lookup), "depreciation_amortization")
                ratio("capex_to_depreciation", "capex", depreciation, f"abs(capex) / abs({depreciation})", True)
                ratio("capex_to_depreciation_amortization", "capex", depreciation,
                      f"abs(capex) / abs({depreciation})", True)
                # the catalog key is selling_and_distribution_expense; selling_distribution_expense is older
                selling = next((key for key in ("selling_and_distribution_expense", "selling_distribution_expense")
                                if key in lookup), None)
                if ("selling_general_administrative_expense" not in lookup and
                        "general_and_administrative_expense" in lookup and selling):
                    add("selling_general_administrative_expense",
                        abs(lookup["general_and_administrative_expense"].value) +
                        abs(lookup[selling].value),
                        f"abs(general_and_administrative_expense) + abs({selling})",
                        lookup["general_and_administrative_expense"],
                        lookup["general_and_administrative_expense"].unit,
                        lookup["general_and_administrative_expense"].currency)
                ratio("selling_general_administrative_to_revenue",
                      "selling_general_administrative_expense", "revenue")
                ratio("research_development_to_revenue", "research_and_development_expense", "revenue")
                ratio("share_based_compensation_to_revenue", "share_based_compensation", "revenue")
                ratio("receivables_to_revenue", "accounts_receivable", "revenue")
                if "ebit" in lookup and "depreciation_amortization" in lookup:
                    add("ebitda", lookup["ebit"].value + abs(lookup["depreciation_amortization"].value),
                        "ebit + abs(depreciation_amortization)", lookup["ebit"],
                        lookup["ebit"].unit, lookup["ebit"].currency)
                ratio("ebit_margin", "ebit", "revenue")
                ratio("ebitda_margin", "ebitda", "revenue")
                ratio("interest_coverage", "ebit", "finance_costs", "ebit / abs(finance_costs)", True)
                # Banking efficiency (fires only when the bank income lines are present)
                if "operating_expense_banking" in lookup and "total_operating_income" in lookup \
                        and lookup["total_operating_income"].value:
                    add("cost_to_income_ratio",
                        abs(lookup["operating_expense_banking"].value) / lookup["total_operating_income"].value,
                        "abs(operating_expense_banking) / total_operating_income",
                        lookup["total_operating_income"])
                shares = lookup.get("weighted_average_shares_diluted") or lookup.get("weighted_average_shares_basic")
                if shares and shares.value:
                    for numerator, metric in (
                        ("revenue", "revenue_per_share"),
                        ("operating_cash_flow", "operating_cash_flow_per_share"),
                        ("free_cash_flow", "free_cash_flow_per_share"),
                        ("cash", "cash_per_share"),
                        ("capex", "capex_per_share"),
                        ("ebit", "ebit_per_share"),
                        ("ebitda", "ebitda_per_share"),
                    ):
                        if numerator in lookup:
                            value = abs(lookup[numerator].value) if numerator == "capex" else lookup[numerator].value
                            add(metric, value / shares.value,
                                f"{numerator} / weighted_average_shares", lookup[numerator],
                                f"{lookup[numerator].currency}/share", lookup[numerator].currency)
                    debt = sum((lookup[key].value for key in ("current_debt", "long_term_debt") if key in lookup), Decimal(0))
                    if debt:
                        reference = lookup.get("current_debt") or lookup["long_term_debt"]
                        add("debt_per_share", debt / shares.value,
                            "(current_debt + long_term_debt) / weighted_average_shares",
                            reference, f"{reference.currency}/share", reference.currency)
                    if "adjusted_net_income" in lookup:
                        add("earnings_per_share_normalized",
                            lookup["adjusted_net_income"].value / shares.value,
                            "adjusted_net_income / weighted_average_shares_diluted",
                            lookup["adjusted_net_income"],
                            f"{lookup['adjusted_net_income'].currency}/share",
                            lookup["adjusted_net_income"].currency)
            if base.period_kind == PeriodKind.INSTANT:
                ratio("liabilities_to_equity", "total_liabilities", "total_equity")
                ratio("liabilities_to_assets", "total_liabilities", "total_assets")
                ratio("equity_ratio", "total_equity", "total_assets")
                ratio("current_ratio", "current_assets", "current_liabilities")
                ratio("cash_ratio", "cash", "current_liabilities")
                if all(key in lookup for key in ("cash", "short_term_investments", "accounts_receivable", "current_liabilities")) and lookup["current_liabilities"].value:
                    add("quick_ratio", (lookup["cash"].value + lookup["short_term_investments"].value +
                                        lookup["accounts_receivable"].value) / lookup["current_liabilities"].value,
                        "(cash + short_term_investments + accounts_receivable) / current_liabilities",
                        lookup["current_liabilities"])
                ratio("inventory_to_assets", "inventory", "total_assets")
                ratio("ppe_to_assets", "property_plant_equipment", "total_assets")
                # Banking balance-sheet ratios (no-op unless the bank lines are present)
                if "gross_loans" not in lookup and "net_loans" in lookup and "credit_loss_allowance" in lookup:
                    add("gross_loans",
                        lookup["net_loans"].value + abs(lookup["credit_loss_allowance"].value),
                        "net_loans + abs(credit_loss_allowance)", lookup["net_loans"],
                        lookup["net_loans"].unit, lookup["net_loans"].currency)
                ratio("loans_to_deposits_ratio", "net_loans", "customer_deposits")
                ratio("nonperforming_loans_ratio", "nonperforming_loans", "gross_loans")
                ratio("nonperforming_loans_coverage", "credit_loss_allowance", "nonperforming_loans")
                ratio("capital_adequacy_ratio", "regulatory_capital", "risk_weighted_assets")
                if all(k in lookup for k in ("demand_deposits", "savings_deposits", "customer_deposits")) \
                        and lookup["customer_deposits"].value:
                    add("casa_ratio",
                        (lookup["demand_deposits"].value + lookup["savings_deposits"].value)
                        / lookup["customer_deposits"].value,
                        "(demand_deposits + savings_deposits) / customer_deposits",
                        lookup["customer_deposits"])
                debt = sum((lookup[key].value for key in ("current_debt", "long_term_debt") if key in lookup), Decimal(0))
                if debt:
                    reference = lookup.get("current_debt") or lookup["long_term_debt"]
                    if "total_equity" in lookup and lookup["total_equity"].value:
                        add("debt_to_equity", debt / lookup["total_equity"].value,
                            "(current_debt + long_term_debt) / total_equity", reference)
                    if "total_assets" in lookup and lookup["total_assets"].value:
                        add("debt_to_assets", debt / lookup["total_assets"].value,
                            "(current_debt + long_term_debt) / total_assets", reference)
                    if "cash" in lookup:
                        net_debt = debt - lookup["cash"].value
                        if "total_equity" in lookup and lookup["total_equity"].value:
                            add("net_debt_to_equity", net_debt / lookup["total_equity"].value,
                                "(current_debt + long_term_debt - cash) / total_equity", reference)
                        if "invested_capital" not in lookup and "total_equity" in lookup:
                            add("invested_capital", lookup["total_equity"].value + net_debt,
                                "total_equity + current_debt + long_term_debt - cash", reference,
                                lookup["total_equity"].unit, lookup["total_equity"].currency)
                    prior_debt_rows = historical.get((company_id, base.fiscal_year - 1, PeriodKind.INSTANT), {})
                    prior_debt = sum((prior_debt_rows[key].value for key in ("current_debt", "long_term_debt") if key in prior_debt_rows), Decimal(0))
                    if prior_debt:
                        add("debt_growth", debt / prior_debt - 1,
                            "(current_debt + long_term_debt) / prior_fy(total_debt) - 1", reference)
                if "current_assets" in lookup and "current_liabilities" in lookup:
                    add("working_capital", lookup["current_assets"].value - lookup["current_liabilities"].value,
                        "current_assets - current_liabilities", lookup["current_assets"],
                        lookup["current_assets"].unit, lookup["current_assets"].currency)
                if "current_assets" in lookup and "total_liabilities" in lookup:
                    add("net_current_asset_value",
                        lookup["current_assets"].value - lookup["total_liabilities"].value,
                        "current_assets - total_liabilities", lookup["current_assets"],
                        lookup["current_assets"].unit, lookup["current_assets"].currency)
                    if all(key in lookup for key in ("cash", "accounts_receivable", "inventory")):
                        conservative = (lookup["cash"].value + Decimal("0.75") * lookup["accounts_receivable"].value +
                                        Decimal("0.5") * lookup["inventory"].value - lookup["total_liabilities"].value)
                        add("graham_net_net", conservative,
                            "cash + 0.75 * accounts_receivable + 0.5 * inventory - total_liabilities",
                            lookup["current_assets"], lookup["current_assets"].unit,
                            lookup["current_assets"].currency)
                if "total_equity" in lookup and "intangible_assets" in lookup:
                    # an unreported intangible line is unknown, not zero
                    tangible = lookup["total_equity"].value - lookup["intangible_assets"].value
                    add("tangible_book_value", tangible, "total_equity - intangible_assets",
                        lookup["total_equity"], lookup["total_equity"].unit,
                        lookup["total_equity"].currency)
                if "total_equity" in lookup:
                    shares = lookup.get("shares_outstanding")
                    if shares and shares.value:
                        add("book_value_per_share", lookup["total_equity"].value / shares.value,
                            "total_equity / shares_outstanding", lookup["total_equity"],
                            f"{lookup['total_equity'].currency}/share", lookup["total_equity"].currency)
                        if "intangible_assets" in lookup:
                            add("tangible_book_value_per_share",
                                (lookup["total_equity"].value - lookup["intangible_assets"].value) / shares.value,
                                "(total_equity - intangible_assets) / shares_outstanding",
                                lookup["total_equity"], f"{lookup['total_equity'].currency}/share",
                                lookup["total_equity"].currency)
                        if "retained_earnings" in lookup:
                            add("retained_earnings_per_share",
                                lookup["retained_earnings"].value / shares.value,
                                "retained_earnings / shares_outstanding", lookup["retained_earnings"],
                                f"{lookup['retained_earnings'].currency}/share",
                                lookup["retained_earnings"].currency)

            if base.period_kind == PeriodKind.FY:
                # Retrospective year-end multiples use the market capitalization
                # reported for the same fiscal period.  This is intentionally
                # separate from point-in-time valuations, which enforce a filing-
                # date cutoff and therefore never look ahead.
                if "market_cap" in lookup and lookup["market_cap"].value:
                    ratio("price_to_earnings", "market_cap", "net_income",
                          "reported_year_end_market_cap / net_income")
                    ratio("price_to_sales", "market_cap", "revenue",
                          "reported_year_end_market_cap / revenue")
                    ratio("price_to_book", "market_cap", "total_equity",
                          "reported_year_end_market_cap / total_equity")
                    ratio("earnings_yield", "net_income", "market_cap",
                          "net_income / reported_year_end_market_cap")
                    ratio("fcf_yield", "free_cash_flow", "market_cap",
                          "free_cash_flow / reported_year_end_market_cap")
                    ratio("cfo_yield", "operating_cash_flow", "market_cap",
                          "operating_cash_flow / reported_year_end_market_cap")
                    ratio("price_to_cash_flow", "market_cap", "operating_cash_flow",
                          "reported_year_end_market_cap / operating_cash_flow")
                    ratio("price_to_free_cash_flow", "market_cap", "free_cash_flow",
                          "reported_year_end_market_cap / free_cash_flow")
                    ratio("market_cap_to_equity", "market_cap", "total_equity",
                          "reported_year_end_market_cap / total_equity")
                    ratio("market_cap_to_net_income", "market_cap", "net_income",
                          "reported_year_end_market_cap / net_income")
                if ("total_hydrocarbon_reserves" in lookup and
                        "total_hydrocarbon_production" in lookup and
                        lookup["total_hydrocarbon_production"].value):
                    add(
                        "reserve_life_index",
                        lookup["total_hydrocarbon_reserves"].value * Decimal(1000) /
                        (lookup["total_hydrocarbon_production"].value * Decimal(365)),
                        "total_hydrocarbon_reserves * 1000 / (total_hydrocarbon_production * 365)",
                        lookup["total_hydrocarbon_production"], unit="years", currency="",
                    )
                prior_instant = historical.get((company_id, base.fiscal_year - 1, PeriodKind.INSTANT), {})
                # Flows of a year with discontinued operations exclude the business that the opening balances
                # still hold (IFRS 5 does not re-present the prior balance sheet), so turnover on an average of
                # the two balances would mix bases and is withheld.
                re_presented_year = any(
                    (row := historical.get((company_id, year, PeriodKind.FY), {}).get("discontinued_operations_income"))
                    and row.value for year in (base.fiscal_year - 1, base.fiscal_year))
                if "total_assets" in lookup and "total_assets" in prior_instant:
                    average = (lookup["total_assets"].value + prior_instant["total_assets"].value) / 2
                    if average and "net_income" in lookup:
                        add("return_on_assets", lookup["net_income"].value / average,
                            "net_income / average(total_assets)", lookup["net_income"])
                    if average and "revenue" in lookup and not re_presented_year:
                        add("asset_turnover", lookup["revenue"].value / average,
                            "revenue / average(total_assets)", lookup["revenue"])
                    if average and "operating_cash_flow" in lookup:
                        add("cash_return_on_assets", lookup["operating_cash_flow"].value / average,
                            "operating_cash_flow / average(total_assets)", lookup["operating_cash_flow"])
                if "total_equity" in lookup and "total_equity" in prior_instant:
                    average = (lookup["total_equity"].value + prior_instant["total_equity"].value) / 2
                    if average and "net_income" in lookup:
                        add("return_on_equity", lookup["net_income"].value / average,
                            "net_income / average(total_equity)", lookup["net_income"])
                    if average and "operating_cash_flow" in lookup:
                        add("cash_return_on_equity", lookup["operating_cash_flow"].value / average,
                            "operating_cash_flow / average(total_equity)", lookup["operating_cash_flow"])
                    current_intangible = lookup["intangible_assets"].value if "intangible_assets" in lookup else Decimal(0)
                    prior_intangible = prior_instant["intangible_assets"].value if "intangible_assets" in prior_instant else Decimal(0)
                    current_tangible = lookup["total_equity"].value - current_intangible
                    prior_tangible = prior_instant["total_equity"].value - prior_intangible
                    average_tangible = (current_tangible + prior_tangible) / 2
                    if average_tangible and "net_income" in lookup:
                        add("return_on_tangible_equity", lookup["net_income"].value / average_tangible,
                            "net_income / average(total_equity - intangible_assets)", lookup["net_income"])
                # Banking: margins on average earning assets / average loans
                earning_keys = ("net_loans", "bank_investments", "due_from_banks")
                if "net_financing_income" in lookup and all(k in lookup for k in earning_keys) \
                        and all(k in prior_instant for k in earning_keys):
                    average_earning = (sum(lookup[k].value for k in earning_keys)
                                       + sum(prior_instant[k].value for k in earning_keys)) / 2
                    if average_earning:
                        add("net_interest_margin", lookup["net_financing_income"].value / average_earning,
                            "net_financing_income / average(net_loans + bank_investments + due_from_banks)",
                            lookup["net_financing_income"])
                if "provision_expense" in lookup and "net_loans" in lookup and "net_loans" in prior_instant:
                    average_loans = (lookup["net_loans"].value + prior_instant["net_loans"].value) / 2
                    if average_loans:
                        add("cost_of_risk", abs(lookup["provision_expense"].value) / average_loans,
                            "abs(provision_expense) / average(net_loans)", lookup["provision_expense"])
                if not re_presented_year and "accounts_receivable" in lookup and "accounts_receivable" in prior_instant \
                        and "revenue" in lookup:
                    average = (lookup["accounts_receivable"].value + prior_instant["accounts_receivable"].value) / 2
                    if average:
                        add("receivables_turnover", lookup["revenue"].value / average,
                            "revenue / average(accounts_receivable)", lookup["revenue"])
                        add("days_sales_outstanding", average / lookup["revenue"].value * Decimal(365),
                            "average(accounts_receivable) / revenue * 365", lookup["revenue"])
                # Inventory and payables turn over against cost of sales, on the average of the opening and
                # closing balances, like receivables against revenue.
                cost = lookup.get("cost_of_revenue")
                for balance, turnover, days in (("inventory", "inventory_turnover", "days_inventory"),
                                                ("accounts_payable", "payables_turnover", "days_payables")):
                    if re_presented_year or cost is None or not cost.value or balance not in lookup \
                            or balance not in prior_instant:
                        continue
                    average = (lookup[balance].value + prior_instant[balance].value) / 2
                    if average:
                        add(turnover, abs(cost.value) / average, f"abs(cost_of_revenue) / average({balance})", cost)
                        add(days, average / abs(cost.value) * Decimal(365),
                            f"average({balance}) / abs(cost_of_revenue) * 365", cost)
                if all(key in lookup for key in ("days_sales_outstanding", "days_inventory", "days_payables")):
                    add("cash_conversion_cycle",
                        lookup["days_sales_outstanding"].value + lookup["days_inventory"].value
                        - lookup["days_payables"].value,
                        "days_sales_outstanding + days_inventory - days_payables", lookup["days_inventory"],
                        "days")
                instant_now = historical.get((company_id, base.fiscal_year, PeriodKind.INSTANT), {})
                debt = sum((instant_now[key].value for key in ("current_debt", "long_term_debt") if key in instant_now), Decimal(0))
                if debt and "ebitda" in lookup and lookup["ebitda"].value:
                    add("debt_to_ebitda", debt / lookup["ebitda"].value,
                        "(current_debt + long_term_debt) / ebitda", lookup["ebitda"])
                    net_debt = instant_now.get("net_debt")
                    if net_debt:
                        add("net_debt_to_ebitda", net_debt.value / lookup["ebitda"].value,
                            "net_debt / ebitda", lookup["ebitda"])
                if debt:
                    if "operating_cash_flow" in lookup:
                        add("cfo_to_debt", lookup["operating_cash_flow"].value / debt,
                            "operating_cash_flow / total_debt", lookup["operating_cash_flow"])
                    if "free_cash_flow" in lookup:
                        add("fcf_to_debt", lookup["free_cash_flow"].value / debt,
                            "free_cash_flow / total_debt", lookup["free_cash_flow"])
                    capital = debt + (instant_now["total_equity"].value if "total_equity" in instant_now else Decimal(0))
                    if capital:
                        add("total_debt_to_capital", debt / capital,
                            "total_debt / (total_debt + total_equity)",
                            instant_now.get("current_debt") or instant_now["long_term_debt"])
                        if "long_term_debt" in instant_now:
                            add("long_term_debt_to_capital", instant_now["long_term_debt"].value / capital,
                                "long_term_debt / (total_debt + total_equity)", instant_now["long_term_debt"])
                self._capital_returns(company_id, base, lookup, historical, instants, add, industry)
                for source_metric, (cagr_stem, horizons) in self.CAGR_METRICS.items():
                    if source_metric not in lookup or not lookup[source_metric].value:
                        continue
                    for years in horizons:
                        prior = historical.get((company_id, base.fiscal_year - years, PeriodKind.FY), {})
                        if source_metric in prior and prior[source_metric].value > 0 and lookup[source_metric].value > 0 \
                                and self._same_presentation(source_metric, lookup[source_metric], prior[source_metric],
                                                            historical, company_id, base.fiscal_year - years,
                                                            base.fiscal_year):
                            add(f"{cagr_stem}_cagr_{years}y",
                                (lookup[source_metric].value / prior[source_metric].value) ** (Decimal(1) / Decimal(years)) - 1,
                                f"({source_metric} / prior_{years}y({source_metric})) ^ (1/{years}) - 1",
                                lookup[source_metric])
            if base.period_kind in {PeriodKind.FY, PeriodKind.INSTANT}:
                if base.period_kind == PeriodKind.FY:
                    prior = historical.get((company_id, base.fiscal_year - 1, PeriodKind.FY), {})
                else:
                    # Annual balance growth: a fiscal year end against the exact prior year end. An interim
                    # balance compared with the last year end is a months-long change, not annual growth.
                    fy_start = fiscal_year_starts.get((company_id, base.period_end))
                    prior = instants.get((company_id, (date.fromisoformat(fy_start) - timedelta(days=1)).isoformat()),
                                         {}) if fy_start else {}
                for source_metric, output_metric in self.GROWTH_METRICS.items():
                    if source_metric in group and source_metric in prior and prior[source_metric].value \
                            and self._same_presentation(source_metric, group[source_metric], prior[source_metric],
                                                        historical, company_id, base.fiscal_year - 1,
                                                        base.fiscal_year):
                        add(output_metric, group[source_metric].value / prior[source_metric].value - 1,
                            f"{source_metric} / prior_fy({source_metric}) - 1", group[source_metric])
            if base.period_kind == PeriodKind.QUARTER:
                self._quarter_changes(company_id, base, group, quarterly, year_to_date, add)

        # Composite scores run last: they read ratios (cost_to_income_ratio,
        # nonperforming_loans_ratio, ROE, ...) that the passes above computed.
        for (company_id, period_end, period_kind, _, _), group in groups.items():
            if period_kind != PeriodKind.FY:
                continue
            base = next(iter(group.values()))
            lookup = combined[(company_id, period_end)]

            def score_add(metric, value, formula, reference=None, unit="ratio", currency=""):
                if metric in lookup:
                    return
                source = reference or base
                calculated = Fact(
                    source.company_id, metric, value, currency, unit, source.period_start,
                    source.period_end, source.period_kind, source.fiscal_year,
                    source.fiscal_quarter, source.source_key, source.source_url, source.filed_at,
                    is_calculated=True, calculation=formula, scope=source.scope,
                    dimensions=source.dimensions,
                )
                out.append(calculated)
                lookup[metric] = calculated

            self._composite_scores(company_id, base, lookup, historical, score_add)

        dimensioned = defaultdict(dict)
        targets = set()
        for fact in all_facts:
            if fact.dimensions.get("segment"):
                key = (fact.company_id, fact.period_end, fact.period_kind, fact.fiscal_year,
                       fact.fiscal_quarter, fact.scope, tuple(sorted(fact.dimensions.items())))
                dimensioned[key][fact.metric] = fact
        for fact in facts:
            if fact.dimensions.get("segment"):
                targets.add((fact.company_id, fact.period_end, fact.period_kind, fact.fiscal_year,
                             fact.fiscal_quarter, fact.scope, tuple(sorted(fact.dimensions.items()))))
        for key in targets:
            metrics = dimensioned[key]
            segment = dict(key[-1])["segment"].lower()
            ebit_key = f"{segment}_ebit"
            depreciation_key = f"{segment}_depreciation_amortization"
            if ebit_key not in metrics or depreciation_key not in metrics:
                continue
            ebit = metrics[ebit_key]
            depreciation = metrics[depreciation_key]
            source = max((ebit, depreciation), key=lambda item: (item.filed_at, item.source_key))
            out.append(Fact(
                source.company_id, f"{segment}_ebitda",
                ebit.value + abs(depreciation.value), source.currency, source.unit,
                source.period_start, source.period_end, source.period_kind, source.fiscal_year,
                source.fiscal_quarter, source.source_key, source.source_url, source.filed_at,
                is_calculated=True,
                calculation=f"{ebit_key} + abs({depreciation_key})",
                scope=source.scope, dimensions=source.dimensions,
            ))

        target_periods = {fact.period_end for fact in facts if fact.period_kind == PeriodKind.QUARTER}
        return out + self._ttm([*all_facts, *out], target_periods)

    def _capital_returns(self, company_id, base, lookup, historical, instants, add, industry):
        """Fiscal-year returns on capital, turnover, coverage and per-share growth.

        Every formula reads ingested lines only, and a metric is emitted only when:
        - the issuer's industry is known and not excluded (banks and insurers have no
          operating-capital structure these ratios describe);
        - balance-sheet averages use the exact opening (day before the fiscal year starts)
          and closing (fiscal year end) instants, never an interim balance;
        - every monetary input is in the numerator's currency and its unit is that currency;
        - every component is reported: a missing debt line is never read as zero;
        - the tax expense keeps its sign (engine convention: expense <= 0) and the effective
          rate lies in [0, 1) on a positive pre-tax income; otherwise after-tax metrics are withheld.
        Metrics in DEFINITION_PENDING are never emitted.
        """
        if not industry or any(term in industry.lower() for term in self.CAPITAL_RETURN_EXCLUDED_INDUSTRIES):
            return
        if not base.period_start:
            return
        closing = instants.get((company_id, base.period_end), {})
        opening = instants.get((company_id, (date.fromisoformat(base.period_start) - timedelta(days=1)).isoformat()), {})
        prior_fy = historical.get((company_id, base.fiscal_year - 1, PeriodKind.FY), {})
        opening_date = (date.fromisoformat(base.period_start) - timedelta(days=1)).isoformat()
        if any(fact.period_end != opening_date for fact in prior_fy.values()):
            prior_fy = {}

        def money(rows, key, currency):
            fact = rows.get(key)
            if fact is None or fact.value is None or not currency:
                return None
            return fact.value if fact.currency == currency and fact.unit == currency else None

        def debt(rows, currency):
            parts = [money(rows, key, currency) for key in ("current_debt", "long_term_debt")]
            return None if None in parts else sum(parts, Decimal(0))

        def invested_capital(rows, currency):
            # Same definition as the invested_capital instant metric, with both debt lines reported.
            total_debt, equity, cash = debt(rows, currency), money(rows, "total_equity", currency), money(rows, "cash", currency)
            return None if None in (total_debt, equity, cash) else equity + total_debt - cash

        def capital_employed(rows, currency):
            assets, current = money(rows, "total_assets", currency), money(rows, "current_liabilities", currency)
            return None if None in (assets, current) else assets - current

        def working_capital(rows, currency):
            assets, current = money(rows, "current_assets", currency), money(rows, "current_liabilities", currency)
            return None if None in (assets, current) else assets - current

        def average(measure, currency):
            now, prior = measure(closing, currency), measure(opening, currency)
            return None if now is None or prior is None else (now + prior) / 2

        def tax_rate(rows, currency):
            taxes = money(rows, "income_taxes_and_zakat", currency)
            pretax = money(rows, "income_before_income_taxes_and_zakat", currency)
            if taxes is None or pretax is None or pretax <= 0 or taxes > 0:
                return None  # loss year, or a tax benefit / sign the engine convention cannot confirm
            rate = -taxes / pretax
            return rate if rate < 1 else None

        def nopat_of(rows):
            ebit_fact = rows.get("ebit")
            currency = ebit_fact.currency if ebit_fact is not None else ""
            ebit_value, rate = money(rows, "ebit", currency), tax_rate(rows, currency)
            return None if ebit_value is None or rate is None else ebit_value * (1 - rate)

        reference = lookup.get("ebit") or lookup.get("revenue") or base
        currency = reference.currency
        ebit, revenue, net_income = (money(lookup, key, currency) for key in ("ebit", "revenue", "net_income"))
        nopat = nopat_of(lookup)
        if nopat is not None:
            add("nopat", nopat, "ebit * (1 - (-income_taxes_and_zakat) / income_before_income_taxes_and_zakat)",
                lookup["ebit"], currency, currency)

        # Continuing-operations flows of a year with discontinued operations exclude a business the opening
        # balances still hold (IFRS 5 leaves the prior balance sheet as it was): withhold flow-to-balance ratios.
        mixed_basis = any(
            (row := historical.get((company_id, year, PeriodKind.FY), {}).get("discontinued_operations_income"))
            and row.value for year in (base.fiscal_year - 1, base.fiscal_year))

        def average_return(metric, numerator, measure, formula):
            if mixed_basis:
                return
            denominator = average(measure, currency)
            if numerator is not None and denominator:
                add(metric, numerator / denominator, formula, reference)

        average_return("return_on_invested_capital", nopat, invested_capital,
                       "nopat / average(opening, closing)(total_equity + current_debt + long_term_debt - cash)")
        average_return("return_on_capital_employed", ebit, capital_employed,
                       "ebit / average(opening, closing)(total_assets - current_liabilities)")
        average_return("fixed_asset_turnover", revenue, lambda rows, cur: money(rows, "property_plant_equipment", cur),
                       "revenue / average(opening, closing)(property_plant_equipment)")
        wc_open, wc_close = working_capital(opening, currency), working_capital(closing, currency)
        # Provisional guard (near-zero threshold is DEFINITION_PENDING): both balances positive and
        # the average at least 5% of revenue, so the turnover never exceeds 20x.
        if not mixed_basis and revenue and wc_open is not None and wc_close is not None and wc_open > 0 and wc_close > 0 \
                and (wc_open + wc_close) / 2 >= revenue * Decimal("0.05"):
            add("working_capital_turnover", revenue / ((wc_open + wc_close) / 2),
                "revenue / average(opening, closing)(current_assets - current_liabilities); "
                "both balances > 0, average >= 5% of revenue", lookup["revenue"])

        prior_nopat = nopat_of(prior_fy) if prior_fy and prior_fy.get("ebit") and prior_fy["ebit"].currency == currency else None
        ic_now, ic_prior = invested_capital(closing, currency), invested_capital(opening, currency)
        if not mixed_basis and None not in (nopat, prior_nopat, ic_now, ic_prior) and ic_now != ic_prior:
            add("incremental_roic", (nopat - prior_nopat) / (ic_now - ic_prior),
                "(nopat - prior_fy(nopat)) / (closing - opening)(invested_capital)", reference)

        operating_income = money(lookup, "operating_income", currency)
        prior_operating_income, prior_revenue = (money(prior_fy, key, currency) for key in ("operating_income", "revenue"))
        if None not in (operating_income, prior_operating_income) and revenue and prior_revenue:
            add("margin_expansion", operating_income / revenue - prior_operating_income / prior_revenue,
                "operating_income / revenue - prior_fy(operating_income / revenue)", lookup["operating_income"])

        inventory = money(closing, "inventory", currency)
        if inventory is not None and revenue:
            add("inventory_to_revenue", inventory / revenue, "closing(inventory) / revenue", lookup["revenue"])
        tangible_parts = [money(closing, key, currency) for key in ("total_assets", "goodwill", "intangible_assets")]
        if net_income is not None and None not in tangible_parts:
            tangible_assets = tangible_parts[0] - tangible_parts[1] - tangible_parts[2]
            if tangible_assets > 0:
                add("return_on_tangible_assets", net_income / tangible_assets,
                    "net_income / closing(total_assets - goodwill - intangible_assets)", lookup["net_income"])

        cfo = money(lookup, "operating_cash_flow", currency)
        interest_paid, debt_repaid = money(lookup, "interest_paid", currency), money(lookup, "debt_repaid", currency)
        if cfo is not None and interest_paid:
            add("cfo_interest_coverage", cfo / abs(interest_paid),
                "operating_cash_flow / abs(interest_paid)", lookup["operating_cash_flow"])
        if cfo is not None and interest_paid is not None and debt_repaid is not None \
                and abs(interest_paid) + abs(debt_repaid):
            add("debt_service_coverage_proxy", cfo / (abs(interest_paid) + abs(debt_repaid)),
                "proxy, not the lender DSCR: operating_cash_flow / (abs(interest_paid) + abs(debt_repaid))",
                lookup["operating_cash_flow"])

        # Per-share growth on one share basis: diluted in both years, else basic in both years.
        basis = next((key for key in ("weighted_average_shares_diluted", "weighted_average_shares_basic")
                      if all(rows.get(key) is not None and rows[key].unit == "shares" and rows[key].value
                             for rows in (lookup, prior_fy))), None)

        def free_cash_flow(rows):
            flow, capex = money(rows, "operating_cash_flow", currency), money(rows, "capex", currency)
            return None if flow is None or capex is None else flow - abs(capex)

        if basis:
            for metric, numerator in (("revenue_per_share_growth", lambda rows: money(rows, "revenue", currency)),
                                      ("free_cash_flow_per_share_growth", free_cash_flow)):
                now, prior = numerator(lookup), numerator(prior_fy)
                if now is not None and prior is not None and prior > 0:
                    per_share_now = now / lookup[basis].value
                    per_share_prior = prior / prior_fy[basis].value
                    stem = metric[:-len("_growth")]
                    add(metric, per_share_now / per_share_prior - 1,
                        f"{stem} / prior_fy({stem}) - 1 on {basis}; prior > 0", reference)

    def _same_presentation(self, metric, current, prior, historical, company_id, first_year, last_year):
        """Whether two fiscal-year figures of `metric` are on one presentation basis.

        Once any year in the span reports discontinued operations, a re-presented line is compared only
        when both figures come from the same filing, which states its comparative on its own basis."""
        if metric not in self.RE_PRESENTED_LINES:
            return True
        discontinued = any(
            (row := historical.get((company_id, year, PeriodKind.FY), {}).get("discontinued_operations_income"))
            and row.value for year in range(first_year, last_year + 1))
        return not discontinued or bool(current.source_url) and current.source_url == prior.source_url

    def _quarter_changes(self, company_id, base, group, quarterly, year_to_date, add):
        """Change against the immediately preceding discrete quarter, in the same currency and unit.

        Growth on a non-positive base is DEFINITION_PENDING and is not emitted. When a year-to-date
        figure ends on this quarter, the previous cumulative figure plus this quarter must add up to it:
        a re-presentation (e.g. a business moved to discontinued operations) puts the two quarters on
        different bases, and that comparison is withheld."""
        if not base.period_start:
            return
        previous_end = (date.fromisoformat(base.period_start) - timedelta(days=1)).isoformat()
        previous = quarterly.get((company_id, previous_end), {})

        def same_basis(metric):
            if metric == "eps_diluted":  # per-share figures do not add across quarters (share counts change)
                return True
            for (cid, start, end), rows in year_to_date.items():
                if cid != company_id or end != base.period_end or metric not in rows:
                    continue
                total = rows[metric]
                before = (year_to_date.get((company_id, start, previous_end), {}).get(metric)
                          or (previous.get(metric) if previous.get(metric) and previous[metric].period_start == start else None))
                current = group.get(metric)
                if before is None or current is None or not start < base.period_start:
                    continue
                values = [before.value, current.value, total.value]
                if abs(before.value + current.value - total.value) > self._rounding_bound(values):
                    return False
            return True

        def quarter_value(rows, metric, currency, unit):
            if metric == "free_cash_flow":
                parts = [rows.get(key) for key in ("operating_cash_flow", "capex")]
                if any(part is None or part.currency != currency or part.unit != currency for part in parts):
                    return None
                return parts[0].value - abs(parts[1].value)
            fact = rows.get(metric)
            return fact.value if fact is not None and fact.currency == currency and fact.unit == unit else None

        for source_metric, output_metric in self.QOQ_METRICS.items():
            anchor = group.get("operating_cash_flow" if source_metric == "free_cash_flow" else source_metric)
            if anchor is None:
                continue
            currency, unit = anchor.currency, anchor.unit
            current = quarter_value(group, source_metric, currency, unit)
            prior_value = quarter_value(previous, source_metric, currency, unit)
            parts = ("operating_cash_flow", "capex") if source_metric == "free_cash_flow" else (source_metric,)
            if not all(same_basis(part) for part in parts):
                continue
            if current is not None and prior_value is not None and prior_value > 0:
                add(output_metric, current / prior_value - 1,
                    f"{source_metric} / prior_quarter({source_metric}) - 1; prior > 0", anchor)

    def _composite_scores(self, company_id, base, lookup, historical, add):
        """Sector-aware composite scores, computed from ingested lines only.

        Piotroski F / Altman Z'' / Beneish M are defined for non-financial
        issuers; bank_health_score is the parallel for banks. Each is emitted
        only when enough of its inputs are present.
        """
        year = base.fiscal_year
        prior = {**historical.get((company_id, year - 1, PeriodKind.FY), {}),
                 **historical.get((company_id, year - 1, PeriodKind.INSTANT), {})}
        prior_assets = historical.get((company_id, year - 2, PeriodKind.INSTANT), {}).get("total_assets")

        def val(source, key):
            fact = source.get(key)
            return fact.value if fact is not None and fact.value is not None else None

        def frac(numerator, denominator):
            return (numerator / denominator) if (numerator is not None and denominator) else None

        # A bank's operating cash flow is dominated by loan-book and deposit
        # movements, so cash-flow accrual and conversion metrics are noise.
        is_bank = "customer_deposits" in lookup or "net_financing_income" in lookup

        ni = val(lookup, "net_income")
        cfo = val(lookup, "operating_cash_flow")
        ta = val(lookup, "total_assets")
        ta_prior = val(prior, "total_assets")

        if not is_bank and ni is not None and cfo is not None and ta:
            add("accrual_ratio", (ni - cfo) / ta,
                "(net_income - operating_cash_flow) / total_assets", lookup["net_income"])
        # fcf_conversion is computed in the main pass (free_cash_flow / ebitda).

        roa_now = frac(ni, ta_prior)
        roa_prior = frac(val(prior, "net_income"), prior_assets.value if prior_assets else None)
        lev_now = frac(val(lookup, "long_term_debt"), ta)
        lev_prior = frac(val(prior, "long_term_debt"), ta_prior)
        cr_now = frac(val(lookup, "current_assets"), val(lookup, "current_liabilities"))
        cr_prior = frac(val(prior, "current_assets"), val(prior, "current_liabilities"))
        gm_now = frac(val(lookup, "gross_profit"), val(lookup, "revenue"))
        gm_prior = frac(val(prior, "gross_profit"), val(prior, "revenue"))
        turn_now = frac(val(lookup, "revenue"), ta_prior)
        turn_prior = frac(val(prior, "revenue"), prior_assets.value if prior_assets else None)
        shares_now, shares_prior = val(lookup, "shares_outstanding"), val(prior, "shares_outstanding")

        signals = {
            "roa_positive": (roa_now > 0) if roa_now is not None else None,
            "cfo_positive": (cfo > 0) if cfo is not None else None,
            "roa_rising": (roa_now > roa_prior) if (roa_now is not None and roa_prior is not None) else None,
            "accruals_ok": (cfo > ni) if (cfo is not None and ni is not None) else None,
            "leverage_falling": (lev_now < lev_prior) if (lev_now is not None and lev_prior is not None) else None,
            "liquidity_rising": (cr_now > cr_prior) if (cr_now is not None and cr_prior is not None) else None,
            "no_dilution": (shares_now <= shares_prior) if (shares_now is not None and shares_prior is not None) else None,
            "margin_rising": (gm_now > gm_prior) if (gm_now is not None and gm_prior is not None) else None,
            "turnover_rising": (turn_now > turn_prior) if (turn_now is not None and turn_prior is not None) else None,
        }
        evaluated = {name: passed for name, passed in signals.items() if passed is not None}
        if not is_bank and len(evaluated) >= 6 and "net_income" in lookup:
            add("piotroski_f_score", Decimal(sum(1 for passed in evaluated.values() if passed)),
                "sum of Piotroski signals passed [" + ", ".join(sorted(evaluated)) + "]",
                base, unit="score")

        ca, cl = val(lookup, "current_assets"), val(lookup, "current_liabilities")
        wc = val(lookup, "working_capital")
        if wc is None and ca is not None and cl is not None:
            wc = ca - cl
        retained = val(lookup, "retained_earnings")
        ebit = val(lookup, "ebit")
        equity = val(lookup, "total_equity")
        liabilities = val(lookup, "total_liabilities")
        if not is_bank and None not in (wc, retained, ebit, equity, liabilities, ta) and ta and liabilities:
            z = (Decimal("3.25") + Decimal("6.56") * (wc / ta) + Decimal("3.26") * (retained / ta)
                 + Decimal("6.72") * (ebit / ta) + Decimal("1.05") * (equity / liabilities))
            add("altman_z_score", z,
                "3.25 + 6.56*(working_capital/total_assets) + 3.26*(retained_earnings/total_assets)"
                " + 6.72*(ebit/total_assets) + 1.05*(total_equity/total_liabilities)",
                base, unit="score")

        ar_n, ar_p = val(lookup, "accounts_receivable"), val(prior, "accounts_receivable")
        sales_n, sales_p = val(lookup, "revenue"), val(prior, "revenue")
        gp_n, gp_p = val(lookup, "gross_profit"), val(prior, "gross_profit")
        ca_n, ca_p = val(lookup, "current_assets"), val(prior, "current_assets")
        ppe_n, ppe_p = val(lookup, "property_plant_equipment"), val(prior, "property_plant_equipment")
        dep_n, dep_p = val(lookup, "depreciation_amortization"), val(prior, "depreciation_amortization")
        sga_n, sga_p = val(lookup, "selling_general_administrative_expense"), val(prior, "selling_general_administrative_expense")
        ltd_n, ltd_p = val(lookup, "long_term_debt"), val(prior, "long_term_debt")
        cl_n, cl_p = val(lookup, "current_liabilities"), val(prior, "current_liabilities")
        beneish_inputs = [ar_n, ar_p, sales_n, sales_p, gp_n, gp_p, ca_n, ca_p, ppe_n, ppe_p,
                          dep_n, dep_p, sga_n, sga_p, ltd_n, ltd_p, cl_n, cl_p, ni, cfo, ta, ta_prior]
        if not is_bank and all(v is not None for v in beneish_inputs) and all(
                v for v in (sales_n, sales_p, ta, ta_prior, ar_p, gp_n, sga_p)):
            dep_n, dep_p, sga_n, sga_p = abs(dep_n), abs(dep_p), abs(sga_n), abs(sga_p)
            dsri = (ar_n / sales_n) / (ar_p / sales_p)
            gmi = (gp_p / sales_p) / (gp_n / sales_n) if gp_n else Decimal(1)
            aqi = ((1 - (ca_n + ppe_n) / ta) / (1 - (ca_p + ppe_p) / ta_prior)
                   if (ca_p + ppe_p) != ta_prior else Decimal(1))
            sgi = sales_n / sales_p
            depi = ((dep_p / (dep_p + ppe_p)) / (dep_n / (dep_n + ppe_n))
                    if (dep_n + ppe_n) and (dep_p + ppe_p) else Decimal(1))
            sgai = (sga_n / sales_n) / (sga_p / sales_p)
            lvgi = (((ltd_n + cl_n) / ta) / ((ltd_p + cl_p) / ta_prior))
            tata = (ni - cfo) / ta
            m = (Decimal("-4.84") + Decimal("0.92") * dsri + Decimal("0.528") * gmi
                 + Decimal("0.404") * aqi + Decimal("0.892") * sgi + Decimal("0.115") * depi
                 - Decimal("0.172") * sgai + Decimal("4.679") * tata - Decimal("0.327") * lvgi)
            add("beneish_m_score", m,
                "-4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI"
                " - 0.172*SGAI + 4.679*TATA - 0.327*LVGI", base, unit="score")

        bank_signals = {
            "roe_positive": (val(lookup, "return_on_equity") > 0) if "return_on_equity" in lookup else None,
            "efficient": (val(lookup, "cost_to_income_ratio") < Decimal("0.45")) if "cost_to_income_ratio" in lookup else None,
            "clean_book": (val(lookup, "nonperforming_loans_ratio") < Decimal("0.03")) if "nonperforming_loans_ratio" in lookup else None,
            "well_provisioned": (val(lookup, "nonperforming_loans_coverage") > 1) if "nonperforming_loans_coverage" in lookup else None,
            "well_capitalised": (val(lookup, "capital_adequacy_ratio") > Decimal("0.15")) if "capital_adequacy_ratio" in lookup else None,
            "efficiency_improving": (val(lookup, "cost_to_income_ratio") < val(prior, "cost_to_income_ratio"))
                if ("cost_to_income_ratio" in lookup and "cost_to_income_ratio" in prior) else None,
            "asset_quality_stable": (val(lookup, "nonperforming_loans_ratio") <= val(prior, "nonperforming_loans_ratio"))
                if ("nonperforming_loans_ratio" in lookup and "nonperforming_loans_ratio" in prior) else None,
        }
        bank_evaluated = {name: passed for name, passed in bank_signals.items() if passed is not None}
        if len(bank_evaluated) >= 4:
            add("bank_health_score", Decimal(sum(1 for passed in bank_evaluated.values() if passed)),
                "sum of bank-quality signals passed [" + ", ".join(sorted(bank_evaluated)) + "]",
                base, unit="score")

    @staticmethod
    def _rounding_half_unit(value: Decimal) -> Decimal:
        """Half the last reported unit of a figure: 0.3312 -> 0.00005, 80104000000 -> 500000.

        A figure with a fractional part keeps its stated decimals. A whole number (often a scaled figure
        such as millions) has ambiguous trailing zeros: they count as rounding only as far as a figure
        showing three significant digits, so 1000 carries +/-5 rather than +/-500, and never less than 0.5."""
        exponent = value.as_tuple().exponent
        if value and value == value.to_integral_value():
            trailing = value.normalize().as_tuple().exponent
            three_significant = value.adjusted() - 2
            exponent = max(0, min(trailing, three_significant))
        return Decimal(1).scaleb(exponent) / 2

    @classmethod
    def _rounding_bound(cls, values: list[Decimal]) -> Decimal:
        """Largest gap rounding alone can explain between a sum and a total; a zero has no stated
        precision, so it takes the finest precision of the other figures."""
        units = [cls._rounding_half_unit(value) for value in values if value]
        finest = min(units, default=Decimal(0))
        return sum(units, Decimal(0)) + finest * sum(1 for value in values if not value)

    def _cumulative_quarters(self, all_facts: list[Fact], current: list[Fact]) -> list[Fact]:
        """Discrete quarters of cumulative-only cash-flow lines: cumulative(start..end) - cumulative(start..prior end).

        A cumulative figure is a fiscal-year, year-to-date or first-quarter row; both figures share the start, currency
        and unit, and the later one ends one quarter after the earlier. A reported quarter is never replaced, and a
        quarter is emitted only when one of its two figures is in the current batch."""
        cumulative = {}
        reported = set()
        for fact in all_facts:
            # a quarter derived earlier is recomputed from the current cumulative figures, never treated as reported
            if fact.metric not in self.CUMULATIVE_QUARTER_FLOWS or fact.scope != "consolidated" or fact.dimensions \
                    or not fact.period_start or (fact.is_calculated and fact.period_kind == PeriodKind.QUARTER):
                continue
            if fact.period_kind == PeriodKind.QUARTER:
                reported.add((fact.company_id, fact.metric, fact.period_end))
            if fact.period_kind in {PeriodKind.FY, PeriodKind.YTD, PeriodKind.QUARTER}:
                cumulative[(fact.company_id, fact.metric, fact.currency, fact.unit, fact.period_start,
                            fact.period_end)] = fact
        current_ids = {id(fact) for fact in current}
        out = []
        for (company_id, metric, currency, unit, start, end), total in cumulative.items():
            if (company_id, metric, end) in reported:
                continue
            earlier = [fact for (cid, m, cur, u, s, e), fact in cumulative.items()
                       if (cid, m, cur, u, s) == (company_id, metric, currency, unit, start) and e < end]
            if not earlier:
                continue
            before = max(earlier, key=lambda fact: fact.period_end)
            quarter_start = date.fromisoformat(before.period_end) + timedelta(days=1)
            if not 80 <= (date.fromisoformat(end) - quarter_start).days <= 100:
                continue
            if id(total) not in current_ids and id(before) not in current_ids:
                continue
            quarter = round((date.fromisoformat(end) - date.fromisoformat(start)).days / Decimal("91.3"))
            out.append(Fact(
                company_id, metric, total.value - before.value, currency, unit, quarter_start.isoformat(), end,
                PeriodKind.QUARTER, total.fiscal_year, int(quarter), total.source_key, total.source_url,
                total.filed_at, is_calculated=True,
                calculation=f"{metric}({start}..{end}) - {metric}({start}..{before.period_end}); "
                            f"sources {total.source_url} and {before.source_url}",
            ))
        return out

    def _ttm(self, facts: list[Fact], target_periods: set[str]) -> list[Fact]:
        out = []
        groups = defaultdict(dict)
        fiscal_years = {}
        cumulative = {}
        for fact in facts:
            identity = (fact.company_id, fact.metric, fact.currency, fact.unit, fact.scope,
                        tuple(sorted(fact.dimensions.items())))
            if fact.period_kind == PeriodKind.FY:
                fiscal_years[(*identity, fact.period_start, fact.period_end)] = fact
            if fact.period_kind in {PeriodKind.FY, PeriodKind.YTD} and fact.period_start:
                cumulative[(identity, fact.period_start, fact.period_end)] = fact
            if (fact.metric in self.TTM_FLOWS or fact.metric in self.TTM_NAMED) and fact.period_kind == PeriodKind.QUARTER:
                groups[(
                    fact.company_id, fact.metric, fact.currency, fact.unit, fact.scope,
                    tuple(sorted(fact.dimensions.items())),
                )][fact.period_end] = fact

        def disagrees(identity, rows_by_period, quarter):
            """Whether the quarter fails to add up with its fiscal year's published cumulative figures."""
            previous_end = (date.fromisoformat(quarter.period_start) - timedelta(days=1)).isoformat()
            for (key, start, end), total in cumulative.items():
                if key != identity or end != quarter.period_end or not start < quarter.period_start:
                    continue
                previous = rows_by_period.get(previous_end)
                before = cumulative.get((identity, start, previous_end)) or (
                    previous if previous is not None and previous.period_start == start else None)
                if before is not None and abs(before.value + quarter.value - total.value) > self._rounding_bound(
                        [before.value, quarter.value, total.value]):
                    return True
            return False

        def window(identity, rows_by_period, end):
            """The four discrete quarters ending on `end` and their sum, or None."""
            rows = sorted((row for period, row in rows_by_period.items() if period <= end),
                          key=lambda item: item.period_end)
            if len(rows) < 4 or rows[-1].period_end != end:
                return None
            last = rows[-4:]
            # Four discrete quarters must be contiguous; a missing quarter is never bridged.
            if any(not current.period_start or
                   date.fromisoformat(current.period_start) - timedelta(days=1)
                   != date.fromisoformat(previous.period_end)
                   for previous, current in zip(last, last[1:])):
                return None
            # A quarter that disagrees with its year's cumulative figures is on another presentation basis than
            # they are; the window then mixes bases if it also holds another quarter of that fiscal year.
            years = [item.fiscal_year for item in last]
            if any(years.count(item.fiscal_year) > 1 and disagrees(identity, rows_by_period, item) for item in last):
                return None
            total = sum((item.value for item in last), Decimal(0))
            annual = fiscal_years.get((*identity, last[0].period_start, end))
            # A window that is exactly a fiscal year must agree with that year's reported value
            # within the rounding the five reported figures can carry; a larger gap is a conflict.
            if annual is not None and abs(total - annual.value) > self._rounding_bound(
                    [item.value for item in last] + [annual.value]):
                return None
            return last, total

        for identity, rows_by_period, end in sorted(
                ((identity, rows_by_period, end) for identity, rows_by_period in groups.items()
                 for end in rows_by_period if end in target_periods), key=lambda item: item[2]):
            current = window(identity, rows_by_period, end)
            if current is None:
                continue
            last, total = current
            base = last[-1]
            out.append(Fact(
                base.company_id, self.TTM_NAMED.get(base.metric, base.metric + "_ttm"), total,
                base.currency, base.unit, last[0].period_start, base.period_end, PeriodKind.TTM,
                base.fiscal_year, base.fiscal_quarter, base.source_key, base.source_url, base.filed_at,
                is_calculated=True, calculation="sum(last 4 discrete quarters)",
                scope=base.scope, dimensions=base.dimensions,
            ))
            growth_metric = self.TTM_GROWTH.get(base.metric)
            if growth_metric is None or base.dimensions or base.scope != "consolidated":
                continue
            # The same trailing window one year earlier: four quarters ending on the prior-year date.
            prior_end = (date.fromisoformat(end) - timedelta(days=365)).isoformat()
            prior_end = next((period for period in rows_by_period
                              if abs((date.fromisoformat(period) - date.fromisoformat(prior_end)).days) <= 3), None)
            prior = window(identity, rows_by_period, prior_end) if prior_end else None
            # Growth on a non-positive base is not defined (as for quarter-on-quarter changes).
            if prior is None or prior[1] <= 0 or prior[0][-1].period_end >= last[0].period_start:
                continue
            out.append(Fact(
                base.company_id, growth_metric, total / prior[1] - 1, "", "ratio",
                last[0].period_start, base.period_end, PeriodKind.TTM, base.fiscal_year, base.fiscal_quarter,
                base.source_key, base.source_url, base.filed_at, is_calculated=True,
                calculation=f"ttm({base.metric}) / ttm({base.metric}) one year earlier - 1",
                scope=base.scope, dimensions=base.dimensions,
            ))
        return out
