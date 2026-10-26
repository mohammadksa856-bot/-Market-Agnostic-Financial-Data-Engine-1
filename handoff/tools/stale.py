"""Calculated rows whose value differs from a full recompute on the current inputs (diagnostic, read-only)."""
import sys, collections
from finengine.database import Database, _dimensions
from finengine.calculations import Calculator
db = Database(sys.argv[1]); only = sys.argv[2:] 
calc = Calculator()
cos = [r[0] for r in db.conn.execute("select company_id from companies")]
tot = collections.Counter(); ex = []
for cid in cos:
    if only and cid not in only: continue
    ind = (db.conn.execute("SELECT industry FROM companies WHERE company_id=?", (cid,)).fetchone() or [None])[0]
    inputs = [f for f in db.calculation_history(cid, calc.HISTORY_METRICS) if not f.is_calculated]
    exp = {}
    for f in calc.calculate(inputs, [], industry=ind):
        exp[(f.metric, f.period_end, f.period_kind.value, f.fiscal_year, f.fiscal_quarter or 0, f.currency, f.unit, f.scope, _dimensions(f.dimensions)[1])] = f
    for r in db.conn.execute("select * from data_points where company_id=? and is_current=1 and is_calculated=1", (cid,)):
        k = (r["metric_key"], r["period_end"], r["period_kind"], r["fiscal_year"], r["fiscal_quarter"] or 0, r["currency"], r["unit"], r["scope"], r["dimensions_hash"])
        f = exp.get(k)
        if f is None: tot["not_recomputed"] += 1; continue
        if r["value_decimal"] != str(f.value):
            a, b = float(r["value_decimal"]), float(f.value)
            rel = abs(a-b)/max(abs(a),abs(b),1e-12)
            if rel > 1e-9:
                tot["differs"] += 1; ex.append((cid, r["metric_key"], r["period_kind"], r["period_end"], a, b, rel))
            else: tot["rounding"] += 1
        else: tot["same"] += 1
print(dict(tot))
for e in sorted(ex, key=lambda e: -e[6])[:40]: print(e)
