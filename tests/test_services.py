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
            backlog=query.backlog("SA","2222")
        finally:
            query.close()
        self.assertEqual(dossier["attributes"]["employees"]["value"],76664)
        self.assertEqual(len(dossier["ownership"]),4)
        self.assertGreaterEqual(len(dossier["disclosures"]),9)
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
        financial_2025 = [row for row in dossier["facts_by_category"]["financial"]
                          if row["period_end"] == "2025-12-31"]
        commitments = {row["metric"]: row for row in financial_2025
                       if row["metric"] in {"capital_commitments", "lease_commitments_not_commenced"}}
        self.assertEqual(commitments["capital_commitments"]["value"], "174551000000")
        self.assertEqual(commitments["capital_commitments"]["provenance"]["extraction"]["page"], 69)
        self.assertEqual(commitments["lease_commitments_not_commenced"]["value"], "25357000000")
        ecl = next(row for row in financial_2025 if row["metric"] == "expected_credit_losses")
        self.assertEqual(ecl["value"], "246000000")
        self.assertEqual(ecl["provenance"]["extraction"]["page"], 51)
        lease_interest = next(row for row in financial_2025
                              if row["metric"] == "lease_interest_expense")
        self.assertEqual(lease_interest["value"], "3309000000")
        self.assertEqual(lease_interest["provenance"]["extraction"]["page"], 54)
        goodwill = next(row for row in financial_2025
                        if row["metric"] == "goodwill_by_cash_generating_unit")
        self.assertEqual(goodwill["value"], "99116000000")
        undrawn = [row for row in financial_2025 if row["metric"] == "undrawn_credit_facilities"]
        self.assertEqual(len(undrawn), 9)
        self.assertTrue(any("do not sum" in row["dimensions"].get("overlap_note", "")
                            for row in undrawn))
        accounts_payable = next(row for row in financial_2025 if row["metric"] == "accounts_payable")
        self.assertEqual(accounts_payable["value"], "79054000000")
        self.assertEqual(accounts_payable["provenance"]["extraction"]["page"], 66)
        geography = [row for row in financial_2025 if row["metric"] == "revenue_by_geography"]
        self.assertEqual(sum(int(row["value"]) for row in geography), 1559342000000)
        service_cost = [row for row in financial_2025
                        if row["metric"] == "service_cost_employee_benefits"]
        self.assertEqual(len(service_cost), 2)
        commercial_disclosures = [row for row in dossier["disclosures"]
                                  if row["disclosure_type"] == "commercial_contract"]
        self.assertEqual(commercial_disclosures[0]["metadata"]["quantitative_volume_disclosed"], False)
        contingency = next(row for row in dossier["disclosures"]
                           if row["disclosure_type"] == "contingency")
        self.assertFalse(contingency["metadata"]["quantitative_amount_disclosed"])
        customer_risk = next(row for row in dossier["disclosures"]
                             if row["disclosure_type"] == "customer_concentration")
        self.assertFalse(customer_risk["metadata"]["major_customer_amount_disclosed"])
        financial_notes_backlog = next(row for row in backlog
                                       if row["domain"] == "financial_notes")
        note_availability = {
            row["field_key"]: row["availability"]
            for row in financial_notes_backlog["payload"]["field_assessments"]
        }
        self.assertEqual(note_availability["contingencies"], "qualitative_disclosure_only")
        self.assertEqual(note_availability["customer_concentration"],
                         "qualitative_disclosure_only")
        self.assertNotIn("lease_interest_expense", note_availability)
        commercial_backlog = next(row for row in backlog
                                  if row["domain"] == "commercial_pipeline")
        availability = {row["field_key"]: row["availability"]
                        for row in commercial_backlog["payload"]["field_assessments"]}
        self.assertEqual(availability["minimum_volume_commitments"],
                         "qualitative_disclosure_only")
        self.assertEqual(availability["sales_order_backlog"],
                         "not_disclosed_in_archived_filings")
        commercial_coverage = commercial_backlog["payload"]["coverage_interpretation"]
        self.assertGreater(commercial_coverage["verified_unavailable"], 0)
        self.assertLess(commercial_coverage["actionable_missing"],
                        len(commercial_backlog["payload"]["missing_fields"]))
        operations = {row["metric"]: row for row in dossier["facts_by_category"]["operational"]
                      if row["period_end"] == "2025-12-31" and not row["dimensions"]}
        self.assertEqual(operations["total_liquids_production"]["value"], "10.678")
        self.assertEqual(operations["total_gas_production"]["value"], "11.365")
        self.assertEqual(operations["total_hydrocarbon_production"]["value"], "12.891")
        reserve_life = operations["reserve_life_index"]
        self.assertAlmostEqual(float(reserve_life["value"]), 52.5374504672, places=8)
        self.assertEqual(reserve_life["provenance"]["derivation"]["type"],
                         "deterministic_calculation")
        segment_2025 = {
            (row["metric"], row["dimensions"].get("segment")): row
            for row in dossier["facts_by_category"]["operational"]
            if row["period_end"] == "2025-12-31" and row["dimensions"].get("segment")
        }
        self.assertEqual(segment_2025[("upstream_ebitda", "Upstream")]["value"],
                         "780775000000")
        self.assertEqual(segment_2025[("downstream_ebitda", "Downstream")]["value"],
                         "29508000000")
        self.assertEqual(
            segment_2025[("upstream_ebitda", "Upstream")]["provenance"]["derivation"]["type"],
            "deterministic_calculation",
        )
        oil_gas_backlog = next(row for row in backlog if row["domain"] == "oil_gas_operations")
        oil_gas_availability = {
            row["field_key"]: row["availability"]
            for row in oil_gas_backlog["payload"]["field_assessments"]
        }
        self.assertEqual(oil_gas_availability["spare_capacity"],
                         "not_disclosed_in_archived_annual_report")
        self.assertNotIn("reserve_life_index", oil_gas_availability)
        oil_gas_coverage = oil_gas_backlog["payload"]["coverage_interpretation"]
        self.assertEqual(oil_gas_coverage["verified_unavailable"], 15)
        self.assertEqual(oil_gas_coverage["actionable_missing"], 0)
        valuation={row["metric"]:row for row in dossier["facts_by_category"]["calculated"]
                   if row["period_end"]=="2026-09-03"}
        self.assertIn("price_to_earnings",valuation)
        self.assertEqual(valuation["price_to_earnings"]["provenance"]["derivation"]["type"],
                         "deterministic_calculation")
        ratios_2025 = {row["metric"]: row for row in dossier["facts_by_category"]["ratio"]
                       if row["period_end"] == "2025-12-31"}
        self.assertIn("effective_tax_rate", ratios_2025)
        self.assertAlmostEqual(float(ratios_2025["effective_tax_rate"]["value"]),
                               352650 / 702860, places=10)

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
