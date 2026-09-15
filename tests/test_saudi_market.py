import json
import unittest

from finengine.saudi_market import _access_blocked, normalize_saudi_market_rows


class SaudiMarketHistoryTests(unittest.TestCase):
    def test_detects_exchange_cdn_denial_before_waiting_for_missing_selectors(self):
        self.assertTrue(_access_blocked(
            "Access Denied",
            "You don't have permission to access this URL. errors.edgesuite.net",
        ))
        self.assertFalse(_access_blocked("Historical Reports", "Market and sector filters"))

    def test_normalizes_visible_close_and_numeric_fields(self):
        rows = [{
            "transactionDateStr": "2026/09/14", "todaysOpen": "25.70",
            "highPrice": "25.82", "lowPrice": "25.52",
            "previousClosePrice": "25.66", "volumeTraded": "5,671,859",
            "turnOver": "145,606,257.96",
        }]
        result = normalize_saudi_market_rows(rows)
        self.assertEqual(result, [{
            "observed_at": "2026-09-14", "interval": "1d", "open": "25.70",
            "high": "25.82", "low": "25.52", "close": "25.66",
            "volume": "5671859", "turnover": "145606257.96", "currency": "SAR",
        }])

    def test_deduplicates_dates_and_rejects_invalid_numbers(self):
        row = {"transactionDate": "2026/09/14", "previousClosePrice": "25.66"}
        self.assertEqual(len(normalize_saudi_market_rows([row, row])), 1)
        with self.assertRaises(ValueError):
            normalize_saudi_market_rows([{**row, "previousClosePrice": "not-a-price"}])


if __name__ == "__main__":
    unittest.main()
