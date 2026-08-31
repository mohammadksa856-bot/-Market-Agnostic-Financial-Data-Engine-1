from __future__ import annotations
import hashlib, json
from urllib.request import Request, urlopen
from ..models import Company, Market, SourceDocument

class SaudiManifestConnector:
    """Fetches a configured JSON manifest. Keep issuer/Tadawul endpoints outside core."""
    name = "saudi-manifest"
    def __init__(self, manifest_url: str, opener=urlopen): self.manifest_url,self.opener=manifest_url,opener
    def fetch(self, company: Company) -> SourceDocument:
        if company.market != Market.SA: raise ValueError("Saudi connector requires SA company")
        req=Request(self.manifest_url,headers={"User-Agent":"finengine/0.3 (+data-contact-required)"})
        with self.opener(req,timeout=30) as r: content=r.read()
        p=json.loads(content); filed=p.get("filed_at") or p["period_end"]
        return SourceDocument(company.company_id,company.market,self.manifest_url,"sa:"+hashlib.sha256(content).hexdigest(),p.get("filing_type","financial-results"),filed,content)
