import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

REGISTRY = Path(__file__).resolve().parents[1] / "config" / "source-registry" / "sa-batch-zero-source-01.json"

EXPECTED_SYMBOLS = [
    "1182", "1183", "2060", "2080", "2081", "2100", "2120", "2140", "2230",
    "2282", "2284", "2285", "2286", "2288", "3004", "4002", "4003", "4007",
    "4008", "4009", "4011", "4014", "4051", "4061", "4071", "4080", "4081",
    "4130", "4163", "4165", "4193", "4200", "4220", "4230", "4290", "4300",
    "4322", "4323", "6012", "6040",
]
ALLOWED_STATUS = {"reachable", "js_required", "ssl_issue", "blocked", "not_found"}
URL_FIELDS = [
    "official_website", "investor_relations_url", "annual_reports_url",
    "quarterly_results_url", "financial_statements_url", "data_supplements_url",
    "tadawul_profile_url", "disclosures_url", "financial_results_url",
]
REQUIRED_KEYS = set(URL_FIELDS[:-1]) | {
    "symbol", "company_name", "access_status", "direct_document_links_found",
    "oldest_visible_year", "latest_visible_year", "checked_at", "evidence",
}
SECONDARY = ("argaam", "mubasher", "yahoo", "zawya", "investing.com", "marketscreener")


class SaSourceRegistryBatch01Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_no_duplicate_symbols(self):
        symbols = [r["symbol"] for r in self.rows]
        self.assertEqual(len(symbols), len(set(symbols)))

    def test_every_requested_symbol_present_exactly_once(self):
        symbols = [r["symbol"] for r in self.rows]
        self.assertEqual(sorted(symbols), sorted(EXPECTED_SYMBOLS))
        self.assertEqual(len(symbols), 40)

    def test_required_keys_present(self):
        for row in self.rows:
            self.assertTrue(REQUIRED_KEYS <= set(row), row["symbol"])

    def test_non_empty_urls_are_https(self):
        for row in self.rows:
            for field in URL_FIELDS:
                value = row.get(field)
                if value:
                    self.assertTrue(value.startswith("https://"), f"{row['symbol']} {field}: {value}")

    def test_access_status_is_approved_value(self):
        for row in self.rows:
            self.assertIn(row["access_status"], ALLOWED_STATUS, row["symbol"])

    def test_no_secondary_domains_in_urls(self):
        for row in self.rows:
            for field in URL_FIELDS:
                value = row.get(field)
                if value:
                    host = urlparse(value).netloc.lower()
                    for bad in SECONDARY:
                        self.assertNotIn(bad, host, f"{row['symbol']} {field}: {value}")

    def test_tadawul_profile_is_on_saudi_exchange(self):
        for row in self.rows:
            url = row["tadawul_profile_url"]
            self.assertEqual(urlparse(url).netloc, "www.saudiexchange.sa", row["symbol"])
            self.assertTrue(url.endswith("companySymbol=" + row["symbol"]), row["symbol"])

    def test_visible_years_are_sane(self):
        for row in self.rows:
            old, new = row["oldest_visible_year"], row["latest_visible_year"]
            for year in (old, new):
                self.assertTrue(year is None or (isinstance(year, int) and 2000 <= year <= 2030), row["symbol"])
            if old is not None and new is not None:
                self.assertLessEqual(old, new, row["symbol"])

    def test_direct_links_flag_is_boolean_or_null(self):
        for row in self.rows:
            self.assertIn(row["direct_document_links_found"], (True, False, None), row["symbol"])

    def test_evidence_and_timestamp_present(self):
        for row in self.rows:
            self.assertTrue(row["evidence"].strip(), row["symbol"])
            self.assertRegex(row["checked_at"], r"^\d{4}-\d{2}-\d{2}T")


if __name__ == "__main__":
    unittest.main()
