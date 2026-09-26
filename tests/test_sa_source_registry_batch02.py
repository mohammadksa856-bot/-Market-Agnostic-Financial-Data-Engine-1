import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


REGISTRY = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "source-registry"
    / "sa-financial-statements-source-batch02.json"
)
EXPECTED_SYMBOLS = {"1201", "1210", "1212", "1214"}
URL_FIELDS = (
    "official_website",
    "investor_relations_url",
    "annual_reports_url",
    "quarterly_results_url",
    "financial_statements_url",
    "data_supplements_url",
    "tadawul_profile_url",
    "disclosures_url",
)


class SaSourceRegistryBatch02Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_contains_the_reviewed_batch_once(self):
        symbols = [row["symbol"] for row in self.rows]
        self.assertEqual(set(symbols), EXPECTED_SYMBOLS)
        self.assertEqual(len(symbols), len(set(symbols)))

    def test_all_recorded_urls_are_https_and_first_party_or_exchange(self):
        for row in self.rows:
            for field in URL_FIELDS:
                value = row.get(field)
                if not value:
                    continue
                self.assertTrue(value.startswith("https://"), (row["symbol"], field, value))
                host = urlparse(value).netloc.lower()
                self.assertFalse(
                    any(name in host for name in ("argaam", "mubasher", "yahoo", "zawya")),
                    (row["symbol"], field, value),
                )

    def test_downloadable_companies_have_a_financial_statement_page(self):
        by_symbol = {row["symbol"]: row for row in self.rows}
        for symbol in ("1201", "1212", "1214"):
            self.assertEqual(by_symbol[symbol]["access_status"], "reachable")
            self.assertTrue(by_symbol[symbol]["direct_document_links_found"])
            self.assertTrue(by_symbol[symbol]["financial_statements_url"])

    def test_bci_gap_is_explicit_and_does_not_invent_a_source(self):
        bci = next(row for row in self.rows if row["symbol"] == "1210")
        self.assertEqual(bci["access_status"], "not_found")
        self.assertFalse(bci["direct_document_links_found"])
        self.assertIsNone(bci["financial_statements_url"])
        self.assertIn("Saudi Exchange", bci["access_notes"])


if __name__ == "__main__":
    unittest.main()
