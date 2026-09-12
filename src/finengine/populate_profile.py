from __future__ import annotations

"""The company-profile production line: ties `page_selection.py` and
`reading_qualitative.py` together into one call that goes from "a PDF on
disk" to "a manifest ready for the normal data/imports review flow",
without a human having to read the document first and hand-pick page
numbers -- which is how the original Al Rajhi pilot (data/imports/
alrajhi-company-profile-2025.json on claude/data-banking-profiles-1) was
built, and does not scale past one company.

This module only assembles what `reading_qualitative.py` already
verified (dual-pass, grounded, agreeing) into the same
`company_attributes`/`disclosures` shape every other manifest in this
project uses. It adds no new trust decision of its own: an attribute
lands in the manifest if and only if `qualitative_read` put it in
`accepted`; everything in `review_queue` is written to a sidecar file
instead, exactly as `read-profile`'s docstring already requires, and is
never silently dropped.
"""

import json
from pathlib import Path

from .page_selection import select_pages
from .reading_qualitative import qualitative_read

# Coarse grouping only, for readability in the manifest -- not load-
# bearing for anything downstream (publication keys off attribute_key,
# not category). Anything not listed here defaults to "general" rather
# than guessing a more specific bucket.
_CATEGORY_BY_KEY = {
    "company_name": "identity", "company_name_ar": "identity", "legal_name": "identity",
    "legal_name_ar": "identity", "symbol": "identity", "isin": "identity", "cik": "identity",
    "lei": "identity", "exchange": "identity", "market": "identity", "country": "identity",
    "currency": "identity", "listing_date": "identity", "sector": "identity",
    "industry": "identity", "sub_industry": "identity", "sharia_status": "identity",
    "website": "identity", "investor_relations_url": "identity",
    "founding_date": "identity", "incorporation_date": "identity", "legal_form": "identity",
    "headquarters_address": "identity",
    "ceo_name": "governance", "chairman_name": "governance",
    "executive_management_team": "governance", "board_of_directors": "governance",
    "auditor": "governance", "credit_rating": "governance",
    "reporting_standard": "governance", "reporting_languages": "governance",
    "employees": "workforce",
    "business_model": "business_model", "business_description": "business_model",
    "products_services": "business_model", "geographic_presence": "business_model",
    "subsidiaries_count": "business_model", "investor_contact_email": "business_model",
    "fiscal_year_end": "identity", "index_memberships": "identity",
}


def _category_for(attribute_key: str) -> str:
    return _CATEGORY_BY_KEY.get(attribute_key, "general")


def build_profile_manifest(
    pdf_path: str | Path, *, market: str, symbol: str, source_url: str, filed_at: str,
    company_id: str | None = None, period_end: str | None = None,
    filing_type: str = "Annual report / audited financial statements — automated profile extraction",
    max_pages: int = 40, model: str | None = None, client=None,
) -> dict:
    """Run the full auto pipeline for one company and return
    `{"manifest": {...}, "page_selection": {...}, "review_queue": [...],
    "model_usage": {...}}`.

    `manifest` is written straight into `data/imports/` if the caller is
    satisfied with it -- same shape as every hand-built profile manifest
    in this project. `review_queue` should go to a sidecar file next to
    it for a human to look at later, never merged into the manifest.
    """
    pdf_path = Path(pdf_path)
    selection = select_pages(pdf_path, max_pages=max_pages)
    kwargs = {"model": model} if model else {}
    result = qualitative_read(
        pdf_path, market=market, symbol=symbol, source_url=source_url,
        filed_at=filed_at, pages=selection["selected_pages"], client=client, **kwargs,
    )

    company_attributes = []
    disclosures = []
    for finding in result["accepted"]:
        key = finding["attribute_key"]
        if key == "risk_factor":
            value = finding["value"]
            disclosures.append({
                "disclosure_type": "risk_factor",
                "title": value if len(value) <= 80 else value[:77] + "...",
                "body_text": value,
                "published_at": filed_at,
                "period_end": period_end,
                "metadata": {"page": finding["source_page"], "method": finding["method"]},
            })
            continue
        company_attributes.append({
            "attribute_key": key, "value": finding["value"], "category": _category_for(key),
            "metadata": {"source_page": finding["source_page"], "method": finding["method"]},
        })

    manifest = {
        "company_id": company_id or f"{market.lower()}:{symbol.lower()}",
        "market": market, "symbol": symbol,
        "filing_type": filing_type, "filed_at": filed_at, "period_end": period_end,
        "source_url": source_url,
        "reader": f"finengine.populate_profile/{result['reader'].rsplit('/', 1)[-1]}",
        "profile": "corporate",
        "notes": (
            f"Auto-generated by the company-profile production line: "
            f"{selection['total_pages']} pages read, {len(selection['selected_pages'])} "
            f"selected by keyword scoring ({sorted(selection['selected_pages'])}), then "
            f"dual-pass extraction + grounding + agreement checking. "
            f"{len(company_attributes)} attributes and {len(disclosures)} disclosures "
            f"cleared all three gates; {len(result['review_queue'])} findings did not "
            f"and are in the sidecar review-queue file instead, not in this manifest."
        ),
        "company_attributes": company_attributes,
        "disclosures": disclosures,
    }

    return {
        "manifest": manifest,
        "page_selection": selection,
        "review_queue": result["review_queue"],
        "model_usage": result["model_usage"],
    }


def write_profile_batch(
    jobs: list[dict], *, out_dir: str | Path, model: str | None = None, client=None,
) -> list[dict]:
    """Run `build_profile_manifest` for each job dict (same kwargs as that
    function, plus an `"out_name"` stem for the two output files) and
    write `<out_dir>/<out_name>.json` (the manifest) and
    `<out_name>.review-queue.json` (everything that didn't clear the bar).

    Returns a summary list, one dict per job, with counts and any error
    -- a failure on one company (a corrupt PDF, an API error) is caught
    and recorded rather than aborting the whole batch, since the whole
    point of a batch is that one company's problem should not block the
    other 99.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for job in jobs:
        job = dict(job)
        out_name = job.pop("out_name")
        try:
            result = build_profile_manifest(**job, model=model, client=client)
        except Exception as error:  # noqa: BLE001 - recorded, not swallowed
            summaries.append({"out_name": out_name, "error": f"{type(error).__name__}: {error}"})
            continue
        manifest_path = out_dir / f"{out_name}.json"
        review_path = out_dir / f"{out_name}.review-queue.json"
        manifest_path.write_text(
            json.dumps(result["manifest"], indent=2, ensure_ascii=False), encoding="utf-8",
        )
        review_path.write_text(
            json.dumps(result["review_queue"], indent=2, ensure_ascii=False), encoding="utf-8",
        )
        summaries.append({
            "out_name": out_name,
            "attributes": len(result["manifest"]["company_attributes"]),
            "disclosures": len(result["manifest"]["disclosures"]),
            "review_queue": len(result["review_queue"]),
            "pages_selected": len(result["page_selection"]["selected_pages"]),
            "total_pages": result["page_selection"]["total_pages"],
            "model_usage": result["model_usage"],
        })
    return summaries
