from __future__ import annotations
import hashlib
from pathlib import Path
from .calculations import Calculator
from .database import Database
from .extraction import JsonExtractor
from .models import Company
from .validation import Validator

class Pipeline:
    def __init__(self, db: Database, raw_dir: str | Path):
        self.db=db; self.raw_dir=Path(raw_dir); self.extractor=JsonExtractor(); self.validator=Validator(); self.calculator=Calculator()
    def run(self, company: Company, connector) -> dict:
        self.db.register_company(company); doc=connector.fetch(company)
        if self.db.has_source(doc.source_key): return {"status":"duplicate","source_key":doc.source_key,"published":0}
        digest=hashlib.sha256(doc.content).hexdigest(); target=self.raw_dir/company.market.value/company.symbol/(doc.source_key.replace(":","_")+".json")
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(doc.content)
        self.db.save_source(doc,digest,str(target)); facts,errors=self.extractor.extract(company,doc)
        for e in errors: self.db.exception(company.company_id,doc.source_key,"extraction",e["code"],e.get("message",e["code"]),e)
        facts,validation=self.validator.validate(facts)
        for e in validation: self.db.exception(company.company_id,doc.source_key,"validation",e["code"],e["code"],e)
        fatal={"required_field","balance_sheet_unbalanced"}
        if any(e["code"] in fatal for e in validation): return {"status":"exception","source_key":doc.source_key,"published":0,"exceptions":len(errors)+len(validation)}
        calculated=self.calculator.calculate(facts); states=[self.db.publish(f) for f in facts+calculated]
        return {"status":"published","source_key":doc.source_key,"published":len(states),"inserted":states.count("inserted"),"restated":states.count("restated"),"duplicates":states.count("duplicate"),"exceptions":len(errors)+len(validation)}
