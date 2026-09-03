import hashlib
import json
import tempfile
import threading
import unittest
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from finengine.api import create_api_server
from finengine.audit import audit_release
from finengine.bootstrap import rebuild_snapshot
from finengine.database import Database
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument
from finengine.report import export_readable_report
from finengine.telegram import answer_command


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); root=Path(self.temp.name)
        self.dbpath=str(root/"financial.sqlite3"); self.raw=root/"source.json"; self.raw.write_bytes(b"{}")
        db=Database(self.dbpath); company=Company("sa:TST",Market.SA,"TST","Test Company","SAR")
        db.register_company(company)
        document=SourceDocument(company.company_id,company.market,"https://example.test/report","source:test","annual","2026-01-01",b"{}")
        db.save_source(document,hashlib.sha256(b"{}").hexdigest(),str(self.raw)); db.set_source_status(document.source_key,"published")
        db.publish(Fact(company.company_id,"revenue",Decimal("100"),"SAR","SAR","2025-01-01","2025-12-31",PeriodKind.FY,2025,None,document.source_key,document.source_url,document.filed_at))
        db.close()

    def tearDown(self): self.temp.cleanup()

    def test_http_api_is_authenticated_and_read_only(self):
        server=create_api_server(self.dbpath,"127.0.0.1",0,"secret")
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        port=server.server_address[1]
        try:
            with self.assertRaises(HTTPError) as denied:
                urlopen(f"http://127.0.0.1:{port}/health")
            self.assertEqual(denied.exception.code,401)
            request=Request(f"http://127.0.0.1:{port}/v1/companies/SA/TST/metrics/revenue",
                            headers={"X-API-Key":"secret"})
            payload=json.loads(urlopen(request).read())
            self.assertEqual(payload[0]["value"],"100")
            request=Request(f"http://127.0.0.1:{port}/v1/catalog?limit=500",
                            headers={"X-API-Key":"secret"})
            catalog=json.loads(urlopen(request).read())
            self.assertGreaterEqual(len(catalog),300)
            request=Request(f"http://127.0.0.1:{port}/health",data=b"{}",method="POST",
                            headers={"X-API-Key":"secret"})
            with self.assertRaises(HTTPError) as readonly: urlopen(request)
            self.assertEqual(readonly.exception.code,405)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)

    def test_telegram_adapter_reads_the_same_database(self):
        answer=answer_command(self.dbpath,"/metric SA TST revenue")
        self.assertIn("100 SAR",answer)

    def test_release_audit_checks_source_hashes(self):
        result=audit_release(self.dbpath)
        self.assertTrue(result["ready"])
        self.raw.write_bytes(b"tampered")
        result=audit_release(self.dbpath)
        self.assertFalse(result["ready"])
        self.assertEqual(next(check for check in result["checks"] if check["name"]=="source_archive_hashes")["status"],"fail")

    def test_reviewed_manifests_rebuild_portable_snapshot(self):
        project=Path(__file__).resolve().parents[1]
        output=Path(self.temp.name)/"rebuilt.sqlite3"
        result=rebuild_snapshot(output,project/"data"/"imports",project/"config"/"companies.json",
                                Path(self.temp.name)/"raw")
        self.assertEqual(result["manifests"],26)
        audit=audit_release(output,project)
        self.assertTrue(audit["ready"])
        self.assertEqual(audit["current_facts"],321)

    def test_readable_report_is_utf8_searchable_and_source_linked(self):
        root=Path(self.temp.name)
        html_path=root/"financial-report.html"; csv_path=root/"financial-data.csv"
        export_readable_report(self.dbpath,str(html_path),str(csv_path))
        page=html_path.read_text(encoding="utf-8")
        self.assertIn('lang="ar" dir="rtl"',page)
        self.assertIn('id="search"',page)
        self.assertIn('id="company"',page)
        self.assertIn('data-company="TST"',page)
        self.assertIn("الإيرادات",page)
        self.assertIn('rel="noopener" href="https://example.test/report"',page)
        self.assertNotIn("\ufffd",page)
        self.assertTrue(csv_path.read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__=="__main__": unittest.main()
