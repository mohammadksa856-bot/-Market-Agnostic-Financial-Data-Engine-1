from __future__ import annotations
import hashlib
from decimal import Decimal
from pathlib import Path
from .calculations import Calculator
from .database import Database
from .domains import CompanyDomainStore
from .extraction import JsonExtractor
from .mapping import MappingEngine
from .models import Company
from .normalization import NormalizationEngine
from .validation import Validator

class Pipeline:
    def __init__(self, db: Database, raw_dir: str | Path):
        self.db=db; self.raw_dir=Path(raw_dir); self.extractor=JsonExtractor(); self.mapper=MappingEngine(); self.normalizer=NormalizationEngine(); self.validator=Validator(); self.calculator=Calculator(); self.domains=CompanyDomainStore(db)

    def run(self, company: Company, connector, job_id: str | None = None) -> dict:
        self.db.register_company(company); run_id=self.db.start_pipeline_run(company.company_id,job_id)
        try:
            result=self._run(company,connector)
        except Exception as error:
            self.db.finish_pipeline_run(run_id,"failed","unexpected",None,{"error":str(error)})
            raise
        result["run_id"]=run_id
        self.db.finish_pipeline_run(run_id,result["status"],result.get("stage","complete"),result.get("source_key"),result)
        return result

    def _run(self, company: Company, connector) -> dict:
        self.db.register_company(company); doc=connector.fetch(company)
        previous_status=self.db.source_status(doc.source_key)
        if previous_status=="published": return {"status":"duplicate","source_key":doc.source_key,"published":0}
        if previous_status=="review_required": return {"status":"exception","stage":"review","source_key":doc.source_key,"published":0,"exceptions":0}
        if previous_status: self.db.reset_unfinished_source(doc.source_key)
        digest=hashlib.sha256(doc.content).hexdigest()
        extension={"application/json":".json","application/pdf":".pdf","text/html":".html","application/xhtml+xml":".html","application/xml":".xml","text/xml":".xml"}.get(doc.content_type,".bin")
        target=self.raw_dir/company.market.value/company.symbol/(doc.source_key.replace(":","_")+extension)
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(doc.content)
        if not previous_status: self.db.save_source(doc,digest,str(target))
        self.db.set_source_status(doc.source_key,"extracting")
        extracted,errors=self.extractor.extract_raw(company,doc)
        extracted_ids=self.db.save_extracted(extracted)
        for e in errors: self.db.exception(company.company_id,doc.source_key,"extraction",e["code"],e.get("message",e["code"]),e)
        if errors or not extracted:
            self.db.set_source_status(doc.source_key,"review_required"); self.db.publication_batch(doc.source_key,company.company_id,"blocked",len(extracted),0)
            return {"status":"exception","source_key":doc.source_key,"published":0,"exceptions":len(errors) or 1,"stage":"extraction"}
        mapped,mapping_errors=self.mapper.map(extracted,company.market.value)
        mapped_ids=self.db.save_mapped(mapped,extracted_ids)
        facts,normalization_errors,accepted_indexes=self.normalizer.normalize(mapped,Decimal("0.95"))
        normalized_ids=self.db.save_normalized(facts,mapped_ids,accepted_indexes)
        gate_errors=normalization_errors
        for e in gate_errors: self.db.exception(company.company_id,doc.source_key,"mapping",e["code"],e["code"],e)
        if gate_errors:
            self.db.set_normalized_status(normalized_ids,"rejected"); self.db.set_source_status(doc.source_key,"review_required"); self.db.publication_batch(doc.source_key,company.company_id,"blocked",len(facts),0)
            return {"status":"exception","source_key":doc.source_key,"published":0,"exceptions":len(gate_errors),"stage":"mapping","minimum_confidence":"0.95"}
        facts,validation=self.validator.validate(facts)
        self.db.save_validation(doc.source_key,company.company_id,validation)
        for e in validation: self.db.exception(company.company_id,doc.source_key,"validation",e["code"],e["code"],e)
        fatal={"required_field","balance_sheet_unbalanced"}
        if any(e["code"] in fatal for e in validation):
            self.db.set_normalized_status(normalized_ids,"rejected"); self.db.set_source_status(doc.source_key,"review_required"); self.db.publication_batch(doc.source_key,company.company_id,"blocked",len(facts),0)
            return {"status":"exception","source_key":doc.source_key,"published":0,"exceptions":len(validation),"stage":"validation"}
        self.db.set_normalized_status(normalized_ids,"validated")
        history=self.db.quarter_history(company.company_id,self.calculator.TTM_FLOWS)
        calculated=self.calculator.calculate(facts,history); states=self.db.publish_batch(facts+calculated)
        coverage=[]
        for period_end,period_kind in sorted({(f.period_end,f.period_kind.value) for f in facts}):
            try: coverage.append(self.domains.refresh_coverage(company.company_id,period_end,period_kind))
            except Exception as error: self.db.exception(company.company_id,doc.source_key,"coverage","coverage_refresh_failed",str(error),severity="warning")
        self.db.set_normalized_status(normalized_ids,"published"); self.db.set_source_status(doc.source_key,"published"); self.db.publication_batch(doc.source_key,company.company_id,"published",len(facts),len(states))
        return {"status":"published","source_key":doc.source_key,"published":len(states),"inserted":states.count("inserted"),"restated":states.count("restated"),"duplicates":states.count("duplicate"),"exceptions":len(validation),"coverage":coverage,"staging":{"extracted":len(extracted),"mapped":len(mapped),"normalized":len(facts),"minimum_confidence":"0.95"}}

    def backfill_staging(self, company: Company, doc) -> dict:
        """Build the audit trail for legacy documents without republishing observations."""
        if self.db.has_staging(doc.source_key): return {"status":"skipped","source_key":doc.source_key}
        extracted,extraction_errors=self.extractor.extract_raw(company,doc)
        extracted_ids=self.db.save_extracted(extracted)
        mapped,mapping_errors=self.mapper.map(extracted,company.market.value)
        mapped_ids=self.db.save_mapped(mapped,extracted_ids)
        facts,normalization_errors,accepted_indexes=self.normalizer.normalize(mapped,Decimal("0.95"))
        normalized_ids=self.db.save_normalized(facts,mapped_ids,accepted_indexes)
        facts,validation=self.validator.validate(facts)
        self.db.save_validation(doc.source_key,company.company_id,validation)
        errors=extraction_errors+mapping_errors+normalization_errors+validation
        fatal=bool(extraction_errors or normalization_errors or any(e["code"] in {"required_field","balance_sheet_unbalanced"} for e in validation))
        self.db.set_normalized_status(normalized_ids,"rejected" if fatal else "published")
        if fatal:
            for e in errors: self.db.exception(company.company_id,doc.source_key,"backfill",e["code"],e.get("message",e["code"]),e)
        else: self.db.set_source_status(doc.source_key,"published")
        self.db.publication_batch(doc.source_key,company.company_id,"blocked" if fatal else "backfilled",len(facts),0)
        return {"status":"review_required" if fatal else "backfilled","source_key":doc.source_key,"extracted":len(extracted),"mapped":len(mapped),"normalized":len(facts),"exceptions":len(errors)}
