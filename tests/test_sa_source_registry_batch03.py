import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


REGISTRY = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "source-registry"
    / "sa-financial-statements-source-batch03.json"
)


class SaSourceRegistryBatch03Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.by_symbol = {row["symbol"]: row for row in cls.rows}

    def test_expected_companies_are_present_once(self):
        self.assertEqual(set(self.by_symbol), {"1302", "1304", "1320", "1322"})
        self.assertEqual(len(self.by_symbol), len(self.rows))

    def test_downloadable_companies_use_official_https_statement_pages(self):
        for symbol in ("1302", "1320", "1322"):
            row = self.by_symbol[symbol]
            self.assertEqual(row["access_status"], "reachable")
            self.assertTrue(row["direct_document_links_found"])
            statement_url = row["financial_statements_url"]
            self.assertTrue(statement_url.startswith("https://"))
            self.assertNotIn(urlparse(statement_url).netloc, {"argaam.com", "mubasher.info"})

    def test_yamamah_gap_is_explicit(self):
        row = self.by_symbol["1304"]
        self.assertEqual(row["access_status"], "blocked")
        self.assertFalse(row["direct_document_links_found"])
        self.assertIsNone(row["financial_statements_url"])
        self.assertIn("Saudi Exchange", row["access_notes"])

    def test_visible_year_ranges_are_consistent(self):
        for row in self.rows:
            oldest = row["oldest_visible_year"]
            latest = row["latest_visible_year"]
            if oldest is not None and latest is not None:
                self.assertLessEqual(oldest, latest)


if __name__ == "__main__":
    unittest.main()
