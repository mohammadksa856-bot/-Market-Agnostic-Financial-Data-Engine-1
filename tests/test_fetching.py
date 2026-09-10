import unittest

from finengine.fetching import (
    BrowserFetcher, BrowserIssuerMonitor, _official_issuer_websites,
    _direct_document_bytes, _is_report_page, _published_at_from_url,
    _request_document_bytes,
    _saudi_financial_announcement_links, _slug,
    _validate_document_bytes,
)
from finengine.models import Company, Market


class FetchAgentUnitTests(unittest.TestCase):
    def test_historical_report_pages_and_year_children_are_detected(self):
        reports = "https://issuer.example/investors/annual-reports"
        self.assertTrue(_is_report_page(reports, "Annual reports"))
        self.assertTrue(_is_report_page(
            "https://issuer.example/investors/annual-reports/2021",
            "2021", reports,
        ))
        self.assertFalse(_is_report_page(
            "https://issuer.example/careers/2021", "Careers",
            "https://issuer.example/",
        ))

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
        self.assertEqual(
            BrowserIssuerMonitor._document_type("Q2 2026 النتائج المالية"),
            "interim-report",
        )

    def test_exchange_profile_selects_only_hostname_labelled_issuer_site(self):
        links = [
            ["http://www.sabic.com/", "www.sabic.com"],
            ["https://linkedin.com/company/sabic", "LinkedIn"],
            ["https://example.test/", "Unrelated partner"],
        ]
        self.assertEqual(
            _official_issuer_websites(
                "https://www.saudiexchange.sa/company/2010", links
            ),
            ["https://www.sabic.com/"],
        )

    def test_browser_monitor_preserves_spreadsheet_type(self):
        class FakeFetcher:
            def discover(self, _):
                return [{
                    "url": "https://issuer.example/Q2-2026-data-supplement.xlsx",
                    "title": "Q2 2026 Data Supplement",
                    "content_type": (
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                }]

        company = Company("sa:1120", Market.SA, "1120", "Al Rajhi", "SAR")
        candidate = BrowserIssuerMonitor(
            "https://issuer.example/investors", FakeFetcher()
        ).discover(company).candidates[0]
        self.assertEqual(candidate.document_type, "data-supplement")
        self.assertEqual(
            candidate.content_type,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_browser_monitor_forwards_historical_discovery_limit(self):
        class RecordingFetcher:
            limit = None

            def discover(self, _, max_documents=20):
                self.limit = max_documents
                return []

        fetcher = RecordingFetcher()
        company = Company("sa:2010", Market.SA, "2010", "SABIC", "SAR")
        BrowserIssuerMonitor(
            "https://issuer.example/investors", fetcher, max_documents=200
        ).discover(company)
        self.assertEqual(fetcher.limit, 200)

    def test_document_signatures_are_checked_by_type(self):
        xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        _validate_document_bytes(b"%PDF-test", "https://issuer/report.pdf", "application/pdf")
        _validate_document_bytes(b"PK\x03\x04-test", "https://issuer/data.xlsx", xlsx)
        with self.assertRaisesRegex(RuntimeError, "not an XLSX"):
            _validate_document_bytes(b"<html>", "https://issuer/data.xlsx", xlsx)

    def test_explicit_attachment_upload_date_is_preserved(self):
        self.assertEqual(
            _published_at_from_url(
                "https://exchange.example/fs/23192_480_2026-07-29_11-19-33_en.pdf"
            ),
            "2026-07-29",
        )
        self.assertIsNone(_published_at_from_url("https://issuer.example/Q2-2026.xlsx"))

    def test_request_context_download_preserves_official_referer(self):
        class Response:
            ok = True
            status = 200
            def body(self): return b"%PDF-test"

        class Request:
            def __init__(self): self.call = None
            def get(self, url, **kwargs):
                self.call = (url, kwargs)
                return Response()

        class Context:
            request = Request()

        context = Context()
        content = _request_document_bytes(
            context, "https://issuer.example/report.pdf",
            "https://issuer.example/investors",
        )
        self.assertEqual(content, b"%PDF-test")
        self.assertEqual(context.request.call, (
            "https://issuer.example/report.pdf",
            {"headers": {"Referer": "https://issuer.example/investors"},
             "timeout": 60000},
        ))

    def test_browser_download_rejects_non_https_urls_before_launch(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            BrowserFetcher().download_bytes("http://issuer.example/report.pdf")

    def test_direct_fallback_is_bounded_and_preserves_provenance(self):
        class Response:
            def __init__(self): self.parts = [b"%PDF", b"-test", b""]
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self, _size): return self.parts.pop(0)

        observed = {}
        def opener(request, **kwargs):
            observed["url"] = request.full_url
            observed["headers"] = dict(request.header_items())
            observed["timeout"] = kwargs["timeout"]
            return Response()

        content = _direct_document_bytes(
            "https://issuer.example/report.pdf",
            "https://issuer.example/investors", 12, opener, 20,
        )
        self.assertEqual(content, b"%PDF-test")
        self.assertEqual(observed["timeout"], 12)
        self.assertEqual(observed["headers"]["Referer"],
                         "https://issuer.example/investors")
        self.assertIn("MarketAgnostic", observed["headers"]["User-agent"])

        with self.assertRaisesRegex(ValueError, "exceeded"):
            _direct_document_bytes(
                "https://issuer.example/report.pdf", opener=opener, max_bytes=4
            )


if __name__ == "__main__":
    unittest.main()
