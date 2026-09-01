from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from .database import Database, _json


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


@dataclass(frozen=True)
class ClaimedJob:
    job_id: str
    job_type: str
    company_id: str | None
    source_key: str | None
    payload: dict
    attempts: int
    max_attempts: int
    leased_by: str


class DurableJobQueue:
    """SQLite-backed queue with idempotency, leases, retries and an audit trail."""

    def __init__(self, db: Database):
        self.db = db

    def enqueue(
        self, job_type: str, payload: dict | None = None, company_id: str | None = None,
        source_key: str | None = None, idempotency_key: str | None = None,
        priority: int = 100, available_at: datetime | None = None, max_attempts: int = 5,
    ) -> tuple[str, bool]:
        job_id = str(uuid.uuid4())
        key = idempotency_key or f"manual:{job_type}:{job_id}"
        available = _iso(available_at or _now())
        with self.db.conn:
            existing = self.db.conn.execute(
                "SELECT job_id FROM jobs WHERE idempotency_key=?", (key,)
            ).fetchone()
            if existing:
                return existing["job_id"], False
            self.db.conn.execute(
                """INSERT INTO jobs(job_id,job_type,company_id,source_key,payload_json,priority,
                available_at,max_attempts,idempotency_key) VALUES(?,?,?,?,?,?,?,?,?)""",
                (job_id, job_type, company_id, source_key, _json(payload or {}), priority,
                 available, max_attempts, key),
            )
        return job_id, True

    def _recover_expired(self, now: str) -> None:
        expired = self.db.conn.execute(
            "SELECT job_id,attempts,max_attempts FROM jobs WHERE status='running' AND lease_until<?", (now,)
        ).fetchall()
        for row in expired:
            status = "dead" if row["attempts"] >= row["max_attempts"] else "queued"
            self.db.conn.execute(
                """UPDATE jobs SET status=?,available_at=?,leased_by=NULL,lease_until=NULL,
                last_error='worker lease expired',updated_at=? WHERE job_id=?""",
                (status, now, now, row["job_id"]),
            )
            self.db.conn.execute(
                """UPDATE job_attempts SET status='expired',finished_at=?,error='worker lease expired'
                WHERE job_id=? AND attempt_number=? AND finished_at IS NULL""",
                (now, row["job_id"], row["attempts"]),
            )

    def claim(
        self, worker_id: str, job_types: tuple[str, ...] | None = None, lease_seconds: int = 300,
    ) -> ClaimedJob | None:
        now_dt = _now(); now = _iso(now_dt); lease_until = _iso(now_dt + timedelta(seconds=lease_seconds))
        conn = self.db.conn
        try:
            conn.execute("BEGIN IMMEDIATE")
            self._recover_expired(now)
            args: list = [now]
            type_filter = ""
            if job_types:
                type_filter = " AND job_type IN (" + ",".join("?" for _ in job_types) + ")"
                args.extend(job_types)
            row = conn.execute(
                """SELECT * FROM jobs WHERE status='queued' AND available_at<=?""" + type_filter +
                " ORDER BY priority ASC,created_at ASC LIMIT 1", args,
            ).fetchone()
            if not row:
                conn.commit(); return None
            attempt = row["attempts"] + 1
            conn.execute(
                """UPDATE jobs SET status='running',attempts=?,leased_by=?,lease_until=?,updated_at=?
                WHERE job_id=? AND status='queued'""",
                (attempt, worker_id, lease_until, now, row["job_id"]),
            )
            conn.execute(
                "INSERT INTO job_attempts(job_id,attempt_number,worker_id,started_at,status) VALUES(?,?,?,?,?)",
                (row["job_id"], attempt, worker_id, now, "running"),
            )
            conn.commit()
        except Exception:
            conn.rollback(); raise
        return ClaimedJob(
            row["job_id"], row["job_type"], row["company_id"], row["source_key"],
            json.loads(row["payload_json"]), attempt, row["max_attempts"], worker_id,
        )

    def complete(self, job: ClaimedJob, result: dict | None = None) -> None:
        now = _iso(_now())
        with self.db.conn:
            updated = self.db.conn.execute(
                """UPDATE jobs SET status='succeeded',result_json=?,leased_by=NULL,lease_until=NULL,
                updated_at=?,finished_at=? WHERE job_id=? AND status='running' AND leased_by=?""",
                (_json(result or {}), now, now, job.job_id, job.leased_by),
            )
            if updated.rowcount != 1:
                raise RuntimeError("job lease is no longer owned by this worker")
            self.db.conn.execute(
                """UPDATE job_attempts SET status='succeeded',finished_at=?
                WHERE job_id=? AND attempt_number=?""", (now, job.job_id, job.attempts),
            )

    def fail(self, job: ClaimedJob, error: Exception | str, base_backoff_seconds: int = 30) -> str:
        now_dt = _now(); now = _iso(now_dt)
        terminal = job.attempts >= job.max_attempts
        status = "dead" if terminal else "queued"
        delay = min(3600, base_backoff_seconds * (2 ** max(job.attempts - 1, 0)))
        available = _iso(now_dt + timedelta(seconds=delay))
        message = str(error)[:4000]
        with self.db.conn:
            updated = self.db.conn.execute(
                """UPDATE jobs SET status=?,available_at=?,last_error=?,leased_by=NULL,lease_until=NULL,
                updated_at=?,finished_at=? WHERE job_id=? AND status='running' AND leased_by=?""",
                (status, available, message, now, now if terminal else None, job.job_id, job.leased_by),
            )
            if updated.rowcount != 1:
                raise RuntimeError("job lease is no longer owned by this worker")
            self.db.conn.execute(
                """UPDATE job_attempts SET status=?,finished_at=?,error=?
                WHERE job_id=? AND attempt_number=?""",
                ("dead" if terminal else "failed", now, message, job.job_id, job.attempts),
            )
        return status

    def heartbeat(self, worker_id: str, job: ClaimedJob | None = None, lease_seconds: int = 300) -> None:
        now_dt = _now(); now = _iso(now_dt)
        with self.db.conn:
            self.db.conn.execute(
                """INSERT INTO workers(worker_id,started_at,heartbeat_at,status) VALUES(?,?,?,'online')
                ON CONFLICT(worker_id) DO UPDATE SET heartbeat_at=excluded.heartbeat_at,status='online'""",
                (worker_id, now, now),
            )
            if job:
                result = self.db.conn.execute(
                    """UPDATE jobs SET lease_until=?,updated_at=?
                    WHERE job_id=? AND status='running' AND leased_by=?""",
                    (_iso(now_dt + timedelta(seconds=lease_seconds)), now, job.job_id, worker_id),
                )
                if result.rowcount != 1:
                    raise RuntimeError("cannot extend a lease owned by another worker")


class DurableScheduler:
    def __init__(self, db: Database, queue: DurableJobQueue | None = None):
        self.db = db
        self.queue = queue or DurableJobQueue(db)

    def upsert(
        self, schedule_id: str, name: str, job_type: str, interval_seconds: int,
        payload: dict | None = None, company_id: str | None = None, priority: int = 100,
        next_run_at: datetime | None = None, enabled: bool = True,
    ) -> None:
        if interval_seconds < 60:
            raise ValueError("interval_seconds must be at least 60")
        with self.db.conn:
            self.db.conn.execute(
                """INSERT INTO schedules(schedule_id,name,job_type,company_id,payload_json,interval_seconds,
                priority,next_run_at,enabled) VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(schedule_id) DO UPDATE SET name=excluded.name,job_type=excluded.job_type,
                company_id=excluded.company_id,payload_json=excluded.payload_json,
                interval_seconds=excluded.interval_seconds,priority=excluded.priority,enabled=excluded.enabled,
                updated_at=CURRENT_TIMESTAMP""",
                (schedule_id, name, job_type, company_id, _json(payload or {}), interval_seconds,
                 priority, _iso(next_run_at or _now()), int(enabled)),
            )

    def tick(self, now: datetime | None = None) -> list[str]:
        now_dt = now or _now(); now_text = _iso(now_dt); created = []
        due = self.db.conn.execute(
            "SELECT * FROM schedules WHERE enabled=1 AND next_run_at<=? ORDER BY next_run_at", (now_text,)
        ).fetchall()
        for row in due:
            key = f"schedule:{row['schedule_id']}:{row['next_run_at']}"
            job_id, was_created = self.queue.enqueue(
                row["job_type"], json.loads(row["payload_json"]), row["company_id"],
                idempotency_key=key, priority=row["priority"],
            )
            next_run = _iso(now_dt + timedelta(seconds=row["interval_seconds"]))
            with self.db.conn:
                self.db.conn.execute(
                    "UPDATE schedules SET next_run_at=?,updated_at=? WHERE schedule_id=?",
                    (next_run, now_text, row["schedule_id"]),
                )
            if was_created:
                created.append(job_id)
        return created


class Worker:
    def __init__(self, queue: DurableJobQueue, worker_id: str,
                 handlers: dict[str, Callable[[ClaimedJob], dict | None]], lease_seconds: int = 300):
        self.queue = queue; self.worker_id = worker_id; self.handlers = handlers; self.lease_seconds = lease_seconds

    def run_once(self) -> bool:
        self.queue.heartbeat(self.worker_id)
        job = self.queue.claim(self.worker_id, tuple(self.handlers), self.lease_seconds)
        if not job:
            return False
        try:
            result = self.handlers[job.job_type](job)
            self.queue.complete(job, result)
        except Exception as error:
            self.queue.fail(job, error)
        return True

    def serve(self, poll_seconds: int = 10) -> None:
        try:
            while True:
                if not self.run_once():
                    time.sleep(max(1, min(poll_seconds, 30)))
        finally:
            now = _iso(_now())
            with self.queue.db.conn:
                self.queue.db.conn.execute(
                    "UPDATE workers SET status='offline',heartbeat_at=? WHERE worker_id=?", (now, self.worker_id))
