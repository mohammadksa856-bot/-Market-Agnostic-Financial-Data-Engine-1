"""Read-only feature-schema checks shared by the consumer and writer preflight.

This does not migrate or certify full DDL equivalence for deployment.
"""

# Versioned consumer vocabulary, checked against the declarative contract in tests.
CANONICAL_CATEGORY_KEYS_V1 = frozenset({
    "company_profile", "financial_statements", "profitability", "liquidity_solvency",
    "efficiency", "growth", "per_share", "valuation", "market_data", "dividends",
    "segments", "ownership", "corporate_actions", "announcements", "operational_kpis",
    "sector_specific_fields", "calculated_smart_metrics", "sources_lineage_freshness",
})

REQUIRED_COLUMNS = {
    "factory_company_readiness": {
        "company_id", "contract_version", "scoring_model", "sector_pack",
        "total_score", "target_score", "readiness_state",
        "coverage_thresholds_passed", "all_hard_gates_evaluated",
        "all_hard_gates_passed", "blocking_reasons_json", "checked_at",
    },
    "factory_category_scores": {
        "company_id", "category_key", "weight", "threshold", "score",
        "weighted_score", "status", "threshold_passed", "hard_gates_json",
        "evidence_json", "checked_at",
    },
}


def readiness_schema_gaps(conn) -> dict:
    gaps = {}
    for table, columns in REQUIRED_COLUMNS.items():
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,),
        ).fetchone()
        if not exists:
            gaps[table] = {"table_missing": True, "missing_columns": sorted(columns)}
            continue
        # Only fixed allowlisted identifiers are interpolated.
        actual = {row["name"] for row in conn.execute(f'PRAGMA table_info("{table}")')}
        if columns - actual:
            gaps[table] = {"table_missing": False, "missing_columns": sorted(columns - actual)}
    return gaps
