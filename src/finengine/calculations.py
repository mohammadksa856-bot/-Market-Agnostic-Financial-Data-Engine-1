from collections import defaultdict
from decimal import Decimal
from .models import Fact, PeriodKind

class Calculator:
    TTM_FLOWS = {"revenue", "net_income", "operating_cash_flow", "capex", "free_cash_flow"}

    def calculate(self, facts: list[Fact], history: list[Fact] | None = None) -> list[Fact]:
        out=[]; by=defaultdict(dict)
        for f in facts: by[(f.company_id,f.period_end,f.period_kind,f.fiscal_year,f.fiscal_quarter)][f.metric]=f
        for _,g in by.items():
            base=next(iter(g.values()))
            def add(metric,value,formula,reference=None,currency=None,unit=None):
                source=reference or base
                out.append(Fact(source.company_id,metric,value,source.currency if currency is None else currency,source.unit if unit is None else unit,source.period_start,source.period_end,source.period_kind,source.fiscal_year,source.fiscal_quarter,source.source_key,source.source_url,source.filed_at,is_calculated=True,calculation=formula))
            if "operating_cash_flow" in g and "capex" in g:
                add("free_cash_flow",g["operating_cash_flow"].value-abs(g["capex"].value),"operating_cash_flow - abs(capex)",g["operating_cash_flow"])
            if "net_income" in g and "revenue" in g and g["revenue"].value:
                add("net_margin",g["net_income"].value/g["revenue"].value, "net_income / revenue",g["net_income"],"","ratio")
            if "total_liabilities" in g and "total_equity" in g and g["total_equity"].value:
                add("liabilities_to_equity",g["total_liabilities"].value/g["total_equity"].value,"total_liabilities / total_equity",g["total_liabilities"],"","ratio")
        target_periods = {f.period_end for f in facts if f.period_kind == PeriodKind.QUARTER}
        return out + self._ttm([*(history or []), *facts, *out], target_periods)

    def _ttm(self, facts: list[Fact], target_periods: set[str]) -> list[Fact]:
        out=[]; groups=defaultdict(dict)
        for f in facts:
            if f.metric in self.TTM_FLOWS and f.period_kind==PeriodKind.QUARTER:
                groups[(f.company_id,f.metric,f.currency,f.unit,f.scope)][f.period_end]=f
        for rows_by_period in groups.values():
            rows=sorted(rows_by_period.values(),key=lambda x:x.period_end)
            if len(rows)>=4 and rows[-1].period_end in target_periods:
                last=rows[-4:]; b=last[-1]
                out.append(Fact(b.company_id,b.metric+"_ttm",sum((x.value for x in last),Decimal(0)),b.currency,b.unit,last[0].period_start,b.period_end,PeriodKind.TTM,b.fiscal_year,b.fiscal_quarter,b.source_key,b.source_url,b.filed_at,is_calculated=True,calculation="sum(last 4 discrete quarters)",scope=b.scope,dimensions=b.dimensions))
        return out
