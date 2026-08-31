import json
from pathlib import Path
from .models import Company, Market

class CompanyRegistry:
    def __init__(self, companies: list[Company]):
        self._companies = {c.company_id: c for c in companies}
        self._symbols = {(c.market.value, c.symbol.upper()): c for c in companies}
    @classmethod
    def from_json(cls, path: str | Path) -> "CompanyRegistry":
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([Company(company_id=r["company_id"], market=Market(r["market"]), symbol=r["symbol"], name=r["name"], currency=r["currency"], cik=r.get("cik"), isin=r.get("isin"), fiscal_year_end=r.get("fiscal_year_end", "12-31"), sources=tuple(r.get("sources", []))) for r in rows])
    def get(self, company_id: str) -> Company:
        return self._companies[company_id]
    def resolve(self, market: str, symbol: str) -> Company:
        return self._symbols[(market.upper(), symbol.upper())]
    def all(self) -> list[Company]:
        return list(self._companies.values())
