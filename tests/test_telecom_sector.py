"""Acceptance tests for the four-company Saudi telecommunications universe.

Covers stc (7010), Mobily (7020), Zain KSA (7030), and Etihad Atheeb/GO
(7040). Source-specific assertions remain below for each completed issuer batch.
"""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.bootstrap import rebuild_snapshot
from finengine.catalog import iter_catalog_fields
from finengine.query import FinancialQueryService
from finengine.verification import ManifestVerifier

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_IMPORTS = REPO_ROOT / "data" / "imports"
TELECOM_SYMBOLS = ("7010", "7020", "7030", "7040")
TELECOM_COMPANY_IDS = tuple(f"sa:{symbol}" for symbol in TELECOM_SYMBOLS)
TELECOM_SYMBOLS_WITH_INDUSTRY_CONTEXT = ("7010", "7020", "7030")


class TelecomManifestVerificationTests(unittest.TestCase):
    def test_telecom_catalog_uses_typed_units_and_periods(self):
        fields = {item["field_key"]: item for item in iter_catalog_fields()}
        self.assertEqual(fields["mobile_subscribers"]["default_unit"], "count")
        self.assertEqual(fields["mobile_subscribers"]["allowed_period_kinds"], ("instant",))
        self.assertEqual(fields["five_g_coverage"]["default_unit"], "ratio")
        self.assertEqual(fields["network_capex"]["default_unit"], "currency")
        self.assertIn("fy", fields["network_capex"]["allowed_period_kinds"])

    def test_stc_manifest_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("stc-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 15)

    def test_zain_ksa_manifest_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("zain-ksa-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 15)

    def test_mobily_manifest_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("mobily-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 2)

    def test_go_telecom_manifest_has_no_identity_failures(self):
        report = ManifestVerifier(REPO_IMPORTS).verify("go-telecom-")
        self.assertEqual(report["failures"], 0, report["detail"])
        self.assertEqual(report["unmapped_labels"], [])
        self.assertGreater(report["passed"], 2)

    def test_stc_discontinued_operations_close_the_pre_tax_to_net_bridge(self):
        # 2024 net income includes the ~SAR 14.0bn discontinued-ops gain from the
        # TAWAL / DIC disposals; the identity must accept it as the optional
        # third component instead of failing the pre-tax -> net bridge.
        report = ManifestVerifier(REPO_IMPORTS).verify("stc-")
        bridge = [
            c for c in report["detail"]
            if c["check"].startswith("income_statement: pre-tax income - tax")
            and c["period"].startswith("2024")
        ]
        self.assertTrue(bridge, report["detail"])
        self.assertTrue(all(c["status"] == "pass" for c in bridge), bridge)


class TelecomSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "telecom.sqlite3")
        cls.summary = rebuild_snapshot(
            cls.dbpath,
            imports_dir=REPO_IMPORTS,
            registry_path=REPO_ROOT / "config" / "companies.json",
            raw_dir=REPO_ROOT / "data" / "raw",
            replace=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _published(self, company_id):
        return [r for r in self.summary["results"] if r["company_id"] == company_id]

    def test_registry_contains_the_complete_four_company_telecom_universe(self):
        companies = json.loads((REPO_ROOT / "config" / "companies.json").read_text(encoding="utf-8"))
        enabled = {
            row["company_id"] for row in companies
            if row.get("enabled") and row.get("industry") == "Telecommunications"
        }
        self.assertEqual(enabled, set(TELECOM_COMPANY_IDS))

    def test_all_enabled_telecoms_publish_without_errors(self):
        for company_id in TELECOM_COMPANY_IDS:
            rows = self._published(company_id)
            self.assertTrue(rows, f"no manifest published for {company_id}")
            for row in rows:
                self.assertIn(row["status"], {"published", "duplicate"}, row)
                self.assertNotIn("error", row, row)

    def test_official_regulator_industry_context_is_available_where_ingested(self):
        q = FinancialQueryService(self.dbpath)
        try:
            for symbol in TELECOM_SYMBOLS_WITH_INDUSTRY_CONTEXT:
                attributes = q.attributes("SA", symbol)
                self.assertIn("industry_overview", attributes)
                self.assertIn("industry_drivers", attributes)
                self.assertIn("regulatory_environment", attributes)
                self.assertEqual(
                    attributes["industry_overview"]["value"]["internet_penetration"],
                    0.99,
                )
        finally:
            q.close()

    def test_mobily_headline_and_operating_metrics_match_the_annual_report(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "7020", "revenue")
            net_income = q.metric_history("SA", "7020", "net_income")
            subscribers = q.metric_history("SA", "7020", "mobile_subscribers")
            sites = q.metric_history("SA", "7020", "network_sites")
        finally:
            q.close()
        self.assertEqual(_value(revenue, "2025-12-31", scope="consolidated"), Decimal("19641705000"))
        self.assertEqual(_value(net_income, "2025-12-31"), Decimal("3466423000"))
        self.assertEqual(_value(subscribers, "2025-12-31"), Decimal("14400000"))
        self.assertEqual(_value(sites, "2025-12-31"), Decimal("7668"))

    def test_mobily_segment_revenue_reconciles_to_consolidated_revenue(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "7020", "revenue", limit=100)
        finally:
            q.close()
        segments = [row for row in revenue if row["period_end"] == "2025-12-31"
                    and row["scope"] == "segment"]
        self.assertEqual(len(segments), 4)
        self.assertEqual(sum(Decimal(row["value"]) for row in segments), Decimal("19641705000"))

    def test_mobily_company_profile_ownership_and_dividends_are_sourced(self):
        q = FinancialQueryService(self.dbpath)
        try:
            attributes = q.attributes("SA", "7020")
            ownership = q.ownership("SA", "7020")
            actions = q.corporate_actions("SA", "7020")
            disclosures = q.disclosures("SA", "7020")
        finally:
            q.close()
        self.assertEqual(attributes["founding_date"]["value"], "2004")
        self.assertIn("business_segments", attributes)
        self.assertEqual(sum(Decimal(row["ownership_pct"]) for row in ownership), Decimal("1.0000"))
        action_keys = {row["action_key"] for row in actions}
        self.assertTrue({
            "sa:7020:dividend:2024:h2",
            "sa:7020:dividend:2025:h1",
            "sa:7020:dividend:2025:h2",
        }.issubset(action_keys))
        self.assertGreaterEqual(len(actions), 3)
        self.assertGreaterEqual(len(disclosures), 4)

    def test_mobily_four_year_financial_and_twelve_quarter_history_is_available(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "7020", "revenue", limit=50)
        finally:
            q.close()
        annual = {row["period_end"]: Decimal(row["value"])
                  for row in revenue if row["period_kind"] == "fy"}
        quarters = [row for row in revenue if row["period_kind"] == "quarter"]
        self.assertEqual(annual["2021-12-31"], Decimal("14834056000"))
        self.assertEqual(annual["2024-12-31"], Decimal("18206000000"))
        self.assertEqual(len(quarters), 12)

    def test_stc_headline_metrics_match_the_filing(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "7010", "revenue")
            net_income = q.metric_history("SA", "7010", "net_income")
        finally:
            q.close()
        self.assertEqual(_value(revenue, "2025-12-31"), Decimal("77818675000"))
        self.assertEqual(_value(net_income, "2025-12-31"), Decimal("15134945000"))

    def test_stc_network_history_is_available_from_official_reports(self):
        q = FinancialQueryService(self.dbpath)
        try:
            coverage = q.metric_history("SA", "7010", "five_g_coverage", limit=20)
            subscribers = q.metric_history("SA", "7010", "mobile_subscribers", limit=20)
        finally:
            q.close()
        self.assertEqual(_value(coverage, "2021-12-31"), Decimal("0.3775"))
        self.assertEqual(_value(coverage, "2025-12-31"), Decimal("0.63"))
        self.assertEqual(_value(subscribers, "2025-12-31"), Decimal("30000000"))

    def test_stc_five_year_financial_and_2025_quarterly_history_is_available(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "7010", "revenue", limit=50)
        finally:
            q.close()
        annual = {row["period_end"]: Decimal(row["value"]) for row in revenue if row["period_kind"] == "fy"}
        quarters = [row for row in revenue if row["period_kind"] == "quarter"]
        self.assertEqual(annual["2020-12-31"], Decimal("58953318000"))
        self.assertEqual(annual["2025-12-31"], Decimal("77818675000"))
        quarters = sorted(quarters, key=lambda r: r["period_end"])
        self.assertGreaterEqual(len(quarters), 12)
        self.assertEqual(quarters[-12]["period_end"], "2023-03-31")
        self.assertEqual(quarters[-1]["period_end"], "2025-12-31")
        self.assertEqual(Decimal(quarters[-1]["value"]), Decimal("19894000000"))

    def test_stc_company_profile_ownership_dividend_and_governance_are_sourced(self):
        q = FinancialQueryService(self.dbpath)
        try:
            attributes = q.attributes("SA", "7010")
            ownership = q.ownership("SA", "7010")
            actions = q.corporate_actions("SA", "7010")
            disclosures = q.disclosures("SA", "7010")
        finally:
            q.close()
        self.assertEqual(sum(Decimal(row["ownership_pct"]) for row in ownership), Decimal("1.0000"))
        self.assertEqual(attributes["chairman"]["value"], "HRH Prince Mohammed Khalid Al-Faisal")
        self.assertIn("board_of_directors", attributes)
        self.assertIn("dividend_policy", attributes)
        self.assertEqual(Decimal(actions[0]["cash_amount"]), Decimal("21000000000"))
        self.assertGreaterEqual(len(disclosures), 8)

    def test_stc_company_profile_and_ownership_are_sourced(self):
        q = FinancialQueryService(self.dbpath)
        try:
            attributes = q.attributes("SA", "7010")
            ownership = q.ownership("SA", "7010")
            disclosures = q.disclosures("SA", "7010")
        finally:
            q.close()
        self.assertEqual(attributes["isin"]["value"], "SA0007879543")
        self.assertEqual(attributes["shares_outstanding"]["value"], 5000000000)
        self.assertEqual(sum(Decimal(row["ownership_pct"]) for row in ownership), Decimal("1.0000"))
        self.assertGreaterEqual(len(disclosures), 4)

    def test_zain_ksa_headline_metrics_match_the_filing(self):
        q = FinancialQueryService(self.dbpath)
        try:
            revenue = q.metric_history("SA", "7030", "revenue")
            net_income = q.metric_history("SA", "7030", "net_income")
            equity = q.metric_history("SA", "7030", "total_equity")
        finally:
            q.close()
        self.assertEqual(_value(revenue, "2025-12-31"), Decimal("10983264000"))
        self.assertEqual(_value(net_income, "2025-12-31"), Decimal("603873000"))
        self.assertEqual(_value(equity, "2025-12-31"), Decimal("10875951000"))

    def test_zain_ksa_five_year_customer_and_arpu_history_is_available(self):
        q = FinancialQueryService(self.dbpath)
        try:
            subscribers = q.metric_history("SA", "7030", "mobile_subscribers", limit=20)
            arpu = q.metric_history("SA", "7030", "arpu", limit=20)
        finally:
            q.close()
        self.assertEqual(_value(subscribers, "2021-12-31"), Decimal("8027000"))
        self.assertEqual(_value(subscribers, "2025-12-31"), Decimal("8100000"))
        self.assertEqual(_value(arpu, "2021-12-31"), Decimal("19"))
        self.assertEqual(_value(arpu, "2025-12-31"), Decimal("17"))

    def test_zain_ksa_profile_ownership_and_dividend_are_sourced(self):
        q = FinancialQueryService(self.dbpath)
        try:
            attributes = q.attributes("SA", "7030")
            ownership = q.ownership("SA", "7030")
            actions = q.corporate_actions("SA", "7030")
            disclosures = q.disclosures("SA", "7030")
        finally:
            q.close()
        self.assertEqual(attributes["founding_date"]["value"], "2008-08-26")
        self.assertEqual(sum(Decimal(row["ownership_pct"]) for row in ownership), Decimal("1.0000"))
        self.assertEqual(len(actions), 4)
        self.assertGreaterEqual(len(disclosures), 4)

    def test_derived_margins_are_reasonable_for_both_operators(self):
        q = FinancialQueryService(self.dbpath)
        try:
            for symbol, lo, hi in (("7010", Decimal("0.10"), Decimal("0.35")),
                                   ("7030", Decimal("0.03"), Decimal("0.10"))):
                margin = _value(q.metric_history("SA", symbol, "net_margin"), "2025-12-31")
                self.assertIsNotNone(margin, f"{symbol} net_margin missing")
                self.assertTrue(lo <= margin <= hi, f"{symbol} net_margin {margin}")
        finally:
            q.close()


def _value(history, period_end, scope=None):
    for row in history:
        if row["period_end"] == period_end and (scope is None or row["scope"] == scope):
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
