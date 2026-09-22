from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .database import Database
from .domains import CompanyDomainStore


DEFAULT_CONTRACT = Path("config/factory/18-category-contract.json")
DEFAULT_SECTOR_PACKS = Path("config/factory/sector-packs")


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sector_pack(industry: str, directory: str | Path) -> tuple[str | None, dict | None]:
    for path in sorted(Path(directory).glob("*.json")):
        pack = _load_json(path)
        if industry in pack.get("canonical_industry_values", []):
            return path.stem, pack
    return None, None


def _provenance_score(db: Database, company_id: str) -> tuple[Decimal, dict]:
    row = db.conn.execute(
        """SELECT count(*) AS total,
        sum(CASE WHEN source_url<>'' AND filed_at<>'' AND content_hash<>''
            AND created_at<>'' THEN 1 ELSE 0 END) AS valid
        FROM source_documents WHERE company_id=?""",
        (company_id,),
    ).fetchone()
    total = int(row["total"] or 0)
    valid = int(row["valid"] or 0)
    # Page/table lineage lives on extracted facts, not source_documents.  Until
    # every published fact has a durable link to that location, the strict
    # five-field provenance contract cannot be certified as complete.
    located = db.conn.execute(
        """SELECT count(*) FROM extracted_facts
        WHERE company_id=? AND (page IS NOT NULL OR table_ref IS NOT NULL)""",
        (company_id,),
    ).fetchone()[0]
    score = Decimal(valid) / Decimal(total) if total else Decimal(0)
    if located == 0:
        score = Decimal(0)
    return score, {
        "source_documents": total,
        "documents_with_url_hash_filing_and_retrieval_time": valid,
        "facts_with_page_or_table_reference": located,
        "strict_five_field_provenance_certified": bool(total and valid == total and located),
    }


def evaluate_factory_contract(
    db: Database,
    company_id: str,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
    sector_pack_dir: str | Path = DEFAULT_SECTOR_PACKS,
) -> dict:
    """Evaluate the declarative factory contract without claiming unevaluated gates pass.

    This is intentionally separate from the legacy investor-understanding score.
    The two taxonomies answer different questions and must never be blended into
    one percentage.  Catalog coverage supplies the category numerators; sector
    packs narrow sector-specific groups and provide evidence-backed N/A rules.
    """
    company = db.conn.execute(
        "SELECT * FROM companies WHERE company_id=?", (company_id,)
    ).fetchone()
    if not company:
        raise KeyError(company_id)

    contract = _load_json(contract_path)
    completeness = CompanyDomainStore(db).refresh_catalog_completeness(company_id)
    groups = {row["category"]: row for row in completeness["categories"]}
    pack_key, pack = _sector_pack(company["industry"] or "", sector_pack_dir)
    not_applicable = set(
        (pack or {}).get("category_overrides", {}).get("not_applicable_categories", [])
    )
    activations = (pack or {}).get("activates", {})

    categories = []
    total_score = Decimal(0)
    all_thresholds_pass = True
    all_gates_evaluated = True
    blocking_reasons: list[str] = []

    for category in contract["categories"]:
        key = category["category_key"]
        weight = Decimal(str(category["weight"]))
        threshold = Decimal(str(category["completeness_threshold"]))
        field_groups = list(category["field_groups"])
        if key == "operational_kpis" and pack:
            field_groups = list(activations.get("operational_kpis_field_groups", []))
        elif key == "sector_specific_fields" and pack:
            field_groups = list(activations.get("sector_specific_fields_field_groups", []))

        evidence: dict = {"field_groups": field_groups, "sector_pack": pack_key}
        if key in not_applicable:
            score = Decimal(1)
            status = "not_applicable"
            threshold_passed = True
            evidence["not_applicable"] = {
                "reason": "sector_pack_rule",
                "pack": pack_key,
                "rule": "category_overrides.not_applicable_categories",
            }
        elif key == "sources_lineage_freshness":
            score, provenance = _provenance_score(db, company_id)
            evidence.update(provenance)
            threshold_passed = score >= threshold
            status = "complete" if threshold_passed else ("partial" if score else "missing")
        else:
            selected = [groups[name] for name in field_groups if name in groups]
            expected = sum(int(row["expected"]) for row in selected)
            populated = sum(int(row["populated"]) for row in selected)
            required = sum(int(row["required"]) for row in selected)
            populated_required = sum(int(row["populated_required"]) for row in selected)
            score = Decimal(populated) / Decimal(expected) if expected else Decimal(0)
            threshold_passed = score >= threshold
            status = "complete" if threshold_passed else ("partial" if populated else "missing")
            evidence.update({
                "expected_fields": expected,
                "populated_fields": populated,
                "required_fields": required,
                "populated_required_fields": populated_required,
                "missing_field_groups": [name for name in field_groups if name not in groups],
                "missing_fields": {
                    row["category"]: row["missing"] for row in selected if row["missing"]
                },
            })

        weighted_score = score * weight
        total_score += weighted_score
        if not threshold_passed:
            all_thresholds_pass = False
            blocking_reasons.append(f"category_threshold:{key}")

        hard_gates = []
        for index, gate in enumerate(category["hard_gates"], start=1):
            # The contract currently describes gates in prose.  A gate is not
            # silently passed until a named deterministic evaluator exists.
            hard_gates.append({
                "gate_id": f"{key}:{index}",
                "status": "not_evaluated",
                "condition": gate["condition"],
                "action": gate["action"],
            })
            all_gates_evaluated = False
        if hard_gates:
            blocking_reasons.append(f"hard_gate_evaluator_required:{key}")

        categories.append({
            "category_key": key,
            "weight": str(weight),
            "threshold": str(threshold),
            "score": str(score),
            "weighted_score": str(weighted_score),
            "status": status,
            "threshold_passed": threshold_passed,
            "hard_gates": hard_gates,
            "evidence": evidence,
        })

    target = Decimal(str(contract["overall_completeness_threshold"])) * Decimal(100)
    weighted_passed = total_score >= target
    ready = weighted_passed and all_thresholds_pass and all_gates_evaluated
    if not weighted_passed:
        blocking_reasons.insert(0, "weighted_coverage_95")
    return {
        "company_id": company_id,
        "contract_version": contract["contract_version"],
        "scoring_model": "factory_18_category_contract",
        "legacy_understanding_score_included": False,
        "sector_pack": pack_key,
        "total_score": str(total_score),
        "target_score": str(target),
        "coverage_thresholds_passed": weighted_passed and all_thresholds_pass,
        "all_hard_gates_evaluated": all_gates_evaluated,
        "readiness_state": "ready" if ready else "not_ready",
        "blocking_reasons": list(dict.fromkeys(blocking_reasons)),
        "categories": categories,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
