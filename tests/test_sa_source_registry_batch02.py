import importlib.util
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BATCH01 = ROOT / "config" / "source-registry" / "sa-batch-zero-source-01.json"
BATCH02 = ROOT / "config" / "source-registry" / "sa-batch-zero-source-02.json"

SCRIPT = ROOT / "scripts" / "build_sa_market_registry.py"
SPEC = importlib.util.spec_from_file_location("build_sa_market_registry", SCRIPT)
registry_builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(registry_builder)

EXPECTED_SYMBOLS = [
    "1090", "1111", "1201", "1202", "1210", "1211", "1212", "1213", "1214", "1301",
    "1302", "1303", "1304", "1310", "1320", "1321", "1322", "1323", "1324", "1330",
    "1810", "1820", "1830", "1831", "1832", "1833", "1834", "1835", "2001", "2002",
    "2020", "2030", "2040", "2050", "2070", "2083", "2084", "2090", "2110", "2130",
    "2150", "2160", "2170", "2180", "2190", "2200", "2210", "2220", "2223", "2240",
    "2250", "2260", "2270", "2280", "2281", "2283", "2287", "2290", "2300", "2310",
    "2320", "2330", "2340", "2350", "2360", "2370", "2380", "2381", "2382", "3001",
    "3007", "3008", "3080", "3090", "3091", "3092", "4001", "4004", "4005", "4006",
]
# Not on the Saudi Exchange listed-companies page when checked, so no profile URL exists.
UNLISTED = {"1090", "1310", "1330", "2002", "2260", "3001"}
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


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class SaSourceRegistryBatch02Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = _load(BATCH02)
        cls.batch01 = _load(BATCH01)

    def test_exactly_the_requested_eighty_symbols(self):
        symbols = [r["symbol"] for r in self.rows]
        self.assertEqual(len(EXPECTED_SYMBOLS), 80)
        self.assertEqual(len(set(EXPECTED_SYMBOLS)), 80)
        self.assertEqual(len(symbols), 80)
        self.assertEqual(sorted(symbols), sorted(EXPECTED_SYMBOLS))

    def test_no_duplicates_within_batch(self):
        symbols = [r["symbol"] for r in self.rows]
        self.assertEqual(len(symbols), len(set(symbols)))

    def test_no_overlap_with_batch01(self):
        first = {r["symbol"] for r in self.batch01}
        self.assertEqual(first & {r["symbol"] for r in self.rows}, set())

    def test_required_keys_present(self):
        for row in self.rows:
            self.assertTrue(REQUIRED_KEYS <= set(row), row["symbol"])

    def test_non_empty_urls_are_https(self):
        for row in self.rows:
            for field in URL_FIELDS:
                value = row.get(field)
                if value:
                    self.assertTrue(value.startswith("https://"), f"{row['symbol']} {field}: {value}")

    def test_no_secondary_source_domains(self):
        for row in self.rows:
            for field in URL_FIELDS:
                value = row.get(field)
                if value:
                    host = urlparse(value).netloc.lower()
                    for bad in SECONDARY:
                        self.assertNotIn(bad, host, f"{row['symbol']} {field}: {value}")

    def test_access_status_is_valid(self):
        for row in self.rows:
            self.assertIn(row["access_status"], ALLOWED_STATUS, row["symbol"])

    def test_direct_links_flag_is_boolean_or_null(self):
        for row in self.rows:
            self.assertIn(row["direct_document_links_found"], (True, False, None), row["symbol"])

    def test_saudi_exchange_profile_urls_match_symbols(self):
        for row in self.rows:
            url = row["tadawul_profile_url"]
            if row["symbol"] in UNLISTED:
                self.assertIsNone(url, row["symbol"])
                continue
            self.assertEqual(urlparse(url).netloc, "www.saudiexchange.sa", row["symbol"])
            self.assertTrue(url.endswith("companySymbol=" + row["symbol"]), row["symbol"])

    def test_visible_years_are_valid_and_ordered(self):
        for row in self.rows:
            old, new = row["oldest_visible_year"], row["latest_visible_year"]
            for year in (old, new):
                self.assertTrue(year is None or (isinstance(year, int) and 2000 <= year <= 2030), row["symbol"])
            if old is not None and new is not None:
                self.assertLessEqual(old, new, row["symbol"])

    def test_evidence_and_checked_at_present(self):
        for row in self.rows:
            self.assertTrue(row["evidence"].strip(), row["symbol"])
            self.assertRegex(row["checked_at"], r"^\d{4}-\d{2}-\d{2}T")

    def test_unlisted_symbols_carry_no_report_urls(self):
        for row in self.rows:
            if row["symbol"] in UNLISTED:
                self.assertEqual(row["access_status"], "not_found", row["symbol"])
                for field in URL_FIELDS:
                    self.assertIsNone(row.get(field), f"{row['symbol']} {field}")


class SaSourceRegistryBuilderIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = _load(BATCH02)
        cls.built = registry_builder.build_registry()
        cls.by_symbol = {item["symbol"]: item for item in cls.built}

    def test_builder_loads_both_batches_together(self):
        pages = registry_builder._source_pages(registry_builder.DEFAULT_SOURCE_REGISTRY)
        first = {r["symbol"] for r in _load(BATCH01)}
        second = {r["symbol"] for r in self.rows}
        self.assertTrue(first & set(pages), "batch01 contributes no sources")
        self.assertTrue(second & set(pages), "batch02 contributes no sources")
        self.assertEqual(first & second, set())
        registry_builder.validate_registry(self.built)

    def test_registry_still_has_439_unique_companies(self):
        self.assertEqual(len(self.built), 439)
        self.assertEqual(len({item["symbol"] for item in self.built}), 439)
        tracked = _load(registry_builder.DEFAULT_OUTPUT)
        self.assertEqual(len(tracked), 439)
        self.assertEqual(len({item["symbol"] for item in tracked}), 439)

    def test_every_verified_issuer_page_enters_the_sources_list(self):
        checked = 0
        for row in self.rows:
            for field in registry_builder.SOURCE_URL_FIELDS:
                url = row.get(field)
                if isinstance(url, str) and url.startswith("https://"):
                    self.assertIn(url, self.by_symbol[row["symbol"]]["sources"], f"{row['symbol']} {field}")
                    checked += 1
        self.assertGreater(checked, 100)

    def test_tracked_registry_is_current(self):
        self.assertFalse(registry_builder.ensure_registry(check=True))

    def test_batch01_sources_are_untouched_by_batch02(self):
        for row in _load(BATCH01):
            for field in registry_builder.SOURCE_URL_FIELDS:
                url = row.get(field)
                if isinstance(url, str) and url.startswith("https://"):
                    self.assertIn(url, self.by_symbol[row["symbol"]]["sources"], f"{row['symbol']} {field}")


if __name__ == "__main__":
    unittest.main()
