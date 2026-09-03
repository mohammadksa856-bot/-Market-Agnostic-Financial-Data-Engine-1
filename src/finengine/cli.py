import argparse, json, os, socket, threading, time
from pathlib import Path
from .connectors import (
    IssuerReportsMonitor, LocalFileConnector, SecCompanyFactsConnector,
    SecFilingsMonitor, SaudiManifestConnector, StoredDocumentConnector,
)
from .api import create_api_server, serve_api
from .audit import audit_release
from .bootstrap import rebuild_snapshot
from .verification import ManifestVerifier
from .database import Database
from .pipeline import Pipeline
from .query import FinancialQueryService
from .registry import CompanyRegistry
from .report import export_readable_report
from .models import SourceDocument
from .jobs import DurableJobQueue, DurableScheduler, Worker
from .domains import CompanyDomainStore
from .monitoring import DocumentArchiver, MonitorService
from .telegram import TelegramBot


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
        company, monitor, "fetch_document", {
            "raw_dir": common_payload["raw_dir"], "registry": registry_path,
        }, True,
    )


def _monitor_job_handler(db: Database, queue: DurableJobQueue):
    def handle(job):
        return _monitor_once(db, queue, job.payload)
    return handle


def _fetch_document_job_handler(db: Database, queue: DurableJobQueue):
    def handle(job):
        candidate_id = int(job.payload["candidate_id"])
        try:
            result=DocumentArchiver(db, job.payload.get("raw_dir", "data/raw")).fetch(candidate_id)
            if result.get("next_stage") == "extraction":
                extraction_payload={
                    "source_key":result["source_key"],
                    "raw_dir":job.payload.get("raw_dir","data/raw"),
                    "registry":job.payload.get("registry","config/companies.json"),
                }
                extraction_job,created=queue.enqueue(
                    "extract_document",extraction_payload,job.company_id,result["source_key"],
                    idempotency_key=f"extract:{result['source_key']}",priority=20,
                )
                result["extraction_job_id"]=extraction_job
                result["extraction_job_created"]=created
            return result
        except Exception:
            db.set_source_candidate_status(candidate_id, "error")
            raise
    return handle


def _extract_document_job_handler(db: Database):
    def handle(job):
        source_key=job.payload["source_key"]; row=db.stored_source(source_key)
        registry=CompanyRegistry.from_json(job.payload.get("registry","config/companies.json"))
        company=registry.get(row["company_id"]); path=Path(row["local_path"] or "")
        if not path.is_file(): raise FileNotFoundError(f"archived source is missing: {path}")
        document=SourceDocument(
            row["company_id"],company.market,row["source_url"],row["source_key"],row["filing_type"],
            row["filed_at"],path.read_bytes(),row["content_type"],json.loads(row["metadata_json"]),
        )
        if row["content_type"] == "application/json":
            return Pipeline(db,job.payload.get("raw_dir","data/raw")).run(
                company,StoredDocumentConnector(document),job.job_id,
            )
        code="binary_extractor_required"
        db.exception(company.company_id,source_key,"extraction",code,
                     "A reviewed PDF/XLSX extraction adapter must produce source-faithful facts.",
                     {"content_type":row["content_type"],"local_path":row["local_path"]})
        db.set_source_status(source_key,"review_required")
        db.publication_batch(source_key,company.company_id,"blocked",0,0)
        key=f"extraction:{source_key}"
        db.upsert_backlog_item(
            key,"document_extraction","financial",f"Extract {row['filing_type']}: {company.name}",
            company_id=company.company_id,source_url=row["source_url"],priority=10,
            payload={"source_key":source_key,"content_type":row["content_type"],
                     "local_path":row["local_path"],"origin":"extraction_queue"},
        )
        with db.conn:
            db.conn.execute("UPDATE backlog_items SET status='ready',updated_at=CURRENT_TIMESTAMP WHERE idempotency_key=?",(key,))
        return {"status":"review_required","stage":"extraction","source_key":source_key,
                "code":code,"published":0}
    return handle

def main():
    p=argparse.ArgumentParser(prog="finengine"); p.add_argument("--db",default="data/financial.sqlite3"); sub=p.add_subparsers(dest="cmd",required=True)
    init=sub.add_parser("init"); init.add_argument("--registry",default="config/companies.json")
    bootstrap=sub.add_parser("bootstrap"); bootstrap.add_argument("--imports",default="data/imports"); bootstrap.add_argument("--registry",default="config/companies.json"); bootstrap.add_argument("--raw-dir",default="data/raw"); bootstrap.add_argument("--replace",action="store_true"); bootstrap.add_argument("--html",default="data/financial-report.html"); bootstrap.add_argument("--csv",default="data/financial-data.csv"); bootstrap.add_argument("--schedule-every",type=int)
    audit=sub.add_parser("audit"); audit.add_argument("--project-root",default="."); audit.add_argument("--strict-warnings",action="store_true")
    verify=sub.add_parser("verify"); verify.add_argument("prefix",nargs="?"); verify.add_argument("--imports",default="data/imports"); verify.add_argument("--strict-warnings",action="store_true")
    read=sub.add_parser("read"); read.add_argument("pdf"); read.add_argument("market",choices=["SA","US"]); read.add_argument("symbol"); read.add_argument("--registry",default="config/companies.json"); read.add_argument("--period-end",required=True); read.add_argument("--fiscal-year",type=int,required=True); read.add_argument("--source-url",required=True); read.add_argument("--filed-at",required=True); read.add_argument("--filing-type",default="financial-statements"); read.add_argument("--out")
    fetch=sub.add_parser("fetch"); fetch.add_argument("market",choices=["SA","US"]); fetch.add_argument("symbol"); fetch.add_argument("url"); fetch.add_argument("--discover",action="store_true"); fetch.add_argument("--raw-dir",default="data/raw"); fetch.add_argument("--show",action="store_true",help="run a visible browser instead of headless")
    ingest=sub.add_parser("ingest"); ingest.add_argument("market",choices=["SA","US"]); ingest.add_argument("symbol"); ingest.add_argument("--registry",default="config/companies.json"); ingest.add_argument("--sa-manifest"); ingest.add_argument("--file"); ingest.add_argument("--source-url"); ingest.add_argument("--raw-dir",default="data/raw")
    query=sub.add_parser("query"); query.add_argument("market"); query.add_argument("symbol"); query.add_argument("metric"); query.add_argument("--limit",type=int,default=20)
    dossier=sub.add_parser("dossier"); dossier.add_argument("market"); dossier.add_argument("symbol")
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
    catalog=sub.add_parser("catalog"); catalog.add_argument("--category"); catalog.add_argument("--domain"); catalog.add_argument("--limit",type=int,default=1000)
    completeness=sub.add_parser("completeness"); completeness.add_argument("market"); completeness.add_argument("symbol"); completeness.add_argument("--refresh",action="store_true")
    exceptions=sub.add_parser("exceptions"); exceptions.add_argument("market",nargs="?"); exceptions.add_argument("symbol",nargs="?"); exceptions.add_argument("--status",default="open",choices=["open","resolved","all"]); exceptions.add_argument("--limit",type=int,default=100)
    resolve=sub.add_parser("resolve-exception"); resolve.add_argument("exception_id",type=int); resolve.add_argument("--resolution",required=True); resolve.add_argument("--assigned-to")
    retry=sub.add_parser("retry-source"); retry.add_argument("source_key"); retry.add_argument("--registry",default="config/companies.json"); retry.add_argument("--raw-dir",default="data/raw")
    serve=sub.add_parser("serve"); serve.add_argument("--host",default="127.0.0.1"); serve.add_argument("--port",type=int,default=8000); serve.add_argument("--api-key-env",default="FINENGINE_API_KEY")
    run=sub.add_parser("run"); run.add_argument("--host",default="127.0.0.1"); run.add_argument("--port",type=int,default=8000); run.add_argument("--api-key-env",default="FINENGINE_API_KEY"); run.add_argument("--poll",type=int,default=10); run.add_argument("--worker-id")
    telegram=sub.add_parser("telegram"); telegram.add_argument("--token-env",default="TELEGRAM_BOT_TOKEN"); telegram.add_argument("--poll",type=int,default=2)
    a=p.parse_args(); Path(a.db).parent.mkdir(parents=True,exist_ok=True)
    if a.cmd=="init":
        db=Database(a.db); reg=CompanyRegistry.from_json(a.registry)
        for c in reg.all(): db.register_company(c)
        db.close(); print(f"initialized {a.db} with {len(reg.all())} companies"); return
    if a.cmd=="bootstrap":
        result=rebuild_snapshot(a.db,a.imports,a.registry,a.raw_dir,a.replace,a.html,a.csv,a.schedule_every)
        print(json.dumps(result,indent=2)); return
    if a.cmd=="audit":
        result=audit_release(a.db,a.project_root); print(json.dumps(result,indent=2))
        if result["failures"] or (a.strict_warnings and result["warnings"]): raise SystemExit(1)
        return
    if a.cmd=="verify":
        result=ManifestVerifier(a.imports).verify(a.prefix); print(json.dumps(result,indent=2,ensure_ascii=False))
        if result["failures"] or result["unmapped_labels"] or (a.strict_warnings and result["warnings"]): raise SystemExit(1)
        return
    if a.cmd=="read":
        from .reading import StatementReader
        company=CompanyRegistry.from_json(a.registry).resolve(a.market,a.symbol)
        manifest=StatementReader(a.pdf).read(
            market=a.market,symbol=a.symbol,currency=company.currency,source_url=a.source_url,
            filed_at=a.filed_at,period_end=a.period_end,fiscal_year=a.fiscal_year,filing_type=a.filing_type)
        text=json.dumps(manifest,indent=2,ensure_ascii=False)
        if a.out: Path(a.out).write_text(text,encoding="utf-8"); print(f"wrote {len(manifest['facts'])} facts to {a.out}")
        else: print(text)
        return
    if a.cmd=="fetch":
        from .fetching import BrowserFetcher
        fetcher=BrowserFetcher(raw_dir=a.raw_dir,headless=not a.show)
        if a.discover:
            print(json.dumps(fetcher.discover(a.url),indent=2,ensure_ascii=False))
        else:
            print(json.dumps(fetcher.fetch(a.url,a.market,a.symbol),indent=2,ensure_ascii=False))
        return
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
                  "fetch_document":_fetch_document_job_handler(db,queue),
                  "extract_document":_extract_document_job_handler(db)}
        runner=Worker(queue,worker_id,handlers)
        if a.once:
            created=scheduler.tick(); worked=runner.run_once(); print(json.dumps({"scheduled_jobs":len(created),"worked":worked,"worker_id":worker_id})); db.close(); return
        try:
            while True:
                scheduler.tick()
                if not runner.run_once(): time.sleep(max(1,min(a.poll,30)))
        except KeyboardInterrupt:
            db.close(); return
    if a.cmd=="serve":
        api_key=os.environ.get(a.api_key_env) or None
        print(f"read-only API listening on http://{a.host}:{a.port}")
        try: serve_api(a.db,a.host,a.port,api_key)
        except KeyboardInterrupt: return
    if a.cmd=="run":
        db=Database(a.db); queue=DurableJobQueue(db); scheduler=DurableScheduler(db,queue)
        worker_id=a.worker_id or f"{socket.gethostname()}-{os.getpid()}"
        handlers={"ingest":_ingest_job_handler(db),"monitor":_monitor_job_handler(db,queue),
                  "fetch_document":_fetch_document_job_handler(db,queue),
                  "extract_document":_extract_document_job_handler(db)}
        runner=Worker(queue,worker_id,handlers)
        server=create_api_server(a.db,a.host,a.port,os.environ.get(a.api_key_env) or None)
        api_thread=threading.Thread(target=server.serve_forever,name="finengine-api",daemon=True); api_thread.start()
        print(f"engine worker and read-only API running on http://{a.host}:{a.port}")
        try:
            while True:
                scheduler.tick()
                if not runner.run_once(): time.sleep(max(1,min(a.poll,30)))
        except KeyboardInterrupt: pass
        finally:
            server.shutdown(); server.server_close(); api_thread.join(timeout=5); db.close()
        return
    if a.cmd=="telegram":
        token=os.environ.get(a.token_env,"").strip()
        if not token: p.error(f"{a.token_env} is required")
        try: TelegramBot(a.db,token).serve(a.poll)
        except KeyboardInterrupt: return
    if a.cmd=="exceptions":
        if bool(a.market) != bool(a.symbol): p.error("market and symbol must be supplied together")
        q=FinancialQueryService(a.db); print(json.dumps(q.exceptions(a.market,a.symbol,a.status,a.limit),indent=2)); q.close(); return
    if a.cmd=="resolve-exception":
        db=Database(a.db); result=db.resolve_exception(a.exception_id,a.resolution,a.assigned_to); db.close(); print(json.dumps(result,indent=2)); return
    if a.cmd=="retry-source":
        db=Database(a.db); row=db.stored_source(a.source_key); reg=CompanyRegistry.from_json(a.registry); company=reg.get(row["company_id"])
        path=Path(row["local_path"] or "")
        if not path.is_file(): db.close(); raise FileNotFoundError(f"archived source is missing: {path}")
        document=SourceDocument(row["company_id"],company.market,row["source_url"],row["source_key"],row["filing_type"],row["filed_at"],path.read_bytes(),row["content_type"],json.loads(row["metadata_json"]))
        db.reopen_source_for_retry(a.source_key)
        result=Pipeline(db,a.raw_dir).run(company,StoredDocumentConnector(document)); db.close(); print(json.dumps(result,indent=2)); return
    if a.cmd=="facts":
        q=FinancialQueryService(a.db); print(json.dumps(q.facts(a.market,a.symbol,a.category,a.period_kind,a.limit),indent=2)); q.close(); return
    if a.cmd=="dossier":
        q=FinancialQueryService(a.db); print(json.dumps(q.company_dossier(a.market,a.symbol),ensure_ascii=False,indent=2)); q.close(); return
    if a.cmd=="coverage":
        if a.refresh:
            db=Database(a.db); row=db.conn.execute("SELECT company_id FROM companies WHERE market=? AND symbol=?",(a.market.upper(),a.symbol.upper())).fetchone()
            if not row: raise KeyError(f"unknown company {a.market}:{a.symbol}")
            CompanyDomainStore(db).refresh_company_coverage(row["company_id"]); db.close()
        q=FinancialQueryService(a.db); print(json.dumps(q.coverage(a.market,a.symbol),indent=2)); q.close(); return
    if a.cmd=="completeness":
        if a.refresh:
            db=Database(a.db); row=db.conn.execute("SELECT company_id FROM companies WHERE market=? AND symbol=?",(a.market.upper(),a.symbol.upper())).fetchone()
            if not row: db.close(); raise KeyError(f"unknown company {a.market}:{a.symbol}")
            CompanyDomainStore(db).refresh_catalog_completeness(row["company_id"]); db.close()
        q=FinancialQueryService(a.db); print(json.dumps(q.completeness(a.market,a.symbol),indent=2)); q.close(); return
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
        q=FinancialQueryService(a.db); print(json.dumps(q.data_catalog(a.category,a.domain,a.limit),indent=2)); q.close(); return
    if a.cmd=="sources":
        q=FinancialQueryService(a.db); print(json.dumps(q.source_candidates(a.market,a.symbol,a.status,a.limit),indent=2)); q.close(); return
    q=FinancialQueryService(a.db); print(json.dumps(q.metric_history(a.market,a.symbol,a.metric,a.limit),indent=2)); q.close()

if __name__=="__main__": main()
