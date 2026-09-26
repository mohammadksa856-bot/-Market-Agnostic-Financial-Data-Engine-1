import json
import unittest
from pathlib import Path


REGISTRY = Path(__file__).resolve().parents[1] / "config" / "source-registry" / "sa-financial-statements-source-batch04.json"


class SaSourceRegistryBatch04Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.by_symbol = {row["symbol"]: row for row in cls.rows}

    def test_expected_companies_are_present_once(self):
        self.assertEqual(set(self.by_symbol), {"1324", "1810", "1830", "1832"})
        self.assertEqual(len(self.by_symbol), len(self.rows))

    def test_verified_issuer_pages_are_download_sources(self):
        for symbol in ("1810", "1830", "1832"):
            row = self.by_symbol[symbol]
            self.assertEqual(row["access_status"], "reachable")
            self.assertTrue(row["financial_statements_url"].startswith("https://"))

    def test_source_less_company_is_routed_to_exchange(self):
        row = self.by_symbol["1324"]
        self.assertFalse(row["direct_document_links_found"])
        self.assertIsNone(row["financial_statements_url"])
        self.assertIn("Saudi Exchange", row["access_notes"])


if __name__ == "__main__":
    unittest.main()
