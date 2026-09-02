import argparse, json, os, socket, time
from pathlib import Path
from .connectors import (
    IssuerReportsMonitor, LocalFileConnector, SecCompanyFactsConnector,
    SecFilingsMonitor, SaudiManifestConnector,
)
from .database import Database
from .pipeline import Pipeline
from .query import FinancialQueryService
from .registry import CompanyRegistry
from .report import export_readable_report
from .models import SourceDocument
from .jobs import DurableJobQueue, DurableScheduler, Worker
from .domains import CompanyDomainStore
from .monitoring import DocumentArchiver, MonitorService


def _sec_user_agent() -> str:
    value = os.environ.get("SEC_USER_AGENT", "").strip()
    if "@" not in value:
        raise ValueError(
            "live SEC access requires SEC_USER_AGENT='Product operator@example.com'"
        )
    return value


def _ingest_job_handler(db: Database):
    def handle(job):
        payload=job.payload; reg=CompanyRegistry.from_json(payload.get("registry","config/companies.json"))
        company=reg.resolve(payload["market"],payload["symbol"])
        if company.market.value=="US":
            connector=SecCompanyFactsConnector(_sec_user_agent())
        else:
            manifest=payload.get("sa_manifest")
            if not manifest: raise ValueError("Saudi scheduled ingestion requires sa_manifest")
            connector=SaudiManifestConnector(manifest)
        candidate_ids = [int(value) for value in payload.get("candidate_ids", [])]
        try:
            result = Pipeline(db,payload.get("raw_dir","data/raw")).run(company,connector,job.job_id)
        except Exception:
            for candidate_id in candidate_ids:
                db.set_source_candidate_status(candidate_id, "error")
            raise
        for candidate_id in candidate_ids:
            db.set_source_candidate_status(candidate_id, "fetched")
        return result
    return handle


def _monitor_once(db: Database, queue: DurableJobQueue, payload: dict) -> dict:
    registry_path = payload.get("registry", "config/companies.json")
    registry = CompanyRegistry.from_json(registry_path)
    company = registry.resolve(payload["market"], payload["symbol"])
    common_payload = {
        "market": payload["market"], "symbol": payload["symbol"],
        "registry": registry_path, "raw_dir": payload.get("raw_dir", "data/raw"),
        "sa_manifest": payload.get("sa_manifest"),
    }
    service = MonitorService(db, queue)
    if company.market.value == "US":
        monitor = SecFilingsMonitor(_sec_user_agent())
        return service.poll(company, monitor, "ingest", common_payload)
    source_index = payload.get("source_index") or (company.sources[0] if company.sources else None)
    if not source_index:
        raise ValueError("issuer monitoring requires source_index or a registry source URL")
    monitor = IssuerReportsMonitor(source_index, max_documents=int(payload.get("source_limit", 12)))
    return service.poll(
        company, monitor, "fetch_document", {"raw_dir": common_payload["raw_dir"]}, True,
    )


def _monitor_job_handler(db: Database, queue: DurableJobQueue):
    def handle(job):
        return _monitor_once(db, queue, job.payload)
    return handle


def _fetch_document_job_handler(db: Database):
    def handle(job):
        candidate_id = int(job.payload["candidate_id"])
        try:
            return DocumentArchiver(db, job.payload.get("raw_dir", "data/raw")).fetch(candidate_id)
        except Exception:
            db.set_source_candidate_status(candidate_id, "error")
            raise
    return handle

def main():
    p=argparse.ArgumentParser(prog="finengine"); p.add_argument("--db",default="data/financial.sqlite3"); sub=p.add_subparsers(dest="cmd",required=True)
    init=sub.add_parser("init"); init.add_argument("--registry",default="config/companies.json")
    ingest=sub.add_parser("ingest"); ingest.add_argument("market",choices=["SA","US"]); ingest.add_argument("symbol"); ingest.add_argument("--registry",default="config/companies.json"); ingest.add_argument("--sa-manifest"); ingest.add_argument("--file"); ingest.add_argument("--source-url"); ingest.add_argument("--raw-dir",default="data/raw")
    query=sub.add_parser("query"); query.add_argument("market"); query.add_argument("symbol"); query.add_argument("metric"); query.add_argument("--limit",type=int,default=20)
    report=sub.add_parser("report"); report.add_argument("--html",default="data/financial-report.html"); report.add_argument("--csv",default="data/financial-data.csv")
    backfill=sub.add_parser("backfill-staging"); backfill.add_argument("--registry",default="config/companies.json"); backfill.add_argument("--raw-dir",default="data/raw")
    facts=sub.add_parser("facts"); facts.add_argument("market"); facts.add_argument("symbol"); facts.add_argument("--category"); facts.add_argument("--period-kind"); facts.add_argument("--limit",type=int,default=500)
    sub.add_parser("status")
    monitor=sub.add_parser("monitor"); monitor.add_argument("market",choices=["SA","US"]); monitor.add_argument("symbol"); monitor.add_argument("--registry",default="config/companies.json"); monitor.add_argument("--raw-dir",default="data/raw"); monitor.add_argument("--source-index"); monitor.add_argument("--source-limit",type=int,default=12); monitor.add_argument("--sa-manifest")
    sources=sub.add_parser("sources"); sources.add_argument("market"); sources.add_argument("symbol"); sources.add_argument("--status"); sources.add_argument("--limit",type=int,default=100)
    schedule=sub.add_parser("schedule"); schedule.add_argument("market",choices=["SA","US"]); schedule.add_argument("symbol"); schedule.add_argument("--every",type=int,required=True); schedule.add_argument("--mode",choices=["monitor","ingest"],default="monitor"); schedule.add_argument("--registry",default="config/companies.json"); schedule.add_argument("--raw-dir",default="data/raw"); schedule.add_argument("--sa-manifest"); schedule.add_argument("--source-index"); schedule.add_argument("--source-limit",type=int,default=12)
    worker=sub.add_parser("worker"); worker.add_argument("--once",action="store_true"); worker.add_argument("--poll",type=int,default=10); worker.add_argument("--worker-id")
    coverage=sub.add_parser("coverage"); coverage.add_argument("market"); coverage.add_argument("symbol"); coverage.add_argument("--refresh",action="store_true")
    backlog=sub.add_parser("backlog"); backlog.add_argument("market",nargs="?"); backlog.add_argument("symbol",nargs="?"); backlog.add_argument("--refresh",action="store_true"); backlog.add_argument("--status",default="active",choices=["active","open","ready","in_progress","blocked","completed","cancelled","all"]); backlog.add_argument("--limit",type=int,default=500)
    prices=sub.add_parser("prices"); prices.add_argument("market"); prices.add_argument("symbol"); prices.add_argument("--interval",default="1d"); prices.add_argument("--limit",type=int,default=100)
    actions=sub.add_parser("actions"); actions.add_argument("market"); actions.add_argument("symbol"); actions.add_argument("--type"); actions.add_argument("--limit",type=int,default=100)
    ownership=sub.add_parser("ownership"); ownership.add_argument("market"); ownership.add_argument("symbol"); ownership.add_argument("--as-of"); ownership.add_argument("--limit",type=int,default=100)
    catalog=sub.add_parser("catalog"); catalog.add_argument("--category"); catalog.add_argument("--limit",type=int,default=1000)
    a=p.parse_args(); Path(a.db).parent.mkdir(parents=True,exist_ok=True)
    if a.cmd=="init":
        db=Database(a.db); reg=CompanyRegistry.from_json(a.registry)
        for c in reg.all(): db.register_company(c)
        db.close(); print(f"initialized {a.db} with {len(reg.all())} companies"); return
    if a.cmd=="ingest":
        db=Database(a.db); reg=CompanyRegistry.from_json(a.registry); c=reg.resolve(a.market,a.symbol)
        if a.file: connector=LocalFileConnector(a.file,a.source_url)
        elif a.market=="US": connector=SecCompanyFactsConnector(_sec_user_agent())
        else:
            if not a.sa_manifest: p.error("--sa-manifest is required for SA")
            connector=SaudiManifestConnector(a.sa_manifest)
        print(json.dumps(Pipeline(db,a.raw_dir).run(c,connector),indent=2)); db.close(); return
    if a.cmd=="backfill-staging":
        db=Database(a.db); reg=CompanyRegistry.from_json(a.registry); pipeline=Pipeline(db,a.raw_dir); results=[]
        rows=db.conn.execute("SELECT source_key,company_id,source_url,filing_type,filed_at,local_path,metadata_json FROM source_documents ORDER BY created_at").fetchall()
        companies={c.company_id:c for c in reg.all()}
        for row in rows:
            company=companies.get(row["company_id"]); path=Path(row["local_path"] or "")
            if not company or not path.is_file():
                results.append({"status":"missing_raw","source_key":row["source_key"]}); continue
            doc=SourceDocument(row["company_id"],company.market,row["source_url"],row["source_key"],row["filing_type"],row["filed_at"],path.read_bytes(),metadata=json.loads(row["metadata_json"]))
            results.append(pipeline.backfill_staging(company,doc))
        db.close(); print(json.dumps(results,indent=2)); return
    if a.cmd=="report":
        export_readable_report(a.db,a.html,a.csv); print(f"created {a.html} and {a.csv}"); return
    if a.cmd=="status":
        db=Database(a.db); result=db.health(); result["jobs_by_status"]={row["status"]:row["n"] for row in db.conn.execute("SELECT status,count(*) n FROM jobs GROUP BY status")}; db.close(); print(json.dumps(result,indent=2)); return
    if a.cmd=="monitor":
        db=Database(a.db); queue=DurableJobQueue(db)
        payload={"market":a.market,"symbol":a.symbol,"registry":a.registry,"raw_dir":a.raw_dir,
                 "source_index":a.source_index,"source_limit":a.source_limit,"sa_manifest":a.sa_manifest}
        result=_monitor_once(db,queue,payload); db.close(); print(json.dumps(result,indent=2)); return
    if a.cmd=="schedule":
        if a.mode=="ingest" and a.market=="SA" and not a.sa_manifest:
            p.error("--sa-manifest is required for scheduled Saudi ingestion")
        db=Database(a.db); reg=CompanyRegistry.from_json(a.registry); company=reg.resolve(a.market,a.symbol); db.register_company(company)
        payload={"market":a.market,"symbol":a.symbol,"registry":a.registry,"raw_dir":a.raw_dir,
                 "sa_manifest":a.sa_manifest,"source_index":a.source_index,"source_limit":a.source_limit}
        DurableScheduler(db).upsert(f"{a.mode}:{a.market}:{a.symbol}",f"{a.mode.title()} {a.market}:{a.symbol}",a.mode,a.every,payload,company.company_id)
        db.close(); print(f"scheduled {a.mode} for {a.market}:{a.symbol} every {a.every} seconds"); return
    if a.cmd=="worker":
        db=Database(a.db); queue=DurableJobQueue(db); scheduler=DurableScheduler(db,queue)
        worker_id=a.worker_id or f"{socket.gethostname()}-{os.getpid()}"
        handlers={"ingest":_ingest_job_handler(db),"monitor":_monitor_job_handler(db,queue),
                  "fetch_document":_fetch_document_job_handler(db)}
        runner=Worker(queue,worker_id,handlers)
        if a.once:
            created=scheduler.tick(); worked=runner.run_once(); print(json.dumps({"scheduled_jobs":len(created),"worked":worked,"worker_id":worker_id})); db.close(); return
        try:
            while True:
                scheduler.tick()
                if not runner.run_once(): time.sleep(max(1,min(a.poll,30)))
        except KeyboardInterrupt:
            db.close(); return
    if a.cmd=="facts":
        q=FinancialQueryService(a.db); print(json.dumps(q.facts(a.market,a.symbol,a.category,a.period_kind,a.limit),indent=2)); q.close(); return
    if a.cmd=="coverage":
        if a.refresh:
            db=Database(a.db); row=db.conn.execute("SELECT company_id FROM companies WHERE market=? AND symbol=?",(a.market.upper(),a.symbol.upper())).fetchone()
            if not row: raise KeyError(f"unknown company {a.market}:{a.symbol}")
            CompanyDomainStore(db).refresh_company_coverage(row["company_id"]); db.close()
        q=FinancialQueryService(a.db); print(json.dumps(q.coverage(a.market,a.symbol),indent=2)); q.close(); return
    if a.cmd=="backlog":
        if bool(a.market) != bool(a.symbol): p.error("market and symbol must be supplied together")
        if a.refresh:
            db=Database(a.db); store=CompanyDomainStore(db)
            if a.market:
                row=db.conn.execute("SELECT company_id FROM companies WHERE market=? AND symbol=?",(a.market.upper(),a.symbol.upper())).fetchone()
                if not row: raise KeyError(f"unknown company {a.market}:{a.symbol}")
                store.refresh_company_backlog(row["company_id"])
            else: store.refresh_all_backlog()
            db.close()
        q=FinancialQueryService(a.db); print(json.dumps(q.backlog(a.market,a.symbol,a.status,a.limit),indent=2)); q.close(); return
    if a.cmd=="prices":
        q=FinancialQueryService(a.db); print(json.dumps(q.market_prices(a.market,a.symbol,a.interval,a.limit),indent=2)); q.close(); return
    if a.cmd=="actions":
        q=FinancialQueryService(a.db); print(json.dumps(q.corporate_actions(a.market,a.symbol,a.type,a.limit),indent=2)); q.close(); return
    if a.cmd=="ownership":
        q=FinancialQueryService(a.db); print(json.dumps(q.ownership(a.market,a.symbol,a.as_of,a.limit),indent=2)); q.close(); return
    if a.cmd=="catalog":
        q=FinancialQueryService(a.db); print(json.dumps(q.metric_catalog(a.category,a.limit),indent=2)); q.close(); return
    if a.cmd=="sources":
        q=FinancialQueryService(a.db); print(json.dumps(q.source_candidates(a.market,a.symbol,a.status,a.limit),indent=2)); q.close(); return
    q=FinancialQueryService(a.db); print(json.dumps(q.metric_history(a.market,a.symbol,a.metric,a.limit),indent=2)); q.close()

if __name__=="__main__": main()
