from __future__ import annotations

"""Keyword-based page selection for the qualitative reader.

`reading_qualitative.py` can run over an entire document, but doing that
for every company at scale is expensive and slow (an integrated annual
report can run 400+ pages) and, for a plain audited-financial-statements
PDF, mostly wasted on numeric tables the qualitative reader was never
meant to read. This module replaces the manual "read the PDF yourself
and pick page numbers" step (how the Al Rajhi pilot was built) with a
deterministic, auditable heuristic: score every page by how many
keywords from each target category it contains, then keep the
highest-scoring pages up to a page budget.

This is deliberately dumb and inspectable -- a keyword hit count, not a
model call -- because the page list it produces only decides what the
*next* stage (the actual dual-pass LLM extraction) gets to read. A
heuristic that misses a page only means that page's facts stay
undiscovered this round, same as before this module existed; it can
never cause a false fact to be published, because grounding and
agreement checking still happens downstream in `reading_qualitative.py`
against whatever pages were selected.
"""

import re
import unicodedata
from pathlib import Path

# Category -> keywords (English + Arabic where the document may be
# bilingual). Matched case-insensitively, substring, against normalized
# page text. Kept narrow and literal on purpose: widen this list only
# when a real miss is found, never loosen to a fuzzy match.
_KEYWORDS: dict[str, list[str]] = {
    "leadership": [
        "chief executive officer", "chairman", "board of directors",
        "managing director", "executive management", "the ceo",
        "الرئيس التنفيذي", "رئيس مجلس الإدارة", "مجلس الإدارة",
    ],
    "business_description": [
        "principal activities", "nature of activities", "nature of operations",
        "the group's activities", "the bank's activities", "the company's activities",
        "commercial registration", "licensed to", "business model",
        "طبيعة النشاط", "نشاط الشركة", "أنشطة الشركة",
    ],
    "subsidiaries": [
        "subsidiaries", "subsidiary companies", "ownership percentage",
        "consolidated subsidiaries", "list of subsidiaries",
        "الشركات التابعة",
    ],
    "segments": [
        "operating segments", "segment information", "reportable segments",
        "geographic segments", "القطاعات التشغيلية",
    ],
    "risk_factors": [
        "risk management", "principal risks", "key risks", "risk factors",
        "credit risk", "market risk", "liquidity risk", "going concern",
        "إدارة المخاطر", "المخاطر الرئيسية",
    ],
    "operational_kpis": [
        "branches", "atms", "point of sale", "pos terminals", "customers",
        "employees", "saudization", "digital channels", "mobile app",
        "market share", "الفروع", "أجهزة الصراف", "عدد الموظفين",
    ],
    "corporate_info": [
        "founded", "established", "incorporated", "headquartered",
        "head office", "commercial registration number", "auditor",
        "تأسست", "المقر الرئيسي", "المراجع",
    ],
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def score_pages(pages: dict[int, str]) -> dict[int, dict]:
    """Score every page against every category's keyword list.

    Returns {page_number: {"total": int, "categories": {category: hits}}},
    sorted by nothing in particular -- callers sort/select as needed.
    """
    scored = {}
    for page_num, text in pages.items():
        normalized = _normalize(text)
        categories = {}
        for category, keywords in _KEYWORDS.items():
            hits = sum(normalized.count(_normalize(kw)) for kw in keywords)
            if hits:
                categories[category] = hits
        if categories:
            scored[page_num] = {"total": sum(categories.values()), "categories": categories}
    return scored


def select_pages(
    pdf_path: str | Path, *, max_pages: int = 40, always_include_first: int = 3,
) -> dict:
    """Read every page of `pdf_path`, score it, and return the selected subset.

    Always includes the first `always_include_first` pages (an annual
    report's cover/overview/chairman's letter is rarely keyword-dense but
    often carries the company's own framing of who it is), plus the
    highest-scoring remaining pages up to `max_pages` total. Ties broken
    by page order (earlier page wins) for reproducibility.

    Returns {"selected_pages": [int, ...], "scores": {page: score_dict},
    "total_pages": int} -- `scores` is kept for the caller to log/inspect,
    not just the final list, so a reviewer can see *why* a page was or
    wasn't picked.
    """
    import pymupdf

    doc = pymupdf.open(pdf_path)
    try:
        all_pages = {i + 1: doc[i].get_text() for i in range(doc.page_count)}
    finally:
        doc.close()

    scored = score_pages(all_pages)
    forced = set(range(1, min(always_include_first, len(all_pages)) + 1))
    ranked = sorted(
        (p for p in scored if p not in forced),
        key=lambda p: (-scored[p]["total"], p),
    )
    remaining_budget = max(0, max_pages - len(forced))
    selected = sorted(forced | set(ranked[:remaining_budget]))

    return {
        "selected_pages": selected,
        "scores": scored,
        "total_pages": len(all_pages),
    }
