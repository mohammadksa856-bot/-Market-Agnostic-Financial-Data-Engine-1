import json
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from finengine.connectors import IssuerReportsMonitor, SecFilingsMonitor
from finengine.cli import _extract_document_job_handler, _monitor_once, _source_period
from finengine.database import Database
from finengine.jobs import DurableJobQueue
from finengine.models import Company, DiscoveryResult, Market, SourceCandidate
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

    def test_issuer_monitor_uses_list_item_context_for_icon_only_downloads(self):
        html = b"""
        <ul><li><div><h6>30 June 2026</h6>Consolidated Financial Statement</div>
        <div><a href='/media/acwa-q2-2026-english-fs.pdf'>&nbsp;<i></i></a></div></li></ul>
        """
        monitor = IssuerReportsMonitor(
            self.aramco.sources[0], opener=opener_for(html), max_documents=20,
        )
        result = monitor.discover(self.aramco)
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].title,
                         "30 June 2026 Consolidated Financial Statement")
        self.assertEqual(result.candidates[0].document_type, "interim-report")

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

    def test_monitor_job_falls_back_across_registered_official_sources(self):
        fallback = "https://www.saudiexchange.sa/company/2222"
        with self.db.conn:
            self.db.conn.execute(
                "INSERT INTO company_sources(company_id,source_type,url,priority) "
                "VALUES(?,?,?,?)", (self.aramco.company_id, "exchange", fallback, 200),
            )

        class FakeMonitor:
            name = "browser-issuer-reports"
            def __init__(self, index_url, **_kwargs):
                self.index_url = index_url
            def discover(self, _company, _cursor=None):
                if self.index_url != fallback:
                    raise RuntimeError("endpoint unavailable")
                return DiscoveryResult("fallback-cursor", ())

        payload = {
            "market": "SA", "symbol": "2222", "browser": True,
            "source_index": "https://unreachable.example/investors",
            "registry": str(Path(self.temp.name) / "missing.json"),
            "raw_dir": str(Path(self.temp.name) / "raw"),
        }
        with patch("finengine.fetching.BrowserFetcher"), patch(
            "finengine.fetching.BrowserIssuerMonitor", FakeMonitor
        ):
            result = _monitor_once(self.db, DurableJobQueue(self.db), payload)
        self.assertEqual(result["source_index"], fallback)
        self.assertEqual(result["attempted_sources"], 3)
        self.assertEqual(len(result["fallback_errors"]), 2)

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

        queue=DurableJobQueue(self.db)
        registry=Path(__file__).resolve().parents[1]/"config"/"companies.json"
        queue.enqueue("extract_document",{"source_key":result["source_key"],"registry":str(registry)},
                      self.aramco.company_id,result["source_key"],"extract:test")
        job=queue.claim("extractor",("extract_document",))
        extraction=_extract_document_job_handler(self.db)(job); queue.complete(job,extraction)
        self.assertEqual(extraction["status"],"review_required")
        self.assertEqual(self.db.source_status(result["source_key"]),"review_required")
        backlog=self.db.conn.execute("SELECT status,item_type FROM backlog_items").fetchone()
        self.assertEqual((backlog["status"],backlog["item_type"]),("ready","document_extraction"))
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM data_points").fetchone()[0],0)

    def test_candidate_fetcher_receives_referer_provenance(self):
        referer = "https://www.saudiexchange.sa/announcements/details/?anId=1"
        candidate = SourceCandidate(
            self.aramco.company_id, "browser-issuer-reports", "report-referrer",
            "https://www.saudiexchange.sa/Resources/fsPdf/report.pdf",
            "Interim Financial Results", "interim-report", None, "application/pdf",
            {"referer": referer},
        )
        candidate_id, _ = self.db.save_source_candidate(candidate)
        received = {}

        def fetch_with_candidate(row):
            received.update(row)
            return b"%PDF-referer-test"

        result = DocumentArchiver(
            self.db, Path(self.temp.name) / "raw",
            candidate_fetcher=fetch_with_candidate,
        ).fetch(candidate_id)
        self.assertEqual(result["status"], "archived")
        self.assertEqual(received["metadata"]["referer"], referer)

    def test_context_only_news_is_archived_but_never_sent_to_numeric_extraction(self):
        candidate = SourceCandidate(
            self.aramco.company_id, "official-announcements", "news-1",
            "https://www.aramco.com/news/example.html", "Company announcement",
            "announcement", "2026-09-10", "text/html",
            {"source_role": "official_news", "authority_tier": "issuer_official",
             "numeric_authority": False},
        )
        candidate_id, _ = self.db.save_source_candidate(candidate)
        result = DocumentArchiver(
            self.db, Path(self.temp.name) / "raw", opener=opener_for(b"<html>news</html>"),
        ).fetch(candidate_id)
        self.assertNotIn("next_stage", result)
        self.assertFalse(result["numeric_authority"])
        self.assertEqual(self.db.source_status(result["source_key"]), "context_only")
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM extracted_facts").fetchone()[0], 0)

    def test_interim_pdf_is_held_until_period_semantics_are_proven(self):
        candidate = SourceCandidate(
            self.aramco.company_id, "browser-issuer-reports", "interim-review",
            "https://www.saudiexchange.sa/Resources/fsPdf/interim.pdf",
            "Interim Financial Results", "interim-report", None, "application/pdf",
        )
        candidate_id, _ = self.db.save_source_candidate(candidate)
        archived = DocumentArchiver(
            self.db, Path(self.temp.name) / "raw", opener=opener_for(b"%PDF-test"),
        ).fetch(candidate_id)
        registry = Path(__file__).resolve().parents[1] / "config" / "companies.json"
        job = type("Job", (), {
            "payload": {"source_key": archived["source_key"], "registry": str(registry)},
            "job_id": "interim-semantics-test",
        })()
        result = _extract_document_job_handler(self.db)(job)
        self.assertEqual(result["code"], "interim_period_semantics_required")
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM data_points").fetchone()[0], 0)

    def test_unreadable_interim_with_known_period_reports_extraction_failure(self):
        candidate = SourceCandidate(
            self.aramco.company_id, "browser-issuer-reports", "interim-unreadable",
            "https://www.saudiexchange.sa/Resources/fsPdf/interim.pdf",
            "Interim results for period ending 2026-06-30", "interim-report",
            "2026-08-06", "application/pdf",
        )
        candidate_id, _ = self.db.save_source_candidate(candidate)
        archived = DocumentArchiver(
            self.db, Path(self.temp.name) / "raw", opener=opener_for(b"%PDF-test"),
        ).fetch(candidate_id)
        job = type("Job", (), {
            "payload": {"source_key": archived["source_key"]},
            "job_id": "interim-unreadable-test",
        })()
        result = _extract_document_job_handler(self.db)(job)
        self.assertEqual(result["code"], "pdf_extraction_failed")

    def test_interim_period_is_derived_only_from_explicit_source_title(self):
        explicit = {"metadata_json": json.dumps({
            "title": "Interim Financial Results Period Ending on 30-06-2026"
        })}
        quarterly = {"metadata_json": json.dumps({
            "title": "Quarterly report 2026 Q2"
        })}
        unknown = {"metadata_json": json.dumps({"title": "Interim results"})}
        compact = {"metadata_json": json.dumps({
            "title": "Interim results for the period ending on 30-6-2026"
        })}
        iso = {"metadata_json": json.dumps({
            "title": "Interim results for the period ending on 2026-06-30"
        })}
        named = {"metadata_json": json.dumps({
            "title": "30 June 2026 Consolidated Financial Statement"
        })}
        self.assertEqual(_source_period(explicit, self.aramco), ("2026-06-30", 2026))
        self.assertEqual(_source_period(quarterly, self.aramco), ("2026-06-30", 2026))
        self.assertEqual(_source_period(compact, self.aramco), ("2026-06-30", 2026))
        self.assertEqual(_source_period(iso, self.aramco), ("2026-06-30", 2026))
        self.assertEqual(_source_period(named, self.aramco), ("2026-06-30", 2026))
        self.assertIsNone(_source_period(unknown, self.aramco))

    def test_xlsx_without_reviewed_map_enters_precise_exception_queue(self):
        content = b"PK\x03\x04-test-workbook"
        candidate = SourceCandidate(
            self.aramco.company_id, "browser-issuer-reports", "xlsx-no-map",
            "https://www.aramco.com/data.xlsx", "Q2 Data Supplement",
            "data-supplement", "2026-08-01",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        candidate_id, _ = self.db.save_source_candidate(candidate)
        archived = DocumentArchiver(
            self.db, Path(self.temp.name) / "raw", opener=opener_for(content),
        ).fetch(candidate_id)
        job = type("Job", (), {
            "payload": {"source_key": archived["source_key"]},
            "job_id": "xlsx-map-test",
        })()
        result = _extract_document_job_handler(self.db)(job)
        self.assertEqual(result["code"], "xlsx_mapping_required")
        exception = self.db.conn.execute(
            "SELECT code FROM exceptions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        self.assertEqual(exception["code"], "xlsx_mapping_required")

    def test_reviewed_bank_xlsx_is_extracted_and_published(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl is not installed")
        bank = Company(
            "sa:1120", Market.SA, "1120", "Al Rajhi Bank", "SAR",
            industry="Banks",
        )
        self.db.register_company(bank)
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "1. Income Statement"
        sheet.append(["SAR mn", "FY 2025", "1Q 2026"])
        sheet.append(["Net income for the period after Zakat", 21000, 6000])
        stream = io.BytesIO()
        workbook.save(stream)
        workbook.close()
        candidate = SourceCandidate(
            bank.company_id, "browser-issuer-reports", "xlsx-reviewed",
            "https://issuer.example/Q1-2026-data.xlsx", "Q1 2026 Data Supplement",
            "data-supplement", "2026-04-30",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        candidate_id, _ = self.db.save_source_candidate(candidate)
        archived = DocumentArchiver(
            self.db, Path(self.temp.name) / "raw", opener=opener_for(stream.getvalue()),
        ).fetch(candidate_id)
        registry = Path(__file__).resolve().parents[1] / "config" / "companies.json"
        job = type("Job", (), {
            "payload": {
                "source_key": archived["source_key"], "registry": str(registry),
                "raw_dir": str(Path(self.temp.name) / "pipeline"),
            },
            "job_id": "xlsx-publish-test",
        })()
        result = _extract_document_job_handler(self.db)(job)
        self.assertEqual(result["status"], "published", result)
        self.assertEqual(result["source_key"], archived["source_key"])
        self.assertEqual(self.db.source_status(archived["source_key"]), "published")
        kinds = {row["period_kind"] for row in self.db.conn.execute(
            "SELECT period_kind FROM data_points "
            "WHERE company_id='sa:1120' AND is_current=1"
        )}
        self.assertEqual(kinds, {"fy", "quarter"})


if __name__ == "__main__":
    unittest.main()
