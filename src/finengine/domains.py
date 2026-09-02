from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone

from .database import Database, _json


class CompanyDomainStore:
    """Structured stores for market, ownership, actions, formulas and coverage."""

    def __init__(self, db: Database):
        self.db = db

    def primary_listing_id(self, company_id: str) -> str:
        row = self.db.conn.execute(
            """SELECT l.listing_id FROM listings l JOIN securities s USING(security_id)
            WHERE s.company_id=? AND l.active=1 ORDER BY l.is_primary DESC,l.created_at LIMIT 1""",
            (company_id,)).fetchone()
        if not row:
            raise KeyError(f"company has no active listing: {company_id}")
        return row["listing_id"]

    def publish_market_price(
        self, company_id: str, observed_at: str, close, currency: str, source_key: str,
        interval: str = "1d", open=None, high=None, low=None, adjusted_close=None,
        volume=None, turnover=None, listing_id: str | None = None,
    ) -> str:
        listing_id = listing_id or self.primary_listing_id(company_id)
        numbers = {name: Decimal(str(value)) for name, value in {
            "open": open, "high": high, "low": low, "close": close,
            "adjusted_close": adjusted_close, "volume": volume, "turnover": turnover,
        }.items() if value is not None}
        if numbers.get("volume", Decimal(0)) < 0 or numbers.get("turnover", Decimal(0)) < 0:
            raise ValueError("volume and turnover cannot be negative")
        comparable = [numbers[name] for name in ("open", "close", "low") if name in numbers]
        if "high" in numbers and comparable and numbers["high"] < max(comparable):
            raise ValueError("high price is below another OHLC value")
        comparable = [numbers[name] for name in ("open", "close", "high") if name in numbers]
        if "low" in numbers and comparable and numbers["low"] > min(comparable):
            raise ValueError("low price is above another OHLC value")
        fields = tuple(str(numbers[name]) if name in numbers else None for name in
                       ("open", "high", "low", "close", "adjusted_close", "volume", "turnover"))
        old = self.db.conn.execute(
            "SELECT * FROM market_prices WHERE listing_id=? AND observed_at=? AND interval=? AND is_current=1",
            (listing_id, observed_at, interval)).fetchone()
        current = (*fields, currency, source_key)
        if old and tuple(old[name] for name in ("open", "high", "low", "close", "adjusted_close", "volume", "turnover", "currency", "source_key")) == current:
            return "duplicate"
        version = old["version"] + 1 if old else 1
        with self.db.conn:
            if old:
                self.db.conn.execute("UPDATE market_prices SET is_current=0 WHERE id=?", (old["id"],))
            self.db.conn.execute(
                """INSERT INTO market_prices(listing_id,observed_at,interval,open,high,low,close,
                adjusted_close,volume,turnover,currency,source_key,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (listing_id, observed_at, interval, *fields, currency, source_key, version))
        return "restated" if old else "inserted"

    def publish_ownership_position(
        self, company_id: str, holder_key: str, holder_name: str, ownership_type: str,
        as_of_date: str, source_key: str, shares=None, ownership_pct=None,
        holder_type: str | None = None, country: str | None = None, metadata: dict | None = None,
    ) -> str:
        share_value = str(Decimal(str(shares))) if shares is not None else None
        pct_value = Decimal(str(ownership_pct)) if ownership_pct is not None else None
        if pct_value is not None and not Decimal(0) <= pct_value <= Decimal(1):
            raise ValueError("ownership_pct must be between 0 and 1")
        encoded = _json(metadata or {})
        old = self.db.conn.execute(
            """SELECT * FROM ownership_positions WHERE company_id=? AND holder_key=?
            AND ownership_type=? AND as_of_date=? AND is_current=1""",
            (company_id, holder_key, ownership_type, as_of_date)).fetchone()
        current = (holder_name, holder_type, share_value, str(pct_value) if pct_value is not None else None,
                   country, source_key, encoded)
        if old and tuple(old[name] for name in ("holder_name", "holder_type", "shares", "ownership_pct", "country", "source_key", "metadata_json")) == current:
            return "duplicate"
        version = old["version"] + 1 if old else 1
        with self.db.conn:
            if old:
                self.db.conn.execute("UPDATE ownership_positions SET is_current=0 WHERE id=?", (old["id"],))
            self.db.conn.execute(
                """INSERT INTO ownership_positions(company_id,holder_key,holder_name,holder_type,
                ownership_type,as_of_date,shares,ownership_pct,country,source_key,metadata_json,version)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (company_id, holder_key, holder_name, holder_type, ownership_type, as_of_date,
                 share_value, str(pct_value) if pct_value is not None else None, country, source_key, encoded, version))
        return "restated" if old else "inserted"

    def publish_corporate_action(
        self, action_key: str, company_id: str, action_type: str, title: str,
        announcement_date: str, source_key: str, listing_id: str | None = None,
        ex_date: str | None = None, record_date: str | None = None,
        eligibility_date: str | None = None, payment_date: str | None = None,
        effective_date: str | None = None, cash_amount=None, currency: str | None = None,
        ratio_numerator=None, ratio_denominator=None, status: str = "announced",
        details: dict | None = None,
    ) -> str:
        listing_id = listing_id or self.primary_listing_id(company_id)
        cash = str(Decimal(str(cash_amount))) if cash_amount is not None else None
        numerator = str(Decimal(str(ratio_numerator))) if ratio_numerator is not None else None
        denominator = str(Decimal(str(ratio_denominator))) if ratio_denominator is not None else None
        encoded = _json(details or {})
        old = self.db.conn.execute(
            "SELECT * FROM corporate_actions WHERE action_key=? AND is_current=1", (action_key,)).fetchone()
        fields = (company_id, listing_id, action_type, title, announcement_date, ex_date, record_date,
                  eligibility_date, payment_date, effective_date, cash, currency, numerator, denominator,
                  status, source_key, encoded)
        names = ("company_id", "listing_id", "action_type", "title", "announcement_date", "ex_date",
                 "record_date", "eligibility_date", "payment_date", "effective_date", "cash_amount",
                 "currency", "ratio_numerator", "ratio_denominator", "status", "source_key", "details_json")
        if old and tuple(old[name] for name in names) == fields:
            return "duplicate"
        version = old["version"] + 1 if old else 1
        with self.db.conn:
            if old:
                self.db.conn.execute("UPDATE corporate_actions SET is_current=0 WHERE id=?", (old["id"],))
            self.db.conn.execute(
                """INSERT INTO corporate_actions(action_key,company_id,listing_id,action_type,title,
                announcement_date,ex_date,record_date,eligibility_date,payment_date,effective_date,
                cash_amount,currency,ratio_numerator,ratio_denominator,status,source_key,details_json,version)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (action_key, *fields, version))
        return "restated" if old else "inserted"

    def register_calculation(
        self, metric_key: str, expression: str, dependencies: list[str], formula_version: int,
        output_unit: str | None = None, period_rule: str = "same_period",
        description: str | None = None,
    ) -> None:
        self.db.register_metric(metric_key, category="calculated", commit=False)
        for dependency in dependencies:
            self.db.register_metric(dependency, commit=False)
        with self.db.conn:
            self.db.conn.execute(
                "UPDATE calculation_definitions SET is_current=0 WHERE metric_key=?", (metric_key,))
            self.db.conn.execute(
                """INSERT INTO calculation_definitions(metric_key,formula_version,expression,output_unit,
                period_rule,description,is_current) VALUES(?,?,?,?,?,?,1)
                ON CONFLICT(metric_key,formula_version) DO UPDATE SET expression=excluded.expression,
                output_unit=excluded.output_unit,period_rule=excluded.period_rule,
                description=excluded.description,enabled=1,is_current=1""",
                (metric_key, formula_version, expression, output_unit, period_rule, description))
            self.db.conn.execute(
                "DELETE FROM calculation_dependencies WHERE metric_key=? AND formula_version=?",
                (metric_key, formula_version))
            self.db.conn.executemany(
                """INSERT INTO calculation_dependencies(metric_key,formula_version,dependency_metric)
                VALUES(?,?,?)""", [(metric_key, formula_version, dependency) for dependency in dependencies])

    def set_metric_applicability(
        self, metric_key: str, scope_type: str, scope_value: str = "*", period_kind: str = "*",
        requirement: str = "optional",
    ) -> None:
        self.db.register_metric(metric_key, commit=False)
        with self.db.conn:
            self.db.conn.execute(
                """INSERT INTO metric_applicability(metric_key,scope_type,scope_value,period_kind,requirement)
                VALUES(?,?,?,?,?) ON CONFLICT(metric_key,scope_type,scope_value,period_kind)
                DO UPDATE SET requirement=excluded.requirement,enabled=1""",
                (metric_key, scope_type, scope_value, period_kind, requirement))

    def apply_metric_pack(self, scope_type: str, scope_value: str, metrics: list[dict]) -> None:
        """Install a reviewed market/sector/company metric pack without code changes."""
        for item in metrics:
            self.db.register_metric(
                item["metric_key"], item.get("display_name"), item.get("category", "operational"),
                item.get("statement"), item.get("value_type", "decimal"), item.get("default_unit"),
                item.get("aggregation", "none"), item.get("description"), commit=False)
            self.set_metric_applicability(
                item["metric_key"], scope_type, scope_value, item.get("period_kind", "*"),
                item.get("requirement", "optional"))

    def set_freshness_policy(self, scope_type: str, scope_value: str, domain: str,
                             max_age_seconds: int) -> None:
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        with self.db.conn:
            self.db.conn.execute(
                """INSERT INTO freshness_policies(scope_type,scope_value,domain,max_age_seconds)
                VALUES(?,?,?,?) ON CONFLICT(scope_type,scope_value,domain)
                DO UPDATE SET max_age_seconds=excluded.max_age_seconds,enabled=1""",
                (scope_type, scope_value, domain, max_age_seconds))

    def refresh_coverage(self, company_id: str, period_end: str, period_kind: str,
                         domain: str = "all", now: datetime | None = None) -> dict:
        company = self.db.conn.execute(
            "SELECT market,sector,industry FROM companies WHERE company_id=?", (company_id,)).fetchone()
        if not company:
            raise KeyError(company_id)
        rows = self.db.conn.execute(
            """SELECT a.metric_key,a.scope_type,a.scope_value,a.requirement,m.category
            FROM metric_applicability a JOIN metric_definitions m USING(metric_key)
            WHERE a.enabled=1 AND a.period_kind IN ('*',?)""", (period_kind,)).fetchall()
        rank = {"optional": 0, "recommended": 1, "required": 2}
        applicable: dict[str, str] = {}
        for row in rows:
            matches = (
                row["scope_type"] == "all" or
                (row["scope_type"] == "market" and row["scope_value"] == company["market"]) or
                (row["scope_type"] == "sector" and row["scope_value"] == (company["sector"] or "")) or
                (row["scope_type"] == "industry" and row["scope_value"] == (company["industry"] or "")) or
                (row["scope_type"] == "company" and row["scope_value"] == company_id)
            )
            if matches and (domain == "all" or row["category"] == domain):
                previous = applicable.get(row["metric_key"])
                if previous is None or rank[row["requirement"]] > rank[previous]:
                    applicable[row["metric_key"]] = row["requirement"]
        expected = {metric for metric, requirement in applicable.items() if requirement != "optional"}
        required = {metric for metric, requirement in applicable.items() if requirement == "required"}
        available_rows = self.db.conn.execute(
            """SELECT DISTINCT d.metric_key,d.filed_at,m.category FROM data_points d
            JOIN metric_definitions m USING(metric_key) WHERE d.company_id=? AND d.period_end=?
            AND d.period_kind=? AND d.is_current=1""", (company_id, period_end, period_kind)).fetchall()
        available = {row["metric_key"] for row in available_rows
                     if domain == "all" or row["category"] == domain}
        available_expected = expected & available
        missing_required = sorted(required - available)
        if not expected:
            status = "not_applicable"
        elif not available_expected:
            status = "missing"
        elif missing_required or len(available_expected) < len(expected):
            status = "partial"
        else:
            status = "complete"
        score = Decimal(1) if not expected else Decimal(len(available_expected)) / Decimal(len(expected))
        latest = max((row["filed_at"] for row in available_rows), default=None)
        scope_rank = {"all": 0, "market": 1, "sector": 2, "industry": 3, "company": 4}
        policy_rows = self.db.conn.execute(
            "SELECT * FROM freshness_policies WHERE enabled=1 AND domain IN ('all',?)", (domain,)).fetchall()
        matching_policies = []
        for policy in policy_rows:
            matches = (
                policy["scope_type"] == "all" or
                (policy["scope_type"] == "market" and policy["scope_value"] == company["market"]) or
                (policy["scope_type"] == "sector" and policy["scope_value"] == (company["sector"] or "")) or
                (policy["scope_type"] == "industry" and policy["scope_value"] == (company["industry"] or "")) or
                (policy["scope_type"] == "company" and policy["scope_value"] == company_id)
            )
            if matches:
                matching_policies.append((scope_rank[policy["scope_type"]], int(policy["domain"] == domain), policy))
        freshness_status = "unknown"; age_seconds = None
        if latest and matching_policies:
            policy = max(matching_policies, key=lambda item: (item[0], item[1]))[2]
            source_time = datetime.fromisoformat(latest.replace("Z", "+00:00"))
            if source_time.tzinfo is None:
                source_time = source_time.replace(tzinfo=timezone.utc)
            checked = now or datetime.now(timezone.utc)
            if checked.tzinfo is None:
                checked = checked.replace(tzinfo=timezone.utc)
            age_seconds = max(0, int((checked - source_time).total_seconds()))
            freshness_status = "fresh" if age_seconds <= policy["max_age_seconds"] else "stale"
        result = {
            "company_id": company_id, "period_end": period_end, "period_kind": period_kind,
            "domain": domain, "expected_count": len(expected), "available_count": len(available_expected),
            "required_missing": missing_required, "status": status, "quality_score": str(score),
            "latest_source_at": latest, "freshness_status": freshness_status, "age_seconds": age_seconds,
        }
        with self.db.conn:
            self.db.conn.execute(
                """INSERT INTO coverage_status(company_id,period_end,period_kind,domain,expected_count,
                available_count,required_missing_json,status,quality_score,latest_source_at,freshness_status,age_seconds)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(company_id,period_end,period_kind,domain)
                DO UPDATE SET expected_count=excluded.expected_count,available_count=excluded.available_count,
                required_missing_json=excluded.required_missing_json,status=excluded.status,
                quality_score=excluded.quality_score,latest_source_at=excluded.latest_source_at,
                freshness_status=excluded.freshness_status,age_seconds=excluded.age_seconds,
                checked_at=CURRENT_TIMESTAMP""",
                (company_id, period_end, period_kind, domain, len(expected), len(available_expected),
                 _json(missing_required), status, str(score), latest, freshness_status, age_seconds))
        missing_expected = {metric: applicable[metric] for metric in sorted(expected - available)}
        result["backlog"] = self.db.sync_coverage_backlog(
            company_id, period_end, period_kind, domain, missing_expected,
        )
        return result

    def refresh_company_coverage(self, company_id: str) -> list[dict]:
        periods = self.db.conn.execute(
            """SELECT DISTINCT period_end,period_kind FROM data_points
            WHERE company_id=? AND is_current=1 ORDER BY period_end,period_kind""", (company_id,)).fetchall()
        return [self.refresh_coverage(company_id, row["period_end"], row["period_kind"])
                for row in periods]

    def refresh_company_backlog(self, company_id: str) -> dict:
        """Create backlog work for coverage gaps and still-empty company data domains."""
        company = self.db.conn.execute(
            "SELECT name FROM companies WHERE company_id=?", (company_id,)).fetchone()
        if not company:
            raise KeyError(company_id)
        coverage = self.refresh_company_coverage(company_id)
        source = self.db.conn.execute(
            "SELECT url FROM company_sources WHERE company_id=? AND enabled=1 ORDER BY priority LIMIT 1",
            (company_id,),
        ).fetchone()
        source_url = source["url"] if source else None
        counts = {
            "historical_financials": self.db.conn.execute(
                "SELECT count(*) FROM data_points WHERE company_id=? AND is_current=1", (company_id,)).fetchone()[0],
            "company_profile": self.db.conn.execute(
                "SELECT count(*) FROM company_attributes WHERE company_id=? AND is_current=1", (company_id,)).fetchone()[0],
            "disclosures": self.db.conn.execute(
                "SELECT count(*) FROM disclosures WHERE company_id=? AND is_current=1", (company_id,)).fetchone()[0],
            "ownership": self.db.conn.execute(
                "SELECT count(*) FROM ownership_positions WHERE company_id=? AND is_current=1", (company_id,)).fetchone()[0],
            "corporate_actions": self.db.conn.execute(
                "SELECT count(*) FROM corporate_actions WHERE company_id=? AND is_current=1", (company_id,)).fetchone()[0],
            "market_prices": self.db.conn.execute(
                """SELECT count(*) FROM market_prices p JOIN listings l USING(listing_id)
                JOIN securities s USING(security_id) WHERE s.company_id=? AND p.is_current=1""",
                (company_id,),
            ).fetchone()[0],
        }
        tasks = {
            "historical_financials": ("financial", "Ingest historical financial statements", 10),
            "corporate_actions": ("corporate_actions", "Collect dividends, splits and corporate actions", 30),
            "market_prices": ("market", "Load historical market prices", 30),
            "disclosures": ("disclosures", "Archive and classify company disclosures", 40),
            "ownership": ("ownership", "Load ownership and major-holder history", 40),
            "company_profile": ("general", "Complete versioned company profile", 50),
        }
        created = 0
        completed = 0
        for key, (domain, title, priority) in tasks.items():
            idempotency_key = f"domain:{company_id}:{key}"
            if counts[key] == 0:
                state = self.db.upsert_backlog_item(
                    idempotency_key, "domain_backfill", domain,
                    f"{title}: {company['name']}", company_id=company_id,
                    description="This domain is empty and must remain outside production until validated.",
                    source_url=source_url, priority=priority,
                    payload={"origin": "domain_audit", "domain_key": key},
                )
                created += int(state in {"inserted", "reopened"})
            else:
                completed += int(self.db.complete_backlog_item(idempotency_key))
        open_count = self.db.conn.execute(
            """SELECT count(*) FROM backlog_items WHERE company_id=?
            AND status IN ('open','ready','in_progress','blocked')""", (company_id,)).fetchone()[0]
        return {
            "company_id": company_id, "coverage_periods": len(coverage), "domain_counts": counts,
            "created": created, "completed": completed, "open": open_count,
        }

    def refresh_all_backlog(self) -> list[dict]:
        companies = self.db.conn.execute(
            "SELECT company_id FROM companies WHERE enabled=1 ORDER BY company_id").fetchall()
        return [self.refresh_company_backlog(row["company_id"]) for row in companies]
