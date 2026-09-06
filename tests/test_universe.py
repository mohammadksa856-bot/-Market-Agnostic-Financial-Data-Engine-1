import json
import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.query import FinancialQueryService
from finengine.universe import parse_saudi_reference, parse_sec_ticker_exchange, sync_universe


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


if __name__ == "__main__":
    unittest.main()
