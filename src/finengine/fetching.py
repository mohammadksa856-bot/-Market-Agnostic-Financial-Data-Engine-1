from __future__ import annotations

"""Fetch agent: pull a filed document through a real browser engine.

Simple HTTP clients are blocked by the CDN / bot protection in front of several
official issuer sites (Akamai, Cloudflare). A headless Chromium context presents
a real TLS/HTTP2 fingerprint and passes most of them, and downloads through the
same context so referer and hotlink checks are satisfied.

This only *archives* documents into immutable staging with a SHA-256; it never
extracts or publishes. Requires the optional `browser` extra
(`pip install -e ".[browser]" && playwright install chromium`).

Bot protection is partly IP-reputation based: a residential connection in the
issuer's country gets through sites that reject a datacenter IP. Tadawul in
particular stays hostile to automation - prefer issuer investor-relations pages.
"""

import hashlib
import re
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
_KEYWORDS = ("financial statement", "financial results", "interim", "annual report",
             "consolidated", "quarterly", "half year", "data supplement", "databook",
             "القوائم المالية",
             "النتائج المالية", "التقرير السنوي", "تقارير سنوية", "ربع سنوي",
             "مرحلية")
_SAUDI_EXCHANGE_HOST = "www.saudiexchange.sa"
_XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_ONCLICK_LOCATION = re.compile(
    r"document\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", re.I
)


def _slug(url: str) -> str:
    name = Path(unquote(urlparse(url).path)).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "document.pdf"


def _validate_document_bytes(content: bytes, url: str, content_type: str) -> None:
    if content_type == "application/pdf" and not content.startswith(b"%PDF"):
        raise RuntimeError(f"downloaded content is not a PDF: {url}")
    if content_type == _XLSX_CONTENT_TYPE and not content.startswith(b"PK\x03\x04"):
        raise RuntimeError(f"downloaded content is not an XLSX workbook: {url}")


def _request_document_bytes(context, url: str, referer: str | None = None,
                            timeout_ms: int = 60000) -> bytes:
    """Download through Playwright's cookie-sharing request context.

    Some issuer pages allow the document itself but block an in-page ``fetch``
    with CORS.  ``BrowserContext.request`` shares the browser cookie jar without
    being subject to page CORS, so it is the safe second path after visiting the
    official referer.
    """
    options = {"timeout": timeout_ms}
    if referer:
        options["headers"] = {"Referer": referer}
    response = context.request.get(url, **options)
    if not response.ok:
        raise RuntimeError(f"fetch failed: HTTP {response.status} for {url}")
    return response.body()


def _direct_document_bytes(url: str, referer: str | None = None,
                           timeout_seconds: float = 60, opener=urlopen,
                           max_bytes: int = 100 * 1024 * 1024) -> bytes:
    """Bounded ordinary-HTTP fallback for issuer CDNs with inverted bot rules."""
    headers = {"User-Agent": "MarketAgnosticFinancialDataEngine/0.6"}
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    chunks, total = [], 0
    with opener(request, timeout=timeout_seconds) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"document exceeded {max_bytes} bytes")
            chunks.append(chunk)
    return b"".join(chunks)


def _published_at_from_url(url: str) -> str | None:
    """Extract only an explicit ISO upload date embedded in a document path."""
    match = re.search(r"(?:^|[_/])(20\d{2}-\d{2}-\d{2})(?:[_./-]|$)", unquote(urlparse(url).path))
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1)).isoformat()
    except ValueError:
        return None


def _saudi_financial_announcement_links(index_url: str, rows: list[dict],
                                        keywords: tuple[str, ...] = _KEYWORDS) -> list[dict]:
    """Extract official announcement-detail links from Saudi Exchange onclick cards."""
    found, seen = [], set()
    for row in rows:
        title = " ".join(str(row.get("text") or "").split())
        match = _ONCLICK_LOCATION.search(str(row.get("onclick") or ""))
        if not match or not any(keyword in title.lower() for keyword in keywords):
            continue
        url = urljoin(index_url, match.group(1).replace("&amp;", "&"))
        parsed = urlparse(url)
        if (parsed.scheme != "https" or parsed.hostname != _SAUDI_EXCHANGE_HOST or
                url in seen):
            continue
        seen.add(url)
        found.append({"url": url, "title": title})
    return found


def _official_issuer_websites(index_url: str, links: list[list[str]]) -> list[str]:
    """Select company websites explicitly labelled as their own hostname.

    Saudi Exchange profiles contain social and group-wide external links too. A
    hostname-labelled anchor (for example ``www.sabic.com``) is the conservative
    signal used for the issuer's own site; HTTP links are upgraded to HTTPS.
    """
    exchange_host = (urlparse(index_url).hostname or "").lower()
    found, seen = [], set()
    for href, text in links:
        parsed = urlparse(urljoin(index_url, href))
        hostname = (parsed.hostname or "").lower()
        label = str(text or "").strip().lower().rstrip("/")
        expected = {hostname, f"www.{hostname}" if not hostname.startswith("www.")
                    else hostname[4:]}
        if (parsed.scheme not in {"http", "https"} or not hostname or
                hostname == exchange_host or label not in expected):
            continue
        secure = urlunparse(("https", parsed.netloc, parsed.path or "/",
                             parsed.params, parsed.query, ""))
        if secure not in seen:
            seen.add(secure)
            found.append(secure)
    return found


class BrowserFetcher:
    def __init__(self, raw_dir: str | Path = "data/raw", headless: bool = True,
                 timeout_ms: int = 60000):
        self.raw_dir = Path(raw_dir)
        self.headless = headless
        self.timeout_ms = timeout_ms

    def _context(self, stack):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "the fetch agent needs the optional 'browser' extra: "
                "pip install -e \".[browser]\" && playwright install chromium"
            ) from error
        pw = stack.enter_context(sync_playwright())
        browser = pw.chromium.launch(headless=self.headless)
        stack.callback(browser.close)
        return browser.new_context(accept_downloads=True, user_agent=_UA,
                                   locale="en-US", ignore_https_errors=True)

    def discover(self, index_url: str, keywords: tuple[str, ...] = _KEYWORDS) -> list[dict]:
        """Render an investor-relations page and return candidate filing links."""
        import contextlib
        host = urlparse(index_url).hostname or ""
        allowed_hosts = {host}
        trusted_documents: set[str] = set()
        referers: dict[str, str] = {}
        with contextlib.ExitStack() as stack:
            context = self._context(stack)
            page = context.new_page()
            page.goto(index_url, timeout=self.timeout_ms, wait_until="domcontentloaded")
            # give client-rendered link lists a moment; do not wait for networkidle -
            # corporate sites keep long-poll / analytics connections open forever.
            with contextlib.suppress(Exception):
                page.wait_for_load_state("load", timeout=8000)
            page.wait_for_timeout(2500)
            raw = page.eval_on_selector_all(
                "a[href]", "els => els.map(e => { "
                "const label=(e.textContent||'').trim(); let node=e.parentElement; "
                "let heading=''; for(let i=0;i<4 && node;i++,node=node.parentElement){ "
                "const own=[...node.children].find(c => /^H[1-6]$/.test(c.tagName)); "
                "if(own){ heading=(own.textContent||'').trim(); break; } } "
                "return [e.href,(heading+' '+label).trim()]; })")
            # Exact document URLs linked by the configured official source page
            # may live on the issuer's cloud/CDN hostname. The trust is the link
            # provenance, not a broad allow-list for that external host.
            for linked_url, _ in raw:
                linked = urlparse(linked_url)
                if (linked.scheme == "https" and linked.hostname and
                        any(ext in linked.path.lower() for ext in (".pdf", ".xlsx"))):
                    trusted_documents.add(linked_url)
                    referers[linked_url] = page.url
            # Saudi Exchange's company profile uses clickable cards rather than
            # anchors for filing announcements. Follow only financial-result cards,
            # then collect their official PDF attachments. This keeps the generic
            # issuer-page path unchanged while making the exchange source useful.
            if host == _SAUDI_EXCHANGE_HOST:
                cards = page.eval_on_selector_all(
                    "[onclick*='document.location.href']",
                    "els => els.map(e => ({onclick:e.getAttribute('onclick')||'', "
                    "text:(e.textContent||'').trim()}))",
                )
                announcements = _saudi_financial_announcement_links(
                    index_url, cards, keywords
                )[:12]
                detail = context.new_page()
                for announcement in announcements:
                    try:
                        detail.goto(announcement["url"], timeout=self.timeout_ms,
                                    wait_until="domcontentloaded")
                        detail.wait_for_timeout(500)
                        attachments = detail.eval_on_selector_all(
                            "a[href]", "els => els.map(e => e.href)")
                    except Exception:
                        continue
                    for attachment in attachments:
                        parsed = urlparse(attachment)
                        if (parsed.scheme == "https" and
                                parsed.hostname == _SAUDI_EXCHANGE_HOST and
                                ".pdf" in parsed.path.lower()):
                            raw.append([attachment, announcement["title"]])
                            referers[attachment] = announcement["url"]
                # The Exchange profile is also the authoritative bridge to the
                # issuer's own website. Crawl a bounded set of investor/report
                # pages there to find full annual and interim statements, which
                # are often not attached to Exchange announcements.
                for issuer_site in _official_issuer_websites(index_url, raw)[:1]:
                    issuer_host = urlparse(issuer_site).hostname or ""
                    allowed_hosts.add(issuer_host)
                    issuer_page = context.new_page()
                    try:
                        issuer_page.goto(issuer_site, timeout=self.timeout_ms,
                                         wait_until="domcontentloaded")
                        issuer_page.wait_for_timeout(2000)
                        issuer_links = issuer_page.eval_on_selector_all(
                            "a[href]", "els => els.map(e => [e.href, "
                            "(e.textContent||'').trim()])")
                    except Exception:
                        continue
                    report_pages = []
                    for href, label in issuer_links:
                        parsed = urlparse(href)
                        if (parsed.scheme != "https" or parsed.hostname is None or
                                not (parsed.hostname == issuer_host or
                                     parsed.hostname.endswith("." + issuer_host))):
                            continue
                        lowered = f"{label} {parsed.path}".lower()
                        if any(ext in parsed.path.lower() for ext in (".pdf", ".xlsx")):
                            raw.append([href, label])
                            referers[href] = issuer_page.url
                        elif any(term in lowered for term in (
                                "annual report", "quarterly report",
                                "quarterly financial", "financial statement",
                                "performance-financial", "/investors",
                                "investor-relations", "علاقات المستثمرين",
                                "التقارير السنوية", "القوائم المالية",
                                "النتائج المالية",
                        )):
                            report_pages.append((href, label))
                    crawled = set()
                    for report_url, _ in report_pages:
                        if report_url in crawled or len(crawled) >= 5:
                            continue
                        crawled.add(report_url)
                        try:
                            issuer_page.goto(report_url, timeout=self.timeout_ms,
                                             wait_until="domcontentloaded")
                            issuer_page.wait_for_timeout(1500)
                            documents = issuer_page.eval_on_selector_all(
                                "a[href]", "els => els.map(e => { "
                                "const label=(e.textContent||'').trim(); let node=e.parentElement; "
                                "let heading=''; for(let i=0;i<4 && node;i++,node=node.parentElement){ "
                                "const own=[...node.children].find(c => /^H[1-6]$/.test(c.tagName)); "
                                "if(own){ heading=(own.textContent||'').trim(); break; } } "
                                "return [e.href,(heading+' '+label).trim()]; })")
                        except Exception:
                            continue
                        for document_url, document_title in documents:
                            parsed = urlparse(document_url)
                            if (parsed.scheme == "https" and parsed.hostname and
                                    any(ext in parsed.path.lower() for ext in (".pdf", ".xlsx"))):
                                raw.append([document_url, document_title])
                                referers[document_url] = report_url
                                trusted_documents.add(document_url)
        seen, out = set(), []
        for href, text in raw:
            full = urljoin(index_url, href)
            parsed = urlparse(full)
            if (parsed.scheme != "https" or
                    not any(ext in parsed.path.lower() for ext in (".pdf", ".xlsx"))):
                continue
            same_site = any(
                parsed.hostname == allowed or
                (parsed.hostname or "").endswith("." + allowed)
                for allowed in allowed_hosts
            )
            label = (text or _slug(full)).lower()
            if full in seen or (not same_site and full not in trusted_documents):
                continue
            if not any(k in label or k in parsed.path.lower() for k in keywords):
                continue
            seen.add(full)
            content_type = (_XLSX_CONTENT_TYPE if ".xlsx" in parsed.path.lower()
                            else "application/pdf")
            item = {"url": full, "title": text.strip() or _slug(full),
                    "content_type": content_type}
            if full in referers:
                item["referer"] = referers[full]
            out.append(item)
        return out

    def download_bytes(self, url: str, referer: str | None = None,
                       content_type: str = "application/pdf") -> bytes:
        """Fetch one URL's raw bytes through a real browser context - the piece
        `DocumentArchiver` plugs in as its `content_fetcher` for sites a plain
        HTTP client can't pass. Validates the expected filing signature."""
        import contextlib
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("document URL must be HTTPS")
        with contextlib.ExitStack() as stack:
            context = self._context(stack)
            # a real navigation first sets cookies some CDNs require for the asset
            page = context.new_page()
            with contextlib.suppress(Exception):
                page.goto(referer or f"https://{urlparse(url).hostname}/",
                          timeout=self.timeout_ms,
                          wait_until="domcontentloaded")
                page.wait_for_load_state("load", timeout=8000)
                page.wait_for_timeout(1500)
            if referer:
                # Execute same-origin fetch in the rendered announcement page.
                # Saudi Exchange rejects API-context requests even with a Referer,
                # but accepts the browser document's cookies and fetch metadata.
                response = None
                page_error = None
                for attempt in range(3):
                    try:
                        with page.expect_response(lambda item: item.url == url,
                                                  timeout=self.timeout_ms) as response_info:
                            status = page.evaluate(
                                "async url => { const response = await fetch(url); "
                                "await response.arrayBuffer(); return response.status; }", url,
                            )
                        response = response_info.value
                        break
                    except Exception as error:
                        page_error = error
                        if (attempt == 2 or
                                "execution context was destroyed" not in str(error).lower()):
                            break
                        page.wait_for_timeout(1000)
                if response is not None and 200 <= status < 300:
                    content = response.body()
                else:
                    try:
                        content = _request_document_bytes(
                            context, url, referer, self.timeout_ms
                        )
                    except Exception as request_error:
                        try:
                            # A few issuer CDNs reject browser-shaped requests
                            # while allowing a conventional document client. This
                            # final bounded path is still limited to the exact URL
                            # selected from the official monitored page.
                            content = _direct_document_bytes(
                                url, referer, self.timeout_ms / 1000
                            )
                        except Exception as direct_error:
                            detail = (f"; browser page fetch: {page_error}"
                                      if page_error is not None else "")
                            raise RuntimeError(
                                f"all document download paths failed for {url}{detail}; "
                                f"request context: {request_error}; direct: {direct_error}"
                            ) from direct_error
            else:
                content = _request_document_bytes(
                    context, url, timeout_ms=self.timeout_ms
                )
        _validate_document_bytes(content, url, content_type)
        return content

    def download_candidate(self, candidate: dict) -> bytes:
        """Download with discovery provenance needed by referer-protected CDNs."""
        return self.download_bytes(
            candidate["source_url"], (candidate.get("metadata") or {}).get("referer"),
            candidate.get("content_type") or "application/pdf",
        )

    def fetch(self, url: str, market: str, symbol: str) -> dict:
        """Download one PDF through the browser context and archive it immutably."""
        content = self.download_bytes(url)
        digest = hashlib.sha256(content).hexdigest()
        target = self.raw_dir / market.upper() / symbol.upper() / "documents" / f"{digest}.pdf"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = target.with_suffix(".pdf.part")
            temporary.write_bytes(content)
            temporary.replace(target)
        return {
            "status": "archived", "url": url, "sha256": digest,
            "bytes": len(content), "local_path": str(target),
            "fetched_at": date.today().isoformat(), "next_stage": "read",
        }


class BrowserIssuerMonitor:
    """Durable discovery for issuer pages a plain HTTP client can't render or
    pass bot protection on. Same idempotency contract as
    `connectors.issuer.IssuerReportsMonitor` (cursor = hash of the candidate
    set) so it plugs into `MonitorService.poll` / the job queue / scheduler
    unchanged - the only difference is *how* the page is rendered."""

    name = "browser-issuer-reports"

    def __init__(self, index_url: str, fetcher: "BrowserFetcher | None" = None,
                 max_documents: int = 20):
        parsed = urlparse(index_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("issuer report index must be an HTTPS URL")
        self.index_url = index_url
        self.fetcher = fetcher or BrowserFetcher()
        self.max_documents = max(1, min(max_documents, 200))

    def discover(self, company, cursor: str | None = None):
        from .models import DiscoveryResult, SourceCandidate

        found = self.fetcher.discover(self.index_url)[: self.max_documents]
        digest = hashlib.sha256(
            "\n".join(sorted(item["url"] for item in found)).encode("utf-8")).hexdigest()
        if cursor == digest:
            return DiscoveryResult(digest, ())
        candidates = tuple(
            SourceCandidate(
                company.company_id, self.name,
                hashlib.sha256(item["url"].encode("utf-8")).hexdigest(),
                item["url"], item["title"],
                self._document_type(f"{item['title']} {item['url']}"),
                _published_at_from_url(item["url"]),
                item.get("content_type", "application/pdf"),
                {"index_url": self.index_url, **(
                    {"referer": item["referer"]} if item.get("referer") else {}
                )},
            )
            for item in found
        )
        return DiscoveryResult(digest, candidates)

    @staticmethod
    def _document_type(title: str) -> str:
        lowered = title.lower()
        if ".xlsx" in lowered or "data supplement" in lowered or "databook" in lowered:
            return "data-supplement"
        if ("interim" in lowered or "quarter" in lowered or "half year" in lowered or
                "مرحلية" in lowered or "ربع سنوي" in lowered or
                re.search(r"(?:^|[^a-z0-9])(?:[1-4]q|q[1-4])(?:[^a-z0-9]|$)", lowered)):
            return "interim-report"
        if ("annual" in lowered or "year ending" in lowered or "year ended" in lowered or
                "التقرير السنوي" in lowered):
            return "annual-report"
        if "financial" in lowered:
            return "financial-report"
        return "issuer-report"
