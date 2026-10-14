from collections import defaultdict
from datetime import date
from decimal import Decimal
from .models import Fact, PeriodKind

class Validator:
    FLOW_METRICS = {
        "revenue", "net_income", "net_income_parent", "operating_income",
        "operating_cash_flow", "capex", "dividends_paid", "free_cash_flow",
    }

    def validate(self, facts: list[Fact], history: list[Fact] | None = None) -> tuple[list[Fact],list[dict]]:
        errors=[]
        for f in facts:
            missing = not f.metric or not f.period_end or not f.unit
            missing_monetary_currency = f.unit in {"SAR", "USD"} and not f.currency
            if missing or missing_monetary_currency:
                errors.append({"code":"required_field","fact":repr(f)})
                continue
            try:
                end=date.fromisoformat(f.period_end)
                start=date.fromisoformat(f.period_start) if f.period_start else None
            except ValueError:
                errors.append({"code":"invalid_period","metric":f.metric,"period_start":f.period_start,"period_end":f.period_end})
                continue
            if start and start>end:
                errors.append({"code":"invalid_period","metric":f.metric,"period_start":f.period_start,"period_end":f.period_end})
            if f.period_kind in {PeriodKind.QUARTER,PeriodKind.YTD} and f.fiscal_quarter not in {1,2,3,4}:
                errors.append({"code":"invalid_fiscal_quarter","metric":f.metric,"period_kind":f.period_kind.value,"fiscal_quarter":f.fiscal_quarter})
            if f.period_kind in {PeriodKind.QUARTER,PeriodKind.YTD,PeriodKind.FY,PeriodKind.TTM} and not start:
                errors.append({"code":"missing_period_start","metric":f.metric,"period_kind":f.period_kind.value})
        groups=defaultdict(dict)
        for f in facts:
            if f.period_kind.value == "instant":
                identity = (
                    f.company_id, f.period_end, f.currency, f.unit, f.scope,
                    tuple(sorted(f.dimensions.items())),
                )
                groups[identity][f.metric] = f.value
        for key,g in groups.items():
            if {"total_assets","total_liabilities","total_equity"} <= g.keys():
                delta=abs(g["total_assets"]-g["total_liabilities"]-g["total_equity"])
                tolerance=max(abs(g["total_assets"])*Decimal("0.005"),Decimal("1"))
                if delta > tolerance:
                    errors.append({
                        "code": "balance_sheet_unbalanced", "period": key[1],
                        "scope": key[4], "dimensions": dict(key[5]), "delta": str(delta),
                    })
        errors.extend(self._validate_rollforwards([*(history or []),*facts],facts))
        return facts,errors

    def _validate_rollforwards(self, all_facts: list[Fact], incoming: list[Fact]) -> list[dict]:
        """Check YTD/FY flow totals only when every required discrete quarter exists."""
        discrete=defaultdict(dict)
        for fact in all_facts:
            if fact.metric not in self.FLOW_METRICS or fact.period_kind != PeriodKind.QUARTER:
                continue
            key=(fact.company_id,fact.metric,fact.fiscal_year,fact.currency,fact.unit,fact.scope,tuple(sorted(fact.dimensions.items())))
            discrete[key][fact.fiscal_quarter]=fact
        errors=[]
        for total in incoming:
            if total.metric not in self.FLOW_METRICS or total.period_kind not in {PeriodKind.YTD,PeriodKind.FY}:
                continue
            expected_quarters=(
                tuple(range(1,(total.fiscal_quarter or 0)+1))
                if total.period_kind == PeriodKind.YTD else (1,2,3,4)
            )
            if not expected_quarters:
                continue
            key=(total.company_id,total.metric,total.fiscal_year,total.currency,total.unit,total.scope,tuple(sorted(total.dimensions.items())))
            available=discrete.get(key,{})
            if not all(quarter in available for quarter in expected_quarters):
                continue
            quarter_sum=sum((available[q].value for q in expected_quarters),Decimal(0))
            delta=abs(total.value-quarter_sum)
            tolerance=max(abs(total.value)*Decimal("0.005"),Decimal("1"))
            if delta>tolerance:
                errors.append({
                    "code":"period_rollforward_mismatch","metric":total.metric,
                    "period_end":total.period_end,"period_kind":total.period_kind.value,
                    "reported":str(total.value),"quarters_sum":str(quarter_sum),
                    "delta":str(delta),"severity":"error",
                })
        return errors
