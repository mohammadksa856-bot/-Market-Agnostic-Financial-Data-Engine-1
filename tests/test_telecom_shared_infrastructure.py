import json
import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.factory import FactoryOrchestrator
from finengine.models import Company, Market
from finengine.registry import CompanyRegistry


TELECOM_SYMBOLS = ["7010", "7020", "7030", "7040"]


class SaudiSymbolResolutionTests(unittest.TestCase):
    """Any spelling of a Saudi telecom symbol must resolve to the same company.

    The Saudi Exchange historical-reports selector, third-party feeds and
    operator payloads spell the same instrument differently: bare ("7010"),
    zero-padded ("07010") or market-prefixed ("SA7010"). `CompanyRegistry`
    is the single place company/job code resolves a market+symbol pair, so
    it must accept all three spellings for each of the four listed telecom
    operators without ever matching a symbol whose digits genuinely differ.
    """

    def setUp(self):
        self.registry = CompanyRegistry([
            Company(f"sa:{symbol}", Market.SA, symbol, f"Telecom {symbol}", "SAR",
                    sector="Telecommunication Services")
            for symbol in TELECOM_SYMBOLS
        ])

    def test_bare_symbol_resolves(self):
        for symbol in TELECOM_SYMBOLS:
            with self.subTest(symbol=symbol):
                self.assertEqual(self.registry.resolve("SA", symbol).symbol, symbol)

    def test_zero_padded_symbol_resolves_to_the_same_company(self):
        for symbol in TELECOM_SYMBOLS:
            with self.subTest(symbol=symbol):
                padded = "0" + symbol
                self.assertEqual(self.registry.resolve("SA", padded).symbol, symbol)

    def test_market_prefixed_symbol_resolves_to_the_same_company(self):
        for symbol in TELECOM_SYMBOLS:
            with self.subTest(symbol=symbol):
                prefixed = f"SA{symbol}"
                self.assertEqual(self.registry.resolve("SA", prefixed).symbol, symbol)

    def test_lowercase_market_and_mixed_padding_still_resolve(self):
        self.assertEqual(self.registry.resolve("sa", "sa07010").symbol, "7010")

    def test_digits_that_do_not_match_any_company_are_rejected(self):
        with self.assertRaises(KeyError):
            self.registry.resolve("SA", "9999")
        with self.assertRaises(KeyError):
            self.registry.resolve("SA", "SA09999")
        with self.assertRaises(KeyError):
            self.registry.resolve("SA", "issuer-7010-copy")

    def test_non_saudi_market_never_falls_back_to_digit_matching(self):
        registry = CompanyRegistry(self.registry.all() + [
            Company("us:7010", Market.US, "7010", "US Ticker 7010", "USD"),
        ])
        # An exact match still wins over the fallback path.
        self.assertEqual(registry.resolve("US", "7010").company_id, "us:7010")
        # A US-market lookup for a padded/prefixed spelling must not silently
        # borrow the Saudi digit-matching fallback.
        with self.assertRaises(KeyError):
            registry.resolve("US", "SA7010")


class FactoryThroughputReportingTests(unittest.TestCase):
    """Throughput must reflect completed work, never queue depth."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "factory.sqlite3"
        Database(self.db_path).close()

    def tearDown(self):
        self.temp.cleanup()

    def test_throughput_report_shape_and_zero_state_is_honest(self):
        db = Database(self.db_path)
        try:
            db.register_company(Company(
                "sa:TST", Market.SA, "TST", "Test Company", "SAR",
                sector="Telecommunication Services",
                sources=("https://issuer.example.test/investors",),
            ))
            factory = FactoryOrchestrator(db)
            run_id = factory.plan(market="SA", symbols=["TST"])["run_id"]
            report = factory.throughput(run_id)
            self.assertEqual(report["companies_attempted"], 1)
            # No work has finished yet, so nothing should be reported as
            # completed and no throughput rate should be fabricated.
            self.assertEqual(report["companies_reaching_target"], 0)
            self.assertEqual(report["companies_completed_in_window"], 0)
            self.assertIsNone(report["estimated_sustainable_daily_throughput"])
            self.assertIn("top_blocking_categories", report)
            factory.dispatch(run_id, limit=10)
            report_after_dispatch = factory.throughput(run_id)
            # Dispatch alone (no finished jobs) must not be reported as
            # completed throughput either.
            self.assertEqual(report_after_dispatch["companies_reaching_target"], 0)
            self.assertEqual(report_after_dispatch["companies_blocked"], 0)
        finally:
            db.close()

    def test_window_must_be_positive(self):
        db = Database(self.db_path)
        try:
            with self.assertRaises(ValueError):
                FactoryOrchestrator(db).throughput(window_hours=0)
        finally:
            db.close()

    def test_legacy_run_status_remains_readable_after_contract_migration(self):
        db = Database(self.db_path)
        try:
            db.register_company(Company(
                "sa:TST", Market.SA, "TST", "Test Company", "SAR",
                sector="Telecommunication Services",
            ))
            with db.conn:
                db.conn.execute(
                    "INSERT INTO factory_runs(run_id,scope_json,target_score,total_items) "
                    "VALUES('legacy-run','{}','95',1)"
                )
                db.conn.execute(
                    """INSERT INTO factory_work_items(
                    work_item_id,run_id,company_id,category_key,state
                    ) VALUES('legacy-item','legacy-run','sa:TST','identity','queued')"""
                )
            status = FactoryOrchestrator(db).status("legacy-run")
            self.assertEqual(status["scoring_model"], "legacy_investor_understanding")
            self.assertEqual(status["companies"][0]["categories_total"], 1)
        finally:
            db.close()


class ConsensusGovernanceCannotInflateReadinessTests(unittest.TestCase):
    """Missing consensus must stay visible inside the contract's valuation category."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "factory.sqlite3"
        Database(self.db_path).close()

    def tearDown(self):
        self.temp.cleanup()

    def test_zero_consensus_does_not_create_a_fake_analyst_category_or_completion(self):
        db = Database(self.db_path)
        try:
            db.register_company(Company(
                "sa:TST", Market.SA, "TST", "Test Company", "SAR",
                sector="Telecommunication Services",
                sources=("https://issuer.example.test/investors",),
            ))
            factory = FactoryOrchestrator(db)
            run_id = factory.plan(market="SA", symbols=["TST"])["run_id"]

            row = db.conn.execute(
                "SELECT state,gap_snapshot_json FROM factory_work_items "
                "WHERE run_id=? AND category_key='valuation'", (run_id,),
            ).fetchone()
            self.assertEqual(row["state"], "queued")
            snapshot = json.loads(row["gap_snapshot_json"])
            self.assertEqual(snapshot["strategy"], "deterministic_refresh")
            self.assertEqual(snapshot["contract_job_strategy"], "calculated_no_network")
            self.assertNotEqual(snapshot["score_before"], "1")
            self.assertEqual(db.conn.execute(
                "SELECT count(*) FROM factory_work_items WHERE run_id=? AND category_key='analysts'",
                (run_id,),
            ).fetchone()[0], 0)

            factory.dispatch(run_id, limit=10)
            valuation = db.conn.execute(
                "SELECT state FROM factory_work_items "
                "WHERE run_id=? AND category_key='valuation'", (run_id,),
            ).fetchone()
            self.assertEqual(valuation["state"], "running")

            status = factory.status(run_id)
            company_row = status["companies"][0]
            self.assertEqual(status["scoring_model"], "factory_18_category_contract")
            self.assertLess(company_row["categories_complete"], company_row["categories_total"])
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
