from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .database import Database, _json
from .factory_contract import (
    contract_category_ready,
    evaluate_factory_contract,
    seed_factory_contract_categories,
)
from .jobs import DurableJobQueue
from .understanding import CATEGORIES as LEGACY_CATEGORIES, refresh_company_understanding


CATEGORY_TARGET = Decimal("0.95")

# Several categories deliberately share one deterministic acquisition job.  A
# single issuer crawl can improve identity, business, governance and risks; it
# must not be repeated once per category.  Analyst data stays blocked until a
# licensed or publicly attributable provider is configured.
LEGACY_STRATEGIES = {
    "identity": "issuer_monitor",
    "business": "issuer_monitor",
    "governance": "issuer_monitor",
    "ownership": "issuer_monitor",
    "financials": "issuer_monitor",
    "earnings_quality": "issuer_monitor",
    "operations": "issuer_monitor",
    "dividends_actions": "issuer_monitor",
    "industry": "issuer_monitor",
    "forecasts": "issuer_monitor",
    "risks": "issuer_monitor",
    "esg": "issuer_monitor",
    "news": "issuer_monitor",
    "ratios": "deterministic_refresh",
    "competitors": "deterministic_refresh",
    "trading": "market_history",
    "valuation": "market_history",
    "analysts": "licensed_provider_required",
}

CONTRACT_JOB_STRATEGIES = {
    "one_time_profile_capture": "issuer_monitor",
    "periodic_statement_ingestion": "issuer_monitor",
    "periodic_market_data_sync": "market_history",
    "periodic_ownership_sync": "issuer_monitor",
    "continuous_announcement_polling": "issuer_monitor",
    "dividend_corporate_action_polling": "issuer_monitor",
    "periodic_operational_kpi_capture": "issuer_monitor",
    "sector_specific_periodic_capture": "issuer_monitor",
    "segment_note_periodic_capture": "issuer_monitor",
    "calculated_no_network": "deterministic_refresh",
    "provenance_audit_continuous": "deterministic_refresh",
}


class FactoryOrchestrator:
    """Durable, token-free controller for the 18-category readiness contract."""

    def __init__(self, db: Database):
        self.db = db
        self.queue = DurableJobQueue(db)

    def plan(
        self, *, market: str | None = None, symbols: list[str] | None = None,
        target_score: Decimal = Decimal("95"),
    ) -> dict:
        clauses = ["enabled=1"]
        args: list[object] = []
        if market:
            clauses.append("market=?")
            args.append(market.upper())
        if symbols:
            clauses.append("symbol IN (" + ",".join("?" for _ in symbols) + ")")
            args.extend(symbols)
        companies = self.db.conn.execute(
            "SELECT * FROM companies WHERE " + " AND ".join(clauses) + " ORDER BY market,symbol",
            args,
        ).fetchall()
        contract_keys = seed_factory_contract_categories(self.db)
        run_id = str(uuid.uuid4())
        scope = {"market": market.upper() if market else None, "symbols": symbols or [],
                 "scoring_model": "factory_18_category_contract", "contract_version": "1.0.0"}
        with self.db.conn:
            self.db.conn.execute(
                "INSERT INTO factory_runs(run_id,scope_json,target_score,total_items) VALUES(?,?,?,?)",
                (run_id, _json(scope), str(target_score), len(companies) * len(contract_keys)),
            )
        queued = completed = 0
        for company in companies:
            result = evaluate_factory_contract(self.db, company["company_id"])
            for ordinal, category in enumerate(result["categories"], start=1):
                key = category["category_key"]
                score = Decimal(category["score"])
                category_ready = contract_category_ready(category)
                state = "published" if category_ready and (
                    result["readiness_state"] == "ready" or score >= Decimal(1)
                ) else "queued"
                queued += state == "queued"
                completed += state == "published"
                work_id = f"factory:{run_id}:{company['company_id']}:{key}"
                gap = {
                    "score_before": str(score),
                    "weighted_score_before": category["weighted_score"],
                    "threshold": category["threshold"],
                    "hard_gates": category["hard_gates"],
                    "strategy": CONTRACT_JOB_STRATEGIES[category["job_strategy"]],
                    "contract_job_strategy": category["job_strategy"],
                    "scoring_model": result["scoring_model"],
                }
                with self.db.conn:
                    self.db.conn.execute(
                        """INSERT INTO factory_work_items(
                        work_item_id,run_id,company_id,category_key,state,priority,
                        source_plan_json,gap_snapshot_json,finished_at
                        ) VALUES(?,?,?,?,?,?,?,?,CASE WHEN ?='published' THEN CURRENT_TIMESTAMP END)""",
                        (work_id, run_id, company["company_id"], key, state,
                         10 + ordinal, "[]", _json(gap), state),
                    )
        with self.db.conn:
            self.db.conn.execute(
                "UPDATE factory_runs SET completed_items=?,updated_at=CURRENT_TIMESTAMP WHERE run_id=?",
                (completed, run_id),
            )
        return {"run_id": run_id, "companies": len(companies), "categories": len(contract_keys),
                "total_items": len(companies) * len(contract_keys), "completed": completed,
                "queued": queued, "target_score": str(target_score)}

    def dispatch(
        self, run_id: str, *, limit: int = 50,
        registry: str = "config/companies.json", raw_dir: str = "data/raw",
    ) -> dict:
        if limit < 1:
            raise ValueError("dispatch limit must be positive")
        run = self._run(run_id)
        if run["status"] in {"completed", "cancelled"}:
            return {"run_id": run_id, "status": run["status"], "dispatched_jobs": 0}
        rows = self.db.conn.execute(
            """SELECT w.*,c.market,c.symbol,c.sector,c.exchange,
            (SELECT url FROM company_sources s WHERE s.company_id=w.company_id AND s.enabled=1
             ORDER BY priority,id LIMIT 1) AS source_index
            FROM factory_work_items w JOIN companies c USING(company_id)
            WHERE w.run_id=? AND w.state='queued'
            ORDER BY w.priority,w.created_at LIMIT ?""", (run_id, limit * 18),
        ).fetchall()
        groups: dict[tuple[str, str], list] = {}
        for row in rows:
            strategy = json.loads(row["gap_snapshot_json"])["strategy"]
            groups.setdefault((row["company_id"], strategy), []).append(row)
        dispatched = blocked = 0
        for (company_id, strategy), items in list(groups.items())[:limit]:
            if strategy == "licensed_provider_required":
                with self.db.conn:
                    for item in items:
                        self.db.conn.execute(
                            """UPDATE factory_work_items SET state='blocked',
                            last_error='licensed or publicly attributable provider required',
                            updated_at=CURRENT_TIMESTAMP WHERE work_item_id=?""",
                            (item["work_item_id"],),
                        )
                        blocked += 1
                continue
            first = items[0]
            if strategy == "market_history":
                job_type = "market_history"
                payload = {"symbol": first["symbol"], "registry": registry, "raw_dir": raw_dir,
                           "sector": first["sector"], "market_segment": first["exchange"]}
            elif strategy == "deterministic_refresh":
                job_type = "understanding_refresh"
                payload = {"source_map_version": "factory-18-category-contract-v1",
                           "target_score": "95"}
            else:
                job_type = "monitor"
                payload = {"market": first["market"], "symbol": first["symbol"],
                           "registry": registry, "raw_dir": raw_dir,
                           "source_index": first["source_index"], "source_limit": 50,
                           "sa_manifest": None, "browser": first["market"] == "SA", "llm": False}
            job_id, _ = self.queue.enqueue(
                job_type, payload, company_id,
                idempotency_key=f"factory:{run_id}:{company_id}:{strategy}",
                priority=min(item["priority"] for item in items),
            )
            with self.db.conn:
                for item in items:
                    self.db.conn.execute(
                        """UPDATE factory_work_items SET state='running',job_id=?,attempts=attempts+1,
                        updated_at=CURRENT_TIMESTAMP WHERE work_item_id=?""",
                        (job_id, item["work_item_id"]),
                    )
            dispatched += 1
        with self.db.conn:
            self.db.conn.execute(
                """UPDATE factory_runs SET status='running',started_at=COALESCE(started_at,CURRENT_TIMESTAMP),
                updated_at=CURRENT_TIMESTAMP WHERE run_id=? AND status='queued'""", (run_id,),
            )
        return {"run_id": run_id, "status": "running", "dispatched_jobs": dispatched,
                "blocked_items": blocked}

    def reconcile(self, run_id: str) -> dict:
        run = self._run(run_id)
        contract_mode = json.loads(run["scope_json"] or "{}").get("scoring_model") == (
            "factory_18_category_contract"
        )
        company_ids = [row[0] for row in self.db.conn.execute(
            "SELECT DISTINCT company_id FROM factory_work_items WHERE run_id=?", (run_id,)
        )]
        latest = {}
        company_ready = {}
        for company_id in company_ids:
            if contract_mode:
                result = evaluate_factory_contract(self.db, company_id)
                latest[company_id] = {item["category_key"]: item for item in result["categories"]}
                company_ready[company_id] = result["readiness_state"] == "ready"
            else:
                result = refresh_company_understanding(self.db.conn, company_id)
                latest[company_id] = {item["category_key"]: Decimal(item["score"])
                                      for item in result["categories"]}
        rows = self.db.conn.execute(
            """SELECT w.*,j.status AS job_status,j.last_error AS job_error,j.result_json
            FROM factory_work_items w LEFT JOIN jobs j ON j.job_id=w.job_id
            WHERE w.run_id=?""", (run_id,),
        ).fetchall()
        with self.db.conn:
            for row in rows:
                current = latest[row["company_id"]][row["category_key"]]
                if contract_mode:
                    score = Decimal(current["score"])
                    passed = contract_category_ready(current) and (
                        company_ready[row["company_id"]] or score >= Decimal(1)
                    )
                else:
                    score = current
                    passed = score >= CATEGORY_TARGET
                if passed:
                    state, error = "published", None
                elif row["job_status"] == "dead":
                    state, error = "blocked", row["job_error"] or "deterministic worker exhausted retries"
                elif row["job_status"] == "succeeded":
                    state, error = "validated", None
                else:
                    continue
                self.db.conn.execute(
                    """UPDATE factory_work_items SET state=?,last_error=?,result_json=?,
                    updated_at=CURRENT_TIMESTAMP,finished_at=CASE WHEN ? IN ('published','blocked')
                    THEN CURRENT_TIMESTAMP ELSE finished_at END WHERE work_item_id=?""",
                    (state, error, row["result_json"] or "{}", state, row["work_item_id"]),
                )
        return self.status(run_id)

    def status(self, run_id: str) -> dict:
        run = self._run(run_id)
        scope = json.loads(run["scope_json"] or "{}")
        contract_mode = scope.get("scoring_model") == "factory_18_category_contract"
        counts = {row["state"]: row["n"] for row in self.db.conn.execute(
            "SELECT state,count(*) n FROM factory_work_items WHERE run_id=? GROUP BY state",
            (run_id,),
        )}
        completed = counts.get("published", 0) + counts.get("skipped", 0)
        failed = counts.get("blocked", 0)
        total = sum(counts.values())
        status = run["status"]
        if total and completed == total:
            status = "completed"
        elif failed and not counts.get("queued", 0) and not counts.get("running", 0):
            status = "blocked"
        with self.db.conn:
            self.db.conn.execute(
                """UPDATE factory_runs SET status=?,total_items=?,completed_items=?,failed_items=?,
                updated_at=CURRENT_TIMESTAMP,finished_at=CASE WHEN ? IN ('completed','blocked')
                THEN CURRENT_TIMESTAMP ELSE finished_at END WHERE run_id=?""",
                (status, total, completed, failed, status, run_id),
            )
        company_rows = self.db.conn.execute(
            """SELECT w.company_id,c.market,c.symbol,c.name,
            sum(w.state='published') AS categories_complete,count(*) AS categories_total,
            sum(w.state='blocked') AS categories_blocked
            FROM factory_work_items w JOIN companies c USING(company_id)
            WHERE w.run_id=?
            GROUP BY w.company_id ORDER BY c.market,c.symbol""", (run_id,),
        ).fetchall()
        companies = []
        for row in company_rows:
            company = dict(row)
            if contract_mode:
                readiness = evaluate_factory_contract(self.db, row["company_id"])
                company.update({"total_score": readiness["total_score"],
                                "readiness_state": readiness["readiness_state"],
                                "scoring_model": readiness["scoring_model"]})
            else:
                readiness = self.db.conn.execute(
                    "SELECT total_score,readiness_state FROM company_readiness WHERE company_id=?",
                    (row["company_id"],),
                ).fetchone()
                company.update({"total_score": readiness["total_score"] if readiness else None,
                                "readiness_state": readiness["readiness_state"] if readiness else None,
                                "scoring_model": "legacy_investor_understanding"})
            companies.append(company)
        return {"run_id": run_id, "status": status, "target_score": run["target_score"],
                "scoring_model": scope.get("scoring_model", "legacy_investor_understanding"),
                "counts": counts, "companies": companies}

    def throughput(self, run_id: str | None = None, *, window_hours: int = 24) -> dict:
        """Report factory throughput from work that has actually finished.

        Every figure is derived from finished `factory_work_items` and the
        scoring model recorded on their run; none of it is estimated
        from queue depth or backlog size, per the reporting requirement that the
        sustainable daily throughput reflect completed runs only.
        """
        if window_hours <= 0:
            raise ValueError("window_hours must be positive")
        clauses = ["1=1"]
        args: list[object] = []
        if run_id:
            clauses.append("w.run_id=?")
            args.append(run_id)
        where = " AND ".join(clauses)
        rows = self.db.conn.execute(
            f"""SELECT w.run_id,w.company_id,w.category_key,w.state,w.finished_at,w.created_at,
            f.scope_json FROM factory_work_items w JOIN factory_runs f USING(run_id)
            WHERE {where}""", args,
        ).fetchall()
        by_run_company: dict[tuple[str, str], list] = {}
        for row in rows:
            by_run_company.setdefault((row["run_id"], row["company_id"]), []).append(row)

        companies_attempted = len({company_id for _, company_id in by_run_company})
        ready_companies: set[str] = set()
        companies_blocked = 0
        blocked_categories: dict[str, int] = {}
        completions: dict[str, str] = {}
        blocked_companies: set[str] = set()
        for (_, company_id), items in by_run_company.items():
            scope = json.loads(items[0]["scope_json"] or "{}")
            terminal = all(item["state"] in ("published", "skipped") for item in items)
            if scope.get("scoring_model") == "factory_18_category_contract":
                ready = terminal and evaluate_factory_contract(
                    self.db, company_id
                )["readiness_state"] == "ready"
            else:
                row = self.db.conn.execute(
                    "SELECT readiness_state FROM company_readiness WHERE company_id=?",
                    (company_id,),
                ).fetchone()
                ready = terminal and row is not None and row["readiness_state"] == "ready"
            if ready:
                ready_companies.add(company_id)
                finished = [item["finished_at"] for item in items if item["finished_at"]]
                if finished:
                    completions[company_id] = max(finished)
            blocked_keys = [item["category_key"] for item in items if item["state"] == "blocked"]
            if blocked_keys:
                blocked_companies.add(company_id)
            for key in blocked_keys:
                blocked_categories[key] = blocked_categories.get(key, 0) + 1

        companies_reaching_target = len(ready_companies)
        companies_blocked = len(blocked_companies)

        category_jobs_completed = sum(1 for row in rows if row["state"] in ("published", "skipped"))
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=window_hours)

        def _timestamp(value: str) -> datetime:
            # SQLite CURRENT_TIMESTAMP has no offset; treat stored timestamps as UTC.
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed

        companies_completed_in_window = sum(
            1 for finished_at in completions.values() if _timestamp(finished_at) >= window_start
        )
        earliest_started = min((row["created_at"] for row in rows), default=None)
        sustainable_daily_throughput = None
        if earliest_started and completions:
            started_at = _timestamp(earliest_started)
            elapsed_hours = max((now - started_at).total_seconds() / 3600, 1e-6)
            sustainable_daily_throughput = round(len(completions) / elapsed_hours * 24, 4)
        top_blocking_categories = sorted(
            blocked_categories.items(), key=lambda item: item[1], reverse=True
        )[:5]

        return {
            "run_id": run_id,
            "window_hours": window_hours,
            "companies_attempted": companies_attempted,
            "companies_reaching_target": companies_reaching_target,
            "companies_blocked": companies_blocked,
            "category_jobs_completed": category_jobs_completed,
            "companies_completed_in_window": companies_completed_in_window,
            "top_blocking_categories": [
                {"category_key": key, "companies_blocked": count}
                for key, count in top_blocking_categories
            ],
            "estimated_sustainable_daily_throughput": sustainable_daily_throughput,
            "basis": "completed_factory_work_items_and_run_scoring_model",
        }

    def cancel(self, run_id: str) -> dict:
        self._run(run_id)
        with self.db.conn:
            self.db.conn.execute(
                "UPDATE jobs SET status='cancelled',leased_by=NULL,lease_until=NULL WHERE job_id IN "
                "(SELECT job_id FROM factory_work_items WHERE run_id=? AND job_id IS NOT NULL) "
                "AND status IN ('queued','running')", (run_id,),
            )
            self.db.conn.execute(
                "UPDATE factory_work_items SET state='cancelled',updated_at=CURRENT_TIMESTAMP "
                "WHERE run_id=? AND state NOT IN ('published','skipped')", (run_id,),
            )
            self.db.conn.execute(
                "UPDATE factory_runs SET status='cancelled',finished_at=CURRENT_TIMESTAMP,"
                "updated_at=CURRENT_TIMESTAMP WHERE run_id=?", (run_id,),
            )
        return self.status(run_id)

    def _run(self, run_id: str):
        row = self.db.conn.execute("SELECT * FROM factory_runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            raise KeyError(f"unknown factory run {run_id}")
        return row
