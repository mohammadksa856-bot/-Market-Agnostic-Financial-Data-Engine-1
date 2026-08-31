from __future__ import annotations
import json
from decimal import Decimal
from .mapping import canonicalize
from .models import Company, Fact, PeriodKind, SourceDocument

class JsonExtractor:
    def extract(self, company: Company, doc: SourceDocument) -> tuple[list[Fact],list[dict]]:
        data=json.loads(doc.content); return self._sec(company,doc,data) if company.market.value=="US" else self._sa(company,doc,data)
    def _sec(self,c,d,p):
        facts=[]; errors=[]
        for taxonomy, concepts in p.get("facts",{}).items():
            for tag, concept in concepts.items():
                metric=canonicalize(tag,"US")
                if not metric: continue
                for unit, rows in concept.get("units",{}).items():
                    for r in rows:
                        if r.get("form") not in {"10-K","10-Q","20-F","40-F"} or "end" not in r: continue
                        kind,quarter=self._period(r)
                        try: value=Decimal(str(r["val"]))
                        except Exception: errors.append({"code":"invalid_value","tag":tag,"row":r}); continue
                        facts.append(Fact(c.company_id,metric,value,c.currency,unit,r.get("start"),r["end"],kind,int(r.get("fy") or r["end"][:4]),quarter,d.source_key,d.source_url,r.get("filed",d.filed_at),r.get("accn"),r.get("form")))
        return self._latest_accession(facts),errors
    def _sa(self,c,d,p):
        facts=[]; errors=[]
        for r in p.get("facts",[]):
            metric=canonicalize(r.get("metric") or r.get("label",""),"SA")
            if not metric: errors.append({"code":"unmapped_metric","row":r}); continue
            try: kind=PeriodKind(r["period_kind"]); value=Decimal(str(r["value"])) * Decimal(str(r.get("scale",1)))
            except Exception as e: errors.append({"code":"invalid_fact","message":str(e),"row":r}); continue
            facts.append(Fact(c.company_id,metric,value,r.get("currency",c.currency),r.get("unit",c.currency),r.get("period_start"),r["period_end"],kind,int(r["fiscal_year"]),r.get("fiscal_quarter"),d.source_key,d.source_url,d.filed_at,r.get("accession"),d.filing_type))
        return facts,errors
    @staticmethod
    def _period(r):
        fp=r.get("fp"); start=r.get("start"); end=r["end"]
        if not start: return PeriodKind.INSTANT,None
        days=__import__("datetime").date.fromisoformat(end)-__import__("datetime").date.fromisoformat(start)
        if fp=="FY" or days.days>300: return PeriodKind.FY,None
        if fp in {"Q1","Q2","Q3","Q4"} and days.days<130: return PeriodKind.QUARTER,int(fp[1])
        return PeriodKind.YTD, int(fp[1]) if fp and fp.startswith("Q") else None
    @staticmethod
    def _latest_accession(facts):
        chosen={}
        for f in facts:
            old=chosen.get(f.natural_key)
            if old is None or (f.filed_at,f.accession or "")>(old.filed_at,old.accession or ""): chosen[f.natural_key]=f
        return list(chosen.values())
