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
from urllib.parse import unquote, urljoin, urlparse

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
_KEYWORDS = ("financial statement", "financial results", "interim", "annual report",
             "consolidated", "quarterly", "q1", "q2", "q3", "q4", "fy", "half year")


def _slug(url: str) -> str:
    name = Path(unquote(urlparse(url).path)).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "document.pdf"


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
        """Render an investor-relations page and return candidate PDF links."""
        import contextlib
        host = urlparse(index_url).hostname or ""
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
                "a[href]", "els => els.map(e => [e.href, (e.textContent||'').trim()])")
        seen, out = set(), []
        for href, text in raw:
            full = urljoin(index_url, href)
            parsed = urlparse(full)
            if parsed.scheme != "https" or ".pdf" not in parsed.path.lower():
                continue
            same_site = parsed.hostname == host or (parsed.hostname or "").endswith("." + host)
            label = (text or _slug(full)).lower()
            if full in seen or not same_site:
                continue
            if not any(k in label or k in parsed.path.lower() for k in keywords):
                continue
            seen.add(full)
            out.append({"url": full, "title": text.strip() or _slug(full)})
        return out

    def fetch(self, url: str, market: str, symbol: str) -> dict:
        """Download one PDF through the browser context and archive it immutably."""
        import contextlib
        with contextlib.ExitStack() as stack:
            context = self._context(stack)
            # a real navigation first sets cookies some CDNs require for the asset
            page = context.new_page()
            with contextlib.suppress(Exception):
                page.goto(f"https://{urlparse(url).hostname}/", timeout=self.timeout_ms,
                          wait_until="domcontentloaded")
            response = context.request.get(url, timeout=self.timeout_ms)
            if not response.ok:
                raise RuntimeError(f"fetch failed: HTTP {response.status} for {url}")
            content = response.body()
        if not content.startswith(b"%PDF"):
            raise RuntimeError(f"downloaded content is not a PDF: {url}")
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
