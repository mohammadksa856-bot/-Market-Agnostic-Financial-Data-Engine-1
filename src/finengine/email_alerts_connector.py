from __future__ import annotations

"""Zero-AI-cost news connector: reads Google Alerts emails out of a Gmail
inbox via IMAP and matches them against the same named-outlet allowlist
used everywhere else in this project's news pipeline.

Google itself does the discovery (its own web crawler, covering vastly
more sites than the two RSS feeds `rss_news_connector.py` currently
covers) -- this module only does two things, both free: (1) read the
alert emails Google already sends, (2) decode each alert's Google
redirect link to the real article URL and check it against
`news_connector.ALLOWLIST`. An alert whose real destination is not on
the allowlist is reported in `rejected_offlist`, exactly like
`news_connector.py`'s search-tool path -- broader discovery does not
mean a lower trust bar.

Setup this module needs from the user (not built here, cannot be):
1. An active Google Alert for each company, delivered to a Gmail inbox
   this code can read.
2. A Gmail "App Password" for that inbox (myaccount.google.com/apppasswords
   -- requires 2-Step Verification), never the account's real password.
   Read from GOOGLE_ALERTS_EMAIL / GOOGLE_ALERTS_APP_PASSWORD in the
   environment (.env), the same pattern already used for
   ANTHROPIC_API_KEY in this repo.

Requires only the Python standard library (imaplib, email, html.parser)
-- no new dependency.
"""

import email
import imaplib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

from .news_connector import ALLOWLIST, _registrable_domain

GOOGLE_ALERTS_SENDER = "googlealerts-noreply@google.com"


@dataclass
class AlertItem:
    title: str
    real_url: str
    snippet: str


class _GoogleAlertHTMLParser(HTMLParser):
    """Walks a Google Alerts email body looking for `<a href="...">` tags
    whose href is a Google redirect carrying a `url=` query parameter --
    the actual link Google Alerts wraps every result in. Collects each
    such anchor's visible text as the title, and up to ~300 characters of
    the text that follows it (before the next such anchor) as the
    snippet. Deliberately does not assume a specific div/class structure,
    since Google has changed the surrounding markup before and will
    again -- the `url=` redirect pattern is the one stable signal."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items: list[AlertItem] = []
        self._current_url: str | None = None
        self._current_title_parts: list[str] = []
        self._in_alert_anchor = False
        self._trailing_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        real_url = _extract_redirect_target(href)
        if real_url:
            self._flush_trailing_snippet()
            self._current_url = real_url
            self._current_title_parts = []
            self._in_alert_anchor = True

    def handle_endtag(self, tag):
        if tag == "a" and self._in_alert_anchor:
            self._in_alert_anchor = False

    def handle_data(self, data):
        if self._in_alert_anchor:
            self._current_title_parts.append(data)
        elif self._current_url is not None:
            self._trailing_text.append(data)

    def _flush_trailing_snippet(self):
        if self._current_url is None:
            return
        title = re.sub(r"\s+", " ", "".join(self._current_title_parts)).strip()
        snippet = re.sub(r"\s+", " ", "".join(self._trailing_text)).strip()[:300]
        if title:
            self.items.append(AlertItem(title=title, real_url=self._current_url, snippet=snippet))
        self._current_url = None
        self._trailing_text = []

    def close(self):
        self._flush_trailing_snippet()
        super().close()


def _extract_redirect_target(href: str) -> str | None:
    """Pull the real destination out of a Google redirect URL
    (`https://www.google.com/url?...&url=<encoded>&...`). Returns None
    for anything that isn't that pattern -- e.g. Google's own
    unsubscribe/settings links in the same email, which must not be
    treated as article results."""
    if "google.com/url" not in href and "google.com/alerts" not in href:
        return None
    query = parse_qs(urlparse(href).query)
    candidates = query.get("url") or query.get("q")
    if not candidates:
        return None
    return candidates[0]


def parse_alert_email(html_body: str) -> list[AlertItem]:
    parser = _GoogleAlertHTMLParser()
    parser.feed(html_body)
    parser.close()
    return parser.items


def _connect(email_address: str, app_password: str) -> imaplib.IMAP4_SSL:
    connection = imaplib.IMAP4_SSL("imap.gmail.com")
    connection.login(email_address, app_password)
    return connection


def find_news_from_email_alerts(
    *, market: str, symbol: str, email_address: str, app_password: str,
    since_days: int = 2, mailbox: str = "INBOX", connector=_connect,
    allowlist: dict[str, dict] | None = None,
) -> dict:
    """Read recent Google Alerts emails from `mailbox` and split their
    results into `official`/`press`/`rejected_offlist` using the same
    domain allowlist as `news_connector.py`.

    `connector` is injectable for testing (return an object exposing the
    same `select`/`search`/`fetch`/`logout` surface as
    `imaplib.IMAP4_SSL`) so no test needs a real Gmail connection.
    """
    allowlist = allowlist or ALLOWLIST
    official: list[dict] = []
    press: list[dict] = []
    rejected_offlist: list[dict] = []
    seen_urls: set[str] = set()

    connection = connector(email_address, app_password)
    try:
        connection.select(mailbox)
        since = (datetime.now(timezone.utc).date())
        status, data = connection.search(
            None, f'(FROM "{GOOGLE_ALERTS_SENDER}" SINCE "{_imap_date(since_days)}")')
        if status != "OK":
            raise RuntimeError(f"IMAP search failed: {status}")
        message_ids = data[0].split()
        for message_id in message_ids:
            status, msg_data = connection.fetch(message_id, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            message = email.message_from_bytes(msg_data[0][1])
            html_body = _extract_html_body(message)
            if not html_body:
                continue
            for item in parse_alert_email(html_body):
                if item.real_url in seen_urls:
                    continue
                seen_urls.add(item.real_url)
                domain = _registrable_domain(item.real_url)
                if domain is None:
                    rejected_offlist.append({"title": item.title, "url": item.real_url})
                    continue
                source = allowlist[domain]
                record = {
                    "title": item.title, "url": item.real_url, "summary": item.snippet,
                    "source_domain": domain, "source_name": source["name"], "tier": source["tier"],
                    "display_rule": f"must show 'per {source['name']}' to the reader, never as a bare fact",
                }
                (official if source["tier"] == 1 else press).append(record)
    finally:
        try:
            connection.logout()
        except Exception:  # noqa: BLE001 - best-effort cleanup, never mask the real result
            pass

    return {
        "market": market, "symbol": symbol, "reader": "finengine.email_alerts_connector",
        "official": official, "press": press, "rejected_offlist": rejected_offlist,
        "cost": "zero (no LLM call, no search tool)",
    }


def _imap_date(days_ago: int) -> str:
    from datetime import timedelta

    return (datetime.now(timezone.utc).date() - timedelta(days=days_ago)).strftime("%d-%b-%Y")


def _extract_html_body(message: email.message.Message) -> str | None:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return None
    if message.get_content_type() == "text/html":
        payload = message.get_payload(decode=True)
        charset = message.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    return None
