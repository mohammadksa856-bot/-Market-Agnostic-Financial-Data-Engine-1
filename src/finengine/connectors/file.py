from __future__ import annotations
import hashlib, json
from pathlib import Path
from ..models import Company, SourceDocument

class LocalFileConnector:
    name = "local-file"
    def __init__(self, path: str | Path, source_url: str | None = None):
        self.path=Path(path); self.source_url=source_url
    def fetch(self, company: Company) -> SourceDocument:
        content=self.path.read_bytes(); payload=json.loads(content)
        filed=payload.get("filed_at") or payload.get("filed") or payload.get("period_end")
        if not filed:
            filed=max((x.get("filed","") for ns in payload.get("facts",{}).values() for c in ns.values() for rows in c.get("units",{}).values() for x in rows),default="")
        if not filed: raise ValueError("local filing must contain a filed date")
        url=self.source_url or payload.get("source_url") or self.path.resolve().as_uri()
        return SourceDocument(company.company_id,company.market,url,"file:"+hashlib.sha256(content).hexdigest(),payload.get("filing_type","companyfacts"),filed,content)
