import argparse, calendar, json, os, re, socket, threading, time
from datetime import date
from pathlib import Path
from .connectors import (
    IssuerReportsMonitor, LocalFileConnector, SecCompanyFactsConnector,
    SecFilingsMonitor, SaudiManifestConnector, StoredDocumentConnector,
)
from .api import create_api_server, serve_api
from .audit import audit_release
from .archive import archive_manifest_sources
from .bootstrap import rebuild_snapshot
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


def _browser_headless() -> bool:
    """Allow production to run a visible Chromium inside an Xvfb display."""
    return os.environ.get("FINENGINE_BROWSER_HEADLESS", "true").strip().lower() not in {
        "0", "false", "no", "off",
    }


def _ingest_job_handler(db: Database):
    def handle(job):
        payload=job.payload; reg=CompanyRegistry.combined(db.conn,payload.get("registry","config/companies.json"))
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
    registry = CompanyRegistry.combined(db.conn, registry_path)
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
    browser = bool(payload.get("browser"))
    if browser:
        from .fetching import BrowserFetcher, BrowserIssuerMonitor
        monitor = BrowserIssuerMonitor(
            source_index,
            fetcher=BrowserFetcher(
                raw_dir=payload.get("raw_dir", "data/raw"),
                headless=_browser_headless(),
            ),
            max_documents=int(payload.get("source_limit", 12)),
        )
    else:
        monitor = IssuerReportsMonitor(source_index, max_documents=int(payload.get("source_limit", 12)))
    return service.poll(
        company, monitor, "fetch_document", {
            "raw_dir": common_payload["raw_dir"], "registry": registry_path,
            "browser": browser, "llm": bool(payload.get("llm")),
        }, True,
    )


def _monitor_job_handler(db: Database, queue: DurableJobQueue):
    def handle(job):
        return _monitor_once(db, queue, job.payload)
    return handle


def _fetch_document_job_handler(db: Database, queue: DurableJobQueue):
    def handle(job):
        candidate_id = int(job.payload["candidate_id"])
        raw_dir = job.payload.get("raw_dir", "data/raw")
        content_fetcher = None
        candidate_fetcher = None
        if job.payload.get("browser"):
            from .fetching import BrowserFetcher
            candidate_fetcher = BrowserFetcher(
                raw_dir, headless=_browser_headless()
            ).download_candidate
        try:
            result=DocumentArchiver(
                db, raw_dir, content_fetcher=content_fetcher,
                candidate_fetcher=candidate_fetcher,
            ).fetch(candidate_id)
            if result.get("next_stage") == "extraction":
                extraction_payload={
                    "source_key":result["source_key"],
                    "raw_dir":raw_dir,
                    "registry":job.payload.get("registry","config/companies.json"),
                    "llm":bool(job.payload.get("llm")),
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


def _company_profile(company) -> str:
    """Which statement-layout map the reader should use for this issuer."""
    industry = (getattr(company, "industry", "") or "").lower()
    if "bank" in industry:
        return "bank"
    return "corporate"


def _source_period(row: dict, company) -> tuple[str, int] | None:
    """Derive an interim period only from explicit source metadata."""
    try:
        metadata = json.loads(row["metadata_json"] or "{}")
    except (KeyError, TypeError, json.JSONDecodeError):
        metadata = {}
    title = str(metadata.get("title") or "")
    iso = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", title)
    if iso:
        year, month, day = (int(value) for value in iso.groups())
        try:
            return date(year, month, day).isoformat(), year
        except ValueError:
            return None
    explicit = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", title)
    if explicit:
        day, month, year = (int(value) for value in explicit.groups())
        try:
            return date(year, month, day).isoformat(), year
        except ValueError:
            return None
    named = re.search(
        r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+(20\d{2})\b", title, re.I,
    )
    if named:
        day, month_name, year = named.groups()
        month = {name.lower(): index for index, name in enumerate(
            ("January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"), 1
        )}[month_name.lower()]
        try:
            return date(int(year), month, int(day)).isoformat(), int(year)
        except ValueError:
            return None
    quarter = re.search(r"\bQ([1-4])\b", title, re.I)
    year_match = re.search(r"\b(20\d{2})\b", title)
    if not quarter or not year_match:
        return None
    fiscal_year, fiscal_quarter = int(year_match.group(1)), int(quarter.group(1))
    try:
        fiscal_end_month, fiscal_end_day = (
            int(value) for value in company.fiscal_year_end.split("-")
        )
    except (AttributeError, TypeError, ValueError):
        fiscal_end_month, fiscal_end_day = 12, 31
    month_index = (fiscal_year * 12 + fiscal_end_month - 1) - (4 - fiscal_quarter) * 3
    year, month = divmod(month_index, 12)
    month += 1
    day = min(fiscal_end_day, calendar.monthrange(year, month)[1])
    return date(year, month, day).isoformat(), fiscal_year


def _read_pdf_manifest(pdf_path: Path, company, row: dict, use_llm: bool) -> tuple[dict, dict, str]:
    """Read deterministically; use the LLM only when explicitly enabled."""
    import tempfile
    from .reading import StatementReader
    from .verification import ManifestVerifier

    def verify(manifest: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            return ManifestVerifier(directory).verify()

    kwargs = {
        "market": company.market.value,
        "symbol": company.symbol,
        "currency": company.currency,
        "source_url": row["source_url"],
        "filed_at": row["filed_at"],
        "filing_type": row["filing_type"],
        "profile": _company_profile(company),
        "fiscal_year_end": company.fiscal_year_end,
    }
    source_period = _source_period(row, company)
    if source_period:
        kwargs["period_end"], kwargs["fiscal_year"] = source_period
    reader = StatementReader(pdf_path)
    manifest = reader.read(**kwargs)
    report = verify(manifest)
    reader_source = "deterministic+ocr" if reader.used_ocr else "deterministic"
    if not report["ok"] and use_llm and os.environ.get("ANTHROPIC_API_KEY"):
        from .reading_llm import llm_read
        manifest = llm_read(pdf_path, **kwargs)
        report = verify(manifest)
        reader_source = "llm"
    return manifest, report, reader_source


def _read_xlsx_manifest(xlsx_path: Path, company, row: dict,
                        mapping_path: Path) -> tuple[dict, dict]:
    """Read a reviewed issuer supplement map and verify before publication."""
    import tempfile
    from .reading_xlsx import SupplementReader
    from .verification import ManifestVerifier

    manifest = SupplementReader(xlsx_path, mapping_path).read(
        market=company.market.value,
        symbol=company.symbol,
        currency=company.currency,
        filed_at=row["filed_at"],
        filing_type=row["filing_type"],
        period_kinds=("fy", "quarter", "ytd"),
    )
    # The immutable archived URL, not a URL embedded in configuration, is the
    # authoritative provenance for this particular workbook version.
    manifest["source_url"] = row["source_url"]
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        report = ManifestVerifier(directory).verify()
    return manifest, report


def _extract_document_job_handler(db: Database):
    def handle(job):
        source_key=job.payload["source_key"]; row=db.stored_source(source_key)
        registry=CompanyRegistry.combined(db.conn,job.payload.get("registry","config/companies.json"))
        company=registry.get(row["company_id"]); path=Path(row["local_path"] or "")
        if not path.is_file(): raise FileNotFoundError(f"archived source is missing: {path}")
        document=SourceDocument(
            row["company_id"],company.market,row["source_url"],row["source_key"],row["filing_type"],
            row["filed_at"],path.read_bytes(),row["content_type"],json.loads(row["metadata_json"]),
        )
        raw_dir=job.payload.get("raw_dir","data/raw")
        if row["content_type"] == "application/json":
            return Pipeline(db,raw_dir).run(
                company,StoredDocumentConnector(document),job.job_id,
            )
        if row["content_type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            mapping_path = Path("config") / "supplements" / f"{company.symbol}.json"
            if not mapping_path.is_file():
                manifest=None; report=None; reader_source="xlsx-supplement"
                read_error=f"reviewed issuer mapping is missing: {mapping_path}"
                code="xlsx_mapping_required"
            else:
                try:
                    manifest,report=_read_xlsx_manifest(path,company,row,mapping_path)
                except Exception as error:
                    manifest=None; report=None; read_error=str(error)
                    code="xlsx_extraction_failed"
                else:
                    reader_source="xlsx-supplement"; read_error=None
                    code="xlsx_extraction_failed"
        elif row["content_type"] == "application/pdf":
            interim_period_missing = (
                row["filing_type"] == "interim-report" and
                _source_period(row, company) is None
            )
            if interim_period_missing:
                manifest=None; report=None; reader_source=None
                read_error=(
                    "automatic interim extraction is held for review because one PDF can "
                    "contain quarter and YTD columns for the same date"
                )
            else:
                try:
                    manifest,report,reader_source=_read_pdf_manifest(
                        path,company,row,bool(job.payload.get("llm")),
                    )
                except Exception as error:
                    manifest=None; report=None; reader_source=None; read_error=str(error)
                else:
                    read_error=None
        else:
            manifest=None; report=None; reader_source=None; read_error=None
            code="binary_extractor_required"
        if row["content_type"] in {
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }:
            if manifest is not None and report["ok"]:
                manifest_dir=Path(raw_dir)/company.market.value/company.symbol/"manifests"
                manifest_dir.mkdir(parents=True,exist_ok=True)
                manifest_path=manifest_dir/f"{path.stem}.json"
                manifest_path.write_text(
                    json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8",
                )
                prior_extraction_exceptions = [
                    record["id"] for record in db.conn.execute(
                        """SELECT id FROM exceptions
                           WHERE source_key=? AND stage='extraction' AND status='open'""",
                        (source_key,),
                    )
                ]
                result=Pipeline(db,raw_dir).run(
                    company,LocalFileConnector(
                        manifest_path,row["source_url"],source_key=source_key
                    ),job.job_id,
                )
                if result["status"] == "published":
                    for exception_id in prior_extraction_exceptions:
                        db.resolve_exception(
                            exception_id,
                            "Document reprocessed and published successfully.",
                            "pipeline",
                        )
                    db.complete_backlog_item(f"extraction:{source_key}")
                result["reader"]=reader_source
                result["manifest_path"]=str(manifest_path)
                return result
            if row["content_type"] == "application/pdf":
                if interim_period_missing:
                    code="interim_period_semantics_required"
                elif read_error and "optional OCR dependencies" in read_error:
                    code="pdf_ocr_required"
                else:
                    code="pdf_extraction_failed"
            db.exception(
                company.company_id,source_key,"extraction",code,
                "The reader agent could not produce a manifest that passes verify.",
                {"content_type":row["content_type"],"local_path":row["local_path"],
                 "reader":reader_source,"read_error":read_error,
                 "verify_failures":report["failures"] if report else None},
            )
        else:
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
    backup=sub.add_parser("backup"); backup.add_argument("--output-dir",default="backups"); backup.add_argument("--keep",type=int,default=14)
    bundle=sub.add_parser("backup-bundle"); bundle.add_argument("--output-dir",default="backups/bundles"); bundle.add_argument("--project-root",default="."); bundle.add_argument("--keep",type=int,default=7)
    production=sub.add_parser("configure-production"); production.add_argument("--registry",default="config/companies.json"); production.add_argument("--every",type=int,default=21600); production.add_argument("--source-limit",type=int,default=50); production.add_argument("--no-llm",action="store_true")
    universe_sync=sub.add_parser("universe-sync"); universe_sync.add_argument("market",choices=["SA","US"]); universe_sync.add_argument("--input"); universe_sync.add_argument("--source-url"); universe_sync.add_argument("--raw-dir",default="data/raw/universe"); universe_sync.add_argument("--show",action="store_true",help="show browser during live Saudi directory sync")
    universe_activate=sub.add_parser("universe-activate"); universe_activate.add_argument("market",choices=["SA","US"]); universe_activate.add_argument("--limit",type=int,default=50); universe_activate.add_argument("--exchange",action="append",default=[]); universe_activate.add_argument("--symbols"); universe_activate.add_argument("--enable",action="store_true"); universe_activate.add_argument("--schedule-every",type=int); universe_activate.add_argument("--registry",default="config/companies.json"); universe_activate.add_argument("--include-funds",action="store_true")
    universe_enrich=sub.add_parser("universe-enrich"); universe_enrich.add_argument("--batch"); universe_enrich.add_argument("--limit",type=int,default=25); universe_enrich.add_argument("--raw-dir",default="data/raw/universe")
    universe_promote=sub.add_parser("universe-promote"); universe_promote.add_argument("batch"); universe_promote.add_argument("--limit",type=int,default=10); universe_promote.add_argument("--schedule-every",type=int,default=21600); universe_promote.add_argument("--registry",default="config/companies.json")
    sub.add_parser("universe-status")
    archive=sub.add_parser("archive-sources"); archive.add_argument("--imports",default="data/imports"); archive.add_argument("--registry",default="config/companies.json"); archive.add_argument("--raw-dir",default="data/raw"); archive.add_argument("--index"); archive.add_argument("--project-root",default="."); archive.add_argument("--market"); archive.add_argument("--symbol")
    audit=sub.add_parser("audit"); audit.add_argument("--project-root",default="."); audit.add_argument("--strict-warnings",action="store_true")
    verify=sub.add_parser("verify"); verify.add_argument("prefix",nargs="?"); verify.add_argument("--imports",default="data/imports"); verify.add_argument("--strict-warnings",action="store_true")
    read=sub.add_parser("read"); read.add_argument("pdf"); read.add_argument("market",choices=["SA","US"]); read.add_argument("symbol"); read.add_argument("--registry",default="config/companies.json"); read.add_argument("--period-end"); read.add_argument("--fiscal-year",type=int); read.add_argument("--source-url",required=True); read.add_argument("--filed-at",required=True); read.add_argument("--filing-type",default="financial-statements"); read.add_argument("--out"); read.add_argument("--llm",action="store_true"); read.add_argument("--llm-only",action="store_true"); read.add_argument("--model",default="claude-opus-5"); read.add_argument("--profile",choices=["corporate","bank"])
    readx=sub.add_parser("read-xlsx"); readx.add_argument("xlsx"); readx.add_argument("market",choices=["SA","US"]); readx.add_argument("symbol"); readx.add_argument("--registry",default="config/companies.json"); readx.add_argument("--mapping"); readx.add_argument("--filed-at",required=True); readx.add_argument("--filing-type",default="data-supplement"); readx.add_argument("--period-kinds",default="fy"); readx.add_argument("--out")
    fetch=sub.add_parser("fetch"); fetch.add_argument("market",choices=["SA","US"]); fetch.add_argument("symbol"); fetch.add_argument("url"); fetch.add_argument("--discover",action="store_true"); fetch.add_argument("--raw-dir",default="data/raw"); fetch.add_argument("--show",action="store_true")
    ingest=sub.add_parser("ingest"); ingest.add_argument("market",choices=["SA","US"]); ingest.add_argument("symbol"); ingest.add_argument("--registry",default="config/companies.json"); ingest.add_argument("--sa-manifest"); ingest.add_argument("--file"); ingest.add_argument("--source-url"); ingest.add_argument("--raw-dir",default="data/raw")
    query=sub.add_parser("query"); query.add_argument("market"); query.add_argument("symbol"); query.add_argument("metric"); query.add_argument("--limit",type=int,default=20)
    dossier=sub.add_parser("dossier"); dossier.add_argument("market"); dossier.add_argument("symbol"); dossier.add_argument("--output")
    page=sub.add_parser("page"); page.add_argument("market"); page.add_argument("symbol"); page.add_argument("--output")
    report=sub.add_parser("report"); report.add_argument("--html",default="data/financial-report.html"); report.add_argument("--csv",default="data/financial-data.csv")
    backfill=sub.add_parser("backfill-staging"); backfill.add_argument("--registry",default="config/companies.json"); backfill.add_argument("--raw-dir",default="data/raw")
    facts=sub.add_parser("facts"); facts.add_argument("market"); facts.add_argument("symbol"); facts.add_argument("--category"); facts.add_argument("--period-kind"); facts.add_argument("--limit",type=int,default=500)
    sub.add_parser("status")
    monitor=sub.add_parser("monitor"); monitor.add_argument("market",choices=["SA","US"]); monitor.add_argument("symbol"); monitor.add_argument("--registry",default="config/companies.json"); monitor.add_argument("--raw-dir",default="data/raw"); monitor.add_argument("--source-index"); monitor.add_argument("--source-limit",type=int,default=12); monitor.add_argument("--sa-manifest"); monitor.add_argument("--browser",action="store_true"); monitor.add_argument("--llm",action="store_true")
    sources=sub.add_parser("sources"); sources.add_argument("market"); sources.add_argument("symbol"); sources.add_argument("--status"); sources.add_argument("--limit",type=int,default=100)
    schedule=sub.add_parser("schedule"); schedule.add_argument("market",choices=["SA","US"]); schedule.add_argument("symbol"); schedule.add_argument("--every",type=int,required=True); schedule.add_argument("--mode",choices=["monitor","ingest"],default="monitor"); schedule.add_argument("--registry",default="config/companies.json"); schedule.add_argument("--raw-dir",default="data/raw"); schedule.add_argument("--sa-manifest"); schedule.add_argument("--source-index"); schedule.add_argument("--source-limit",type=int,default=12); schedule.add_argument("--browser",action="store_true"); schedule.add_argument("--llm",action="store_true")
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
    resolve_source=sub.add_parser("resolve-source-exceptions"); resolve_source.add_argument("source_key"); resolve_source.add_argument("--resolution",required=True); resolve_source.add_argument("--assigned-to")
    retry=sub.add_parser("retry-source"); retry.add_argument("source_key"); retry.add_argument("--registry",default="config/companies.json"); retry.add_argument("--raw-dir",default="data/raw")
    serve=sub.add_parser("serve"); serve.add_argument("--host",default="127.0.0.1"); serve.add_argument("--port",type=int,default=8000); serve.add_argument("--api-key-env",default="FINENGINE_API_KEY")
    run=sub.add_parser("run"); run.add_argument("--host",default="127.0.0.1"); run.add_argument("--port",type=int,default=8000); run.add_argument("--api-key-env",default="FINENGINE_API_KEY"); run.add_argument("--poll",type=int,default=10); run.add_argument("--worker-id")
    telegram=sub.add_parser("telegram"); telegram.add_argument("--token-env",default="TELEGRAM_BOT_TOKEN"); telegram.add_argument("--poll",type=int,default=2)
    export=sub.add_parser("export-supabase")
    export.add_argument("market",nargs="?",choices=["SA","US"]); export.add_argument("symbol",nargs="?")
    export.add_argument("--all",action="store_true"); export.add_argument("--registry",default="config/companies.json")
    export.add_argument("--url-env",default="SUPABASE_URL"); export.add_argument("--key-env",default="SUPABASE_SERVICE_KEY")
    export.add_argument("--batch",type=int,default=500); export.add_argument("--prune",action="store_true")
    export.add_argument("--sql-out"); export.add_argument("--dry-run",action="store_true")
    a=p.parse_args(); Path(a.db).parent.mkdir(parents=True,exist_ok=True)
    if a.cmd=="init":
        db=Database(a.db); reg=CompanyRegistry.from_json(a.registry)
        for c in reg.all(): db.register_company(c)
        db.close(); print(f"initialized {a.db} with {len(reg.all())} companies"); return
    if a.cmd=="bootstrap":
        result=rebuild_snapshot(a.db,a.imports,a.registry,a.raw_dir,a.replace,a.html,a.csv,a.schedule_every)
        print(json.dumps(result,indent=2)); return
    if a.cmd=="backup":
        from .operations import backup_database
        print(json.dumps(backup_database(a.db,a.output_dir,a.keep),indent=2)); return
    if a.cmd=="backup-bundle":
        from .operations import create_portable_bundle
        print(json.dumps(create_portable_bundle(
            a.db,a.output_dir,a.project_root,a.keep),indent=2)); return
    if a.cmd=="configure-production":
        from .operations import configure_production_schedules
        result=configure_production_schedules(a.db,a.registry,a.every,a.source_limit,not a.no_llm)
        print(json.dumps(result,indent=2)); return
    if a.cmd=="universe-sync":
        from .universe import sync_universe
        db=Database(a.db)
        try:
            user_agent=_sec_user_agent() if a.market=="US" and not a.input else None
            result=sync_universe(db,a.market,a.raw_dir,user_agent,a.input,a.source_url,
                                 headless=not a.show)
        finally: db.close()
        print(json.dumps(result,ensure_ascii=False,indent=2)); return
    if a.cmd=="universe-activate":
        from .universe import activate_universe
        symbols=tuple(value.strip() for value in (a.symbols or "").split(",") if value.strip())
        db=Database(a.db)
        try:
            result=activate_universe(db,a.market,a.limit,tuple(a.exchange),symbols,
                                     a.enable,a.schedule_every,a.registry,a.include_funds)
        finally: db.close()
        print(json.dumps(result,ensure_ascii=False,indent=2)); return
    if a.cmd=="universe-enrich":
        from .universe import enrich_activation_batch
        db=Database(a.db)
        try: result=enrich_activation_batch(db,a.raw_dir,_sec_user_agent(),a.batch,a.limit)
        finally: db.close()
        print(json.dumps(result,ensure_ascii=False,indent=2)); return
    if a.cmd=="universe-promote":
        from .universe import promote_activation_batch
        db=Database(a.db)
        try: result=promote_activation_batch(db,a.batch,a.limit,a.schedule_every,a.registry)
        finally: db.close()
        print(json.dumps(result,ensure_ascii=False,indent=2)); return
    if a.cmd=="universe-status":
        q=FinancialQueryService(a.db); print(json.dumps(q.universe_status(),ensure_ascii=False,indent=2)); q.close(); return
    if a.cmd=="archive-sources":
        result=archive_manifest_sources(a.db,a.imports,a.registry,a.raw_dir,a.index,
                                        a.project_root,a.market,a.symbol)
        print(json.dumps(result,ensure_ascii=False,indent=2)); return
    if a.cmd=="audit":
        result=audit_release(a.db,a.project_root); print(json.dumps(result,indent=2))
        if result["failures"] or (a.strict_warnings and result["warnings"]): raise SystemExit(1)
        return
    if a.cmd=="verify":
        from .verification import ManifestVerifier
        result=ManifestVerifier(a.imports).verify(a.prefix)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        if result["failures"] or result["unmapped_labels"] or (a.strict_warnings and result["warnings"]):
            raise SystemExit(1)
        return
    if a.cmd=="read-xlsx":
        import tempfile
        from .verification import ManifestVerifier
        from .reading_xlsx import SupplementReader
        company=CompanyRegistry.from_json(a.registry).resolve(a.market,a.symbol)
        mapping=a.mapping or f"config/supplements/{a.symbol}.json"
        manifest=SupplementReader(a.xlsx,mapping).read(
            market=a.market,symbol=a.symbol,currency=company.currency,filed_at=a.filed_at,
            filing_type=a.filing_type,period_kinds=tuple(a.period_kinds.split(",")))
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,"m.json").write_text(json.dumps(manifest),encoding="utf-8")
            verification=ManifestVerifier(directory).verify()
        manifest["verify"]={"ok":verification["ok"],"passed":verification["passed"],
                            "failures":verification["failures"],"source":"xlsx-supplement"}
        output=json.dumps(manifest,indent=2,ensure_ascii=False)
        if a.out:
            Path(a.out).write_text(output,encoding="utf-8")
            print(f"wrote {len(manifest['facts'])} facts to {a.out}; verify ok={verification['ok']} ({verification['passed']} checks, {verification['failures']} fail)")
        else:
            print(output)
        if not verification["ok"]: raise SystemExit(1)
        return
    if a.cmd=="read":
        import tempfile
        from .verification import ManifestVerifier
        company=CompanyRegistry.from_json(a.registry).resolve(a.market,a.symbol)
        kwargs={"market":a.market,"symbol":a.symbol,"currency":company.currency,
                "source_url":a.source_url,"filed_at":a.filed_at,"period_end":a.period_end,
                "fiscal_year":a.fiscal_year,"filing_type":a.filing_type,
                "profile":a.profile or _company_profile(company)}
        def verify_manifest(manifest):
            with tempfile.TemporaryDirectory() as directory:
                Path(directory,"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
                return ManifestVerifier(directory).verify()
        manifest=None; source="deterministic"
        if not a.llm_only:
            from .reading import StatementReader
            manifest=StatementReader(a.pdf).read(**kwargs)
            verification=verify_manifest(manifest)
            if not verification["ok"] and a.llm:
                manifest=None
        if manifest is None:
            from .reading_llm import llm_read
            manifest=llm_read(a.pdf,model=a.model,**kwargs); source=f"llm:{a.model}"
        verification=verify_manifest(manifest)
        manifest["verify"]={"ok":verification["ok"],"passed":verification["passed"],
                            "failures":verification["failures"],"source":source}
        output=json.dumps(manifest,indent=2,ensure_ascii=False)
        if a.out:
            Path(a.out).write_text(output,encoding="utf-8")
            print(f"wrote {len(manifest['facts'])} facts ({source}) to {a.out}; verify ok={verification['ok']}")
        else:
            print(output)
        if not verification["ok"]: raise SystemExit(1)
        return
    if a.cmd=="fetch":
        from .fetching import BrowserFetcher
        fetcher=BrowserFetcher(raw_dir=a.raw_dir,headless=not a.show)
        result=fetcher.discover(a.url) if a.discover else fetcher.fetch(a.url,a.market,a.symbol)
        print(json.dumps(result,indent=2,ensure_ascii=False)); return
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
                 "source_index":a.source_index,"source_limit":a.source_limit,"sa_manifest":a.sa_manifest,
                 "browser":a.browser,"llm":a.llm}
        result=_monitor_once(db,queue,payload); db.close(); print(json.dumps(result,indent=2)); return
    if a.cmd=="schedule":
        if a.mode=="ingest" and a.market=="SA" and not a.sa_manifest:
            p.error("--sa-manifest is required for scheduled Saudi ingestion")
        db=Database(a.db); reg=CompanyRegistry.from_json(a.registry); company=reg.resolve(a.market,a.symbol); db.register_company(company)
        payload={"market":a.market,"symbol":a.symbol,"registry":a.registry,"raw_dir":a.raw_dir,
                 "sa_manifest":a.sa_manifest,"source_index":a.source_index,"source_limit":a.source_limit,
                 "browser":a.browser,"llm":a.llm}
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
    if a.cmd=="export-supabase":
        from . import __version__
        from .export_supabase import SupabaseExporter, facts_to_sql
        registry=CompanyRegistry.from_json(a.registry)
        if a.all:
            targets=[(c.market.value,c.symbol) for c in registry.all() if c.enabled]
        elif a.market and a.symbol:
            targets=[(a.market,a.symbol)]
        else:
            p.error("give MARKET SYMBOL, or --all")
        if a.sql_out or a.dry_run:
            from datetime import datetime, timezone
            from .export_supabase import flatten_fact
            service=FinancialQueryService(a.db); rows=[]
            stamp=datetime.now(timezone.utc).isoformat()
            try:
                for market,symbol in targets:
                    company=registry.resolve(market,symbol); offset=0
                    while True:
                        page=service.facts(market,symbol,limit=2000,offset=offset)
                        rows.extend(flatten_fact(company,f,engine_version=__version__,synced_at=stamp) for f in page)
                        if len(page)<2000: break
                        offset+=2000
            finally:
                service.close()
            if a.sql_out:
                Path(a.sql_out).write_text(facts_to_sql(rows),encoding="utf-8")
                print(json.dumps({"sql_out":a.sql_out,"facts":len(rows),"companies":len(targets)},indent=2))
            else:
                print(json.dumps({"dry_run":True,"facts":len(rows),"companies":len(targets),"sample":rows[:3]},ensure_ascii=False,indent=2,default=str))
            return
        url=os.environ.get(a.url_env,"").strip(); key=os.environ.get(a.key_env,"").strip()
        if not url: p.error(f"{a.url_env} is required (or use --sql-out)")
        if not key: p.error(f"{a.key_env} is required (or use --sql-out)")
        exporter=SupabaseExporter(a.db,url,key,engine_version=__version__)
        results=[exporter.export(m,s,registry,prune=a.prune,batch=a.batch) for m,s in targets]
        print(json.dumps({"exported":results,"total_facts":sum(r["facts"] for r in results)},indent=2)); return
    if a.cmd=="exceptions":
        if bool(a.market) != bool(a.symbol): p.error("market and symbol must be supplied together")
        q=FinancialQueryService(a.db); print(json.dumps(q.exceptions(a.market,a.symbol,a.status,a.limit),indent=2)); q.close(); return
    if a.cmd=="resolve-exception":
        db=Database(a.db); result=db.resolve_exception(a.exception_id,a.resolution,a.assigned_to); db.close(); print(json.dumps(result,indent=2)); return
    if a.cmd=="resolve-source-exceptions":
        db=Database(a.db); result=db.resolve_source_exceptions(a.source_key,a.resolution,a.assigned_to); db.close(); print(json.dumps(result,indent=2)); return
    if a.cmd=="retry-source":
        db=Database(a.db); row=db.stored_source(a.source_key); reg=CompanyRegistry.combined(db.conn,a.registry); company=reg.get(row["company_id"])
        path=Path(row["local_path"] or "")
        if not path.is_file(): db.close(); raise FileNotFoundError(f"archived source is missing: {path}")
        document=SourceDocument(row["company_id"],company.market,row["source_url"],row["source_key"],row["filing_type"],row["filed_at"],path.read_bytes(),row["content_type"],json.loads(row["metadata_json"]))
        db.reopen_source_for_retry(a.source_key)
        result=Pipeline(db,a.raw_dir).run(company,StoredDocumentConnector(document)); db.close(); print(json.dumps(result,indent=2)); return
    if a.cmd=="facts":
        q=FinancialQueryService(a.db); print(json.dumps(q.facts(a.market,a.symbol,a.category,a.period_kind,a.limit),indent=2)); q.close(); return
    if a.cmd=="dossier":
        q=FinancialQueryService(a.db); payload=json.dumps(q.company_dossier(a.market,a.symbol),ensure_ascii=False,indent=2); q.close()
        if a.output:
            target=Path(a.output); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(payload+"\n",encoding="utf-8")
            print(f"created {target}")
        else: print(payload)
        return
    if a.cmd=="page":
        q=FinancialQueryService(a.db); payload=json.dumps(q.company_page(a.market,a.symbol),ensure_ascii=False,indent=2); q.close()
        if a.output:
            target=Path(a.output); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(payload+"\n",encoding="utf-8")
            print(f"created {target}")
        else: print(payload)
        return
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
