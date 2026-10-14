from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from .models import Fact, PeriodKind
from .calculation_lineage import trace, validate_periods
from .normalization import per_share_contract_issues


class Calculator:
    """Deterministic, source-traceable calculations; AI never calculates production facts."""

    def __init__(self):
        self.blocked_calculations = []

    def _prepare(self, output, inputs, operation, parameters=None):
        candidate=trace(output,inputs,operation,parameters)
        try:
            for item in inputs:
                issues=per_share_contract_issues(item.metric,item.unit,item.currency)
                if issues:raise ValueError('financial_input_unit_review_required:'+','.join(issues))
            validate_periods(candidate,candidate.consumed_inputs,operation,candidate.lineage_parameters)
        except (ValueError,TypeError,ArithmeticError) as error:
            self.blocked_calculations.append({
                "code":"calculation_input_contract_blocked", "reason":str(error),
                "company_id":output.company_id,"metric":output.metric,
                "period_end":output.period_end,"period_kind":output.period_kind.value,
                "fiscal_year":output.fiscal_year,"operation":operation,
                "formula":output.calculation,"source_key":output.source_key,"scope":output.scope,
                "inputs":[{"metric":item.metric,"source_key":item.source_key,
                           "value":str(item.value),"currency":item.currency,"unit":item.unit,
                           "dimensions":dict(item.dimensions),
                           "period_start":item.period_start,"period_end":item.period_end,
                           "period_kind":item.period_kind.value,"fiscal_year":item.fiscal_year,
                           "fiscal_quarter":item.fiscal_quarter,"scope":item.scope,
                           "data_point_id":getattr(item,"consumed_data_point_id",None),
                           "version":getattr(item,"consumed_data_point_version",None)} for item in inputs],
            })
            return None
        return candidate

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
        "dividends_per_share": "dividend_per_share_growth",
    }

    def calculate(self, facts: list[Fact], history: list[Fact] | None = None) -> list[Fact]:
        self.blocked_calculations=[]
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

            def add(metric, value, formula, reference=None, unit="ratio", currency="", inputs=(), operation="", parameters=None):
                if metric in group:
                    return
                source = reference or base
                calculated = Fact(
                    source.company_id, metric, value, currency, unit, source.period_start,
                    source.period_end, source.period_kind, source.fiscal_year, source.fiscal_quarter,
                    source.source_key, source.source_url, source.filed_at, is_calculated=True,
                    calculation=formula, scope=source.scope, dimensions=source.dimensions,
                )
                if inputs:
                    calculated = self._prepare(calculated, inputs, operation, parameters)
                    if calculated is None:
                        return
                out.append(calculated)
                group[metric] = calculated
                lookup[metric] = calculated

            def ratio(metric, numerator, denominator, formula=None, absolute=False):
                if numerator in lookup and denominator in lookup and lookup[denominator].value:
                    value = lookup[numerator].value / lookup[denominator].value
                    reference = lookup[numerator]
                    point_reference=(reference.period_kind==PeriodKind.INSTANT or
                                     reference.period_kind==PeriodKind.AS_OF and reference.metric=="market_cap")
                    if point_reference and lookup[denominator].period_kind not in {PeriodKind.INSTANT,PeriodKind.AS_OF}:
                        reference = lookup[denominator]
                    expression=formula or f"{numerator} / {denominator}"
                    if absolute:
                        expression=f"abs({expression})"
                    add(metric, abs(value) if absolute else value,
                        expression, reference,
                        inputs=(lookup[numerator], lookup[denominator]),
                        operation="absolute_ratio" if absolute else "ratio")

            if base.period_kind in {PeriodKind.FY, PeriodKind.QUARTER, PeriodKind.YTD, PeriodKind.TTM}:
                if "insurance_revenue" in group and "revenue" not in group:
                    insurance_revenue = group["insurance_revenue"]
                    add("revenue", insurance_revenue.value,
                        "insurance_revenue (IFRS 17 universal revenue alias)",
                        insurance_revenue, insurance_revenue.unit,
                        insurance_revenue.currency, inputs=(insurance_revenue,), operation="identity")
                if "operating_cash_flow" in group and "capex" in group:
                    add("free_cash_flow", group["operating_cash_flow"].value - abs(group["capex"].value),
                        "operating_cash_flow - abs(capex)", group["operating_cash_flow"],
                        group["operating_cash_flow"].unit, group["operating_cash_flow"].currency,
                        inputs=(group["operating_cash_flow"],group["capex"]), operation="free_cash_flow")
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
                        lookup["general_and_administrative_expense"].currency,
                        inputs=(lookup["general_and_administrative_expense"],lookup["selling_distribution_expense"]),
                        operation="sum_absolute")
                ratio("selling_general_administrative_to_revenue",
                      "selling_general_administrative_expense", "revenue")
                ratio("research_development_to_revenue", "research_and_development_expense", "revenue")
                ratio("share_based_compensation_to_revenue", "share_based_compensation", "revenue")
                ratio("receivables_to_revenue", "accounts_receivable", "revenue")
                if "ebit" in lookup and "depreciation_amortization" in lookup:
                    add("ebitda", lookup["ebit"].value + abs(lookup["depreciation_amortization"].value),
                        "ebit + abs(depreciation_amortization)", lookup["ebit"],
                        lookup["ebit"].unit, lookup["ebit"].currency,
                        inputs=(lookup["ebit"],lookup["depreciation_amortization"]),operation="add_absolute_second")
                ratio("ebit_margin", "ebit", "revenue")
                ratio("ebitda_margin", "ebitda", "revenue")
                ratio("interest_coverage", "ebit", "finance_costs", "ebit / abs(finance_costs)", True)
                # Banking efficiency (fires only when the bank income lines are present)
                if "operating_expense_banking" in lookup and "total_operating_income" in lookup \
                        and lookup["total_operating_income"].value:
                    add("cost_to_income_ratio",
                        abs(lookup["operating_expense_banking"].value) / lookup["total_operating_income"].value,
                        "abs(operating_expense_banking) / total_operating_income",
                        lookup["total_operating_income"],
                        inputs=(lookup["operating_expense_banking"],lookup["total_operating_income"]),
                        operation="absolute_numerator_ratio")
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
                                f"{numerator} / weighted_average_shares",
                                shares if lookup[numerator].period_kind==PeriodKind.INSTANT else lookup[numerator],
                                f"{lookup[numerator].currency}/share", lookup[numerator].currency,
                                inputs=(lookup[numerator],shares),
                                operation="absolute_numerator_ratio" if numerator=="capex" else "ratio")
                    debt = sum((lookup[key].value for key in ("current_debt", "long_term_debt") if key in lookup), Decimal(0))
                    if debt:
                        reference = lookup.get("current_debt") or lookup["long_term_debt"]
                        add("debt_per_share", debt / shares.value,
                            "(current_debt + long_term_debt) / weighted_average_shares",
                            shares, f"{reference.currency}/share", reference.currency,
                            inputs=tuple(lookup[k] for k in ("current_debt","long_term_debt") if k in lookup)+(shares,),
                            operation="sum_numerator_ratio")
                    if "adjusted_net_income" in lookup:
                        add("earnings_per_share_normalized",
                            lookup["adjusted_net_income"].value / shares.value,
                            "adjusted_net_income / weighted_average_shares_diluted",
                            lookup["adjusted_net_income"],
                            f"{lookup['adjusted_net_income'].currency}/share",
                            lookup["adjusted_net_income"].currency,
                            inputs=(lookup["adjusted_net_income"],shares),operation="ratio")
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
                        lookup["current_liabilities"],
                        inputs=tuple(lookup[k] for k in ("cash","short_term_investments","accounts_receivable","current_liabilities")),
                        operation="quick_ratio")
                ratio("inventory_to_assets", "inventory", "total_assets")
                ratio("ppe_to_assets", "property_plant_equipment", "total_assets")
                # Banking balance-sheet ratios (no-op unless the bank lines are present)
                if "gross_loans" not in lookup and "net_loans" in lookup and "credit_loss_allowance" in lookup:
                    add("gross_loans",
                        lookup["net_loans"].value + abs(lookup["credit_loss_allowance"].value),
                        "net_loans + abs(credit_loss_allowance)", lookup["net_loans"],
                        lookup["net_loans"].unit, lookup["net_loans"].currency,
                        inputs=(lookup["net_loans"],lookup["credit_loss_allowance"]),operation="add_absolute_second")
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
                        lookup["customer_deposits"],inputs=tuple(lookup[k] for k in ("demand_deposits","savings_deposits","customer_deposits")),operation="sum_numerator_ratio")
                debt = sum((lookup[key].value for key in ("current_debt", "long_term_debt") if key in lookup), Decimal(0))
                if debt:
                    reference = lookup.get("current_debt") or lookup["long_term_debt"]
                    debt_inputs=tuple(lookup[k] for k in ("current_debt","long_term_debt") if k in lookup)
                    if "total_equity" in lookup and lookup["total_equity"].value:
                        add("debt_to_equity", debt / lookup["total_equity"].value,
                            "(current_debt + long_term_debt) / total_equity", reference,inputs=debt_inputs+(lookup["total_equity"],),operation="sum_numerator_ratio")
                    if "total_assets" in lookup and lookup["total_assets"].value:
                        add("debt_to_assets", debt / lookup["total_assets"].value,
                            "(current_debt + long_term_debt) / total_assets", reference,inputs=debt_inputs+(lookup["total_assets"],),operation="sum_numerator_ratio")
                    if "cash" in lookup:
                        net_debt = debt - lookup["cash"].value
                        if "total_equity" in lookup and lookup["total_equity"].value:
                            add("net_debt_to_equity", net_debt / lookup["total_equity"].value,
                                "(current_debt + long_term_debt - cash) / total_equity", reference,
                                inputs=debt_inputs+(lookup["cash"],lookup["total_equity"]),operation="weighted_arithmetic",
                                parameters={"numerator_weights":["1"]*len(debt_inputs)+["-1","0"],"denominator_weights":["0"]*(len(debt_inputs)+1)+["1"]})
                        if "invested_capital" not in lookup and "total_equity" in lookup:
                            add("invested_capital", lookup["total_equity"].value + net_debt,
                                "total_equity + current_debt + long_term_debt - cash", reference,
                                lookup["total_equity"].unit, lookup["total_equity"].currency,
                                inputs=(lookup["total_equity"],)+debt_inputs+(lookup["cash"],),operation="weighted_arithmetic",
                                parameters={"numerator_weights":["1"]*(len(debt_inputs)+1)+["-1"]})
                    prior_debt_rows = historical.get((company_id, base.fiscal_year - 1, PeriodKind.INSTANT), {})
                    prior_debt = sum((prior_debt_rows[key].value for key in ("current_debt", "long_term_debt") if key in prior_debt_rows), Decimal(0))
                    if prior_debt:
                        prior_debt_inputs=tuple(prior_debt_rows[k] for k in ("current_debt","long_term_debt") if k in prior_debt_rows)
                        add("debt_growth", debt / prior_debt - 1,
                            "(current_debt + long_term_debt) / prior_fy(total_debt) - 1", reference,
                            inputs=debt_inputs+prior_debt_inputs,operation="weighted_arithmetic",
                            parameters={"numerator_weights":["1"]*len(debt_inputs)+["0"]*len(prior_debt_inputs),"denominator_weights":["0"]*len(debt_inputs)+["1"]*len(prior_debt_inputs),"year_offsets":[0]*len(debt_inputs)+[1]*len(prior_debt_inputs),"result_offset":"-1"})
                if "current_assets" in lookup and "current_liabilities" in lookup:
                    add("working_capital", lookup["current_assets"].value - lookup["current_liabilities"].value,
                        "current_assets - current_liabilities", lookup["current_assets"],
                        lookup["current_assets"].unit, lookup["current_assets"].currency,
                        inputs=(lookup["current_assets"],lookup["current_liabilities"]),operation="weighted_arithmetic",parameters={"numerator_weights":["1","-1"]})
                if "current_assets" in lookup and "total_liabilities" in lookup:
                    add("net_current_asset_value",
                        lookup["current_assets"].value - lookup["total_liabilities"].value,
                        "current_assets - total_liabilities", lookup["current_assets"],
                        lookup["current_assets"].unit, lookup["current_assets"].currency,
                        inputs=(lookup["current_assets"],lookup["total_liabilities"]),operation="weighted_arithmetic",parameters={"numerator_weights":["1","-1"]})
                    if all(key in lookup for key in ("cash", "accounts_receivable", "inventory")):
                        conservative = (lookup["cash"].value + Decimal("0.75") * lookup["accounts_receivable"].value +
                                        Decimal("0.5") * lookup["inventory"].value - lookup["total_liabilities"].value)
                        add("graham_net_net", conservative,
                            "cash + 0.75 * accounts_receivable + 0.5 * inventory - total_liabilities",
                            lookup["current_assets"], lookup["current_assets"].unit,
                            lookup["current_assets"].currency,
                            inputs=tuple(lookup[k] for k in ("cash","accounts_receivable","inventory","total_liabilities")),operation="weighted_arithmetic",parameters={"numerator_weights":["1","0.75","0.5","-1"]})
                if "total_equity" in lookup:
                    intangible = lookup.get("intangible_assets")
                    tangible = lookup["total_equity"].value - (intangible.value if intangible else Decimal(0))
                    tangible_inputs=(lookup["total_equity"],)+((intangible,) if intangible else ())
                    tangible_weights=["1"]+(["-1"] if intangible else [])
                    add("tangible_book_value", tangible, "total_equity - intangible_assets",
                        lookup["total_equity"], lookup["total_equity"].unit,
                        lookup["total_equity"].currency,inputs=tangible_inputs,operation="weighted_arithmetic",parameters={"numerator_weights":tangible_weights})
                    shares = lookup.get("shares_outstanding")
                    if shares and shares.value:
                        add("book_value_per_share", lookup["total_equity"].value / shares.value,
                            "total_equity / shares_outstanding", lookup["total_equity"],
                            f"{lookup['total_equity'].currency}/share", lookup["total_equity"].currency,
                            inputs=(lookup["total_equity"],shares),operation="ratio")
                        add("tangible_book_value_per_share", tangible / shares.value,
                            "(total_equity - intangible_assets) / shares_outstanding",
                            lookup["total_equity"], f"{lookup['total_equity'].currency}/share",
                            lookup["total_equity"].currency,inputs=tangible_inputs+(shares,),operation="weighted_arithmetic",
                            parameters={"numerator_weights":tangible_weights+["0"],"denominator_weights":["0"]*len(tangible_inputs)+["1"]})
                        if "retained_earnings" in lookup:
                            add("retained_earnings_per_share",
                                lookup["retained_earnings"].value / shares.value,
                                "retained_earnings / shares_outstanding", lookup["retained_earnings"],
                                f"{lookup['retained_earnings'].currency}/share",
                                lookup["retained_earnings"].currency,inputs=(lookup["retained_earnings"],shares),operation="ratio")

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
                        inputs=(lookup["total_hydrocarbon_reserves"],lookup["total_hydrocarbon_production"]),operation="weighted_arithmetic",
                        parameters={"numerator_weights":["1000","0"],"denominator_weights":["0","365"]},
                    )
                prior_instant = historical.get((company_id, base.fiscal_year - 1, PeriodKind.INSTANT), {})
                if "total_assets" in lookup and "total_assets" in prior_instant:
                    average = (lookup["total_assets"].value + prior_instant["total_assets"].value) / 2
                    if average and "net_income" in lookup:
                        add("return_on_assets", lookup["net_income"].value / average,
                            "net_income / average(total_assets)", lookup["net_income"],
                            inputs=(lookup["net_income"],lookup["total_assets"],prior_instant["total_assets"]),operation="average_ratio")
                    if average and "revenue" in lookup:
                        add("asset_turnover", lookup["revenue"].value / average,
                            "revenue / average(total_assets)", lookup["revenue"],
                            inputs=(lookup["revenue"],lookup["total_assets"],prior_instant["total_assets"]),operation="average_ratio")
                    if average and "operating_cash_flow" in lookup:
                        add("cash_return_on_assets", lookup["operating_cash_flow"].value / average,
                            "operating_cash_flow / average(total_assets)", lookup["operating_cash_flow"],
                            inputs=(lookup["operating_cash_flow"],lookup["total_assets"],prior_instant["total_assets"]),operation="average_ratio")
                if "total_equity" in lookup and "total_equity" in prior_instant:
                    average = (lookup["total_equity"].value + prior_instant["total_equity"].value) / 2
                    if average and "net_income" in lookup:
                        add("return_on_equity", lookup["net_income"].value / average,
                            "net_income / average(total_equity)", lookup["net_income"],
                            inputs=(lookup["net_income"],lookup["total_equity"],prior_instant["total_equity"]),operation="average_ratio")
                    if average and "operating_cash_flow" in lookup:
                        add("cash_return_on_equity", lookup["operating_cash_flow"].value / average,
                            "operating_cash_flow / average(total_equity)", lookup["operating_cash_flow"],
                            inputs=(lookup["operating_cash_flow"],lookup["total_equity"],prior_instant["total_equity"]),operation="average_ratio")
                    current_intangible = lookup["intangible_assets"].value if "intangible_assets" in lookup else Decimal(0)
                    prior_intangible = prior_instant["intangible_assets"].value if "intangible_assets" in prior_instant else Decimal(0)
                    current_tangible = lookup["total_equity"].value - current_intangible
                    prior_tangible = prior_instant["total_equity"].value - prior_intangible
                    average_tangible = (current_tangible + prior_tangible) / 2
                    if average_tangible and "net_income" in lookup:
                        tangible_average_inputs=(lookup["net_income"],lookup["total_equity"],prior_instant["total_equity"])
                        intangible_current=(lookup["intangible_assets"],) if "intangible_assets" in lookup else ()
                        intangible_prior=(prior_instant["intangible_assets"],) if "intangible_assets" in prior_instant else ()
                        all_tangible_inputs=tangible_average_inputs+intangible_current+intangible_prior
                        add("return_on_tangible_equity", lookup["net_income"].value / average_tangible,
                            "net_income / average(total_equity - intangible_assets)", lookup["net_income"],
                            inputs=all_tangible_inputs,operation="weighted_arithmetic",
                            parameters={"numerator_weights":["1"]+["0"]*(len(all_tangible_inputs)-1),"denominator_weights":["0","0.5","0.5"]+["-0.5"]*(len(intangible_current)+len(intangible_prior)),"year_offsets":[0,0,1]+[0]*len(intangible_current)+[1]*len(intangible_prior)})
                # Banking: margins on average earning assets / average loans
                earning_keys = ("net_loans", "bank_investments", "due_from_banks")
                if "net_financing_income" in lookup and all(k in lookup for k in earning_keys) \
                        and all(k in prior_instant for k in earning_keys):
                    average_earning = (sum(lookup[k].value for k in earning_keys)
                                       + sum(prior_instant[k].value for k in earning_keys)) / 2
                    if average_earning:
                        add("net_interest_margin", lookup["net_financing_income"].value / average_earning,
                            "net_financing_income / average(net_loans + bank_investments + due_from_banks)",
                            lookup["net_financing_income"],
                            inputs=(lookup["net_financing_income"],)+tuple(lookup[k] for k in earning_keys)+tuple(prior_instant[k] for k in earning_keys),operation="average_sum_ratio")
                if "provision_expense" in lookup and "net_loans" in lookup and "net_loans" in prior_instant:
                    average_loans = (lookup["net_loans"].value + prior_instant["net_loans"].value) / 2
                    if average_loans:
                        add("cost_of_risk", abs(lookup["provision_expense"].value) / average_loans,
                            "abs(provision_expense) / average(net_loans)", lookup["provision_expense"],
                            inputs=(lookup["provision_expense"],lookup["net_loans"],prior_instant["net_loans"]),operation="absolute_average_ratio")
                if "accounts_receivable" in lookup and "accounts_receivable" in prior_instant and "revenue" in lookup:
                    average = (lookup["accounts_receivable"].value + prior_instant["accounts_receivable"].value) / 2
                    if average:
                        add("receivables_turnover", lookup["revenue"].value / average,
                            "revenue / average(accounts_receivable)", lookup["revenue"],
                            inputs=(lookup["revenue"],lookup["accounts_receivable"],prior_instant["accounts_receivable"]),operation="average_ratio")
                        add("days_sales_outstanding", average / lookup["revenue"].value * Decimal(365),
                            "average(accounts_receivable) / revenue * 365", lookup["revenue"],
                            inputs=(lookup["revenue"],lookup["accounts_receivable"],prior_instant["accounts_receivable"]),operation="average_days")
                instant_now = historical.get((company_id, base.fiscal_year, PeriodKind.INSTANT), {})
                debt = sum((instant_now[key].value for key in ("current_debt", "long_term_debt") if key in instant_now), Decimal(0))
                debt_inputs=tuple(instant_now[k] for k in ("current_debt","long_term_debt") if k in instant_now)
                if debt and "ebitda" in lookup and lookup["ebitda"].value:
                    add("debt_to_ebitda", debt / lookup["ebitda"].value,
                        "(current_debt + long_term_debt) / ebitda", lookup["ebitda"],inputs=debt_inputs+(lookup["ebitda"],),operation="sum_numerator_ratio")
                    net_debt = instant_now.get("net_debt")
                    if net_debt:
                        add("net_debt_to_ebitda", net_debt.value / lookup["ebitda"].value,
                            "net_debt / ebitda", lookup["ebitda"],inputs=(net_debt,lookup["ebitda"]),operation="ratio")
                if debt:
                    if "operating_cash_flow" in lookup:
                        add("cfo_to_debt", lookup["operating_cash_flow"].value / debt,
                            "operating_cash_flow / total_debt", lookup["operating_cash_flow"],inputs=(lookup["operating_cash_flow"],)+debt_inputs,
                            operation="weighted_arithmetic",parameters={"numerator_weights":["1"]+["0"]*len(debt_inputs),"denominator_weights":["0"]+["1"]*len(debt_inputs)})
                    if "free_cash_flow" in lookup:
                        add("fcf_to_debt", lookup["free_cash_flow"].value / debt,
                            "free_cash_flow / total_debt", lookup["free_cash_flow"],inputs=(lookup["free_cash_flow"],)+debt_inputs,
                            operation="weighted_arithmetic",parameters={"numerator_weights":["1"]+["0"]*len(debt_inputs),"denominator_weights":["0"]+["1"]*len(debt_inputs)})
                    capital = debt + (instant_now["total_equity"].value if "total_equity" in instant_now else Decimal(0))
                    if capital:
                        capital_inputs=debt_inputs+((instant_now["total_equity"],) if "total_equity" in instant_now else ())
                        add("total_debt_to_capital", debt / capital,
                            "total_debt / (total_debt + total_equity)",
                            instant_now.get("current_debt") or instant_now["long_term_debt"],inputs=capital_inputs,operation="weighted_arithmetic",
                            parameters={"numerator_weights":["1"]*len(debt_inputs)+["0"]*(len(capital_inputs)-len(debt_inputs)),"denominator_weights":["1"]*len(capital_inputs)})
                        if "long_term_debt" in instant_now:
                            add("long_term_debt_to_capital", instant_now["long_term_debt"].value / capital,
                                "long_term_debt / (total_debt + total_equity)", instant_now["long_term_debt"],inputs=capital_inputs,operation="weighted_arithmetic",
                                parameters={"numerator_weights":["1" if f.metric=="long_term_debt" else "0" for f in capital_inputs],"denominator_weights":["1"]*len(capital_inputs)})
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
                                lookup[source_metric],inputs=(lookup[source_metric],prior[source_metric]),
                                operation="cagr",parameters={"years":years})
            if base.period_kind in {PeriodKind.FY, PeriodKind.INSTANT}:
                prior = historical.get((company_id, base.fiscal_year - 1, base.period_kind), {})
                for source_metric, output_metric in self.GROWTH_METRICS.items():
                    if source_metric in group and source_metric in prior and prior[source_metric].value:
                        add(output_metric, group[source_metric].value / prior[source_metric].value - 1,
                            f"{source_metric} / prior_fy({source_metric}) - 1", group[source_metric],
                            inputs=(group[source_metric],prior[source_metric]),operation="growth")

        # Composite scores run last: they read ratios (cost_to_income_ratio,
        # nonperforming_loans_ratio, ROE, ...) that the passes above computed.
        for (company_id, period_end, period_kind, _, _), group in groups.items():
            if period_kind != PeriodKind.FY:
                continue
            base = next(iter(group.values()))
            lookup = combined[(company_id, period_end)]

            def score_add(metric, value, formula, reference=None, unit="ratio", currency="", inputs=(), operation="", parameters=None):
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
                if inputs:
                    calculated=self._prepare(calculated,inputs,operation,parameters)
                    if calculated is None:
                        return
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
            candidate=self._prepare(Fact(
                source.company_id, f"{segment}_ebitda",
                ebit.value + abs(depreciation.value), source.currency, source.unit,
                source.period_start, source.period_end, source.period_kind, source.fiscal_year,
                source.fiscal_quarter, source.source_key, source.source_url, source.filed_at,
                is_calculated=True,
                calculation=f"{ebit_key} + abs({depreciation_key})",
                scope=source.scope, dimensions=source.dimensions,
            ),(ebit,depreciation),"add_absolute_second")
            if candidate is not None:
                out.append(candidate)

        first_quarters = self._first_quarters([*all_facts, *out])
        target_periods = {fact.period_end for fact in facts if fact.period_kind == PeriodKind.QUARTER
                          or (fact.period_kind == PeriodKind.YTD and fact.fiscal_quarter == 1)}
        return out + first_quarters + self._ttm([*all_facts, *out, *first_quarters], target_periods)

    def _first_quarters(self, facts: list[Fact]) -> list[Fact]:
        """First-quarter YTD is the same interval, not a guessed value."""
        from dataclasses import replace
        def key(f):
            return (f.company_id, f.metric, f.period_end, f.currency, f.unit,
                    f.scope, tuple(sorted(f.dimensions.items())))
        existing = {key(f) for f in facts if f.period_kind == PeriodKind.QUARTER}
        out = []
        for fact in facts:
            if fact.period_kind != PeriodKind.YTD or fact.fiscal_quarter != 1 or fact.metric not in self.TTM_FLOWS:
                continue
            try:
                days = (date.fromisoformat(fact.period_end) - date.fromisoformat(fact.period_start)).days + 1
            except (TypeError, ValueError):
                continue
            if not 80 <= days <= 100 or key(fact) in existing:
                continue
            candidate=self._prepare(replace(fact, period_kind=PeriodKind.QUARTER, is_calculated=True,
                               calculation="Q1 discrete flow equals Q1 YTD over identical dates"),
                             (fact,),"q1_identity")
            if candidate is not None:
                out.append(candidate)
            existing.add(key(fact))
        return out

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
        original_add=add
        operand_keys={
            "accrual_ratio": ("net_income","operating_cash_flow","total_assets"),
            "piotroski_f_score": ("net_income","operating_cash_flow","total_assets","long_term_debt","current_assets","current_liabilities","gross_profit","revenue","shares_outstanding"),
            "altman_z_score": ("working_capital","current_assets","current_liabilities","retained_earnings","ebit","total_equity","total_liabilities","total_assets"),
            "beneish_m_score": ("accounts_receivable","revenue","gross_profit","current_assets","property_plant_equipment","depreciation_amortization","selling_general_administrative_expense","long_term_debt","current_liabilities","net_income","operating_cash_flow","total_assets"),
            "bank_health_score": ("return_on_equity","cost_to_income_ratio","nonperforming_loans_ratio","nonperforming_loans_coverage","capital_adequacy_ratio"),
        }
        def add(metric,value,formula,reference=None,unit="ratio",currency=""):
            if metric not in operand_keys:
                return original_add(metric,value,formula,reference,unit,currency)
            selected=[]; aliases=[]
            current_keys=operand_keys[metric]
            if metric=="altman_z_score" and "working_capital" in lookup:
                current_keys=tuple(k for k in current_keys if k not in {"current_assets","current_liabilities"})
            prior_keys={
                "accrual_ratio":(), "altman_z_score":(),
                "piotroski_f_score":tuple(k for k in operand_keys[metric] if k!="operating_cash_flow"),
                "beneish_m_score":tuple(k for k in operand_keys[metric] if k not in {"net_income","operating_cash_flow"}),
                "bank_health_score":("cost_to_income_ratio","nonperforming_loans_ratio"),
            }[metric]
            for role,source in (("now",lookup),("prior_fy",historical.get((company_id,year-1,PeriodKind.FY),{})),("prior_instant",historical.get((company_id,year-1,PeriodKind.INSTANT),{}))):
                keys=current_keys+("customer_deposits","net_financing_income") if role=="now" else prior_keys
                for key in keys:
                    if key in source:
                        selected.append(source[key]); aliases.append(f"{role}.{key}")
            if metric=="piotroski_f_score" and prior_assets:
                selected.append(prior_assets); aliases.append("prior2_instant.total_assets")
            return original_add(metric,value,formula,reference,unit,currency,
                                inputs=selected,operation="composite_replay",parameters={"year":year,"metric":metric,"aliases":aliases})

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
                # Four available observations are not necessarily four
                # consecutive quarters. Reject gaps, overlaps and YTD values
                # accidentally labelled as discrete quarters.
                try:
                    spans = [(date.fromisoformat(f.period_start), date.fromisoformat(f.period_end)) for f in last]
                except (TypeError, ValueError):
                    continue
                if any(not 80 <= (end - start).days + 1 <= 100 for start, end in spans):
                    continue
                if any(spans[i][0] != spans[i-1][1] + timedelta(days=1) for i in range(1, 4)):
                    continue
                # Calendar years and 52/53-week fiscal years are supported;
                # longer sequences must never be labelled trailing 12 months.
                if not 350 <= (spans[-1][1] - spans[0][0]).days + 1 <= 371:
                    continue
                base = last[-1]
                candidate=self._prepare(Fact(
                    base.company_id, base.metric + "_ttm", sum((item.value for item in last), Decimal(0)),
                    base.currency, base.unit, last[0].period_start, base.period_end, PeriodKind.TTM,
                    base.fiscal_year, base.fiscal_quarter, base.source_key, base.source_url, base.filed_at,
                    is_calculated=True, calculation="sum(last 4 discrete quarters)",
                    scope=base.scope, dimensions=base.dimensions,
                ),last,"ttm_sum")
                if candidate is not None:
                    out.append(candidate)
        return out
