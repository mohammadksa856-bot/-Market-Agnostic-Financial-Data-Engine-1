from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlparse


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

READINESS_TARGET = Decimal("95")
CATEGORY_TARGET = Decimal("0.95")
SOURCE_MAP_VERSION = "18-categories-v1"

# This is the executable acquisition plan behind the 18-category model.  It is
# deliberately phrased as work the factory can perform, rather than a prose
# description of an ideal database.  Every incomplete category is mirrored to
# the durable backlog with this action and the governed sources from RULES.
CATEGORY_ACQUISITION = {
    "identity": "Extract legal identity and reporting basis from audited statements; verify the listing against the exchange or SEC.",
    "business": "Read the operating-segment note and issuer annual report for products, geography, subsidiaries and business economics.",
    "governance": "Extract board, committees, remuneration and related parties from the board report; monitor official appointment disclosures.",
    "ownership": "Capture major holders, foreign ownership and free float from the official exchange company profile and version every observation.",
    "financials": "Backfill audited annual statements and interim periods, preserving restatements, quarter/YTD/TTM semantics and page provenance.",
    "earnings_quality": "Extract audit opinion, key audit matters, going-concern language, one-offs and impairments; calculate cash conversion.",
    "ratios": "Calculate the applicable corporate, bank, insurer or loss-making-company ratio pack from primary facts with declared formulas.",
    "operations": "Extract sector-specific operating KPIs from annual reports, presentations and data supplements with units and dimensions.",
    "dividends_actions": "Backfill official dividend and corporate-action disclosures, then calculate payout, yield and continuity metrics.",
    "industry": "Ingest official regulator/statistics series and retain issuer management commentary as supporting context only.",
    "competitors": "Build peer sets from reviewed classifications and calculate period-safe comparisons from the engine's own sourced facts.",
    "trading": "Archive official daily prices, volume and turnover; calculate 52-week ranges, returns, volatility and beta internally.",
    "forecasts": "Extract issuer guidance from official presentations/disclosures and keep external estimates explicitly attributed.",
    "analysts": "Ingest only licensed or publicly attributable recommendations, targets and consensus with provider and as-of date.",
    "valuation": "Calculate relative valuation from current market data and TTM/FY facts; publish intrinsic values only with explicit assumptions.",
    "risks": "Extract disclosed risk factors, debt maturities, concentration, contingencies and rating opinions with source attribution.",
    "esg": "Extract issuer-reported environmental and social KPIs; keep third-party ESG ratings attributed and rights-controlled.",
    "news": "Continuously archive official disclosures and IR materials; attach named press coverage as secondary context.",
}


def _source_authorities(conn, company_id: str) -> set[str]:
    """Return only authorities supported by archived company evidence.

    Older manifests predate the explicit source_authority metadata field, so a
    conservative URL/filing classifier keeps their provenance usable without
    rewriting or pretending that a secondary source was primary.
    """
    result: set[str] = set()
    issuer_hosts = {
        (urlparse(row["url"]).hostname or "").lower()
        for row in conn.execute(
            "SELECT url FROM company_sources WHERE company_id=? AND enabled=1", (company_id,)
        )
    }
    issuer_hosts.discard("")
    for row in conn.execute(
        "SELECT source_url,filing_type,metadata_json FROM source_documents WHERE company_id=?",
        (company_id,),
    ):
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except (TypeError, ValueError):
            metadata = {}
        explicit = metadata.get("source_authority")
        if explicit in {item[0] for item in SOURCES}:
            result.add(explicit)
        url = (row["source_url"] or "").lower()
        filing = (row["filing_type"] or "").lower()
        if "sec.gov/" in url:
            result.add("sec_edgar")
        elif "saudiexchange.sa/" in url or "tadawul.com.sa/" in url:
            result.add("tadawul")
        elif ((urlparse(url).hostname or "").lower() in issuer_hosts):
            result.add("issuer_ir")
        if any(token in filing for token in (
            "audited", "financial statement", "annual financial", "10-k", "20-f",
        )):
            result.add("audited_statements")
        if metadata.get("outlet") or metadata.get("source_tier") == "secondary":
            result.add("attributed_press")
    calculated = conn.execute(
        "SELECT 1 FROM data_points WHERE company_id=? AND is_current=1 AND is_calculated=1 LIMIT 1",
        (company_id,),
    ).fetchone()
    if calculated:
        result.add("internal_calculation")
    estimates = conn.execute(
        "SELECT 1 FROM consensus_estimates WHERE company_id=? AND is_current=1 LIMIT 1",
        (company_id,),
    ).fetchone()
    if estimates:
        result.add("analyst_research")
    return result


def _source_plan(category_key: str, available: set[str]) -> list[dict]:
    authorities = {item[0]: item for item in SOURCES}
    plan = []
    for priority, (source_code, role) in enumerate(RULES[category_key], 1):
        source = authorities[source_code]
        plan.append({
            "priority": priority,
            "source_code": source_code,
            "source_name": source[1],
            "source_class": source[2],
            "source_role": role,
            "available": source_code in available,
            "rights_status": source[8],
        })
    return plan


def _sync_understanding_backlog(
    conn, company_id: str, category_key: str, score: Decimal,
    gaps: list[str], evidence: dict,
) -> None:
    key = f"understanding:{company_id}:{category_key}"
    if score >= CATEGORY_TARGET:
        conn.execute(
            """UPDATE backlog_items SET status='completed',completed_at=CURRENT_TIMESTAMP,
            updated_at=CURRENT_TIMESTAMP WHERE idempotency_key=?
            AND status NOT IN ('completed','cancelled')""", (key,),
        )
        return
    payload = json.dumps({
        "origin": "18_category_understanding_orchestrator",
        "source_map_version": SOURCE_MAP_VERSION,
        "category_key": category_key,
        "target_score": str(CATEGORY_TARGET),
        "current_score": str(score),
        "gaps": gaps,
        "acquisition_action": CATEGORY_ACQUISITION[category_key],
        "source_plan": evidence["source_plan"],
    }, ensure_ascii=False, separators=(",", ":"))
    backlog_id = "backlog:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    title = f"Reach 95% coverage for {category_key}"
    description = CATEGORY_ACQUISITION[category_key]
    priority = 15 if category_key in {"identity", "business", "financials", "risks"} else 40
    conn.execute(
        """INSERT INTO backlog_items(backlog_id,company_id,item_type,domain,title,description,
        priority,payload_json,idempotency_key) VALUES(?,?,?,?,?,?,?,?,?)
        ON CONFLICT(idempotency_key) DO UPDATE SET item_type=excluded.item_type,
        domain=excluded.domain,title=excluded.title,description=excluded.description,
        priority=excluded.priority,payload_json=excluded.payload_json,
        status=CASE WHEN backlog_items.status IN ('completed','cancelled') THEN 'open'
                    ELSE backlog_items.status END,
        completed_at=CASE WHEN backlog_items.status IN ('completed','cancelled') THEN NULL
                          ELSE backlog_items.completed_at END,
        updated_at=CURRENT_TIMESTAMP""",
        (backlog_id, company_id, "understanding_gap", category_key, title,
         description, priority, payload, key),
    )


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


def _evidence_adjusted_catalog_scores(conn, company_id: str, raw_scores: dict[str, Decimal]) -> tuple[dict[str, Decimal], dict[str, dict]]:
    """Use reviewed negative evidence without pretending a missing fact exists.

    The durable catalog audit is accepted only when its raw counters still
    match the current completeness row and every excluded field carries a
    recognized, explained availability state.  Stale or hand-edited payloads
    therefore cannot inflate readiness.
    """
    non_actionable = {
        "event_driven_no_event_observed", "not_applicable_market_identifier",
        "not_applicable_company_business_model",
        "not_disclosed_in_archived_annual_report",
        "not_disclosed_in_archived_filings", "qualitative_disclosure_only",
    }
    adjusted = dict(raw_scores)
    evidence: dict[str, dict] = {}
    rows = conn.execute(
        """SELECT b.domain,b.payload_json,c.expected_fields,c.populated_fields
        FROM backlog_items b JOIN company_completeness c
          ON c.company_id=b.company_id AND c.category=b.domain
        WHERE b.company_id=? AND b.item_type='catalog_backfill'
          AND b.status IN ('open','ready','in_progress','blocked')""",
        (company_id,),
    ).fetchall()
    for row in rows:
        try:
            payload = json.loads(row["payload_json"] or "{}")
            coverage = payload["coverage_interpretation"]
            assessments = payload["field_assessments"]
            verified = [item for item in assessments if item.get("availability") in non_actionable]
            valid = (
                int(coverage["raw_expected"]) == int(row["expected_fields"])
                and int(coverage["raw_populated"]) == int(row["populated_fields"])
                and int(coverage["verified_unavailable"]) == len(verified)
                and all(item.get("field_key") and item.get("reason") and item.get("resolution")
                        for item in verified)
            )
            if not valid:
                continue
            score = _ratio(coverage["actionable_score"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        adjusted[row["domain"]] = max(adjusted.get(row["domain"], Decimal(0)), score)
        evidence[row["domain"]] = {
            "raw_score": str(raw_scores.get(row["domain"], Decimal(0))),
            "actionable_score": str(score),
            "raw_expected": int(coverage["raw_expected"]),
            "raw_populated": int(coverage["raw_populated"]),
            "verified_unavailable": len(verified),
            "actionable_expected": int(coverage["actionable_expected"]),
            "methodology": "reviewed_field_level_applicability_and_negative_evidence",
        }
    return adjusted, evidence


def refresh_company_understanding(conn, company_id: str) -> dict:
    company = conn.execute("SELECT * FROM companies WHERE company_id=?", (company_id,)).fetchone()
    if not company:
        raise KeyError(f"unknown company {company_id}")
    completeness = {r["category"]: _ratio(r["completeness_score"]) for r in conn.execute(
        "SELECT category,completeness_score FROM company_completeness WHERE company_id=?", (company_id,)
    )}
    completeness, catalog_evidence = _evidence_adjusted_catalog_scores(
        conn, company_id, completeness,
    )

    def avg(*keys):
        values = [completeness[k] for k in keys if k in completeness]
        return sum(values, Decimal(0)) / len(values) if values else Decimal(0)

    def count(sql, args=()):
        return conn.execute(sql, args).fetchone()[0]

    attrs = count("SELECT count(*) FROM company_attributes WHERE company_id=? AND is_current=1", (company_id,))
    governance_attrs = count("SELECT count(*) FROM company_attributes WHERE company_id=? AND is_current=1 AND category='governance'", (company_id,))
    ownership = count("SELECT count(*) FROM ownership_positions WHERE company_id=? AND is_current=1", (company_id,))
    ownership_latest = conn.execute(
        "SELECT max(as_of_date) FROM ownership_positions WHERE company_id=? AND is_current=1",
        (company_id,),
    ).fetchone()[0]
    ownership_total = Decimal(0)
    ownership_types: set[str] = set()
    if ownership_latest:
        for row in conn.execute(
            """SELECT ownership_pct,holder_type,ownership_type FROM ownership_positions
            WHERE company_id=? AND as_of_date=? AND is_current=1""",
            (company_id, ownership_latest),
        ):
            if row["ownership_pct"] is not None:
                ownership_total += Decimal(row["ownership_pct"])
            ownership_types.update(filter(None, (row["holder_type"], row["ownership_type"])))
    ownership_reconciled = (
        ownership_latest is not None and abs(ownership_total - Decimal(1)) <= Decimal("0.001")
        and bool(ownership_types & {"government", "sovereign_and_strategic", "strategic",
                                    "corporate_strategic"})
        and bool(ownership_types & {"public", "free_float"})
    )
    actions = count("SELECT count(*) FROM corporate_actions WHERE company_id=? AND is_current=1", (company_id,))
    prices = count("""SELECT count(*) FROM market_prices p JOIN listings l USING(listing_id)
                    JOIN securities s USING(security_id) WHERE s.company_id=? AND p.is_current=1""", (company_id,))
    estimates = count("SELECT count(*) FROM consensus_estimates WHERE company_id=? AND is_current=1", (company_id,))
    disclosures = count("SELECT count(*) FROM disclosures WHERE company_id=? AND is_current=1", (company_id,))
    sources = count("SELECT count(*) FROM source_documents WHERE company_id=?", (company_id,))
    # A label alone is not enough to earn forward-looking coverage. Historical
    # manifests may contain dividend declarations or completed events under the
    # broad ``guidance`` label. Only explicitly reviewed forward-looking issuer
    # records contribute; analyst forecasts remain in consensus_estimates.
    guidance = count("""SELECT count(*) FROM disclosures WHERE company_id=?
        AND is_current=1 AND disclosure_type='guidance'
        AND json_extract(metadata_json,'$.forward_looking')=1
        AND COALESCE(json_extract(metadata_json,'$.analyst_forecast'),0)=0""", (company_id,))
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
        'regulatory_environment','competitive_environment','industry_size','industry_growth')""", (company_id,))
    classification_fields = int(bool(company["sector"])) + int(bool(company["industry"]))
    def classified_peer_count(scope_field: str, scope_value: str) -> int:
        if not scope_value:
            return 0
        return count(f"""SELECT count(DISTINCT c.company_id) FROM companies c
            WHERE c.company_id<>? AND c.enabled=1 AND c.{scope_field}=?
              AND EXISTS (SELECT 1 FROM data_points d JOIN metric_definitions m
                          ON m.metric_key=d.metric_key WHERE d.company_id=c.company_id
                          AND d.is_current=1 AND m.category IN ('ratio','calculated')
                          AND d.period_kind IN ('ttm','fy') AND d.scope='consolidated'
                          AND d.dimensions_json='{{}}' AND d.value_type='decimal'
                          AND d.value_decimal IS NOT NULL)""", (company_id, scope_value))

    peer_scope_field = "industry" if company["industry"] else "sector"
    peer_scope_value = company[peer_scope_field] or ""
    peer_count = classified_peer_count(peer_scope_field, peer_scope_value)
    peer_universe = count(
        f"SELECT count(*) FROM companies WHERE company_id<>? AND enabled=1 "
        f"AND {peer_scope_field}=?",
        (company_id, peer_scope_value),
    ) if peer_scope_value else 0
    peer_scope_fallback = None
    if peer_scope_field == "industry" and peer_count < 5 and company["sector"]:
        peer_scope_fallback = {
            "field": "industry", "value": peer_scope_value,
            "reason": (
                "no_other_peer_with_comparable_facts" if peer_count == 0
                else "fewer_than_five_peers_with_comparable_facts"
            ),
        }
        peer_scope_field = "sector"
        peer_scope_value = company["sector"]
        peer_count = classified_peer_count(peer_scope_field, peer_scope_value)
        peer_universe = count(
            "SELECT count(*) FROM companies WHERE company_id<>? AND enabled=1 AND sector=?",
            (company_id, peer_scope_value),
        )
    peer_metrics = count("""SELECT count(DISTINCT d.metric_key) FROM data_points d
        JOIN metric_definitions m ON m.metric_key=d.metric_key WHERE d.company_id=?
        AND d.is_current=1 AND m.category IN ('ratio','calculated')
        AND d.period_kind IN ('ttm','fy')""", (company_id,))
    available_authorities = _source_authorities(conn, company_id)

    scores = {
        "identity": _ratio(Decimal(identity_base + min(attrs, 8)) / Decimal(18)),
        "business": avg("company_model", "segments"),
        "governance": _ratio(Decimal(governance_attrs) / Decimal(10)),
        "ownership": Decimal(1) if ownership_reconciled else max(
            avg("ownership"), _ratio(Decimal(ownership) / Decimal(5))),
        "financials": avg("income_statement", "balance_sheet", "cash_flow"),
        "earnings_quality": avg("financial_notes") if not risk_items else max(avg("financial_notes"), Decimal("0.5")),
        "ratios": max(avg("profitability", "efficiency", "liquidity_solvency", "growth"), _ratio(Decimal(ratio_points) / Decimal(30))),
        "operations": max(avg("oil_gas_operations", "chemical_operations", "banking"), _ratio(Decimal(op_points) / Decimal(20))),
        "dividends_actions": max(avg("dividends", "corporate_actions"), _ratio(Decimal(actions) / Decimal(5))),
        "industry": _ratio(Decimal(classification_fields + industry_context) / Decimal(5)),
        # Some listed sectors genuinely contain fewer than five peers. Requiring
        # five made the 95% target mathematically unreachable even when every
        # available listed peer had comparable, sourced data.
        "competitors": min(_ratio(Decimal(peer_count) / Decimal(min(5, peer_universe)))
                           if peer_universe else Decimal(0),
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
        source_plan = _source_plan(key, available_authorities)
        evidence = {
            "attributes": attrs, "sources": sources, "disclosures": disclosures,
            "source_map_version": SOURCE_MAP_VERSION,
            "available_source_authorities": sorted(available_authorities),
            "source_plan": source_plan,
            "acquisition_action": CATEGORY_ACQUISITION[key],
        }
        relevant_catalog = {
            "business": ("company_model", "segments"),
            "financials": ("income_statement", "balance_sheet", "cash_flow"),
            "earnings_quality": ("financial_notes",),
            "valuation": ("valuation",),
        }.get(key, ())
        if relevant_catalog:
            evidence["catalog_coverage"] = {
                category: catalog_evidence[category]
                for category in relevant_catalog if category in catalog_evidence
            }
        if key == "ownership":
            evidence.update({
                "latest_snapshot_date": ownership_latest,
                "latest_snapshot_total": str(ownership_total),
                "latest_snapshot_reconciled": ownership_reconciled,
                "position_count": ownership,
            })
        if key == "industry":
            evidence.update({"classification_fields": classification_fields,
                             "industry_context_items": industry_context})
        elif key == "competitors":
            evidence.update({"inferred_peers_with_ratio_data": peer_count,
                             "classified_peer_universe": peer_universe,
                             "required_peer_count": min(5, peer_universe),
                             "comparable_metrics": peer_metrics,
                             "methodology": "internal_calculation",
                             "classification_basis":
                                 "inferred_peer_not_issuer_declared_competitor",
                             "peer_scope": {
                                 "field": peer_scope_field,
                                 "value": peer_scope_value,
                                 "classification_source": "reviewed_company_registry",
                                 **({"fallback_from": peer_scope_fallback}
                                    if peer_scope_fallback else {}),
                             }})
        gaps = []
        if status != "complete":
            gaps.append("category_coverage_below_95_percent")
            preferred = [item["source_code"] for item in source_plan
                         if item["source_role"] in {"record", "calculated", "opinion"}]
            if preferred and not any(source in available_authorities for source in preferred):
                gaps.append("missing_governed_source_evidence:" + ",".join(preferred))
            if key == "analysts" and estimates == 0:
                gaps.append("licensed_or_publicly_attributed_analyst_source_required")
        conn.execute(
            """INSERT INTO company_understanding_scores(company_id,category_key,score,weighted_score,status,
            evidence_json,gaps_json,checked_at) VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(company_id,category_key) DO UPDATE SET score=excluded.score,
            weighted_score=excluded.weighted_score,status=excluded.status,evidence_json=excluded.evidence_json,
            gaps_json=excluded.gaps_json,checked_at=excluded.checked_at""",
            (company_id, key, str(score), str(weighted), status, json.dumps(evidence), json.dumps(gaps), now),
        )
        _sync_understanding_backlog(conn, company_id, key, score, gaps, evidence)
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
        "weighted_coverage_95": {
            "passed": total >= READINESS_TARGET,
            "actual": str(total),
            "required": str(READINESS_TARGET),
        },
        "five_annual_periods": {"passed": annual_years >= 5, "actual": annual_years, "required": 5},
        "twelve_quarters_when_available": {"passed": quarter_periods >= 12, "actual": quarter_periods, "required": 12},
        "required_core_fields": {"passed": required[0] > 0 and required[0] == required[1], "actual": required[1], "required": required[0]},
        "no_critical_exceptions": {"passed": critical == 0, "actual": critical, "required": 0},
        "no_synthetic_sources": {"passed": synthetic == 0, "actual": synthetic, "required": 0},
        "source_provenance": {"passed": sources > 0, "actual": sources, "required": 1},
    }
    blockers = [key for key, value in gates.items() if not value["passed"]]
    state = "ready" if total >= READINESS_TARGET and not blockers else "awaiting_data" if not sources else "not_ready"
    conn.execute(
        """INSERT INTO company_readiness(company_id,total_score,readiness_state,hard_gates_json,
        blocking_reasons_json,checked_at) VALUES(?,?,?,?,?,?) ON CONFLICT(company_id) DO UPDATE SET
        total_score=excluded.total_score,readiness_state=excluded.readiness_state,
        hard_gates_json=excluded.hard_gates_json,blocking_reasons_json=excluded.blocking_reasons_json,
        checked_at=excluded.checked_at""",
        (company_id, str(total), state, json.dumps(gates), json.dumps(blockers), now),
    )
    conn.commit()
    return {"company_id": company_id, "target_score": str(READINESS_TARGET),
            "source_map_version": SOURCE_MAP_VERSION,
            "total_score": str(total), "readiness_state": state,
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
