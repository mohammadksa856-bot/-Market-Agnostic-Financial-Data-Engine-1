import json
import types
import unittest


def _fake_client(results):
    class Messages:
        def create(self, **kwargs):
            self.request = kwargs
            text = json.dumps({"results": results})
            return types.SimpleNamespace(
                content=[types.SimpleNamespace(type="text", text=text)],
                usage=types.SimpleNamespace(input_tokens=500, output_tokens=200))
    return types.SimpleNamespace(messages=Messages())


class NewsConnectorTests(unittest.TestCase):
    def test_allowlisted_results_split_into_tiers(self):
        from finengine.news_connector import find_news

        client = _fake_client([
            {"title": "Al Rajhi Bank announces Q2 results", "url": "https://www.saudiexchange.sa/wps/portal/x",
             "published_at": "2026-07-21", "summary": "Official issuer announcement."},
            {"title": "Al Rajhi Bank Q2 profit up 14%", "url": "https://www.argaam.com/en/article/1",
             "published_at": "2026-08-04", "summary": "Argaam's own coverage of the results."},
            {"title": "Al Rajhi prices sukuk", "url": "https://markets.ft.com/data/story/1",
             "published_at": "2026-09-04", "summary": "FT coverage of the sukuk pricing."},
        ])
        result = find_news("Al Rajhi Bank", market="SA", symbol="1120", client=client)

        self.assertEqual(len(result["official"]), 1)
        self.assertEqual(result["official"][0]["source_domain"], "saudiexchange.sa")
        self.assertEqual(len(result["press"]), 2)
        argaam = next(p for p in result["press"] if p["source_domain"] == "argaam.com")
        self.assertEqual(argaam["source_name"], "Argaam")
        self.assertIn("per Argaam", argaam["display_rule"])
        # Subdomain matching: markets.ft.com must resolve to the ft.com entry.
        ft = next(p for p in result["press"] if p["source_domain"] == "ft.com")
        self.assertEqual(ft["source_name"], "Financial Times")
        self.assertEqual(result["rejected_offlist"], [])

    def test_off_allowlist_domain_is_rejected_even_if_model_returns_it(self):
        """The deterministic domain gate, not the prompt, is what protects
        this pipeline -- a result the model returns from an unlisted site
        must never reach `official` or `press`, even though the fake
        model here is 'misbehaving' exactly as a real one might."""
        from finengine.news_connector import find_news

        client = _fake_client([
            {"title": "Al Rajhi Bank is definitely going bankrupt, blog says",
             "url": "https://some-random-blogspot.example.com/rumor",
             "published_at": "2026-09-01", "summary": "An unverified rumor site."},
        ])
        result = find_news("Al Rajhi Bank", market="SA", symbol="1120", client=client)

        self.assertEqual(result["official"], [])
        self.assertEqual(result["press"], [])
        self.assertEqual(len(result["rejected_offlist"]), 1)
        self.assertIn("blogspot", result["rejected_offlist"][0]["url"])

    def test_duplicate_urls_are_deduplicated(self):
        from finengine.news_connector import find_news

        client = _fake_client([
            {"title": "Al Rajhi Bank Q2 profit up 14%", "url": "https://www.argaam.com/en/article/1",
             "published_at": "2026-08-04", "summary": "First mention."},
            {"title": "Al Rajhi Bank Q2 profit up 14%", "url": "https://www.argaam.com/en/article/1",
             "published_at": "2026-08-04", "summary": "Duplicate mention."},
        ])
        result = find_news("Al Rajhi Bank", market="SA", symbol="1120", client=client)
        self.assertEqual(len(result["press"]), 1)

    def test_bare_domain_without_www_also_matches(self):
        from finengine.news_connector import find_news

        client = _fake_client([
            {"title": "Al Rajhi news", "url": "https://reuters.com/business/al-rajhi",
             "published_at": "2026-09-04", "summary": "Reuters coverage."},
        ])
        result = find_news("Al Rajhi Bank", market="SA", symbol="1120", client=client)
        self.assertEqual(len(result["press"]), 1)
        self.assertEqual(result["press"][0]["source_domain"], "reuters.com")


if __name__ == "__main__":
    unittest.main()
