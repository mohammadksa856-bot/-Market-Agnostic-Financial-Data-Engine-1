"""Explicit, additive flow quarter derivation; no publication side effects."""
from dataclasses import fields
from datetime import date, timedelta
from .models import Fact, PeriodKind
from .calculation_lineage import trace

ADDITIVE_FLOW_METRICS = frozenset({
    "revenue", "net_income", "operating_income", "gross_profit", "cost_of_revenue",
    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "capital_expenditures", "capex",
})

def derive_quarter(current, previous=None, *, accounting_basis, restatement_version,
                   previous_accounting_basis=None, previous_restatement_version=None):
    """Inputs must be B06 BoundFacts, with independently supplied accounting editions."""
    for item in (current,) if previous is None else (current, previous):
        if getattr(item, "consumed_data_point_id", None) is None or getattr(item, "consumed_data_point_version", None) is None:
            raise ValueError("bound input id/version required")
    if not accounting_basis or not restatement_version:
        raise ValueError("accounting basis and restatement edition required")
    params = {"accounting_basis": accounting_basis, "restatement_version": restatement_version,
              "previous_accounting_basis": previous_accounting_basis,
              "previous_restatement_version": previous_restatement_version}
    quarter = 4 if current.period_kind == PeriodKind.FY else current.fiscal_quarter
    start = current.period_start if previous is None else (date.fromisoformat(previous.period_end) + timedelta(days=1)).isoformat()
    data = {f.name: getattr(current, f.name) for f in fields(Fact)}
    data.update(value=current.value if previous is None else current.value - previous.value,
                period_start=start, period_kind=PeriodKind.QUARTER, fiscal_quarter=quarter,
                is_calculated=True, calculation="FY - YTD Q3" if quarter == 4 else "YTD quarter difference")
    output = Fact(**data)
    operands = (current,) if previous is None else (current, previous)
    validate_derived_quarter(output, operands, params)
    return trace(output, operands, "derived_quarter", params)

def validate_derived_quarter(output, inputs, parameters):
    if len(inputs) not in (1, 2) or output.metric not in ADDITIVE_FLOW_METRICS:
        raise ValueError("quarter derivation requires approved additive flow metric")
    current = inputs[0]
    for item in inputs:
        if (item.company_id, item.metric, item.currency, item.unit, item.scope, item.dimensions, item.fiscal_year) != (output.company_id, output.metric, output.currency, output.unit, output.scope, output.dimensions, output.fiscal_year):
            raise ValueError("quarter inputs do not align")
    if not parameters.get("accounting_basis") or not parameters.get("restatement_version"):
        raise ValueError("accounting edition missing")
    if output.period_kind != PeriodKind.QUARTER or output.period_end != current.period_end:
        raise ValueError("quarter output kind/end mismatch")
    if len(inputs) == 1:
        if current.period_kind != PeriodKind.YTD or current.fiscal_quarter != 1 or output.fiscal_quarter != 1 or current.period_start != output.period_start:
            raise ValueError("single input only valid for Q1 YTD")
    else:
        previous = inputs[1]
        if parameters.get("previous_accounting_basis") != parameters["accounting_basis"] or parameters.get("previous_restatement_version") != parameters["restatement_version"]:
            raise ValueError("mixed accounting/restatement editions")
        quarter = 4 if current.period_kind == PeriodKind.FY else current.fiscal_quarter
        if current.period_kind not in (PeriodKind.FY, PeriodKind.YTD) or quarter not in (2, 3, 4) or previous.period_kind != PeriodKind.YTD or previous.fiscal_quarter != quarter - 1:
            raise ValueError("cumulative quarter sequence mismatch")
        if current.period_start != previous.period_start or output.fiscal_quarter != quarter or output.period_start != (date.fromisoformat(previous.period_end) + timedelta(days=1)).isoformat():
            raise ValueError("cumulative interval mismatch")
        if current.period_kind == PeriodKind.YTD and quarter == 4:
            raise ValueError("Q4 requires FY")
        cumulative_days = (date.fromisoformat(current.period_end) - date.fromisoformat(current.period_start)).days + 1
        prior_days = (date.fromisoformat(previous.period_end) - date.fromisoformat(previous.period_start)).days + 1
        if not 80 * quarter <= cumulative_days <= 100 * quarter or not 80 * (quarter - 1) <= prior_days <= 100 * (quarter - 1):
            raise ValueError("fiscal cumulative duration mismatch")
        if current.period_kind == PeriodKind.FY and not 350 <= cumulative_days <= 371:
            raise ValueError("transition FY cannot supply ordinary Q4")
    days = (date.fromisoformat(output.period_end) - date.fromisoformat(output.period_start)).days + 1
    if not 80 <= days <= 100:
        raise ValueError("irregular transition period is not a regular quarter")

