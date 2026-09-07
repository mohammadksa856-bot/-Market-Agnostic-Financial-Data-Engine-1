import io
import json
import tempfile
import unittest
from pathlib import Path

from finengine import tadawul


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _feed(pages):
    """Return a urlopen stub that serves one JSON page per POST call."""
    calls = {"n": 0}

    def opener(request, timeout=0):
        index = calls["n"]
        calls["n"] += 1
        body = pages[index] if index < len(pages) else {"announcementList": []}
        return _Resp(json.dumps(body).encode("utf-8"))

    return opener, calls


def _row(symbol, an_id, desc, pr_date="Mar 31, 2026"):
    return {
        "SYMBOL": symbol, "SHORT_DESC": desc, "announcementNumber": str(an_id),
        "PRESS_REL_ID": an_id, "PR_DATE": pr_date,
        "announcementUrl": ("/wps/portal/saudiexchange/newsandreports/issuer-news/"
                            "issuer-announcements/issuer-announcements-details/"
                            f"?anId\\u003d{an_id}\\u0026anCat\\u003d1\\u0026cs\\u003d{symbol}"
                            "\\u003d\\u003den"),
    }


class FindAnnualResultsTests(unittest.TestCase):
    def test_pages_the_feed_then_filters_by_symbol_and_title(self):
        page1 = {"announcementList": [
            _row("4190", 93101, "Jarir Marketing Company announces its Annual "
                 "Financial results for the period ending on 31-12-2025"),
            _row("4190", 92000, "Jarir Marketing Company announces the date of "
                 "its board meeting"),
            _row("2010", 93102, "SABIC announces its Annual Financial results for "
                 "the period ending on 31-12-2025"),
        ]}
        # oldest row on page 2 predates the cutoff -> paging stops after it
        page2 = {"announcementList": [
            _row("4190", 88010, "Jarir Marketing Company announces its Interim "
                 "Financial results for the period ending on 30-09-2025",
                 pr_date="Jan 2, 2024"),
        ]}
        opener, calls = _feed([page1, page2])

        with tempfile.TemporaryDirectory() as name:
            cache = Path(name) / "feed.json"
            found = tadawul.find_annual_results("4190", cache_path=cache, opener=opener)

            self.assertEqual([f["an_id"] for f in found], ["93101"])
            self.assertIn("anId=93101", found[0]["details_url"])
            self.assertTrue(cache.is_file())  # feed cached for the next issuer
            # a second issuer reads the cache, no more HTTP
            before = calls["n"]
            tadawul.find_annual_results("2010", cache_path=cache, opener=opener)
            self.assertEqual(calls["n"], before)

    def test_incremental_refresh_stops_at_a_known_announcement(self):
        old = {"announcementList": [
            _row("4190", 100, "Jarir Marketing Company announces its Annual "
                 "Financial results for the period ending on 31-12-2025")]}
        new_then_known = {"announcementList": [
            _row("4190", 101, "Jarir Marketing Company announces its Annual "
                 "Financial results for the period ending on 31-12-2026"),
            _row("4190", 100, "Jarir Marketing Company announces its Annual "
                 "Financial results for the period ending on 31-12-2025"),
        ]}
        with tempfile.TemporaryDirectory() as name:
            cache = Path(name) / "feed.json"
            opener1, _ = _feed([old])
            tadawul.refresh_feed(cache, opener=opener1)
            opener2, calls2 = _feed([new_then_known])
            rows = tadawul.refresh_feed(cache, opener=opener2)

        ids = sorted(r["an_id"] for r in rows)
        self.assertEqual(ids, ["100", "101"])  # old kept, new merged in

    def test_no_match_returns_empty(self):
        opener, _ = _feed([{"announcementList": [
            _row("4190", 1, "Jarir board meeting date", pr_date="Jan 2, 2024")]}])
        with tempfile.TemporaryDirectory() as name:
            self.assertEqual(
                tadawul.find_annual_results("1211", cache_path=Path(name) / "f.json",
                                            opener=opener),
                [])

    def test_matches_the_alternate_annual_phrasings_and_skips_interim(self):
        opener, _ = _feed([{"announcementList": [
            _row("2280", 10, "Almarai Company announces its consolidated financial "
                 "results for the year ended 31 December 2025"),
            _row("2280", 11, "Almarai Company announces its interim condensed "
                 "consolidated financial results for the period ending 30-06-2026"),
            _row("2350", 12, "Saudi Kayan announces the annual financial results "
                 "for the period ending on 2025-12-31"),
        ]}])
        with tempfile.TemporaryDirectory() as name:
            cache = Path(name) / "f.json"
            self.assertEqual(
                [r["an_id"] for r in tadawul.find_annual_results("2280", cache_path=cache,
                                                                 opener=opener)],
                ["10"])
            self.assertEqual(
                [r["an_id"] for r in tadawul.find_annual_results("2350", cache_path=cache,
                                                                 opener=opener)],
                ["12"])


class CompanyAnnualFsUrlTests(unittest.TestCase):
    _HTML = (
        '<tr class="cf"><th>2026</th><th>2025</th><th>2024</th><th>2023</th></tr>'
        '<tr><td>Annual</td>'
        '<td> - </td>'
        '<td><div class="dwnIcn"><a href="/Resources/fsPdf/454_0_2026-03-31_11-52-35_En.pdf" '
        'class="btn-pdf"></a></div><p>2026-03-31 </p></td>'
        '<td><a href="/Resources/fsPdf/454_0_2025-03-25_02-00-19_En.pdf"></a><p>2025-03-25 </p></td>'
        '<td><a href="/Resources/fsPdf/454_0_2024-03-10_08-03-20_En.pdf"></a><p>2024-03-10 </p></td>'
        '</tr>')

    def test_picks_the_newest_annual_fs_with_its_filed_date(self):
        url, filed = tadawul.company_annual_fs_url(
            "4190", html_getter=lambda _s: self._HTML)
        self.assertEqual(
            url, "https://www.saudiexchange.sa/Resources/fsPdf/"
                 "454_0_2026-03-31_11-52-35_En.pdf")
        self.assertEqual(filed, "2026-03-31")

    def test_can_target_a_specific_year_column(self):
        # the column labelled <year> holds that fiscal year's FS, filed the
        # following March -> the 2024 column links the 2025-03-25 file.
        url, filed = tadawul.company_annual_fs_url(
            "4190", year=2024, html_getter=lambda _s: self._HTML)
        self.assertIn("454_0_2025-03-25", url)
        self.assertEqual(filed, "2025-03-25")

    def test_returns_none_when_the_tab_has_no_annual_fs(self):
        self.assertIsNone(tadawul.company_annual_fs_url(
            "9999", html_getter=lambda _s: "<table><tr><th>2025</th></tr></table>"))

    def test_requires_a_fetcher_or_getter(self):
        with self.assertRaises(ValueError):
            tadawul.company_annual_fs_url("9999")


class StatementPdfUrlTests(unittest.TestCase):
    def test_scrapes_the_fspdf_link_from_details_html(self):
        html = (
            '<table><tr><td>Financial Statement</td>'
            '<td>&nbsp;<a href="/Resources/fsPdf/31073_370_2026-03-05_15-41-48_en.pdf">'
            '<img src="/icons/pdf.png"></a></td></tr></table>')
        url = tadawul.statement_pdf_url("93484", "1211", html_getter=lambda _u: html)
        self.assertEqual(
            url,
            "https://www.saudiexchange.sa/Resources/fsPdf/"
            "31073_370_2026-03-05_15-41-48_en.pdf")

    def test_returns_none_when_no_pdf_present(self):
        url = tadawul.statement_pdf_url("1", "9999", html_getter=lambda _u: "<html>no pdf</html>")
        self.assertIsNone(url)

    def test_requires_a_fetcher_or_getter(self):
        with self.assertRaises(ValueError):
            tadawul.statement_pdf_url("1", "9999")


if __name__ == "__main__":
    unittest.main()
