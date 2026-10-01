"""Archive a Saudi Exchange disclosure that has no downloadable PDF of its
own - only an HTML data table on the announcement detail page - by
rendering that table/text into a real PDF and feeding it through the
collector's own classification/hashing/archiving pipeline unchanged.

Some issuers (confirmed live: Watani Steel/9513's routine quarterly and
annual results) publish real, complete financial disclosure (revenue,
profit, equity, EPS, management commentary) directly as a Saudi Exchange
announcement-detail page, with no PDF/XLSX attachment at all - the number
this collector is built to archive exists, it is just never a file. This
turns the page's own text into one, so the same real figures end up
in the archive instead of being dropped as "nothing to collect".

Usage: write the announcement's visible text to a .txt file (one file per
announcement; get it via get_page_text on the real announcement-details
page - this script does not fetch pages itself, since these specific
pages are exactly the kind that need a real browser to render), then:

  _scrape_disclosure.py --root <dir> --symbol <symbol> --title <title>
      --source-url <tadawul-announcement-url> --fiscal-year <YYYY>
      --period-slot <Q1|H1|9M|FY> --text-file <path>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sa_raw_statement_collector as col  # noqa: E402
from finengine import sa_raw_statements as raw  # noqa: E402

from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

ARABIC_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def _register_font() -> str:
    for path in ARABIC_FONT_CANDIDATES:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont("ArabicFont", path))
            return "ArabicFont"
    return "Helvetica"  # no Arabic glyphs, but keeps this from hard-failing


def text_to_pdf(text: str, out_path: Path, title: str) -> None:
    font = _register_font()
    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4
    c.setFont(font, 10)
    y = height - 50
    c.drawString(40, y, title[:120])
    y -= 25
    c.setFont(font, 9)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            y -= 8
            continue
        # Wrap long lines crudely so nothing runs off the page edge -
        # exact visual shaping is not the goal here, text-layer
        # extractability for the archive/classifier is.
        while line:
            chunk, line = line[:110], line[110:]
            if y < 40:
                c.showPage()
                c.setFont(font, 9)
                y = height - 50
            c.drawString(40, y, chunk)
            y -= 13
    c.save()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--fiscal-year", type=int, required=True)
    ap.add_argument("--period-slot", required=True, choices=["Q1", "H1", "9M", "FY"])
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--fy-end-month", type=int, default=12)
    args = ap.parse_args()
    root = Path(args.root)
    text = Path(args.text_file).read_text(encoding="utf-8")

    reg = raw.load_registry(col.REGISTRY)
    company = next((c for c in reg if c["symbol"] == args.symbol), None)
    if company is None:
        print(f"symbol {args.symbol} not in registry", file=sys.stderr)
        return 2

    tmp_pdf = root / "tmp" / f"disclosure-{args.symbol}-{args.fiscal_year}-{args.period_slot}.pdf"
    tmp_pdf.parent.mkdir(parents=True, exist_ok=True)
    text_to_pdf(text, tmp_pdf, args.title)
    content = tmp_pdf.read_bytes()

    logf = root / "logs" / f"scrape-{args.symbol}.jsonl"
    log = lambda ev: col.jlog(logf, ev)  # noqa: E731
    run = col.CompanyRun(root, company, None, log, part="issuer")

    digest = raw.sha256_bytes(content)
    if any(d["content_hash"] == digest for d in run.state["docs"]):
        print("duplicate, already archived")
        tmp_pdf.unlink(missing_ok=True)
        return 0
    target = raw.archive_path(root, args.symbol, digest, "pdf", "statement")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_pdf.replace(target)

    doc = {
        "company_id": run.state["company_id"], "symbol": args.symbol,
        "source_url": args.source_url, "index_url": args.source_url,
        "source": "tadawul_disclosure_table_scrape",
        "bucket": "statement", "supporting_type": None,
        "document_type": "financial_statement",
        "fiscal_year": args.fiscal_year, "period_slot": args.period_slot,
        "period_end": None, "language": raw.detect_language(text),
        "downloaded_at": col.NOW(), "content_hash": digest, "file_kind": "pdf",
        "bytes": len(content), "title": args.title[:200], "scanned": False,
        "local_path": str(target), "classification_method": "manual_scrape",
        "evidence": " ".join((args.title + " " + text[:500]).split())[:600],
        "scope": None, "amended": False,
    }
    run.state["docs"].append(doc)
    run.state["seen_urls"][args.source_url] = {"status": "collected", "sha256": digest}
    run.save()
    log({"event": "collected", "symbol": args.symbol, **doc})
    print(f"archived: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
