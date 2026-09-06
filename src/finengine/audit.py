from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def audit_release(db_path: str | Path, project_root: str | Path = ".") -> dict:
    """Run read-only release checks against the portable snapshot and its provenance."""
    root = Path(project_root).resolve()
    conn = sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    checks = []

    def add(name: str, status: str, detail):
        checks.append({"name": name, "status": status, "detail": detail})

    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    add("sqlite_integrity", "pass" if integrity == "ok" else "fail", integrity)
    foreign = conn.execute("PRAGMA foreign_key_check").fetchall()
    add("foreign_keys", "pass" if not foreign else "fail", len(foreign))
    duplicates = conn.execute(
        """SELECT count(*) FROM (SELECT 1 FROM data_points WHERE is_current=1 GROUP BY
        company_id,metric_key,period_end,period_kind,fiscal_year,fiscal_quarter,currency,unit,
        scope,dimensions_hash HAVING count(*)>1)"""
    ).fetchone()[0]
    add("current_fact_uniqueness", "pass" if duplicates == 0 else "fail", duplicates)
    open_exceptions = conn.execute(
        "SELECT count(*) FROM exceptions WHERE status='open' AND severity='error'"
    ).fetchone()[0]
    add("publication_exceptions", "pass" if open_exceptions == 0 else "fail", open_exceptions)
    dead_jobs = conn.execute("SELECT count(*) FROM jobs WHERE status='dead'").fetchone()[0]
    add("dead_jobs", "pass" if dead_jobs == 0 else "fail", dead_jobs)
    review_mappings = conn.execute(
        "SELECT count(*) FROM mapped_facts WHERE status='review'"
    ).fetchone()[0]
    add("mapping_review", "pass" if review_mappings == 0 else "fail", review_mappings)
    catalog_count = conn.execute("SELECT count(*) FROM data_catalog_fields WHERE enabled=1 AND review_state='reviewed'").fetchone()[0]
    add("commercial_catalog", "pass" if catalog_count >= 300 else "fail", catalog_count)
    current_versions = conn.execute(
        "SELECT count(*) FROM data_catalog_field_versions WHERE is_current=1"
    ).fetchone()[0]
    invalid_version_sets = conn.execute(
        """SELECT count(*) FROM (SELECT field_key FROM data_catalog_field_versions
        GROUP BY field_key HAVING sum(is_current)<>1)"""
    ).fetchone()[0]
    add("catalog_version_history", "pass" if current_versions == catalog_count and invalid_version_sets == 0 else "fail",
        {"current_versions": current_versions, "catalog_fields": catalog_count,
         "invalid_version_sets": invalid_version_sets})
    dimension_keys = {row["dimension_key"] for row in conn.execute(
        "SELECT dimension_key FROM dimension_definitions WHERE enabled=1"
    )}
    unknown_dimensions = set()
    for row in conn.execute("SELECT dimensions_json FROM data_points WHERE dimensions_json<>'{}'"):
        unknown_dimensions.update(set(json.loads(row["dimensions_json"])) - dimension_keys)
    add("governed_dimensions", "pass" if dimension_keys and not unknown_dimensions else "fail",
        {"registered": len(dimension_keys), "unknown": sorted(unknown_dimensions)})
    expected_contracts = conn.execute(
        """SELECT count(*) FROM data_catalog_fields WHERE enabled=1
        AND storage_domain IN ('data_points','consensus_estimates')"""
    ).fetchone()[0]
    contract_rows = conn.execute(
        "SELECT metric_key,allowed_period_kinds_json,allowed_dimensions_json FROM metric_contracts WHERE enabled=1"
    ).fetchall()
    contracts = {row["metric_key"]: (set(json.loads(row["allowed_period_kinds_json"])),
                                     set(json.loads(row["allowed_dimensions_json"]))) for row in contract_rows}
    contract_violations = []
    for row in conn.execute(
        """SELECT metric_key,period_kind,dimensions_json FROM data_points
        WHERE is_current=1 AND metric_key IN (SELECT metric_key FROM metric_contracts WHERE enabled=1)"""
    ):
        periods, dimensions = contracts[row["metric_key"]]
        actual_dimensions = set(json.loads(row["dimensions_json"]))
        if row["period_kind"] not in periods or not actual_dimensions.issubset(dimensions):
            contract_violations.append({"metric": row["metric_key"], "period_kind": row["period_kind"],
                                        "dimensions": sorted(actual_dimensions)})
    add("metric_contracts", "pass" if len(contracts) == expected_contracts and not contract_violations else "fail",
        {"contracts": len(contracts), "expected": expected_contracts,
         "violations": contract_violations[:20]})
    oil_gas_count = conn.execute("SELECT count(*) FROM data_catalog_fields WHERE enabled=1 AND pack_key='oil_gas_v2'").fetchone()[0]
    add("oil_gas_sector_pack", "pass" if oil_gas_count >= 40 else "fail", oil_gas_count)
    pack_minimums = {
        "company_core_v5": 500,
        "dividends_v1": 20,
        "announcements_v1": 20,
        "oil_gas_v2": 40,
        "chemicals_v1": 35,
        "banking_v1": 30,
        "insurance_v1": 20,
        "telecommunications_v1": 20,
        "utilities_v1": 20,
        "mining_v1": 20,
        "real_estate_v1": 20,
        "retail_v1": 20,
        "healthcare_v1": 20,
        "transportation_logistics_v1": 20,
        "industrial_construction_v1": 20,
        "technology_v1": 20,
        "food_agriculture_v1": 20,
        "asset_management_v1": 20,
    }
    pack_counts = {row["pack_key"]: row["n"] for row in conn.execute(
        "SELECT pack_key,count(*) n FROM data_catalog_fields WHERE enabled=1 GROUP BY pack_key"
    )}
    undersized = {key: {"actual": pack_counts.get(key, 0), "minimum": minimum}
                  for key, minimum in pack_minimums.items()
                  if pack_counts.get(key, 0) < minimum}
    sector_scope = {
        "oil_gas_v2": "Integrated Oil & Gas",
        "chemicals_v1": "Diversified Chemicals",
        "banking_v1": "Banks",
        "insurance_v1": "Insurance",
        "telecommunications_v1": "Telecommunications",
        "utilities_v1": "Utilities",
        "mining_v1": "Mining",
        "real_estate_v1": "Real Estate & REITs",
        "retail_v1": "Retail",
        "healthcare_v1": "Health Care",
        "transportation_logistics_v1": "Transportation & Logistics",
        "industrial_construction_v1": "Industrials & Construction",
        "technology_v1": "Technology",
        "food_agriculture_v1": "Food & Agriculture",
        "asset_management_v1": "Asset Management",
    }
    sector_pack_keys = tuple(sector_scope)
    placeholders = ",".join("?" for _ in sector_pack_keys)
    scope_violations = [dict(row) for row in conn.execute(
        f"""SELECT field_key,pack_key,scope_type,scope_value FROM data_catalog_fields
        WHERE enabled=1 AND pack_key IN ({placeholders})""", sector_pack_keys
    ) if row["scope_type"] != "industry" or row["scope_value"] != sector_scope[row["pack_key"]]]
    add("master_schema_packs", "pass" if not undersized and not scope_violations else "fail",
        {"counts": pack_counts, "undersized": undersized, "scope_violations": scope_violations[:20]})

    missing_files = []
    hash_mismatches = []
    for row in conn.execute("SELECT source_key,local_path,content_hash FROM source_documents"):
        if not row["local_path"]:
            missing_files.append(row["source_key"]); continue
        path = Path(row["local_path"])
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            missing_files.append(row["source_key"]); continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["content_hash"]:
            hash_mismatches.append(row["source_key"])
    add("source_archive_present", "pass" if not missing_files else "fail", missing_files)
    add("source_archive_hashes", "pass" if not hash_mismatches else "fail", hash_mismatches)

    missing_artifacts = []
    artifact_hash_mismatches = []
    for row in conn.execute("SELECT artifact_key,local_path,content_hash FROM source_artifacts"):
        path = Path(row["local_path"])
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            missing_artifacts.append(row["artifact_key"]); continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["content_hash"]:
            artifact_hash_mismatches.append(row["artifact_key"])
    add("raw_artifacts_present", "pass" if not missing_artifacts else "fail", missing_artifacts)
    add("raw_artifact_hashes", "pass" if not artifact_hash_mismatches else "fail", artifact_hash_mismatches)

    missing_universe = []
    universe_hash_mismatches = []
    for row in conn.execute("SELECT snapshot_id,local_path,content_hash FROM universe_snapshots"):
        if not row["local_path"]:
            missing_universe.append(row["snapshot_id"]); continue
        path = Path(row["local_path"])
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            missing_universe.append(row["snapshot_id"]); continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["content_hash"]:
            universe_hash_mismatches.append(row["snapshot_id"])
    add("universe_snapshots_present", "pass" if not missing_universe else "fail", missing_universe)
    add("universe_snapshot_hashes", "pass" if not universe_hash_mismatches else "fail",
        universe_hash_mismatches)

    missing_profiles = []
    profile_hash_mismatches = []
    for row in conn.execute(
        "SELECT issuer_id,local_path,content_hash FROM universe_issuer_profiles"
    ):
        path = Path(row["local_path"])
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            missing_profiles.append(row["issuer_id"]); continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["content_hash"]:
            profile_hash_mismatches.append(row["issuer_id"])
    add("universe_profiles_present", "pass" if not missing_profiles else "fail",
        missing_profiles)
    add("universe_profile_hashes", "pass" if not profile_hash_mismatches else "fail",
        profile_hash_mismatches)
    activation_violations = [dict(row) for row in conn.execute(
        """SELECT a.issuer_id,a.company_id,a.status,c.enabled,a.schedule_id
        FROM universe_activations a JOIN companies c USING(company_id)
        LEFT JOIN schedules s ON s.schedule_id=a.schedule_id
        WHERE (a.status='active' AND c.enabled<>1)
        OR (a.schedule_id IS NOT NULL AND s.schedule_id IS NULL)"""
    )]
    add("universe_activation_integrity", "pass" if not activation_violations else "fail",
        activation_violations)

    balances = defaultdict(dict)
    for row in conn.execute(
        """SELECT company_id,period_end,metric_key,value_decimal,currency,unit,scope,dimensions_hash
        FROM data_points
        WHERE is_current=1 AND period_kind='instant'
        AND metric_key IN ('total_assets','total_liabilities','total_equity')"""
    ):
        identity = (
            row["company_id"], row["period_end"], row["currency"], row["unit"],
            row["scope"], row["dimensions_hash"],
        )
        balances[identity][row["metric_key"]] = float(row["value_decimal"])
    unbalanced=[]
    for key, values in balances.items():
        if len(values) == 3:
            delta=abs(values["total_assets"]-values["total_liabilities"]-values["total_equity"])
            if delta > max(abs(values["total_assets"])*0.005, 1):
                unbalanced.append({
                    "company_id": key[0], "period_end": key[1], "currency": key[2],
                    "unit": key[3], "scope": key[4], "dimensions_hash": key[5],
                    "delta": delta,
                })
    add("balance_sheet_equation", "pass" if not unbalanced else "fail", unbalanced)

    companies=[]
    for row in conn.execute(
        """SELECT c.company_id,c.market,c.symbol,c.name,count(d.id) current_facts
        FROM companies c LEFT JOIN data_points d ON d.company_id=c.company_id AND d.is_current=1
        WHERE c.enabled=1 GROUP BY c.company_id ORDER BY c.market,c.symbol"""
    ):
        companies.append(dict(row))
    empty=[item["company_id"] for item in companies if item["current_facts"] == 0]
    add("enabled_company_coverage", "pass" if not empty else "warn", empty)
    status_counts={row["status"]: row["n"] for row in conn.execute(
        "SELECT status,count(*) n FROM source_documents GROUP BY status"
    )}
    unpublished=sum(count for status,count in status_counts.items() if status != "published")
    add("source_processing", "pass" if unpublished == 0 else "warn", status_counts)
    schema = conn.execute("SELECT max(version) FROM schema_migrations").fetchone()[0]
    facts = conn.execute("SELECT count(*) FROM data_points WHERE is_current=1").fetchone()[0]
    sources = conn.execute("SELECT count(*) FROM source_documents").fetchone()[0]
    artifacts = conn.execute("SELECT count(*) FROM source_artifacts").fetchone()[0]
    conn.close()
    failures=[check for check in checks if check["status"] == "fail"]
    warnings=[check for check in checks if check["status"] == "warn"]
    return {
        "ready": not failures, "schema_version": schema, "sources": sources,
        "raw_artifacts": artifacts,
        "current_facts": facts, "companies": companies, "checks": checks,
        "failures": len(failures), "warnings": len(warnings),
    }
