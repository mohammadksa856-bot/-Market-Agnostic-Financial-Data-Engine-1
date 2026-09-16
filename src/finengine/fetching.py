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
             # Basel III Pillar 3 disclosures carry the regulatory capital,
             # leverage and liquidity metrics no financial statement prints.
             "pillar 3", "basel iii", "regulatory disclosure",
             "القوائم المالية",
             "النتائج المالية", "التقرير السنوي", "تقارير سنوية", "ربع سنوي",
             "مرحلية", "الركيزة الثالثة")
_SAUDI_EXCHANGE_HOST = "www.saudiexchange.sa"
_XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PDF_LABEL = re.compile(
    r"(?:\bpdf\b|download\s+(?:the\s+)?(?:full\s+)?report|view\s+pdf|"
    r"تحميل\s+(?:التقرير|ملف)|عرض\s+(?:ملف\s+)?pdf)", re.I
)
_XLSX_LABEL = re.compile(r"(?:\bxlsx\b|\bexcel\b|data\s+supplement)", re.I)
_ONCLICK_LOCATION = re.compile(
    r"document\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", re.I
)
_REPORT_PAGE_TERMS = (
    "annual report", "quarterly report", "quarterly financial",
    "financial statement", "financial result", "reports-and-presentations",
    "performance-financial", "investor-relations", "/investors", "/reports",
    "علاقات المستثمرين", "التقارير السنوية", "القوائم المالية", "النتائج المالية",
)


class SourceAccessBlocked(RuntimeError):
    """The official document exists but its host denies this worker access.

    This is a source-access exception, not a pipeline crash.  Keeping it as a
    distinct type lets the durable worker finish the job truthfully while the
    candidate remains queued for an alternate-network fetcher or manual review.
    """


def _slug(url: str) -> str:
    name = Path(unquote(urlparse(url).path)).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "document.pdf"


def _document_content_type(url: str, label: str = "") -> str | None:
    """Classify explicit filing downloads, including query-driven IR links.

    Several Saudi bank sites expose a PDF through a download route whose URL
    has no filename extension.  We accept those only when the official page's
    link text explicitly says PDF/download; downloaded bytes are still checked
    by :func:`_validate_document_bytes` before they enter the archive.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    target = unquote(f"{parsed.path}?{parsed.query}").lower()
    normalized_label = " ".join(str(label or "").split())
    # An explicit extension in the URL wins over the link text: Al Rajhi
    # publishes several quarters of its "Data Supplement" as a PDF, and
    # classifying those as XLSX rejects the download as a corrupt workbook.
    if ".xlsx" in target:
        return _XLSX_CONTENT_TYPE
    if ".pdf" in target:
        return "application/pdf"
    if _XLSX_LABEL.search(normalized_label):
        return _XLSX_CONTENT_TYPE
    historical_download = (
        re.search(r"annual[-_ ]reports?", target)
        and re.search(r"\bdownload\s+file\b", normalized_label, re.I)
    )
    if ".pdf" in target or _PDF_LABEL.search(normalized_label) or historical_download:
        return "application/pdf"
    return None


def _goto_with_partial_dom(page, url: str, timeout_ms: int) -> None:
    """Keep a usable same-site DOM when a heavy IR page times out late.

    Riyad Bank's report library can populate hundreds of filing anchors before
    analytics and secondary assets finish.  Playwright raises on the navigation
    timeout even though the authoritative links are already present.  A partial
    page is accepted only when it has anchors and remains on the requested host.
    """
    try:
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
    except Exception:
        requested = (urlparse(url).hostname or "").lower().removeprefix("www.")
        landed = (urlparse(getattr(page, "url", "")).hostname or "").lower().removeprefix("www.")
        try:
            anchors = page.locator("a[href]").count()
        except Exception:
            anchors = 0
        if not anchors or requested != landed:
            raise


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


def _is_report_page(url: str, label: str, parent_url: str = "") -> bool:
    """Conservatively identify an official page likely to contain filings."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    lowered = f"{label} {unquote(parsed.path)} {parsed.query}".lower()
    if any(extension in parsed.path.lower() for extension in (".pdf", ".xlsx")):
        return False
    if any(term in lowered for term in _REPORT_PAGE_TERMS):
        return True
    parent = unquote(urlparse(parent_url).path).lower()
    return bool(
        any(term.strip("/") in parent for term in _REPORT_PAGE_TERMS)
        and re.search(r"(?:^|[/=_-])20(?:0\d|1\d|2\d)(?:$|[/=&_-])", lowered)
    )


def _is_dedicated_filing_index(url: str) -> bool:
    """True when the configured page itself is the issuer's filing library."""
    path = unquote(urlparse(url).path).lower().replace("_", "-")
    return any(term in path for term in (
        "annual-report", "previous-annual-report", "financial-result",
        "financial-statement", "financial-reports-chart",
    ))


def _matches_filing_keywords(url: str, label: str,
                             keywords: tuple[str, ...] = _KEYWORDS) -> bool:
    parsed = urlparse(url)
    searchable = re.sub(
        r"[-_/]+", " ",
        unquote(f"{label} {parsed.path} {parsed.query}").lower(),
    )
    if any(keyword in searchable for keyword in keywords):
        return True
    # Some official filing libraries label interim statements only as ``Q1``
    # or ``First Quarter`` while the PDF filename is abbreviated to ``FS``.
    # Those are authoritative filing links, not navigation pages (the caller
    # has already required a document content type), so keep the quarter token
    # as a valid discovery signal.
    return bool(
        re.search(r"(?:^|[^a-z0-9])(?:q[1-4]|[1-4]q)(?:[^a-z0-9]|$)", searchable)
        or re.search(r"\b(?:first|second|third|fourth)\s+quarter\b", searchable)
        or re.search(r"الربع\s+(?:الأول|الاول|الثاني|الثالث|الرابع)", searchable)
    )


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

    def discover(self, index_url: str, keywords: tuple[str, ...] = _KEYWORDS,
                 max_documents: int = 20) -> list[dict]:
        """Render an investor-relations page and return candidate filing links."""
        max_documents = max(1, min(int(max_documents), 200))
        import contextlib
        host = urlparse(index_url).hostname or ""
        allowed_hosts = {host}
        trusted_documents: set[str] = set()
        referers: dict[str, str] = {}
        with contextlib.ExitStack() as stack:
            context = self._context(stack)
            page = context.new_page()
            _goto_with_partial_dom(page, index_url, self.timeout_ms)
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
            for linked_url, linked_label in raw:
                linked = urlparse(linked_url)
                if (linked.scheme == "https" and linked.hostname and
                        _document_content_type(linked_url, linked_label)):
                    trusted_documents.add(linked_url)
                    referers[linked_url] = page.url
            # A dedicated filing library already exposes the authoritative
            # downloads in its first DOM. Avoid crawling dozens of navigation
            # links after those documents are found; generic IR landing pages
            # still receive the bounded recursive crawl.
            if (host != _SAUDI_EXCHANGE_HOST and
                    not (trusted_documents and
                         _is_dedicated_filing_index(index_url))):
                self._crawl_report_pages(
                    page, host, list(raw), raw, referers, trusted_documents,
                    max_pages=min(max_documents, 50),
                )
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
                )[:max_documents]
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
                    self._crawl_report_pages(
                        issuer_page, issuer_host, issuer_links, raw, referers,
                        trusted_documents, max_pages=min(max_documents, 50),
                    )
        seen, out = set(), []
        for href, text in raw:
            full = urljoin(index_url, href)
            parsed = urlparse(full)
            content_type = _document_content_type(full, text)
            if parsed.scheme != "https" or not content_type:
                continue
            same_site = any(
                parsed.hostname == allowed or
                (parsed.hostname or "").endswith("." + allowed)
                for allowed in allowed_hosts
            )
            label = (text or _slug(full)).lower()
            if full in seen or (not same_site and full not in trusted_documents):
                continue
            if not _matches_filing_keywords(full, label, keywords):
                continue
            seen.add(full)
            item = {"url": full, "title": text.strip() or _slug(full),
                    "content_type": content_type}
            if full in referers:
                item["referer"] = referers[full]
            out.append(item)
        return out

    def _crawl_report_pages(self, page, issuer_host: str,
                            initial_links: list[list[str]], raw: list[list[str]],
                            referers: dict[str, str], trusted_documents: set[str],
                            max_pages: int) -> None:
        """Follow the bounded official IR tree, including year sub-pages."""
        queue: list[tuple[str, str, int, str]] = []
        queued: set[str] = set()

        def inspect_links(links, parent_url: str, depth: int) -> None:
            for href, label in links:
                parsed = urlparse(href)
                same_host = bool(
                    parsed.scheme == "https" and parsed.hostname and
                    (parsed.hostname == issuer_host or
                     parsed.hostname.endswith("." + issuer_host))
                )
                if not same_host:
                    continue
                if _document_content_type(href, label):
                    raw.append([href, label])
                    referers[href] = parent_url
                    trusted_documents.add(href)
                elif depth <= 2 and href not in queued and _is_report_page(
                        href, label, parent_url):
                    queued.add(href)
                    queue.append((href, label, depth, parent_url))

        inspect_links(initial_links, page.url, 0)
        crawled: set[str] = set()
        while queue and len(crawled) < max_pages:
            report_url, _, depth, _ = queue.pop(0)
            if report_url in crawled:
                continue
            crawled.add(report_url)
            try:
                _goto_with_partial_dom(page, report_url, self.timeout_ms)
                page.wait_for_timeout(1500)
                links = page.eval_on_selector_all(
                    "a[href]", "els => els.map(e => { "
                    "const label=(e.textContent||'').trim(); let node=e.parentElement; "
                    "let heading=''; for(let i=0;i<4 && node;i++,node=node.parentElement){ "
                    "const own=[...node.children].find(c => /^H[1-6]$/.test(c.tagName)); "
                    "if(own){ heading=(own.textContent||'').trim(); break; } } "
                    "return [e.href,(heading+' '+label).trim()]; })")
            except Exception:
                continue
            inspect_links(links, report_url, depth + 1)

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
                content = None
                if response is not None and 200 <= status < 300:
                    try:
                        content = response.body()
                    except Exception as error:
                        # Chromium may evict a large response body after the page
                        # has consumed it. Continue through the two bounded,
                        # provenance-preserving download paths below.
                        page_error = error
                if content is None:
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
                                url, referer, max(self.timeout_ms / 1000, 300)
                            )
                        except Exception as direct_error:
                            detail = (f"; browser page fetch: {page_error}"
                                      if page_error is not None else "")
                            error_type = (
                                SourceAccessBlocked
                                if "403" in str(request_error) and "403" in str(direct_error)
                                else RuntimeError
                            )
                            raise error_type(
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

        try:
            found = self.fetcher.discover(
                self.index_url, max_documents=self.max_documents
            )[: self.max_documents]
        except TypeError as error:
            # Preserve compatibility with small injected test/custom fetchers
            # that implement the original one-argument discovery contract.
            if "max_documents" not in str(error):
                raise
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
                {"index_url": self.index_url,
                 "source_role": "official_filing",
                 "authority_tier": (
                     "exchange_official" if (
                         urlparse(self.index_url).hostname == _SAUDI_EXCHANGE_HOST or
                         urlparse(item.get("referer") or "").hostname == _SAUDI_EXCHANGE_HOST
                     ) else "issuer_official"
                 ),
                 "numeric_authority": True,
                 **(
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
        # Checked before the quarter tokens: "Pillar 3 Disclosures Q2 2026" is a
        # regulatory capital disclosure, not interim financial statements.
        if (re.search(r"pillar[\s_%20-]*3|basel[\s_%20-]*iii", lowered) or
                "regulatory disclosure" in lowered or "الركيزة الثالثة" in lowered):
            return "regulatory-disclosure"
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
