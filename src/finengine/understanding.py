from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal


CATEGORIES = (
    ("identity", 1, "Identity", "هوية الشركة", 5, "Legal identity, listing and classification."),
    ("business", 2, "Business model", "نموذج العمل", 8, "Products, economics, segments and geography."),
    ("governance", 3, "Management and governance", "الإدارة والحوكمة", 4, "Management, board, committees and audit."),
    ("ownership", 4, "Ownership", "الملكية والمساهمون", 4, "Major holders, free float and ownership changes."),
    ("financials", 5, "Historical financials", "القوائم المالية التاريخية", 15, "Audited annual and interim statements."),
    ("earnings_quality", 6, "Earnings quality", "جودة الأرباح", 5, "Audit opinion, one-offs, restatements and cash conversion."),
    ("ratios", 7, "Financial ratios", "النسب المالية", 7, "Company-type-specific calculated ratios."),
    ("operations", 8, "Operational KPIs", "المؤشرات التشغيلية", 8, "Sector-specific operating drivers."),
    ("dividends_actions", 9, "Dividends and actions", "التوزيعات وإجراءات الشركة", 5, "Dividend history and corporate actions."),
    ("industry", 10, "Industry and sector", "القطاع والصناعة", 5, "Sector dynamics, regulation and aggregates."),
    ("competitors", 11, "Competitors", "المنافسون والحصة السوقية", 5, "Peers, market share and relative position."),
    ("trading", 12, "Trading and liquidity", "التداول والسيولة", 4, "Prices, liquidity and market risk."),
    ("forecasts", 13, "Guidance and forecasts", "التوجيهات والتوقعات", 5, "Issuer guidance and forward estimates."),
    ("analysts", 14, "Analyst coverage", "تغطية المحللين", 3, "Attributed ratings, targets and consensus."),
    ("valuation", 15, "Valuation", "التقييم", 5, "Relative and intrinsic valuation with declared methodology."),
    ("risks", 16, "Risks and exposures", "المخاطر والتعرضات", 7, "Disclosed risks, debt, concentration and contingencies."),
    ("esg", 17, "Sustainability", "الاستدامة", 3, "Environmental, social and governance indicators."),
    ("news", 18, "News and materials", "الأخبار ومواد المستثمرين", 2, "Official announcements, attributed press and IR materials."),
)

SOURCES = (
    ("audited_statements", "Audited financial statements", "P", "audited", 1, 1, 1, 0, "review_required", None, "Issuer filing, with auditor opinion and page-level provenance."),
    ("tadawul", "Saudi Exchange", "P", "regulatory_filing", 1, 1, 0, 0, "review_required", "connector_backoff", "Official exchange filing or market record."),
    ("issuer_ir", "Issuer investor relations", "P", "management_reported", 1, 1, 0, 0, "review_required", "robots_and_backoff", "Issuer annual reports, presentations, releases and guidance."),
    ("sec_edgar", "SEC EDGAR/XBRL", "P", "regulatory_filing", 1, 1, 1, 0, "cleared", "sec_fair_access", "Filed SEC facts and documents; archive raw source and accession."),
    ("official_regulator", "Official regulator/statistics authority", "P", "regulator_published", 1, 1, 0, 0, "review_required", "source_specific", "SAMA, GASTAT, Insurance Authority or equivalent official dataset."),
    ("internal_calculation", "FinEngine deterministic calculation", "C", "deterministic_calculation", 1, 1, 1, 0, "cleared", None, "Calculated from primary facts; formula, version and basis are mandatory."),
    ("analyst_research", "Attributed analyst research", "O", "external_opinion", 1, 0, 0, 0, "restricted", "license_specific", "Opinion or estimate; firm and as-of date must be displayed."),
    ("rating_agency", "Attributed rating agency", "O", "external_opinion", 1, 0, 0, 0, "restricted", "license_specific", "External opinion; agency, scale and date are mandatory."),
    ("attributed_press", "Named press source", "S", "attributed_secondary", 1, 1, 0, 0, "review_required", "feed_specific", "Secondary report, always attributed and never promoted to primary fact."),
)

RULES = {
    "identity": (("tadawul", "record"), ("sec_edgar", "record"), ("audited_statements", "supporting")),
    "business": (("issuer_ir", "record"), ("audited_statements", "record")),
    "governance": (("issuer_ir", "record"), ("tadawul", "record"), ("audited_statements", "supporting")),
    "ownership": (("tadawul", "record"), ("issuer_ir", "supporting")),
    "financials": (("audited_statements", "record"), ("tadawul", "supporting"), ("sec_edgar", "record")),
    "earnings_quality": (("audited_statements", "record"), ("internal_calculation", "calculated")),
    "ratios": (("internal_calculation", "calculated"),),
    "operations": (("issuer_ir", "record"), ("audited_statements", "supporting")),
    "dividends_actions": (("tadawul", "record"), ("internal_calculation", "calculated")),
    "industry": (("official_regulator", "record"), ("issuer_ir", "supporting")),
    "competitors": (("internal_calculation", "calculated"), ("issuer_ir", "supporting")),
    "trading": (("tadawul", "record"), ("internal_calculation", "calculated")),
    "forecasts": (("issuer_ir", "record"), ("tadawul", "record"), ("analyst_research", "opinion")),
    "analysts": (("analyst_research", "opinion"),),
    "valuation": (("internal_calculation", "calculated"),),
    "risks": (("audited_statements", "record"), ("issuer_ir", "record"), ("rating_agency", "opinion")),
    "esg": (("issuer_ir", "record"), ("rating_agency", "opinion")),
    "news": (("tadawul", "record"), ("issuer_ir", "record"), ("attributed_press", "supporting")),
}


def seed_understanding_governance(conn) -> None:
    conn.executemany(
        """INSERT INTO knowledge_categories(category_key,ordinal,name_en,name_ar,weight,description)
        VALUES(?,?,?,?,?,?) ON CONFLICT(category_key) DO UPDATE SET ordinal=excluded.ordinal,
        name_en=excluded.name_en,name_ar=excluded.name_ar,weight=excluded.weight,
        description=excluded.description,updated_at=CURRENT_TIMESTAMP""", CATEGORIES,
    )
    conn.executemany(
        """INSERT INTO source_authorities(source_code,name,source_class,assurance_level,
        internal_use_allowed,platform_display_allowed,api_redistribution_allowed,
        raw_redistribution_allowed,rights_status,rate_limit_policy,methodology)
        VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_code) DO UPDATE SET
        name=excluded.name,source_class=excluded.source_class,assurance_level=excluded.assurance_level,
        internal_use_allowed=excluded.internal_use_allowed,platform_display_allowed=excluded.platform_display_allowed,
        api_redistribution_allowed=excluded.api_redistribution_allowed,
        raw_redistribution_allowed=excluded.raw_redistribution_allowed,rights_status=excluded.rights_status,
        rate_limit_policy=excluded.rate_limit_policy,methodology=excluded.methodology,updated_at=CURRENT_TIMESTAMP""", SOURCES,
    )
    for category, rules in RULES.items():
        for priority, (source, role) in enumerate(rules, 1):
            conn.execute(
                """INSERT INTO category_source_rules(category_key,source_code,source_role,priority)
                VALUES(?,?,?,?) ON CONFLICT(category_key,source_code,source_role)
                DO UPDATE SET priority=excluded.priority""", (category, source, role, priority),
            )
    conn.commit()


def _ratio(value) -> Decimal:
    try:
        return max(Decimal(0), min(Decimal(1), Decimal(str(value))))
    except Exception:
        return Decimal(0)


def refresh_company_understanding(conn, company_id: str) -> dict:
    company = conn.execute("SELECT * FROM companies WHERE company_id=?", (company_id,)).fetchone()
    if not company:
        raise KeyError(f"unknown company {company_id}")
    completeness = {r["category"]: _ratio(r["completeness_score"]) for r in conn.execute(
        "SELECT category,completeness_score FROM company_completeness WHERE company_id=?", (company_id,)
    )}

    def avg(*keys):
        values = [completeness[k] for k in keys if k in completeness]
        return sum(values, Decimal(0)) / len(values) if values else Decimal(0)

    def count(sql, args=()):
        return conn.execute(sql, args).fetchone()[0]

    attrs = count("SELECT count(*) FROM company_attributes WHERE company_id=? AND is_current=1", (company_id,))
    governance_attrs = count("SELECT count(*) FROM company_attributes WHERE company_id=? AND is_current=1 AND category='governance'", (company_id,))
    ownership = count("SELECT count(*) FROM ownership_positions WHERE company_id=? AND is_current=1", (company_id,))
    actions = count("SELECT count(*) FROM corporate_actions WHERE company_id=? AND is_current=1", (company_id,))
    prices = count("""SELECT count(*) FROM market_prices p JOIN listings l USING(listing_id)
                    JOIN securities s USING(security_id) WHERE s.company_id=? AND p.is_current=1""", (company_id,))
    estimates = count("SELECT count(*) FROM consensus_estimates WHERE company_id=? AND is_current=1", (company_id,))
    disclosures = count("SELECT count(*) FROM disclosures WHERE company_id=? AND is_current=1", (company_id,))
    sources = count("SELECT count(*) FROM source_documents WHERE company_id=?", (company_id,))
    guidance = count("SELECT count(*) FROM disclosures WHERE company_id=? AND is_current=1 AND disclosure_type='guidance'", (company_id,))
    risk_items = count("""SELECT count(*) FROM disclosures WHERE company_id=? AND is_current=1
                        AND disclosure_type IN ('risk_factor','liquidity_risk','contingency','customer_concentration','restatement')""", (company_id,))
    op_points = count("""SELECT count(*) FROM data_points p JOIN metric_definitions m ON m.metric_key=p.metric_key
                       WHERE p.company_id=? AND p.is_current=1 AND m.category='operational'""", (company_id,))
    ratio_points = count("""SELECT count(*) FROM data_points p JOIN metric_definitions m ON m.metric_key=p.metric_key
                          WHERE p.company_id=? AND p.is_current=1 AND m.category IN ('ratio','calculated')""", (company_id,))
    esg_points = count("""SELECT count(*) FROM data_points WHERE company_id=? AND is_current=1 AND
        (metric_key LIKE '%emission%' OR metric_key LIKE '%water%' OR metric_key LIKE '%saudization%'
         OR metric_key LIKE '%injury%' OR metric_key LIKE '%sustainab%')""", (company_id,))
    identity_base = sum(bool(company[k]) for k in ("name", "symbol", "market", "currency", "fiscal_year_end", "exchange", "country", "sector", "industry", "isin"))
    industry_context = count("""SELECT count(*) FROM company_attributes WHERE company_id=?
        AND is_current=1 AND attribute_key IN ('industry_overview','industry_drivers',
        'regulatory_environment','industry_size','industry_growth')""", (company_id,))
    classification_fields = int(bool(company["sector"])) + int(bool(company["industry"]))
    peer_count = count("""SELECT count(DISTINCT c.company_id) FROM companies c
        WHERE c.company_id<>? AND c.enabled=1
          AND ((?<>'' AND c.industry=?) OR (?='' AND c.sector=?))
          AND EXISTS (SELECT 1 FROM data_points d JOIN metric_definitions m
                      ON m.metric_key=d.metric_key WHERE d.company_id=c.company_id
                      AND d.is_current=1 AND m.category IN ('ratio','calculated'))""",
        (company_id, company["industry"] or "", company["industry"] or "",
         company["industry"] or "", company["sector"] or ""))
    peer_metrics = count("""SELECT count(DISTINCT d.metric_key) FROM data_points d
        JOIN metric_definitions m ON m.metric_key=d.metric_key WHERE d.company_id=?
        AND d.is_current=1 AND m.category IN ('ratio','calculated')
        AND d.period_kind IN ('ttm','fy')""", (company_id,))

    scores = {
        "identity": _ratio(Decimal(identity_base + min(attrs, 8)) / Decimal(18)),
        "business": avg("company_model", "segments"),
        "governance": _ratio(Decimal(governance_attrs) / Decimal(10)),
        "ownership": max(avg("ownership"), _ratio(Decimal(ownership) / Decimal(5))),
        "financials": avg("income_statement", "balance_sheet", "cash_flow"),
        "earnings_quality": avg("financial_notes") if not risk_items else max(avg("financial_notes"), Decimal("0.5")),
        "ratios": max(avg("profitability", "efficiency", "liquidity_solvency", "growth"), _ratio(Decimal(ratio_points) / Decimal(30))),
        "operations": max(avg("oil_gas_operations", "chemical_operations", "banking"), _ratio(Decimal(op_points) / Decimal(20))),
        "dividends_actions": max(avg("dividends", "corporate_actions"), _ratio(Decimal(actions) / Decimal(5))),
        "industry": _ratio(Decimal(classification_fields + industry_context) / Decimal(5)),
        "competitors": min(_ratio(Decimal(peer_count) / Decimal(5)),
                           _ratio(Decimal(peer_metrics) / Decimal(8))),
        "trading": max(avg("market_data"), _ratio(Decimal(prices) / Decimal(252))),
        "forecasts": max(avg("consensus") * Decimal("0.5"), _ratio(Decimal(guidance + estimates) / Decimal(10))),
        "analysts": _ratio(Decimal(estimates) / Decimal(12)),
        "valuation": avg("valuation"),
        "risks": max(_ratio(Decimal(risk_items) / Decimal(8)), avg("financial_notes") * Decimal("0.5")),
        "esg": _ratio(Decimal(esg_points) / Decimal(8)),
        "news": _ratio(Decimal(disclosures + min(sources, 10)) / Decimal(20)),
    }
    now = datetime.now(timezone.utc).isoformat()
    categories = []
    total = Decimal(0)
    for key, ordinal, name_en, name_ar, weight, _ in CATEGORIES:
        score = scores[key]
        status = "complete" if score >= Decimal("0.95") else "partial" if score > 0 else "missing"
        weighted = score * Decimal(weight)
        total += weighted
        evidence = {"attributes": attrs, "sources": sources, "disclosures": disclosures}
        if key == "industry":
            evidence.update({"classification_fields": classification_fields,
                             "industry_context_items": industry_context})
        elif key == "competitors":
            evidence.update({"inferred_peers_with_ratio_data": peer_count,
                             "comparable_metrics": peer_metrics,
                             "methodology": "internal_calculation"})
        gaps = [] if status == "complete" else ["category coverage is below 95%"]
        conn.execute(
            """INSERT INTO company_understanding_scores(company_id,category_key,score,weighted_score,status,
            evidence_json,gaps_json,checked_at) VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(company_id,category_key) DO UPDATE SET score=excluded.score,
            weighted_score=excluded.weighted_score,status=excluded.status,evidence_json=excluded.evidence_json,
            gaps_json=excluded.gaps_json,checked_at=excluded.checked_at""",
            (company_id, key, str(score), str(weighted), status, json.dumps(evidence), json.dumps(gaps), now),
        )
        categories.append({"category_key": key, "ordinal": ordinal, "name_en": name_en,
                           "name_ar": name_ar, "weight": weight, "score": str(score),
                           "weighted_score": str(weighted), "status": status,
                           "evidence": evidence, "gaps": gaps})

    annual_years = count("SELECT count(DISTINCT fiscal_year) FROM data_points WHERE company_id=? AND is_current=1 AND period_kind='fy'", (company_id,))
    quarter_periods = count("SELECT count(DISTINCT period_end) FROM data_points WHERE company_id=? AND is_current=1 AND period_kind='quarter'", (company_id,))
    required = conn.execute("""SELECT COALESCE(sum(required_fields),0),COALESCE(sum(populated_required_fields),0)
                             FROM company_completeness WHERE company_id=?""", (company_id,)).fetchone()
    critical = count("SELECT count(*) FROM exceptions WHERE company_id=? AND status='open' AND severity IN ('critical','error')", (company_id,))
    synthetic = count("""SELECT count(*) FROM source_documents WHERE company_id=? AND
        (lower(metadata_json) LIKE '%synthetic%' OR lower(metadata_json) LIKE '%fixture%' OR lower(metadata_json) LIKE '%demo%')""", (company_id,))
    gates = {
        "five_annual_periods": {"passed": annual_years >= 5, "actual": annual_years, "required": 5},
        "twelve_quarters_when_available": {"passed": quarter_periods >= 12, "actual": quarter_periods, "required": 12},
        "required_core_fields": {"passed": required[0] > 0 and required[0] == required[1], "actual": required[1], "required": required[0]},
        "no_critical_exceptions": {"passed": critical == 0, "actual": critical, "required": 0},
        "no_synthetic_sources": {"passed": synthetic == 0, "actual": synthetic, "required": 0},
        "source_provenance": {"passed": sources > 0, "actual": sources, "required": 1},
    }
    blockers = [key for key, value in gates.items() if not value["passed"]]
    state = "ready" if total >= Decimal(95) and not blockers else "awaiting_data" if not sources else "not_ready"
    conn.execute(
        """INSERT INTO company_readiness(company_id,total_score,readiness_state,hard_gates_json,
        blocking_reasons_json,checked_at) VALUES(?,?,?,?,?,?) ON CONFLICT(company_id) DO UPDATE SET
        total_score=excluded.total_score,readiness_state=excluded.readiness_state,
        hard_gates_json=excluded.hard_gates_json,blocking_reasons_json=excluded.blocking_reasons_json,
        checked_at=excluded.checked_at""",
        (company_id, str(total), state, json.dumps(gates), json.dumps(blockers), now),
    )
    conn.commit()
    return {"company_id": company_id, "total_score": str(total), "readiness_state": state,
            "hard_gates": gates, "blocking_reasons": blockers, "categories": categories}


def refresh_all_understanding(conn, market: str | None = None) -> dict:
    filters = "WHERE enabled=1"
    args = ()
    if market:
        filters += " AND market=?"
        args = (market.upper(),)
    company_ids = [row[0] for row in conn.execute(
        f"SELECT company_id FROM companies {filters} ORDER BY market,symbol", args
    )]
    states: dict[str, int] = {}
    for company_id in company_ids:
        result = refresh_company_understanding(conn, company_id)
        state = result["readiness_state"]
        states[state] = states.get(state, 0) + 1
    return {"companies": len(company_ids), "states": states, "market": market.upper() if market else None}
