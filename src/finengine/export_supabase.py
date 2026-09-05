"""Publish current, source-traced facts to a Supabase `financial_facts` table.

This is the bridge between the engine's SQLite production store and the
consumer application (website + Telegram bot). It is deliberately one-way and
additive: it upserts the engine's *current* facts (the same rows `finengine
facts` returns) into one flat, queryable table, carrying every provenance
column - official source URL, archived SHA-256, the raw extracted label and
value, and the mapping confidence - so a reader can audit any number without
leaving the database. Derived rows carry their deterministic formula.

No third-party package: the engine stays dependency-free and talks to
Supabase's PostgREST endpoint over stdlib HTTP. Writes use the service-role
key (set it in the environment, never in code) which bypasses row-level
security; readers use the anon key and the table's read policy.

    export = SupabaseExporter(db_path, url, key, engine_version="1.5.0")
    summary = export.export("SA", "2222", registry, prune=True)

`--sql-out` instead emits an idempotent INSERT ... ON CONFLICT script for
review-before-apply when a service key is not available locally.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

TABLE = "financial_facts"
CONFLICT = "company_id,metric,period_end,period_kind,scope,dimensions_key"

# Columns on the target table, in a stable order. The exporter only ever sends
# these keys; anything else on a fact row is ignored.
COLUMNS = (
    "company_id", "ticker", "market", "metric", "display_name", "category",
    "statement", "period_end", "period_kind", "fiscal_year", "fiscal_quarter",
    "scope", "dimensions", "dimensions_key", "value", "value_text", "value_type",
    "currency", "unit", "is_calculated", "calculation", "quality_score",
    "source_url", "source_key", "filed_at", "report_page", "report_table",
    "extraction_label", "extraction_value", "mapping_confidence", "mapping_method",
    "archived_path", "archived_sha256", "engine_version", "synced_at",
)


def canonical_dimensions(dimensions: dict | None) -> str:
    """A stable string form of a fact's dimensions, for the unique key.

    Empty dimensions collapse to '' so an undimensioned fact has one identity.
    """
    if not dimensions:
        return ""
    return json.dumps(dimensions, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _num(value):
    """A JSON-safe numeric: the value as a string so Postgres parses it at full
    precision (no float rounding of billion-scale integers), or None."""
    if value in (None, ""):
        return None
    try:
        float(value)
    except (TypeError, ValueError):
        return None
    return str(value).strip()


def flatten_fact(company, fact: dict, *, engine_version: str, synced_at: str) -> dict:
    """Map one `FinancialQueryService.facts()` row to a `financial_facts` row."""
    provenance = fact.get("provenance") or {}
    source = provenance.get("source") or {}
    extraction = provenance.get("extraction") or {}
    derivation = provenance.get("derivation") or {}
    dimensions = fact.get("dimensions") or {}

    value_type = fact.get("value_type", "decimal")
    value = None
    value_text = None
    if value_type == "decimal":
        value = _num(fact.get("value"))
    elif value_type == "boolean":
        value_text = "true" if fact.get("value") else "false"
    elif value_type == "json":
        value_text = json.dumps(fact.get("value"), ensure_ascii=False)
    else:  # text, date
        raw = fact.get("value")
        value_text = raw if isinstance(raw, str) else (None if raw is None else str(raw))

    calculation = fact.get("calculation") or derivation.get("calculation")

    return {
        "company_id": company.company_id,
        "ticker": company.symbol,
        "market": company.market.value,
        "metric": fact["metric"],
        "display_name": fact.get("display_name"),
        "category": fact.get("category"),
        "statement": fact.get("statement"),
        "period_end": fact["period_end"],
        "period_kind": fact["period_kind"],
        "fiscal_year": fact.get("fiscal_year"),
        "fiscal_quarter": fact.get("fiscal_quarter"),
        "scope": fact.get("scope") or "consolidated",
        "dimensions": dimensions,
        "dimensions_key": canonical_dimensions(dimensions),
        "value": value,
        "value_text": value_text,
        "value_type": value_type,
        "currency": fact.get("currency") or None,
        "unit": fact.get("unit") or None,
        "is_calculated": bool(fact.get("is_calculated")),
        "calculation": calculation,
        "quality_score": _num(fact.get("quality_score")),
        "source_url": fact.get("source_url") or source.get("source_url"),
        "source_key": fact.get("source_key") or source.get("source_key"),
        "filed_at": fact.get("filed_at") or source.get("filed_at"),
        "report_page": extraction.get("page"),
        "report_table": extraction.get("table_ref"),
        "extraction_label": extraction.get("raw_label"),
        "extraction_value": extraction.get("raw_value"),
        "mapping_confidence": _num(extraction.get("confidence")),
        "mapping_method": extraction.get("mapping_method"),
        "archived_path": (source.get("archived_path") or "").replace("\\", "/") or None,
        "archived_sha256": source.get("artifact_sha256"),
        "engine_version": engine_version,
        "synced_at": synced_at,
    }


class SupabaseExporter:
    def __init__(
        self, db_path: str, base_url: str, service_key: str,
        *, engine_version: str, timeout: int = 30, opener=None,
    ):
        if not base_url:
            raise ValueError("a Supabase project URL is required")
        if not service_key:
            raise ValueError("a Supabase service-role key is required")
        self.db_path = db_path
        self.base_url = base_url.rstrip("/")
        self.service_key = service_key
        self.engine_version = engine_version
        self.timeout = timeout
        self._opener = opener or urllib.request.urlopen

    # -- HTTP ---------------------------------------------------------------
    def _request(self, method: str, path: str, *, body: bytes | None = None, prefer: str = "") -> bytes:
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        request = urllib.request.Request(
            f"{self.base_url}/rest/v1/{path}", data=body, headers=headers, method=method,
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")
            raise RuntimeError(f"supabase {method} {path} -> {error.code}: {detail}") from None

    def _upsert(self, rows: list[dict]) -> None:
        body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
        self._request(
            "POST", f"{TABLE}?on_conflict={CONFLICT}", body=body,
            prefer="resolution=merge-duplicates,return=minimal",
        )

    def _prune(self, company_id: str, before: str) -> int:
        raw = self._request(
            "DELETE",
            f"{TABLE}?company_id=eq.{company_id}&synced_at=lt.{before}",
            prefer="return=representation",
        )
        try:
            return len(json.loads(raw))
        except (ValueError, TypeError):
            return 0

    # -- rows -------------------------------------------------------------
    def rows_for(self, market: str, symbol: str, company, service) -> list[dict]:
        synced_at = datetime.now(timezone.utc).isoformat()
        rows: list[dict] = []
        offset = 0
        page = 2000
        while True:
            batch = service.facts(market, symbol, limit=page, offset=offset)
            rows.extend(
                flatten_fact(company, fact, engine_version=self.engine_version, synced_at=synced_at)
                for fact in batch
            )
            if len(batch) < page:
                break
            offset += page
        return rows

    def export(self, market: str, symbol: str, registry, *, prune: bool = False, batch: int = 500) -> dict:
        from .query import FinancialQueryService

        company = registry.resolve(market, symbol)
        service = FinancialQueryService(self.db_path)
        try:
            rows = self.rows_for(market, symbol, company, service)
        finally:
            service.close()
        if not rows:
            return {"company_id": company.company_id, "facts": 0, "batches": 0, "pruned": 0}

        run_stamp = rows[0]["synced_at"]
        sent = 0
        for start in range(0, len(rows), batch):
            self._upsert(rows[start:start + batch])
            sent += 1
            time.sleep(0.05)
        pruned = self._prune(company.company_id, run_stamp) if prune else 0
        return {
            "company_id": company.company_id, "ticker": company.symbol,
            "facts": len(rows), "batches": sent, "pruned": pruned, "synced_at": run_stamp,
        }


def facts_to_sql(rows: list[dict]) -> str:
    """An idempotent INSERT ... ON CONFLICT DO UPDATE script for the given rows.

    For review-before-apply, or when no service-role key is available locally.
    """
    if not rows:
        return "-- no current facts to export\n"
    updatable = [c for c in COLUMNS if c not in {"company_id", "metric", "period_end", "period_kind", "scope", "dimensions_key"}]
    set_clause = ", ".join(f"{c} = excluded.{c}" for c in updatable)
    lines = [
        "-- generated by finengine export-supabase --sql-out",
        f"-- {len(rows)} current facts",
        "begin;",
    ]
    for row in rows:
        values = ", ".join(_sql_literal(row.get(column)) for column in COLUMNS)
        lines.append(
            f"insert into public.{TABLE} ({', '.join(COLUMNS)}) values ({values})\n"
            f"  on conflict ({CONFLICT}) do update set {set_clause};"
        )
    lines.append("commit;")
    return "\n".join(lines) + "\n"


def _sql_literal(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (dict, list)):
        return "'" + json.dumps(value, ensure_ascii=False).replace("'", "''") + "'::jsonb"
    return "'" + str(value).replace("'", "''") + "'"
