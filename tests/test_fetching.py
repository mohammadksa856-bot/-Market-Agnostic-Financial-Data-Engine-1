import unittest

from finengine.fetching import BrowserFetcher, _slug


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


if __name__ == "__main__":
    unittest.main()
