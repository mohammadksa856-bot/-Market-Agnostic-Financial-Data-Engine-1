"""Review-only policy v2. No production call-site, database writes or contract edits.

Inputs are technical diagnostics, never independent financial verification.
Exclusion decisions must be explicitly reviewed and evidence-bound; a pack's
N/A string or empty catalog is not, by itself, structural evidence.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import json
from .factory_contract import DEFAULT_CONTRACT

VERSION = "applicable-weight-review/2.0.0"


def normalized_score(earned, denominator):
    return None if denominator == 0 else str(Decimal(100) * earned / denominator)


def apply_review_policy(measurement, decisions=None):
    decisions = decisions or {}
    result = deepcopy(measurement)
    reasons = []
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    normative = {c["category_key"]: c for c in contract["categories"]}
    keys = [r["category_key"] for r in result["categories"]]
    if set(keys) != set(normative) or len(keys) != len(normative):
        reasons.append("category_definition_mismatch")
    if Decimal(str(measurement["target_score"])) != Decimal(95):
        reasons.append("target_not_95")
    earned, denominator = Decimal(0), Decimal(0)
    thresholds_pass = True
    for row in result["categories"]:
        key = row["category_key"]
        weight = Decimal(row["weight"])
        original = normative.get(key)
        if not original or weight != Decimal(str(original["weight"])) or Decimal(row["threshold"]) != Decimal(str(original["completeness_threshold"])):
            reasons.append("contract_definition_mismatch:" + key)
        decision = decisions.get(key, {})
        structural = (decision.get("kind") == "structural_exclusion"
                      and decision.get("reviewed") is True
                      and bool(decision.get("evidence_reference"))
                      and len(decision.get("evidence_sha256", "")) == 64
                      and all(c in "0123456789abcdef" for c in decision.get("evidence_sha256", "")))
        if structural and original and original["applicability"]["rule"].startswith("universal"):
            reasons.append("forbidden_category_exclusion:" + key)
            structural = False
        row["original_score"] = row["score"]
        row["original_weighted_score"] = row["weighted_score"]
        if structural:
            row.update(score=None, weighted_score=None, policy_status="structural_exclusion", exclusion_evidence=deepcopy(decision))
            continue
        denominator += weight
        evidence = row.get("evidence", {})
        gap = (decision.get("kind") == "catalog_gap"
               or row["status"] == "not_applicable"
               or bool(evidence.get("missing_field_groups"))
               or (evidence.get("expected_fields") == 0 and key != "sources_lineage_freshness"))
        if gap:
            row.update(score=None, weighted_score=None, policy_status="not_measurable")
            reasons.append("measurement_definition_gap:" + key)
            thresholds_pass = False
            continue
        try:
            score = Decimal(row["score"])
            if not score.is_finite() or not Decimal(0) <= score <= Decimal(1):
                raise ValueError("invalid score")
        except (InvalidOperation, TypeError, ValueError):
            reasons.append("invalid_score:" + key)
            row.update(score=None, weighted_score=None, policy_status="not_measurable")
            thresholds_pass = False
            continue
        row.update(weighted_score=str(weight * score), policy_status="applicable")
        earned += weight * score
        thresholds_pass &= score >= Decimal(row["threshold"])
    if denominator == 0:
        reasons.append("no_applicable_denominator")
    score = None if reasons else normalized_score(earned, denominator)
    result.update(policy_version=VERSION, policy_state="LOCAL_REVIEW_NOT_ADOPTED",
                  previous_total_score=measurement["total_score"], total_score=score,
                  applicable_weight=str(denominator), applicable_earned_weight=str(earned),
                  policy_blocking_reasons=reasons, applicable_thresholds_passed=thresholds_pass,
                  coverage_thresholds_passed=(score is not None and Decimal(score) >= Decimal(95) and thresholds_pass),
                  readiness_state="not_assessed" if score is None else "not_ready",
                  production_approved=False, independently_verified=False)
    # Even a perfect candidate cannot certify readiness without all original gates
    # and period/independent-verification evidence. This module never grants ready.
    return result
