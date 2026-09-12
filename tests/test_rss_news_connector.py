import unittest

SAMPLE_FEED_STR = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel>
<title>Sample Feed</title>
<item>
  <title>‎Qassim Cement acquires 100% of Amix Ready Mix for SAR 65M</title>
  <description>&lt;p&gt;Qassim Cement Co. said it acquired Amix Ready Mix for SAR 65 million.&lt;/p&gt;</description>
  <link>https://www.argaam.com/en/article/articledetail/id/1935200</link>
  <pubDate>Wed, 09 Sep 2026 10:09:00 GMT</pubDate>
  <guid>1-1935200</guid>
</item>
<item>
  <title>‎Horizon Educational board OKs 20% cash dividend</title>
  <description>&lt;p&gt;Unrelated company news.&lt;/p&gt;</description>
  <link>https://www.argaam.com/en/article/articledetail/id/1935100</link>
  <pubDate>Thu, 10 Sep 2026 20:08:00 GMT</pubDate>
  <guid>1-1935100</guid>
</item>
</channel></rss>"""
SAMPLE_FEED = SAMPLE_FEED_STR.encode("utf-8")

MALFORMED_FEED = b"not xml at all"


class RssNewsConnectorTests(unittest.TestCase):
    def test_matches_company_and_ignores_unrelated_items(self):
        from finengine.rss_news_connector import find_news_rss

        feeds = {"https://example.test/feed": {"source_name": "Argaam", "source_domain": "argaam.com", "tier": 2}}
        fetcher = lambda url: SAMPLE_FEED
        result = find_news_rss(
            ["Qassim Cement", "إسمنت القصيم"], market="SA", symbol="3040",
            feeds=feeds, fetcher=fetcher)

        self.assertEqual(len(result["press"]), 1)
        self.assertIn("Qassim Cement", result["press"][0]["title"])
        self.assertEqual(result["press"][0]["source_name"], "Argaam")
        self.assertEqual(result["cost"], "zero (no LLM call)")
        self.assertEqual(result["feed_errors"], [])

    def test_no_match_returns_empty_not_error(self):
        from finengine.rss_news_connector import find_news_rss

        feeds = {"https://example.test/feed": {"source_name": "Argaam", "source_domain": "argaam.com", "tier": 2}}
        result = find_news_rss(
            ["Some Totally Unrelated Company"], market="SA", symbol="9999",
            feeds=feeds, fetcher=lambda url: SAMPLE_FEED)
        self.assertEqual(result["press"], [])
        self.assertEqual(result["official"], [])

    def test_feed_fetch_failure_is_reported_not_silently_swallowed(self):
        from finengine.rss_news_connector import find_news_rss

        def broken_fetcher(url):
            raise TimeoutError("connection timed out")

        feeds = {"https://example.test/dead-feed": {"source_name": "Argaam", "source_domain": "argaam.com", "tier": 2}}
        result = find_news_rss(["Qassim Cement"], market="SA", symbol="3040", feeds=feeds, fetcher=broken_fetcher)
        self.assertEqual(len(result["feed_errors"]), 1)
        self.assertIn("TimeoutError", result["feed_errors"][0]["error"])
        self.assertEqual(result["press"], [])

    def test_malformed_xml_reported_as_feed_error_not_crash(self):
        from finengine.rss_news_connector import find_news_rss

        feeds = {"https://example.test/broken": {"source_name": "Argaam", "source_domain": "argaam.com", "tier": 2}}
        result = find_news_rss(["Qassim Cement"], market="SA", symbol="3040",
                               feeds=feeds, fetcher=lambda url: MALFORMED_FEED)
        self.assertEqual(len(result["feed_errors"]), 1)

    def test_duplicate_links_across_feeds_are_deduplicated(self):
        from finengine.rss_news_connector import find_news_rss

        feeds = {
            "https://example.test/feed-a": {"source_name": "Argaam", "source_domain": "argaam.com", "tier": 2},
            "https://example.test/feed-b": {"source_name": "Argaam", "source_domain": "argaam.com", "tier": 2},
        }
        result = find_news_rss(["Qassim Cement"], market="SA", symbol="3040",
                               feeds=feeds, fetcher=lambda url: SAMPLE_FEED)
        self.assertEqual(len(result["press"]), 1)

    def test_tier_1_feed_routes_to_official(self):
        from finengine.rss_news_connector import find_news_rss

        feeds = {"https://example.test/feed": {"source_name": "Saudi Exchange", "source_domain": "saudiexchange.sa", "tier": 1}}
        result = find_news_rss(["Qassim Cement"], market="SA", symbol="3040",
                               feeds=feeds, fetcher=lambda url: SAMPLE_FEED)
        self.assertEqual(len(result["official"]), 1)
        self.assertEqual(result["press"], [])


if __name__ == "__main__":
    unittest.main()
