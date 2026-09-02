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
                        source_url=d.source_url
                        if r.get("accn") and c.cik and "companyfacts" in d.source_url.lower():
                            source_url=(
                                f"https://www.sec.gov/Archives/edgar/data/{int(c.cik)}/"
                                f"{r['accn'].replace('-', '')}/"
                            )
                        facts.append(ExtractedFact(
                            company_id=c.company_id, raw_label=tag, raw_value=value,
                            raw_currency=c.currency, raw_unit=unit, scale=Decimal(1),
                            period_start=r.get("start"), period_end=r["end"], period_kind=kind,
                            fiscal_year=int(r.get("fy") or r["end"][:4]), fiscal_quarter=quarter,
                            source_key=d.source_key, source_url=source_url,
                            filed_at=r.get("filed",d.filed_at), accession=r.get("accn"),
                            form=r.get("form"),
                            location={"taxonomy":taxonomy,"tag":tag,"frame":r.get("frame")},
                        ))
        return self._latest_accession(facts),errors

    def _sa(self,c,d,p):
        facts=[]; errors=[]
        for r in p.get("facts",[]):
            label=r.get("metric") or r.get("label","")
            try:
                dimensions=r.get("dimensions") or {}
                if not isinstance(dimensions,dict) or not all(
                    isinstance(key,str) and isinstance(value,str)
                    for key,value in dimensions.items()
                ):
                    raise ValueError("dimensions must be a string-to-string object")
                facts.append(ExtractedFact(
                    company_id=c.company_id, raw_label=label,
                    raw_value=Decimal(str(r["value"])),
                    raw_currency=r.get("currency",c.currency),
                    raw_unit=r.get("unit",c.currency), scale=Decimal(str(r.get("scale",1))),
                    period_start=r.get("period_start"), period_end=r["period_end"],
                    period_kind=PeriodKind(r["period_kind"]), fiscal_year=int(r["fiscal_year"]),
                    fiscal_quarter=r.get("fiscal_quarter"), source_key=d.source_key,
                    source_url=d.source_url, filed_at=d.filed_at, accession=r.get("accession"),
                    form=d.filing_type, page=r.get("page"),
                    table_ref=r.get("table") or r.get("table_ref"),
                    location={"row":r.get("row"),"cell":r.get("cell")},
                    scope=r.get("scope","consolidated"), dimensions=dimensions,
                ))
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
