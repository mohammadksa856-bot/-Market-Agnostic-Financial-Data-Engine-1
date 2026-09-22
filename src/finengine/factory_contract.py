from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
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


def _deterministic_gates(
    db: Database, company_id: str, category_key: str, evidence: dict, *,
    category_not_applicable: bool,
) -> list[dict]:
    """Return gate results only where the current schema proves the condition."""
    if category_key == "company_profile":
        row = db.conn.execute(
            "SELECT completeness_score FROM company_completeness WHERE company_id=? AND category='company_model'",
            (company_id,),
        ).fetchone()
        actual = Decimal(row[0]) if row else Decimal(0)
        return [{"status": "passed" if actual >= Decimal("0.6") else "failed",
                 "actual": str(actual), "required": "0.6"}]

    if category_key == "financial_statements":
        annual = db.conn.execute(
            "SELECT count(DISTINCT fiscal_year) FROM data_points WHERE company_id=? AND is_current=1 AND period_kind='fy'",
            (company_id,),
        ).fetchone()[0]
        quarters = db.conn.execute(
            "SELECT count(DISTINCT period_end) FROM data_points WHERE company_id=? AND is_current=1 AND period_kind='quarter'",
            (company_id,),
        ).fetchone()[0]
        orphaned = db.conn.execute(
            """SELECT count(*) FROM data_points d LEFT JOIN source_documents s USING(source_key)
            WHERE d.company_id=? AND d.is_current=1 AND
            (s.source_key IS NULL OR s.source_url='' OR s.content_hash='')""",
            (company_id,),
        ).fetchone()[0]
        return [
            {"status": "passed" if annual >= 5 and quarters >= 12 else "failed",
             "annual_periods": annual, "quarter_periods": quarters,
             "required_annual_periods": 5, "required_quarter_periods": 12},
            {"status": "passed" if orphaned == 0 else "failed",
             "published_values_without_source_hash": orphaned, "required": 0},
        ]

    if category_key == "market_data":
        latest = db.conn.execute(
            """SELECT max(p.observed_at) FROM market_prices p JOIN listings l USING(listing_id)
            JOIN securities s USING(security_id) WHERE s.company_id=? AND p.is_current=1""",
            (company_id,),
        ).fetchone()[0]
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        observed = datetime.fromisoformat(latest.replace("Z", "+00:00")) if latest else None
        if observed and observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        return [{"status": "passed" if observed and observed >= cutoff else "failed",
                 "latest_market_observation": latest,
                 "maximum_calendar_age_days_for_five_trading_days": 7}]

    if category_key == "ownership":
        latest = db.conn.execute(
            "SELECT max(as_of_date) FROM ownership_positions WHERE company_id=? AND is_current=1",
            (company_id,),
        ).fetchone()[0]
        total = db.conn.execute(
            """SELECT COALESCE(sum(CAST(ownership_pct AS REAL)),0) FROM ownership_positions
            WHERE company_id=? AND is_current=1 AND as_of_date=?""",
            (company_id, latest or ""),
        ).fetchone()[0]
        passed = latest is not None and float(total) <= 1.0001
        return [{"status": "passed" if passed else "failed", "as_of_date": latest,
                 "ownership_percentage_sum": str(total), "maximum": "1.0001"}]

    if category_key == "corporate_actions":
        unlinked = db.conn.execute(
            """SELECT count(*) FROM corporate_actions a WHERE a.company_id=? AND a.is_current=1
            AND NOT EXISTS (SELECT 1 FROM disclosures d WHERE d.company_id=a.company_id
            AND d.is_current=1 AND d.source_key=a.source_key)""",
            (company_id,),
        ).fetchone()[0]
        return [{"status": "passed" if unlinked == 0 else "failed",
                 "actions_without_disclosure_source_link": unlinked, "required": 0}]

    if category_key == "announcements":
        latest = db.conn.execute(
            "SELECT max(published_at) FROM disclosures WHERE company_id=? AND is_current=1",
            (company_id,),
        ).fetchone()[0]
        cutoff = datetime.now(timezone.utc) - timedelta(days=180)
        published = datetime.fromisoformat(latest.replace("Z", "+00:00")) if latest else None
        if published and published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        return [{"status": "passed" if published and published >= cutoff else "failed",
                 "latest_announcement": latest, "maximum_age_days": 180}]

    if category_key == "operational_kpis":
        populated = int(evidence.get("populated_fields", 0))
        return [{"status": "passed" if populated > 0 else "failed",
                 "activated_groups": evidence.get("field_groups", []),
                 "populated_fields": populated, "required_minimum": 1}]

    if category_key == "sector_specific_fields" and category_not_applicable:
        return [{"status": "passed", "basis": evidence.get("not_applicable", {})}]

    if category_key == "sources_lineage_freshness":
        certified = bool(evidence.get("strict_five_field_provenance_certified"))
        return [{"status": "passed" if certified else "failed",
                 "strict_five_field_provenance_certified": certified}]

    return []


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
    all_gates_passed = True
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
        deterministic = _deterministic_gates(
            db, company_id, key, evidence, category_not_applicable=key in not_applicable
        )
        for index, gate in enumerate(category["hard_gates"], start=1):
            evaluated = deterministic[index - 1] if index <= len(deterministic) else {
                "status": "not_evaluated"
            }
            gate_result = {
                "gate_id": f"{key}:{index}",
                "condition": gate["condition"],
                "action": gate["action"],
                **evaluated,
            }
            hard_gates.append(gate_result)
            if gate_result["status"] == "not_evaluated":
                all_gates_evaluated = False
                blocking_reasons.append(f"hard_gate_evaluator_required:{key}")
            elif gate_result["status"] == "failed":
                all_gates_passed = False
                blocking_reasons.append(f"hard_gate_failed:{key}:{index}")

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
    ready = weighted_passed and all_thresholds_pass and all_gates_evaluated and all_gates_passed
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
        "all_hard_gates_passed": all_gates_passed,
        "readiness_state": "ready" if ready else "not_ready",
        "blocking_reasons": list(dict.fromkeys(blocking_reasons)),
        "categories": categories,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
