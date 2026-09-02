from __future__ import annotations
import hashlib, json
from datetime import date
from urllib.request import Request, urlopen
from ..models import Company, DiscoveryResult, Market, SourceCandidate, SourceDocument

class SecCompanyFactsConnector:
    name = "sec-companyfacts"
    def __init__(self, user_agent: str, opener=urlopen):
        if "@" not in user_agent: raise ValueError("SEC user_agent must identify an email address")
        self.user_agent, self.opener = user_agent, opener
    def fetch(self, company: Company) -> SourceDocument:
        if company.market != Market.US or not company.cik: raise ValueError("SEC connector requires US company with CIK")
        url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{company.cik}.json"
        req=Request(url,headers={"User-Agent":self.user_agent})
        with self.opener(req,timeout=30) as r: content=r.read()
        payload=json.loads(content); filed=max((x.get("filed","") for ns in payload["facts"].values() for c in ns.values() for units in c.get("units",{}).values() for x in units),default=date.today().isoformat())
        return SourceDocument(company.company_id,company.market,url,"sec:"+hashlib.sha256(content).hexdigest(), "companyfacts",filed,content)


class SecFilingsMonitor:
    """Discovers new SEC financial filings before the heavier Company Facts ingest."""

    name = "sec-submissions"
    FORMS = {"10-K", "10-Q", "20-F", "40-F"}

    def __init__(self, user_agent: str, opener=urlopen, initial_backfill: int = 8):
        if "@" not in user_agent:
            raise ValueError("SEC user_agent must identify an email address")
        self.user_agent = user_agent
        self.opener = opener
        self.initial_backfill = max(1, min(initial_backfill, 100))

    def discover(self, company: Company, cursor: str | None = None) -> DiscoveryResult:
        if company.market != Market.US or not company.cik:
            raise ValueError("SEC monitor requires US company with CIK")
        url = f"https://data.sec.gov/submissions/CIK{company.cik}.json"
        request = Request(url, headers={"User-Agent": self.user_agent})
        with self.opener(request, timeout=30) as response:
            payload = json.loads(response.read())
        recent = payload.get("filings", {}).get("recent", {})
        accessions = recent.get("accessionNumber", [])
        latest = next((accession for accession, form in zip(accessions, recent.get("form", []))
                       if form in self.FORMS), cursor or "")
        candidates = []
        for index, accession in enumerate(accessions):
            form = self._at(recent, "form", index)
            if form not in self.FORMS:
                continue
            if cursor and accession == cursor:
                break
            if not cursor and len(candidates) >= self.initial_backfill:
                break
            primary_document = self._at(recent, "primaryDocument", index)
            if not primary_document:
                continue
            accession_path = accession.replace("-", "")
            archive_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(company.cik)}/"
                f"{accession_path}/{primary_document}"
            )
            description = self._at(recent, "primaryDocDescription", index) or form
            filed_at = self._at(recent, "filingDate", index) or None
            candidates.append(SourceCandidate(
                company.company_id, self.name, accession, archive_url, description, form,
                filed_at, "text/html", {
                    "accession": accession,
                    "report_date": self._at(recent, "reportDate", index),
                    "primary_document": primary_document,
                    "submissions_url": url,
                },
            ))
        return DiscoveryResult(latest or cursor or "", tuple(candidates))

    @staticmethod
    def _at(columns: dict, name: str, index: int):
        values = columns.get(name, [])
        return values[index] if index < len(values) else None
