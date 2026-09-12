import email
import email.message
import unittest
from urllib.parse import quote

REAL_ARTICLE_URL = "https://www.argaam.com/en/article/articledetail/id/1935133"
OFFLIST_URL = "https://some-random-blog.example.com/rumor-about-al-rajhi"
UNSUBSCRIBE_URL = "https://www.google.com/alerts/manage?hl=en"

SAMPLE_ALERT_HTML = f"""
<html><body>
<div>
  <a href="https://www.google.com/url?rct=j&sa=t&url={quote(REAL_ARTICLE_URL, safe='')}&ct=ga&cd=1">
    Al Rajhi Bank <b>acquires</b> stake in fintech firm
  </a>
  <div>Al Rajhi Bank announced today a new investment in a Riyadh-based fintech startup...</div>
</div>
<div>
  <a href="https://www.google.com/url?rct=j&sa=t&url={quote(OFFLIST_URL, safe='')}&ct=ga&cd=2">
    Al Rajhi Bank is secretly bankrupt says anonymous blog
  </a>
  <div>An unverified claim with no named source...</div>
</div>
<a href="{UNSUBSCRIBE_URL}">Unsubscribe from this alert</a>
</body></html>
"""


def _make_raw_email(html_body: str) -> bytes:
    msg = email.message.EmailMessage()
    msg["From"] = "Google Alerts <googlealerts-noreply@google.com>"
    msg["Subject"] = "Google Alert - Al Rajhi Bank"
    msg.set_content("plain text fallback")
    msg.add_alternative(html_body, subtype="html")
    return bytes(msg)


class ParseAlertEmailTests(unittest.TestCase):
    def test_extracts_real_url_and_title_ignoring_unsubscribe_link(self):
        from finengine.email_alerts_connector import parse_alert_email

        items = parse_alert_email(SAMPLE_ALERT_HTML)
        urls = [item.real_url for item in items]
        self.assertIn(REAL_ARTICLE_URL, urls)
        self.assertIn(OFFLIST_URL, urls)
        self.assertNotIn(UNSUBSCRIBE_URL, urls)

        argaam_item = next(i for i in items if i.real_url == REAL_ARTICLE_URL)
        self.assertIn("Al Rajhi Bank", argaam_item.title)
        self.assertIn("fintech", argaam_item.snippet.lower())


class _FakeImap:
    """Minimal stand-in for imaplib.IMAP4_SSL exposing only what
    find_news_from_email_alerts uses."""

    def __init__(self, raw_messages: list[bytes]):
        self._raw_messages = raw_messages

    def select(self, mailbox):
        return "OK", [b""]

    def search(self, charset, criteria):
        ids = [str(i).encode() for i in range(len(self._raw_messages))]
        return "OK", [b" ".join(ids)]

    def fetch(self, message_id, parts):
        index = int(message_id)
        return "OK", [(b"1 (RFC822 {n})", self._raw_messages[index])]

    def logout(self):
        pass


class FindNewsFromEmailAlertsTests(unittest.TestCase):
    def test_splits_allowlisted_and_rejects_offlist_from_a_real_looking_email(self):
        from finengine.email_alerts_connector import find_news_from_email_alerts

        raw = _make_raw_email(SAMPLE_ALERT_HTML)
        fake_imap = _FakeImap([raw])
        result = find_news_from_email_alerts(
            market="SA", symbol="1120", email_address="test@example.test",
            app_password="fake-app-password", connector=lambda *a, **k: fake_imap)

        self.assertEqual(len(result["press"]), 1)
        self.assertEqual(result["press"][0]["url"], REAL_ARTICLE_URL)
        self.assertEqual(result["press"][0]["source_name"], "Argaam")
        self.assertEqual(len(result["rejected_offlist"]), 1)
        self.assertEqual(result["rejected_offlist"][0]["url"], OFFLIST_URL)
        self.assertEqual(result["cost"], "zero (no LLM call, no search tool)")

    def test_no_alert_emails_returns_empty_not_error(self):
        from finengine.email_alerts_connector import find_news_from_email_alerts

        fake_imap = _FakeImap([])
        result = find_news_from_email_alerts(
            market="SA", symbol="1120", email_address="test@example.test",
            app_password="fake-app-password", connector=lambda *a, **k: fake_imap)
        self.assertEqual(result["official"], [])
        self.assertEqual(result["press"], [])

    def test_search_failure_raises_rather_than_reporting_false_silence(self):
        from finengine.email_alerts_connector import find_news_from_email_alerts

        class BrokenImap(_FakeImap):
            def search(self, charset, criteria):
                return "NO", [b""]

        with self.assertRaises(RuntimeError):
            find_news_from_email_alerts(
                market="SA", symbol="1120", email_address="test@example.test",
                app_password="fake-app-password", connector=lambda *a, **k: BrokenImap([]))


if __name__ == "__main__":
    unittest.main()
