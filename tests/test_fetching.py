import unittest

from finengine.fetching import (
    BrowserFetcher, BrowserIssuerMonitor, _saudi_financial_announcement_links, _slug,
)


class FetchAgentUnitTests(unittest.TestCase):
    def test_slug_is_filesystem_safe(self):
        self.assertEqual(
            _slug("https://issuer.example/reports/FY%202025%20Financials.pdf"),
            "FY_2025_Financials.pdf")
        self.assertEqual(_slug("https://issuer.example/"), "document.pdf")

    def test_missing_playwright_raises_a_clear_message(self):
        import importlib.util
        if importlib.util.find_spec("playwright") is not None:
            self.skipTest("playwright is installed in this environment")
        import contextlib
        with self.assertRaises(RuntimeError) as caught, contextlib.ExitStack() as stack:
            BrowserFetcher()._context(stack)
        self.assertIn("browser", str(caught.exception))

    def test_saudi_exchange_financial_cards_are_converted_to_detail_urls(self):
        index = "https://www.saudiexchange.sa/company/2010"
        rows = [
            {"text": "SABIC announces its Interim Financial Results for Q2 2026",
             "onclick": "document.location.href='/announcements/details/?anId=97060&amp;cs=2010'"},
            {"text": "SABIC signs a supply agreement",
             "onclick": "document.location.href='/announcements/details/?anId=97061'"},
            {"text": "Financial results mirror",
             "onclick": "document.location.href='https://evil.example/report'"},
        ]
        result = _saudi_financial_announcement_links(index, rows)
        self.assertEqual(result, [{
            "url": ("https://www.saudiexchange.sa/announcements/details/"
                    "?anId=97060&cs=2010"),
            "title": "SABIC announces its Interim Financial Results for Q2 2026",
        }])

    def test_browser_monitor_classifies_interim_and_annual_reports(self):
        self.assertEqual(
            BrowserIssuerMonitor._document_type("Interim Financial Results for Q1"),
            "interim-report",
        )
        self.assertEqual(
            BrowserIssuerMonitor._document_type("Annual financial results, year ended 2025"),
            "annual-report",
        )


if __name__ == "__main__":
    unittest.main()
