import unittest

from finengine.relay_discovery import (
    discovery_sources,
    gather_company_candidates,
    select_upload_candidates,
)


PROFILE = "https://www.saudiexchange.sa/company-profile?companySymbol=1010"


def candidate(url: str, title: str) -> dict:
    return {"url": url, "title": title, "content_type": "application/pdf"}


class FakeFetcher:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def discover(self, url, max_documents, crawl_issuer_site):
        self.calls.append((url, max_documents, crawl_issuer_site))
        response = self.responses.get(url, [])
        if isinstance(response, Exception):
            raise response
        return response[:max_documents]


class RelayDiscoveryTests(unittest.TestCase):
    def test_all_configured_sources_and_profile_are_planned_before_budget(self):
        company = {
            "sources": [
                "https://issuer.example/annual-reports",
                {"url": "https://issuer.example/quarterly-results"},
            ]
        }
        without_bridge = discovery_sources(company, PROFILE, False)
        self.assertEqual(
            [item.url for item in without_bridge],
            [
                "https://issuer.example/annual-reports",
                "https://issuer.example/quarterly-results",
                PROFILE,
            ],
        )
        self.assertFalse(any(item.crawl_issuer_site for item in without_bridge))

        with_bridge = discovery_sources(company, PROFILE, True)
        self.assertEqual(
            [item.crawl_issuer_site for item in with_bridge], [False, False, True]
        )

    def test_twenty_five_links_advance_to_eleven_through_twenty_next_run(self):
        source = "https://issuer.example/reports"
        reports = [
            candidate(f"https://issuer.example/report-{number}.pdf", f"Report {number}")
            for number in range(1, 26)
        ]
        fetcher = FakeFetcher({source: reports, PROFILE: []})
        company = {"sources": [source]}

        first_discovery = gather_company_candidates(
            fetcher, company, PROFILE, False
        )
        first = select_upload_candidates(first_discovery.candidates, 10, seen={})
        self.assertEqual(
            [item["url"] for item in first],
            [f"https://issuer.example/report-{number}.pdf" for number in range(1, 11)],
        )

        seen = {item["url"]: {"status": "queued"} for item in first}
        second_discovery = gather_company_candidates(
            fetcher, company, PROFILE, False
        )
        second = select_upload_candidates(
            second_discovery.candidates, 10, seen=seen
        )
        self.assertEqual(
            [item["url"] for item in second],
            [f"https://issuer.example/report-{number}.pdf" for number in range(11, 21)],
        )
        self.assertTrue(all(call[1] == 200 for call in fetcher.calls))

    def test_company_without_sources_uses_profile_issuer_bridge(self):
        fetcher = FakeFetcher({PROFILE: []})
        result = gather_company_candidates(fetcher, {"sources": []}, PROFILE, True)
        self.assertEqual(result.candidates, ())
        self.assertEqual(fetcher.calls, [(PROFILE, 200, True)])

    def test_partial_source_failure_keeps_candidates_and_retry_signal(self):
        failed = "https://issuer.example/annual-reports"
        working = "https://issuer.example/quarterly-results"
        report = candidate("https://issuer.example/q1-2026.pdf", "Q1 2026")
        fetcher = FakeFetcher({
            failed: RuntimeError("issuer annual archive timed out"),
            working: [report],
            PROFILE: [],
        })
        result = gather_company_candidates(
            fetcher, {"sources": [failed, working]}, PROFILE, True
        )
        self.assertEqual([item["url"] for item in result.candidates], [report["url"]])
        self.assertTrue(result.needs_retry)
        self.assertEqual(
            [(failure.source_url, str(failure.error)) for failure in result.source_failures],
            [(failed, "issuer annual archive timed out")],
        )
        self.assertEqual(
            [call[0] for call in fetcher.calls], [failed, working, PROFILE]
        )

    def test_annual_source_cannot_starve_quarterly_coverage(self):
        annual_source = "https://issuer.example/annual-reports"
        quarter_source = "https://issuer.example/quarterly-results"
        annual = [
            candidate(
                f"https://issuer.example/annual-{year}.pdf",
                f"Annual report {year}",
            )
            for year in range(2025, 2005, -1)
        ]
        quarterly = []
        for offset in range(20):
            year = 2026 - offset // 4
            quarter = 4 - offset % 4
            quarterly.append(candidate(
                f"https://issuer.example/{year}-q{quarter}.pdf",
                f"Q{quarter} {year} interim financial statements",
            ))
        fetcher = FakeFetcher({
            annual_source: annual,
            quarter_source: quarterly,
            PROFILE: [],
        })
        discovery = gather_company_candidates(
            fetcher,
            {"sources": [annual_source, quarter_source]},
            PROFILE,
            False,
        )
        selected = select_upload_candidates(discovery.candidates, 10, seen={})
        titles = [item["title"].lower() for item in selected]
        self.assertEqual(sum("annual" in title for title in titles), 3)
        self.assertEqual(sum("interim" in title for title in titles), 7)

        coverage = select_upload_candidates(discovery.candidates, 17, seen={})
        coverage_titles = [item["title"].lower() for item in coverage]
        self.assertEqual(sum("annual" in title for title in coverage_titles), 5)
        self.assertEqual(sum("interim" in title for title in coverage_titles), 12)

    def test_outbox_candidates_are_excluded_before_budget(self):
        reports = [
            candidate(f"https://issuer.example/report-{number}.pdf", f"Report {number}")
            for number in range(1, 13)
        ]
        outbox = {
            "version": 1,
            "documents": {
                f"SA:1010:{number}": {
                    "source_url": reports[number - 1]["url"],
                    "local_path": f"archive/{number}.pdf",
                    "status": "pending_enqueue",
                }
                for number in range(1, 6)
            },
        }
        selected = select_upload_candidates(
            reports, 5, seen={}, outbox=outbox
        )
        self.assertEqual(
            [item["url"] for item in selected],
            [f"https://issuer.example/report-{number}.pdf" for number in range(6, 11)],
        )


if __name__ == "__main__":
    unittest.main()
