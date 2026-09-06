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
        return cls([Company(
            company_id=r["company_id"], market=Market(r["market"]), symbol=r["symbol"],
            name=r["name"], currency=r["currency"], cik=r.get("cik"), isin=r.get("isin"),
            fiscal_year_end=r.get("fiscal_year_end", "12-31"), sources=tuple(r.get("sources", [])),
            exchange=r.get("exchange"), country=r.get("country"), sector=r.get("sector"),
            industry=r.get("industry"), timezone=r.get("timezone", "UTC"),
            locale=r.get("locale", "en"), enabled=r.get("enabled", True)
        ) for r in rows])
    @classmethod
    def from_database(cls, conn) -> "CompanyRegistry":
        sources = {}
        for row in conn.execute(
            "SELECT company_id,url FROM company_sources WHERE enabled=1 ORDER BY priority,id"
        ).fetchall():
            sources.setdefault(row["company_id"], []).append(row["url"])
        rows = conn.execute("SELECT * FROM companies").fetchall()
        return cls([Company(
            company_id=r["company_id"], market=Market(r["market"]), symbol=r["symbol"],
            name=r["name"], currency=r["currency"], cik=r["cik"], isin=r["isin"],
            fiscal_year_end=r["fiscal_year_end"], sources=tuple(sources.get(r["company_id"], [])),
            exchange=r["exchange"], country=r["country"], sector=r["sector"],
            industry=r["industry"], timezone=r["timezone"], locale=r["locale"],
            enabled=bool(r["enabled"]),
        ) for r in rows])
    @classmethod
    def combined(cls, conn, path: str | Path = "config/companies.json") -> "CompanyRegistry":
        companies = {c.company_id: c for c in cls.from_database(conn).all()}
        registry_path = Path(path)
        if registry_path.is_file():
            companies.update({c.company_id: c for c in cls.from_json(registry_path).all()})
        return cls(list(companies.values()))
    def get(self, company_id: str) -> Company:
        return self._companies[company_id]
    def resolve(self, market: str, symbol: str) -> Company:
        return self._symbols[(market.upper(), symbol.upper())]
    def all(self) -> list[Company]:
        return list(self._companies.values())
