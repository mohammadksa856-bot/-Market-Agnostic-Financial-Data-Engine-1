from __future__ import annotations
import hashlib, json
from datetime import date
from urllib.request import Request, urlopen
from ..models import Company, Market, SourceDocument

class SecCompanyFactsConnector:
    name = "sec-companyfacts"
    def __init__(self, user_agent: str, opener=urlopen):
        if "@" not in user_agent: raise ValueError("SEC user_agent must identify an email address")
        self.user_agent, self.opener = user_agent, opener
    def fetch(self, company: Company) -> SourceDocument:
        if company.market != Market.US or not company.cik: raise ValueError("SEC connector requires US company with CIK")
        url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{company.cik}.json"
        req=Request(url,headers={"User-Agent":self.user_agent,"Accept-Encoding":"gzip, deflate"})
        with self.opener(req,timeout=30) as r: content=r.read()
        payload=json.loads(content); filed=max((x.get("filed","") for ns in payload["facts"].values() for c in ns.values() for units in c.get("units",{}).values() for x in units),default=date.today().isoformat())
        return SourceDocument(company.company_id,company.market,url,"sec:"+hashlib.sha256(content).hexdigest(), "companyfacts",filed,content)
