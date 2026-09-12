from __future__ import annotations

"""News connector: finds recent coverage of a company from a fixed,
named allowlist of outlets, split into the two trust tiers this
project's news policy defines.

The safety gate here is NOT the model's judgment -- it is a deterministic
post-filter: every candidate result's URL is parsed and its registrable
domain checked against `ALLOWLIST` before anything is returned. The
search itself uses Claude's server-side web-search tool as a *retrieval*
mechanism (the model is prompted to restrict its search to the allowlist,
which helps relevance), but the actual admission gate does not trust that
prompt instruction -- a result from an unlisted domain is dropped even if
the model returned it. This mirrors the same principle as
`reading_qualitative.py`: never let the model's own claim be the last
line of defense.

Requires the optional `llm` extra and an `ANTHROPIC_API_KEY`. Confined to
staging: callers must publish `official` results as `disclosures` with
disclosure_type `official_announcement`, and `press` results as
disclosure_type `press_coverage`, each carrying the outlet name/URL/tier
in metadata per this project's display rule (press coverage must always
be shown attributed to its publisher, never as a bare fact).
"""

import json
import re
from urllib.parse import urlparse

# Measured live against the real API during development (2026-09-12), same
# task, same company: Opus 5 cost ~$1.04/run (47,122 in / 3,157 out tokens,
# 12 web searches); Haiku 4.5 cost ~$0.02/run (10,401 in / 477 out tokens) --
# roughly 50x cheaper, at the cost of finding fewer results per run in that
# comparison. Opus remains available via the `model=` argument for a company
# that needs deeper digging, but the default favors the cost that is actually
# viable to run across hundreds of companies on a recurring schedule. Prefer
# `rss_news_connector.py` first wherever it covers a company/outlet -- it is
# free -- and reserve this module for what an RSS feed can't surface.
DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# Named, reputable outlets only -- widened per the 2026-09-12 request to
# go beyond the original 3-outlet pilot (Reuters, Argaam, Maaal). Tier 1
# is an issuer's/exchange's own official channel (same trust level as a
# financial disclosure); Tier 2 is third-party journalism, always
# attributed, never presented as an engine-verified fact. Add outlets
# here only -- never widen matching logic to "anything that looks
# official" in code, since that is exactly how an unreliable source
# would sneak in.
ALLOWLIST: dict[str, dict] = {
    # Tier 1 -- official / exchange / state news channels
    "saudiexchange.sa": {"tier": 1, "name": "Saudi Exchange (Tadawul) issuer announcements"},
    "spa.gov.sa": {"tier": 1, "name": "Saudi Press Agency"},
    "cma.org.sa": {"tier": 1, "name": "Capital Market Authority"},
    # Tier 2 -- named international financial press
    "reuters.com": {"tier": 2, "name": "Reuters"},
    "bloomberg.com": {"tier": 2, "name": "Bloomberg"},
    "wsj.com": {"tier": 2, "name": "The Wall Street Journal"},
    "ft.com": {"tier": 2, "name": "Financial Times"},
    "cnbc.com": {"tier": 2, "name": "CNBC"},
    # Tier 2 -- named Gulf/Saudi financial press
    "argaam.com": {"tier": 2, "name": "Argaam"},
    "maaal.com": {"tier": 2, "name": "Maaal"},
    "aleqt.com": {"tier": 2, "name": "Al-Eqtisadiah (الاقتصادية)"},
    "asharqbusiness.com": {"tier": 2, "name": "Asharq Business"},
    "cnbcarabia.com": {"tier": 2, "name": "CNBC Arabia"},
    "zawya.com": {"tier": 2, "name": "Zawya"},
    "mubasher.info": {"tier": 2, "name": "Mubasher"},
    "arabnews.com": {"tier": 2, "name": "Arab News"},
    "aawsat.com": {"tier": 2, "name": "Asharq Al-Awsat"},
    "okaz.com.sa": {"tier": 2, "name": "Okaz"},
}


def _registrable_domain(url: str) -> str | None:
    try:
        host = urlparse(url).hostname
    except ValueError:
        return None
    if not host:
        return None
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    # Match the allowlist entry itself or any subdomain of it
    # (e.g. "markets.ft.com" matches the "ft.com" entry).
    for domain in ALLOWLIST:
        if host == domain or host.endswith("." + domain):
            return domain
    return None


_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "published_at": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["title", "url", "summary"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["results"],
    "additionalProperties": False,
}


def _search(company_name: str, market: str, symbol: str, client, model: str):
    allowed = ", ".join(sorted(ALLOWLIST))
    system = (
        "You search the web for recent news about one company and report only what "
        "you find, never inventing an article. Restrict your search to these named "
        "outlets only (do not report results from any other site, even if relevant): "
        f"{allowed}. For each article found, report its exact headline, its exact "
        "URL, its publication date if shown, and a short factual summary in your own "
        "words. Never fabricate a URL or a date. If you find nothing on an allowed "
        "outlet, return an empty results list rather than substituting an off-list "
        "source."
    )
    user = f"Company: {company_name} (ticker {symbol}, {market}). Find its most recent news."
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=system,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
    )
    payload = json.loads(next(b.text for b in response.content if b.type == "text"))
    return payload.get("results", []), response.usage


def find_news(
    company_name: str, *, market: str, symbol: str, model: str = DEFAULT_MODEL,
    client=None,
) -> dict:
    """Search the named allowlist for recent company news.

    Returns `official` (tier 1) and `press` (tier 2) lists, each item
    carrying its verified source domain/name and a `display_rule` string
    reminding the caller how it must be shown. Any result whose URL does
    not resolve to an allowlisted domain is placed in `rejected_offlist`
    instead -- dropped from publication, kept only for visibility into
    what the search step returned so a reviewer can widen the allowlist
    deliberately later, rather than the filter silently discarding
    everything with no record.
    """
    if client is None:
        try:
            import anthropic
        except ImportError as error:  # pragma: no cover - environment dependent
            raise RuntimeError(
                'the news connector needs the optional "llm" extra: pip install -e ".[llm]"'
            ) from error
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

    raw_results, usage = _search(company_name, market, symbol, client, model)

    official: list[dict] = []
    press: list[dict] = []
    rejected_offlist: list[dict] = []
    seen_urls: set[str] = set()
    for item in raw_results:
        url = item.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        domain = _registrable_domain(url)
        if domain is None:
            rejected_offlist.append(item)
            continue
        source = ALLOWLIST[domain]
        record = {
            "title": item["title"].strip(),
            "url": url,
            "published_at": item.get("published_at") or None,
            "summary": item["summary"].strip(),
            "source_domain": domain,
            "source_name": source["name"],
            "tier": source["tier"],
            "display_rule": f"must show 'per {source['name']}' to the reader, never as a bare fact",
        }
        (official if source["tier"] == 1 else press).append(record)

    return {
        "market": market, "symbol": symbol, "company_name": company_name,
        "reader": f"finengine.news_connector/{model}",
        "official": official, "press": press, "rejected_offlist": rejected_offlist,
        "model_usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
    }
