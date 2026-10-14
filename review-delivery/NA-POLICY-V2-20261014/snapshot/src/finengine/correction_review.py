"""Offline correction review only: never infer a replacement from a bad value."""
from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

from .normalization import per_share_contract_issues


def review_candidate(original: dict, evidence: dict, root: Path) -> dict:
    """Bind a manually reviewed page to one exact period and document vintage.

    Source verification is separate from selection/publication authority. Even a
    verified number cannot replace a current row until the vintage, descendants,
    rollback and explicit local-only application gates have been reviewed.
    """
    blockers = []
    for key in ("company_id", "metric", "period_end"):
        if evidence.get(key) != original.get(key):
            blockers.append("identity_mismatch:" + key)
    if evidence.get("period_kind") != original.get("period_kind"):
        blockers.append("identity_mismatch:period_kind")
    if evidence.get("fiscal_quarter", 0) != original.get("fiscal_quarter", 0):
        blockers.append("identity_mismatch:fiscal_quarter")
    blockers.extend(per_share_contract_issues(evidence.get("metric"), evidence.get("unit"),
                                             evidence.get("currency"), evidence.get("scale")))
    try:
        value = Decimal(str(evidence["value"]))
        if not value.is_finite():
            raise ValueError("nonfinite")
    except (KeyError, ValueError, ArithmeticError):
        blockers.append("explicit_finite_source_value_required")
    if not evidence.get("visual_reviewed") or not evidence.get("source_label"):
        blockers.append("independent_page_review_required")
    if not evidence.get("document_vintage") or not evidence.get("report_period_end"):
        blockers.append("document_vintage_required")
    if not isinstance(evidence.get("pdf_page"), int) or evidence.get("pdf_page", 0) < 1:
        blockers.append("one_based_pdf_page_required")
    for prefix in ("document", "page_image"):
        relative = evidence.get(prefix + "_path")
        path = (root / relative).resolve() if relative else None
        if not path or not path.is_relative_to(root.resolve()) or not path.is_file():
            blockers.append(prefix + "_artifact_missing_or_outside_root")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != evidence.get(prefix + "_sha256"):
            blockers.append(prefix + "_hash_mismatch")
    if evidence.get("interpretation") != "reported_numeric_cell":
        blockers.append("numeric_cell_not_directly_reported")
    return {"source_review": "VERIFIED_PAGE_VALUE" if not blockers else "BLOCKED",
            "blockers": sorted(set(blockers)), "candidate": evidence,
            "publication_authorized": False, "applied": False,
            "remaining_gates": ["official_disclosure_known_at", "vintage_selection_review",
                                "historical_version_retention", "dependent_outputs_inventory",
                                "verified_rollback", "local_TEST_and_independent_postcheck",
                                "explicit_production_approval_before_any_production_apply"]}
