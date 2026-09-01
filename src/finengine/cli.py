import argparse, json, os, socket, time
from pathlib import Path
from .connectors import LocalFileConnector, SecCompanyFactsConnector, SaudiManifestConnector
from .database import Database
from .pipeline import Pipeline
from .query import FinancialQueryService
from .registry import CompanyRegistry
from .report import export_readable_report
from .models import SourceDocument
from .jobs import DurableJobQueue, DurableScheduler, Worker
from .domains import CompanyDomainStore


def _ingest_job_handler(db: Database):
    def handle(job):
        payload=job.payload; reg=CompanyRegistry.from_json(payload.get("registry","config/companies.json"))
        company=reg.resolve(payload["market"],payload["symbol"])
        if company.market.value=="US":
            connector=SecCompanyFactsConnector(os.environ.get("SEC_USER_AGENT","finengine contact@example.com"))
        else:
            manifest=payload.get("sa_manifest")
            if not manifest: raise ValueError("Saudi scheduled ingestion requires sa_manifest")
            connector=SaudiManifestConnector(manifest)
        return Pipeline(db,payload.get("raw_dir","data/raw")).run(company,connector,job.job_id)
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
    schedule=sub.add_parser("schedule"); schedule.add_argument("market",choices=["SA","US"]); schedule.add_argument("symbol"); schedule.add_argument("--every",type=int,required=True); schedule.add_argument("--registry",default="config/companies.json"); schedule.add_argument("--raw-dir",default="data/raw"); schedule.add_argument("--sa-manifest")
    worker=sub.add_parser("worker"); worker.add_argument("--once",action="store_true"); worker.add_argument("--poll",type=int,default=10); worker.add_argument("--worker-id")
    coverage=sub.add_parser("coverage"); coverage.add_argument("market"); coverage.add_argument("symbol"); coverage.add_argument("--refresh",action="store_true")
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
        elif a.market=="US": connector=SecCompanyFactsConnector(os.environ.get("SEC_USER_AGENT","finengine contact@example.com"))
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
    if a.cmd=="schedule":
        if a.market=="SA" and not a.sa_manifest: p.error("--sa-manifest is required for scheduled Saudi ingestion")
        db=Database(a.db); reg=CompanyRegistry.from_json(a.registry); company=reg.resolve(a.market,a.symbol); db.register_company(company)
        payload={"market":a.market,"symbol":a.symbol,"registry":a.registry,"raw_dir":a.raw_dir,"sa_manifest":a.sa_manifest}
        DurableScheduler(db).upsert(f"ingest:{a.market}:{a.symbol}",f"Ingest {a.market}:{a.symbol}","ingest",a.every,payload,company.company_id)
        db.close(); print(f"scheduled {a.market}:{a.symbol} every {a.every} seconds"); return
    if a.cmd=="worker":
        db=Database(a.db); queue=DurableJobQueue(db); scheduler=DurableScheduler(db,queue)
        worker_id=a.worker_id or f"{socket.gethostname()}-{os.getpid()}"; runner=Worker(queue,worker_id,{"ingest":_ingest_job_handler(db)})
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
    if a.cmd=="prices":
        q=FinancialQueryService(a.db); print(json.dumps(q.market_prices(a.market,a.symbol,a.interval,a.limit),indent=2)); q.close(); return
    if a.cmd=="actions":
        q=FinancialQueryService(a.db); print(json.dumps(q.corporate_actions(a.market,a.symbol,a.type,a.limit),indent=2)); q.close(); return
    if a.cmd=="ownership":
        q=FinancialQueryService(a.db); print(json.dumps(q.ownership(a.market,a.symbol,a.as_of,a.limit),indent=2)); q.close(); return
    if a.cmd=="catalog":
        q=FinancialQueryService(a.db); print(json.dumps(q.metric_catalog(a.category,a.limit),indent=2)); q.close(); return
    q=FinancialQueryService(a.db); print(json.dumps(q.metric_history(a.market,a.symbol,a.metric,a.limit),indent=2)); q.close()

if __name__=="__main__": main()
