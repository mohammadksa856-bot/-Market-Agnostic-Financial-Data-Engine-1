from __future__ import annotations

import json
import uuid
from decimal import Decimal

from .database import Database, _json
from .jobs import DurableJobQueue
from .understanding import CATEGORIES, refresh_company_understanding


CATEGORY_TARGET = Decimal("0.95")

# Several categories deliberately share one deterministic acquisition job.  A
# single issuer crawl can improve identity, business, governance and risks; it
# must not be repeated once per category.  Analyst data stays blocked until a
# licensed or publicly attributable provider is configured.
STRATEGIES = {
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
        run_id = str(uuid.uuid4())
        scope = {"market": market.upper() if market else None, "symbols": symbols or []}
        with self.db.conn:
            self.db.conn.execute(
                "INSERT INTO factory_runs(run_id,scope_json,target_score,total_items) VALUES(?,?,?,?)",
                (run_id, _json(scope), str(target_score), len(companies) * len(CATEGORIES)),
            )
        queued = completed = 0
        for company in companies:
            result = refresh_company_understanding(self.db.conn, company["company_id"])
            by_key = {item["category_key"]: item for item in result["categories"]}
            for key, ordinal, *_ in CATEGORIES:
                category = by_key[key]
                score = Decimal(category["score"])
                state = "published" if score >= CATEGORY_TARGET else "queued"
                queued += state == "queued"
                completed += state == "published"
                work_id = f"factory:{run_id}:{company['company_id']}:{key}"
                source_plan = category.get("evidence", {}).get("source_plan", [])
                gap = {
                    "score_before": str(score),
                    "gaps": category.get("gaps", []),
                    "hard_gates": result["hard_gates"],
                    "strategy": STRATEGIES[key],
                }
                with self.db.conn:
                    self.db.conn.execute(
                        """INSERT INTO factory_work_items(
                        work_item_id,run_id,company_id,category_key,state,priority,
                        source_plan_json,gap_snapshot_json,finished_at
                        ) VALUES(?,?,?,?,?,?,?,?,CASE WHEN ?='published' THEN CURRENT_TIMESTAMP END)""",
                        (work_id, run_id, company["company_id"], key, state,
                         10 + ordinal, _json(source_plan), _json(gap), state),
                    )
        with self.db.conn:
            self.db.conn.execute(
                "UPDATE factory_runs SET completed_items=?,updated_at=CURRENT_TIMESTAMP WHERE run_id=?",
                (completed, run_id),
            )
        return {"run_id": run_id, "companies": len(companies), "categories": len(CATEGORIES),
                "total_items": len(companies) * len(CATEGORIES), "completed": completed,
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
            ORDER BY w.priority,w.created_at LIMIT ?""", (run_id, limit * len(CATEGORIES)),
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
                payload = {"source_map_version": "18-categories-v1", "target_score": "95"}
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
        self._run(run_id)
        company_ids = [row[0] for row in self.db.conn.execute(
            "SELECT DISTINCT company_id FROM factory_work_items WHERE run_id=?", (run_id,)
        )]
        latest = {}
        for company_id in company_ids:
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
                score = latest[row["company_id"]][row["category_key"]]
                if score >= CATEGORY_TARGET:
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
        companies = [dict(row) for row in self.db.conn.execute(
            """SELECT c.market,c.symbol,c.name,r.total_score,r.readiness_state,
            sum(w.state='published') AS categories_complete,count(*) AS categories_total,
            sum(w.state='blocked') AS categories_blocked
            FROM factory_work_items w JOIN companies c USING(company_id)
            LEFT JOIN company_readiness r USING(company_id) WHERE w.run_id=?
            GROUP BY w.company_id ORDER BY c.market,c.symbol""", (run_id,),
        )]
        return {"run_id": run_id, "status": status, "target_score": run["target_score"],
                "counts": counts, "companies": companies}

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
