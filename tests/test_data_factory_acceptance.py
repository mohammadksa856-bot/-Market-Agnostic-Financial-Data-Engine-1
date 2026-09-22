import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from finengine.database import Database
from finengine.factory import FactoryOrchestrator
from finengine.jobs import DurableJobQueue, JobLeaseLost
from finengine.models import Company, Market
from finengine.operations import configure_production_schedules


class DataFactoryAcceptanceTests(unittest.TestCase):
    """Durability contracts required by the unattended data factory."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "factory.sqlite3"
        Database(self.db_path).close()

    def tearDown(self):
        self.temp.cleanup()

    def _registry(self) -> Path:
        path = self.root / "companies.json"
        path.write_text(json.dumps([{
            "company_id": "sa:TST",
            "market": "SA",
            "symbol": "TST",
            "name": "Test Company",
            "currency": "SAR",
            "sector": "Telecommunication Services",
            "sources": ["https://issuer.example.test/investors"],
        }]), encoding="utf-8")
        return path

    def test_production_is_deterministic_by_default_and_llm_requires_opt_in(self):
        registry = self._registry()
        configure_production_schedules(self.db_path, registry)
        db = Database(self.db_path)
        try:
            schedules = db.conn.execute(
                "SELECT schedule_id,payload_json FROM schedules WHERE enabled=1"
            ).fetchall()
        finally:
            db.close()

        by_id = {row["schedule_id"]: json.loads(row["payload_json"])
                 for row in schedules}
        self.assertFalse(by_id["monitor:SA:TST"]["llm"])
        self.assertNotIn("profile-scan", by_id)

        configure_production_schedules(self.db_path, registry, use_llm=True)
        db = Database(self.db_path)
        try:
            schedules = db.conn.execute(
                "SELECT schedule_id,payload_json FROM schedules WHERE enabled=1"
            ).fetchall()
        finally:
            db.close()
        by_id = {row["schedule_id"]: json.loads(row["payload_json"])
                 for row in schedules}
        self.assertTrue(by_id["monitor:SA:TST"]["llm"])
        self.assertIn("profile-scan", by_id)

    def test_failure_retries_then_dead_letters_with_complete_attempt_ledger(self):
        db = Database(self.db_path)
        try:
            queue = DurableJobQueue(db)
            job_id, _ = queue.enqueue(
                "extract_document", {"source_key": "document:test"},
                idempotency_key="extract:document:test", max_attempts=3,
            )
            expected = ["queued", "queued", "dead"]
            for attempt, expected_status in enumerate(expected, 1):
                job = queue.claim(f"worker-{attempt}")
                self.assertIsNotNone(job)
                self.assertEqual(queue.fail(job, f"failure-{attempt}", 0), expected_status)

            row = db.conn.execute(
                "SELECT status,attempts,last_error,leased_by,lease_until FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            self.assertEqual((row["status"], row["attempts"], row["last_error"]),
                             ("dead", 3, "failure-3"))
            self.assertIsNone(row["leased_by"])
            self.assertIsNone(row["lease_until"])
            ledger = db.conn.execute(
                "SELECT attempt_number,worker_id,status,error FROM job_attempts "
                "WHERE job_id=? ORDER BY attempt_number", (job_id,),
            ).fetchall()
            self.assertEqual(
                [(r["attempt_number"], r["worker_id"], r["status"], r["error"])
                 for r in ledger],
                [(1, "worker-1", "failed", "failure-1"),
                 (2, "worker-2", "failed", "failure-2"),
                 (3, "worker-3", "dead", "failure-3")],
            )
        finally:
            db.close()

    def test_expired_lease_is_reassigned_and_stale_worker_is_fenced(self):
        db = Database(self.db_path)
        queue = DurableJobQueue(db)
        job_id, _ = queue.enqueue(
            "extract_document", {}, idempotency_key="lease:fencing", max_attempts=3,
        )
        stale = queue.claim("stale-worker", lease_seconds=60)
        with db.conn:
            db.conn.execute(
                "UPDATE jobs SET lease_until=? WHERE job_id=?",
                ((datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat(), job_id),
            )
        replacement = queue.claim("replacement-worker", lease_seconds=60)
        self.assertIsNotNone(replacement)
        self.assertEqual(replacement.attempts, 2)
        with self.assertRaises(JobLeaseLost):
            queue.complete(stale, {"stale": True})
        queue.complete(replacement, {"published": True})
        row = db.conn.execute(
            "SELECT status,result_json,attempts FROM jobs WHERE job_id=?", (job_id,),
        ).fetchone()
        self.assertEqual((row["status"], row["attempts"]), ("succeeded", 2))
        self.assertEqual(json.loads(row["result_json"]), {"published": True})
        ledger = db.conn.execute(
            "SELECT status FROM job_attempts WHERE job_id=? ORDER BY attempt_number",
            (job_id,),
        ).fetchall()
        self.assertEqual([r["status"] for r in ledger], ["expired", "succeeded"])
        db.close()

    def test_concurrent_enqueue_with_same_key_creates_exactly_one_job(self):
        workers = 8
        barrier = threading.Barrier(workers)
        lock = threading.Lock()
        results = []
        errors = []

        def enqueue(worker_number: int) -> None:
            db = Database(self.db_path)
            try:
                barrier.wait(timeout=5)
                result = DurableJobQueue(db).enqueue(
                    "extract_document", {"worker": worker_number},
                    idempotency_key="extract:shared-source",
                )
                with lock:
                    results.append(result)
            except Exception as error:  # acceptance assertion reports all races
                with lock:
                    errors.append(error)
            finally:
                db.close()

        threads = [threading.Thread(target=enqueue, args=(index,))
                   for index in range(workers)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertEqual(errors, [])
        self.assertEqual(len(results), workers)
        self.assertEqual(sum(created for _, created in results), 1)
        self.assertEqual(len({job_id for job_id, _ in results}), 1)
        db = Database(self.db_path)
        try:
            self.assertEqual(db.conn.execute(
                "SELECT count(*) FROM jobs WHERE idempotency_key='extract:shared-source'"
            ).fetchone()[0], 1)
        finally:
            db.close()

    def test_factory_plan_materializes_all_18_categories_once(self):
        db = Database(self.db_path)
        try:
            db.register_company(Company(
                "sa:TST", Market.SA, "TST", "Test Company", "SAR",
                sector="Telecommunication Services",
            ))
            factory = FactoryOrchestrator(db)
            planned = factory.plan(market="SA", symbols=["TST"])
            self.assertEqual((planned["companies"], planned["categories"], planned["total_items"]),
                             (1, 18, 18))
            self.assertEqual(db.conn.execute(
                "SELECT count(DISTINCT category_key) FROM factory_work_items WHERE run_id=?",
                (planned["run_id"],),
            ).fetchone()[0], 18)
        finally:
            db.close()

    def test_factory_dispatch_coalesces_categories_and_never_enables_llm(self):
        db = Database(self.db_path)
        try:
            db.register_company(Company(
                "sa:TST", Market.SA, "TST", "Test Company", "SAR",
                sector="Telecommunication Services",
                sources=("https://issuer.example.test/investors",),
            ))
            factory = FactoryOrchestrator(db)
            run_id = factory.plan(market="SA", symbols=["TST"])["run_id"]
            result = factory.dispatch(run_id, limit=10)
            self.assertLessEqual(result["dispatched_jobs"], 3)
            jobs = db.conn.execute(
                "SELECT job_type,payload_json FROM jobs ORDER BY job_type"
            ).fetchall()
            monitor = [json.loads(row["payload_json"]) for row in jobs
                       if row["job_type"] == "monitor"]
            self.assertEqual(len(monitor), 1)
            self.assertFalse(monitor[0]["llm"])
            self.assertEqual(db.conn.execute(
                "SELECT count(*) FROM factory_work_items WHERE run_id=? AND category_key='analysts' "
                "AND state='blocked'", (run_id,),
            ).fetchone()[0], 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
