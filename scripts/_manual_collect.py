"""Collect a hand-curated list of document URLs for one company using a
plain HTTP downloader, reusing the real collector's own classification/
hashing/archiving pipeline (CompanyRun.handle_candidate) unchanged.

Why this exists: two companies (Saudi Energy/5110, NBM/9510) hang forever
under Playwright/headless-Edge regardless of page, timeout length, or
process isolation - confirmed live. A plain HTTP GET of the exact same
file URL, from the exact same machine, succeeds in seconds. The hang is
specific to browser automation, not the site or the network path. This
script downloads a URL list gathered by hand (a real, interactive browser
session) via plain HTTP instead, so those two companies are not
permanently stuck just because Playwright cannot talk to their site.

Usage: edit URLS below (or pass --file with one "url\\ttitle" per line),
then: _manual_collect.py --root <dir> --symbol <symbol> [--file path]
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sa_raw_statement_collector as col  # noqa: E402
from finengine import sa_raw_statements as raw  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


class PlainHttpDownloader:
    """Drop-in replacement for col.Downloader.get() using plain HTTP,
    no browser/Playwright involved at all."""

    def __init__(self, log):
        self.log = log
        self.last = 0.0

    def get(self, url: str, referer: str | None) -> bytes:
        wait = self.last + 1.0 - time.time()
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        headers = {"User-Agent": UA}
        if referer:
            # HTTP header values must be latin-1; a referer URL with raw
            # non-ASCII characters (e.g. an Arabic URL path) breaks
            # urllib's own header encoding otherwise.
            headers["Referer"] = urllib.parse.quote(referer, safe=":/?&=%")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--file", help="one 'url<TAB>title' per line; "
                    "if omitted, reads the same from stdin")
    ap.add_argument("--index-url", default="", help="the page these links were found on")
    ap.add_argument("--fy-end-month", type=int, default=12)
    args = ap.parse_args()
    root = Path(args.root)

    lines = (Path(args.file).read_text(encoding="utf-8") if args.file
             else sys.stdin.read()).splitlines()
    items = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", 1)
        url = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else col.title_from_url(url)
        items.append((url, title))
    print(f"{len(items)} URL(s) to process for {args.symbol}")

    reg = raw.load_registry(col.REGISTRY)
    company = next((c for c in reg if c["symbol"] == args.symbol), None)
    if company is None:
        print(f"symbol {args.symbol} not in registry", file=sys.stderr)
        return 2

    logf = root / "logs" / f"manual-{args.symbol}.jsonl"
    log = lambda ev: col.jlog(logf, ev)  # noqa: E731
    run = col.CompanyRun(root, company, None, log, part="issuer")
    dl = PlainHttpDownloader(log)
    before = len(run.state["docs"])
    for url, title in items:
        run.handle_candidate(dl, url, title, "", args.index_url,
                             "manual_http", args.fy_end_month)
    run.save()
    after = len(run.state["docs"])
    print(f"docs: {before} -> {after} (+{after - before})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
