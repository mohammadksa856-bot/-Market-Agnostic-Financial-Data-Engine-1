import json
import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.query import FinancialQueryService
from finengine.registry import CompanyRegistry
from finengine.universe import (
    activate_universe, classify_sec_submission, enrich_activation_batch,
    normalize_saudi_directory_rows, parse_saudi_reference, parse_sec_ticker_exchange,
    promote_activation_batch,
    sync_universe,
)


class UniverseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "universe.sqlite3"
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_sec_snapshot_groups_multiple_tickers_under_one_issuer(self):
        payload = {"fields": ["cik", "name", "ticker", "exchange"], "data": [
            [1, "Example Inc", "EXB", "OTC"],
            [1, "Example Inc", "EXA", "Nasdaq"],
            [2, "Second Corp", "SEC", "NYSE"],
        ]}
        issuers, securities = parse_sec_ticker_exchange(payload)
        self.assertEqual(len(issuers), 2)
        self.assertEqual(len(securities), 3)
        first = next(item for item in issuers if item["authority_id"] == "0000000001")
        self.assertEqual(first["primary_symbol"], "EXA")
        self.assertEqual(sum(item["is_primary"] for item in securities), 2)

    def test_saudi_json_snapshot_is_archived_versioned_and_queryable(self):
        source = self.root / "issuers.json"
        source.write_text(json.dumps({"data": [{
            "issuer_id": "123", "symbol": "1234", "name": "Example Saudi",
            "name_ar": "مثال", "isin": "SA0000000001", "sector": "Energy",
            "market_segment": "Main Market"
        }]}), encoding="utf-8")
        first = sync_universe(self.db, "SA", self.root / "raw", input_path=source,
                              source_url="https://example.test/official")
        second = sync_universe(self.db, "SA", self.root / "raw", input_path=source,
                               source_url="https://example.test/official")
        self.assertEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertTrue(Path(first["local_path"]).is_file())
        query = FinancialQueryService(str(self.db_path))
        try:
            rows = query.universe("SA")
            status = query.universe_status()
        finally: query.close()
        self.assertEqual(rows[0]["symbol"], "1234")
        self.assertEqual(rows[0]["issuer_metadata"]["name_ar"], "مثال")
        self.assertEqual(status["markets"][0]["active_issuers"], 1)
        self.assertEqual(len(status["snapshots"]), 1)

    def test_saudi_csv_requires_identity_fields(self):
        issuers, securities = parse_saudi_reference(
            b"symbol,name,issuer_id\n,Missing,1\n2000,Valid,2\n", ".csv")
        self.assertEqual(len(issuers), 1)
        self.assertEqual(securities[0]["symbol"], "2000")

    def test_public_saudi_directory_normalizes_markets_and_instrument_types(self):
        content = normalize_saudi_directory_rows({
            "M": [
                {"symbol": "2222", "lonaName": "Saudi Arabian Oil Co.",
                 "shortName": "SAUDI ARAMCO", "isinCode": "SA14TG012N13",
                 "companyURL": "/company/2222"},
                {"symbol": "4330", "lonaName": "Riyad REIT Fund",
                 "shortName": "RIYAD REIT", "isinCode": "SA145G523L57"},
            ],
            "S": [{"symbol": "9602", "lonaName": "Yaqeen Capital Co.",
                   "shortName": "YAQEEN", "isinCode": "SA1620K4M113"}],
        })
        payload = json.loads(content)
        self.assertEqual([row["symbol"] for row in payload["data"]],
                         ["2222", "4330", "9602"])
        by_symbol = {row["symbol"]: row for row in payload["data"]}
        self.assertEqual(by_symbol["2222"]["market_segment"], "Main Market")
        self.assertEqual(by_symbol["9602"]["market_segment"],
                         "Nomu - Parallel Market")
        self.assertEqual(by_symbol["4330"]["instrument_type"], "fund")
        self.assertEqual(by_symbol["2222"]["instrument_type"], "company")
        self.assertEqual(by_symbol["2222"]["profile_url"],
                         "https://www.saudiexchange.sa/company/2222")
        issuers, securities = parse_saudi_reference(content, ".json")
        self.assertEqual((len(issuers), len(securities)), (3, 3))
        self.assertEqual(next(s for s in securities if s["symbol"] == "9602")["exchange"],
                         "Saudi Exchange Nomu - Parallel Market")

    def test_saudi_activation_excludes_funds_unless_explicitly_requested(self):
        source = self.root / "saudi.json"
        source.write_bytes(normalize_saudi_directory_rows({"M": [
            {"symbol": "2222", "lonaName": "Saudi Arabian Oil Co.",
             "shortName": "SAUDI ARAMCO", "isinCode": "SA14TG012N13"},
            {"symbol": "4330", "lonaName": "Riyad REIT Fund",
             "shortName": "RIYAD REIT", "isinCode": "SA145G523L57"},
        ]}))
        sync_universe(self.db, "SA", self.root / "raw", input_path=source)
        default = activate_universe(self.db, "SA", limit=10)
        self.assertEqual([row["symbol"] for row in default["companies"]], ["2222"])
        with_funds = activate_universe(self.db, "SA", limit=10, include_funds=True)
        self.assertEqual([row["symbol"] for row in with_funds["companies"]], ["4330"])

    def test_activation_stages_a_bounded_batch_without_schedules(self):
        source = self.root / "sec.json"
        source.write_text(json.dumps({"fields": ["cik", "name", "ticker", "exchange"],
            "data": [[1, "Alpha Inc", "AAA", "Nasdaq"],
                     [2, "Beta Inc", "BBB", "NYSE"]]}), encoding="utf-8")
        sync_universe(self.db, "US", self.root / "raw", input_path=source)
        result = activate_universe(self.db, "US", limit=1)
        self.assertEqual((result["status"], result["count"]), ("staged", 1))
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM schedules").fetchone()[0], 0)
        company = self.db.conn.execute("SELECT cik,enabled FROM companies").fetchone()
        self.assertEqual((company["cik"], company["enabled"]), ("0000000001", 0))
        status = FinancialQueryService(str(self.db_path))
        try:
            batches = status.universe_status()["activation_batches"]
        finally:
            status.close()
        self.assertEqual(batches[0]["staged"], 1)

    def test_enabled_activation_is_scheduled_and_database_resolvable(self):
        source = self.root / "sec.json"
        source.write_text(json.dumps({"fields": ["cik", "name", "ticker", "exchange"],
            "data": [[320193, "Apple Inc", "AAPL", "Nasdaq"]]}), encoding="utf-8")
        sync_universe(self.db, "US", self.root / "raw", input_path=source)
        result = activate_universe(
            self.db, "US", symbols=("AAPL",), enable=True, schedule_every=21600,
            registry_path=str(self.root / "missing.json"),
        )
        self.assertEqual(result["companies"][0]["schedule_id"], "monitor:US:AAPL")
        registry = CompanyRegistry.combined(self.db.conn, self.root / "missing.json")
        self.assertEqual(registry.resolve("US", "AAPL").cik, "0000320193")
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM schedules WHERE enabled=1").fetchone()[0], 1)

        query = FinancialQueryService(str(self.db_path))
        try:
            inventory = query.universe_rollout("US")
        finally:
            query.close()
        self.assertEqual(inventory["total"], 1)
        self.assertEqual(inventory["coverage_warning"],
                         "inventory_membership_is_not_product_coverage")
        operations = inventory["items"][0]["operations"]
        self.assertEqual(operations["readiness_state"], "enabled_awaiting_data")
        self.assertEqual(operations["schedule_id"], "monitor:US:AAPL")
        self.assertEqual(operations["published_points"], 0)

    def test_enabled_saudi_activation_schedules_official_profile_source(self):
        profile_url = "https://www.saudiexchange.sa/company/2010"
        source = self.root / "saudi.json"
        source.write_bytes(normalize_saudi_directory_rows({"M": [{
            "symbol": "2010", "lonaName": "Saudi Basic Industries Corp.",
            "shortName": "SABIC", "isinCode": "SA0007879121",
            "companyURL": profile_url,
        }]}))
        sync_universe(self.db, "SA", self.root / "raw", input_path=source)
        result = activate_universe(
            self.db, "SA", symbols=("2010",), enable=True, schedule_every=21600,
            registry_path=str(self.root / "missing.json"),
        )
        self.assertEqual(result["companies"][0]["schedule_id"], "monitor:SA:2010")
        schedule = self.db.conn.execute(
            "SELECT payload_json FROM schedules WHERE schedule_id='monitor:SA:2010'"
        ).fetchone()
        payload = json.loads(schedule["payload_json"])
        self.assertEqual(payload["source_index"], profile_url)
        self.assertTrue(payload["browser"])
        registry = CompanyRegistry.combined(self.db.conn, self.root / "missing.json")
        self.assertEqual(registry.resolve("SA", "2010").sources, (profile_url,))

    def test_saudi_schedule_without_profile_source_is_rejected_atomically(self):
        source = self.root / "saudi.json"
        source.write_bytes(normalize_saudi_directory_rows({"M": [{
            "symbol": "2010", "lonaName": "Saudi Basic Industries Corp.",
            "shortName": "SABIC", "isinCode": "SA0007879121",
        }]}))
        sync_universe(self.db, "SA", self.root / "raw", input_path=source)
        with self.assertRaisesRegex(ValueError, "missing for: 2010"):
            activate_universe(
                self.db, "SA", enable=True, schedule_every=21600,
                registry_path=str(self.root / "missing.json"),
            )
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM companies").fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM schedules").fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute(
            "SELECT count(*) FROM universe_activation_batches").fetchone()[0], 0)

    def test_scheduling_requires_explicit_enable(self):
        with self.assertRaisesRegex(ValueError, "requires --enable"):
            activate_universe(self.db, "US", schedule_every=3600)

    def test_sec_eligibility_is_conservative(self):
        operating = {"name": "Example Inc", "entityType": "operating", "sic": "3571",
                     "filings": {"recent": {"form": ["10-K"]}}}
        blank_check = {"name": "Example Acquisition Corp", "entityType": "operating",
                       "sic": "6770", "sicDescription": "Blank Checks",
                       "filings": {"recent": {"form": ["10-K"]}}}
        unclear = {"name": "Example", "entityType": "other", "sic": "0000"}
        self.assertEqual(classify_sec_submission(operating)[0], "eligible")
        self.assertEqual(classify_sec_submission(blank_check)[0], "excluded")
        self.assertEqual(classify_sec_submission(unclear)[0], "review")

    def test_enrichment_archives_and_profiles_sec_metadata(self):
        source = self.root / "sec.json"
        source.write_text(json.dumps({"fields": ["cik", "name", "ticker", "exchange"],
            "data": [[1, "Alpha Inc", "AAA", "Nasdaq"]]}), encoding="utf-8")
        sync_universe(self.db, "US", self.root / "raw", input_path=source)
        activation = activate_universe(self.db, "US", limit=1)
        payload = json.dumps({"name": "Alpha Inc", "entityType": "operating", "sic": "3571",
            "sicDescription": "Electronic Computers", "fiscalYearEnd": "1231",
            "tickers": ["AAA"], "exchanges": ["Nasdaq"],
            "filings": {"recent": {"form": ["10-K"]}}}).encode()
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self): return payload
        result = enrich_activation_batch(
            self.db, self.root / "raw", "Product test@example.com",
            activation["batch_id"], opener=lambda *_args, **_kwargs: Response(),
            request_interval=0,
        )
        self.assertEqual(result["counts"]["eligible"], 1)
        profile = self.db.conn.execute(
            "SELECT eligibility_status,local_path FROM universe_issuer_profiles").fetchone()
        self.assertEqual(profile["eligibility_status"], "eligible")
        self.assertTrue(Path(profile["local_path"]).is_file())

    def test_promotion_enables_only_eligible_profile(self):
        source = self.root / "sec.json"
        source.write_text(json.dumps({"fields": ["cik", "name", "ticker", "exchange"],
            "data": [[1, "Alpha Inc", "AAA", "Nasdaq"],
                     [2, "Beta Acquisition Corp", "BBB", "Nasdaq"]]}), encoding="utf-8")
        sync_universe(self.db, "US", self.root / "raw", input_path=source)
        activation = activate_universe(self.db, "US", limit=2)
        profiles = {
            "0000000001": {"name": "Alpha Inc", "entityType": "operating", "sic": "3571",
                "filings": {"recent": {"form": ["10-K"]}}},
            "0000000002": {"name": "Beta Acquisition Corp", "entityType": "operating",
                "sic": "6770", "filings": {"recent": {"form": ["10-K"]}}},
        }
        class Response:
            def __init__(self, payload): self.payload = payload
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self): return json.dumps(self.payload).encode()
        def opener(request, **_kwargs):
            cik = request.full_url.split("CIK", 1)[1].split(".", 1)[0]
            return Response(profiles[cik])
        enrich_activation_batch(self.db, self.root / "raw", "Product test@example.com",
            activation["batch_id"], limit=2, opener=opener, request_interval=0)
        result = promote_activation_batch(self.db, activation["batch_id"], limit=10)
        self.assertEqual((result["promoted"], result["eligible_remaining"]), (1, 0))
        states = {row["symbol"]: (row["enabled"], row["status"]) for row in self.db.conn.execute(
            """SELECT c.symbol,c.enabled,a.status FROM universe_activations a
            JOIN companies c USING(company_id)""")}
        self.assertEqual(states["AAA"], (1, "active"))
        self.assertEqual(states["BBB"], (0, "staged"))
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM schedules").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
