import unittest

from finengine.relay_discovery import (
    discovery_sources,
    financial_statement_slot,
    gather_company_candidates,
    missing_financial_statement_slots,
    select_financial_statement_candidates,
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
    def test_financial_statement_slots_cover_all_years_without_fixed_horizon(self):
        reports = []
        for year in range(2010, 2026):
            for token, label in (
                ("q1", "Q1"), ("h1", "H1 six months"),
                ("9m", "Q3 nine months"), ("fy", "audited"),
            ):
                reports.append(candidate(
                    f"https://issuer.example/{year}-{token}-financial-statements.pdf",
                    f"{label} financial statements {year}",
                ))
        selected = select_financial_statement_candidates(reports, 200)
        self.assertEqual(len(selected), 16 * 4)
        self.assertEqual(financial_statement_slot(selected[0]), (2025, "Q1"))
        self.assertEqual(financial_statement_slot(selected[-1]), (2010, "FY"))

    def test_non_statement_documents_never_fill_statement_slots(self):
        excluded = (
            candidate("https://issuer.example/annual-2025.pdf", "Annual report 2025"),
            candidate("https://issuer.example/bod-2025.pdf", "Board of Directors Report 2025"),
            candidate("https://issuer.example/BOD-2025.pdf", "Financial Statements and Reports Download"),
            candidate("https://issuer.example/deck-2025.pdf", "Investor presentation financial results 2025"),
            candidate("https://issuer.example/pillar-2025.pdf", "Pillar 3 financial disclosure 2025"),
            candidate("https://issuer.example/supplement-2025.xlsx", "Data Supplement financials 2025"),
        )
        self.assertTrue(all(financial_statement_slot(item) is None for item in excluded))
        self.assertEqual(select_financial_statement_candidates(excluded, 200), [])

    def test_statement_end_dates_map_to_the_four_slots(self):
        expected = (("31 March", "Q1"), ("30 June", "Q2"),
                    ("30 September", "Q3"), ("31 December", "FY"))
        for end_date, slot in expected:
            filing = candidate(
                f"https://issuer.example/statement-{end_date.replace(' ', '-')}-2024.pdf",
                f"Financial statements for period ended {end_date} 2024",
            )
            self.assertEqual(financial_statement_slot(filing), (2024, slot))

    def test_missing_slots_are_reported_for_each_discovered_year(self):
        reports = [
            candidate("https://issuer.example/q1-2025-financial.pdf", "Q1 financial statements 2025"),
            candidate("https://issuer.example/fy-2025-financial.pdf", "Audited financial statements 2025"),
            candidate("https://issuer.example/h1-2024-financial.pdf", "H1 financial statements 2024"),
        ]
        self.assertEqual(missing_financial_statement_slots(reports), {
            2025: ["Q2", "Q3"],
            2024: ["Q1", "Q3", "FY"],
        })

    def test_configured_sources_avoid_unreliable_exchange_profile(self):
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
            ],
        )
        self.assertFalse(any(item.crawl_issuer_site for item in without_bridge))

        with_bridge = discovery_sources(company, PROFILE, True)
        self.assertEqual(
            [item.crawl_issuer_site for item in with_bridge], [False, False]
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
        self.assertEqual([call[0] for call in fetcher.calls], [failed, working])

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
