"""Comparison and trailing-twelve-month rows recomputed from the inputs current once a sync has finished.

Manifests are applied one at a time, so a growth rate, CAGR or quarter-on-quarter change is computed from the
inputs current at that moment. When a later filing restates or re-presents one of its inputs, the row computed
earlier would otherwise stay current with a value no current input supports. After a sync every comparison of the
company is recomputed from its current inputs: an unchanged row is kept, a changed one is superseded and one the
calculation rules now withhold is retired.
"""
from __future__ import annotations

from .calculations import Calculator
from .database import Database, _dimensions


def comparison_metrics() -> set[str]:
    calculator = Calculator()
    return {*calculator.GROWTH_METRICS.values(), *calculator.QOQ_METRICS.values(), *calculator.TTM_GROWTH.values(),
            *calculator.TURNOVER_METRICS,
            *(calculator.TTM_NAMED.get(metric, f"{metric}_ttm") for metric in {*calculator.TTM_FLOWS, *calculator.TTM_NAMED}),
            *(f"{stem}_cagr_{years}y" for stem, horizons in calculator.CAGR_METRICS.values() for years in horizons)}


def _identity(metric, period_end, period_kind, fiscal_year, fiscal_quarter, currency, unit, scope, dimensions_hash):
    return (metric, period_end, period_kind, fiscal_year, fiscal_quarter or 0, currency, unit, scope, dimensions_hash)


def reconcile_comparisons(db: Database, company_id: str) -> dict:
    calculator = Calculator()
    outputs = comparison_metrics()
    industry = (db.conn.execute("SELECT industry FROM companies WHERE company_id=?", (company_id,)).fetchone()
                or [None])[0]
    inputs = [fact for fact in db.calculation_history(company_id, calculator.HISTORY_METRICS)
              if fact.metric not in outputs]
    expected = {}
    for fact in calculator.calculate(inputs, [], industry=industry):
        if fact.metric in outputs:
            expected[_identity(fact.metric, fact.period_end, fact.period_kind.value, fact.fiscal_year,
                               fact.fiscal_quarter, fact.currency, fact.unit, fact.scope,
                               _dimensions(fact.dimensions)[1])] = fact
    placeholders = ",".join("?" for _ in outputs)
    rows = db.conn.execute(
        f"""SELECT * FROM data_points WHERE company_id=? AND is_current=1 AND is_calculated=1
        AND metric_key IN ({placeholders})""", (company_id, *sorted(outputs))).fetchall()
    retired = superseded = 0
    for row in rows:
        key = _identity(row["metric_key"], row["period_end"], row["period_kind"], row["fiscal_year"],
                        row["fiscal_quarter"], row["currency"], row["unit"], row["scope"], row["dimensions_hash"])
        fact = expected.pop(key, None)
        if fact is not None and row["value_decimal"] == str(fact.value):
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
    db.conn.commit()
    return {"retired": retired, "superseded": superseded, "added": added}
