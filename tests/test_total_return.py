import tempfile
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from finengine.database import Database
from finengine.domains import CompanyDomainStore
from finengine.models import Company, Market, SourceDocument


class TotalReturnTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.temp.name) / "tr.sqlite3"))
        self.db.register_company(Company("sa:TST", Market.SA, "TST", "Test", "SAR", country="SA"))
        self.sources = []
        for key in ("source:a", "source:b"):
            source = SourceDocument("sa:TST", Market.SA, f"https://example.test/{key}", key, "prices", "2026-01-01", b"{}")
            self.db.save_source(source, "domain", None)
            self.sources.append(source.source_key)
        self.store = CompanyDomainStore(self.db)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def metrics(self):
        self.store.refresh_market_statistics("sa:TST")
        return {r[0]: Decimal(r[1]) for r in self.db.conn.execute(
            "SELECT metric_key,value_decimal FROM data_points WHERE company_id='sa:TST' AND is_current=1")}

    def publish(self, start, days, close, adjusted, source):
        for offset in range(days):
            self.store.publish_market_price("sa:TST", (start + timedelta(days=offset)).isoformat(), Decimal(close),
                                            "SAR", source, adjusted_close=None if adjusted is None else Decimal(adjusted))

    def test_one_year_total_return_uses_the_adjusted_series(self):
        self.publish(date(2025, 1, 1), 10, "100", "80", self.sources[0])
        self.publish(date(2026, 1, 1), 10, "100", "100", self.sources[0])
        out = self.metrics()
        self.assertEqual(out["total_return_1y"], Decimal("0.25"))  # dividends: price flat, total return +25%
        self.assertEqual(out["market_return_1y"], Decimal("0"))

    def test_series_from_different_sources_are_not_combined(self):
        self.publish(date(2025, 1, 1), 10, "100", "80", self.sources[0])
        self.publish(date(2026, 1, 1), 10, "100", "100", self.sources[1])
        self.assertNotIn("total_return_1y", self.metrics())

    def test_no_adjusted_close_no_total_return(self):
        self.publish(date(2025, 1, 1), 10, "100", None, self.sources[0])
        self.publish(date(2026, 1, 1), 10, "100", None, self.sources[0])
        self.assertNotIn("total_return_1y", self.metrics())


if __name__ == "__main__":
    unittest.main()
