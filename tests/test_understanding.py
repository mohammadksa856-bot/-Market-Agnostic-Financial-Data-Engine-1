import tempfile
import unittest
import json
from decimal import Decimal
from pathlib import Path

from finengine.database import Database
from finengine.domains import CompanyDomainStore
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument
from finengine.query import FinancialQueryService
from finengine.understanding import refresh_all_understanding, refresh_company_understanding


class UnderstandingModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "understanding.sqlite3")
        self.db = Database(self.path)
        self.db.register_company(Company(
            "sa:TST", Market.SA, "TST", "Test Company", "SAR",
            isin="SA0000000001", exchange="Saudi Exchange", country="SA",
            sector="Materials", industry="Chemicals", timezone="Asia/Riyadh",
        ))
        self.db.save_source(SourceDocument(
            "sa:TST", Market.SA, "https://example.test/annual.pdf", "src:annual",
            "annual-report", "2026-03-01", b"annual report",
            "application/pdf", {"source_authority": "issuer_ir"},
        ), "annual", None)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_18_categories_and_governed_sources_are_seeded(self):
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM knowledge_categories").fetchone()[0], 18)
        self.assertEqual(self.db.conn.execute(
            "SELECT sum(weight) FROM knowledge_categories").fetchone()[0], 100)
        classes = {r[0] for r in self.db.conn.execute(
            "SELECT DISTINCT source_class FROM source_authorities")}
        self.assertEqual(classes, {"P", "C", "O", "S"})
        self.assertGreater(self.db.conn.execute(
            "SELECT count(*) FROM category_source_rules").fetchone()[0], 18)

    def test_refresh_is_honest_about_missing_data_and_queryable(self):
        result = refresh_company_understanding(self.db.conn, "sa:TST")
        self.assertEqual(len(result["categories"]), 18)
        self.assertEqual(result["target_score"], "95")
        self.assertEqual(result["source_map_version"], "18-categories-v1")
        self.assertEqual(result["readiness_state"], "not_ready")
        self.assertIn("five_annual_periods", result["blocking_reasons"])
        self.assertIn("weighted_coverage_95", result["blocking_reasons"])
        backlog = self.db.conn.execute(
            """SELECT domain,payload_json FROM backlog_items
            WHERE company_id='sa:TST' AND item_type='understanding_gap'"""
        ).fetchall()
        self.assertEqual(len(backlog), 18)
        financials = next(row for row in backlog if row["domain"] == "financials")
        payload = json.loads(financials["payload_json"])
        self.assertEqual(payload["target_score"], "0.95")
        self.assertEqual(payload["source_map_version"], "18-categories-v1")
        self.assertEqual(payload["source_plan"][0]["source_code"], "audited_statements")
        self.db.close()
        query = FinancialQueryService(self.path)
        try:
            payload = query.understanding("SA", "TST")
            self.assertEqual(len(payload["categories"]), 18)
            self.assertEqual(payload["target_score"], "95")
            self.assertFalse(payload["hard_gates"]["five_annual_periods"]["passed"])
            governance = query.source_governance()
            self.assertEqual(len(governance["sources"]), 9)
        finally:
            query.close()
        self.db = Database(self.path)

    def test_refresh_all_reports_market_states(self):
        result = refresh_all_understanding(self.db.conn, "SA")
        self.assertEqual(result["companies"], 1)
        self.assertEqual(result["states"], {"not_ready": 1})

    def test_industry_score_counts_reviewed_classification_without_claiming_full_context(self):
        result = refresh_company_understanding(self.db.conn, "sa:TST")
        industry = next(item for item in result["categories"]
                        if item["category_key"] == "industry")
        self.assertEqual(industry["score"], "0.4")
        self.assertEqual(industry["evidence"]["classification_fields"], 2)

    def test_competitor_coverage_uses_reviewed_sector_when_exact_industry_has_no_peers(self):
        peer = Company(
            "sa:PEER", Market.SA, "PEER", "Fertilizer Peer", "SAR",
            sector="Materials", industry="Fertilizers",
        )
        self.db.register_company(peer)
        peer_source = SourceDocument(
            peer.company_id, peer.market, "https://example.test/peer.pdf", "src:peer",
            "annual-report", "2026-03-01", b"peer report",
            "application/pdf", {"source_authority": "issuer_ir"},
        )
        self.db.save_source(peer_source, "peer", None)
        for company_id, source_key, source_url, value in (
            ("sa:TST", "src:annual", "https://example.test/annual.pdf", "0.10"),
            ("sa:PEER", "src:peer", "https://example.test/peer.pdf", "0.20"),
        ):
            self.db.publish(Fact(
                company_id, "net_margin", Decimal(value), "ratio", "ratio",
                "2025-01-01", "2025-12-31", PeriodKind.FY, 2025, None,
                source_key, source_url, "2026-03-01",
            ))

        result = refresh_company_understanding(self.db.conn, "sa:TST")
        competitors = next(item for item in result["categories"]
                           if item["category_key"] == "competitors")
        evidence = competitors["evidence"]
        self.assertEqual(evidence["inferred_peers_with_ratio_data"], 1)
        self.assertEqual(evidence["classified_peer_universe"], 1)
        self.assertEqual(evidence["required_peer_count"], 1)
        self.assertEqual(evidence["peer_scope"]["field"], "sector")
        self.assertEqual(evidence["peer_scope"]["value"], "Materials")
        self.assertEqual(evidence["peer_scope"]["fallback_from"]["field"], "industry")
        self.assertEqual(evidence["classification_basis"],
                         "inferred_peer_not_issuer_declared_competitor")
        self.assertGreater(Decimal(competitors["score"]), Decimal(0))

    def test_forecast_score_counts_only_reviewed_forward_looking_guidance(self):
        self.db.publish_disclosure(
            "sa:TST", "guidance", "Declared dividend", "The board declared a dividend.",
            "2026-03-01", "src:annual", "2025-12-31", metadata={},
        )
        self.db.publish_disclosure(
            "sa:TST", "guidance", "Capacity target", "Capacity is targeted for 2030.",
            "2026-03-01", "src:annual", "2025-12-31",
            metadata={"forward_looking": True, "analyst_forecast": False,
                      "issuer_reported": True},
        )
        result = refresh_company_understanding(self.db.conn, "sa:TST")
        forecasts = next(item for item in result["categories"]
                         if item["category_key"] == "forecasts")
        self.assertEqual(forecasts["score"], "0.1")

    def test_reconciled_corporate_strategic_and_public_ownership_is_complete(self):
        store = CompanyDomainStore(self.db)
        store.publish_ownership_position(
            "sa:TST", "strategic_holder", "Strategic Holder", "direct",
            "2025-12-31", "src:annual", ownership_pct=Decimal("0.28"),
            holder_type="corporate_strategic",
        )
        store.publish_ownership_position(
            "sa:TST", "public_float", "Public Float", "free_float",
            "2025-12-31", "src:annual", ownership_pct=Decimal("0.72"),
            holder_type="public",
        )
        result = refresh_company_understanding(self.db.conn, "sa:TST")
        ownership = next(item for item in result["categories"]
                         if item["category_key"] == "ownership")
        self.assertEqual(ownership["score"], "1")
        self.assertTrue(ownership["evidence"]["latest_snapshot_reconciled"])

    def test_esg_score_counts_reviewed_numeric_esg_attributes(self):
        for index in range(8):
            self.db.publish_company_attribute(
                "sa:TST", f"esg_metric_{index}", index, "2025-12-31",
                source_key="src:annual", category="esg_environmental",
                metadata={"source_page": 10 + index},
            )
        result = refresh_company_understanding(self.db.conn, "sa:TST")
        esg = next(item for item in result["categories"] if item["category_key"] == "esg")
        self.assertEqual(esg["score"], "1")
        self.assertEqual(esg["evidence"]["reviewed_attributes"], 8)

    def test_official_risk_disclosure_contributes_to_risk_coverage(self):
        self.db.publish_disclosure(
            "sa:TST", "risk_disclosure", "Principal risks",
            "The issuer identified and described its principal risks and controls.",
            "2026-03-01", "src:annual", "2025-12-31",
            metadata={"source_page": 30},
        )
        result = refresh_company_understanding(self.db.conn, "sa:TST")
        risks = next(item for item in result["categories"] if item["category_key"] == "risks")
        self.assertGreater(Decimal(risks["score"]), Decimal(0))


if __name__ == "__main__":
    unittest.main()
