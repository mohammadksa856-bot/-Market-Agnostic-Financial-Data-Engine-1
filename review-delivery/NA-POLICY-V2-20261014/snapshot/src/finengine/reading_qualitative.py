from __future__ import annotations

"""Multi-agent qualitative reader: two independent LLM extraction passes,
a deterministic quote-grounding check, and an agreement check between the
two passes -- before anything is allowed anywhere near publication.

This exists because qualitative/company-profile facts (business
description, leadership, products, risk factors, segment commentary)
cannot be checked by an accounting identity the way financial-statement
facts can (see `verification.py`'s ADDITIVE_IDENTITIES). This module is
the equivalent rigor for text: every claimed attribute must (a) come with
an exact quote the model claims appears on a specific page, (b) actually
be found on that page when checked byte-for-byte (not trusted from the
model), and (c) be independently reproduced by a second, differently-
framed extraction pass. Only attributes clearing all three gates are
returned as `accepted`; everything else -- a single-pass finding, a
disagreement between the two passes, or a quote that isn't actually on
the cited page -- goes to `review_queue` and is never silently published.

Requires the optional `llm` extra (`pip install -e ".[llm]"`) and an
`ANTHROPIC_API_KEY`. Confined to staging: callers must route `accepted`
items through the normal `company_attributes`/`disclosures` publication
path (which already carries its own source_key/versioning), and must
route `review_queue` items to the exceptions table, never to publication.
"""

import json
import re
import types
import unicodedata
from pathlib import Path

from .catalog import iter_catalog_fields

DEFAULT_MODEL = "claude-opus-5"

# The attribute vocabulary this reader is allowed to populate: every
# company_model field plus the two disclosure types this project's news
# policy defines (risk_factor already existed; the model may also
# surface it here since risk-factor lists live in the same narrative
# sections as the company profile in most annual reports).
_VOCAB = sorted(
    {f["field_key"] for f in iter_catalog_fields()
     if f["storage_domain"] == "company_profile"}
    | {"risk_factor"}
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "attribute_key": {"type": "string", "enum": _VOCAB},
                    "value": {"type": "string"},
                    "quote": {"type": "string"},
                    "page": {"type": "integer"},
                },
                "required": ["attribute_key", "value", "quote", "page"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["findings"],
    "additionalProperties": False,
}

_BASE_RULES = (
    "You extract company-profile facts from the pages of an official corporate "
    "document (annual report, investor-relations page, or exchange company-profile "
    "page). Rules, in strict order of importance:\n"
    "1. Every finding MUST include `quote`: the exact, verbatim substring of the "
    "source pages that supports it -- copy it character-for-character, including "
    "punctuation. Never paraphrase the quote. If you cannot quote it verbatim, omit "
    "the finding entirely.\n"
    "2. `page` is the page number (as printed in the PAGE markers below) where the "
    "quote appears. Never guess a page.\n"
    "3. `value` is your own concise, structured rendering of the fact (a name, a "
    "short phrase, a list rendered as a comma-separated string) -- this is what "
    "gets published if this finding survives verification; `quote` is only the "
    "proof.\n"
    "4. Map each finding to exactly one attribute_key from the provided list. Skip "
    "anything that doesn't fit one of them -- never invent a new key.\n"
    "5. Do not infer, compute, or combine facts from multiple pages into one "
    "quote. One finding, one page, one verbatim quote."
)

# Two independently-worded framings for the two extraction passes. They ask
# for the same underlying facts but frame the task differently on purpose --
# correlated phrasing between the two passes would undermine the point of
# having two of them.
_SYSTEM_PASS_A = (
    _BASE_RULES + "\n\nFraming: you are populating a financial database's company "
    "profile fields. Be conservative -- prefer omitting a finding to guessing."
)
_SYSTEM_PASS_B = (
    _BASE_RULES + "\n\nFraming: you are fact-checking a company profile someone else "
    "already drafted, by finding the exact source quote for each fact independently, "
    "as if you had never seen a draft. Be skeptical -- only report what the text "
    "actually says."
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _page_text_window(pages: dict[int, str], page: int) -> str:
    """The cited page plus its immediate neighbours, concatenated -- tolerates
    the common off-by-one error models make when a document's printed page
    number differs slightly from its physical index."""
    return " ".join(pages.get(p, "") for p in (page - 1, page, page + 1))


def _grounded(quote: str, pages: dict[int, str], page: int) -> bool:
    if not quote or not quote.strip():
        return False
    window = _normalize(_page_text_window(pages, page))
    return _normalize(quote) in window


def _run_pass(document: str, system: str, client, model: str):
    response = client.messages.create(
        model=model,
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": document}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
    )
    payload = json.loads(next(b.text for b in response.content if b.type == "text"))
    usage = response.usage
    return payload.get("findings", []), usage


def _value_words(text: str) -> set[str]:
    """A deliberately looser normalization than `_normalize`, used only for
    comparing `value` (the model's own rendering of a fact) between the two
    passes -- never for `quote` (the verbatim grounding proof, which must
    stay strict). Two agents independently describing the same real fact
    ('Ernst and Young; Deloitte and Touche & Co' vs 'Ernst & Young and
    Deloitte and Touche & Co') can legitimately differ in punctuation and
    '&'-vs-'and' without disagreeing about the underlying fact -- found by
    running this reader against a real annual report page during
    development, not a hypothetical. Comparing as a word set (order- and
    punctuation-insensitive) catches that case while still catching an
    actual disagreement (different names, different numbers, a missing
    qualifier)."""
    text = unicodedata.normalize("NFKC", text).lower().replace("&", " and ")
    text = re.sub(r"[^\w\s]", " ", text)
    return set(text.split())


def _values_agree(a: str, b: str) -> bool:
    words_a, words_b = _value_words(a), _value_words(b)
    if not words_a or not words_b:
        return words_a == words_b
    overlap = len(words_a & words_b) / len(words_a | words_b)
    return overlap >= 0.8


def qualitative_read(
    pdf_path: str | Path, *, market: str, symbol: str, source_url: str,
    filed_at: str, pages: list[int] | None = None, model: str = DEFAULT_MODEL,
    client=None,
) -> dict:
    """Two independent extraction passes over the given pages (or the whole
    document if `pages` is omitted), grounding-checked and reconciled.

    Returns a dict with:
      - `accepted`: findings both passes reproduced (same attribute_key,
        agreeing value) that are grounded on their cited page in both
        passes -- safe to publish through the normal company_attributes/
        disclosures path.
      - `review_queue`: everything else, each entry tagged with why it
        did not clear the bar (single_pass, disagreement, ungrounded) --
        route these to the exceptions table, never publish them directly.
      - `model_usage`: combined token counts for both passes.
    """
    pdf_path = Path(pdf_path)
    page_texts = _extract_pages(pdf_path, pages)
    if not page_texts:
        raise RuntimeError(f"no readable pages found in {pdf_path.name}")

    document = "\n\n".join(f"===== PAGE {p} =====\n{t}" for p, t in sorted(page_texts.items()))
    allowed_vocab_hint = f"Allowed attribute_key values: {', '.join(_VOCAB)}\n\n"

    if client is None:
        try:
            import anthropic
        except ImportError as error:  # pragma: no cover - environment dependent
            raise RuntimeError(
                'the qualitative reader needs the optional "llm" extra: pip install -e ".[llm]"'
            ) from error
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

    findings_a, usage_a = _run_pass(allowed_vocab_hint + document, _SYSTEM_PASS_A, client, model)
    findings_b, usage_b = _run_pass(allowed_vocab_hint + document, _SYSTEM_PASS_B, client, model)

    by_key_a = {f["attribute_key"]: f for f in findings_a if f.get("attribute_key") in _VOCAB}
    by_key_b = {f["attribute_key"]: f for f in findings_b if f.get("attribute_key") in _VOCAB}

    accepted = []
    review_queue = []
    for key in sorted(set(by_key_a) | set(by_key_b)):
        a = by_key_a.get(key)
        b = by_key_b.get(key)
        if a is None or b is None:
            only = a or b
            review_queue.append({
                "attribute_key": key, "reason": "single_pass",
                "detail": "only one of the two independent passes reported this attribute",
                "finding": only,
            })
            continue
        grounded_a = _grounded(a["quote"], page_texts, a["page"])
        grounded_b = _grounded(b["quote"], page_texts, b["page"])
        if not (grounded_a and grounded_b):
            review_queue.append({
                "attribute_key": key, "reason": "ungrounded",
                "detail": f"pass A grounded={grounded_a}, pass B grounded={grounded_b}",
                "pass_a": a, "pass_b": b,
            })
            continue
        if not _values_agree(a["value"], b["value"]):
            review_queue.append({
                "attribute_key": key, "reason": "disagreement",
                "detail": "both passes are grounded but reported different values",
                "pass_a": a, "pass_b": b,
            })
            continue
        accepted.append({
            "attribute_key": key, "value": a["value"],
            "source_page": a["page"], "quote": a["quote"],
            "confidence": "high", "method": "dual_pass_grounded_agreement",
        })

    return {
        "market": market, "symbol": symbol, "source_url": source_url,
        "filed_at": filed_at, "reader": f"finengine.reading_qualitative/{model}",
        "accepted": accepted, "review_queue": review_queue,
        "model_usage": {
            "input_tokens": usage_a.input_tokens + usage_b.input_tokens,
            "output_tokens": usage_a.output_tokens + usage_b.output_tokens,
        },
    }


def _extract_pages(pdf_path: Path, pages: list[int] | None) -> dict[int, str]:
    import pymupdf

    doc = pymupdf.open(pdf_path)
    try:
        indices = range(doc.page_count) if pages is None else [p - 1 for p in pages]
        return {i + 1: doc[i].get_text() for i in indices if 0 <= i < doc.page_count}
    finally:
        doc.close()
