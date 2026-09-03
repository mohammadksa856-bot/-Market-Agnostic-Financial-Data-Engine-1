from collections import defaultdict
from decimal import Decimal

from .models import Fact, PeriodKind


class Calculator:
    """Deterministic, source-traceable calculations; AI never calculates production facts."""

    TTM_FLOWS = {"revenue", "net_income", "operating_cash_flow", "capex", "free_cash_flow"}
    HISTORY_METRICS = {
        "revenue", "gross_profit", "operating_income", "income_before_income_taxes_and_zakat",
        "net_income", "operating_cash_flow", "capex", "free_cash_flow", "total_assets",
        "total_equity", "total_liabilities", "current_assets", "current_liabilities",
        "cash", "inventory", "accounts_receivable", "property_plant_equipment",
        "current_debt", "long_term_debt", "shares_outstanding", "eps_diluted",
    }
    GROWTH_METRICS = {
        "revenue": "revenue_growth", "gross_profit": "gross_profit_growth",
        "operating_income": "operating_income_growth", "net_income": "net_income_growth",
        "eps_diluted": "eps_growth", "total_assets": "asset_growth",
        "total_equity": "equity_growth", "operating_cash_flow": "operating_cash_flow_growth",
        "free_cash_flow": "free_cash_flow_growth",
    }

    def calculate(self, facts: list[Fact], history: list[Fact] | None = None) -> list[Fact]:
        all_facts = [*(history or []), *facts]
        out: list[Fact] = []
        groups = defaultdict(dict)
        combined = defaultdict(dict)
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
            lookup = combined[(company_id, base.period_end)] if base.period_kind == PeriodKind.FY else group

            def add(metric, value, formula, reference=None, unit="ratio", currency=""):
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
                ratio("operating_margin", "operating_income", "revenue")
                ratio("pretax_margin", "income_before_income_taxes_and_zakat", "revenue")
                ratio("cfo_margin", "operating_cash_flow", "revenue")
                ratio("fcf_margin", "free_cash_flow", "revenue")
                ratio("capex_to_revenue", "capex", "revenue", "abs(capex) / revenue", True)
                ratio("capex_to_cfo", "capex", "operating_cash_flow", "abs(capex) / operating_cash_flow", True)
                ratio("receivables_to_revenue", "accounts_receivable", "revenue")
            if base.period_kind == PeriodKind.INSTANT:
                ratio("liabilities_to_equity", "total_liabilities", "total_equity")
                ratio("liabilities_to_assets", "total_liabilities", "total_assets")
                ratio("equity_ratio", "total_equity", "total_assets")
                ratio("current_ratio", "current_assets", "current_liabilities")
                ratio("cash_ratio", "cash", "current_liabilities")
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

            if base.period_kind == PeriodKind.FY:
                prior_instant = historical.get((company_id, base.fiscal_year - 1, PeriodKind.INSTANT), {})
                if "total_assets" in lookup and "total_assets" in prior_instant:
                    average = (lookup["total_assets"].value + prior_instant["total_assets"].value) / 2
                    if average and "net_income" in lookup:
                        add("return_on_assets", lookup["net_income"].value / average,
                            "net_income / average(total_assets)", lookup["net_income"])
                    if average and "revenue" in lookup:
                        add("asset_turnover", lookup["revenue"].value / average,
                            "revenue / average(total_assets)", lookup["revenue"])
                if "total_equity" in lookup and "total_equity" in prior_instant:
                    average = (lookup["total_equity"].value + prior_instant["total_equity"].value) / 2
                    if average and "net_income" in lookup:
                        add("return_on_equity", lookup["net_income"].value / average,
                            "net_income / average(total_equity)", lookup["net_income"])
            if base.period_kind in {PeriodKind.FY, PeriodKind.INSTANT}:
                prior = historical.get((company_id, base.fiscal_year - 1, base.period_kind), {})
                for source_metric, output_metric in self.GROWTH_METRICS.items():
                    if source_metric in group and source_metric in prior and prior[source_metric].value:
                        add(output_metric, group[source_metric].value / prior[source_metric].value - 1,
                            f"{source_metric} / prior_fy({source_metric}) - 1", group[source_metric])

        target_periods = {fact.period_end for fact in facts if fact.period_kind == PeriodKind.QUARTER}
        return out + self._ttm([*all_facts, *out], target_periods)

    def _ttm(self, facts: list[Fact], target_periods: set[str]) -> list[Fact]:
        out = []
        groups = defaultdict(dict)
        for fact in facts:
            if fact.metric in self.TTM_FLOWS and fact.period_kind == PeriodKind.QUARTER:
                groups[(fact.company_id, fact.metric, fact.currency, fact.unit, fact.scope)][fact.period_end] = fact
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
