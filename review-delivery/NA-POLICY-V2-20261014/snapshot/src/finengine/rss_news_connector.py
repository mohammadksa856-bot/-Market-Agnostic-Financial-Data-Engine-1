from __future__ import annotations

"""Zero-AI-cost news connector: polls named outlets' own public RSS feeds
and matches company mentions with plain string matching -- no LLM call,
no web-search tool, no per-run API cost at all.

Built as the cheaper alternative to `news_connector.py` (which uses
Claude's web-search tool and costs real money per call -- roughly $1/run
on Opus, ~$0.02/run on Haiku, measured against the live API during this
project). This module trades that cost for a real capability gap: it can
only ever surface what a feed already published, using only the words
the feed's own author chose. It cannot go read a fresh page or judge
relevance the way an LLM-driven search can, so it should be the FIRST
check (cheap, frequent, e.g. hourly), with the LLM-driven connector
reserved as an occasional fallback for companies it turns up nothing for
over some longer window -- not a full replacement.

Same trust-tier and output shape as `news_connector.py`'s `find_news()`
so a caller can treat both as interchangeable sources into the same
publication path.
"""

import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Feeds actually fetched and verified live during development (2026-09-12).
# Each entry names the outlet (for attribution/display) and its trust tier.
# Only add a feed here after confirming it returns real, parseable RSS --
# a dead or malformed URL should not silently produce zero results forever.
FEEDS: dict[str, dict] = {
    "https://www.argaam.com/en/rss/ho-company-disclosures?sectionid=244": {
        "source_name": "Argaam", "source_domain": "argaam.com", "tier": 2,
        "feed_label": "Argaam — company disclosures",
    },
    "https://www.argaam.com/en/rss/companies?sectionid=1542": {
        "source_name": "Argaam", "source_domain": "argaam.com", "tier": 2,
        "feed_label": "Argaam — companies",
    },
}

# Outlets researched but NOT wired in yet, kept here so the next person
# doesn't have to re-derive this: Reuters discontinued public RSS feeds
# entirely (confirmed by search, no official feed exists to fetch);
# Arab News's advertised /rss endpoint returned an empty/non-XML response
# when fetched directly (needs a browser-rendered fetch or different
# headers, not a plain HTTP GET) -- unresolved, not silently assumed dead.


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("‎", "").replace("‏", "")  # LTR/RTL marks
    return re.sub(r"\s+", " ", text).strip().lower()


@dataclass
class FeedItem:
    title: str
    link: str
    summary: str
    published_at: str | None
    source_name: str
    source_domain: str
    tier: int


def _parse_feed(xml_bytes: bytes, feed_meta: dict) -> list[FeedItem]:
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall(".//item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        date_el = item.find("pubDate")
        if title_el is None or link_el is None:
            continue
        published_at = None
        if date_el is not None and date_el.text:
            try:
                published_at = parsedate_to_datetime(date_el.text).astimezone(timezone.utc).isoformat()
            except (TypeError, ValueError):
                published_at = date_el.text.strip()
        items.append(FeedItem(
            title=_normalize_display(title_el.text or ""),
            link=(link_el.text or "").strip(),
            summary=_strip_html(desc_el.text if desc_el is not None else "")[:500],
            published_at=published_at,
            source_name=feed_meta["source_name"],
            source_domain=feed_meta["source_domain"],
            tier=feed_meta["tier"],
        ))
    return items


def _normalize_display(text: str) -> str:
    return text.replace("‎", "").replace("‏", "").strip()


def _fetch(url: str, timeout: int = 15) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _matches_company(item: FeedItem, company_names: list[str]) -> bool:
    haystack = _normalize(item.title) + " " + _normalize(item.summary)
    return any(_normalize(name) in haystack for name in company_names if name)


def find_news_rss(
    company_names: list[str], *, market: str, symbol: str,
    feeds: dict[str, dict] | None = None, fetcher=_fetch,
) -> dict:
    """Poll the configured RSS feeds for mentions of any of `company_names`
    (pass every name/alias worth matching -- English, Arabic, with and
    without 'Company'/'شركة', since feeds are not consistent about which
    form they use).

    Zero LLM cost: `fetcher` defaults to a plain HTTP GET; inject a fake
    one in tests. Returns the same `official`/`press` shape as
    `news_connector.find_news`, plus `feed_errors` for any feed that
    failed to fetch or parse -- surfaced, never silently swallowed, since
    a feed silently going stale would otherwise look identical to "no
    news happened".
    """
    feeds = feeds or FEEDS
    official: list[dict] = []
    press: list[dict] = []
    feed_errors: list[dict] = []
    seen_links: set[str] = set()

    for url, meta in feeds.items():
        try:
            raw = fetcher(url)
            items = _parse_feed(raw, meta)
        except Exception as error:  # noqa: BLE001 - any feed failure is reported, not fatal
            feed_errors.append({"feed_url": url, "error": f"{type(error).__name__}: {error}"})
            continue
        for item in items:
            if item.link in seen_links or not _matches_company(item, company_names):
                continue
            seen_links.add(item.link)
            record = {
                "title": item.title, "url": item.link, "published_at": item.published_at,
                "summary": item.summary, "source_domain": item.source_domain,
                "source_name": item.source_name, "tier": item.tier,
                "display_rule": f"must show 'per {item.source_name}' to the reader, never as a bare fact",
                "feed_url": url,
            }
            (official if item.tier == 1 else press).append(record)

    return {
        "market": market, "symbol": symbol, "company_names": company_names,
        "reader": "finengine.rss_news_connector", "official": official, "press": press,
        "feed_errors": feed_errors, "cost": "zero (no LLM call)",
    }
