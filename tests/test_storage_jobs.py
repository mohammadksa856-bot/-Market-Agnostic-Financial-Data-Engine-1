import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from finengine.calculations import Calculator
from finengine.database import Database
from finengine.jobs import DurableJobQueue, DurableScheduler
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument
from finengine.query import FinancialQueryService


class StorageAndJobsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "financial.sqlite3")
        self.db = Database(self.path)
        self.company = Company("sa:TST", Market.SA, "TST", "Test Company", "SAR")
        self.db.register_company(self.company)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def source(self, key="source:1"):
        doc = SourceDocument(self.company.company_id, self.company.market, "https://example.test/report",
                             key, "financial-results", "2026-01-01", b"{}")
        self.db.save_source(doc, key.replace(":", ""), None)
        return doc

    def fact(self, source, value, period_end="2025-12-31", kind=PeriodKind.FY,
             quarter=None, dimensions=None):
        return Fact(self.company.company_id, "revenue", Decimal(value), "SAR", "SAR", "2025-01-01",
                    period_end, kind, 2025, quarter, source.source_key, source.source_url,
                    source.filed_at, dimensions=dimensions or {})

    def test_dimensions_allow_multiple_segments_for_same_metric(self):
        source = self.source()
        states = self.db.publish_batch([
            self.fact(source, "60", dimensions={"segment": "upstream"}),
            self.fact(source, "40", dimensions={"segment": "downstream"}),
        ])
        self.assertEqual(states, ["inserted", "inserted"])
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM data_points").fetchone()[0], 2)

    def test_dimensions_are_governed_by_the_master_schema(self):
        source = self.source()
        note_fact = self.fact(source, "60", dimensions={"geography": "Saudi Arabia"})
        note_fact = Fact(**{**note_fact.__dict__, "metric": "revenue_by_geography"})
        self.assertEqual(
            self.db.publish(note_fact),
            "inserted",
        )
        operational = self.fact(source, "40", dimensions={"maturity_band": "one year"})
        operational = Fact(**{**operational.__dict__, "metric": "total_hydrocarbon_production"})
        with self.assertRaisesRegex(ValueError, "dimensions not allowed"):
            self.db.publish(operational)
        with self.assertRaisesRegex(ValueError, "unregistered dimensions"):
            self.db.publish(self.fact(source, "40", dimensions={"random_axis": "x"}))
        wrong_period = self.fact(source, "40")
        wrong_period = Fact(**{**wrong_period.__dict__, "metric": "total_assets"})
        with self.assertRaisesRegex(ValueError, "period kind fy is not allowed"):
            self.db.publish(wrong_period)
        unsupported = self.fact(source, "40")
        unsupported = Fact(**{**unsupported.__dict__, "scope": "free_form_scope"})
        with self.assertRaisesRegex(ValueError, "unsupported fact scope"):
            self.db.publish(unsupported)

    def test_snapshot_never_overwrites_quarter_with_ytd(self):
        source = self.source()
        self.db.publish_batch([
            self.fact(source, "25", kind=PeriodKind.QUARTER, quarter=2),
            self.fact(source, "45", kind=PeriodKind.YTD, quarter=2),
        ])
        query = FinancialQueryService(self.path)
        snapshot = query.snapshot("SA", "TST")
        query.close()
        self.assertEqual({row["period_kind"] for row in snapshot["metrics"]["revenue"]}, {"quarter", "ytd"})

    def test_company_attributes_and_disclosures_are_versioned(self):
        self.assertEqual(self.db.publish_company_attribute("sa:TST", "employee_count", 100, "2025-12-31"), "inserted")
        self.assertEqual(self.db.publish_company_attribute("sa:TST", "employee_count", 110, "2026-12-31"), "restated")
        self.assertEqual(self.db.publish_disclosure("sa:TST", "strategy", "Strategy", "First", "2026-01-01"), "inserted")
        self.assertEqual(self.db.publish_disclosure("sa:TST", "strategy", "Strategy", "Updated", "2026-02-01"), "restated")
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM company_attributes WHERE is_current=1").fetchone()[0], 1)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM disclosures WHERE is_current=1").fetchone()[0], 1)

    def test_job_queue_is_idempotent_and_audited(self):
        queue = DurableJobQueue(self.db)
        first, created = queue.enqueue("ingest", {"market": "SA"}, "sa:TST", idempotency_key="ingest:1")
        second, duplicate = queue.enqueue("ingest", {"market": "SA"}, "sa:TST", idempotency_key="ingest:1")
        self.assertTrue(created); self.assertFalse(duplicate); self.assertEqual(first, second)
        job = queue.claim("worker-1")
        self.assertIsNotNone(job)
        queue.complete(job, {"status": "published"})
        row = self.db.conn.execute("SELECT status,attempts FROM jobs WHERE job_id=?", (first,)).fetchone()
        self.assertEqual((row["status"], row["attempts"]), ("succeeded", 1))
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM job_attempts").fetchone()[0], 1)

    def test_scheduler_materializes_only_one_due_job(self):
        queue = DurableJobQueue(self.db); scheduler = DurableScheduler(self.db, queue)
        due = datetime(2026, 1, 1, tzinfo=timezone.utc)
        scheduler.upsert("daily:TST", "Daily Test", "ingest", 3600, {"symbol": "TST"}, "sa:TST", next_run_at=due)
        self.assertEqual(len(scheduler.tick(due)), 1)
        self.assertEqual(len(scheduler.tick(due)), 0)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)

    def _bank_fact(self, metric, value, kind, source):
        return Fact(self.company.company_id, metric, Decimal(value), "SAR", "SAR",
                    "2025-01-01" if kind == PeriodKind.FY else None, "2025-12-31", kind, 2025,
                    None, source.source_key, source.source_url, source.filed_at, dimensions={})

    def test_bank_ratios_are_computed_not_ingested(self):
        source = self.source()
        current_year = [
            self._bank_fact("net_financing_income", "29845671000", PeriodKind.FY, source),
            self._bank_fact("total_operating_income", "39093965000", PeriodKind.FY, source),
            self._bank_fact("operating_expense_banking", "-9126988000", PeriodKind.FY, source),
            self._bank_fact("provision_expense", "-2320481000", PeriodKind.FY, source),
            self._bank_fact("net_loans", "752759851000", PeriodKind.INSTANT, source),
            self._bank_fact("customer_deposits", "667287500000", PeriodKind.INSTANT, source),
            self._bank_fact("bank_investments", "174304596000", PeriodKind.INSTANT, source),
            self._bank_fact("due_from_banks", "26940586000", PeriodKind.INSTANT, source),
            self._bank_fact("nonperforming_loans", "8000000000", PeriodKind.INSTANT, source),
            self._bank_fact("gross_loans", "761000000000", PeriodKind.INSTANT, source),
            self._bank_fact("credit_loss_allowance", "16000000000", PeriodKind.INSTANT, source),
            self._bank_fact("risk_weighted_assets", "600000000000", PeriodKind.INSTANT, source),
            self._bank_fact("regulatory_capital", "120000000000", PeriodKind.INSTANT, source),
        ]
        prior = [
            Fact(self.company.company_id, m, Decimal(v), "SAR", "SAR", None, "2024-12-31",
                 PeriodKind.INSTANT, 2024, None, source.source_key, source.source_url,
                 source.filed_at, dimensions={})
            for m, v in (("net_loans", "693409723000"),
                         ("bank_investments", "175033587000"),
                         ("due_from_banks", "19529727000"))
        ]
        out = {f.metric: f for f in Calculator().calculate(current_year, prior)}

        self.assertAlmostEqual(float(out["cost_to_income_ratio"].value), 0.23346, places=4)
        self.assertIn("operating_expense_banking", out["cost_to_income_ratio"].calculation)
        self.assertAlmostEqual(float(out["loans_to_deposits_ratio"].value), 1.12809, places=4)
        self.assertAlmostEqual(float(out["nonperforming_loans_ratio"].value), 8000000000 / 761000000000, places=6)
        self.assertAlmostEqual(float(out["nonperforming_loans_coverage"].value), 16000000000 / 8000000000, places=6)
        self.assertAlmostEqual(float(out["capital_adequacy_ratio"].value), 0.20, places=4)
        self.assertIn("net_interest_margin", out)
        self.assertIn("cost_of_risk", out)
        for metric in ("cost_to_income_ratio", "loans_to_deposits_ratio", "nonperforming_loans_ratio",
                       "capital_adequacy_ratio", "net_interest_margin"):
            self.assertTrue(out[metric].is_calculated)
            self.assertEqual(out[metric].unit, "ratio")

    def test_bank_ratios_dormant_for_non_banks(self):
        source = self.source()
        facts = [
            self.fact(source, "100000"),  # revenue
            Fact(self.company.company_id, "net_income", Decimal("20000"), "SAR", "SAR",
                 "2025-01-01", "2025-12-31", PeriodKind.FY, 2025, None, source.source_key,
                 source.source_url, source.filed_at, dimensions={}),
        ]
        metrics = {f.metric for f in Calculator().calculate(facts)}
        self.assertNotIn("cost_to_income_ratio", metrics)
        self.assertNotIn("loans_to_deposits_ratio", metrics)
        self.assertNotIn("nonperforming_loans_ratio", metrics)

    def test_ifrs17_insurance_revenue_supplies_universal_revenue(self):
        source = self.source()
        facts = [
            Fact(self.company.company_id, "insurance_revenue", Decimal("1000"),
                 "SAR", "SAR", "2025-01-01", "2025-12-31", PeriodKind.FY,
                 2025, None, source.source_key, source.source_url, source.filed_at),
            Fact(self.company.company_id, "net_income", Decimal("100"),
                 "SAR", "SAR", "2025-01-01", "2025-12-31", PeriodKind.FY,
                 2025, None, source.source_key, source.source_url, source.filed_at),
        ]
        out = {fact.metric: fact for fact in Calculator().calculate(facts)}
        self.assertEqual(out["revenue"].value, Decimal("1000"))
        self.assertEqual(out["net_margin"].value, Decimal("0.1"))
        self.assertIn("IFRS 17", out["revenue"].calculation)

    def test_composite_scores_are_sector_aware(self):
        source = self.source()

        def fy(metric, value, year):
            return Fact(self.company.company_id, metric, Decimal(value), "SAR", "SAR",
                        f"{year}-01-01", f"{year}-12-31", PeriodKind.FY, year, None,
                        source.source_key, source.source_url, source.filed_at, dimensions={})

        def bs(metric, value, year):
            return Fact(self.company.company_id, metric, Decimal(value), "SAR", "SAR", None,
                        f"{year}-12-31", PeriodKind.INSTANT, year, None, source.source_key,
                        source.source_url, source.filed_at, dimensions={})

        facts = []
        for year, scale in ((2023, "0.9"), (2024, "0.95"), (2025, "1.0")):
            s = Decimal(scale)
            facts += [
                fy("revenue", int(1000 * s), year),
                fy("gross_profit", int(400 * s), year),
                fy("cost_of_revenue", int(-600 * s), year),
                fy("ebit", int(250 * s), year),
                fy("net_income", int(180 * s), year),
                fy("operating_cash_flow", int(220 * s), year),
                fy("capex", int(-60 * s), year),
                fy("selling_general_administrative_expense", int(-90 * s), year),
                fy("depreciation_amortization", int(-50 * s), year),
                bs("total_assets", int(2000 * s), year),
                bs("current_assets", int(700 * s), year),
                bs("current_liabilities", int(300 * s), year),
                bs("property_plant_equipment", int(900 * s), year),
                bs("accounts_receivable", int(150 * s), year),
                bs("retained_earnings", int(500 * s), year),
                bs("total_equity", int(1200 * s), year),
                bs("total_liabilities", int(800 * s), year),
                bs("long_term_debt", int(250 * s), year),
                bs("shares_outstanding", 1000, year),
            ]
        out = {(f.metric, f.fiscal_year): f for f in Calculator().calculate(facts)}

        f_score = out[("piotroski_f_score", 2025)]
        self.assertTrue(0 <= f_score.value <= 9)
        self.assertEqual(f_score.unit, "score")
        self.assertTrue(f_score.is_calculated)
        z = out[("altman_z_score", 2025)]
        self.assertIn("working_capital/total_assets", z.calculation)
        self.assertGreater(z.value, Decimal("2.6"))          # healthy synthetic company
        self.assertIn(("beneish_m_score", 2025), out)
        self.assertIn(("accrual_ratio", 2025), out)

    def test_bank_gets_bank_health_not_f_score(self):
        source = self.source()

        def row(metric, value, year, kind):
            return Fact(self.company.company_id, metric, Decimal(value), "SAR", "SAR",
                        f"{year}-01-01" if kind == PeriodKind.FY else None, f"{year}-12-31",
                        kind, year, None, source.source_key, source.source_url,
                        source.filed_at, dimensions={})

        facts = []
        for year in (2024, 2025):
            facts += [
                row("net_financing_income", "29000000000", year, PeriodKind.FY),
                row("total_operating_income", "39000000000", year, PeriodKind.FY),
                row("operating_expense_banking", "-9000000000", year, PeriodKind.FY),
                row("provision_expense", "-2300000000", year, PeriodKind.FY),
                row("net_income", "24000000000", year, PeriodKind.FY),
                row("operating_cash_flow", "-22000000000", year, PeriodKind.FY),
                row("net_loans", "750000000000", year, PeriodKind.INSTANT),
                row("customer_deposits", "667000000000", year, PeriodKind.INSTANT),
                row("nonperforming_loans", "8000000000", year, PeriodKind.INSTANT),
                row("gross_loans", "760000000000", year, PeriodKind.INSTANT),
                row("credit_loss_allowance", "16000000000", year, PeriodKind.INSTANT),
                row("risk_weighted_assets", "600000000000", year, PeriodKind.INSTANT),
                row("regulatory_capital", "120000000000", year, PeriodKind.INSTANT),
                row("total_assets", "1040000000000", year, PeriodKind.INSTANT),
                row("total_equity", "142000000000", year, PeriodKind.INSTANT),
            ]
        out = {f.metric for f in Calculator().calculate(facts)}
        self.assertIn("bank_health_score", out)
        self.assertNotIn("piotroski_f_score", out)
        self.assertNotIn("altman_z_score", out)
        self.assertNotIn("accrual_ratio", out)      # cash-flow accruals are noise for banks
        self.assertNotIn("beneish_m_score", out)

    def test_ttm_uses_published_history(self):
        for index, (end, value) in enumerate((("2025-03-31", "10"), ("2025-06-30", "20"), ("2025-09-30", "30")), 1):
            source = self.source(f"source:{index}")
            self.db.publish(self.fact(source, value, end, PeriodKind.QUARTER, index))
        current_source = self.source("source:4")
        current = self.fact(current_source, "40", "2025-12-31", PeriodKind.QUARTER, 4)
        history = self.db.quarter_history("sa:TST", Calculator.TTM_FLOWS)
        calculated = Calculator().calculate([current], history)
        ttm = next(f for f in calculated if f.metric == "revenue_ttm")
        self.assertEqual(ttm.value, Decimal("100"))

    def test_ttm_keeps_dimensions_isolated(self):
        source = self.source()
        facts = []
        periods = (
            ("2025-03-31", 1), ("2025-06-30", 2),
            ("2025-09-30", 3), ("2025-12-31", 4),
        )
        for end, quarter in periods:
            facts.extend([
                self.fact(source, "10", end, PeriodKind.QUARTER, quarter,
                          {"segment": "upstream"}),
                self.fact(source, "100", end, PeriodKind.QUARTER, quarter,
                          {"segment": "downstream"}),
            ])
        ttm = [fact for fact in Calculator().calculate(facts) if fact.metric == "revenue_ttm"]
        values = {fact.dimensions["segment"]: fact.value for fact in ttm}
        self.assertEqual(values, {"upstream": Decimal("40"), "downstream": Decimal("400")})


if __name__ == "__main__":
    unittest.main()
