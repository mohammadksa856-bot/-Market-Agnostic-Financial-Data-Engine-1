from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from .mapping import MappingEngine, canonicalize
from .models import Company, ExtractedFact, PeriodKind, SourceDocument
from .normalization import NormalizationEngine


class JsonExtractor:
    """Extracts source-faithful facts; mapping and normalization are separate stages."""
    def extract_raw(self, company: Company, doc: SourceDocument) -> tuple[list[ExtractedFact],list[dict]]:
        data=json.loads(doc.content)
        return self._sec(company,doc,data) if company.market.value=="US" else self._sa(company,doc,data)

    def extract(self, company: Company, doc: SourceDocument):
        """Backward-compatible convenience facade used by connector unit tests."""
        raw,errors=self.extract_raw(company,doc)
        mapped,mapping_errors=MappingEngine().map(raw,company.market.value)
        facts,normalization_errors,_=NormalizationEngine().normalize(mapped)
        return facts,errors+mapping_errors+normalization_errors

    def _sec(self,c,d,p):
        facts=[]; errors=[]
        for taxonomy, concepts in p.get("facts",{}).items():
            for tag, concept in concepts.items():
                if not canonicalize(tag,"US"): continue
                for unit, rows in concept.get("units",{}).items():
                    for r in rows:
                        if r.get("form") not in {"10-K","10-Q","20-F","40-F"} or "end" not in r: continue
                        kind,quarter=self._period(r)
                        try: value=Decimal(str(r["val"]))
                        except Exception: errors.append({"code":"invalid_value","tag":tag,"row":r}); continue
                        facts.append(ExtractedFact(c.company_id,tag,value,c.currency,unit,Decimal(1),r.get("start"),r["end"],kind,int(r.get("fy") or r["end"][:4]),quarter,d.source_key,d.source_url,r.get("filed",d.filed_at),r.get("accn"),r.get("form"),location={"taxonomy":taxonomy,"tag":tag}))
        return self._latest_accession(facts),errors

    def _sa(self,c,d,p):
        facts=[]; errors=[]
        for r in p.get("facts",[]):
            label=r.get("metric") or r.get("label","")
            try:
                facts.append(ExtractedFact(c.company_id,label,Decimal(str(r["value"])),r.get("currency",c.currency),r.get("unit",c.currency),Decimal(str(r.get("scale",1))),r.get("period_start"),r["period_end"],PeriodKind(r["period_kind"]),int(r["fiscal_year"]),r.get("fiscal_quarter"),d.source_key,d.source_url,d.filed_at,r.get("accession"),d.filing_type,r.get("page"),r.get("table") or r.get("table_ref"),{"row":r.get("row"),"cell":r.get("cell")}))
            except Exception as e:
                errors.append({"code":"invalid_fact","message":str(e),"row":r})
        return facts,errors

    @staticmethod
    def _period(r):
        fp=r.get("fp"); start=r.get("start"); end=r["end"]
        if not start: return PeriodKind.INSTANT,None
        days=(date.fromisoformat(end)-date.fromisoformat(start)).days
        if fp=="FY" or days>300: return PeriodKind.FY,None
        if fp in {"Q1","Q2","Q3","Q4"} and days<130: return PeriodKind.QUARTER,int(fp[1])
        return PeriodKind.YTD, int(fp[1]) if fp and fp.startswith("Q") else None

    @staticmethod
    def _latest_accession(facts):
        chosen={}
        for f in facts:
            key=(f.company_id,f.raw_label,f.period_end,f.period_kind.value,f.fiscal_year,f.fiscal_quarter,f.raw_currency,f.raw_unit)
            old=chosen.get(key)
            if old is None or (f.filed_at,f.accession or "")>(old.filed_at,old.accession or ""): chosen[key]=f
        return list(chosen.values())
