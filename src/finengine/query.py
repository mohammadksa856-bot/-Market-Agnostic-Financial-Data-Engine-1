from __future__ import annotations

import json
import sqlite3
from decimal import Decimal


class FinancialQueryService:
    """Read-only facade suitable for an API or Telegram bot."""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def _source_trace(self, source_key: str | None) -> dict | None:
        if not source_key:
            return None
        row = self.conn.execute(
            """SELECT s.source_key,s.source_url,s.filing_type,s.filed_at,s.content_hash,
            s.local_path AS manifest_path,a.artifact_key,a.local_path AS archived_path,
            a.content_hash AS artifact_sha256,a.content_type,a.byte_size
            FROM source_documents s LEFT JOIN source_artifact_links l USING(source_key)
            LEFT JOIN source_artifacts a USING(artifact_key) WHERE s.source_key=?
            ORDER BY a.archived_at DESC LIMIT 1""", (source_key,),
        ).fetchone()
        return dict(row) if row else None

    def _fact_trace(self, point_id: int) -> dict:
        point = self.conn.execute(
            "SELECT source_key,is_calculated,calculation,metric_key FROM data_points WHERE id=?", (point_id,),
        ).fetchone()
        if not point:
            return {}
        trace = {"source": self._source_trace(point["source_key"])}
        if point["is_calculated"]:
            trace["derivation"] = {
                "type": "deterministic_calculation",
                "calculation": point["calculation"],
                "definition": self.calculation_definition(point["metric_key"]),
            }
            return trace
        extracted = self.conn.execute(
            """SELECT e.raw_label,e.raw_value,e.raw_currency,e.raw_unit,e.scale,e.page,e.table_ref,
            e.location_json,m.confidence,m.mapping_method,m.reason
            FROM data_points d JOIN extracted_facts e ON e.source_key=d.source_key
             AND e.company_id=d.company_id AND e.period_end=d.period_end
             AND e.period_kind=d.period_kind AND e.fiscal_year=d.fiscal_year
             AND COALESCE(e.fiscal_quarter,0)=d.fiscal_quarter AND e.scope=d.scope
             AND e.dimensions_json=d.dimensions_json
            JOIN mapped_facts m ON m.extracted_fact_id=e.id AND m.canonical_metric=d.metric_key
            JOIN normalized_facts n ON n.mapped_fact_id=m.id AND n.normalized_value=d.value_decimal
             AND n.currency=d.currency AND n.unit=d.unit
            WHERE d.id=? ORDER BY e.id DESC LIMIT 1""", (point_id,),
        ).fetchone()
        if extracted:
            item = dict(extracted)
            item["location"] = json.loads(item.pop("location_json"))
            trace["extraction"] = item
        else:
            trace["extraction"] = None
        return trace

    def _point_with_trace(self, row: sqlite3.Row) -> dict:
        point_id = row["data_point_id"]
        item = self._point(row)
        item.pop("data_point_id", None)
        item["provenance"] = self._fact_trace(point_id)
        return item

    def _attach_source(self, item: dict) -> dict:
        source_key = item.get("source_key")
        item["provenance"] = {"source": self._source_trace(source_key)}
        return item

    @staticmethod
    def _point(row: sqlite3.Row) -> dict:
        item = dict(row)
        value_type = item.get("value_type", "decimal")
        if value_type in {"text", "date"}:
            item["value"] = item.get("value_text")
        elif value_type == "boolean":
            item["value"] = item.get("value_text") == "true"
        elif value_type == "json":
            item["value"] = json.loads(item.get("value_json") or "null")
        if "dimensions_json" in item:
            item["dimensions"] = json.loads(item.pop("dimensions_json"))
        if item.get("fiscal_quarter") == 0:
            item["fiscal_quarter"] = None
        return item

    def metric_history(self, market: str, symbol: str, metric: str, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(
            """SELECT d.id AS data_point_id,d.metric_key AS metric,d.value_decimal AS value,d.value_text,d.value_json,d.value_type,d.currency,d.unit,d.period_start,
            d.period_end,d.period_kind,d.fiscal_year,d.fiscal_quarter,d.scope,d.dimensions_json,
            d.version,d.source_key,d.source_url,d.is_calculated,d.calculation,d.quality_score,m.category,m.statement
            FROM data_points d JOIN companies c USING(company_id)
            JOIN metric_definitions m ON m.metric_key=d.metric_key
            WHERE c.market=? AND c.symbol=? AND d.metric_key=? AND d.is_current=1
            ORDER BY d.period_end DESC,d.period_kind LIMIT ?""",
            (market.upper(), symbol.upper(), metric, min(max(limit, 1), 500)),
        ).fetchall()
        return [self._point_with_trace(row) for row in rows]

    def facts(
        self, market: str, symbol: str, category: str | None = None,
        period_kind: str | None = None, limit: int = 500, offset: int = 0,
    ) -> list[dict]:
        filters = ["c.market=?", "c.symbol=?", "d.is_current=1"]
        args: list = [market.upper(), symbol.upper()]
        if category:
            filters.append("m.category=?"); args.append(category)
        if period_kind:
            filters.append("d.period_kind=?"); args.append(period_kind)
        args.extend([min(max(limit, 1), 2000), max(offset, 0)])
        rows = self.conn.execute(
            """SELECT d.id AS data_point_id,d.metric_key AS metric,m.display_name,m.category,m.statement,
            d.value_decimal AS value,d.value_text,d.value_json,d.value_type,d.currency,d.unit,
            d.period_start,d.period_end,d.period_kind,d.fiscal_year,d.fiscal_quarter,d.scope,
            d.dimensions_json,d.version,d.quality_score,d.source_key,d.source_url,d.filed_at,d.is_calculated,d.calculation
            FROM data_points d JOIN companies c USING(company_id)
            JOIN metric_definitions m ON m.metric_key=d.metric_key WHERE """ + " AND ".join(filters) +
            " ORDER BY d.period_end DESC,m.category,d.metric_key LIMIT ? OFFSET ?", args,
        ).fetchall()
        return [self._point_with_trace(row) for row in rows]

    def snapshot(self, market: str, symbol: str, period_end: str | None = None) -> dict:
        if period_end is None:
            row = self.conn.execute(
                """SELECT MAX(d.period_end) p FROM data_points d JOIN companies c USING(company_id)
                WHERE c.market=? AND c.symbol=? AND d.is_current=1""",
                (market.upper(), symbol.upper()),
            ).fetchone()
            period_end = row["p"]
        rows = self.conn.execute(
            """SELECT d.id AS data_point_id,d.metric_key AS metric,d.value_decimal AS value,d.value_text,d.value_json,d.value_type,d.currency,d.unit,d.period_kind,
            d.fiscal_quarter,d.scope,d.dimensions_json,d.version,d.quality_score,d.source_key,d.source_url,d.is_calculated,d.calculation,m.category
            FROM data_points d JOIN companies c USING(company_id)
            JOIN metric_definitions m ON m.metric_key=d.metric_key
            WHERE c.market=? AND c.symbol=? AND d.period_end=? AND d.is_current=1
            ORDER BY d.metric_key,d.period_kind,d.scope""",
            (market.upper(), symbol.upper(), period_end),
        ).fetchall()
        grouped: dict[str, list[dict]] = {}
        for row in rows:
            item = self._point_with_trace(row)
            grouped.setdefault(item.pop("metric"), []).append(item)
        return {"market": market.upper(), "symbol": symbol.upper(), "period_end": period_end, "metrics": grouped}

    def company_overview(self, market: str, symbol: str) -> dict:
        company = self.conn.execute(
            """SELECT company_id,market,symbol,name,currency,cik,isin,fiscal_year_end,exchange,country,
            sector,industry,timezone,locale FROM companies WHERE market=? AND symbol=?""",
            (market.upper(), symbol.upper()),
        ).fetchone()
        if not company:
            raise KeyError(f"unknown company {market}:{symbol}")
        counts = self.conn.execute(
            """SELECT m.category,count(*) AS facts FROM data_points d
            JOIN metric_definitions m ON m.metric_key=d.metric_key
            WHERE d.company_id=? AND d.is_current=1 GROUP BY m.category""",
            (company["company_id"],),
        ).fetchall()
        latest = self.conn.execute(
            "SELECT MAX(filed_at) AS latest_filing FROM source_documents WHERE company_id=?",
            (company["company_id"],),
        ).fetchone()
        result = dict(company)
        result["fact_counts"] = {row["category"]: row["facts"] for row in counts}
        result["latest_filing"] = latest["latest_filing"]
        result["listings"] = self.listings(market, symbol)
        result["completeness"] = self.completeness(market, symbol)
        return result

    def company_dossier(self, market: str, symbol: str) -> dict:
        """One read-only response containing everything known about a company."""
        overview = self.company_overview(market, symbol)
        facts = self.facts(market, symbol, limit=2000)
        categories: dict[str, list[dict]] = {}
        for fact in facts:
            categories.setdefault(fact["category"], []).append(fact)
        sources = self.conn.execute(
            """SELECT s.filing_type,s.filed_at,s.source_url,s.status,s.content_hash,
            a.artifact_key,a.local_path AS archived_path,a.content_hash AS artifact_hash,
            a.content_type AS artifact_content_type,a.byte_size AS artifact_bytes
            FROM source_documents s JOIN companies c USING(company_id)
            LEFT JOIN source_artifact_links l USING(source_key)
            LEFT JOIN source_artifacts a USING(artifact_key)
            WHERE c.market=? AND c.symbol=? ORDER BY s.filed_at DESC""",
            (market.upper(), symbol.upper()),
        ).fetchall()
        return {
            "overview": overview,
            "attributes": self.attributes(market, symbol),
            "market_prices": self.market_prices(market, symbol, limit=100),
            "ownership": self.ownership(market, symbol, limit=1000),
            "corporate_actions": self.corporate_actions(market, symbol, limit=1000),
            "consensus_estimates": self.consensus_estimates(market, symbol, limit=1000),
            "disclosures": self.disclosures(market, symbol, limit=200),
            "latest_snapshot": self.snapshot(market, symbol),
            "facts_by_category": categories,
            "coverage": self.coverage(market, symbol, limit=1000),
            "sources": [dict(row) for row in sources],
        }

    def listings(self, market: str, symbol: str) -> list[dict]:
        rows = self.conn.execute(
            """SELECT s.security_id,s.security_type,s.name AS security_name,s.isin,
            l.listing_id,l.market,l.exchange,l.symbol,l.currency,l.country,l.timezone,l.is_primary,l.active
            FROM listings l JOIN securities s USING(security_id)
            JOIN companies c ON c.company_id=s.company_id WHERE c.market=? AND c.symbol=?
            ORDER BY l.is_primary DESC,l.market,l.symbol""", (market.upper(), symbol.upper())).fetchall()
        return [dict(row) for row in rows]

    def market_prices(self, market: str, symbol: str, interval: str = "1d", limit: int = 100) -> list[dict]:
        rows = self.conn.execute(
            """SELECT p.observed_at,p.interval,p.open,p.high,p.low,p.close,p.adjusted_close,
            p.volume,p.turnover,p.currency,p.version,p.source_key,s.source_url
            FROM market_prices p JOIN listings l USING(listing_id) JOIN securities sec USING(security_id)
            JOIN companies c ON c.company_id=sec.company_id JOIN source_documents s USING(source_key)
            WHERE c.market=? AND c.symbol=? AND p.interval=? AND p.is_current=1
            ORDER BY p.observed_at DESC LIMIT ?""",
            (market.upper(), symbol.upper(), interval, min(max(limit, 1), 2000))).fetchall()
        return [self._attach_source(dict(row)) for row in rows]

    def ownership(self, market: str, symbol: str, as_of_date: str | None = None, limit: int = 100) -> list[dict]:
        filters = ["c.market=?", "c.symbol=?", "o.is_current=1"]
        args: list = [market.upper(), symbol.upper()]
        if as_of_date:
            filters.append("o.as_of_date=?"); args.append(as_of_date)
        args.append(min(max(limit, 1), 1000))
        rows = self.conn.execute(
            """SELECT o.holder_key,o.holder_name,o.holder_type,o.ownership_type,o.as_of_date,
            o.shares,o.ownership_pct,o.country,o.metadata_json,o.version,o.source_key,s.source_url
            FROM ownership_positions o JOIN companies c USING(company_id)
            JOIN source_documents s USING(source_key) WHERE """ + " AND ".join(filters) +
            " ORDER BY o.as_of_date DESC,o.ownership_pct DESC LIMIT ?", args).fetchall()
        result=[]
        for row in rows:
            item=dict(row); item["metadata"]=json.loads(item.pop("metadata_json")); result.append(self._attach_source(item))
        return result

    def consensus_estimates(
        self, market: str, symbol: str, metric: str | None = None,
        target_period_end: str | None = None, limit: int = 100,
    ) -> list[dict]:
        filters = ["c.market=?", "c.symbol=?", "e.is_current=1"]
        args: list = [market.upper(), symbol.upper()]
        if metric:
            filters.append("e.metric_key=?"); args.append(metric)
        if target_period_end:
            filters.append("e.target_period_end=?"); args.append(target_period_end)
        args.append(min(max(limit, 1), 2000))
        rows = self.conn.execute(
            """SELECT e.metric_key AS metric,e.target_period_end,e.period_kind,e.estimate_type,
            e.value_decimal AS value,e.currency,e.unit,e.analyst_count,e.estimate_as_of,
            e.metadata_json,e.version,e.source_key,s.source_url
            FROM consensus_estimates e JOIN companies c USING(company_id)
            JOIN source_documents s USING(source_key) WHERE """ + " AND ".join(filters) +
            " ORDER BY e.target_period_end,e.metric_key,e.estimate_type,e.estimate_as_of DESC LIMIT ?", args,
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row); item["metadata"] = json.loads(item.pop("metadata_json")); result.append(self._attach_source(item))
        return result

    def corporate_actions(self, market: str, symbol: str, action_type: str | None = None,
                          limit: int = 100) -> list[dict]:
        filters = ["c.market=?", "c.symbol=?", "a.is_current=1"]
        args: list = [market.upper(), symbol.upper()]
        if action_type:
            filters.append("a.action_type=?"); args.append(action_type)
        args.append(min(max(limit, 1), 1000))
        rows = self.conn.execute(
            """SELECT a.action_key,a.action_type,a.title,a.announcement_date,a.ex_date,a.record_date,
            a.eligibility_date,a.payment_date,a.effective_date,a.cash_amount,a.currency,
            a.ratio_numerator,a.ratio_denominator,a.status,a.details_json,a.version,a.source_key,s.source_url
            FROM corporate_actions a JOIN companies c USING(company_id)
            JOIN source_documents s USING(source_key) WHERE """ + " AND ".join(filters) +
            " ORDER BY a.announcement_date DESC LIMIT ?", args).fetchall()
        result=[]
        for row in rows:
            item=dict(row); item["details"]=json.loads(item.pop("details_json")); result.append(self._attach_source(item))
        return result

    def calculation_definition(self, metric: str) -> dict | None:
        row = self.conn.execute(
            """SELECT metric_key,formula_version,expression,output_unit,period_rule,description
            FROM calculation_definitions WHERE metric_key=? AND enabled=1 AND is_current=1""", (metric,)).fetchone()
        if not row:
            return None
        result=dict(row)
        dependencies=self.conn.execute(
            """SELECT dependency_metric,role FROM calculation_dependencies
            WHERE metric_key=? AND formula_version=? ORDER BY dependency_metric""",
            (metric,row["formula_version"])).fetchall()
        result["dependencies"]=[dict(item) for item in dependencies]
        return result

    def coverage(self, market: str, symbol: str, limit: int = 100) -> list[dict]:
        rows = self.conn.execute(
            """SELECT v.period_end,v.period_kind,v.domain,v.expected_count,v.available_count,
            v.required_missing_json,v.status,v.quality_score,v.latest_source_at,
            v.freshness_status,v.age_seconds,v.checked_at
            FROM coverage_status v JOIN companies c USING(company_id)
            WHERE c.market=? AND c.symbol=? ORDER BY v.period_end DESC,v.period_kind,v.domain LIMIT ?""",
            (market.upper(),symbol.upper(),min(max(limit,1),1000))).fetchall()
        result=[]
        for row in rows:
            item=dict(row); item["required_missing"]=json.loads(item.pop("required_missing_json")); result.append(item)
        return result

    def backlog(
        self, market: str | None = None, symbol: str | None = None,
        status: str = "active", limit: int = 500,
    ) -> list[dict]:
        filters = []
        args: list = []
        if market or symbol:
            if not market or not symbol:
                raise ValueError("market and symbol must be supplied together")
            filters.extend(["c.market=?", "c.symbol=?"])
            args.extend([market.upper(), symbol.upper()])
        if status == "active":
            filters.append("b.status IN ('open','ready','in_progress','blocked')")
        elif status != "all":
            filters.append("b.status=?")
            args.append(status)
        args.append(min(max(limit, 1), 5000))
        where = " WHERE " + " AND ".join(filters) if filters else ""
        rows = self.conn.execute(
            """SELECT b.backlog_id,c.market,c.symbol,c.name AS company,b.item_type,b.domain,
            b.title,b.description,b.period_end,b.period_kind,b.metric_key,b.source_url,b.priority,
            b.status,b.payload_json,b.job_id,b.created_at,b.updated_at,b.completed_at
            FROM backlog_items b LEFT JOIN companies c USING(company_id)""" + where +
            " ORDER BY CASE b.status WHEN 'in_progress' THEN 0 WHEN 'ready' THEN 1 WHEN 'open' THEN 2 ELSE 3 END,b.priority,b.created_at LIMIT ?",
            args,
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            result.append(item)
        return result

    def metric_catalog(self, category: str | None = None, limit: int = 1000) -> list[dict]:
        where="WHERE enabled=1"; args:list=[]
        if category:
            where+=" AND category=?"; args.append(category)
        args.append(min(max(limit,1),5000))
        rows=self.conn.execute(
            """SELECT metric_key,display_name,category,statement,value_type,default_unit,
            aggregation,description,schema_version FROM metric_definitions """+where+
            " ORDER BY category,metric_key LIMIT ?",args).fetchall()
        return [dict(row) for row in rows]

    def data_catalog(self, category: str | None = None, storage_domain: str | None = None,
                     limit: int = 1000) -> list[dict]:
        filters=["enabled=1"]; args=[]
        if category: filters.append("category=?"); args.append(category)
        if storage_domain: filters.append("storage_domain=?"); args.append(storage_domain)
        args.append(min(max(limit,1),5000))
        rows=self.conn.execute(
            """SELECT f.field_key,f.display_name,f.category,f.storage_domain,f.statement,f.period_behavior,
            f.value_type,f.default_unit,f.aggregation,f.pack_key,f.scope_type,f.scope_value,f.requirement,
            f.review_state,f.schema_version,c.allowed_period_kinds_json,c.allowed_dimensions_json,c.unit_family,
            c.contract_version FROM data_catalog_fields f LEFT JOIN metric_contracts c ON c.metric_key=f.field_key
            WHERE """+" AND ".join("f."+value if "=" in value and "." not in value else value for value in filters)+
            " ORDER BY pack_key,category,field_key LIMIT ?",args).fetchall()
        result=[]
        for row in rows:
            item=dict(row)
            item["allowed_period_kinds"]=json.loads(item.pop("allowed_period_kinds_json")) if item["allowed_period_kinds_json"] else []
            item["allowed_dimensions"]=json.loads(item.pop("allowed_dimensions_json")) if item["allowed_dimensions_json"] else []
            result.append(item)
        return result

    def catalog_history(self, field_key: str) -> list[dict]:
        rows = self.conn.execute(
            """SELECT field_key,definition_version,definition_hash,definition_json,valid_from,valid_to,is_current
            FROM data_catalog_field_versions WHERE field_key=? ORDER BY definition_version DESC""",
            (field_key,),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["definition"] = json.loads(item.pop("definition_json"))
            result.append(item)
        return result

    def dimensions(self) -> list[dict]:
        return [dict(row) for row in self.conn.execute(
            """SELECT dimension_key,display_name,description,value_type,schema_version
            FROM dimension_definitions WHERE enabled=1 ORDER BY dimension_key"""
        ).fetchall()]

    def completeness(self, market: str, symbol: str) -> dict:
        company=self.conn.execute(
            "SELECT company_id FROM companies WHERE market=? AND symbol=?",(market.upper(),symbol.upper())).fetchone()
        if not company: raise KeyError(f"unknown company {market}:{symbol}")
        rows=self.conn.execute(
            """SELECT category,expected_fields,populated_fields,required_fields,populated_required_fields,
            completeness_score,status,missing_fields_json,required_missing_json,checked_at
            FROM company_completeness WHERE company_id=? ORDER BY category""",
            (company["company_id"],)).fetchall()
        categories=[]
        for row in rows:
            item=dict(row)
            item["missing_fields"]=json.loads(item.pop("missing_fields_json"))
            item["required_missing"]=json.loads(item.pop("required_missing_json"))
            categories.append(item)
        expected=sum(item["expected_fields"] for item in categories)
        populated=sum(item["populated_fields"] for item in categories)
        required=sum(item["required_fields"] for item in categories)
        populated_required=sum(item["populated_required_fields"] for item in categories)
        return {"expected_fields":expected,"populated_fields":populated,
                "required_fields":required,"populated_required_fields":populated_required,
                "completeness_score":str(Decimal(populated)/Decimal(expected) if expected else Decimal(1)),
                "categories":categories}

    def disclosures(self, market: str, symbol: str, disclosure_type: str | None = None,
                    limit: int = 50) -> list[dict]:
        filters = ["c.market=?", "c.symbol=?", "d.is_current=1"]
        args: list = [market.upper(), symbol.upper()]
        if disclosure_type:
            filters.append("d.disclosure_type=?"); args.append(disclosure_type)
        args.append(min(max(limit, 1), 200))
        rows = self.conn.execute(
            """SELECT d.disclosure_type,d.title,d.body_text,d.language,d.published_at,d.period_end,
            d.metadata_json,d.version,d.source_key,s.source_url FROM disclosures d JOIN companies c USING(company_id)
            LEFT JOIN source_documents s ON s.source_key=d.source_key WHERE """ + " AND ".join(filters) +
            " ORDER BY d.published_at DESC LIMIT ?", args,
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row); item["metadata"] = json.loads(item.pop("metadata_json")); result.append(self._attach_source(item))
        return result

    def source_candidates(self, market: str, symbol: str, status: str | None = None,
                          limit: int = 100) -> list[dict]:
        filters = ["c.market=?", "c.symbol=?"]
        args: list = [market.upper(), symbol.upper()]
        if status:
            filters.append("s.status=?")
            args.append(status)
        args.append(min(max(limit, 1), 2000))
        rows = self.conn.execute(
            """SELECT s.id,s.connector,s.external_id,s.source_url,s.title,s.document_type,
            s.published_at,s.content_type,s.status,s.metadata_json,s.discovered_at,s.last_seen_at
            FROM source_candidates s JOIN companies c USING(company_id) WHERE """ +
            " AND ".join(filters) + " ORDER BY COALESCE(s.published_at,s.discovered_at) DESC LIMIT ?",
            args,
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json"))
            result.append(item)
        return result

    def exceptions(self, market: str | None = None, symbol: str | None = None,
                   status: str = "open", limit: int = 100) -> list[dict]:
        filters=[]; args=[]
        if market or symbol:
            if not market or not symbol:
                raise ValueError("market and symbol must be supplied together")
            filters.extend(["c.market=?", "c.symbol=?"])
            args.extend([market.upper(), symbol.upper()])
        if status != "all":
            filters.append("e.status=?"); args.append(status)
        args.append(min(max(limit,1),1000))
        where=" WHERE " + " AND ".join(filters) if filters else ""
        rows=self.conn.execute(
            """SELECT e.id,e.source_key,c.market,c.symbol,e.stage,e.code,e.message,e.payload_json,
            e.severity,e.status,e.assigned_to,e.resolution,e.retry_count,e.created_at,e.updated_at
            FROM exceptions e LEFT JOIN companies c USING(company_id)""" + where +
            " ORDER BY CASE e.severity WHEN 'error' THEN 0 ELSE 1 END,e.created_at LIMIT ?", args,
        ).fetchall()
        result=[]
        for row in rows:
            item=dict(row); item["payload"]=json.loads(item.pop("payload_json")); result.append(item)
        return result

    def attributes(self, market: str, symbol: str) -> dict:
        rows = self.conn.execute(
            """SELECT a.attribute_key,a.value_json,a.category,a.language,a.effective_at,a.version,a.source_key
            FROM company_attributes a JOIN companies c USING(company_id)
            WHERE c.market=? AND c.symbol=? AND a.is_current=1 ORDER BY a.category,a.attribute_key""",
            (market.upper(), symbol.upper()),
        ).fetchall()
        return {row["attribute_key"]: self._attach_source({"value": json.loads(row["value_json"]),
                "category": row["category"], "language": row["language"], "source_key": row["source_key"],
                "effective_at": row["effective_at"], "version": row["version"]}) for row in rows}

    def health(self) -> dict:
        tables = {
            "companies": "companies", "sources": "source_documents",
            "source_candidates": "source_candidates", "facts": "data_points",
            "disclosures": "disclosures", "attributes": "company_attributes",
            "securities": "securities", "listings": "listings", "market_prices": "market_prices",
            "ownership_positions": "ownership_positions", "corporate_actions": "corporate_actions",
            "consensus_estimates": "consensus_estimates",
            "coverage_rows": "coverage_status", "freshness_policies": "freshness_policies",
            "open_backlog": "backlog_items WHERE status IN ('open','ready','in_progress','blocked')",
            "completed_backlog": "backlog_items WHERE status='completed'",
            "open_exceptions": "exceptions WHERE status='open'", "queued_jobs": "jobs WHERE status='queued'",
            "running_jobs": "jobs WHERE status='running'", "dead_jobs": "jobs WHERE status='dead'",
            "active_schedules": "schedules WHERE enabled=1",
            "catalog_fields": "data_catalog_fields WHERE enabled=1",
            "catalog_versions": "data_catalog_field_versions",
            "dimensions": "dimension_definitions WHERE enabled=1",
            "metric_contracts": "metric_contracts WHERE enabled=1",
            "completeness_rows": "company_completeness",
        }
        return {key: self.conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for key, table in tables.items()}
