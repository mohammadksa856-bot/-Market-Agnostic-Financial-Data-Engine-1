import json
import tempfile
import unittest
from pathlib import Path

from finengine.connectors import IssuerReportsMonitor, SecFilingsMonitor
from finengine.database import Database
from finengine.jobs import DurableJobQueue
from finengine.models import Company, Market, SourceCandidate
from finengine.monitoring import DocumentArchiver, MonitorService


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content
        self.position = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, size=-1):
        if size is None or size < 0:
            result = self.content[self.position:]
            self.position = len(self.content)
            return result
        result = self.content[self.position:self.position + size]
        self.position += len(result)
        return result


def opener_for(content: bytes):
    return lambda request, timeout=0: FakeResponse(content)


class MonitoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "db.sqlite3")
        self.aramco = Company(
            "sa:2222", Market.SA, "2222", "Aramco", "SAR",
            sources=("https://www.aramco.com/en/investors/reports-and-presentations",),
        )
        self.db.register_company(self.aramco)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_issuer_monitor_discovers_only_official_financial_documents(self):
        html = b"""
        <a href='/media/q2-interim-report.pdf'><span>Q2 interim report</span></a>
        <a href='/media/aramco-databook.xlsx'>Aramco Databook</a>
        <a href='https://evil.example/annual-report.pdf'>Annual report mirror</a>
        <a href='/media/photo.jpg'>Annual report cover</a>
        """
        monitor = IssuerReportsMonitor(
            self.aramco.sources[0], opener=opener_for(html), max_documents=20,
        )
        first = monitor.discover(self.aramco)
        self.assertEqual(len(first.candidates), 2)
        self.assertEqual(first.candidates[0].document_type, "interim-report")
        self.assertEqual(first.candidates[1].content_type,
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertEqual(monitor.discover(self.aramco, first.cursor).candidates, ())

    def test_sec_monitor_uses_accession_cursor_and_financial_forms(self):
        payload = {"filings": {"recent": {
            "accessionNumber": ["0003", "0002", "0001"],
            "form": ["10-Q", "8-K", "10-K"],
            "filingDate": ["2026-08-01", "2026-07-01", "2026-02-01"],
            "reportDate": ["2026-06-30", "", "2025-12-31"],
            "primaryDocument": ["q2.htm", "event.htm", "fy.htm"],
            "primaryDocDescription": ["Q2 report", "Event", "Annual report"],
        }}}
        company = Company("us:TST", Market.US, "TST", "Test", "USD", cik="0000000123")
        monitor = SecFilingsMonitor("test test@example.com", opener=opener_for(json.dumps(payload).encode()))
        initial = monitor.discover(company)
        self.assertEqual([item.external_id for item in initial.candidates], ["0003", "0001"])
        self.assertIn("/123/0003/q2.htm", initial.candidates[0].source_url)
        changed = monitor.discover(company, "0001")
        self.assertEqual([item.external_id for item in changed.candidates], ["0003"])

    def test_monitor_service_is_cursor_and_job_idempotent(self):
        html = b"<a href='/media/annual-report.pdf'>Annual report 2025</a>"
        monitor = IssuerReportsMonitor(self.aramco.sources[0], opener=opener_for(html))
        service = MonitorService(self.db, DurableJobQueue(self.db))
        first = service.poll(
            self.aramco, monitor, "fetch_document", {"raw_dir": self.temp.name}, True,
        )
        second = service.poll(
            self.aramco, monitor, "fetch_document", {"raw_dir": self.temp.name}, True,
        )
        self.assertEqual((first["new_candidates"], first["queued_jobs"]), (1, 1))
        self.assertEqual((second["new_candidates"], second["queued_jobs"]), (0, 0))
        row = self.db.conn.execute("SELECT status FROM source_candidates").fetchone()
        self.assertEqual(row["status"], "queued")
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)

    def test_bulk_monitor_job_tracks_every_candidate(self):
        html = b"""
        <a href='/media/q1-interim-report.pdf'>Q1 interim report</a>
        <a href='/media/q2-interim-report.pdf'>Q2 interim report</a>
        """
        monitor = IssuerReportsMonitor(self.aramco.sources[0], opener=opener_for(html))
        result = MonitorService(self.db).poll(
            self.aramco, monitor, "ingest", {"market": "SA", "symbol": "2222"}, False,
        )
        self.assertEqual(result["queued_jobs"], 1)
        job = self.db.conn.execute("SELECT payload_json FROM jobs").fetchone()
        payload = json.loads(job["payload_json"])
        self.assertEqual(len(payload["candidate_ids"]), 2)
        statuses = self.db.conn.execute(
            "SELECT DISTINCT status FROM source_candidates"
        ).fetchall()
        self.assertEqual([row["status"] for row in statuses], ["queued"])

    def test_document_archiver_stages_binary_without_publishing(self):
        candidate = SourceCandidate(
            self.aramco.company_id, "issuer-reports", "report-1",
            "https://www.aramco.com/media/report.pdf", "Annual report 2025",
            "annual-report", "2026-03-10", "application/pdf",
        )
        candidate_id, _ = self.db.save_source_candidate(candidate)
        result = DocumentArchiver(
            self.db, Path(self.temp.name) / "raw", opener=opener_for(b"%PDF-test"),
        ).fetch(candidate_id)
        self.assertEqual(result["status"], "archived")
        self.assertTrue(Path(result["local_path"]).is_file())
        self.assertEqual(self.db.source_status(result["source_key"]), "awaiting_extraction")
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM data_points").fetchone()[0], 0)
        self.assertEqual(self.db.get_source_candidate(candidate_id)["status"], "fetched")


if __name__ == "__main__":
    unittest.main()
