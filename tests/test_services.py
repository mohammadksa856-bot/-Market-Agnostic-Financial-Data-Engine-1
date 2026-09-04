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
from finengine.archive import archive_manifest_sources
from finengine.bootstrap import rebuild_snapshot
from finengine.database import Database
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument
from finengine.query import FinancialQueryService
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
            request=Request(f"http://127.0.0.1:{port}/v1/companies/SA/TST/dossier",
                            headers={"X-API-Key":"secret"})
            dossier=json.loads(urlopen(request).read())
            self.assertEqual(dossier["overview"]["name"],"Test Company")
            self.assertEqual(dossier["facts_by_category"]["financial"][0]["metric"],"revenue")
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
        profile=answer_command(self.dbpath,"/profile SA TST")
        self.assertIn("Test Company",profile)
        self.assertIn("100 SAR",profile)

    def test_release_audit_checks_source_hashes(self):
        result=audit_release(self.dbpath)
        self.assertTrue(result["ready"])
        self.raw.write_bytes(b"tampered")
        result=audit_release(self.dbpath)
        self.assertFalse(result["ready"])
        self.assertEqual(next(check for check in result["checks"] if check["name"]=="source_archive_hashes")["status"],"fail")

    def test_official_source_artifact_is_archived_and_indexed(self):
        root=Path(self.temp.name); imports=root/"imports"; imports.mkdir()
        manifest=imports/"aramco-2025.json"
        manifest.write_text(json.dumps({
            "company_id":"sa:TST","source_url":"https://example.test/report.pdf","facts":[]
        }),encoding="utf-8")
        registry=root/"companies.json"
        registry.write_text(json.dumps([{
            "company_id":"sa:TST","market":"SA","symbol":"TST","name":"Test Company",
            "currency":"SAR"
        }]),encoding="utf-8")

        class Headers(dict):
            def get_content_type(self): return "application/pdf"
        class Response:
            headers=Headers()
            def __init__(self): self.sent=False
            def __enter__(self): return self
            def __exit__(self,*_): return None
            def read(self,_size):
                if self.sent: return b""
                self.sent=True; return b"%PDF-1.7 archived"
        def opener(_request,timeout=0): return Response()

        result=archive_manifest_sources(
            self.dbpath,imports,registry,root/"raw",project_root=root,opener=opener,
        )
        self.assertEqual(result["archived"],1)
        self.assertTrue((root/"raw"/"archive-index.json").is_file())
        db=Database(self.dbpath)
        try:
            row=db.conn.execute("SELECT local_path,content_hash FROM source_artifacts").fetchone()
            self.assertTrue((root/row["local_path"]).is_file())
            self.assertEqual(db.health()["source_artifacts"],1)
        finally: db.close()

    def test_domain_only_manifest_publishes_market_prices(self):
        root=Path(self.temp.name); imports=root/"imports"; imports.mkdir()
        manifest=imports/"aramco-market.json"
        manifest.write_text(json.dumps({
            "company_id":"sa:2222",
            "filing_type":"Saudi Exchange historical price snapshot",
            "filed_at":"2026-09-04",
            "source_url":"https://example.test/historical-prices",
            "facts":[],
            "market_prices":[{
                "observed_at":"2026-09-03","interval":"1d",
                "open":"26.02","high":"26.10","low":"25.90","close":"25.96",
                "volume":"6688799","turnover":"173977896.58","currency":"SAR"
            }]
        }),encoding="utf-8")
        output=root/"snapshot.sqlite3"
        result=rebuild_snapshot(output,imports,Path(__file__).resolve().parents[1]/"config"/"companies.json",
                                root/"raw")
        self.assertEqual(result["manifests"],1)
        query=FinancialQueryService(output)
        try: prices=query.market_prices("SA","2222")
        finally: query.close()
        self.assertEqual((len(prices),prices[0]["close"]),(1,"25.96"))

    def test_reviewed_manifests_rebuild_portable_snapshot(self):
        project=Path(__file__).resolve().parents[1]
        output=Path(self.temp.name)/"rebuilt.sqlite3"
        result=rebuild_snapshot(output,project/"data"/"imports",project/"config"/"companies.json",
                                Path(self.temp.name)/"raw")
        self.assertGreaterEqual(result["manifests"],30)
        audit=audit_release(output,project)
        self.assertTrue(audit["ready"])
        self.assertGreaterEqual(audit["current_facts"],600)
        query=FinancialQueryService(str(output))
        try:
            dossier=query.company_dossier("SA","2222")
        finally:
            query.close()
        self.assertEqual(dossier["attributes"]["employees"]["value"],76664)
        self.assertEqual(len(dossier["ownership"]),4)
        self.assertGreaterEqual(len(dossier["disclosures"]),8)
        self.assertEqual(len(dossier["corporate_actions"]),8)
        self.assertEqual(len(dossier["market_prices"]),23)
        self.assertGreaterEqual(sum(
            1 for row in dossier["facts_by_category"]["financial"]
            if row["statement"] == "financial_notes"
        ), 100)
        commercial = {row["metric"]: row for row in dossier["facts_by_category"]["commercial"]
                      if row["period_end"] == "2025-12-31"}
        advance = commercial["advance_payment_long_term_sales_agreement"]
        self.assertEqual(advance["value"], "5358000000")
        self.assertEqual(advance["provenance"]["extraction"]["page"], 48)
        self.assertIn("long-term sales", advance["provenance"]["extraction"]["table_ref"])
        self.assertTrue(advance["provenance"]["source"]["content_hash"])
        valuation={row["metric"]:row for row in dossier["facts_by_category"]["calculated"]
                   if row["period_end"]=="2026-09-03"}
        self.assertIn("price_to_earnings",valuation)
        self.assertEqual(valuation["price_to_earnings"]["provenance"]["derivation"]["type"],
                         "deterministic_calculation")

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
