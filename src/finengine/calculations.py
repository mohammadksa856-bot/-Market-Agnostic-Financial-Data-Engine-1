from collections import defaultdict
from decimal import Decimal

from .models import Fact, PeriodKind


class Calculator:
    """Deterministic, source-traceable calculations; AI never calculates production facts."""

    TTM_FLOWS = {"revenue", "net_income", "operating_cash_flow", "capex", "free_cash_flow"}
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
        "dividends_per_share",
        "selling_general_administrative_expense", "research_and_development_expense",
        "share_based_compensation",
        "total_hydrocarbon_production", "total_hydrocarbon_reserves",
        "upstream_ebit", "downstream_ebit", "corporate_ebit",
        "upstream_depreciation_amortization", "downstream_depreciation_amortization",
        "corporate_depreciation_amortization",
    }
    GROWTH_METRICS = {
        "revenue": "revenue_growth", "gross_profit": "gross_profit_growth",
        "operating_income": "operating_income_growth", "net_income": "net_income_growth",
        "eps_diluted": "eps_growth", "total_assets": "asset_growth",
        "total_equity": "equity_growth", "operating_cash_flow": "operating_cash_flow_growth",
        "free_cash_flow": "free_cash_flow_growth",
        "ebitda": "ebitda_growth", "dividends_paid": "dividend_growth",
        "dividends_per_share": "dividend_per_share_growth",
    }

    def calculate(self, facts: list[Fact], history: list[Fact] | None = None) -> list[Fact]:
        all_facts = [*(history or []), *facts]
        out: list[Fact] = []
        groups = defaultdict(dict)
        combined = defaultdict(dict)
        for fact in all_facts:
            if fact.scope == "consolidated" and not fact.dimensions:
                combined[(fact.company_id, fact.period_end)].setdefault(fact.metric, fact)
        for fact in facts:
            if fact.scope == "consolidated" and not fact.dimensions:
                groups[(fact.company_id, fact.period_end, fact.period_kind,
                        fact.fiscal_year, fact.fiscal_quarter)][fact.metric] = fact
                combined[(fact.company_id, fact.period_end)][fact.metric] = fact
        historical = defaultdict(dict)
        for fact in all_facts:
            if fact.scope == "consolidated" and not fact.dimensions:
                historical[(fact.company_id, fact.fiscal_year, fact.period_kind)][fact.metric] = fact

        for (company_id, _, _, _, _), group in groups.items():
            base = next(iter(group.values()))
            lookup = combined[(company_id, base.period_end)] if base.period_kind in {PeriodKind.FY, PeriodKind.INSTANT} else group

            def add(metric, value, formula, reference=None, unit="ratio", currency=""):
                if metric in group:
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
                ratio("capex_to_depreciation", "capex", "depreciation_amortization",
                      "abs(capex) / abs(depreciation_amortization)", True)
                ratio("capex_to_depreciation_amortization", "capex", "depreciation_amortization",
                      "abs(capex) / abs(depreciation_amortization)", True)
                if ("selling_general_administrative_expense" not in lookup and
                        "general_and_administrative_expense" in lookup and
                        "selling_distribution_expense" in lookup):
                    add("selling_general_administrative_expense",
                        abs(lookup["general_and_administrative_expense"].value) +
                        abs(lookup["selling_distribution_expense"].value),
                        "abs(general_and_administrative_expense) + abs(selling_distribution_expense)",
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
                if "total_equity" in lookup:
                    intangible = lookup.get("intangible_assets")
                    tangible = lookup["total_equity"].value - (intangible.value if intangible else Decimal(0))
                    add("tangible_book_value", tangible, "total_equity - intangible_assets",
                        lookup["total_equity"], lookup["total_equity"].unit,
                        lookup["total_equity"].currency)
                    shares = lookup.get("shares_outstanding")
                    if shares and shares.value:
                        add("book_value_per_share", lookup["total_equity"].value / shares.value,
                            "total_equity / shares_outstanding", lookup["total_equity"],
                            f"{lookup['total_equity'].currency}/share", lookup["total_equity"].currency)
                        add("tangible_book_value_per_share", tangible / shares.value,
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
                if "total_assets" in lookup and "total_assets" in prior_instant:
                    average = (lookup["total_assets"].value + prior_instant["total_assets"].value) / 2
                    if average and "net_income" in lookup:
                        add("return_on_assets", lookup["net_income"].value / average,
                            "net_income / average(total_assets)", lookup["net_income"])
                    if average and "revenue" in lookup:
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
                if "accounts_receivable" in lookup and "accounts_receivable" in prior_instant and "revenue" in lookup:
                    average = (lookup["accounts_receivable"].value + prior_instant["accounts_receivable"].value) / 2
                    if average:
                        add("receivables_turnover", lookup["revenue"].value / average,
                            "revenue / average(accounts_receivable)", lookup["revenue"])
                        add("days_sales_outstanding", average / lookup["revenue"].value * Decimal(365),
                            "average(accounts_receivable) / revenue * 365", lookup["revenue"])
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
                for source_metric in ("revenue", "net_income", "eps_diluted", "dividends_per_share"):
                    if source_metric not in lookup or not lookup[source_metric].value:
                        continue
                    for years in (3, 5):
                        prior = historical.get((company_id, base.fiscal_year - years, PeriodKind.FY), {})
                        if source_metric in prior and prior[source_metric].value > 0 and lookup[source_metric].value > 0:
                            cagr_stem = {
                                "eps_diluted": "eps", "dividends_per_share": "dividend"
                            }.get(source_metric, source_metric)
                            add(f"{cagr_stem}_cagr_{years}y",
                                (lookup[source_metric].value / prior[source_metric].value) ** (Decimal(1) / Decimal(years)) - 1,
                                f"({source_metric} / prior_{years}y({source_metric})) ^ (1/{years}) - 1",
                                lookup[source_metric])
            if base.period_kind in {PeriodKind.FY, PeriodKind.INSTANT}:
                prior = historical.get((company_id, base.fiscal_year - 1, base.period_kind), {})
                for source_metric, output_metric in self.GROWTH_METRICS.items():
                    if source_metric in group and source_metric in prior and prior[source_metric].value:
                        add(output_metric, group[source_metric].value / prior[source_metric].value - 1,
                            f"{source_metric} / prior_fy({source_metric}) - 1", group[source_metric])

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

    def _ttm(self, facts: list[Fact], target_periods: set[str]) -> list[Fact]:
        out = []
        groups = defaultdict(dict)
        for fact in facts:
            if fact.metric in self.TTM_FLOWS and fact.period_kind == PeriodKind.QUARTER:
                groups[(
                    fact.company_id, fact.metric, fact.currency, fact.unit, fact.scope,
                    tuple(sorted(fact.dimensions.items())),
                )][fact.period_end] = fact
        for rows_by_period in groups.values():
            rows = sorted(rows_by_period.values(), key=lambda item: item.period_end)
            if len(rows) >= 4 and rows[-1].period_end in target_periods:
                last = rows[-4:]
                base = last[-1]
                out.append(Fact(
                    base.company_id, base.metric + "_ttm", sum((item.value for item in last), Decimal(0)),
                    base.currency, base.unit, last[0].period_start, base.period_end, PeriodKind.TTM,
                    base.fiscal_year, base.fiscal_quarter, base.source_key, base.source_url, base.filed_at,
                    is_calculated=True, calculation="sum(last 4 discrete quarters)",
                    scope=base.scope, dimensions=base.dimensions,
                ))
        return out
