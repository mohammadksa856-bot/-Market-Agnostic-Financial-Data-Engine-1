from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .database import Database
from .jobs import DurableJobQueue
from .models import Company, Market, SourceDocument


class MonitorService:
    """Persist discovery cursors and turn only new candidates into durable jobs."""

    def __init__(self, db: Database, queue: DurableJobQueue | None = None):
        self.db = db
        self.queue = queue or DurableJobQueue(db)

    def poll(self, company: Company, monitor, job_type: str | None = None,
             job_payload: dict | None = None, enqueue_per_candidate: bool = False) -> dict:
        self.db.register_company(company)
        state = self.db.get_monitor_state(company.company_id, monitor.name)
        try:
            result = monitor.discover(company, state.get("cursor"))
            created_candidates: list[int] = []
            for candidate in result.candidates:
                candidate_id, created = self.db.save_source_candidate(candidate)
                if created:
                    created_candidates.append(candidate_id)
            jobs: list[str] = []
            if job_type and created_candidates:
                if enqueue_per_candidate:
                    for candidate_id in created_candidates:
                        payload = dict(job_payload or {})
                        payload["candidate_id"] = candidate_id
                        job_id, created = self.queue.enqueue(
                            job_type, payload, company.company_id,
                            idempotency_key=f"candidate:{candidate_id}:{job_type}",
                        )
                        if created:
                            jobs.append(job_id)
                            self.db.set_source_candidate_status(candidate_id, "queued")
                else:
                    payload = dict(job_payload or {})
                    payload["candidate_ids"] = created_candidates
                    job_id, created = self.queue.enqueue(
                        job_type, payload, company.company_id,
                        idempotency_key=(
                            f"monitor:{company.company_id}:{monitor.name}:{result.cursor}:{job_type}"
                        ),
                    )
                    if created:
                        jobs.append(job_id)
                        for candidate_id in created_candidates:
                            self.db.set_source_candidate_status(candidate_id, "queued")
            self.db.mark_monitor_success(company.company_id, monitor.name, result.cursor)
            return {
                "company_id": company.company_id,
                "connector": monitor.name,
                "cursor": result.cursor,
                "discovered": len(result.candidates),
                "new_candidates": len(created_candidates),
                "queued_jobs": len(jobs),
                "job_ids": jobs,
            }
        except Exception as error:
            self.db.mark_monitor_failure(company.company_id, monitor.name, str(error))
            raise


class DocumentArchiver:
    """Download a discovered document into immutable staging; never publish facts."""

    EXTENSIONS = {
        "application/pdf": ".pdf",
        "text/html": ".html",
        "application/xhtml+xml": ".html",
        "application/json": ".json",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    }

    def __init__(self, db: Database, raw_dir: str | Path, opener=urlopen,
                 max_bytes: int = 100 * 1024 * 1024,
                 user_agent: str = "MarketAgnosticFinancialDataEngine/0.6",
                 content_fetcher=None):
        self.db = db
        self.raw_dir = Path(raw_dir)
        self.opener = opener
        self.max_bytes = max_bytes
        self.user_agent = user_agent
        # Optional url -> bytes override, e.g. BrowserFetcher.download_bytes,
        # for sites a plain urllib request can't pass bot protection on.
        self.content_fetcher = content_fetcher

    def fetch(self, candidate_id: int) -> dict:
        candidate = self.db.get_source_candidate(candidate_id)
        if candidate["status"] == "fetched":
            return {"status": "duplicate", "candidate_id": candidate_id}
        if self.content_fetcher is not None:
            content = self.content_fetcher(candidate["source_url"])
        else:
            request = Request(candidate["source_url"], headers={"User-Agent": self.user_agent})
            chunks = []
            total = 0
            with self.opener(request, timeout=60) as response:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > self.max_bytes:
                        raise ValueError(f"document exceeded {self.max_bytes} bytes")
                    chunks.append(chunk)
            content = b"".join(chunks)
        total = len(content)
        if total > self.max_bytes:
            raise ValueError(f"document exceeded {self.max_bytes} bytes")
        if not content:
            raise ValueError("downloaded document was empty")
        digest = hashlib.sha256(content).hexdigest()
        source_key = f"document:{candidate['company_id']}:{digest}"
        content_type = candidate["content_type"] or "application/octet-stream"
        extension = self.EXTENSIONS.get(content_type)
        if not extension:
            suffix = Path(urlparse(candidate["source_url"]).path).suffix.lower()
            extension = suffix if suffix in {".pdf", ".html", ".json", ".xlsx"} else ".bin"
        company = self.db.conn.execute(
            "SELECT market,symbol FROM companies WHERE company_id=?", (candidate["company_id"],)
        ).fetchone()
        target = (
            self.raw_dir / company["market"] / company["symbol"] / "documents" /
            f"{digest}{extension}"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = target.with_suffix(target.suffix + ".part")
            temporary.write_bytes(content)
            temporary.replace(target)
        filed_at = candidate["published_at"] or date.today().isoformat()
        document = SourceDocument(
            candidate["company_id"], Market(company["market"]), candidate["source_url"], source_key,
            candidate["document_type"], filed_at, content, content_type,
            {"candidate_id": candidate_id, "title": candidate["title"],
             "connector": candidate["connector"]},
        )
        previous_status = self.db.source_status(source_key)
        if previous_status is None:
            self.db.save_source(document, digest, str(target))
            self.db.set_source_status(source_key, "awaiting_extraction")
        self.db.set_source_candidate_status(candidate_id, "fetched")
        return {
            "status": "archived" if previous_status is None else "duplicate",
            "candidate_id": candidate_id,
            "source_key": source_key,
            "content_type": content_type,
            "bytes": total,
            "local_path": str(target),
            "next_stage": "extraction",
        }
