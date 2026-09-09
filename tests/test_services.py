import hashlib
import json
import tempfile
import threading
import unittest
import zipfile
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
from finengine.operations import (
    backup_database, configure_production_schedules, create_portable_bundle,
    verify_portable_bundle,
)
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
            request=Request(f"http://127.0.0.1:{port}/v1/companies/SA/TST/page",
                            headers={"X-API-Key":"secret"})
            page=json.loads(urlopen(request).read())
            self.assertEqual(page["placeholder_policy"],"never_substitute_demo_values")
            self.assertEqual(page["sections"]["financials"]["annual"]["period_kind"],"fy")
            self.assertEqual(page["sections"]["financials"]["annual"]["metrics"]["revenue"][0]["value"],"100")
            self.assertEqual(page["sections"]["financials"]["quarter"]["status"],"unavailable")
            self.assertEqual(page["capabilities"]["consensus"]["reason"],"licensed_consensus_feed_required")
            request=Request(f"http://127.0.0.1:{port}/v1/catalog?limit=500",
                            headers={"X-API-Key":"secret"})
            catalog=json.loads(urlopen(request).read())
            self.assertGreaterEqual(len(catalog),300)
            request=Request(f"http://127.0.0.1:{port}/v1/catalog/history/revenue",
                            headers={"X-API-Key":"secret"})
            history=json.loads(urlopen(request).read())
            self.assertEqual(history[0]["definition"]["field_key"],"revenue")
            request=Request(f"http://127.0.0.1:{port}/v1/dimensions",
                            headers={"X-API-Key":"secret"})
            dimensions=json.loads(urlopen(request).read())
            self.assertIn("segment",{item["dimension_key"] for item in dimensions})
            request=Request(f"http://127.0.0.1:{port}/v1/universe/inventory?market=SA",
                            headers={"X-API-Key":"secret"})
            inventory=json.loads(urlopen(request).read())
            self.assertEqual(inventory["coverage_warning"],
                             "inventory_membership_is_not_product_coverage")
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

    def test_company_page_never_mixes_period_semantics(self):
        db=Database(self.dbpath)
        document=SourceDocument("sa:TST",Market.SA,"https://example.test/q2","source:q2",
                                "quarterly","2026-08-01",b"q2")
        raw=Path(self.temp.name)/"q2.json"; raw.write_bytes(b"q2")
        db.save_source(document,hashlib.sha256(b"q2").hexdigest(),str(raw))
        db.set_source_status(document.source_key,"published")
        db.publish(Fact("sa:TST","revenue",Decimal("30"),"SAR","SAR","2026-04-01",
                        "2026-06-30",PeriodKind.QUARTER,2026,2,document.source_key,
                        document.source_url,document.filed_at))
        db.publish(Fact("sa:TST","revenue",Decimal("55"),"SAR","SAR","2026-01-01",
                        "2026-06-30",PeriodKind.YTD,2026,2,document.source_key,
                        document.source_url,document.filed_at))
        db.close()
        query=FinancialQueryService(self.dbpath)
        try: page=query.company_page("SA","TST")
        finally: query.close()
        self.assertEqual(page["sections"]["financials"]["quarter"]["metrics"]["revenue"][0]["value"],"30")
        self.assertEqual(page["sections"]["financials"]["ytd"]["metrics"]["revenue"][0]["value"],"55")

    def test_release_audit_checks_source_hashes(self):
        result=audit_release(self.dbpath)
        self.assertTrue(result["ready"])
        self.raw.write_bytes(b"tampered")
        result=audit_release(self.dbpath)
        self.assertFalse(result["ready"])
        self.assertEqual(next(check for check in result["checks"] if check["name"]=="source_archive_hashes")["status"],"fail")

    def test_online_backup_is_integrity_checked_and_retained(self):
        output=Path(self.temp.name)/"backups"
        first=backup_database(self.dbpath,output,keep=1)
        self.assertEqual(first["status"],"ready")
        self.assertEqual(len(first["sha256"]),64)
        second=backup_database(self.dbpath,output,keep=1)
        self.assertTrue(Path(second["backup"]).is_file())
        self.assertTrue(Path(second["metadata"]).is_file())
        self.assertEqual(len(list(output.glob("financial-*.sqlite3"))),1)

    def test_portable_bundle_contains_verified_database_and_sources(self):
        output=Path(self.temp.name)/"bundles"
        result=create_portable_bundle(self.dbpath,output,self.temp.name,keep=1)
        self.assertEqual(result["status"],"ready")
        self.assertEqual(result["files"],1)
        self.assertTrue(Path(result["bundle"]).is_file())
        verified=verify_portable_bundle(result["bundle"])
        self.assertEqual(verified["format"],"finengine-portable-bundle-v1")
        self.assertGreater(verified["database_bytes"],0)

    def test_portable_bundle_deduplicates_identical_artifact_content(self):
        duplicate=Path(self.temp.name)/"duplicate.json"
        duplicate.write_bytes(self.raw.read_bytes())
        digest=hashlib.sha256(duplicate.read_bytes()).hexdigest()
        db=Database(self.dbpath)
        try:
            db.save_source_artifact("artifact:test","sa:TST","https://example.test/artifact",
                                    digest,str(duplicate),"application/json",
                                    duplicate.stat().st_size)
        finally:
            db.close()
        result=create_portable_bundle(self.dbpath,Path(self.temp.name)/"bundles",
                                      self.temp.name,keep=1)
        self.assertEqual(result["files"],1)
        with zipfile.ZipFile(result["bundle"],"r") as archive:
            members=archive.namelist()
            self.assertEqual(len(members),len(set(members)))
            manifest=json.loads(archive.read("manifest.json"))
        self.assertEqual(len(manifest["files"][0]["original_paths"]),2)

    def test_production_schedule_configuration_is_idempotent(self):
        registry=Path(self.temp.name)/"companies.json"
        registry.write_text(json.dumps([{
            "company_id":"sa:TST","market":"SA","symbol":"TST","name":"Test Company",
            "currency":"SAR","industry":"Diversified Chemicals",
            "sources":["https://example.test/reports"]
        }]),encoding="utf-8")
        runtime_raw=Path(self.temp.name)/"runtime"/"raw"
        first=configure_production_schedules(self.dbpath,registry,3600,25,True,runtime_raw)
        second=configure_production_schedules(self.dbpath,registry,3600,25,True,runtime_raw)
        self.assertEqual(first["count"],1)
        self.assertEqual(second["configured"],["monitor:SA:TST"])
        db=Database(self.dbpath)
        try:
            rows=db.conn.execute("SELECT payload_json FROM schedules WHERE enabled=1").fetchall()
        finally:
            db.close()
        self.assertEqual(len(rows),1)
        payload=json.loads(rows[0]["payload_json"])
        self.assertTrue(payload["browser"])
        self.assertTrue(payload["llm"])
        self.assertEqual(payload["source_limit"],25)
        self.assertEqual(payload["raw_dir"],str(runtime_raw))

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

    def test_archive_resolves_legacy_manifest_by_official_source_host(self):
        root=Path(self.temp.name); imports=root/"imports"; imports.mkdir()
        (imports/"legacy-report.json").write_text(json.dumps({
            "source_url":"https://issuer.example/reports/annual.pdf","facts":[]
        }),encoding="utf-8")
        registry=root/"companies.json"
        registry.write_text(json.dumps([{
            "company_id":"sa:TST","market":"SA","symbol":"TST","name":"Test Company",
            "currency":"SAR","sources":["https://issuer.example/investors"]
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
        result=archive_manifest_sources(
            self.dbpath,imports,registry,root/"raw",project_root=root,
            opener=lambda _request,timeout=0: Response(),
        )
        self.assertEqual(result["archived"],1)
        self.assertEqual(result["results"][0]["company_id"],"sa:TST")

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
            sabic=query.company_dossier("SA","2010")
            sabic_annual_prices=query.market_prices("SA","2010",interval="1y")
            sabic_completeness=query.completeness("SA","2010")
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
        reserve_components = [row for row in financial_2025
                              if row["metric"] == "other_reserve_components"]
        self.assertEqual(len(reserve_components), 7)
        self.assertEqual(sum(int(row["value"]) for row in reserve_components), 1472000000)
        self.assertTrue(all(row["provenance"]["extraction"]["page"] == 214
                            for row in reserve_components))
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
        self.assertTrue(all(
            item.get("reason") and item.get("resolution") and item.get("solution_code")
            for item in commercial_backlog["payload"]["field_assessments"]
        ))
        self.assertTrue(all(
            item.get("reason") and item.get("resolution") and item.get("solution_code")
            for backlog_item in backlog
            for item in backlog_item["payload"].get("field_assessments", [])
        ))
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
        self.assertIn("simple_moving_average_20d", valuation)
        self.assertIn("price_to_sma_20d", valuation)
        market_metrics = {row["metric"]: row for row in dossier["facts_by_category"]["market"]
                          if row["period_end"] == "2026-09-03"}
        self.assertIn("vwap", market_metrics)
        self.assertAlmostEqual(float(market_metrics["vwap"]["value"]),
                               173977896.58 / 6688799, places=10)
        ratios_2025 = {row["metric"]: row for row in dossier["facts_by_category"]["ratio"]
                       if row["period_end"] == "2025-12-31"}
        self.assertIn("effective_tax_rate", ratios_2025)
        self.assertAlmostEqual(float(ratios_2025["effective_tax_rate"]["value"]),
                               352650 / 702860, places=10)
        sabic_segments = {
            (row["metric"], row["dimensions"].get("segment")): row
            for row in sabic["facts_by_category"]["operational"]
            if row["period_end"] == "2025-12-31" and row["dimensions"].get("segment")
        }
        self.assertEqual(sabic_segments[("segment_revenue", "Petrochemicals")]["value"],
                         "103935678000")
        self.assertEqual(sabic_segments[("segment_assets", "Agri-Nutrients")]["value"],
                         "27647759000")
        self.assertEqual(
            sabic_segments[("production_volume", "Chemicals")]["value"], "35.7")
        self.assertEqual(
            sabic_segments[("production_volume", "Chemicals")]["provenance"]["extraction"]["page"],
            47,
        )
        self.assertEqual(sabic["attributes"]["business_description"]["category"],
                         "business_model")
        self.assertEqual(len(sabic["ownership"]), 3)
        self.assertEqual(len(sabic["corporate_actions"]), 3)
        self.assertEqual(len(sabic_annual_prices), 5)
        by_category = {row["category"]: row for row in sabic_completeness["categories"]}
        self.assertNotIn("free_float", by_category["ownership"]["missing_fields"])
        self.assertNotIn("foreign_ownership", by_category["ownership"]["missing_fields"])
        self.assertNotIn("strategic_ownership", by_category["ownership"]["missing_fields"])
        self.assertNotIn("dividend_payment", by_category["corporate_actions"]["missing_fields"])
        self.assertNotIn("fifty_two_week_high", by_category["market_data"]["missing_fields"])
        sabic_esg = {
            row["metric"]: row for row in sabic["facts_by_category"]["operational"]
            if row["period_end"] == "2025-12-31" and not row["dimensions"]
        }
        self.assertEqual(sabic_esg["scope_1_2_emissions"]["value"], "41.51")
        self.assertEqual(sabic_esg["scope_1_2_emissions"]["provenance"]["extraction"]["page"],
                         232)
        sabic_income = {
            row["metric"]: row for row in sabic["facts_by_category"]["financial"]
            if row["period_end"] == "2025-12-31" and row["period_kind"] == "fy"
            and not row["dimensions"]
        }
        self.assertEqual(sabic_income["basic_eps"]["value"], "-8.59")
        self.assertEqual(sabic_income["basic_eps"]["provenance"]["extraction"]["page"], 133)
        sabic_geography = [
            row for row in sabic["facts_by_category"]["financial"]
            if row["metric"] == "revenue_by_geography"
            and row["period_end"] == "2025-12-31"
        ]
        self.assertEqual(len(sabic_geography), 7)
        self.assertEqual(sum(int(row["value"]) for row in sabic_geography), 116525214000)
        sabic_calculated = {
            row["metric"]: row for row in sabic["facts_by_category"]["calculated"]
            if row["period_end"] == "2025-12-31"
        }
        self.assertIn("price_to_sales", sabic_calculated)
        self.assertAlmostEqual(float(sabic_calculated["price_to_sales"]["value"]),
                               153900000000 / 116525214000, places=10)
        self.assertEqual(
            sabic_calculated["price_to_sales"]["provenance"]["derivation"]["type"],
            "deterministic_calculation",
        )
        self.assertIn("revenue_growth", sabic_calculated)
        self.assertAlmostEqual(float(sabic_calculated["revenue_growth"]["value"]),
                               116525214000 / 117736492000 - 1, places=10)
        sabic_notes = [
            row for row in sabic["facts_by_category"]["financial"]
            if row["period_end"] == "2025-12-31" and row["statement"] == "financial_notes"
        ]
        debt_maturities = [row for row in sabic_notes
                           if row["metric"] == "borrowings_by_maturity"]
        self.assertEqual(len(debt_maturities), 4)
        self.assertEqual(sum(int(row["value"]) for row in debt_maturities), 32448947000)
        capital_commitment = next(row for row in sabic_notes
                                  if row["metric"] == "capital_commitments")
        self.assertEqual(capital_commitment["value"], "6503000000")
        self.assertEqual(capital_commitment["provenance"]["extraction"]["page"], 213)
        sabic_2024 = [
            row for row in sabic["facts_by_category"]["financial"]
            if row["period_end"] == "2024-12-31" and row["metric"] == "total_assets"
        ]
        self.assertEqual(sabic_2024[0]["value"], "277543843000")
        self.assertEqual(sabic_2024[0]["provenance"]["extraction"]["page"], 132)

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
