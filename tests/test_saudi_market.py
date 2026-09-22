import json
import unittest

from finengine.saudi_market import (
    _access_blocked,
    normalize_saudi_market_rows,
    parse_saudi_history_csv,
)


class SaudiMarketHistoryTests(unittest.TestCase):
    def test_detects_exchange_cdn_denial_before_waiting_for_missing_selectors(self):
        self.assertTrue(_access_blocked(
            "Access Denied",
            "You don't have permission to access this URL. errors.edgesuite.net",
        ))
        self.assertFalse(_access_blocked("Historical Reports", "Market and sector filters"))

    def test_entity_option_matches_padded_and_prefixed_symbols(self):
        from finengine.saudi_market import _entity_option_for

        # Alinma (1150) is listed by some portal builds as "01150" / "SA1150";
        # the exact-string lookup used to miss it and fail the whole fetch.
        self.assertEqual(_entity_option_for("1150", ["1120", "1150"]), "1150")
        self.assertEqual(_entity_option_for("1150", ["01150", "1120"]), "01150")
        self.assertEqual(_entity_option_for("1150", ["SA1150"]), "SA1150")
        self.assertIsNone(_entity_option_for("1150", ["1151", "2222"]))
        self.assertIsNone(_entity_option_for("1150", []))

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


    def test_parses_thousands_grouped_csv_rows_deterministically(self):
        text = (
            "2026-09-22,64.10,64.60,63.65,63.65,621,870,39,823,443.95,2,975\n"
            "2023-09-13,42.80,42.80,41.75,41.95,820,361,34,378,912.10,1,900\n"
        )
        rows, excluded = parse_saudi_history_csv(text)
        self.assertEqual(excluded, [])
        self.assertEqual(len(rows), 2)
        normalized = normalize_saudi_market_rows(rows)
        self.assertEqual(normalized[0], {
            "observed_at": "2023-09-13", "interval": "1d", "open": "42.80",
            "high": "42.80", "low": "41.75", "close": "41.95",
            "volume": "820361", "turnover": "34378912.10", "currency": "SAR",
        })
        self.assertEqual(normalized[1]["volume"], "621870")
        self.assertEqual(normalized[1]["turnover"], "39823443.95")

    def test_excludes_trading_halt_rows_instead_of_zero_filling(self):
        text = "2024-03-10,-,-,-,-,-,-,-\n"
        rows, excluded = parse_saudi_history_csv(text)
        self.assertEqual(rows, [])
        self.assertEqual(len(excluded), 1)
        self.assertIn("halt", excluded[0]["reason"])

    def test_excludes_rows_failing_ohlc_sanity_check(self):
        # high (10.00) is below close (12.00): not a valid trading day.
        text = "2024-03-11,11.00,10.00,9.50,12.00,100,10,000.00,5\n"
        rows, excluded = parse_saudi_history_csv(text)
        self.assertEqual(rows, [])
        self.assertEqual(len(excluded), 1)
        self.assertIn("sanity", excluded[0]["reason"])


if __name__ == "__main__":
    unittest.main()
