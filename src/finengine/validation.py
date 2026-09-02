from collections import defaultdict
from decimal import Decimal
from .models import Fact

class Validator:
    def validate(self, facts: list[Fact]) -> tuple[list[Fact],list[dict]]:
        errors=[]
        for f in facts:
            missing = not f.metric or not f.period_end or not f.unit
            missing_monetary_currency = f.unit in {"SAR", "USD"} and not f.currency
            if missing or missing_monetary_currency:
                errors.append({"code":"required_field","fact":repr(f)})
        groups=defaultdict(dict)
        for f in facts:
            if f.period_kind.value=="instant": groups[(f.company_id,f.period_end)][f.metric]=f.value
        for key,g in groups.items():
            if {"total_assets","total_liabilities","total_equity"} <= g.keys():
                delta=abs(g["total_assets"]-g["total_liabilities"]-g["total_equity"])
                tolerance=max(abs(g["total_assets"])*Decimal("0.005"),Decimal("1"))
                if delta>tolerance: errors.append({"code":"balance_sheet_unbalanced","period":key[1],"delta":str(delta)})
        return facts,errors
