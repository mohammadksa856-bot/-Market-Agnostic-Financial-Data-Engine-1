from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from ..models import Company, DiscoveryResult, SourceCandidate


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None
            self._text = []


class IssuerReportsMonitor:
    """Discovers official PDF/XLSX reports without assuming a Saudi-only data model."""

    name = "issuer-reports"
    DEFAULT_KEYWORDS = (
        "annual report", "interim report", "financial report", "financial results",
        "financials", "databook",
    )

    def __init__(self, index_url: str, opener=urlopen, keywords: tuple[str, ...] | None = None,
                 max_documents: int = 12, user_agent: str = "MarketAgnosticFinancialDataEngine/0.6"):
        parsed = urlparse(index_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("issuer report index must be an HTTPS URL")
        self.index_url = index_url
        self.allowed_host = parsed.hostname.lower()
        self.opener = opener
        self.keywords = tuple(item.lower() for item in (keywords or self.DEFAULT_KEYWORDS))
        self.max_documents = max(1, min(max_documents, 1000))
        self.user_agent = user_agent

    def discover(self, company: Company, cursor: str | None = None) -> DiscoveryResult:
        request = Request(self.index_url, headers={"User-Agent": self.user_agent})
        with self.opener(request, timeout=45) as response:
            content = response.read(10_000_001)
        if len(content) > 10_000_000:
            raise ValueError("issuer report index exceeded 10 MB")
        parser = _LinkParser()
        parser.feed(content.decode("utf-8", "replace"))
        candidates: list[SourceCandidate] = []
        seen_urls: set[str] = set()
        for rank, (href, title) in enumerate(parser.links):
            full_url = urljoin(self.index_url, href)
            parsed = urlparse(full_url)
            path = unquote(parsed.path).lower()
            if parsed.scheme != "https" or parsed.hostname is None:
                continue
            host = parsed.hostname.lower()
            if host != self.allowed_host and not host.endswith("." + self.allowed_host):
                continue
            extension_match = re.search(r"\.(pdf|xlsx)(?:\$|$)", path)
            if not extension_match or full_url in seen_urls:
                continue
            normalized_title = title.strip() or parsed.path.rsplit("/", 1)[-1]
            if not any(keyword in normalized_title.lower() for keyword in self.keywords):
                continue
            seen_urls.add(full_url)
            extension = extension_match.group(1)
            document_type = self._document_type(normalized_title, extension)
            external_id = hashlib.sha256(full_url.encode("utf-8")).hexdigest()
            candidates.append(SourceCandidate(
                company.company_id, self.name, external_id, full_url, normalized_title,
                document_type, None,
                "application/pdf" if extension == "pdf" else
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                {"index_url": self.index_url, "rank": rank, "extension": extension},
            ))
            if len(candidates) >= self.max_documents:
                break
        digest = hashlib.sha256("\n".join(sorted(item.external_id for item in candidates)).encode("ascii")).hexdigest()
        if cursor == digest:
            return DiscoveryResult(digest, ())
        return DiscoveryResult(digest, tuple(candidates))

    @staticmethod
    def _document_type(title: str, extension: str) -> str:
        lowered = title.lower()
        if extension == "xlsx" or "databook" in lowered:
            return "databook"
        if "annual report" in lowered:
            return "annual-report"
        if "interim report" in lowered:
            return "interim-report"
        if "financial" in lowered:
            return "financial-report"
        return "issuer-report"
