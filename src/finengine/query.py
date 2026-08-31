from __future__ import annotations
import sqlite3

class FinancialQueryService:
    """Read-only facade suitable for an API or Telegram bot."""
    def __init__(self, db_path: str):
        self.conn=sqlite3.connect(f"file:{db_path}?mode=ro",uri=True); self.conn.row_factory=sqlite3.Row
    def close(self): self.conn.close()
    def metric_history(self, market: str, symbol: str, metric: str, limit: int=20) -> list[dict]:
        rows=self.conn.execute("""SELECT o.metric,o.value,o.currency,o.unit,o.period_start,o.period_end,o.period_kind,o.fiscal_year,o.fiscal_quarter,o.version,o.source_url,o.is_calculated FROM observations o JOIN companies c USING(company_id) WHERE c.market=? AND c.symbol=? AND o.metric=? AND o.is_current=1 ORDER BY o.period_end DESC LIMIT ?""",(market.upper(),symbol.upper(),metric,min(max(limit,1),100))).fetchall(); return [dict(r) for r in rows]
    def snapshot(self, market: str, symbol: str, period_end: str | None=None) -> dict:
        if period_end is None:
            row=self.conn.execute("SELECT MAX(o.period_end) p FROM observations o JOIN companies c USING(company_id) WHERE c.market=? AND c.symbol=?",(market.upper(),symbol.upper())).fetchone(); period_end=row["p"]
        rows=self.conn.execute("""SELECT o.metric,o.value,o.currency,o.unit,o.period_kind,o.version,o.source_url FROM observations o JOIN companies c USING(company_id) WHERE c.market=? AND c.symbol=? AND o.period_end=? AND o.is_current=1""",(market.upper(),symbol.upper(),period_end)).fetchall()
        return {"market":market.upper(),"symbol":symbol.upper(),"period_end":period_end,"metrics":{r["metric"]:dict(r) for r in rows}}
