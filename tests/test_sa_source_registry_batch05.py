import json
import unittest
from pathlib import Path


REGISTRY = Path(__file__).resolve().parents[1] / "config" / "source-registry" / "sa-financial-statements-source-batch05.json"


class SaSourceRegistryBatch05Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.by_symbol = {row["symbol"]: row for row in cls.rows}

    def test_expected_companies_are_present_once(self):
        self.assertEqual(set(self.by_symbol), {"1834", "2001", "2030", "2050"})
        self.assertEqual(len(self.by_symbol), len(self.rows))

    def test_verified_statement_archives_are_enabled(self):
        for symbol in ("2001", "2030", "2050"):
            row = self.by_symbol[symbol]
            self.assertTrue(row["direct_document_links_found"])
            self.assertTrue(row["financial_statements_url"].startswith("https://"))

    def test_smasco_does_not_claim_missing_issuer_documents(self):
        row = self.by_symbol["1834"]
        self.assertFalse(row["direct_document_links_found"])
        self.assertIsNone(row["financial_statements_url"])
        self.assertIn("Saudi Exchange", row["access_notes"])


if __name__ == "__main__":
    unittest.main()
