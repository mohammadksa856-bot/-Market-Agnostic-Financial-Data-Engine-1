import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.canonicalization import (
    CanonicalProjector,
    NON_PROJECTABLE_PRESENTATION_FIELDS,
)
from finengine.database import Database
from finengine.domains import CompanyDomainStore
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument
from finengine.pipeline import Pipeline
from finengine.query import FinancialQueryService


class PayloadConnector:
    def __init__(self, payload, key="fixture:canonical-projections"):
        self.content = json.dumps(payload).encode()
        self.key = key

    def fetch(self, company):
        return SourceDocument(
            company.company_id,
            company.market,
            "fixture://audited-notes",
            self.key,
            "Annual financial statement notes",
            "2026-03-10",
            self.content,
        )


def raw_fact(metric, value, *, kind=PeriodKind.INSTANT, dimensions=None, scope="consolidated"):
    return Fact(
        "sa:TST",
        metric,
        Decimal(str(value)),
        "SAR",
        "SAR",
        "2025-01-01" if kind == PeriodKind.FY else None,
        "2025-12-31",
        kind,
        2025,
        None,
        "fixture:source",
        "fixture://source",
        "2026-03-10",
        scope=scope,
        dimensions=dimensions or {},
    )


class CanonicalProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "financial.sqlite3")
        self.db = Database(self.path)
        self.company = Company(
            "sa:TST", Market.SA, "TST", "Projection Test", "SAR",
            sector="Energy", industry="Integrated Oil & Gas",
        )

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_pipeline_materializes_only_reconciled_canonical_projections(self):
        instant = lambda metric, value, dimensions=None: {
            "metric": metric, "value": value, "currency": "SAR", "unit": "SAR",
            "period_end": "2025-12-31", "period_kind": "instant", "fiscal_year": 2025,
            "dimensions": dimensions or {},
        }
        annual = lambda metric, value, dimensions=None, scope="consolidated": {
            "metric": metric, "value": value, "currency": "SAR", "unit": "SAR",
            "period_start": "2025-01-01", "period_end": "2025-12-31",
            "period_kind": "fy", "fiscal_year": 2025, "scope": scope,
            "dimensions": dimensions or {},
        }
        facts = [
            instant("property_plant_equipment", 100),
            instant("property_plant_equipment_by_class", 10, {"asset_class": "Land and land improvements"}),
            instant("property_plant_equipment_by_class", 15, {"asset_class": "Buildings"}),
            instant("property_plant_equipment_by_class", 25, {"asset_class": "Oil and gas properties"}),
            instant("property_plant_equipment_by_class", 30, {"asset_class": "Plant machinery and equipment"}),
            instant("property_plant_equipment_by_class", 20, {"asset_class": "Construction in progress"}),
            instant("current_debt", 20),
            instant("long_term_debt", 80),
            instant("borrowings_by_instrument", 30, {"instrument": "Bank borrowings"}),
            instant("borrowings_by_instrument", 40, {"instrument": "Debentures"}),
            instant("borrowings_by_instrument", 30, {"instrument": "Sukuk"}),
            instant("expected_credit_losses", 2, {
                "asset_class": "Trade receivables", "measure": "Loss allowance",
            }),
            instant("related_party_receivables", 6, {
                "counterparty_type": "Joint ventures", "balance_type": "Trade receivables",
            }),
            instant("related_party_payables", 4, {"counterparty_type": "Joint ventures"}),
            annual("depreciation_amortization", -30),
            annual("depreciation_by_ppe_class", 25, {"asset_class": "Plant machinery and equipment"}),
            annual("intangible_amortization_by_class", 5, {"asset_class": "Computer software"}),
            annual("revenue", 100),
            annual("other_income_related_to_sales", 5),
            annual("revenue_and_other_income_related_to_sales", 105),
            annual("upstream_revenue", 60, {"segment": "Upstream"}, "segment"),
            annual("upstream_ebit", 35, {"segment": "Upstream"}, "segment"),
            annual("upstream_ebitda", 40, {"segment": "Upstream"}, "segment"),
            annual("upstream_capex", 12, {"segment": "Upstream"}, "segment"),
            annual("upstream_depreciation_amortization", -5, {"segment": "Upstream"}, "segment"),
        ]
        result = Pipeline(self.db, Path(self.temp.name) / "raw").run(
            self.company, PayloadConnector({"facts": facts}),
        )
        self.assertEqual(result["status"], "published")
        self.assertGreaterEqual(result["canonical_projections"], 18)

        expected = {
            "land": "10", "buildings": "15", "oil_gas_properties": "25",
            "machinery_equipment": "30", "construction_in_progress": "20",
            "bank_loans": "30", "bonds_sukuk": "70",
            "depreciation_expense": "-25", "amortization_expense": "-5",
            "revenue_ex_other_income": "100", "allowance_doubtful_accounts": "2",
        }
        rows = self.db.conn.execute(
            "SELECT metric_key,value_decimal FROM data_points WHERE company_id='sa:TST' "
            "AND is_current=1 AND metric_key IN (%s)" % ",".join("?" for _ in expected),
            tuple(expected),
        ).fetchall()
        self.assertEqual({row["metric_key"]: row["value_decimal"] for row in rows}, expected)

        segment = self.db.conn.execute(
            """SELECT metric_key,value_decimal,dimensions_json FROM data_points
            WHERE company_id='sa:TST' AND is_current=1 AND metric_key LIKE 'segment_%'
            ORDER BY metric_key"""
        ).fetchall()
        self.assertEqual(
            {row["metric_key"] for row in segment},
            {"segment_revenue", "segment_ebit", "segment_ebitda", "segment_capex",
             "segment_depreciation_amortization"},
        )
        self.assertTrue(all(json.loads(row["dimensions_json"]) == {"segment": "Upstream"}
                            for row in segment))
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM data_points WHERE company_id='sa:TST' AND is_current=1 "
            "AND metric_key IN ('gross_profit','cost_of_revenue','ppe_purchases',"
            "'intangible_asset_purchases','joint_venture_investments')"
        ).fetchone()[0], 0)

        query = FinancialQueryService(self.path)
        try:
            bond = query.metric_history("SA", "TST", "bonds_sukuk")[0]
        finally:
            query.close()
        self.assertTrue(bond["is_calculated"])
        self.assertIn("reconciled", bond["calculation"])
        self.assertEqual(
            bond["provenance"]["derivation"]["definition"]["period_rule"],
            "same_period_after_total_debt_reconciliation",
        )

    def test_unreconciled_components_and_mismatched_segment_are_not_projected(self):
        facts = [
            raw_fact("property_plant_equipment", 100),
            raw_fact("property_plant_equipment_by_class", 90,
                     dimensions={"asset_class": "Land and land improvements"}),
            raw_fact("current_debt", 20),
            raw_fact("long_term_debt", 80),
            raw_fact("borrowings_by_instrument", 90,
                     dimensions={"instrument": "Bank borrowings"}),
            raw_fact("depreciation_amortization", -30, kind=PeriodKind.FY),
            raw_fact("depreciation_by_ppe_class", 20, kind=PeriodKind.FY,
                     dimensions={"asset_class": "Buildings"}),
            raw_fact("intangible_amortization_by_class", 5, kind=PeriodKind.FY,
                     dimensions={"asset_class": "Computer software"}),
            raw_fact("upstream_revenue", 60, kind=PeriodKind.FY,
                     dimensions={"segment": "Downstream"}, scope="segment"),
        ]
        projected = CanonicalProjector().project(facts)
        metrics = {fact.metric for fact in projected}
        self.assertFalse({
            "land", "bank_loans", "bonds_sukuk", "depreciation_expense",
            "amortization_expense", "segment_revenue",
        } & metrics)
        self.assertFalse(NON_PROJECTABLE_PRESENTATION_FIELDS & metrics)

    def test_reported_canonical_value_wins_over_a_projection(self):
        facts = [
            raw_fact("property_plant_equipment", 10),
            raw_fact("property_plant_equipment_by_class", 10,
                     dimensions={"asset_class": "Land and land improvements"}),
            raw_fact("land", 9),
        ]
        self.assertNotIn("land", {fact.metric for fact in CanonicalProjector().project(facts)})

    def test_completeness_refresh_backfills_a_legacy_persistent_database(self):
        self.db.register_company(self.company)
        document = SourceDocument(
            self.company.company_id, self.company.market, "fixture://legacy-note",
            "fixture:source", "Annual financial statement notes", "2026-03-10", b"{}",
        )
        self.db.save_source(document, "legacy-note", None)
        self.db.publish_batch([
            raw_fact("property_plant_equipment", 100),
            raw_fact("property_plant_equipment_by_class", 100,
                     dimensions={"asset_class": "Land and land improvements"}),
        ])
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM data_points WHERE metric_key='land'"
        ).fetchone()[0], 0)
        CompanyDomainStore(self.db).refresh_catalog_completeness(self.company.company_id)
        row = self.db.conn.execute(
            "SELECT value_decimal,is_calculated FROM data_points "
            "WHERE metric_key='land' AND is_current=1"
        ).fetchone()
        self.assertEqual((row["value_decimal"], row["is_calculated"]), ("100", 1))
        # A second refresh is idempotent and does not create another version.
        CompanyDomainStore(self.db).refresh_catalog_completeness(self.company.company_id)
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM data_points WHERE metric_key='land'"
        ).fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
