from __future__ import annotations

"""LLM pass for the reader agent - the fallback behind the deterministic reader.

Two entry points, both confined to the extraction stage (output is staging that
must still pass `finengine verify` and the deterministic publication gate; the
model is told to copy digits verbatim and never compute or infer a value):

* ``llm_read`` reads the *already extracted text* of a filing's statement pages.
  Current reporting period only. Use for text PDFs the deterministic reader
  cannot parse (unusual layouts, RTL tables).
* ``llm_read_vision`` renders the scanned statement pages to images and reads
  them. Captures every period column printed on the page. Use when the pages
  carry no extractable text at all (image-only "signed" filings).

Both require the optional ``llm`` extra (``pip install -e ".[llm]"``) and an
``ANTHROPIC_API_KEY``; ``llm_read_vision`` also needs ``pymupdf``.
"""

import base64
import json
import re
from decimal import Decimal
from pathlib import Path

from .catalog import iter_catalog_fields
from .database import DEFAULT_METRICS
from .reading import ANCHORS, LINE_MAP, _SCALE_PATTERNS

DEFAULT_MODEL = "claude-opus-5"

# The canonical vocabulary the model must map into - core metrics plus the
# reviewed catalog fields, so the manifest stays inside the engine's schema.
_VOCAB = sorted(
    set(DEFAULT_METRICS)
    | {metric for metric, _ in LINE_MAP.values()}
    | {f["field_key"] for f in iter_catalog_fields() if f["storage_domain"] == "data_points"}
)

_PERIOD_KINDS = ("fy", "quarter", "ytd", "instant")

_SYSTEM = (
    "You transcribe figures from a company's primary financial statements into a "
    "strict JSON manifest. Rules, in order of importance:\n"
    "1. Copy digits exactly as printed. Never compute, round, infer or reconcile a "
    "value. If a line is not printed, omit it.\n"
    "2. Use only the current reporting period's column (the most recent date in the "
    "statement header). Ignore prior-year comparatives.\n"
    "3. Parenthesised or clearly negative amounts are negative. Expenses, tax and "
    "cash outflows keep their printed sign.\n"
    "4. Map each line to one canonical metric from the provided list, or omit it. "
    "Keep the exact printed label in source_label.\n"
    "5. period_kind: 'instant' for balance-sheet items, 'fy' for annual flows, "
    "'quarter'/'ytd' only if the statement is explicitly a discrete quarter or "
    "year-to-date period.\n"
    "6. scale is the statement's stated unit multiplier as a plain integer string "
    "('1000' for thousands, '1000000' for millions, '1' if figures are already "
    "whole). Non-monetary metrics (per-share, ratios, production) omit scale."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "reporting_scale": {"type": "string"},
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": _VOCAB},
                    "source_label": {"type": "string"},
                    "value": {"type": "string"},
                    "period_kind": {"type": "string", "enum": list(_PERIOD_KINDS)},
                    "scale": {"type": "string"},
                    "page": {"type": "integer"},
                },
                "required": ["metric", "source_label", "value", "period_kind"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["facts"],
    "additionalProperties": False,
}


def _statement_pages(pdf_path: Path) -> list[tuple[int, str]]:
    import pymupdf

    doc = pymupdf.open(pdf_path)
    pages: list[tuple[int, str]] = []
    for index in range(doc.page_count):
        text = doc[index].get_text()
        low = text.lower()
        head = low[:120]
        leads = any(a in head for anchors in ANCHORS.values() for a in anchors)
        if leads and re.search(r"\b20\d{2}\b", text) and len(text.split()) >= 6:
            pages.append((index + 1, text))
    doc.close()
    return pages


def _detect_scale(pages: list[tuple[int, str]]) -> str:
    joined = " ".join(text for _, text in pages).lower()
    for pattern, value in _SCALE_PATTERNS:
        if pattern.search(joined):
            return str(int(value))
    return "1"


def llm_read(pdf_path: str | Path, *, market: str, symbol: str, currency: str,
             source_url: str, filed_at: str, period_end: str | None = None,
             fiscal_year: int | None = None, filing_type: str = "financial-statements",
             model: str = DEFAULT_MODEL, client=None, profile: str = "corporate") -> dict:
    # profile is accepted for call-site symmetry with the deterministic reader.
    # The vocabulary already spans every catalog field (banking pack included),
    # so no per-profile narrowing is needed here.
    pdf_path = Path(pdf_path)
    pages = _statement_pages(pdf_path)
    if not pages:
        raise RuntimeError(f"no primary-statement pages found in {pdf_path.name}")

    if fiscal_year is None:
        from .reading import StatementReader
        fiscal_year = StatementReader(pdf_path).infer_fiscal_year()
        if fiscal_year is None:
            raise ValueError(
                f"could not infer the reporting year from {pdf_path.name}; "
                "pass fiscal_year explicitly")
    if period_end is None:
        period_end = f"{fiscal_year}-12-31"

    if client is None:
        try:
            import anthropic
        except ImportError as error:  # pragma: no cover - environment dependent
            raise RuntimeError(
                'the LLM reader needs the optional "llm" extra: pip install -e ".[llm]"'
            ) from error
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

    default_scale = _detect_scale(pages)
    document = "\n\n".join(f"===== PAGE {page} =====\n{text}" for page, text in pages)
    user = (
        f"Company: {symbol} ({market}). Reporting currency: {currency}. "
        f"Fiscal year ending {period_end}. Likely reporting scale: {default_scale}.\n\n"
        f"Canonical metrics you may use (map to these or omit the line):\n"
        f"{', '.join(_VOCAB)}\n\n"
        f"Statement pages:\n{document}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
    )
    payload = json.loads(next(b.text for b in response.content if b.type == "text"))

    facts: list[dict] = []
    seen: set[tuple[str, str]] = set()
    monetary_free = {"eps_diluted", "dividends_per_share"}
    for item in payload.get("facts", []):
        metric = item["metric"]
        kind = item["period_kind"]
        key = (metric, kind)
        if key in seen or metric not in _VOCAB:
            continue
        try:
            Decimal(item["value"].replace(",", "").strip("()"))
        except Exception:
            continue
        seen.add(key)
        fact = {
            "metric": metric, "source_label": item["source_label"].strip(),
            "value": item["value"].replace(",", "").strip(), "period_end": period_end,
            "period_kind": kind, "fiscal_year": fiscal_year,
        }
        if item.get("page"):
            fact["page"] = int(item["page"])
        if kind in {"fy", "ytd", "quarter"}:
            fact["period_start"] = f"{fiscal_year}-01-01"
        is_monetary = (
            metric not in monetary_free
            and not any(metric == f["field_key"] and f["category"] in {"ratios", "per_share", "operational"}
                        for f in iter_catalog_fields()))
        if is_monetary:
            fact.update(scale=item.get("scale") or default_scale,
                        currency=currency, unit=currency)
        facts.append(fact)

    return {
        "filing_type": filing_type, "filed_at": filed_at, "period_end": period_end,
        "source_url": source_url, "reader": f"finengine.reading_llm/{model}", "profile": profile,
        "model_usage": {"input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens},
        "facts": sorted(facts, key=lambda f: (f.get("page", 0), f["metric"])),
    }


# --- vision path: read scanned statement pages as images -------------------

_VISION_SYSTEM = (
    "You transcribe figures from images of a company's primary financial "
    "statements into a strict JSON manifest. Rules, in order of importance:\n"
    "1. Copy digits exactly as printed. Never compute, round, infer or reconcile "
    "a value. If a line is not printed, omit it.\n"
    "2. Capture EVERY period column shown (typically the current year and one "
    "prior-year comparative). Emit one fact per (line, period). Put the column's "
    "own year in fiscal_year and its balance-sheet / year-end date in "
    "period_end (YYYY-MM-DD).\n"
    "3. Parenthesised, bracketed or red amounts are negative. Expenses, tax and "
    "cash outflows keep their printed sign.\n"
    "4. Map each line to one canonical metric from the provided list, or omit it. "
    "Keep the exact printed label in source_label. Never invent a metric name.\n"
    "5. period_kind: 'instant' for statement-of-financial-position items, 'fy' "
    "for annual profit-or-loss and cash-flow items.\n"
    "6. scale is the statement's stated unit multiplier as a plain integer string "
    "('1000' thousands, '1000000' millions, '1' if already whole). Per-share "
    "figures and ratios omit scale.\n"
    "7. page is the 1-indexed PDF page the image came from (given with each image)."
)

_VISION_SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": _VOCAB},
                    "source_label": {"type": "string"},
                    "value": {"type": "string"},
                    "period_kind": {"type": "string", "enum": ["fy", "instant"]},
                    "period_end": {"type": "string"},
                    "fiscal_year": {"type": "integer"},
                    "scale": {"type": "string"},
                    "page": {"type": "integer"},
                },
                "required": ["metric", "source_label", "value", "period_kind",
                             "fiscal_year"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["facts"],
    "additionalProperties": False,
}


def _scanned_statement_pages(pdf_path: Path, max_pages: int = 10) -> list[int]:
    """1-indexed pages that look like a scanned primary statement: little or no
    extractable text, at least one image, and a statement anchor on the page or
    an immediate neighbour (the heading is often on the image, not in the text
    layer, so a nearby digital heading page is a good signal too)."""
    import pymupdf

    doc = pymupdf.open(pdf_path)
    anchors = tuple(a for group in ANCHORS.values() for a in group)
    heading_pages, sparse_pages = set(), []
    for index in range(doc.page_count):
        text = doc[index].get_text()
        low = text.lower()
        if any(a in low for a in anchors):
            heading_pages.add(index)
        words = len(text.split())
        if words <= 25 and doc[index].get_images():
            sparse_pages.append(index)
    out = [
        index for index in sparse_pages
        if index in heading_pages
        or (index - 1) in heading_pages or (index + 1) in heading_pages
        or not heading_pages  # nothing digital anywhere -> take the sparse pages
    ]
    doc.close()
    return [index + 1 for index in out[:max_pages]]


def _render_page_png(doc, page_index: int, zoom: float) -> bytes:
    import pymupdf

    pixmap = doc[page_index].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    return pixmap.tobytes("png")


def llm_read_vision(pdf_path: str | Path, *, market: str, symbol: str, currency: str,
                    source_url: str, filed_at: str, pages: list[int] | None = None,
                    period_end: str | None = None, fiscal_year: int | None = None,
                    filing_type: str = "financial-statements",
                    model: str = DEFAULT_MODEL, client=None, profile: str = "corporate",
                    zoom: float = 2.4, max_pages: int = 10) -> dict:
    """Read scanned primary-statement pages from their rendered images.

    ``pages`` (1-indexed) pins the exact pages to read; otherwise the scanned
    statement pages are auto-detected. Every period column on the page is
    captured, so the manifest carries the prior-year comparative too.
    """
    try:
        import pymupdf
    except ImportError as error:  # pragma: no cover - environment dependent
        raise RuntimeError(
            'the vision reader needs pymupdf: pip install -e ".[llm]"') from error

    pdf_path = Path(pdf_path)
    doc = pymupdf.open(pdf_path)
    try:
        if pages is None:
            pages = _scanned_statement_pages(pdf_path, max_pages)
        if not pages:
            raise RuntimeError(
                f"no scanned statement pages found in {pdf_path.name}; pass pages=[...]")
        pages = sorted({p for p in pages if 1 <= p <= doc.page_count})[:max_pages]
        images = [(p, _render_page_png(doc, p - 1, zoom)) for p in pages]
    finally:
        doc.close()

    if fiscal_year is None:
        from .reading import StatementReader
        fiscal_year = StatementReader(pdf_path).infer_fiscal_year()
    if fiscal_year is None:
        raise ValueError(
            f"could not infer the reporting year from {pdf_path.name}; "
            "pass fiscal_year explicitly")
    if period_end is None:
        period_end = f"{fiscal_year}-12-31"

    if client is None:
        try:
            import anthropic
        except ImportError as error:  # pragma: no cover - environment dependent
            raise RuntimeError(
                'the LLM reader needs the optional "llm" extra: pip install -e ".[llm]"'
            ) from error
        client = anthropic.Anthropic()

    content: list[dict] = [{
        "type": "text",
        "text": (
            f"Company {symbol} ({market}). Reporting currency {currency}. "
            f"Latest fiscal year ends {period_end}. Transcribe the primary "
            f"statements in the following {len(images)} page image(s). Map each "
            f"line to one of these canonical metrics or omit it:\n"
            f"{', '.join(_VOCAB)}"),
    }]
    for page, png in images:
        content.append({"type": "text", "text": f"--- PDF page {page} ---"})
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png",
                       "data": base64.standard_b64encode(png).decode("ascii")},
        })

    response = client.messages.create(
        model=model,
        max_tokens=32000,
        system=_VISION_SYSTEM,
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": _VISION_SCHEMA}},
    )
    payload = json.loads(next(b.text for b in response.content if b.type == "text"))

    ratio_categories = {"ratios", "per_share", "operational"}
    monetary_free = {"eps_diluted", "dividends_per_share"}
    ratio_fields = {
        f["field_key"] for f in iter_catalog_fields() if f["category"] in ratio_categories}
    facts: list[dict] = []
    seen: set[tuple] = set()
    for item in payload.get("facts", []):
        metric = item.get("metric")
        if metric not in _VOCAB:
            continue
        try:
            year = int(item["fiscal_year"])
        except (KeyError, TypeError, ValueError):
            continue
        kind = item["period_kind"]
        raw = str(item["value"]).replace(",", "").strip()
        negative = raw.startswith("(") and raw.endswith(")")
        clean = raw.strip("()")
        try:
            Decimal(clean)
        except Exception:
            continue
        if negative and not clean.startswith("-"):
            clean = "-" + clean
        key = (metric, kind, year)
        if key in seen:
            continue
        seen.add(key)
        p_end = item.get("period_end") or f"{year}-12-31"
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p_end):
            p_end = f"{year}-12-31"
        fact = {
            "metric": metric, "source_label": str(item["source_label"]).strip(),
            "value": clean, "period_end": p_end, "period_kind": kind,
            "fiscal_year": year,
        }
        if item.get("page"):
            fact["page"] = int(item["page"])
        if kind == "fy":
            fact["period_start"] = f"{year}-01-01"
        if metric not in monetary_free and metric not in ratio_fields:
            fact.update(scale=str(item.get("scale") or "1"),
                        currency=currency, unit=currency)
        facts.append(fact)

    return {
        "company_id": f"{market.lower()}:{symbol}",
        "market": market, "symbol": symbol,
        "filing_type": filing_type, "filed_at": filed_at, "period_end": period_end,
        "source_url": source_url,
        "reader": f"finengine.reading_llm_vision/{model}", "profile": profile,
        "pages_read": pages,
        "model_usage": {"input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens},
        "facts": sorted(facts, key=lambda f: (f["fiscal_year"], f.get("page", 0), f["metric"])),
    }
