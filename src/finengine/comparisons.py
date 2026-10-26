"""Comparison and trailing-twelve-month rows recomputed from the inputs current once a sync has finished.

Manifests are applied one at a time, so a growth rate, CAGR or quarter-on-quarter change is computed from the
inputs current at that moment. When a later filing restates or re-presents one of its inputs, the row computed
earlier would otherwise stay current with a value no current input supports. After a sync every comparison of the
company is recomputed from its current inputs: an unchanged row is kept, a changed one is superseded and one the
calculation rules now withhold is retired.
"""
from __future__ import annotations

import re

from .calculations import Calculator
from .database import Database, _dimensions


def comparison_metrics() -> set[str]:
    calculator = Calculator()
    return {*calculator.GROWTH_METRICS.values(), *calculator.QOQ_METRICS.values(), *calculator.TTM_GROWTH.values(),
            *calculator.TURNOVER_METRICS,
            *(calculator.TTM_NAMED.get(metric, f"{metric}_ttm") for metric in {*calculator.TTM_FLOWS, *calculator.TTM_NAMED}),
            *(f"{stem}_cagr_{years}y" for stem, horizons in calculator.CAGR_METRICS.values() for years in horizons)}


def derived_quarter_metrics() -> set[str]:
    """Quarter rows computed from cumulative cash-flow figures: recomputed like comparisons."""
    return set(Calculator.CUMULATIVE_QUARTER_FLOWS)


# Calculated free cash flow is an input of trailing sums and their checks against reported years, and its two inputs
# often come from different filings, so a later restatement of either reaches it only here.
RECOMPUTED_FLOWS = {"free_cash_flow"}


def _derived_quarter(metric, period_kind, is_calculated) -> bool:
    return bool(is_calculated) and (metric in RECOMPUTED_FLOWS
                                    or period_kind == "quarter" and metric in derived_quarter_metrics())


def _identity(metric, period_end, period_kind, fiscal_year, fiscal_quarter, currency, unit, scope, dimensions_hash):
    return (metric, period_end, period_kind, fiscal_year, fiscal_quarter or 0, currency, unit, scope, dimensions_hash)


def reconcile_comparisons(db: Database, company_id: str) -> dict:
    calculator = Calculator()
    outputs = comparison_metrics()
    industry = (db.conn.execute("SELECT industry FROM companies WHERE company_id=?", (company_id,)).fetchone()
                or [None])[0]
    def identity_of(fact):
        return _identity(fact.metric, fact.period_end, fact.period_kind.value, fact.fiscal_year, fact.fiscal_quarter,
                         fact.currency, fact.unit, fact.scope, _dimensions(fact.dimensions)[1])

    inputs = [fact for fact in db.calculation_history(company_id, calculator.HISTORY_METRICS)
              if fact.metric not in outputs
              and not _derived_quarter(fact.metric, fact.period_kind.value, fact.is_calculated)]
    # First the recomputed flows (derived quarters, calculated free cash flow), which comparisons then use as inputs.
    flows = {identity_of(fact): fact for fact in calculator.calculate(inputs, [], industry=industry)
             if _derived_quarter(fact.metric, fact.period_kind.value, fact.is_calculated)}
    inputs = [*inputs, *(fact for fact in flows.values() if fact.metric in RECOMPUTED_FLOWS)]
    expected = dict(flows)
    recomputed = {}
    for fact in calculator.calculate(inputs, [], industry=industry):
        if _derived_quarter(fact.metric, fact.period_kind.value, fact.is_calculated):
            continue
        if fact.metric in outputs:
            expected[identity_of(fact)] = fact
        else:
            recomputed[identity_of(fact)] = fact
    placeholders = ",".join("?" for _ in outputs)
    derived = derived_quarter_metrics()
    rows = db.conn.execute(
        f"""SELECT * FROM data_points WHERE company_id=? AND is_current=1 AND is_calculated=1
        AND (metric_key IN ({placeholders}) OR metric_key IN ({",".join("?" for _ in RECOMPUTED_FLOWS)})
             OR (period_kind='quarter' AND metric_key IN ({",".join("?" for _ in derived)})))""",
        (company_id, *sorted(outputs), *sorted(RECOMPUTED_FLOWS), *sorted(derived))).fetchall()
    retired = superseded = 0
    for row in rows:
        key = _identity(row["metric_key"], row["period_end"], row["period_kind"], row["fiscal_year"],
                        row["fiscal_quarter"], row["currency"], row["unit"], row["scope"], row["dimensions_hash"])
        fact = expected.pop(key, None)
        if fact is not None and row["value_decimal"] == str(fact.value):
            continue
        # a recomputed flow is corrected when its inputs change, but never withdrawn for want of a recomputation
        if fact is None and row["metric_key"] not in outputs:
            continue
        db.conn.execute("UPDATE data_points SET is_current=0 WHERE id=?", (row["id"],))
        if row["scope"] == "consolidated" and row["dimensions_json"] in ("{}", ""):
            db.conn.execute(
                """UPDATE observations SET is_current=0 WHERE company_id=? AND metric=? AND period_end=?
                AND period_kind=? AND fiscal_year=? AND is_current=1""",
                (company_id, row["metric_key"], row["period_end"], row["period_kind"], row["fiscal_year"]))
        if fact is None:
            retired += 1
        else:
            db._publish_data_point(fact)
            superseded += 1
    # Comparisons that only the final inputs make possible are published as well.
    added = sum(db._publish_data_point(fact) == "inserted" for fact in expected.values())
    refreshed = _refresh_calculated(db, company_id, recomputed, inputs, {*outputs, *derived, *RECOMPUTED_FLOWS})
    db.conn.commit()
    return {"retired": retired, "superseded": superseded, "added": added, "refreshed": refreshed}


def _refresh_calculated(db: Database, company_id: str, recomputed: dict, inputs: list, handled: set[str]) -> int:
    """Correct other calculated rows whose formula gives another value on the current inputs.

    A row computed while a manifest was applied keeps the inputs current at that moment; when one input is later
    restated (or a cash-flow line completed), the row would stay current with a value no current input supports. Such
    a row is superseded by its recomputation. A row is never added or withdrawn here, and a formula that combines two
    or more re-presented lines from different filings is left as computed: the current lines may then sit on
    different presentation bases, while the row was computed within one filing."""
    sources = {}
    for fact in inputs:
        sources.setdefault((fact.metric, fact.period_end), set()).add(fact.source_url)
    rows = db.conn.execute(
        "SELECT * FROM data_points WHERE company_id=? AND is_current=1 AND is_calculated=1", (company_id,)).fetchall()
    refreshed = 0
    for row in rows:
        if row["metric_key"] in handled:
            continue
        key = _identity(row["metric_key"], row["period_end"], row["period_kind"], row["fiscal_year"],
                        row["fiscal_quarter"], row["currency"], row["unit"], row["scope"], row["dimensions_hash"])
        fact = recomputed.get(key)
        if fact is None or row["value_decimal"] == str(fact.value):
            continue
        lines = {token for token in re.findall(r"[a-z_]+", fact.calculation or "")
                 if token in Calculator.RE_PRESENTED_LINES}
        filings = set().union(*(sources.get((line, fact.period_end), set()) for line in lines)) if lines else set()
        if len(lines) >= 2 and len(filings) >= 2:
            continue
        db.conn.execute("UPDATE data_points SET is_current=0 WHERE id=?", (row["id"],))
        if row["scope"] == "consolidated" and row["dimensions_json"] in ("{}", ""):
            db.conn.execute(
                """UPDATE observations SET is_current=0 WHERE company_id=? AND metric=? AND period_end=?
                AND period_kind=? AND fiscal_year=? AND is_current=1""",
                (company_id, row["metric_key"], row["period_end"], row["period_kind"], row["fiscal_year"]))
        db._publish_data_point(fact)
        refreshed += 1
    return refreshed
