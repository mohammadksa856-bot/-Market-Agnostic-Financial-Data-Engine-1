from __future__ import annotations
import hashlib
from decimal import Decimal
from pathlib import Path
from .calculations import Calculator
from .canonicalization import CanonicalProjector, load_projection_facts, projection_period_key
from .database import Database
from .domains import CompanyDomainStore
from .extraction import JsonExtractor
from .mapping import MappingEngine
from .models import Company
from .normalization import NormalizationEngine
from .validation import Validator

class Pipeline:
    def __init__(self, db: Database, raw_dir: str | Path):
        self.db=db; self.raw_dir=Path(raw_dir); self.extractor=JsonExtractor(); self.mapper=MappingEngine({row["metric_key"] for row in db.conn.execute("SELECT metric_key FROM metric_definitions WHERE enabled=1")}); self.normalizer=NormalizationEngine(); self.validator=Validator(); self.calculator=Calculator(); self.domains=CompanyDomainStore(db)

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
        extension={"application/json":".json","application/pdf":".pdf","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":".xlsx","text/html":".html","application/xhtml+xml":".html","application/xml":".xml","text/xml":".xml"}.get(doc.content_type,".bin")
        # Pipeline manifests are immutable evidence. A corrected reader may
        # reprocess the same source_key into different bytes, so include the
        # content digest instead of overwriting the prior artifact path.
        target=self.raw_dir/company.market.value/company.symbol/(
            f"{doc.source_key.replace(':','_')}_{digest}{extension}"
        )
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(doc.content)
        if not previous_status: self.db.save_source(doc,digest,str(target))
        self.db.save_source_artifact(
            f"artifact:{company.company_id}:{digest}", company.company_id,
            doc.source_url, digest, str(target), doc.content_type, len(doc.content),
            {"source_key": doc.source_key, "pipeline_archive": True, "immutable": True},
        )
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
        history_for_validation=self.db.validation_history(company.company_id,self.validator.FLOW_METRICS)
        facts,validation=self.validator.validate(facts,history_for_validation)
        self.db.save_validation(doc.source_key,company.company_id,validation)
        for e in validation: self.db.exception(company.company_id,doc.source_key,"validation",e["code"],e["code"],e)
        quarantined_ids=[]
        # SEC Company Facts is a long-lived feed, not a single filing.  One
        # inconsistent historical period must not suppress thousands of valid
        # observations.  Keep the anomaly in staging/the exception queue and
        # publish only the facts outside the failing reconciliation group.
        if doc.source_key.startswith("sec:"):
            facts,normalized_ids,quarantined_ids=self._quarantine_reconciliation_anomalies(
                facts,normalized_ids,validation,
            )
            self.db.set_normalized_status(quarantined_ids,"rejected")
        fatal={"required_field","invalid_period","invalid_fiscal_quarter","missing_period_start"}
        if not doc.source_key.startswith("sec:"):
            fatal.update({"balance_sheet_unbalanced","period_rollforward_mismatch"})
        if any(e["code"] in fatal for e in validation):
            self.db.set_normalized_status(normalized_ids,"rejected"); self.db.set_source_status(doc.source_key,"review_required"); self.db.publication_batch(doc.source_key,company.company_id,"blocked",len(facts)+len(quarantined_ids),0)
            return {"status":"exception","source_key":doc.source_key,"published":0,"exceptions":len(validation),"stage":"validation"}
        if not facts:
            self.db.set_source_status(doc.source_key,"review_required"); self.db.publication_batch(doc.source_key,company.company_id,"blocked",len(quarantined_ids),0)
            return {"status":"exception","source_key":doc.source_key,"published":0,"exceptions":len(validation) or 1,"stage":"validation"}
        self.db.set_normalized_status(normalized_ids,"validated")
        source_conflicts = self.db.higher_trust_conflicts(facts)
        publishable_ids = list(normalized_ids)
        if source_conflicts:
            self.db.save_validation(doc.source_key, company.company_id, source_conflicts)
            for conflict in source_conflicts:
                self.db.exception(
                    company.company_id, doc.source_key, "validation", conflict["code"],
                    conflict["message"], conflict, severity="warning",
                )
            conflict_keys = {
                (
                    item["metric"], item["period_end"], item["period_kind"],
                    item["fiscal_year"], item["fiscal_quarter"], item["currency"],
                    item["unit"], item["scope"],
                    tuple(sorted(item["dimensions"].items())),
                )
                for item in source_conflicts
            }
            publishable = [
                (fact, normalized_id) for fact, normalized_id in zip(facts, normalized_ids)
                if (
                    fact.metric, fact.period_end, fact.period_kind.value,
                    fact.fiscal_year, fact.fiscal_quarter or 0, fact.currency,
                    fact.unit, fact.scope, tuple(sorted(fact.dimensions.items())),
                ) not in conflict_keys
            ]
            rejected_ids = [
                normalized_id for fact, normalized_id in zip(facts, normalized_ids)
                if (
                    fact.metric, fact.period_end, fact.period_kind.value,
                    fact.fiscal_year, fact.fiscal_quarter or 0, fact.currency,
                    fact.unit, fact.scope, tuple(sorted(fact.dimensions.items())),
                ) in conflict_keys
            ]
            facts = [item[0] for item in publishable]
            publishable_ids = [item[1] for item in publishable]
            # A lower-trust value is retained in the audit trail and exception
            # queue, but it must never be labelled as a production publication.
            self.db.set_normalized_status(rejected_ids, "rejected")
        history=self.db.calculation_history(company.company_id,self.calculator.HISTORY_METRICS)
        calculated=self.calculator.calculate(facts,history)
        # Canonical projections can depend on a detailed note in this batch and
        # a reported total ingested from another document. Read only the small
        # governed projection context, then publish exact aliases atomically
        # with the current source facts.
        projection_context=load_projection_facts(self.db,company.company_id)
        projection_periods={projection_period_key(fact) for fact in facts+calculated}
        projected=CanonicalProjector().project(
            [*projection_context,*facts,*calculated],projection_periods,
        )
        states=self.db.publish_batch(facts+calculated+projected)
        coverage=[]
        for period_end,period_kind in sorted({(f.period_end,f.period_kind.value) for f in facts}):
            try: coverage.append(self.domains.refresh_coverage(company.company_id,period_end,period_kind))
            except Exception as error: self.db.exception(company.company_id,doc.source_key,"coverage","coverage_refresh_failed",str(error),severity="warning")
        suppressed = states.count("suppressed") + len(source_conflicts)
        published_count = len(states) - states.count("suppressed")
        self.db.set_normalized_status(publishable_ids,"published"); self.db.set_source_status(doc.source_key,"published"); self.db.publication_batch(doc.source_key,company.company_id,"published",len(facts)+len(source_conflicts)+len(quarantined_ids),published_count)
        try:
            self.domains.refresh_company_backlog(company.company_id)
            from .understanding import refresh_company_understanding
            refresh_company_understanding(self.db.conn, company.company_id)
        except Exception as error:
            self.db.exception(company.company_id,doc.source_key,"understanding",
                              "understanding_refresh_failed",str(error),severity="warning")
        return {"status":"published","source_key":doc.source_key,"published":published_count,"inserted":states.count("inserted"),"restated":states.count("restated"),"duplicates":states.count("duplicate"),"suppressed":suppressed,"quarantined":len(quarantined_ids),"exceptions":len(validation)+len(source_conflicts),"coverage":coverage,"canonical_projections":len(projected),"staging":{"extracted":len(extracted),"mapped":len(mapped),"normalized":len(facts),"suppressed":len(source_conflicts),"quarantined":len(quarantined_ids),"minimum_confidence":"0.95"}}

    @staticmethod
    def _quarantine_reconciliation_anomalies(
        facts: list, normalized_ids: list[int], validation: list[dict],
    ) -> tuple[list,list[int],list[int]]:
        """Remove only SEC facts belonging to a failed reconciliation group."""
        balance_groups={
            (error.get("period"),error.get("scope","consolidated"),
             tuple(sorted(error.get("dimensions",{}).items())))
            for error in validation if error.get("code")=="balance_sheet_unbalanced"
        }
        rollforwards={
            (error.get("metric"),error.get("period_end"),error.get("period_kind"))
            for error in validation if error.get("code")=="period_rollforward_mismatch"
        }
        kept=[]; quarantined=[]
        for fact,normalized_id in zip(facts,normalized_ids):
            balance_key=(fact.period_end,fact.scope,tuple(sorted(fact.dimensions.items())))
            is_bad_balance=(
                fact.period_kind.value=="instant"
                and fact.metric in {"total_assets","total_liabilities","total_equity"}
                and balance_key in balance_groups
            )
            is_bad_rollforward=(
                fact.metric,fact.period_end,fact.period_kind.value
            ) in rollforwards
            (quarantined if is_bad_balance or is_bad_rollforward else kept).append(
                (fact,normalized_id)
            )
        return (
            [item[0] for item in kept],
            [item[1] for item in kept],
            [item[1] for item in quarantined],
        )

    def backfill_staging(self, company: Company, doc) -> dict:
        """Build the audit trail for legacy documents without republishing observations."""
        if self.db.has_staging(doc.source_key): return {"status":"skipped","source_key":doc.source_key}
        extracted,extraction_errors=self.extractor.extract_raw(company,doc)
        extracted_ids=self.db.save_extracted(extracted)
        mapped,mapping_errors=self.mapper.map(extracted,company.market.value)
        mapped_ids=self.db.save_mapped(mapped,extracted_ids)
        facts,normalization_errors,accepted_indexes=self.normalizer.normalize(mapped,Decimal("0.95"))
        normalized_ids=self.db.save_normalized(facts,mapped_ids,accepted_indexes)
        history_for_validation=self.db.validation_history(company.company_id,self.validator.FLOW_METRICS)
        facts,validation=self.validator.validate(facts,history_for_validation)
        self.db.save_validation(doc.source_key,company.company_id,validation)
        errors=extraction_errors+mapping_errors+normalization_errors+validation
        fatal_codes={"required_field","invalid_period","invalid_fiscal_quarter","missing_period_start",
                     "balance_sheet_unbalanced","period_rollforward_mismatch"}
        fatal=bool(extraction_errors or normalization_errors or any(e["code"] in fatal_codes for e in validation))
        self.db.set_normalized_status(normalized_ids,"rejected" if fatal else "published")
        if fatal:
            for e in errors: self.db.exception(company.company_id,doc.source_key,"backfill",e["code"],e.get("message",e["code"]),e)
        else: self.db.set_source_status(doc.source_key,"published")
        self.db.publication_batch(doc.source_key,company.company_id,"blocked" if fatal else "backfilled",len(facts),0)
        return {"status":"review_required" if fatal else "backfilled","source_key":doc.source_key,"extracted":len(extracted),"mapped":len(mapped),"normalized":len(facts),"exceptions":len(errors)}
