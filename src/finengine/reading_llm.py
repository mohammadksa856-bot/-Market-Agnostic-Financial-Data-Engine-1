from __future__ import annotations

"""LLM pass for the reader agent - the fallback behind the deterministic reader.

It reads the *already extracted* text of a filing's statement pages (never the
raw PDF bytes) and returns the same manifest shape. It is confined to the
extraction stage: its output is staging that must still pass `finengine verify`
and the deterministic publication gate. The model is instructed to copy digits
verbatim, use the current reporting period, and never compute or infer a value.

Requires the optional `llm` extra (`pip install -e ".[llm]"`) and an
`ANTHROPIC_API_KEY`. Use it when the deterministic reader cannot read a page
(scanned images, Arabic-only right-to-left tables, unusual layouts).
"""

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
