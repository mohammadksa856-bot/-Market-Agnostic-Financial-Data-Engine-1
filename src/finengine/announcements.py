"""Announcement attributes determined by a company's current disclosure records.

Each disclosure is an issuer announcement or filing section with a type, title, body, language, publication date,
related period and source document. The catalog's announcement fields are those properties; a field counts only
when at least one current record carries it. A flag counts only when some record's type (or reviewed event class)
places it in that class, so a flag is never inferred from the absence of a type.
"""
from __future__ import annotations

import json

FLAG_TYPES = {
    "earnings_flag": {"financial_results_announcement", "earnings_release", "interim_report", "annual_report"},
    "dividend_flag": {"dividend_announcement", "dividend_declaration", "dividend_distribution"},
    "contract_flag": {"contract_award", "material_contract", "commercial_contract"},
    "merger_acquisition_flag": {"merger", "acquisition", "divestment", "merger_acquisition"},
    "governance_flag": {"board_change", "management_change", "governance_update", "general_assembly",
                        "related_party_transaction"},
}
EVENT_CLASS_FLAGS = {"divestment": "merger_acquisition_flag", "acquisition": "merger_acquisition_flag",
                     "merger": "merger_acquisition_flag", "dividend": "dividend_flag", "contract": "contract_flag"}


def _metadata(row) -> dict:
    try:
        value = json.loads(row["metadata_json"] or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def announcement_fields(rows) -> set[str]:
    """`rows`: current disclosures joined with their source document's `source_url`."""
    fields: set[str] = set()
    for row in rows:
        metadata = _metadata(row)
        language = (row["language"] or "en").lower()
        checks = {
            "announcement_category": bool(row["disclosure_type"]),
            "announcement_date": bool(row["published_at"]),
            "announcement_body": bool((row["body_text"] or "").strip()),
            "announcement_title_en": language == "en" and bool((row["title"] or "").strip()),
            "announcement_title_ar": (language == "ar" and bool((row["title"] or "").strip()))
                                     or bool(str(metadata.get("title_ar") or "").strip()),
            "announcement_source_url": bool(row["source_url"]),
            "related_financial_period": bool(row["period_end"]),
            "announcement_id": bool(metadata.get("announcement_id")),
            "materiality_tag": bool(metadata.get("materiality")),
        }
        fields.update(key for key, present in checks.items() if present)
        fields.update(flag for flag, types in FLAG_TYPES.items() if row["disclosure_type"] in types)
        event_flag = EVENT_CLASS_FLAGS.get(str(metadata.get("event_class") or ""))
        if event_flag:
            fields.add(event_flag)
    return fields
