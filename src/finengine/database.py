from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from .models import Company, Fact, PeriodKind, SourceCandidate, SourceDocument, TypedFact, ValueType
from .catalog import iter_catalog_fields


SCHEMA_VERSION = 12

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS companies(
 company_id TEXT PRIMARY KEY, market TEXT NOT NULL, symbol TEXT NOT NULL, name TEXT NOT NULL,
 currency TEXT NOT NULL, cik TEXT, isin TEXT, fiscal_year_end TEXT NOT NULL,
 exchange TEXT, country TEXT, sector TEXT, industry TEXT, timezone TEXT NOT NULL DEFAULT 'UTC',
 locale TEXT NOT NULL DEFAULT 'en', enabled INTEGER NOT NULL DEFAULT 1, UNIQUE(market,symbol));
CREATE TABLE IF NOT EXISTS company_sources(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 source_type TEXT NOT NULL, url TEXT NOT NULL, priority INTEGER NOT NULL DEFAULT 100,
 enabled INTEGER NOT NULL DEFAULT 1, config_json TEXT NOT NULL DEFAULT '{}', UNIQUE(company_id,url));
CREATE TABLE IF NOT EXISTS source_documents(
 source_key TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 source_url TEXT NOT NULL, filing_type TEXT NOT NULL, filed_at TEXT NOT NULL,
 content_hash TEXT NOT NULL, local_path TEXT, content_type TEXT NOT NULL DEFAULT 'application/json',
 status TEXT NOT NULL DEFAULT 'fetched', metadata_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS source_artifacts(
 artifact_key TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 source_url TEXT NOT NULL, content_hash TEXT NOT NULL, local_path TEXT NOT NULL,
 content_type TEXT NOT NULL, byte_size INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'archived',
 metadata_json TEXT NOT NULL DEFAULT '{}', archived_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id,source_url,content_hash));
CREATE INDEX IF NOT EXISTS idx_source_artifact_url ON source_artifacts(company_id,source_url);
CREATE TABLE IF NOT EXISTS source_artifact_links(
 source_key TEXT NOT NULL REFERENCES source_documents(source_key),
 artifact_key TEXT NOT NULL REFERENCES source_artifacts(artifact_key),
 PRIMARY KEY(source_key,artifact_key));
CREATE TABLE IF NOT EXISTS source_candidates(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 connector TEXT NOT NULL, external_id TEXT NOT NULL, source_url TEXT NOT NULL,
 title TEXT NOT NULL, document_type TEXT NOT NULL, published_at TEXT,
 content_type TEXT NOT NULL DEFAULT 'application/octet-stream',
 status TEXT NOT NULL DEFAULT 'discovered'
 CHECK(status IN ('discovered','queued','fetched','ignored','error')),
 metadata_json TEXT NOT NULL DEFAULT '{}', discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id,connector,external_id));
CREATE INDEX IF NOT EXISTS idx_source_candidate_status ON source_candidates(company_id,status,discovered_at);
CREATE TABLE IF NOT EXISTS metric_definitions(
 metric_key TEXT PRIMARY KEY, display_name TEXT NOT NULL, category TEXT NOT NULL,
 statement TEXT, value_type TEXT NOT NULL DEFAULT 'decimal', default_unit TEXT,
 aggregation TEXT NOT NULL DEFAULT 'none', description TEXT,
 schema_version INTEGER NOT NULL DEFAULT 1, enabled INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS data_catalog_fields(
 field_key TEXT PRIMARY KEY, display_name TEXT NOT NULL, category TEXT NOT NULL,
 storage_domain TEXT NOT NULL, statement TEXT, period_behavior TEXT NOT NULL,
 value_type TEXT NOT NULL, default_unit TEXT, aggregation TEXT NOT NULL DEFAULT 'none',
 pack_key TEXT NOT NULL, scope_type TEXT NOT NULL CHECK(scope_type IN ('all','market','sector','industry','company')),
 scope_value TEXT NOT NULL DEFAULT '*', requirement TEXT NOT NULL CHECK(requirement IN ('required','recommended','optional')),
 review_state TEXT NOT NULL DEFAULT 'reviewed' CHECK(review_state IN ('candidate','reviewed','deprecated')),
 schema_version INTEGER NOT NULL DEFAULT 3, enabled INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_catalog_scope ON data_catalog_fields(scope_type,scope_value,storage_domain,enabled);
CREATE TABLE IF NOT EXISTS company_completeness(
 company_id TEXT NOT NULL REFERENCES companies(company_id), category TEXT NOT NULL,
 expected_fields INTEGER NOT NULL, populated_fields INTEGER NOT NULL,
 completeness_score TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('complete','partial','missing','not_applicable')),
 missing_fields_json TEXT NOT NULL DEFAULT '[]', checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(company_id,category));
CREATE TABLE IF NOT EXISTS observations(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id), metric TEXT NOT NULL,
 value TEXT NOT NULL, currency TEXT NOT NULL, unit TEXT NOT NULL, period_start TEXT,
 period_end TEXT NOT NULL, period_kind TEXT NOT NULL, fiscal_year INTEGER NOT NULL,
 fiscal_quarter INTEGER, source_key TEXT NOT NULL REFERENCES source_documents(source_key),
 source_url TEXT NOT NULL, filed_at TEXT NOT NULL, accession TEXT, form TEXT,
 is_calculated INTEGER NOT NULL DEFAULT 0, calculation TEXT, version INTEGER NOT NULL,
 is_current INTEGER NOT NULL DEFAULT 1, published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id,metric,period_end,period_kind,fiscal_year,fiscal_quarter,currency,unit,version));
CREATE INDEX IF NOT EXISTS idx_observation_query ON observations(company_id,metric,is_current,period_end);
CREATE TABLE IF NOT EXISTS data_points(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 metric_key TEXT NOT NULL REFERENCES metric_definitions(metric_key), value_decimal TEXT,
 value_text TEXT, value_json TEXT, value_type TEXT NOT NULL DEFAULT 'decimal',
 currency TEXT NOT NULL DEFAULT '', unit TEXT NOT NULL DEFAULT 'pure',
 period_start TEXT NOT NULL DEFAULT '', period_end TEXT NOT NULL, period_kind TEXT NOT NULL,
 fiscal_year INTEGER NOT NULL DEFAULT 0, fiscal_quarter INTEGER NOT NULL DEFAULT 0,
 scope TEXT NOT NULL DEFAULT 'consolidated', dimensions_json TEXT NOT NULL DEFAULT '{}',
 dimensions_hash TEXT NOT NULL, source_key TEXT NOT NULL REFERENCES source_documents(source_key),
 source_url TEXT NOT NULL, filed_at TEXT NOT NULL, accession TEXT, form TEXT,
 is_calculated INTEGER NOT NULL DEFAULT 0, calculation TEXT, quality_score TEXT NOT NULL DEFAULT '1',
 metric_version INTEGER NOT NULL DEFAULT 1, version INTEGER NOT NULL, is_current INTEGER NOT NULL DEFAULT 1,
 published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id,metric_key,period_end,period_kind,fiscal_year,fiscal_quarter,currency,unit,scope,dimensions_hash,version));
CREATE INDEX IF NOT EXISTS idx_data_point_query ON data_points(company_id,metric_key,is_current,period_end,period_kind);
CREATE INDEX IF NOT EXISTS idx_data_point_dimensions ON data_points(company_id,dimensions_hash,is_current);
CREATE TABLE IF NOT EXISTS company_attributes(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 attribute_key TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'general', value_json TEXT NOT NULL,
 language TEXT NOT NULL DEFAULT 'en', effective_at TEXT NOT NULL, source_key TEXT REFERENCES source_documents(source_key),
 version INTEGER NOT NULL, is_current INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id,attribute_key,language,effective_at,version));
CREATE INDEX IF NOT EXISTS idx_company_attribute_current ON company_attributes(company_id,attribute_key,is_current);
CREATE TABLE IF NOT EXISTS disclosures(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 disclosure_type TEXT NOT NULL, title TEXT NOT NULL, body_text TEXT NOT NULL,
 language TEXT NOT NULL DEFAULT 'en', published_at TEXT NOT NULL, period_end TEXT,
 source_key TEXT REFERENCES source_documents(source_key), metadata_json TEXT NOT NULL DEFAULT '{}',
 content_hash TEXT NOT NULL, version INTEGER NOT NULL, is_current INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(company_id,disclosure_type,content_hash,version));
CREATE INDEX IF NOT EXISTS idx_disclosure_query ON disclosures(company_id,disclosure_type,is_current,published_at);
CREATE TABLE IF NOT EXISTS corporate_events(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 event_type TEXT NOT NULL, event_date TEXT NOT NULL, title TEXT NOT NULL,
 payload_json TEXT NOT NULL DEFAULT '{}', source_key TEXT REFERENCES source_documents(source_key),
 idempotency_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS securities(
 security_id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 security_type TEXT NOT NULL, name TEXT NOT NULL, isin TEXT, currency TEXT NOT NULL,
 active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id,security_type));
CREATE TABLE IF NOT EXISTS listings(
 listing_id TEXT PRIMARY KEY, security_id TEXT NOT NULL REFERENCES securities(security_id),
 market TEXT NOT NULL, exchange TEXT NOT NULL, symbol TEXT NOT NULL, currency TEXT NOT NULL,
 country TEXT, timezone TEXT NOT NULL DEFAULT 'UTC', is_primary INTEGER NOT NULL DEFAULT 0,
 active INTEGER NOT NULL DEFAULT 1, valid_from TEXT NOT NULL DEFAULT '', valid_to TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(market,symbol,valid_from));
CREATE INDEX IF NOT EXISTS idx_listing_company ON listings(security_id,is_primary,active);
CREATE TABLE IF NOT EXISTS market_prices(
 id INTEGER PRIMARY KEY, listing_id TEXT NOT NULL REFERENCES listings(listing_id),
 observed_at TEXT NOT NULL, interval TEXT NOT NULL, open TEXT, high TEXT, low TEXT,
 close TEXT NOT NULL, adjusted_close TEXT, volume TEXT, turnover TEXT, currency TEXT NOT NULL,
 source_key TEXT NOT NULL REFERENCES source_documents(source_key), version INTEGER NOT NULL,
 is_current INTEGER NOT NULL DEFAULT 1, published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(listing_id,observed_at,interval,version));
CREATE INDEX IF NOT EXISTS idx_market_price_query ON market_prices(listing_id,interval,is_current,observed_at);
CREATE TABLE IF NOT EXISTS ownership_positions(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 holder_key TEXT NOT NULL, holder_name TEXT NOT NULL, holder_type TEXT,
 ownership_type TEXT NOT NULL, as_of_date TEXT NOT NULL, shares TEXT, ownership_pct TEXT,
 country TEXT, source_key TEXT NOT NULL REFERENCES source_documents(source_key),
 metadata_json TEXT NOT NULL DEFAULT '{}', version INTEGER NOT NULL,
 is_current INTEGER NOT NULL DEFAULT 1, published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id,holder_key,ownership_type,as_of_date,version));
CREATE INDEX IF NOT EXISTS idx_ownership_query ON ownership_positions(company_id,as_of_date,is_current);
CREATE TABLE IF NOT EXISTS corporate_actions(
 id INTEGER PRIMARY KEY, action_key TEXT NOT NULL, company_id TEXT NOT NULL REFERENCES companies(company_id),
 listing_id TEXT REFERENCES listings(listing_id), action_type TEXT NOT NULL, title TEXT NOT NULL,
 announcement_date TEXT NOT NULL, ex_date TEXT, record_date TEXT, eligibility_date TEXT,
 payment_date TEXT, effective_date TEXT, cash_amount TEXT, currency TEXT,
 ratio_numerator TEXT, ratio_denominator TEXT, status TEXT NOT NULL DEFAULT 'announced',
 source_key TEXT NOT NULL REFERENCES source_documents(source_key), details_json TEXT NOT NULL DEFAULT '{}',
 version INTEGER NOT NULL, is_current INTEGER NOT NULL DEFAULT 1,
 published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(action_key,version));
CREATE INDEX IF NOT EXISTS idx_action_query ON corporate_actions(company_id,action_type,is_current,announcement_date);
CREATE TABLE IF NOT EXISTS consensus_estimates(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 metric_key TEXT NOT NULL REFERENCES metric_definitions(metric_key), target_period_end TEXT NOT NULL,
 period_kind TEXT NOT NULL CHECK(period_kind IN ('quarter','fy')),
 estimate_type TEXT NOT NULL CHECK(estimate_type IN ('low','high','mean','median')),
 value_decimal TEXT NOT NULL, currency TEXT NOT NULL DEFAULT '', unit TEXT NOT NULL DEFAULT 'pure',
 analyst_count INTEGER, estimate_as_of TEXT NOT NULL, source_key TEXT NOT NULL REFERENCES source_documents(source_key),
 metadata_json TEXT NOT NULL DEFAULT '{}', version INTEGER NOT NULL, is_current INTEGER NOT NULL DEFAULT 1,
 published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id,metric_key,target_period_end,period_kind,estimate_type,estimate_as_of,version));
CREATE INDEX IF NOT EXISTS idx_consensus_query ON consensus_estimates(company_id,metric_key,is_current,target_period_end,estimate_as_of);
CREATE TABLE IF NOT EXISTS calculation_definitions(
 metric_key TEXT NOT NULL REFERENCES metric_definitions(metric_key), formula_version INTEGER NOT NULL,
 expression TEXT NOT NULL, output_unit TEXT, period_rule TEXT NOT NULL DEFAULT 'same_period',
 description TEXT, enabled INTEGER NOT NULL DEFAULT 1, is_current INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(metric_key,formula_version));
CREATE TABLE IF NOT EXISTS calculation_dependencies(
 metric_key TEXT NOT NULL, formula_version INTEGER NOT NULL, dependency_metric TEXT NOT NULL REFERENCES metric_definitions(metric_key),
 role TEXT NOT NULL DEFAULT 'input', PRIMARY KEY(metric_key,formula_version,dependency_metric),
 FOREIGN KEY(metric_key,formula_version) REFERENCES calculation_definitions(metric_key,formula_version));
CREATE TABLE IF NOT EXISTS metric_applicability(
 id INTEGER PRIMARY KEY, metric_key TEXT NOT NULL REFERENCES metric_definitions(metric_key),
 scope_type TEXT NOT NULL CHECK(scope_type IN ('all','market','sector','industry','company')),
 scope_value TEXT NOT NULL DEFAULT '*', period_kind TEXT NOT NULL DEFAULT '*',
 requirement TEXT NOT NULL CHECK(requirement IN ('required','recommended','optional')),
 enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(metric_key,scope_type,scope_value,period_kind));
CREATE INDEX IF NOT EXISTS idx_metric_applicability ON metric_applicability(scope_type,scope_value,period_kind,enabled);
CREATE TABLE IF NOT EXISTS freshness_policies(
 id INTEGER PRIMARY KEY, scope_type TEXT NOT NULL CHECK(scope_type IN ('all','market','sector','industry','company')),
 scope_value TEXT NOT NULL DEFAULT '*', domain TEXT NOT NULL, max_age_seconds INTEGER NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(scope_type,scope_value,domain));
CREATE TABLE IF NOT EXISTS coverage_status(
 id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id),
 period_end TEXT NOT NULL, period_kind TEXT NOT NULL, domain TEXT NOT NULL,
 expected_count INTEGER NOT NULL, available_count INTEGER NOT NULL, required_missing_json TEXT NOT NULL DEFAULT '[]',
 status TEXT NOT NULL CHECK(status IN ('complete','partial','missing','not_applicable')),
 quality_score TEXT NOT NULL DEFAULT '0', latest_source_at TEXT,
 freshness_status TEXT NOT NULL DEFAULT 'unknown' CHECK(freshness_status IN ('unknown','fresh','stale')),
 age_seconds INTEGER, checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 notes TEXT, UNIQUE(company_id,period_end,period_kind,domain));
CREATE INDEX IF NOT EXISTS idx_coverage_query ON coverage_status(company_id,period_end,period_kind,domain);
CREATE TABLE IF NOT EXISTS exceptions(
 id INTEGER PRIMARY KEY, company_id TEXT, source_key TEXT, stage TEXT NOT NULL,
 code TEXT NOT NULL, message TEXT NOT NULL, payload_json TEXT NOT NULL DEFAULT '{}',
 severity TEXT NOT NULL DEFAULT 'error', status TEXT NOT NULL DEFAULT 'open', assigned_to TEXT,
 resolution TEXT, retry_count INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT);
CREATE TABLE IF NOT EXISTS pipeline_runs(
 run_id TEXT PRIMARY KEY, company_id TEXT NOT NULL, job_id TEXT, source_key TEXT,
 started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, finished_at TEXT, status TEXT NOT NULL,
 stage TEXT, checkpoint_json TEXT NOT NULL DEFAULT '{}', stats_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS monitor_state(
 company_id TEXT NOT NULL, connector TEXT NOT NULL, cursor TEXT, last_checked_at TEXT,
 last_success_at TEXT, error_count INTEGER NOT NULL DEFAULT 0, last_error TEXT,
 PRIMARY KEY(company_id,connector));
CREATE TABLE IF NOT EXISTS schedules(
 schedule_id TEXT PRIMARY KEY, name TEXT NOT NULL, job_type TEXT NOT NULL,
 company_id TEXT REFERENCES companies(company_id), payload_json TEXT NOT NULL DEFAULT '{}',
 interval_seconds INTEGER NOT NULL, priority INTEGER NOT NULL DEFAULT 100,
 next_run_at TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS jobs(
 job_id TEXT PRIMARY KEY, job_type TEXT NOT NULL, company_id TEXT REFERENCES companies(company_id),
 source_key TEXT, payload_json TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'queued'
 CHECK(status IN ('queued','running','succeeded','failed','dead','cancelled')),
 priority INTEGER NOT NULL DEFAULT 100, available_at TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
 max_attempts INTEGER NOT NULL DEFAULT 5, leased_by TEXT, lease_until TEXT, idempotency_key TEXT NOT NULL UNIQUE,
 last_error TEXT, result_json TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, finished_at TEXT);
CREATE INDEX IF NOT EXISTS idx_jobs_claim ON jobs(status,available_at,priority,created_at);
CREATE TABLE IF NOT EXISTS backlog_items(
 backlog_id TEXT PRIMARY KEY, company_id TEXT REFERENCES companies(company_id),
 item_type TEXT NOT NULL, domain TEXT NOT NULL DEFAULT 'all', title TEXT NOT NULL,
 description TEXT, period_end TEXT, period_kind TEXT, metric_key TEXT,
 source_url TEXT, priority INTEGER NOT NULL DEFAULT 100,
 status TEXT NOT NULL DEFAULT 'open'
 CHECK(status IN ('open','ready','in_progress','blocked','completed','cancelled')),
 payload_json TEXT NOT NULL DEFAULT '{}', idempotency_key TEXT NOT NULL UNIQUE,
 job_id TEXT REFERENCES jobs(job_id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT);
CREATE INDEX IF NOT EXISTS idx_backlog_work ON backlog_items(status,priority,created_at);
CREATE INDEX IF NOT EXISTS idx_backlog_company ON backlog_items(company_id,domain,status,period_end);
CREATE TABLE IF NOT EXISTS job_attempts(
 id INTEGER PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(job_id), attempt_number INTEGER NOT NULL,
 worker_id TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL,
 error TEXT, UNIQUE(job_id,attempt_number));
CREATE TABLE IF NOT EXISTS workers(
 worker_id TEXT PRIMARY KEY, capabilities_json TEXT NOT NULL DEFAULT '[]',
 started_at TEXT NOT NULL, heartbeat_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'online');
CREATE TABLE IF NOT EXISTS extracted_facts(
 id INTEGER PRIMARY KEY, source_key TEXT NOT NULL REFERENCES source_documents(source_key), company_id TEXT NOT NULL REFERENCES companies(company_id),
 raw_label TEXT NOT NULL, raw_value TEXT NOT NULL, raw_currency TEXT NOT NULL, raw_unit TEXT NOT NULL, scale TEXT NOT NULL,
 period_start TEXT, period_end TEXT NOT NULL, period_kind TEXT NOT NULL, fiscal_year INTEGER NOT NULL, fiscal_quarter INTEGER,
 accession TEXT, form TEXT, page INTEGER, table_ref TEXT, location_json TEXT NOT NULL DEFAULT '{}',
 scope TEXT NOT NULL DEFAULT 'consolidated', dimensions_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS mapped_facts(
 id INTEGER PRIMARY KEY, extracted_fact_id INTEGER NOT NULL REFERENCES extracted_facts(id), canonical_metric TEXT,
 confidence TEXT NOT NULL, mapping_method TEXT NOT NULL, reason TEXT, status TEXT NOT NULL CHECK(status IN ('accepted','review')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS normalized_facts(
 id INTEGER PRIMARY KEY, mapped_fact_id INTEGER NOT NULL REFERENCES mapped_facts(id), normalized_value TEXT NOT NULL,
 currency TEXT NOT NULL, unit TEXT NOT NULL, period_start TEXT, period_end TEXT NOT NULL, period_kind TEXT NOT NULL,
 fiscal_year INTEGER NOT NULL, fiscal_quarter INTEGER, scope TEXT NOT NULL DEFAULT 'consolidated',
 dimensions_json TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'staged' CHECK(status IN ('staged','validated','rejected','published')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS validation_results(
 id INTEGER PRIMARY KEY, source_key TEXT NOT NULL REFERENCES source_documents(source_key), company_id TEXT NOT NULL,
 rule_code TEXT NOT NULL, severity TEXT NOT NULL, passed INTEGER NOT NULL, message TEXT NOT NULL, payload_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS publication_batches(
 id INTEGER PRIMARY KEY, source_key TEXT NOT NULL REFERENCES source_documents(source_key), company_id TEXT NOT NULL,
 status TEXT NOT NULL, staged_count INTEGER NOT NULL, published_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""


DEFAULT_METRICS = {
    "revenue": ("Revenue", "financial", "income_statement", "sum", "currency"),
    "other_income_related_to_sales": ("Other income related to sales", "financial", "income_statement", "sum", "currency"),
    "revenue_and_other_income_related_to_sales": ("Revenue and other income related to sales", "financial", "income_statement", "sum", "currency"),
    "operating_costs": ("Operating costs", "financial", "income_statement", "sum", "currency"),
    "operating_income": ("Operating income", "financial", "income_statement", "sum", "currency"),
    "income_before_income_taxes_and_zakat": ("Income before income taxes and zakat", "financial", "income_statement", "sum", "currency"),
    "income_taxes_and_zakat": ("Income taxes and zakat", "financial", "income_statement", "sum", "currency"),
    "net_income": ("Net income", "financial", "income_statement", "sum", "currency"),
    "adjusted_net_income": ("Adjusted net income", "financial", "income_statement", "sum", "currency"),
    "net_income_parent": ("Net income attributable to parent", "financial", "income_statement", "sum", "currency"),
    "total_assets": ("Total assets", "financial", "balance_sheet", "last", "currency"),
    "total_liabilities": ("Total liabilities", "financial", "balance_sheet", "last", "currency"),
    "total_equity": ("Total equity", "financial", "balance_sheet", "last", "currency"),
    "cash": ("Cash and cash equivalents", "financial", "balance_sheet", "last", "currency"),
    "operating_cash_flow": ("Operating cash flow", "financial", "cash_flow", "sum", "currency"),
    "capex": ("Capital expenditure", "financial", "cash_flow", "sum", "currency"),
    "dividends_paid": ("Dividends paid", "financial", "cash_flow", "sum", "currency"),
    "base_dividends_paid": ("Base dividends paid", "financial", "cash_flow", "sum", "currency"),
    "performance_linked_dividends_paid": ("Performance-linked dividends paid", "financial", "cash_flow", "sum", "currency"),
    "dividends_per_share": ("Dividends paid per share", "financial", "per_share", "none", "currency/share"),
    "eps_diluted": ("Diluted earnings per share", "financial", "per_share", "none", "currency/share"),
    "share_capital": ("Share capital", "financial", "balance_sheet", "last", "currency"),
    "current_debt": ("Current debt", "financial", "balance_sheet", "last", "currency"),
    "long_term_debt": ("Long-term debt", "financial", "balance_sheet", "last", "currency"),
    "average_realized_crude_oil_price": ("Average realized crude oil price", "operational", "market_driver", "average", "USD/bbl"),
    "total_hydrocarbon_production": ("Total hydrocarbon production", "operational", "production", "average", "mmboed"),
    "total_liquids_production": ("Total liquids production", "operational", "production", "average", "mmbpd"),
    "total_gas_production": ("Total gas production", "operational", "production", "average", "bscfd"),
    "total_hydrocarbon_reserves": ("Total hydrocarbon reserves", "operational", "reserves", "last", "billion_boe"),
    "maximum_sustainable_capacity": ("Maximum sustainable capacity", "operational", "capacity", "last", "mmbpd"),
    "net_refining_capacity": ("Net refining capacity", "operational", "capacity", "last", "mmbpd"),
    "net_chemicals_production_capacity": ("Net chemicals production capacity", "operational", "capacity", "last", "million_tonnes_per_year"),
    "supply_reliability": ("Supply reliability", "operational", "reliability", "average", "percent"),
    "free_cash_flow": ("Free cash flow", "calculated", "cash_flow", "sum", "currency"),
    "net_margin": ("Net margin", "ratio", "ratios", "none", "ratio"),
    "liabilities_to_equity": ("Liabilities to equity", "ratio", "ratios", "none", "ratio"),
    "roace": ("Return on average capital employed", "ratio", "ratios", "none", "percent"),
    "gearing": ("Gearing", "ratio", "ratios", "none", "percent"),
}


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _dimensions(value: dict[str, str]) -> tuple[str, str]:
    encoded = _json(value)
    return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _typed_value(value, value_type: ValueType) -> tuple[str | None, str | None, str | None]:
    if value_type == ValueType.DECIMAL:
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError("decimal facts must be finite")
        return str(number), None, None
    if value_type == ValueType.TEXT:
        return None, str(value), None
    if value_type == ValueType.DATE:
        parsed = date.fromisoformat(str(value))
        return None, parsed.isoformat(), None
    if value_type == ValueType.BOOLEAN:
        if not isinstance(value, bool):
            raise TypeError("boolean facts require a bool value")
        return None, "true" if value else "false", None
    if value_type == ValueType.JSON:
        if not isinstance(value, (dict, list)):
            raise TypeError("json facts require a dict or list value")
        return None, None, _json(value)
    raise ValueError(f"unsupported value type: {value_type}")


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        if self.path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self._migrate_legacy_schema()
        self._seed_metric_catalog()
        self._seed_data_catalog()
        self._seed_calculation_definitions()
        self._seed_metric_applicability()
        self._backfill_data_points()
        self._backfill_company_entities()

    def _columns(self, table: str) -> set[str]:
        return {row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})")}

    def _ensure_column(self, table: str, name: str, definition: str) -> None:
        if name not in self._columns(table):
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def _migrate_legacy_schema(self) -> None:
        for name, definition in {
            "exchange": "TEXT", "country": "TEXT", "sector": "TEXT", "industry": "TEXT",
            "timezone": "TEXT NOT NULL DEFAULT 'UTC'", "locale": "TEXT NOT NULL DEFAULT 'en'",
            "enabled": "INTEGER NOT NULL DEFAULT 1",
        }.items():
            self._ensure_column("companies", name, definition)
        self._ensure_column("source_documents", "content_type", "TEXT NOT NULL DEFAULT 'application/json'")
        for name, definition in {
            "severity": "TEXT NOT NULL DEFAULT 'error'", "assigned_to": "TEXT", "resolution": "TEXT",
            "retry_count": "INTEGER NOT NULL DEFAULT 0", "updated_at": "TEXT",
        }.items():
            self._ensure_column("exceptions", name, definition)
        for name, definition in {
            "job_id": "TEXT", "source_key": "TEXT", "stage": "TEXT",
            "checkpoint_json": "TEXT NOT NULL DEFAULT '{}'",
        }.items():
            self._ensure_column("pipeline_runs", name, definition)
        for name, definition in {
            "last_success_at": "TEXT", "error_count": "INTEGER NOT NULL DEFAULT 0", "last_error": "TEXT",
        }.items():
            self._ensure_column("monitor_state", name, definition)
        for name, definition in {
            "freshness_status": "TEXT NOT NULL DEFAULT 'unknown'", "age_seconds": "INTEGER",
        }.items():
            self._ensure_column("coverage_status", name, definition)
        for table in ("extracted_facts", "normalized_facts"):
            self._ensure_column(table, "scope", "TEXT NOT NULL DEFAULT 'consolidated'")
            self._ensure_column(table, "dimensions_json", "TEXT NOT NULL DEFAULT '{}'")
        # Ratio outputs are dimensionless. Older databases inherited the source currency
        # from their input fact, which made bot/report formatting misleading.
        self.conn.execute(
            "UPDATE observations SET currency='',unit='ratio' "
            "WHERE is_calculated=1 AND metric IN ('net_margin','liabilities_to_equity')"
        )
        self.conn.execute(
            "UPDATE data_points SET currency='',unit='ratio' "
            "WHERE is_calculated=1 AND metric_key IN ('net_margin','liabilities_to_equity')"
        )
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES(?)", (SCHEMA_VERSION,))
        self.conn.commit()

    def _seed_metric_catalog(self) -> None:
        for key, (name, category, statement, aggregation, default_unit) in DEFAULT_METRICS.items():
            self.register_metric(
                key, name, category, statement, default_unit=default_unit,
                aggregation=aggregation, commit=False,
            )
        self.conn.commit()

    def _seed_data_catalog(self) -> None:
        metric_categories = {
            "income_statement": "financial", "balance_sheet": "financial", "cash_flow": "financial",
            "per_share": "financial", "segments": "operational", "oil_gas_operations": "operational",
            "profitability": "ratio", "liquidity_solvency": "ratio", "efficiency": "ratio",
            "growth": "calculated", "valuation": "calculated", "financial_notes": "financial",
            "commercial_pipeline": "commercial", "investor_analytics": "calculated", "consensus": "consensus",
        }
        for item in iter_catalog_fields():
            self.conn.execute(
                """INSERT INTO data_catalog_fields(field_key,display_name,category,storage_domain,statement,
                period_behavior,value_type,default_unit,aggregation,pack_key,scope_type,scope_value,requirement,schema_version)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,4) ON CONFLICT(field_key) DO UPDATE SET
                display_name=excluded.display_name,category=excluded.category,storage_domain=excluded.storage_domain,
                statement=excluded.statement,period_behavior=excluded.period_behavior,value_type=excluded.value_type,
                default_unit=excluded.default_unit,aggregation=excluded.aggregation,pack_key=excluded.pack_key,
                scope_type=excluded.scope_type,scope_value=excluded.scope_value,requirement=excluded.requirement,
                schema_version=4,updated_at=CURRENT_TIMESTAMP""",
                tuple(item[key] for key in ("field_key","display_name","category","storage_domain","statement",
                    "period_behavior","value_type","default_unit","aggregation","pack_key","scope_type",
                    "scope_value","requirement")),
            )
            if item["storage_domain"] in {"data_points", "consensus_estimates"}:
                self.register_metric(
                    item["field_key"], item["display_name"], metric_categories[item["category"]],
                    item["statement"], "decimal", item["default_unit"], item["aggregation"],
                    f"Reviewed {item['pack_key']} catalog field", schema_version=3, commit=False,
                )
        self.conn.commit()

    def _seed_calculation_definitions(self) -> None:
        # Market prices live in their own versioned store, but point-in-time
        # formula lineage still references the canonical close-price key.
        self.register_metric("price_close", category="market", aggregation="last", commit=False)
        definitions = {
            "free_cash_flow": ("operating_cash_flow - abs(capex)", "same_period", ("operating_cash_flow", "capex")),
            "net_margin": ("net_income / revenue", "same_period", ("net_income", "revenue")),
            "liabilities_to_equity": ("total_liabilities / total_equity", "same_period", ("total_liabilities", "total_equity")),
            "operating_margin": ("operating_income / revenue", "same_period", ("operating_income", "revenue")),
            "pretax_margin": ("income_before_income_taxes_and_zakat / revenue", "same_period", ("income_before_income_taxes_and_zakat", "revenue")),
            "effective_tax_rate": ("abs(income_taxes_and_zakat) / income_before_income_taxes_and_zakat", "same_period", ("income_taxes_and_zakat", "income_before_income_taxes_and_zakat")),
            "cfo_margin": ("operating_cash_flow / revenue", "same_period", ("operating_cash_flow", "revenue")),
            "fcf_margin": ("free_cash_flow / revenue", "same_period", ("free_cash_flow", "revenue")),
            "liabilities_to_assets": ("total_liabilities / total_assets", "same_period", ("total_liabilities", "total_assets")),
            "equity_ratio": ("total_equity / total_assets", "same_period", ("total_equity", "total_assets")),
            "current_ratio": ("current_assets / current_liabilities", "same_period", ("current_assets", "current_liabilities")),
            "cash_ratio": ("cash / current_liabilities", "same_period", ("cash", "current_liabilities")),
            "debt_to_equity": ("(current_debt + long_term_debt) / total_equity", "same_period", ("current_debt", "long_term_debt", "total_equity")),
            "debt_to_assets": ("(current_debt + long_term_debt) / total_assets", "same_period", ("current_debt", "long_term_debt", "total_assets")),
            "capex_to_revenue": ("abs(capex) / revenue", "same_period", ("capex", "revenue")),
            "capex_to_cfo": ("abs(capex) / operating_cash_flow", "same_period", ("capex", "operating_cash_flow")),
            "receivables_to_revenue": ("accounts_receivable / revenue", "same_period", ("accounts_receivable", "revenue")),
            "inventory_to_assets": ("inventory / total_assets", "same_period", ("inventory", "total_assets")),
            "ppe_to_assets": ("property_plant_equipment / total_assets", "same_period", ("property_plant_equipment", "total_assets")),
            "return_on_assets": ("net_income / average(total_assets)", "annual_average_balance", ("net_income", "total_assets")),
            "return_on_equity": ("net_income / average(total_equity)", "annual_average_balance", ("net_income", "total_equity")),
            "asset_turnover": ("revenue / average(total_assets)", "annual_average_balance", ("revenue", "total_assets")),
            "ebitda": ("ebit + abs(depreciation_amortization)", "same_period", ("ebit", "depreciation_amortization")),
            "ebit_margin": ("ebit / revenue", "same_period", ("ebit", "revenue")),
            "ebitda_margin": ("ebitda / revenue", "same_period", ("ebitda", "revenue")),
            "interest_coverage": ("ebit / abs(finance_costs)", "same_period", ("ebit", "finance_costs")),
            "quick_ratio": ("(cash + short_term_investments + accounts_receivable) / current_liabilities", "same_period", ("cash", "short_term_investments", "accounts_receivable", "current_liabilities")),
            "net_debt_to_equity": ("(current_debt + long_term_debt - cash) / total_equity", "same_period", ("current_debt", "long_term_debt", "cash", "total_equity")),
            "invested_capital": ("total_equity + current_debt + long_term_debt - cash", "same_period", ("total_equity", "current_debt", "long_term_debt", "cash")),
            "working_capital": ("current_assets - current_liabilities", "same_period", ("current_assets", "current_liabilities")),
            "tangible_book_value": ("total_equity - intangible_assets", "same_period", ("total_equity", "intangible_assets")),
            "book_value_per_share": ("total_equity / shares_outstanding", "same_period", ("total_equity", "shares_outstanding")),
            "tangible_book_value_per_share": ("(total_equity - intangible_assets) / shares_outstanding", "same_period", ("total_equity", "intangible_assets", "shares_outstanding")),
            "cash_return_on_assets": ("operating_cash_flow / average(total_assets)", "annual_average_balance", ("operating_cash_flow", "total_assets")),
            "receivables_turnover": ("revenue / average(accounts_receivable)", "annual_average_balance", ("revenue", "accounts_receivable")),
            "days_sales_outstanding": ("average(accounts_receivable) / revenue * 365", "annual_average_balance", ("revenue", "accounts_receivable")),
            "debt_to_ebitda": ("(current_debt + long_term_debt) / ebitda", "same_period", ("current_debt", "long_term_debt", "ebitda")),
            "net_debt_to_ebitda": ("net_debt / ebitda", "same_period", ("net_debt", "ebitda")),
            "revenue_per_share": ("revenue / weighted_average_shares_diluted", "same_period", ("revenue", "weighted_average_shares_diluted")),
            "operating_cash_flow_per_share": ("operating_cash_flow / weighted_average_shares_diluted", "same_period", ("operating_cash_flow", "weighted_average_shares_diluted")),
            "free_cash_flow_per_share": ("free_cash_flow / weighted_average_shares_diluted", "same_period", ("free_cash_flow", "weighted_average_shares_diluted")),
            "earnings_per_share_normalized": ("adjusted_net_income / weighted_average_shares_diluted", "same_period", ("adjusted_net_income", "weighted_average_shares_diluted")),
            "market_cap": ("price_close * shares_outstanding", "latest_archived_market_price", ("price_close", "shares_outstanding")),
            "enterprise_value": ("market_cap + net_debt", "latest_archived_market_price", ("market_cap", "net_debt")),
            "price_to_earnings": ("market_cap / latest_filed_fy(net_income)", "point_in_time", ("market_cap", "net_income")),
            "price_to_sales": ("market_cap / latest_filed_fy(revenue)", "point_in_time", ("market_cap", "revenue")),
            "price_to_book": ("market_cap / latest_filed(total_equity)", "point_in_time", ("market_cap", "total_equity")),
            "price_to_tangible_book": ("market_cap / latest_filed(tangible_book_value)", "point_in_time", ("market_cap", "tangible_book_value")),
            "price_to_cash_flow": ("market_cap / latest_filed_fy(operating_cash_flow)", "point_in_time", ("market_cap", "operating_cash_flow")),
            "price_to_free_cash_flow": ("market_cap / latest_filed_fy(free_cash_flow)", "point_in_time", ("market_cap", "free_cash_flow")),
            "enterprise_value_to_revenue": ("enterprise_value / latest_filed_fy(revenue)", "point_in_time", ("enterprise_value", "revenue")),
            "enterprise_value_to_ebit": ("enterprise_value / latest_filed_fy(ebit)", "point_in_time", ("enterprise_value", "ebit")),
            "enterprise_value_to_ebitda": ("enterprise_value / latest_filed_fy(ebitda)", "point_in_time", ("enterprise_value", "ebitda")),
            "earnings_yield": ("latest_filed_fy(net_income) / market_cap", "point_in_time", ("net_income", "market_cap")),
            "fcf_yield": ("latest_filed_fy(free_cash_flow) / market_cap", "point_in_time", ("free_cash_flow", "market_cap")),
            "dividend_yield": ("abs(latest_filed_fy(dividends_paid)) / market_cap", "point_in_time", ("dividends_paid", "market_cap")),
            "graham_number": ("sqrt(22.5 * latest_filed_fy(eps) * latest_filed(book_value_per_share))", "point_in_time", ("eps_diluted", "book_value_per_share")),
            "income_quality": ("operating_cash_flow / net_income", "same_period", ("operating_cash_flow", "net_income")),
            "payout_ratio": ("abs(dividends_paid) / net_income", "same_period", ("dividends_paid", "net_income")),
            "capex_to_depreciation": ("abs(capex) / abs(depreciation_amortization)", "same_period", ("capex", "depreciation_amortization")),
            "selling_general_administrative_to_revenue": ("selling_general_administrative_expense / revenue", "same_period", ("selling_general_administrative_expense", "revenue")),
            "research_development_to_revenue": ("research_and_development_expense / revenue", "same_period", ("research_and_development_expense", "revenue")),
            "share_based_compensation_to_revenue": ("share_based_compensation / revenue", "same_period", ("share_based_compensation", "revenue")),
            "cash_per_share": ("cash / weighted_average_shares", "same_period", ("cash", "weighted_average_shares_diluted")),
            "capex_per_share": ("abs(capex) / weighted_average_shares", "same_period", ("capex", "weighted_average_shares_diluted")),
            "debt_per_share": ("(current_debt + long_term_debt) / weighted_average_shares", "same_period", ("current_debt", "long_term_debt", "weighted_average_shares_diluted")),
            "ebitda_per_share": ("ebitda / weighted_average_shares", "same_period", ("ebitda", "weighted_average_shares_diluted")),
            "net_current_asset_value": ("current_assets - total_liabilities", "same_period", ("current_assets", "total_liabilities")),
            "graham_net_net": ("cash + 0.75 * accounts_receivable + 0.5 * inventory - total_liabilities", "same_period", ("cash", "accounts_receivable", "inventory", "total_liabilities")),
            "return_on_tangible_equity": ("net_income / average(total_equity - intangible_assets)", "annual_average_balance", ("net_income", "total_equity", "intangible_assets")),
            "reserve_life_index": (
                "total_hydrocarbon_reserves * 1000 / (total_hydrocarbon_production * 365)",
                "same_fiscal_year_reserves_and_average_daily_production",
                ("total_hydrocarbon_reserves", "total_hydrocarbon_production"),
            ),
        }
        growth_sources = {
            "revenue_growth": "revenue", "gross_profit_growth": "gross_profit",
            "operating_income_growth": "operating_income", "net_income_growth": "net_income",
            "eps_growth": "eps_diluted", "asset_growth": "total_assets",
            "equity_growth": "total_equity", "operating_cash_flow_growth": "operating_cash_flow",
            "free_cash_flow_growth": "free_cash_flow",
            "ebitda_growth": "ebitda", "dividend_growth": "dividends_paid",
        }
        definitions.update({
            output: (f"{source} / prior_fy({source}) - 1", "prior_fiscal_year", (source,))
            for output, source in growth_sources.items()
        })
        for source in ("revenue", "net_income", "eps_diluted"):
            prefix = "eps" if source == "eps_diluted" else source
            for years in (3, 5):
                definitions[f"{prefix}_cagr_{years}y"] = (
                    f"({source} / prior_{years}y({source})) ^ (1/{years}) - 1",
                    f"prior_{years}_fiscal_years", (source,),
                )
        for metric, (expression, period_rule, dependencies) in definitions.items():
            self.conn.execute(
                """INSERT OR IGNORE INTO calculation_definitions(metric_key,formula_version,expression,period_rule)
                VALUES(?,1,?,?)""", (metric, expression, period_rule))
            for dependency in dependencies:
                self.conn.execute(
                    """INSERT OR IGNORE INTO calculation_dependencies(metric_key,formula_version,dependency_metric)
                    VALUES(?,1,?)""", (metric, dependency))
        for base in ("revenue", "net_income", "operating_cash_flow", "capex", "free_cash_flow"):
            metric = f"{base}_ttm"
            self.register_metric(metric, category="calculated", aggregation="sum", commit=False)
            self.conn.execute(
                """INSERT OR IGNORE INTO calculation_definitions(metric_key,formula_version,expression,period_rule)
                VALUES(?,1,?,'last_4_discrete_quarters')""", (metric, f"sum(last_4_quarters({base}))"))
            self.conn.execute(
                """INSERT OR IGNORE INTO calculation_dependencies(metric_key,formula_version,dependency_metric)
                VALUES(?,1,?)""", (metric, base))
        self.conn.commit()

    def _seed_metric_applicability(self) -> None:
        policies = (
            ("revenue", "fy", "required"), ("net_income", "fy", "required"),
            ("operating_cash_flow", "fy", "recommended"), ("capex", "fy", "recommended"),
            ("revenue", "quarter", "required"), ("net_income", "quarter", "required"),
            ("revenue", "ytd", "required"), ("net_income", "ytd", "required"),
            ("total_assets", "instant", "required"), ("total_liabilities", "instant", "required"),
            ("total_equity", "instant", "required"), ("cash", "instant", "recommended"),
        )
        self.conn.executemany(
            """INSERT OR IGNORE INTO metric_applicability(metric_key,scope_type,scope_value,period_kind,requirement)
            VALUES(?,'all','*',?,?)""", policies)
        integrated_oil_and_gas = (
            ("other_income_related_to_sales", "fy", "recommended"),
            ("revenue_and_other_income_related_to_sales", "fy", "recommended"),
            ("operating_costs", "fy", "recommended"),
            ("operating_income", "fy", "recommended"),
            ("income_before_income_taxes_and_zakat", "fy", "recommended"),
            ("income_taxes_and_zakat", "fy", "recommended"),
            ("net_income_parent", "fy", "recommended"),
            ("adjusted_net_income", "fy", "optional"),
            ("dividends_paid", "fy", "recommended"),
            ("base_dividends_paid", "fy", "recommended"),
            ("performance_linked_dividends_paid", "fy", "recommended"),
            ("dividends_per_share", "fy", "recommended"),
            ("eps_diluted", "fy", "recommended"),
            ("average_realized_crude_oil_price", "fy", "recommended"),
            ("roace", "fy", "recommended"),
            ("total_hydrocarbon_production", "fy", "recommended"),
            ("total_liquids_production", "fy", "recommended"),
            ("total_gas_production", "fy", "recommended"),
            ("supply_reliability", "fy", "recommended"),
            ("gearing", "instant", "recommended"),
            ("total_hydrocarbon_reserves", "instant", "recommended"),
            ("maximum_sustainable_capacity", "instant", "recommended"),
            ("net_refining_capacity", "instant", "recommended"),
            ("net_chemicals_production_capacity", "instant", "recommended"),
        )
        self.conn.executemany(
            """INSERT OR IGNORE INTO metric_applicability(metric_key,scope_type,scope_value,period_kind,requirement)
            VALUES(?,'industry','Integrated Oil & Gas',?,?)""", integrated_oil_and_gas)
        self.conn.commit()

    def _backfill_company_entities(self) -> None:
        rows = self.conn.execute("SELECT * FROM companies").fetchall()
        for row in rows:
            self._register_security_listing(
                row["company_id"], row["name"], row["isin"], row["currency"], row["market"],
                row["exchange"] or row["market"], row["symbol"], row["country"], row["timezone"],
            )
        if rows:
            self.conn.commit()

    def _register_security_listing(self, company_id: str, company_name: str, isin: str | None,
                                   currency: str, market: str, exchange: str, symbol: str,
                                   country: str | None, timezone: str) -> tuple[str, str]:
        security_id = f"security:{company_id}:common"
        listing_id = f"listing:{market}:{symbol}"
        self.conn.execute(
            """INSERT INTO securities(security_id,company_id,security_type,name,isin,currency)
            VALUES(?,?,'common_stock',?,?,?) ON CONFLICT(security_id) DO UPDATE SET
            name=excluded.name,isin=excluded.isin,currency=excluded.currency,active=1""",
            (security_id, company_id, company_name, isin, currency))
        self.conn.execute(
            """INSERT INTO listings(listing_id,security_id,market,exchange,symbol,currency,country,timezone,is_primary)
            VALUES(?,?,?,?,?,?,?,?,1) ON CONFLICT(listing_id) DO UPDATE SET exchange=excluded.exchange,
            symbol=excluded.symbol,currency=excluded.currency,country=excluded.country,
            timezone=excluded.timezone,is_primary=1,active=1""",
            (listing_id, security_id, market, exchange, symbol, currency, country, timezone))
        return security_id, listing_id

    def _backfill_data_points(self) -> None:
        rows = self.conn.execute(
            "SELECT o.* FROM observations o LEFT JOIN data_points d ON d.company_id=o.company_id "
            "AND d.metric_key=o.metric AND d.period_end=o.period_end AND d.period_kind=o.period_kind "
            "AND d.version=o.version WHERE d.id IS NULL"
        ).fetchall()
        dimensions_json, dimensions_hash = _dimensions({})
        for row in rows:
            self.register_metric(row["metric"], row["metric"].replace("_", " ").title(), commit=False)
            self.conn.execute(
                """INSERT OR IGNORE INTO data_points(company_id,metric_key,value_decimal,value_type,currency,unit,
                period_start,period_end,period_kind,fiscal_year,fiscal_quarter,scope,dimensions_json,dimensions_hash,
                source_key,source_url,filed_at,accession,form,is_calculated,calculation,version,is_current,published_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (row["company_id"], row["metric"], row["value"], "decimal", row["currency"], row["unit"],
                 row["period_start"] or "", row["period_end"], row["period_kind"], row["fiscal_year"],
                 row["fiscal_quarter"] or 0, "consolidated", dimensions_json, dimensions_hash, row["source_key"],
                 row["source_url"], row["filed_at"], row["accession"], row["form"], row["is_calculated"],
                 row["calculation"], row["version"], row["is_current"], row["published_at"]),
            )
        if rows:
            self.conn.commit()

    def close(self):
        self.conn.close()

    def register_company(self, c: Company):
        self.conn.execute(
            """INSERT INTO companies(company_id,market,symbol,name,currency,cik,isin,fiscal_year_end,
            exchange,country,sector,industry,timezone,locale,enabled) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(company_id) DO UPDATE SET market=excluded.market,symbol=excluded.symbol,
            name=excluded.name,currency=excluded.currency,cik=excluded.cik,isin=excluded.isin,
            fiscal_year_end=excluded.fiscal_year_end,exchange=excluded.exchange,country=excluded.country,
            sector=excluded.sector,industry=excluded.industry,timezone=excluded.timezone,
            locale=excluded.locale,enabled=excluded.enabled""",
            (c.company_id, c.market.value, c.symbol, c.name, c.currency, c.cik, c.isin, c.fiscal_year_end,
             c.exchange, c.country, c.sector, c.industry, c.timezone, c.locale, int(c.enabled)),
        )
        for url in c.sources:
            self.conn.execute(
                "INSERT INTO company_sources(company_id,source_type,url) VALUES(?,?,?) "
                "ON CONFLICT(company_id,url) DO UPDATE SET enabled=1", (c.company_id, "issuer", url))
        self._register_security_listing(c.company_id, c.name, c.isin, c.currency, c.market.value,
                                        c.exchange or c.market.value, c.symbol, c.country, c.timezone)
        self.conn.commit()

    def register_metric(self, metric_key: str, display_name: str | None = None, category: str = "financial",
                        statement: str | None = None, value_type: str = "decimal",
                        default_unit: str | None = None, aggregation: str = "none",
                        description: str | None = None, schema_version: int = 1,
                        commit: bool = True) -> None:
        self.conn.execute(
            """INSERT INTO metric_definitions(metric_key,display_name,category,statement,value_type,
            default_unit,aggregation,description,schema_version) VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(metric_key) DO UPDATE SET display_name=metric_definitions.display_name,
            category=metric_definitions.category,statement=COALESCE(metric_definitions.statement,excluded.statement),
            value_type=excluded.value_type,default_unit=COALESCE(excluded.default_unit,metric_definitions.default_unit),
            aggregation=excluded.aggregation,description=COALESCE(excluded.description,metric_definitions.description),
            schema_version=MAX(metric_definitions.schema_version,excluded.schema_version),updated_at=CURRENT_TIMESTAMP""",
            (metric_key, display_name or metric_key.replace("_", " ").title(), category, statement,
             value_type, default_unit, aggregation, description, schema_version))
        if commit:
            self.conn.commit()

    def has_source(self, key: str) -> bool:
        return self.conn.execute("SELECT 1 FROM source_documents WHERE source_key=?", (key,)).fetchone() is not None

    def source_status(self, key: str) -> str | None:
        row = self.conn.execute("SELECT status FROM source_documents WHERE source_key=?", (key,)).fetchone()
        return row["status"] if row else None

    def get_monitor_state(self, company_id: str, connector: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM monitor_state WHERE company_id=? AND connector=?",
            (company_id, connector),
        ).fetchone()
        return dict(row) if row else {"company_id": company_id, "connector": connector, "cursor": None,
                                      "error_count": 0}

    def mark_monitor_success(self, company_id: str, connector: str, cursor: str) -> None:
        self.conn.execute(
            """INSERT INTO monitor_state(company_id,connector,cursor,last_checked_at,last_success_at,error_count,last_error)
            VALUES(?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,0,NULL)
            ON CONFLICT(company_id,connector) DO UPDATE SET cursor=excluded.cursor,
            last_checked_at=CURRENT_TIMESTAMP,last_success_at=CURRENT_TIMESTAMP,error_count=0,last_error=NULL""",
            (company_id, connector, cursor),
        )
        self.conn.commit()

    def mark_monitor_failure(self, company_id: str, connector: str, error: str) -> None:
        self.conn.execute(
            """INSERT INTO monitor_state(company_id,connector,last_checked_at,error_count,last_error)
            VALUES(?,?,CURRENT_TIMESTAMP,1,?)
            ON CONFLICT(company_id,connector) DO UPDATE SET last_checked_at=CURRENT_TIMESTAMP,
            error_count=monitor_state.error_count+1,last_error=excluded.last_error""",
            (company_id, connector, error[:4000]),
        )
        self.conn.commit()

    def save_source_candidate(self, candidate: SourceCandidate) -> tuple[int, bool]:
        existing = self.conn.execute(
            "SELECT id FROM source_candidates WHERE company_id=? AND connector=? AND external_id=?",
            (candidate.company_id, candidate.connector, candidate.external_id),
        ).fetchone()
        if existing:
            self.conn.execute(
                """UPDATE source_candidates SET source_url=?,title=?,document_type=?,published_at=?,
                content_type=?,metadata_json=?,last_seen_at=CURRENT_TIMESTAMP WHERE id=?""",
                (candidate.source_url, candidate.title, candidate.document_type, candidate.published_at,
                 candidate.content_type, _json(candidate.metadata), existing["id"]),
            )
            self.conn.commit()
            return existing["id"], False
        cursor = self.conn.execute(
            """INSERT INTO source_candidates(company_id,connector,external_id,source_url,title,
            document_type,published_at,content_type,metadata_json) VALUES(?,?,?,?,?,?,?,?,?)""",
            (candidate.company_id, candidate.connector, candidate.external_id, candidate.source_url,
             candidate.title, candidate.document_type, candidate.published_at, candidate.content_type,
             _json(candidate.metadata)),
        )
        self.conn.commit()
        return cursor.lastrowid, True

    def get_source_candidate(self, candidate_id: int) -> dict:
        row = self.conn.execute("SELECT * FROM source_candidates WHERE id=?", (candidate_id,)).fetchone()
        if not row:
            raise KeyError(f"unknown source candidate {candidate_id}")
        result = dict(row)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        return result

    def set_source_candidate_status(self, candidate_id: int, status: str) -> None:
        if status not in {"discovered", "queued", "fetched", "ignored", "error"}:
            raise ValueError(f"invalid source candidate status: {status}")
        updated = self.conn.execute(
            "UPDATE source_candidates SET status=?,last_seen_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, candidate_id),
        )
        if updated.rowcount != 1:
            raise KeyError(f"unknown source candidate {candidate_id}")
        self.conn.commit()

    def reset_unfinished_source(self, source_key: str) -> None:
        """Clear only unpublished staging rows so a crashed job can safely restart."""
        with self.conn:
            self.conn.execute(
                "DELETE FROM normalized_facts WHERE mapped_fact_id IN (SELECT m.id FROM mapped_facts m JOIN extracted_facts e ON e.id=m.extracted_fact_id WHERE e.source_key=?)",
                (source_key,))
            self.conn.execute(
                "DELETE FROM mapped_facts WHERE extracted_fact_id IN (SELECT id FROM extracted_facts WHERE source_key=?)",
                (source_key,))
            self.conn.execute("DELETE FROM extracted_facts WHERE source_key=?", (source_key,))
            self.conn.execute("DELETE FROM validation_results WHERE source_key=?", (source_key,))
            self.conn.execute("DELETE FROM publication_batches WHERE source_key=? AND status!='published'", (source_key,))
            self.conn.execute("UPDATE source_documents SET status='fetched' WHERE source_key=?", (source_key,))

    def start_pipeline_run(self, company_id: str, job_id: str | None = None) -> str:
        run_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO pipeline_runs(run_id,company_id,job_id,status,stage) VALUES(?,?,?,'running','fetch')",
            (run_id, company_id, job_id))
        self.conn.commit(); return run_id

    def finish_pipeline_run(self, run_id: str, status: str, stage: str | None,
                            source_key: str | None, stats: dict | None = None) -> None:
        self.conn.execute(
            """UPDATE pipeline_runs SET finished_at=CURRENT_TIMESTAMP,status=?,stage=?,source_key=?,stats_json=?
            WHERE run_id=?""", (status, stage, source_key, _json(stats or {}), run_id))
        self.conn.commit()

    def has_staging(self, key: str) -> bool:
        return self.conn.execute("SELECT 1 FROM extracted_facts WHERE source_key=? LIMIT 1", (key,)).fetchone() is not None

    def save_source(self, d: SourceDocument, content_hash: str, local_path: str | None):
        self.conn.execute(
            """INSERT OR IGNORE INTO source_documents(source_key,company_id,source_url,filing_type,filed_at,
            content_hash,local_path,content_type,metadata_json) VALUES(?,?,?,?,?,?,?,?,?)""",
            (d.source_key, d.company_id, d.source_url, d.filing_type, d.filed_at, content_hash,
             local_path, d.content_type, _json(d.metadata)))
        self.conn.commit()

    def save_source_artifact(
        self, artifact_key: str, company_id: str, source_url: str, content_hash: str,
        local_path: str, content_type: str, byte_size: int, metadata: dict | None = None,
    ) -> None:
        """Register one immutable raw filing independently from its reviewed manifest."""
        self.conn.execute(
            """INSERT INTO source_artifacts(artifact_key,company_id,source_url,content_hash,
            local_path,content_type,byte_size,metadata_json) VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(artifact_key) DO UPDATE SET local_path=excluded.local_path,
            status='archived',metadata_json=excluded.metadata_json""",
            (artifact_key, company_id, source_url, content_hash, local_path, content_type,
             byte_size, _json(metadata or {})),
        )
        self.conn.execute(
            """INSERT OR IGNORE INTO source_artifact_links(source_key,artifact_key)
            SELECT source_key,? FROM source_documents WHERE company_id=? AND source_url=?""",
            (artifact_key, company_id, source_url),
        )
        self.conn.commit()

    def set_source_status(self, source_key: str, status: str):
        self.conn.execute("UPDATE source_documents SET status=? WHERE source_key=?", (status, source_key)); self.conn.commit()

    def save_extracted(self, facts):
        ids = []
        for f in facts:
            cur = self.conn.execute(
                """INSERT INTO extracted_facts(source_key,company_id,raw_label,raw_value,raw_currency,raw_unit,
                scale,period_start,period_end,period_kind,fiscal_year,fiscal_quarter,accession,form,page,
                table_ref,location_json,scope,dimensions_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f.source_key, f.company_id, f.raw_label, str(f.raw_value), f.raw_currency, f.raw_unit, str(f.scale),
                 f.period_start, f.period_end, f.period_kind.value, f.fiscal_year, f.fiscal_quarter,
                 f.accession, f.form, f.page, f.table_ref, _json(f.location), f.scope, _json(f.dimensions)))
            ids.append(cur.lastrowid)
        self.conn.commit(); return ids

    def save_mapped(self, facts, extracted_ids, threshold=0.95):
        ids = []
        for f, extracted_id in zip(facts, extracted_ids):
            status = "accepted" if f.metric and float(f.confidence) >= threshold else "review"
            cur = self.conn.execute(
                "INSERT INTO mapped_facts(extracted_fact_id,canonical_metric,confidence,mapping_method,reason,status) VALUES(?,?,?,?,?,?)",
                (extracted_id, f.metric, str(f.confidence), f.mapping_method, f.reason, status))
            ids.append(cur.lastrowid)
        self.conn.commit(); return ids

    def save_normalized(self, facts, mapped_ids, accepted_indexes):
        ids = []
        for f, index in zip(facts, accepted_indexes):
            cur = self.conn.execute(
                """INSERT INTO normalized_facts(mapped_fact_id,normalized_value,currency,unit,period_start,
                period_end,period_kind,fiscal_year,fiscal_quarter,scope,dimensions_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (mapped_ids[index], str(f.value), f.currency, f.unit, f.period_start, f.period_end,
                 f.period_kind.value, f.fiscal_year, f.fiscal_quarter, f.scope, _json(f.dimensions)))
            ids.append(cur.lastrowid)
        self.conn.commit(); return ids

    def validation_history(self, company_id: str, metrics: set[str]) -> list[Fact]:
        """Return current published flow facts used by cross-period validation."""
        if not metrics:
            return []
        placeholders = ",".join("?" for _ in metrics)
        rows = self.conn.execute(
            f"""SELECT * FROM data_points WHERE company_id=? AND metric_key IN ({placeholders})
            AND period_kind IN ('quarter','ytd','fy') AND is_current=1""",
            (company_id, *sorted(metrics)),
        ).fetchall()
        return [Fact(
            company_id=row["company_id"], metric=row["metric_key"], value=Decimal(row["value_decimal"]),
            currency=row["currency"], unit=row["unit"], period_start=row["period_start"] or None,
            period_end=row["period_end"], period_kind=PeriodKind(row["period_kind"]),
            fiscal_year=row["fiscal_year"], fiscal_quarter=row["fiscal_quarter"] or None,
            source_key=row["source_key"], source_url=row["source_url"], filed_at=row["filed_at"],
            accession=row["accession"], form=row["form"], scope=row["scope"],
            dimensions=json.loads(row["dimensions_json"]), quality_score=Decimal(row["quality_score"]),
            metric_version=row["metric_version"],
        ) for row in rows]

    def save_validation(self, source_key: str, company_id: str, errors: list[dict]):
        if errors:
            for error in errors:
                self.conn.execute(
                    "INSERT INTO validation_results(source_key,company_id,rule_code,severity,passed,message,payload_json) VALUES(?,?,?,?,?,?,?)",
                    (source_key, company_id, error["code"], error.get("severity", "error"), 0,
                     error.get("message", error["code"]), _json(error)))
        else:
            self.conn.execute(
                "INSERT INTO validation_results(source_key,company_id,rule_code,severity,passed,message) VALUES(?,?,?,?,?,?)",
                (source_key, company_id, "publication_gate", "info", 1, "All validation rules passed"))
        self.conn.commit()

    def set_normalized_status(self, ids: list[int], status: str):
        if ids:
            self.conn.executemany("UPDATE normalized_facts SET status=? WHERE id=?", [(status, i) for i in ids]); self.conn.commit()

    def publication_batch(self, source_key: str, company_id: str, status: str, staged: int, published: int = 0):
        self.conn.execute(
            "INSERT INTO publication_batches(source_key,company_id,status,staged_count,published_count) VALUES(?,?,?,?,?)",
            (source_key, company_id, status, staged, published)); self.conn.commit()

    def _publish_data_point(self, f: Fact) -> str:
        category = "calculated" if f.is_calculated else "financial"
        self.register_metric(f.metric, category=category, schema_version=f.metric_version, commit=False)
        dimensions_json, dimensions_hash = _dimensions(f.dimensions)
        quarter = f.fiscal_quarter or 0
        where = """company_id=? AND metric_key=? AND period_end=? AND period_kind=? AND fiscal_year=?
        AND fiscal_quarter=? AND currency=? AND unit=? AND scope=? AND dimensions_hash=? AND is_current=1"""
        args = (f.company_id, f.metric, f.period_end, f.period_kind.value, f.fiscal_year, quarter,
                f.currency, f.unit, f.scope, dimensions_hash)
        old = self.conn.execute("SELECT id,value_decimal,version,source_key FROM data_points WHERE " + where, args).fetchone()
        if old and old["value_decimal"] == str(f.value) and old["source_key"] == f.source_key:
            return "duplicate"
        version = old["version"] + 1 if old else 1
        if old:
            self.conn.execute("UPDATE data_points SET is_current=0 WHERE id=?", (old["id"],))
        self.conn.execute(
            """INSERT INTO data_points(company_id,metric_key,value_decimal,value_type,currency,unit,period_start,
            period_end,period_kind,fiscal_year,fiscal_quarter,scope,dimensions_json,dimensions_hash,source_key,
            source_url,filed_at,accession,form,is_calculated,calculation,quality_score,metric_version,version)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f.company_id, f.metric, str(f.value), "decimal", f.currency, f.unit, f.period_start or "",
             f.period_end, f.period_kind.value, f.fiscal_year, quarter, f.scope, dimensions_json, dimensions_hash,
             f.source_key, f.source_url, f.filed_at, f.accession, f.form, int(f.is_calculated), f.calculation,
             str(f.quality_score), f.metric_version, version))
        if not f.dimensions and f.scope == "consolidated":
            legacy_where = "company_id=? AND metric=? AND period_end=? AND period_kind=? AND fiscal_year=? AND fiscal_quarter IS ? AND currency=? AND unit=? AND is_current=1"
            legacy = self.conn.execute("SELECT id FROM observations WHERE " + legacy_where, f.natural_key).fetchone()
            if legacy:
                self.conn.execute("UPDATE observations SET is_current=0 WHERE id=?", (legacy["id"],))
            self.conn.execute(
                """INSERT OR IGNORE INTO observations(company_id,metric,value,currency,unit,period_start,period_end,
                period_kind,fiscal_year,fiscal_quarter,source_key,source_url,filed_at,accession,form,is_calculated,
                calculation,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f.company_id, f.metric, str(f.value), f.currency, f.unit, f.period_start, f.period_end,
                 f.period_kind.value, f.fiscal_year, f.fiscal_quarter, f.source_key, f.source_url, f.filed_at,
                 f.accession, f.form, int(f.is_calculated), f.calculation, version))
        return "restated" if old else "inserted"

    def publish(self, f: Fact) -> str:
        with self.conn:
            return self._publish_data_point(f)

    def publish_batch(self, facts: Iterable[Fact]) -> list[str]:
        """Publish a complete validated batch atomically."""
        with self.conn:
            return [self._publish_data_point(f) for f in facts]

    def _publish_typed_data_point(self, f: TypedFact) -> str:
        self.register_metric(f.metric, category="general", value_type=f.value_type.value,
                             schema_version=f.metric_version, commit=False)
        dimensions_json, dimensions_hash = _dimensions(f.dimensions)
        value_decimal, value_text, value_json = _typed_value(f.value, f.value_type)
        quarter = f.fiscal_quarter or 0
        where = """company_id=? AND metric_key=? AND period_end=? AND period_kind=? AND fiscal_year=?
        AND fiscal_quarter=? AND currency=? AND unit=? AND scope=? AND dimensions_hash=? AND is_current=1"""
        args = (f.company_id, f.metric, f.period_end, f.period_kind.value, f.fiscal_year, quarter,
                f.currency, f.unit, f.scope, dimensions_hash)
        old = self.conn.execute(
            "SELECT id,value_decimal,value_text,value_json,value_type,version,source_key FROM data_points WHERE " + where,
            args).fetchone()
        current_value = (value_decimal, value_text, value_json, f.value_type.value, f.source_key)
        if old and (old["value_decimal"], old["value_text"], old["value_json"], old["value_type"], old["source_key"]) == current_value:
            return "duplicate"
        version = old["version"] + 1 if old else 1
        if old:
            self.conn.execute("UPDATE data_points SET is_current=0 WHERE id=?", (old["id"],))
        self.conn.execute(
            """INSERT INTO data_points(company_id,metric_key,value_decimal,value_text,value_json,value_type,
            currency,unit,period_start,period_end,period_kind,fiscal_year,fiscal_quarter,scope,dimensions_json,
            dimensions_hash,source_key,source_url,filed_at,accession,form,is_calculated,calculation,quality_score,
            metric_version,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f.company_id, f.metric, value_decimal, value_text, value_json, f.value_type.value, f.currency, f.unit,
             f.period_start or "", f.period_end, f.period_kind.value, f.fiscal_year, quarter, f.scope,
             dimensions_json, dimensions_hash, f.source_key, f.source_url, f.filed_at, f.accession, f.form,
             int(f.is_calculated), f.calculation, str(f.quality_score), f.metric_version, version))
        return "restated" if old else "inserted"

    def publish_typed(self, fact: TypedFact) -> str:
        with self.conn:
            return self._publish_typed_data_point(fact)

    def publish_typed_batch(self, facts: Iterable[TypedFact]) -> list[str]:
        with self.conn:
            return [self._publish_typed_data_point(fact) for fact in facts]

    def quarter_history(self, company_id: str, metrics: set[str]) -> list[Fact]:
        """Return current consolidated discrete quarters for historical calculations."""
        if not metrics:
            return []
        placeholders = ",".join("?" for _ in metrics)
        empty_dimensions = _dimensions({})[1]
        rows = self.conn.execute(
            f"""SELECT * FROM data_points WHERE company_id=? AND metric_key IN ({placeholders})
            AND period_kind='quarter' AND is_current=1 AND scope='consolidated' AND dimensions_hash=?
            ORDER BY period_end""",
            (company_id, *sorted(metrics), empty_dimensions),
        ).fetchall()
        return [Fact(
            company_id=row["company_id"], metric=row["metric_key"], value=Decimal(row["value_decimal"]),
            currency=row["currency"], unit=row["unit"], period_start=row["period_start"] or None,
            period_end=row["period_end"], period_kind=PeriodKind(row["period_kind"]),
            fiscal_year=row["fiscal_year"], fiscal_quarter=row["fiscal_quarter"] or None,
            source_key=row["source_key"], source_url=row["source_url"], filed_at=row["filed_at"],
            accession=row["accession"], form=row["form"], is_calculated=bool(row["is_calculated"]),
            calculation=row["calculation"], scope=row["scope"], dimensions=json.loads(row["dimensions_json"]),
            quality_score=Decimal(row["quality_score"]), metric_version=row["metric_version"],
        ) for row in rows]

    def calculation_history(self, company_id: str, metrics: set[str]) -> list[Fact]:
        """Return current consolidated observations needed by deterministic formulas."""
        if not metrics:
            return []
        placeholders = ",".join("?" for _ in metrics)
        empty_dimensions = _dimensions({})[1]
        rows = self.conn.execute(
            f"""SELECT * FROM data_points WHERE company_id=? AND metric_key IN ({placeholders})
            AND is_current=1 AND scope='consolidated' AND dimensions_hash=? ORDER BY period_end""",
            (company_id, *sorted(metrics), empty_dimensions),
        ).fetchall()
        return [Fact(
            company_id=row["company_id"], metric=row["metric_key"], value=Decimal(row["value_decimal"]),
            currency=row["currency"], unit=row["unit"], period_start=row["period_start"] or None,
            period_end=row["period_end"], period_kind=PeriodKind(row["period_kind"]),
            fiscal_year=row["fiscal_year"], fiscal_quarter=row["fiscal_quarter"] or None,
            source_key=row["source_key"], source_url=row["source_url"], filed_at=row["filed_at"],
            accession=row["accession"], form=row["form"], is_calculated=bool(row["is_calculated"]),
            calculation=row["calculation"], scope=row["scope"], dimensions=json.loads(row["dimensions_json"]),
            quality_score=Decimal(row["quality_score"]), metric_version=row["metric_version"],
        ) for row in rows]

    def publish_company_attribute(self, company_id: str, attribute_key: str, value, effective_at: str,
                                  source_key: str | None = None, category: str = "general",
                                  language: str = "en") -> str:
        encoded = _json(value)
        old = self.conn.execute(
            "SELECT id,value_json,version FROM company_attributes WHERE company_id=? AND attribute_key=? AND language=? AND is_current=1",
            (company_id, attribute_key, language)).fetchone()
        if old and old["value_json"] == encoded:
            return "duplicate"
        version = old["version"] + 1 if old else 1
        with self.conn:
            if old:
                self.conn.execute("UPDATE company_attributes SET is_current=0 WHERE id=?", (old["id"],))
            self.conn.execute(
                """INSERT INTO company_attributes(company_id,attribute_key,category,value_json,language,
                effective_at,source_key,version) VALUES(?,?,?,?,?,?,?,?)""",
                (company_id, attribute_key, category, encoded, language, effective_at, source_key, version))
        return "restated" if old else "inserted"

    def publish_disclosure(self, company_id: str, disclosure_type: str, title: str, body_text: str,
                           published_at: str, source_key: str | None = None, period_end: str | None = None,
                           language: str = "en", metadata: dict | None = None) -> str:
        content_hash = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
        old = self.conn.execute(
            "SELECT id,content_hash,version FROM disclosures WHERE company_id=? AND disclosure_type=? AND title=? AND is_current=1",
            (company_id, disclosure_type, title)).fetchone()
        if old and old["content_hash"] == content_hash:
            return "duplicate"
        version = old["version"] + 1 if old else 1
        with self.conn:
            if old:
                self.conn.execute("UPDATE disclosures SET is_current=0 WHERE id=?", (old["id"],))
            self.conn.execute(
                """INSERT INTO disclosures(company_id,disclosure_type,title,body_text,language,published_at,
                period_end,source_key,metadata_json,content_hash,version) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (company_id, disclosure_type, title, body_text, language, published_at, period_end,
                 source_key, _json(metadata or {}), content_hash, version))
        return "restated" if old else "inserted"

    def exception(self, company_id: str, source_key: str, stage: str, code: str, message: str,
                  payload: dict | None = None, severity: str = "error"):
        self.conn.execute(
            """INSERT INTO exceptions(company_id,source_key,stage,code,message,payload_json,severity,updated_at)
            VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
            (company_id, source_key, stage, code, message, _json(payload or {}), severity)); self.conn.commit()

    def resolve_exception(self, exception_id: int, resolution: str,
                          assigned_to: str | None = None) -> dict:
        if not resolution.strip():
            raise ValueError("resolution is required")
        row = self.conn.execute("SELECT * FROM exceptions WHERE id=?", (exception_id,)).fetchone()
        if not row:
            raise KeyError(f"unknown exception {exception_id}")
        with self.conn:
            self.conn.execute(
                """UPDATE exceptions SET status='resolved',resolution=?,assigned_to=COALESCE(?,assigned_to),
                updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (resolution.strip(), assigned_to, exception_id),
            )
        return {"exception_id": exception_id, "status": "resolved", "source_key": row["source_key"]}

    def reopen_source_for_retry(self, source_key: str) -> None:
        row = self.conn.execute(
            "SELECT status FROM source_documents WHERE source_key=?", (source_key,)
        ).fetchone()
        if not row:
            raise KeyError(f"unknown source {source_key}")
        if row["status"] != "review_required":
            raise ValueError(f"source is not awaiting review: {source_key}")
        open_count = self.conn.execute(
            "SELECT count(*) FROM exceptions WHERE source_key=? AND status='open'", (source_key,)
        ).fetchone()[0]
        if open_count:
            raise ValueError(f"source still has {open_count} open exception(s)")
        self.reset_unfinished_source(source_key)

    def stored_source(self, source_key: str) -> dict:
        row = self.conn.execute(
            """SELECT s.*,c.market,c.symbol FROM source_documents s
            JOIN companies c USING(company_id) WHERE source_key=?""", (source_key,)
        ).fetchone()
        if not row:
            raise KeyError(f"unknown source {source_key}")
        return dict(row)

    def upsert_backlog_item(
        self, idempotency_key: str, item_type: str, domain: str, title: str,
        company_id: str | None = None, description: str | None = None,
        period_end: str | None = None, period_kind: str | None = None,
        metric_key: str | None = None, source_url: str | None = None,
        priority: int = 100, payload: dict | None = None,
    ) -> str:
        """Create durable data work without duplicating the same backlog item."""
        if not 1 <= priority <= 1000:
            raise ValueError("backlog priority must be between 1 and 1000")
        encoded = _json(payload or {})
        old = self.conn.execute(
            "SELECT backlog_id,status FROM backlog_items WHERE idempotency_key=?",
            (idempotency_key,),
        ).fetchone()
        if old:
            with self.conn:
                self.conn.execute(
                    """UPDATE backlog_items SET item_type=?,domain=?,title=?,description=?,period_end=?,
                    period_kind=?,metric_key=?,source_url=?,priority=?,payload_json=?,
                    status=CASE WHEN status='completed' THEN 'open' ELSE status END,
                    completed_at=CASE WHEN status='completed' THEN NULL ELSE completed_at END,
                    updated_at=CURRENT_TIMESTAMP WHERE backlog_id=?""",
                    (item_type, domain, title, description, period_end, period_kind, metric_key,
                     source_url, priority, encoded, old["backlog_id"]),
                )
            return "reopened" if old["status"] == "completed" else "updated"
        backlog_id = f"backlog:{hashlib.sha256(idempotency_key.encode('utf-8')).hexdigest()[:24]}"
        with self.conn:
            self.conn.execute(
                """INSERT INTO backlog_items(backlog_id,company_id,item_type,domain,title,description,
                period_end,period_kind,metric_key,source_url,priority,payload_json,idempotency_key)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (backlog_id, company_id, item_type, domain, title, description, period_end,
                 period_kind, metric_key, source_url, priority, encoded, idempotency_key),
            )
        return "inserted"

    def complete_backlog_item(self, idempotency_key: str) -> bool:
        with self.conn:
            cursor = self.conn.execute(
                """UPDATE backlog_items SET status='completed',completed_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP WHERE idempotency_key=?
                AND status NOT IN ('completed','cancelled')""", (idempotency_key,))
        return cursor.rowcount > 0

    def sync_coverage_backlog(
        self, company_id: str, period_end: str, period_kind: str, domain: str,
        missing_metrics: dict[str, str],
    ) -> dict:
        """Mirror metric coverage gaps into a durable, automatically closing backlog."""
        prefix = f"coverage:{company_id}:{period_end}:{period_kind}:{domain}:"
        active_keys = {prefix + metric for metric in missing_metrics}
        for metric, requirement in sorted(missing_metrics.items()):
            self.upsert_backlog_item(
                prefix + metric, "coverage_gap", domain,
                f"Backfill {metric} for {period_end} ({period_kind})",
                company_id=company_id, period_end=period_end, period_kind=period_kind,
                metric_key=metric, priority=20 if requirement == "required" else 50,
                payload={"requirement": requirement, "origin": "coverage_engine"},
            )
        rows = self.conn.execute(
            """SELECT idempotency_key FROM backlog_items WHERE company_id=? AND item_type='coverage_gap'
            AND period_end=? AND period_kind=? AND domain=? AND status NOT IN ('completed','cancelled')""",
            (company_id, period_end, period_kind, domain),
        ).fetchall()
        completed = 0
        for row in rows:
            if row["idempotency_key"] not in active_keys:
                completed += int(self.complete_backlog_item(row["idempotency_key"]))
        return {"open": len(active_keys), "completed": completed}

    def health(self) -> dict:
        tables = {
            "companies": "companies", "sources": "source_documents",
            "source_artifacts": "source_artifacts",
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
            "completeness_rows": "company_completeness",
        }
        counts = {key: self.conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for key, table in tables.items()}
        counts["schema_version"] = SCHEMA_VERSION
        return counts
