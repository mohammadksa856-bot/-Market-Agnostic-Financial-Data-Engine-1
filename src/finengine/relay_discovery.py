from __future__ import annotations

"""Bounded, restart-safe discovery policy for the residential Saudi relay.

The browser fetcher answers the question "what is linked by this official
page?".  This module deliberately keeps the relay's scheduling policy separate:
visit every configured source, remove work that is already durable, and only
then spend the per-company upload budget.  Keeping those phases separate is
important for historical backfills because issuer libraries normally return
their newest links first.
"""

from dataclasses import dataclass
import re
from typing import Callable, Iterable, Mapping
from urllib.parse import unquote


DEFAULT_DISCOVERY_LIMIT_PER_SOURCE = 200
ANNUAL_COVERAGE_TARGET = 5
QUARTER_COVERAGE_TARGET = 12

_OUTBOX_STATUSES = {
    "pending_archive",
    "pending_enqueue",
    "job_created",
    "duplicate_job",
    "published_duplicate",
}

_QUARTER_PATTERNS = (
    (1, re.compile(r"(?:^|[^a-z0-9])(?:q\s*1|1\s*q)(?:[^a-z0-9]|$)|\bfirst\s+quarter\b|\b3\s+months?\b|الربع\s+(?:الأول|الاول)", re.I)),
    (2, re.compile(r"(?:^|[^a-z0-9])(?:q\s*2|2\s*q|h\s*1)(?:[^a-z0-9]|$)|\bsecond\s+quarter\b|\bhalf[- ]?year\b|\bsix\s+months?\b|الربع\s+الثاني|النصف\s+الأول", re.I)),
    (3, re.compile(r"(?:^|[^a-z0-9])(?:q\s*3|3\s*q)(?:[^a-z0-9]|$)|\bthird\s+quarter\b|\bnine\s+months?\b|الربع\s+الثالث", re.I)),
    (4, re.compile(r"(?:^|[^a-z0-9])(?:q\s*4|4\s*q|h\s*2)(?:[^a-z0-9]|$)|\bfourth\s+quarter\b|الربع\s+الرابع|النصف\s+الثاني", re.I)),
)
_ANNUAL_PATTERN = re.compile(
    r"\bannual\b|\byear(?:ly)?\s+(?:ended|ending|report|results?)\b|"
    r"(?:^|[^a-z0-9])fy\s*20\d{2}(?:[^a-z0-9]|$)|"
    r"التقرير\s+السنوي|تقارير\s+سنوية|سنوي",
    re.I,
)
_FINANCIAL_PATTERN = re.compile(
    r"financial\s+(?:statement|report|result)|consolidated|"
    r"القوائم\s+المالية|النتائج\s+المالية",
    re.I,
)
_YEAR_PATTERN = re.compile(r"(?<!\d)(20(?:0\d|1\d|2\d))(?!\d)")


@dataclass(frozen=True)
class DiscoverySource:
    url: str
    crawl_issuer_site: bool = False


@dataclass(frozen=True)
class SourceFailure:
    source_url: str
    error: Exception


@dataclass(frozen=True)
class CompanyDiscovery:
    candidates: tuple[dict, ...]
    source_failures: tuple[SourceFailure, ...]

    @property
    def needs_retry(self) -> bool:
        """A partial source failure must survive even when another source worked."""
        return bool(self.source_failures)


def discovery_sources(
    company: Mapping,
    profile_url: str,
    crawl_profile_issuer_site: bool,
) -> tuple[DiscoverySource, ...]:
    """Build a de-duplicated source plan, always ending with the Exchange profile.

    Configured issuer pages are already the trusted pages to crawl, so recursive
    issuer-site discovery is disabled for them.  Only the Saudi Exchange profile
    is allowed to use its labelled official-company-site bridge.
    """
    urls: list[str] = []
    # Reviewed source-registry pages are direct discovery inputs.  The command
    # line flag controls only whether the Exchange profile may follow its
    # issuer-website link; it must not hide the configured sources themselves.
    for source in company.get("sources") or ():
        url = source.get("url") if isinstance(source, Mapping) else source
        if isinstance(url, str) and url.startswith("https://") and url not in urls:
            urls.append(url)
    if profile_url not in urls:
        urls.append(profile_url)
    return tuple(
        DiscoverySource(
            url,
            crawl_issuer_site=bool(crawl_profile_issuer_site and url == profile_url),
        )
        for url in urls
    )


def gather_company_candidates(
    fetcher,
    company: Mapping,
    profile_url: str,
    crawl_profile_issuer_site: bool,
    *,
    max_candidates_per_source: int = DEFAULT_DISCOVERY_LIMIT_PER_SOURCE,
    on_source_failure: Callable[[SourceFailure], None] | None = None,
) -> CompanyDiscovery:
    """Discover from every source before any upload budget is applied."""
    limit = max(1, min(int(max_candidates_per_source), 200))
    found: list[dict] = []
    seen_urls: set[str] = set()
    failures: list[SourceFailure] = []
    for source in discovery_sources(company, profile_url, crawl_profile_issuer_site):
        try:
            discovered = fetcher.discover(
                source.url,
                max_documents=limit,
                crawl_issuer_site=source.crawl_issuer_site,
            )
        except Exception as error:  # source isolation is the point of this layer
            failure = SourceFailure(source.url, error)
            failures.append(failure)
            if on_source_failure is not None:
                on_source_failure(failure)
            continue
        for candidate in discovered:
            url = candidate.get("url") if isinstance(candidate, Mapping) else None
            if not isinstance(url, str) or not url or url in seen_urls:
                continue
            seen_urls.add(url)
            # Preserve provenance for classification/debugging without changing
            # the browser fetcher's public result contract.
            item = dict(candidate)
            item.setdefault("discovery_source", source.url)
            found.append(item)
    return CompanyDiscovery(tuple(found), tuple(failures))


def excluded_candidate_urls(
    seen: Mapping | Iterable | None,
    outbox: Mapping | Iterable | None = None,
) -> set[str]:
    """Return URLs already published or represented by durable outbox work.

    The outbox reader accepts the versioned relay shape as well as a flat list,
    which keeps rolling upgrades safe while the outbox implementation lands.
    """
    excluded: set[str] = set()
    if isinstance(seen, Mapping):
        excluded.update(str(url) for url in seen if isinstance(url, str))
    elif seen is not None:
        for item in seen:
            if isinstance(item, str):
                excluded.add(item)
            elif isinstance(item, Mapping):
                url = item.get("source_url") or item.get("url")
                if isinstance(url, str):
                    excluded.add(url)

    entries: Iterable = ()
    if isinstance(outbox, Mapping):
        documents = outbox.get("documents", outbox)
        entries = documents.values() if isinstance(documents, Mapping) else documents or ()
    elif outbox is not None:
        entries = outbox
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        candidate = entry.get("candidate")
        url = entry.get("source_url") or entry.get("url")
        if not url and isinstance(candidate, Mapping):
            url = candidate.get("source_url") or candidate.get("url")
        status = str(entry.get("status") or "")
        # Every defined outbox state represents durable local work.  The
        # local_path fallback tolerates pre-versioned entries during rollout.
        if isinstance(url, str) and (
            status in _OUTBOX_STATUSES or bool(entry.get("local_path"))
        ):
            excluded.add(url)
    return excluded


def eligible_candidates(
    candidates: Iterable[Mapping],
    seen: Mapping | Iterable | None,
    outbox: Mapping | Iterable | None = None,
) -> list[dict]:
    excluded = excluded_candidate_urls(seen, outbox)
    eligible: list[dict] = []
    local_seen: set[str] = set()
    for candidate in candidates:
        url = candidate.get("url")
        if not isinstance(url, str) or not url or url in excluded or url in local_seen:
            continue
        local_seen.add(url)
        eligible.append(dict(candidate))
    return eligible


def _candidate_period(candidate: Mapping) -> tuple[str, str]:
    text = " ".join(
        str(candidate.get(key) or "")
        for key in ("title", "url", "discovery_source", "document_type", "filing_type")
    )
    text = unquote(text).replace("_", " ").replace("-", " ")
    lowered = text.lower()
    years = [int(value) for value in _YEAR_PATTERN.findall(lowered)]
    year = max(years) if years else None
    explicit_type = str(
        candidate.get("document_type") or candidate.get("filing_type") or ""
    ).lower()
    for quarter, pattern in _QUARTER_PATTERNS:
        if pattern.search(lowered):
            return "quarter", f"{year or 'unknown'}-Q{quarter}"
    if ("interim" in explicit_type or "quarter" in explicit_type or
            re.search(r"\b(?:interim|quarterly?)\b|مرحلية|ربع\s+سنوي", lowered)):
        return "quarter", f"{year or 'unknown'}:{candidate.get('url')}"
    if "annual" in explicit_type or _ANNUAL_PATTERN.search(lowered):
        return "annual", str(year or candidate.get("url"))
    # A year-labelled full financial statement with no interim token is normally
    # the issuer's FY filing (common labels are just "Financial Statements 2024").
    if year is not None and _FINANCIAL_PATTERN.search(lowered):
        return "annual", str(year)
    return "other", str(candidate.get("url") or "")


def select_upload_candidates(
    candidates: Iterable[Mapping],
    upload_budget: int,
    *,
    seen: Mapping | Iterable | None = None,
    outbox: Mapping | Iterable | None = None,
) -> list[dict]:
    """Choose new work fairly, targeting five FYs and twelve interim periods.

    The weighted loop advances whichever coverage target is proportionally
    furthest behind.  With a budget of ten and enough of both kinds this yields
    three annual and seven interim filings, rather than letting the registry's
    first (usually annual) source consume all ten slots.
    """
    budget = max(0, int(upload_budget))
    if budget == 0:
        return []
    eligible = eligible_candidates(candidates, seen, outbox)
    if len(eligible) <= budget:
        return eligible

    annual: list[dict] = []
    quarters: list[dict] = []
    annual_periods: set[str] = set()
    quarter_periods: set[str] = set()
    for candidate in eligible:
        kind, period = _candidate_period(candidate)
        if kind == "annual" and period not in annual_periods:
            annual_periods.add(period)
            annual.append(candidate)
        elif kind == "quarter" and period not in quarter_periods:
            quarter_periods.add(period)
            quarters.append(candidate)

    selected: list[dict] = []
    selected_urls: set[str] = set()
    annual_count = quarter_count = 0
    annual_index = quarter_index = 0
    while len(selected) < budget:
        can_annual = (
            annual_count < ANNUAL_COVERAGE_TARGET and annual_index < len(annual)
        )
        can_quarter = (
            quarter_count < QUARTER_COVERAGE_TARGET and quarter_index < len(quarters)
        )
        if not can_annual and not can_quarter:
            break
        choose_quarter = can_quarter and (
            not can_annual
            or (quarter_count + 1) / QUARTER_COVERAGE_TARGET
            <= (annual_count + 1) / ANNUAL_COVERAGE_TARGET
        )
        if choose_quarter:
            candidate = quarters[quarter_index]
            quarter_index += 1
            quarter_count += 1
        else:
            candidate = annual[annual_index]
            annual_index += 1
            annual_count += 1
        selected.append(candidate)
        selected_urls.add(candidate["url"])

    # Fill spare capacity in original discovery order.  This retains useful
    # supplements, duplicate-period language variants, and deeper history after
    # the primary 5-FY/12-quarter coverage has been advanced.
    for candidate in _round_robin_by_source(eligible):
        if len(selected) >= budget:
            break
        if candidate["url"] in selected_urls:
            continue
        selected.append(candidate)
        selected_urls.add(candidate["url"])
    return selected


def _round_robin_by_source(candidates: Iterable[dict]) -> list[dict]:
    """Keep unclassified/extra documents from being dominated by source order."""
    source_order: list[str] = []
    buckets: dict[str, list[dict]] = {}
    for candidate in candidates:
        source = str(candidate.get("discovery_source") or "")
        if source not in buckets:
            source_order.append(source)
            buckets[source] = []
        buckets[source].append(candidate)
    ordered: list[dict] = []
    index = 0
    while True:
        added = False
        for source in source_order:
            bucket = buckets[source]
            if index < len(bucket):
                ordered.append(bucket[index])
                added = True
        if not added:
            break
        index += 1
    return ordered
