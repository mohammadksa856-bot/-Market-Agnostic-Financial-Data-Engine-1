import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from finengine.calculations import Calculator
from finengine.database import Database
from finengine.jobs import DurableJobQueue, DurableScheduler
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument
from finengine.query import FinancialQueryService


class StorageAndJobsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "financial.sqlite3")
        self.db = Database(self.path)
        self.company = Company("sa:TST", Market.SA, "TST", "Test Company", "SAR")
        self.db.register_company(self.company)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def source(self, key="source:1"):
        doc = SourceDocument(self.company.company_id, self.company.market, "https://example.test/report",
                             key, "financial-results", "2026-01-01", b"{}")
        self.db.save_source(doc, key.replace(":", ""), None)
        return doc

    def fact(self, source, value, period_end="2025-12-31", kind=PeriodKind.FY,
             quarter=None, dimensions=None):
        return Fact(self.company.company_id, "revenue", Decimal(value), "SAR", "SAR", "2025-01-01",
                    period_end, kind, 2025, quarter, source.source_key, source.source_url,
                    source.filed_at, dimensions=dimensions or {})

    def test_dimensions_allow_multiple_segments_for_same_metric(self):
        source = self.source()
        states = self.db.publish_batch([
            self.fact(source, "60", dimensions={"segment": "upstream"}),
            self.fact(source, "40", dimensions={"segment": "downstream"}),
        ])
        self.assertEqual(states, ["inserted", "inserted"])
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM data_points").fetchone()[0], 2)

    def test_snapshot_never_overwrites_quarter_with_ytd(self):
        source = self.source()
        self.db.publish_batch([
            self.fact(source, "25", kind=PeriodKind.QUARTER, quarter=2),
            self.fact(source, "45", kind=PeriodKind.YTD, quarter=2),
        ])
        query = FinancialQueryService(self.path)
        snapshot = query.snapshot("SA", "TST")
        query.close()
        self.assertEqual({row["period_kind"] for row in snapshot["metrics"]["revenue"]}, {"quarter", "ytd"})

    def test_company_attributes_and_disclosures_are_versioned(self):
        self.assertEqual(self.db.publish_company_attribute("sa:TST", "employee_count", 100, "2025-12-31"), "inserted")
        self.assertEqual(self.db.publish_company_attribute("sa:TST", "employee_count", 110, "2026-12-31"), "restated")
        self.assertEqual(self.db.publish_disclosure("sa:TST", "strategy", "Strategy", "First", "2026-01-01"), "inserted")
        self.assertEqual(self.db.publish_disclosure("sa:TST", "strategy", "Strategy", "Updated", "2026-02-01"), "restated")
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM company_attributes WHERE is_current=1").fetchone()[0], 1)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM disclosures WHERE is_current=1").fetchone()[0], 1)

    def test_job_queue_is_idempotent_and_audited(self):
        queue = DurableJobQueue(self.db)
        first, created = queue.enqueue("ingest", {"market": "SA"}, "sa:TST", idempotency_key="ingest:1")
        second, duplicate = queue.enqueue("ingest", {"market": "SA"}, "sa:TST", idempotency_key="ingest:1")
        self.assertTrue(created); self.assertFalse(duplicate); self.assertEqual(first, second)
        job = queue.claim("worker-1")
        self.assertIsNotNone(job)
        queue.complete(job, {"status": "published"})
        row = self.db.conn.execute("SELECT status,attempts FROM jobs WHERE job_id=?", (first,)).fetchone()
        self.assertEqual((row["status"], row["attempts"]), ("succeeded", 1))
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM job_attempts").fetchone()[0], 1)

    def test_scheduler_materializes_only_one_due_job(self):
        queue = DurableJobQueue(self.db); scheduler = DurableScheduler(self.db, queue)
        due = datetime(2026, 1, 1, tzinfo=timezone.utc)
        scheduler.upsert("daily:TST", "Daily Test", "ingest", 3600, {"symbol": "TST"}, "sa:TST", next_run_at=due)
        self.assertEqual(len(scheduler.tick(due)), 1)
        self.assertEqual(len(scheduler.tick(due)), 0)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)

    def test_ttm_uses_published_history(self):
        for index, (end, value) in enumerate((("2025-03-31", "10"), ("2025-06-30", "20"), ("2025-09-30", "30")), 1):
            source = self.source(f"source:{index}")
            self.db.publish(self.fact(source, value, end, PeriodKind.QUARTER, index))
        current_source = self.source("source:4")
        current = self.fact(current_source, "40", "2025-12-31", PeriodKind.QUARTER, 4)
        history = self.db.quarter_history("sa:TST", Calculator.TTM_FLOWS)
        calculated = Calculator().calculate([current], history)
        ttm = next(f for f in calculated if f.metric == "revenue_ttm")
        self.assertEqual(ttm.value, Decimal("100"))

    def test_ttm_keeps_dimensions_isolated(self):
        source = self.source()
        facts = []
        periods = (
            ("2025-03-31", 1), ("2025-06-30", 2),
            ("2025-09-30", 3), ("2025-12-31", 4),
        )
        for end, quarter in periods:
            facts.extend([
                self.fact(source, "10", end, PeriodKind.QUARTER, quarter,
                          {"segment": "upstream"}),
                self.fact(source, "100", end, PeriodKind.QUARTER, quarter,
                          {"segment": "downstream"}),
            ])
        ttm = [fact for fact in Calculator().calculate(facts) if fact.metric == "revenue_ttm"]
        values = {fact.dimensions["segment"]: fact.value for fact in ttm}
        self.assertEqual(values, {"upstream": Decimal("40"), "downstream": Decimal("400")})


if __name__ == "__main__":
    unittest.main()
