"""Every four-contiguous-quarter window that is exactly a fiscal year, against its reported FY value (read-only)."""
import sqlite3, sys, json
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, sys.argv[3])  # engine src: use the engine's own rounding bound
from finengine.calculations import Calculator

db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
metrics = sys.argv[2].split(",")
rows = []
for company, metric, start, end, value in db.execute(
        f"""SELECT company_id,metric_key,period_start,period_end,value_decimal FROM data_points WHERE is_current=1
        AND period_kind='quarter' AND scope='consolidated' AND dimensions_json IN ('{{}}','')
        AND metric_key IN ({','.join('?'*len(metrics))}) ORDER BY 1,2,4""", metrics):
    rows.append((company, metric, start, end, value))
by = {}
for company, metric, start, end, value in rows:
    by.setdefault((company, metric), []).append((start, end, value))
out = []
for (company, metric), quarters in by.items():
    for i in range(3, len(quarters)):
        window = quarters[i-3:i+1]
        if any(date.fromisoformat(b[0]) - timedelta(days=1) != date.fromisoformat(a[1]) for a, b in zip(window, window[1:])):
            continue
        fy = db.execute("""SELECT value_decimal FROM data_points WHERE company_id=? AND metric_key=? AND is_current=1
            AND period_kind='fy' AND period_start=? AND period_end=? AND scope='consolidated' AND dimensions_json IN ('{}','')""",
            (company, metric, window[0][0], window[-1][1])).fetchone()
        if not fy:
            continue
        total = sum(Decimal(q[2]) for q in window)
        bound = Calculator._rounding_bound([Decimal(q[2]) for q in window] + [Decimal(fy[0])])
        diff = abs(total - Decimal(fy[0]))
        rel = diff / abs(Decimal(fy[0])) if Decimal(fy[0]) else None
        out.append({"company": company, "metric": metric, "fy_end": window[-1][1], "diff": str(diff), "rounding_bound": str(bound),
                    "relative": None if rel is None else f"{float(rel):.5%}", "within_rounding": diff <= bound,
                    "within_0.5pct": rel is not None and rel <= Decimal("0.005")})
print(json.dumps(out, indent=1))
