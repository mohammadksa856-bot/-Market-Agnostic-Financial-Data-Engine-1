import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from finengine.database import Database
from finengine.domains import CompanyDomainStore
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument, TypedFact, ValueType
from finengine.query import FinancialQueryService


class CompanyDomainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "domains.sqlite3")
        self.db = Database(self.path)
        self.company = Company("sa:TST", Market.SA, "TST", "Test Energy", "SAR",
                               isin="SA0000000001", exchange="Saudi Exchange",
                               country="SA", sector="Energy", industry="Test Energy",
                               timezone="Asia/Riyadh")
        self.db.register_company(self.company)
        self.source = SourceDocument("sa:TST", Market.SA, "https://example.test/source", "source:domain",
                                     "annual-results", "2026-03-01", b"{}")
        self.db.save_source(self.source, "domain", None)
        self.store = CompanyDomainStore(self.db)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def fact(self, metric, value):
        return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR", "2025-01-01", "2025-12-31",
                    PeriodKind.FY, 2025, None, self.source.source_key, self.source.source_url,
                    self.source.filed_at)

    def test_company_registration_creates_security_and_primary_listing(self):
        listing = self.db.conn.execute(
            """SELECT s.isin,l.exchange,l.symbol,l.is_primary FROM listings l
            JOIN securities s USING(security_id)""").fetchone()
        self.assertEqual((listing["isin"], listing["exchange"], listing["symbol"], listing["is_primary"]),
                         ("SA0000000001", "Saudi Exchange", "TST", 1))

    def test_typed_facts_support_text_boolean_and_json(self):
        facts = [
            TypedFact("sa:TST", "business_description", "Energy producer", ValueType.TEXT,
                      "2025-12-31", PeriodKind.AS_OF, self.source.source_key,
                      self.source.source_url, self.source.filed_at),
            TypedFact("sa:TST", "is_sharia_screened", True, ValueType.BOOLEAN,
                      "2025-12-31", PeriodKind.AS_OF, self.source.source_key,
                      self.source.source_url, self.source.filed_at),
            TypedFact("sa:TST", "production_mix", {"oil": 0.8, "gas": 0.2}, ValueType.JSON,
                      "2025-12-31", PeriodKind.AS_OF, self.source.source_key,
                      self.source.source_url, self.source.filed_at),
        ]
        self.assertEqual(self.db.publish_typed_batch(facts), ["inserted", "inserted", "inserted"])
        self.assertEqual(self.db.publish_typed(facts[0]), "duplicate")
        with self.assertRaises(ValueError):
            self.db.publish_typed(TypedFact("sa:TST", "bad_date", "2025-99-99", ValueType.DATE,
                                  "2025-12-31", PeriodKind.AS_OF, self.source.source_key,
                                  self.source.source_url, self.source.filed_at))
        query = FinancialQueryService(self.path)
        self.assertEqual(query.metric_history("SA", "TST", "business_description")[0]["value"], "Energy producer")
        self.assertIs(query.metric_history("SA", "TST", "is_sharia_screened")[0]["value"], True)
        self.assertEqual(query.metric_history("SA", "TST", "production_mix")[0]["value"]["oil"], 0.8)
        query.close()

    def test_market_price_is_validated_and_versioned(self):
        self.assertEqual(self.store.publish_market_price("sa:TST", "2026-01-01", "30", "SAR",
                         self.source.source_key, open="29", high="31", low="28", volume="1000"), "inserted")
        self.assertEqual(self.store.publish_market_price("sa:TST", "2026-01-01", "30.5", "SAR",
                         self.source.source_key, open="29", high="31", low="28", volume="1000"), "restated")
        with self.assertRaises(ValueError):
            self.store.publish_market_price("sa:TST", "2026-01-02", "30", "SAR",
                                            self.source.source_key, high="29")
        query = FinancialQueryService(self.path)
        self.assertEqual(query.market_prices("SA", "TST")[0]["close"], "30.5")
        query.close()

    def test_ownership_and_corporate_actions_are_structured(self):
        self.assertEqual(self.store.publish_ownership_position(
            "sa:TST", "holder:government", "Government", "beneficial", "2025-12-31",
            self.source.source_key, shares="800", ownership_pct="0.8", holder_type="government"), "inserted")
        with self.assertRaises(ValueError):
            self.store.publish_ownership_position(
                "sa:TST", "holder:bad", "Bad", "beneficial", "2025-12-31",
                self.source.source_key, ownership_pct="1.1")
        self.assertEqual(self.store.publish_corporate_action(
            "dividend:2026:q1", "sa:TST", "cash_dividend", "Q1 dividend", "2026-05-01",
            self.source.source_key, eligibility_date="2026-05-15", payment_date="2026-05-30",
            cash_amount="0.35", currency="SAR"), "inserted")
        query = FinancialQueryService(self.path)
        self.assertEqual(query.ownership("SA", "TST")[0]["ownership_pct"], "0.8")
        self.assertEqual(query.corporate_actions("SA", "TST")[0]["payment_date"], "2026-05-30")
        query.close()

    def test_formula_registry_tracks_dependencies(self):
        self.store.register_calculation("return_on_assets", "net_income / average(total_assets)",
                                        ["net_income", "total_assets"], 1, output_unit="ratio",
                                        period_rule="average_balance")
        query = FinancialQueryService(self.path)
        formula = query.calculation_definition("return_on_assets")
        query.close()
        self.assertEqual(formula["expression"], "net_income / average(total_assets)")
        self.assertEqual({item["dependency_metric"] for item in formula["dependencies"]},
                         {"net_income", "total_assets"})

    def test_coverage_uses_applicability_not_a_fixed_company_template(self):
        self.db.publish_batch([self.fact("revenue", "100"), self.fact("net_income", "10")])
        partial = self.store.refresh_coverage("sa:TST", "2025-12-31", "fy", "financial")
        self.assertEqual((partial["expected_count"], partial["available_count"], partial["status"]),
                         (4, 2, "partial"))
        self.assertEqual(partial["backlog"]["open"], 2)
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM backlog_items WHERE item_type='coverage_gap' AND status='open'"
        ).fetchone()[0], 2)
        self.db.publish_batch([self.fact("operating_cash_flow", "20"), self.fact("capex", "5")])
        complete = self.store.refresh_coverage("sa:TST", "2025-12-31", "fy", "financial")
        self.assertEqual(complete["status"], "complete")
        self.assertEqual(complete["backlog"], {"open": 0, "completed": 2})
        self.store.set_freshness_policy("company", "sa:TST", "financial", 86400)
        stale = self.store.refresh_coverage("sa:TST", "2025-12-31", "fy", "financial",
                                            datetime(2026, 3, 3, tzinfo=timezone.utc))
        self.assertEqual((stale["freshness_status"], stale["age_seconds"]), ("stale", 172800))
        self.store.apply_metric_pack("sector", "Energy", [{
            "metric_key": "hydrocarbon_production", "display_name": "Hydrocarbon production",
            "category": "operational", "default_unit": "boe/day", "period_kind": "fy",
            "requirement": "recommended",
        }])
        energy = self.store.refresh_coverage("sa:TST", "2025-12-31", "fy", "operational")
        self.assertEqual((energy["expected_count"], energy["status"]), (1, "missing"))

    def test_company_backlog_tracks_empty_domains_and_is_queryable(self):
        result = self.store.refresh_company_backlog("sa:TST")
        self.assertEqual(result["created"], 6)
        self.assertGreater(result["open"], 6)
        self.assertGreaterEqual(result["catalog_expected"], 300)
        self.assertGreater(result["catalog_populated"], 0)
        query = FinancialQueryService(self.path)
        items = query.backlog("SA", "TST")
        query.close()
        self.assertIn("domain_backfill", {item["item_type"] for item in items})
        self.assertIn("catalog_backfill", {item["item_type"] for item in items})
        self.assertIn("financial", {item["domain"] for item in items})

    def test_commercial_catalog_has_core_and_oil_gas_layers(self):
        catalog_count=self.db.conn.execute("SELECT count(*) FROM data_catalog_fields WHERE enabled=1").fetchone()[0]
        oil_count=self.db.conn.execute("SELECT count(*) FROM data_catalog_fields WHERE pack_key='oil_gas_v1'").fetchone()[0]
        self.assertGreaterEqual(catalog_count,300)
        self.assertGreaterEqual(oil_count,40)
        with self.db.conn:
            self.db.conn.execute("UPDATE companies SET industry='Integrated Oil & Gas' WHERE company_id='sa:TST'")
        result=self.store.refresh_catalog_completeness("sa:TST")
        categories={row["category"] for row in result["categories"]}
        self.assertIn("company_model",categories)
        self.assertIn("oil_gas_operations",categories)
        query=FinancialQueryService(self.path)
        completeness=query.completeness("SA","TST"); query.close()
        self.assertEqual(completeness["expected_fields"],result["expected"])


if __name__ == "__main__":
    unittest.main()
