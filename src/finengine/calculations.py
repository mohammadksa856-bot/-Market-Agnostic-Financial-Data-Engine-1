from collections import defaultdict
from decimal import Decimal
from .models import Fact, PeriodKind

class Calculator:
    def calculate(self, facts: list[Fact]) -> list[Fact]:
        out=[]; by=defaultdict(dict)
        for f in facts: by[(f.company_id,f.period_end,f.period_kind,f.fiscal_year,f.fiscal_quarter)][f.metric]=f
        for _,g in by.items():
            base=next(iter(g.values()))
            def add(metric,value,formula):
                out.append(Fact(base.company_id,metric,value,base.currency,base.unit,base.period_start,base.period_end,base.period_kind,base.fiscal_year,base.fiscal_quarter,base.source_key,base.source_url,base.filed_at,is_calculated=True,calculation=formula))
            if "operating_cash_flow" in g and "capex" in g: add("free_cash_flow",g["operating_cash_flow"].value-abs(g["capex"].value),"operating_cash_flow - abs(capex)")
            if "net_income" in g and "revenue" in g and g["revenue"].value: add("net_margin",g["net_income"].value/g["revenue"].value, "net_income / revenue")
            if "total_liabilities" in g and "total_equity" in g and g["total_equity"].value: add("liabilities_to_equity",g["total_liabilities"].value/g["total_equity"].value,"total_liabilities / total_equity")
        return out + self._ttm(facts)
    def _ttm(self,facts):
        out=[]; flows={"revenue","net_income","operating_cash_flow","capex","free_cash_flow"}
        groups=defaultdict(list)
        for f in facts:
            if f.metric in flows and f.period_kind==PeriodKind.QUARTER: groups[(f.company_id,f.metric)].append(f)
        for _,rows in groups.items():
            rows.sort(key=lambda x:x.period_end)
            if len(rows)>=4:
                last=rows[-4:]; b=last[-1]
                out.append(Fact(b.company_id,b.metric+"_ttm",sum((x.value for x in last),Decimal(0)),b.currency,b.unit,last[0].period_start,b.period_end,PeriodKind.TTM,b.fiscal_year,b.fiscal_quarter,b.source_key,b.source_url,b.filed_at,is_calculated=True,calculation="sum(last 4 discrete quarters)"))
        return out
