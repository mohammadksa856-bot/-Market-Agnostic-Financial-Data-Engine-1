"""RAW-ONLY collector of historical Saudi financial statements (odd shard).

Collects PDF/XLSX financial statements from (1) Saudi Exchange announcements,
(2)/(3) the issuer's own investor-relations pages and report archives, stores
them content-addressed under ``<root>/archive/SA/<symbol>/<sha256>.<ext>`` and
records a coverage ledger.  It never extracts numbers, never enqueues, never
touches a database and never uploads unless ``--upload`` is given with a key.

Sub-commands: run | launch | merge | status
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from finengine import sa_raw_statements as raw  # noqa: E402

DEFAULT_ROOT = Path(r"C:\Users\Mohammed856\finengine-raw-odd")
REGISTRY = PROJECT / "config" / "sa-market-registry.json"
BATCH_DIR = PROJECT / "config" / "source-registry"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
SE = "https://www.saudiexchange.sa"
SE_ANN_PAGE = SE + "/wps/portal/saudiexchange/newsandreports/issuer-news/issuer-announcements?page=1"
SE_PROFILE = ("https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/"
              "company-profile-main/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8ziTR3NDIw8LAz83d2M"
              "XA0C3SydAl1c3Q0NvE30I4EKzBEKDMKcTQzMDPxN3H19LAzdTU31w8syU8v1wwkpK8hOMgUA-oskdg!!/"
              "?companySymbol={symbol}")
NAV_KEYWORDS = re.compile(
    r"invest|financ|report|statement|annual|quarter|interim|result|disclos|"
    r"publication|download|archive|library|document|\bir\b|shareholder|"
    r"مستثمر|مالي|تقرير|قوائم|نتائج|إفصاح|افصاح|أرشيف|ارشيف|بيانات|سنوي|ربع|مرحل|المساهم",
    re.I)
LOAD_MORE = re.compile(
    r"load more|show more|view more|see more|more results|older|previous years|"
    r"المزيد|عرض المزيد|تحميل المزيد|السابق", re.I)
NEXT = re.compile(r"^\s*(next|›|»|>|التالي)\s*$", re.I)
FIN_RESULT_TITLE = re.compile(
    r"financial results|financial statements|النتائج المالية|القوائم المالية", re.I)
RULES_VERSION = 2
NOW = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")  # noqa: E731


# ---------------------------------------------------------------------------
# small io helpers


def jload(path: Path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def jsave(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def jlog(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": NOW(), **event}, ensure_ascii=False) + "\n")


def classify_error(exc: Exception) -> str:
    m = str(exc).lower()
    if "timeout" in m or "timed out" in m:
        return "timeout"
    if "ssl" in m or "cert" in m or "err_cert" in m or "tls" in m:
        return "tls_error"
    if "403" in m or "access denied" in m or "blocked" in m or "err_http2" in m:
        return "blocked"
    if "name_not_resolved" in m or "dns" in m or "connection_refused" in m:
        return "unreachable"
    return "error"


def first_page_text(path: Path, kind: str, pages: int = 2) -> str:
    """Text of the first pages, for CLASSIFICATION ONLY (no number extraction)."""
    if kind != "pdf":
        return ""
    try:
        import pymupdf
        with pymupdf.open(str(path)) as doc:
            return "\n".join(doc[i].get_text() for i in range(min(pages, len(doc))))
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# sources per company


def load_sources() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in sorted(BATCH_DIR.glob("*.json")):
        rows = jload(f, [])
        if isinstance(rows, dict):
            rows = next((v for v in rows.values() if isinstance(v, list)), [])
        for r in rows:
            if isinstance(r, dict) and r.get("symbol"):
                out[str(r["symbol"])] = r
    return out


def seeds_for(company: dict, batch: dict | None, profile_site: str | None) -> list[dict]:
    seeds: list[dict] = []

    def add(url, origin):
        if url and isinstance(url, str) and url.startswith("http") and \
                url not in {s["url"] for s in seeds}:
            seeds.append({"url": url, "origin": origin})

    for u in company.get("sources") or []:
        add(u, "registry")
    if batch:
        for k in ("financial_statements_url", "quarterly_results_url",
                  "annual_reports_url", "investor_relations_url", "disclosures_url",
                  "data_supplements_url", "official_website"):
            add(batch.get(k), "batch:" + k)
    add(profile_site, "saudi_exchange_profile_website")
    return seeds


# ---------------------------------------------------------------------------
# Saudi Exchange


class SaudiExchange:
    def __init__(self, context, log):
        self.context = context
        self.page = context.new_page()
        self.detail = context.new_page()
        self.log = log
        self.url = None
        self.body = None
        self.last = 0.0

    def _throttle(self, seconds=1.2):
        wait = self.last + seconds - time.time()
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()

    def _prime(self):
        cap: list = []
        self.page.on("request", lambda r: cap.append((r.url, r.post_data))
                     if "getAnnouncementListData" in r.url else None)
        last = None
        for attempt in range(4):
            try:
                self.page.goto(SE_ANN_PAGE, wait_until="domcontentloaded",
                               timeout=60000)
            except Exception as exc:  # partial load is fine if the call fired
                last = exc
            for _ in range(25):
                if cap:
                    break
                self.page.wait_for_timeout(1000)
            if cap:
                self.url, self.body = cap[0]
                return
            time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"saudi exchange announcement api not reachable: {last}")

    def announcements(self, symbol: str) -> list[dict]:
        if not self.url:
            self._prime()
        out, page_no, total = [], 1, None
        while True:
            data = dict(parse_qsl(self.body, keep_blank_values=True))
            data.update(symbol=symbol, pageNumberDb=str(page_no), pageSize="500")
            text = None
            for attempt in range(3):
                self._throttle()
                try:
                    status, text = self.page.evaluate(
                        """async([u,b])=>{const r=await fetch(u,{method:'POST',headers:{
                        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-Requested-With':'XMLHttpRequest'},body:b});
                        return [r.status,await r.text()]}""",
                        [self.url, urlencode(data)])
                    if status == 200:
                        break
                except Exception as exc:
                    text = None
                    self.log({"event": "se_api_error", "symbol": symbol,
                              "error": str(exc)[:200]})
                time.sleep(3 * (attempt + 1))
                self._prime()
            if not text:
                raise RuntimeError("saudi exchange announcement api failed")
            payload = json.loads(text)
            rows = payload.get("announcementList") or []
            total = payload.get("totalCount", len(rows))
            out.extend(rows)
            if not rows or len(out) >= int(total or 0):
                break
            page_no += 1
        return out

    def detail_files(self, symbol: str, ann: dict) -> list[str]:
        url = SE + ann["announcementUrl"]
        last = None
        for attempt in range(3):
            self._throttle(1.5)
            try:
                with contextlib.suppress(Exception):
                    self.detail.goto(url, wait_until="domcontentloaded", timeout=45000)
                self.detail.wait_for_timeout(2200)
                hrefs = self.detail.eval_on_selector_all(
                    "a[href]", "e=>e.map(a=>a.href)")
                html = self.detail.content()
                if len(html) < 3000:
                    raise RuntimeError("detail page did not render")
                files = [h for h in hrefs if re.search(
                    r"\.(pdf|xlsx?)(\?|$)|/Resources/fsPdf/", h, re.I)]
                files += re.findall(r"https?://[^\"'\s<>]*fsPdf[^\"'\s<>]*", html)
                return sorted(set(files))
            except Exception as exc:
                last = exc
                time.sleep(3 * (attempt + 1))
        raise RuntimeError(f"detail page failed: {last}")

    def profile_website(self, symbol: str) -> str | None:
        url = SE_PROFILE.format(symbol=symbol)
        for attempt in range(3):
            self._throttle(1.5)
            try:
                with contextlib.suppress(Exception):
                    self.detail.goto(url, wait_until="domcontentloaded", timeout=45000)
                self.detail.wait_for_timeout(3000)
                text = self.detail.inner_text("body")
                m = re.search(r"Website\s*[:\n]\s*([^\s]+)", text)
                site = raw.normalize_website(m.group(1)) if m else None
                if not site:
                    hrefs = self.detail.eval_on_selector_all(
                        "a[href]", "e=>e.map(a=>[a.href,(a.innerText||'').trim()])")
                    from finengine.fetching import _official_issuer_websites
                    found = _official_issuer_websites(url, hrefs)
                    site = found[0] if found else None
                if m or site or len(text) > 3000:
                    return site
            except Exception:
                pass
            time.sleep(3)
        return None


# ---------------------------------------------------------------------------
# issuer site crawl


def _registrable(host: str) -> str:
    parts = (host or "").lower().removeprefix("www.").split(".")
    return ".".join(parts[-3:] if parts[-2:-1] in (["com"], ["co"], ["org"], ["gov"], ["edu"]) and len(parts) >= 3 else parts[-2:])


def _is_doc_link(href: str, text: str) -> bool:
    p = urlparse(href)
    target = (p.path + "?" + p.query).lower()
    if re.search(r"\.(pdf|xlsx|xls)(\b|$)", target):
        return True
    return bool(re.search(r"\b(pdf|xlsx?|download)\b|تحميل|تنزيل", text or "", re.I)) and \
        bool(re.search(r"download|file|document|media|attachment|getfile|asset|content", target))


LINK_JS = """()=>{
 const out=[];
 const doc=(d)=>{ d.querySelectorAll('a[href]').forEach(a=>{
   let c=a.closest('li,tr,article,.card,.row,.item,.list-group-item,p,div');
   let t=(c?c.innerText:'')||'';
   out.push([a.href,(a.innerText||a.title||a.getAttribute('aria-label')||'').trim().slice(0,200),
             t.replace(/\\s+/g,' ').trim().slice(0,300)]);});};
 doc(document); return out;}"""


class IssuerCrawler:
    def __init__(self, context, log, max_pages=70, max_depth=3, delay=1.5):
        self.context = context
        self.page = context.new_page()
        self.log = log
        self.max_pages, self.max_depth, self.delay = max_pages, max_depth, delay
        self.last_host_time: dict[str, float] = {}

    def _polite(self, url):
        host = urlparse(url).hostname or ""
        wait = self.last_host_time.get(host, 0) + self.delay - time.time()
        if wait > 0:
            time.sleep(wait)
        self.last_host_time[host] = time.time()

    def _links(self) -> list[list[str]]:
        rows = []
        for frame in self.page.frames:
            try:
                rows += frame.evaluate(LINK_JS)
            except Exception:
                pass
        return rows

    CLICK_JS = r"""(re)=>{
      const rx=new RegExp(re,'i');
      const els=[...document.querySelectorAll('button,a,[role=button],li.next,.pagination *')];
      for(const e of els){
        if(e.dataset.rawClicked) continue;
        const t=(e.innerText||e.value||e.getAttribute('aria-label')||'').trim();
        if(!t||t.length>40||!rx.test(t)) continue;
        const r=e.getBoundingClientRect();
        if(!(r.width||r.height)||e.disabled||e.getAttribute('aria-disabled')==='true') continue;
        const h=e.getAttribute('href')||'';
        if(h && !h.startsWith('#') && !h.startsWith('javascript') && e.tagName==='A' && !/page|offset|start/i.test(h)) continue;
        e.dataset.rawClicked='1'; e.click(); return t;
      }
      return null;}"""
    TOGGLE_JS = r"""async()=>{
      let n=0;
      const els=[...document.querySelectorAll('[role=tab],.nav-tabs a,.accordion-button,summary,[aria-expanded=false],[data-toggle=tab],[data-bs-toggle=tab],[data-toggle=collapse],[data-bs-toggle=collapse]')].slice(0,80);
      for(const e of els){
        if(e.dataset.rawClicked) continue;
        const h=e.getAttribute('href')||'';
        if(h && !h.startsWith('#') && !h.startsWith('javascript')) continue;
        try{e.dataset.rawClicked='1'; e.click(); n++; await new Promise(r=>setTimeout(r,120));}catch(x){}
      }
      for(const sel of [...document.querySelectorAll('select')].slice(0,6)){
        const opts=[...sel.options].filter(o=>/(19|20)\d{2}/.test(o.text)).slice(0,40);
        if(opts.length<2) continue;
        for(const o of opts){ sel.value=o.value; sel.dispatchEvent(new Event('change',{bubbles:true}));
          n++; await new Promise(r=>setTimeout(r,250)); window.__rawHarvest&&window.__rawHarvest(); }
      }
      return n;}"""

    def _expand(self, seen_links: dict):
        """Click Load-more / Next / tabs / accordions / year selects until exhausted."""
        def harvest():
            for href, text, ctx in self._links():
                seen_links.setdefault(href, (text, ctx))
        harvest()
        for _ in range(80):
            before = len(seen_links)
            try:
                clicked = self.page.evaluate(self.CLICK_JS, LOAD_MORE.pattern + "|^(next|›|»|التالي)$")
            except Exception:
                break
            if not clicked:
                break
            self.page.wait_for_timeout(900)
            harvest()
            if len(seen_links) == before and _ > 8:
                break
        try:
            self.page.evaluate(self.TOGGLE_JS)
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        harvest()

    def crawl(self, seeds: list[dict]) -> dict:
        """Return {"docs": {url: (text, ctx, page_url)}, "status": ..., "pages": n}."""
        docs: dict[str, tuple] = {}
        queue = [(s["url"], 0) for s in seeds]
        seen_pages: set[str] = set()
        allowed = {_registrable(urlparse(s["url"]).hostname or "") for s in seeds}
        pages, statuses = 0, []
        while queue and pages < self.max_pages:
            url, depth = queue.pop(0)
            key = url.split("#")[0].rstrip("/")
            if key in seen_pages:
                continue
            seen_pages.add(key)
            self._polite(url)
            ok = False
            for attempt in range(2):
                try:
                    try:
                        self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    except Exception as exc:
                        if not self.page.locator("a[href]").count():
                            raise exc
                    with contextlib.suppress(Exception):
                        self.page.wait_for_load_state("networkidle", timeout=6000)
                    self.page.wait_for_timeout(1500)
                    ok = True
                    break
                except Exception as exc:
                    last = classify_error(exc)
                    time.sleep(2 * (attempt + 1))
            pages += 1
            if not ok:
                statuses.append(last)
                self.log({"event": "crawl_fail", "url": url, "reason": last})
                continue
            links: dict[str, tuple] = {}
            try:
                self._expand(links)
            except Exception as exc:
                self.log({"event": "expand_error", "url": url, "error": str(exc)[:150]})
            if not links:
                statuses.append("js_no_content")
            for href, (text, ctx) in links.items():
                if not href.startswith("http"):
                    continue
                if _is_doc_link(href, text):
                    docs.setdefault(href, (text, ctx, url))
                    continue
                host = _registrable(urlparse(href).hostname or "")
                if depth < self.max_depth and host in allowed and \
                        NAV_KEYWORDS.search(f"{text} {urlparse(href).path}") and \
                        href.split("#")[0].rstrip("/") not in seen_pages and \
                        not re.search(r"\.(jpg|png|gif|svg|zip|mp4|css|js)(\?|$)", href, re.I):
                    queue.append((href, depth + 1))
        status = "ok" if pages and (docs or "ok") else "unreachable"
        if statuses and len(statuses) >= pages and not docs:
            status = statuses[0]
        return {"docs": docs, "status": status, "pages": pages, "errors": statuses[:5]}


# ---------------------------------------------------------------------------
# downloading


class Downloader:
    def __init__(self, context, log, se_page=None):
        self.context = context
        self.log = log
        self.se_page = se_page
        self.last = 0.0

    def _se_get(self, url: str) -> bytes:
        """Saudi Exchange files 403 for out-of-page requests; fetch in-page."""
        import base64
        res = self.se_page.evaluate(
            """async(u)=>{const r=await fetch(u,{credentials:'include'});
            if(!r.ok) return {status:r.status};
            const b=new Uint8Array(await r.arrayBuffer()); let s='';
            for(let i=0;i<b.length;i+=32768) s+=String.fromCharCode.apply(null,b.subarray(i,i+32768));
            return {status:200,data:btoa(s)};}""", url)
        if res.get("status") != 200:
            raise RuntimeError(f"HTTP {res.get('status')}")
        return base64.b64decode(res["data"])

    def get(self, url: str, referer: str | None) -> bytes:
        wait = self.last + 1.0 - time.time()
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        err = None
        for attempt in range(2):
            try:
                if self.se_page is not None and "saudiexchange.sa" in url:
                    return self._se_get(url)
                opts = {"timeout": 60000}
                if referer:
                    opts["headers"] = {"Referer": referer}
                r = self.context.request.get(url, **opts)
                if r.ok:
                    return r.body()
                err = RuntimeError(f"HTTP {r.status}")
                if r.status in (403, 401, 404, 410):
                    break
            except Exception as exc:
                err = exc
            time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"{classify_error(err)}: {err}")


# ---------------------------------------------------------------------------
# company processing


def title_from_url(url: str) -> str:
    from urllib.parse import unquote
    name = Path(unquote(urlparse(url).path)).name
    return re.sub(r"[_\-+.]+", " ", re.sub(r"\.(pdf|xlsx?)$", "", name, flags=re.I))


class CompanyRun:
    def __init__(self, root: Path, company: dict, batch: dict | None, log):
        self.root, self.company, self.batch, self.log = root, company, batch, log
        self.symbol = str(company["symbol"])
        self.path = root / "state" / "companies" / f"{self.symbol}.json"
        self.state = jload(self.path, {})
        self.state.setdefault("symbol", self.symbol)
        self.state.setdefault("company_id", company.get("company_id", f"sa:{self.symbol}"))
        self.state.setdefault("seen_urls", {})
        self.state.setdefault("docs", [])
        self.state.setdefault("rejected", [])
        self.state.setdefault("unclassified", [])
        self.state.setdefault("failures", [])
        self.ledger = raw.Ledger(self.symbol)
        self.ledger.docs = self.state["docs"]
        self.new_files = 0

    def save(self):
        jsave(self.path, self.state)

    def fail(self, reason: str, detail: str = "", url: str = ""):
        rec = {"reason": reason, "detail": detail[:300], "url": url}
        if rec not in self.state["failures"]:
            self.state["failures"].append(rec)
        self.log({"event": "failure", "symbol": self.symbol, **rec})

    def _evidence(self, own: str, head: str) -> str:
        return " ".join(f"{own} || {head}".split())[:600]

    def handle_candidate(self, dl: Downloader, url: str, title: str, ctx: str,
                         index_url: str, source: str, fy_end_month: int):
        seen = self.state["seen_urls"]
        if url in seen:
            return
        own = f"{title} {title_from_url(url)}"
        bucket, sub = raw.classify_bucket(own)
        if bucket == "rejected" and sub == "not_financial":
            # weak title: allow a row-context statement hint to trigger download
            b2, s2 = raw.classify_bucket(f"{own} {ctx}")
            if b2 == "statement" and re.search(
                    r"financial statements?|القوائم المالية", ctx, re.I):
                bucket, sub = "statement", s2
        if bucket == "rejected":
            rec = {"url": url, "title": title[:150], "reason": sub,
                   "index_url": index_url}
            self.state["rejected"].append(rec)
            seen[url] = {"status": "rejected", "reason": sub}
            self.log({"event": "rejected", "symbol": self.symbol, **rec})
            return
        try:
            content = dl.get(url, index_url)
        except Exception as exc:
            reason = str(exc).split(":")[0]
            seen[url] = {"status": "failed", "reason": reason}
            self.fail(reason if reason in {"timeout", "tls_error", "blocked",
                                           "unreachable"} else "download_error",
                      str(exc), url)
            return
        kind = raw.detect_file_kind(content)
        if not kind:
            seen[url] = {"status": "invalid", "reason": "invalid_document"}
            self.fail("invalid_document",
                      f"{len(content)} bytes, not PDF/XLSX", url)
            return
        digest = raw.sha256_bytes(content)
        if any(d["content_hash"] == digest for d in self.state["docs"]):
            seen[url] = {"status": "duplicate", "sha256": digest}
            self.log({"event": "duplicate", "symbol": self.symbol, "url": url,
                      "sha256": digest})
            return
        tmp = self.root / "tmp" / f"{self.symbol}-{digest}.{kind}"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(content)
        text = first_page_text(tmp, kind)
        scanned = kind == "pdf" and len(text.strip()) < 40
        head = " ".join(text.split())[:1500]
        supporting = None
        if bucket == "statement" and head:
            b2, s2 = raw.classify_bucket(f"{own} {head[:400]}")
            if b2 == "rejected" and s2 in {"presentation", "board_report",
                                          "sustainability", "prospectus",
                                          "credit_rating", "transcript"}:
                tmp.unlink(missing_ok=True)
                rec = {"url": url, "title": title[:150], "reason": s2,
                       "index_url": index_url, "sha256": digest,
                       "stage": "first_page"}
                self.state["rejected"].append(rec)
                seen[url] = {"status": "rejected", "reason": s2, "sha256": digest}
                return
        doc_bucket = "supporting" if bucket == "supporting" else "statement"
        target = raw.archive_path(self.root, self.symbol, digest, kind, doc_bucket)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp.replace(target)
        if doc_bucket == "supporting":
            supporting = sub
            doc_type = "supporting_" + sub
        else:
            doc_type = "annual_report" if sub == "annual_report" else "financial_statement"
            if sub != "annual_report" and re.search(
                    r"annual report|التقرير السنوي", own, re.I) and not re.search(
                    r"financial statements?", own, re.I):
                doc_type = "annual_report"
        per = self._period(own, head, ctx, fy_end_month)
        doc = {
            "company_id": self.state["company_id"], "symbol": self.symbol,
            "source_url": url, "index_url": index_url, "source": source,
            "bucket": doc_bucket, "supporting_type": supporting,
            "document_type": doc_type, "fiscal_year": per["fiscal_year"],
            "period_slot": per["period_slot"], "period_end": per["period_end"],
            "language": raw.detect_language(f"{title} {head}") if head else
            raw.detect_language(title),
            "downloaded_at": NOW(), "content_hash": digest, "file_kind": kind,
            "bytes": len(content), "title": title[:200],
            "scanned": scanned, "local_path": str(target),
            "classification_method": per["method"],
            "evidence": self._evidence(own, head),
            **raw.variant_flags(f"{own} {head[:300]}"),
        }
        self.state["docs"].append(doc)
        seen[url] = {"status": "collected", "sha256": digest}
        self.new_files += 1
        if doc_bucket == "statement" and not (per["period_slot"] and per["fiscal_year"]):
            self.state["unclassified"].append(
                {"url": url, "sha256": digest, "title": title[:150],
                 "reason": "unclassified"})
        if scanned:
            self.fail("scanned", "image-only pdf archived", url)
        jlog(self.root / "logs" / "documents.jsonl", doc)
        jlog(self.root / "outbox" / "pending_upload.jsonl",
             raw.outbox_row(self.symbol, target, digest, kind, doc_bucket))
        self.log({"event": "collected", "symbol": self.symbol, "url": url,
                  "bucket": doc_bucket, "slot": per["period_slot"],
                  "fy": per["fiscal_year"], "type": doc_type, "sha256": digest})

    @staticmethod
    def _period(own: str, head: str, ctx: str, fy_end_month: int) -> dict:
        best = raw.classify_period(own, fy_end_month)
        if best["period_slot"] and best["fiscal_year"]:
            return best
        for extra in (head, f"{own} {head}", f"{own} {ctx}"):
            if not extra:
                continue
            cand = raw.classify_period(extra, fy_end_month)
            if cand["period_slot"] and cand["fiscal_year"]:
                return cand
            if cand["period_slot"] and not best["period_slot"]:
                best = cand
        return best


def reclassify_doc(root: Path, doc: dict, fy_end_month: int) -> None:
    """Re-derive bucket/period/variant of an archived file from stored metadata
    plus the file's own first page.  Never deletes or re-downloads."""
    own = f"{doc.get('title', '')} {title_from_url(doc['source_url'])}"
    path = Path(doc["local_path"])
    head = ""
    if path.exists():
        head = " ".join(first_page_text(path, doc["file_kind"]).split())[:1500]
    if not head:
        head = doc.get("evidence", "").split("||", 1)[-1].strip()
    bucket, sub = raw.classify_bucket(own)
    if bucket == "rejected" and sub == "not_financial":
        bucket, sub = "statement", "statement"
    if bucket == "statement" and head:
        b2, s2 = raw.classify_bucket(f"{own} {head[:400]}")
        if b2 == "rejected" and s2 in {"presentation", "board_report", "sustainability",
                                      "prospectus", "credit_rating", "transcript"}:
            bucket, sub = "rejected", s2
    doc["excluded_reason"] = None
    if bucket == "rejected":
        doc["bucket"], doc["excluded_reason"] = "excluded", sub
        doc["supporting_type"] = None
    elif bucket == "supporting":
        doc["bucket"], doc["supporting_type"] = "supporting", sub
        doc["document_type"] = "supporting_" + sub
        target = raw.archive_path(root, doc["symbol"], doc["content_hash"],
                                  doc["file_kind"], "supporting")
        if path.exists() and path != target:
            target.parent.mkdir(parents=True, exist_ok=True)
            path.replace(target)
            doc["local_path"] = str(target)
    else:
        doc["bucket"], doc["supporting_type"] = "statement", None
        if sub == "annual_report" or (re.search(r"annual report|التقرير السنوي", own, re.I)
                                      and not re.search(r"financial statements?", own, re.I)):
            doc["document_type"] = "annual_report"
        else:
            doc["document_type"] = "financial_statement"
    per = CompanyRun._period(own, head, "", fy_end_month)
    doc["fiscal_year"], doc["period_slot"] = per["fiscal_year"], per["period_slot"]
    doc["period_end"], doc["classification_method"] = per["period_end"], per["method"]
    doc["language"] = raw.detect_language(f"{doc.get('title', '')} {head}") if head else doc.get("language")
    doc["evidence"] = " ".join(f"{own} || {head}".split())[:600]
    doc.update(raw.variant_flags(f"{own} {head[:300]}"))


def reclassify_state(root: Path, st: dict) -> None:
    fy = st.get("fy_end_month", 12)
    for d in st["docs"]:
        reclassify_doc(root, d, fy)
    st["unclassified"] = [
        {"url": d["source_url"], "sha256": d["content_hash"], "title": d.get("title", "")[:150],
         "reason": "unclassified"} for d in st["docs"]
        if d["bucket"] == "statement" and not (d["period_slot"] and d["fiscal_year"])]


def infer_fy_end_month(anns: list[dict]) -> int:
    months = []
    for a in anns:
        d = a["SHORT_DESC"]
        if FIN_RESULT_TITLE.search(d) and re.search(
                r"annual|year ended|twelve", d, re.I):
            pe = raw.period_end_from_text(d)
            if pe:
                months.append(pe.month)
    if not months:
        return 12
    return max(set(months), key=months.count)


def process_company(root: Path, company: dict, batch: dict | None, se: SaudiExchange,
                    crawler: IssuerCrawler, dl: Downloader, log,
                    force: bool = False, se_sample_only: bool = True) -> dict:
    run = CompanyRun(root, company, batch, log)
    st = run.state
    if st.get("rules_version") != RULES_VERSION:
        # Newer classification rules: re-evaluate previously rejected URLs
        # (no re-download of files that are already archived).
        st["seen_urls"] = {u: v for u, v in st["seen_urls"].items()
                           if v.get("status") in ("collected", "duplicate")}
        reclassify_state(root, st)
        st["rejected"] = []
        st["failures"] = [f for f in st["failures"] if f["reason"] == "scanned"]
        st["status"] = "redo"
        st["rules_version"] = RULES_VERSION
    if st.get("status") == "done" and not force:
        log({"event": "skip_done", "symbol": run.symbol})
        return st
    st["started_at"] = NOW()
    # ---- Saudi Exchange
    try:
        anns = se.announcements(run.symbol)
    except Exception as exc:
        anns = []
        run.fail(classify_error(exc), f"saudi_exchange announcements: {exc}")
    st["se"] = {"total_announcements": len(anns)}
    fy_end = infer_fy_end_month(anns)
    st["fy_end_month"] = fy_end
    results = []
    for a in anns:
        if not FIN_RESULT_TITLE.search(a["SHORT_DESC"]):
            continue
        if re.search(r"general assembly|dividend|recommend|distribut|board of dir",
                     a["SHORT_DESC"], re.I) and not re.search(
                     r"financial results", a["SHORT_DESC"], re.I):
            continue
        per = raw.classify_period(a["SHORT_DESC"], fy_end)
        results.append({"id": a["PRESS_REL_ID"], "date": a["PR_DATE"],
                        "title": a["SHORT_DESC"][:200], "url": SE + a["announcementUrl"],
                        **per})
    expected = raw.expected_slots(
        [raw.date.fromisoformat(r["period_end"]) for r in results
         if r["period_end"] and r["period_slot"]], fy_end)
    st["expected"] = {f"{y}|{s}": pe for (y, s), pe in expected.items()}
    st["se"]["results_announcements"] = len(results)
    st["se"]["results_by_slot"] = {}
    for r in results:
        if r["period_slot"] and r["fiscal_year"]:
            st["se"]["results_by_slot"].setdefault(
                f"{r['fiscal_year']}|{r['period_slot']}", []).append(r["id"])
    # detail pages: newest 6 + oldest 4 + 4 spread; stop early if none has files
    checked, with_files = [], 0
    if results:
        idx = list(range(len(results)))
        order = idx[:6] + idx[-4:] + idx[6:-4:max(1, (len(idx) - 10) // 4 or 1)][:4]
        if not se_sample_only:
            order = idx
        for i in dict.fromkeys(order):
            r = results[i]
            try:
                files = se.detail_files(run.symbol, {"announcementUrl": r["url"].replace(SE, "")})
            except Exception as exc:
                run.fail(classify_error(exc), f"se detail {r['id']}: {exc}", r["url"])
                continue
            checked.append(r["id"])
            for f in files:
                with_files += 1
                run.handle_candidate(dl, f, r["title"], "", r["url"],
                                     "saudi_exchange", fy_end)
        # if any detail page had files, check the remainder too (attachments
        # exist for this issuer, so history is worth completing).
        if with_files and se_sample_only:
            for r in results:
                if r["id"] in checked:
                    continue
                try:
                    files = se.detail_files(run.symbol, {"announcementUrl": r["url"].replace(SE, "")})
                except Exception as exc:
                    run.fail(classify_error(exc), f"se detail {r['id']}: {exc}", r["url"])
                    continue
                checked.append(r["id"])
                for f in files:
                    run.handle_candidate(dl, f, r["title"], "", r["url"],
                                         "saudi_exchange", fy_end)
    st["se"]["detail_pages_checked"] = len(checked)
    st["se"]["detail_pages_with_files"] = with_files
    jsave(root / "logs" / "se" / f"{run.symbol}-announcements.json",
          [{"id": a["PRESS_REL_ID"], "date": a["PR_DATE"], "title": a["SHORT_DESC"]}
           for a in anns])
    run.save()
    # ---- issuer site
    site = batch.get("official_website") if batch else None
    prof = None
    if not (company.get("sources") or batch):
        prof = se.profile_website(run.symbol)
    seeds = seeds_for(company, batch, prof)
    st["issuer"] = {"seeds": seeds, "profile_website": prof}
    if not seeds:
        st["issuer"].update(status="no_source", pages=0)
        run.fail("no_source", "no registry source and no Saudi Exchange website")
    else:
        try:
            res = crawler.crawl(seeds)
        except Exception as exc:
            res = {"docs": {}, "status": classify_error(exc), "pages": 0,
                   "errors": [str(exc)[:200]]}
        st["issuer"].update(status=res["status"], pages=res["pages"],
                            doc_links=len(res["docs"]), errors=res["errors"])
        if res["status"] != "ok":
            run.fail(res["status"], "; ".join(res["errors"]))
        for url, (text, ctx, page_url) in res["docs"].items():
            run.handle_candidate(dl, url, text, ctx, page_url, "issuer_site", fy_end)
            if run.new_files and run.new_files % 20 == 0:
                run.save()
    # ---- ledger
    run.ledger.docs = st["docs"]
    run.ledger.expected = expected
    reason = None
    if st["issuer"].get("status") == "no_source":
        reason = "no_source"
    elif st["issuer"].get("status") != "ok":
        reason = st["issuer"]["status"]
    for (y, s) in expected:
        det = "se_announcement_has_no_attachment"
        run.ledger.slot_reasons[(y, s)] = (
            f"{det};issuer_site:{reason}" if reason else f"{det};not_found_on_issuer_pages")
    st["coverage"] = {str(y): row for y, row in run.ledger.coverage().items()}
    st["counts"] = run.ledger.counts()
    st["supporting_counts"] = run.ledger.supporting_counts()
    st["status"] = "done"
    st["finished_at"] = NOW()
    run.save()
    return st


# ---------------------------------------------------------------------------
# browser context


@contextlib.contextmanager
def browser(edge: Path = EDGE):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=str(edge), headless=True,
                               args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(accept_downloads=False, locale="en-US",
                            ignore_https_errors=True, user_agent=UA)
        try:
            yield ctx
        finally:
            with contextlib.suppress(Exception):
                b.close()


def shard(registry_path=REGISTRY):
    return raw.odd_shard(raw.load_registry(registry_path))


def cmd_run(args) -> int:
    root = Path(args.root)
    companies = shard()
    if args.symbols:
        wanted = set(args.symbols.split(","))
        companies = [c for c in companies if c["symbol"] in wanted]
        missing = wanted - {c["symbol"] for c in companies}
        if missing:
            print(f"symbols not in odd shard (refusing): {sorted(missing)}")
            return 2
        name = args.name or "custom"
    else:
        parts = raw.split_workers(companies, args.workers)
        companies = parts[args.worker_index]
        name = f"worker-{args.worker_index}"
    logf = root / "logs" / f"{name}.jsonl"
    log = lambda ev: jlog(logf, ev)  # noqa: E731
    sources = load_sources()
    done = 0
    log({"event": "start", "worker": name, "companies": len(companies)})
    batch_size = 12
    for start in range(0, len(companies), batch_size):
        chunk = companies[start:start + batch_size]
        try:
            with browser() as ctx:
                se = SaudiExchange(ctx, log)
                crawler = IssuerCrawler(ctx, log)
                dl = Downloader(ctx, log, se.detail)
                for c in chunk:
                    t = time.time()
                    try:
                        st = process_company(root, c, sources.get(c["symbol"]), se,
                                             crawler, dl, log, force=args.force,
                                             se_sample_only=not args.se_full)
                        print(f"[{name}] {c['symbol']} docs={len(st['docs'])} "
                              f"exp={len(st.get('expected', {}))} "
                              f"{round(time.time() - t)}s", flush=True)
                    except Exception as exc:
                        log({"event": "company_error", "symbol": c["symbol"],
                             "error": str(exc)[:300]})
                        print(f"[{name}] {c['symbol']} ERROR {exc}", flush=True)
                    done += 1
        except Exception as exc:
            log({"event": "browser_error", "error": str(exc)[:300]})
            print(f"[{name}] browser error: {exc}", flush=True)
            time.sleep(10)
    log({"event": "finished", "worker": name, "processed": done})
    if args.upload:
        return cmd_upload(args)
    return 0


def cmd_recompute(args) -> int:
    """Offline: re-run classification over the archive; no network."""
    root = Path(args.root)
    for f in sorted((root / "state" / "companies").glob("*.json")):
        st = jload(f, {})
        reclassify_state(root, st)
        if st.get("expected") is not None:
            led = raw.Ledger(st["symbol"])
            led.docs = st["docs"]
            exp = {tuple([int(k.split("|")[0]), k.split("|")[1]]): v
                   for k, v in st["expected"].items()}
            led.expected = exp
            reason = st.get("issuer", {}).get("status")
            for k in exp:
                led.slot_reasons[k] = "se_announcement_has_no_attachment;" + (
                    "issuer_site:" + reason if reason not in (None, "ok")
                    else "not_found_on_issuer_pages")
            st["coverage"] = {str(y): r for y, r in led.coverage().items()}
            st["counts"] = led.counts()
            st["supporting_counts"] = led.supporting_counts()
        jsave(f, st)
    print("recomputed")
    return 0


def cmd_upload(args) -> int:
    root = Path(args.root)
    outbox = root / "outbox" / "pending_upload.jsonl"
    uploaded_path = root / "state" / "uploaded.json"
    uploaded = jload(uploaded_path, {})
    if not (args.ssh_key and Path(args.ssh_key).exists() and
            args.known_hosts and Path(args.known_hosts).exists()):
        print("ssh key / known_hosts not available: local-only mode; outbox kept "
              f"at {outbox}")
        return 0
    rows = [json.loads(x) for x in outbox.read_text(encoding="utf-8").splitlines() if x.strip()] \
        if outbox.exists() else []
    for row in rows:
        if uploaded.get(row["sha256"]):
            continue
        kind = Path(row["local_path"]).suffix.lstrip(".")
        cmds = raw.upload_commands(args.server, args.worker, args.ssh_key,
                                   args.known_hosts, row["symbol"], row["local_path"],
                                   row["sha256"], kind)
        assert raw.commands_are_raw_only(cmds)
        try:
            for cmd in cmds:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                if r.returncode:
                    raise RuntimeError(r.stderr[-300:])
            uploaded[row["sha256"]] = NOW()
            jsave(uploaded_path, uploaded)
        except Exception as exc:
            print(f"upload failed {row['symbol']} {row['sha256'][:10]}: {exc}")
            break
    return 0


def cmd_launch(args) -> int:
    root = Path(args.root)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    for i in range(args.workers):
        out = open(root / "logs" / f"worker-{i}.out", "ab")
        flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0  # DETACHED|NEW_GROUP
        cmd = [sys.executable, "-B", "-u", str(Path(__file__).resolve()), "run",
               "--root", str(root), "--workers", str(args.workers),
               "--worker-index", str(i)]
        subprocess.Popen(cmd, stdout=out, stderr=out, stdin=subprocess.DEVNULL,
                         creationflags=flags, cwd=str(PROJECT), close_fds=True)
        print("launched worker", i)
    return 0


def cmd_merge(args) -> int:
    root = Path(args.root)
    companies = shard()
    rows, agg = [], {"companies": len(companies), "finished": 0,
                     "counts": {s: 0 for s in raw.SLOTS},
                     "fy_via_annual_report": 0, "unclassified": 0, "files": 0,
                     "supporting": {"pillar3": 0, "data_supplement": 0, "factsheet": 0},
                     "excluded_after_download": 0,
                     "failures": {}, "rejected": {}}
    detail = []
    pending = {}
    outbox = root / "outbox" / "pending_upload.jsonl"
    uploaded = jload(root / "state" / "uploaded.json", {})
    if outbox.exists():
        for line in outbox.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                pending[r["sha256"]] = r
    for c in companies:
        st = jload(root / "state" / "companies" / f"{c['symbol']}.json", None)
        if not st or st.get("status") != "done":
            detail.append({"symbol": c["symbol"], "name": c["name"], "status": "not_finished"})
            continue
        agg["finished"] += 1
        led = raw.Ledger(c["symbol"])
        led.docs = st["docs"]
        cnt = led.counts()
        for s in raw.SLOTS:
            agg["counts"][s] += cnt[s]
        agg["fy_via_annual_report"] += cnt["fy_via_annual_report"]
        agg["unclassified"] += cnt["unclassified"]
        agg["files"] += len(st["docs"])
        sc = led.supporting_counts()
        for k, v in sc.items():
            agg["supporting"][k] = agg["supporting"].get(k, 0) + v
        agg["excluded_after_download"] += sum(1 for d in st["docs"] if d.get("bucket") == "excluded")
        for f in st["failures"]:
            agg["failures"][f["reason"]] = agg["failures"].get(f["reason"], 0) + 1
        for r in st["rejected"]:
            agg["rejected"][r["reason"]] = agg["rejected"].get(r["reason"], 0) + 1
        cov = st.get("coverage", {})
        for year, row in sorted(cov.items()):
            for slot in raw.SLOTS:
                cell = row[slot]
                rows.append({
                    "symbol": c["symbol"], "name": c["name"], "fiscal_year": year,
                    "slot": slot, "status": cell["status"],
                    "content_hash": cell.get("hash", ""),
                    "distinct_files": cell.get("distinct_files", ""),
                    "same_language_extras": cell.get("same_language_extras", ""),
                    "variant_hashes": ";".join(v["hash"][:12] + ":" + str(v.get("language")) + ":" + str(v.get("scope")) + (":amended" if v.get("amended") else "") for v in cell.get("variants", [])),
                    "reason": cell.get("reason", "")})
        exp = st.get("expected", {})
        got = sum(1 for y, r in cov.items() for s in raw.SLOTS
                  if r[s]["status"] == "collected")
        miss = sum(1 for y, r in cov.items() for s in raw.SLOTS
                   if r[s]["status"] == "missing")
        detail.append({
            "symbol": c["symbol"], "name": c["name"], "status": "finished",
            "expected_slots": len(exp), "collected_slots": got,
            "missing_slots": miss, "complete": bool(exp) and miss == 0,
            "files": len(st["docs"]), "Q1": cnt["Q1"], "H1": cnt["H1"],
            "9M": cnt["9M"], "FY": cnt["FY"],
            "fy_via_annual_report": cnt["fy_via_annual_report"],
            "unclassified": cnt["unclassified"], "supporting": sc,
            "years": sorted(cov), "issuer_status": st.get("issuer", {}).get("status"),
            "se_results_announcements": st.get("se", {}).get("results_announcements"),
            "se_detail_pages_with_files": st.get("se", {}).get("detail_pages_with_files"),
            "failures": sorted({f["reason"] for f in st["failures"]}),
        })
    agg["aws_uploaded"] = sum(1 for h in pending if uploaded.get(h))
    agg["pending_upload"] = sum(1 for h in pending if not uploaded.get(h))
    agg["remaining"] = agg["companies"] - agg["finished"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    import csv
    with (out / "sa-raw-statements-odd-coverage.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["symbol", "name", "fiscal_year", "slot",
                                           "status", "content_hash", "distinct_files", "same_language_extras", "variant_hashes", "reason"])
        w.writeheader()
        w.writerows(rows)
    jsave(out / "sa-raw-statements-odd-coverage.json",
          {"generated_at": NOW(), "summary": agg, "companies": detail})
    print(json.dumps(agg, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "launch", "merge", "upload", "recompute"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=str(DEFAULT_ROOT))
        p.add_argument("--workers", type=int, default=4)
        p.add_argument("--worker-index", type=int, default=0)
        p.add_argument("--symbols")
        p.add_argument("--name")
        p.add_argument("--force", action="store_true")
        p.add_argument("--se-full", action="store_true",
                       help="open every results announcement detail page")
        p.add_argument("--upload", action="store_true")
        p.add_argument("--ssh-key")
        p.add_argument("--known-hosts")
        p.add_argument("--server", default="ubuntu@13.60.3.12")
        p.add_argument("--worker", default="repo-worker-1")
        p.add_argument("--out", default=str(PROJECT / "docs" / "data"))
    args = ap.parse_args(argv)
    return {"run": cmd_run, "launch": cmd_launch, "merge": cmd_merge,
            "upload": cmd_upload, "recompute": cmd_recompute}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
