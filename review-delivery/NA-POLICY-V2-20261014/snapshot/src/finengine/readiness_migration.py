"""Explicit, bounded canonical-readiness feature migration for schema 23.

Never calls Database initialization, projection, import or readiness evaluation.
The base revision stays 23: older schema-23 consumers remain compatible. The
feature revision is attested by its exact DDL fingerprint, not a forged global
schema version. Calling this function authorizes writes to its connection only.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from typing import Callable

FEATURE_REVISION = "canonical-readiness/1"
BASE_SCHEMA_VERSION = 23
DDL = (
    ("factory_company_readiness", """CREATE TABLE factory_company_readiness(
 company_id TEXT PRIMARY KEY REFERENCES companies(company_id),
 contract_version TEXT NOT NULL, scoring_model TEXT NOT NULL,
 sector_pack TEXT, total_score TEXT NOT NULL, target_score TEXT NOT NULL,
 readiness_state TEXT NOT NULL CHECK(readiness_state IN ('ready','not_ready')),
 coverage_thresholds_passed INTEGER NOT NULL,
 all_hard_gates_evaluated INTEGER NOT NULL,
 all_hard_gates_passed INTEGER NOT NULL,
 blocking_reasons_json TEXT NOT NULL DEFAULT '[]',
 checked_at TEXT NOT NULL)"""),
    ("factory_category_scores", """CREATE TABLE factory_category_scores(
 company_id TEXT NOT NULL REFERENCES companies(company_id),
 category_key TEXT NOT NULL, weight TEXT NOT NULL, threshold TEXT NOT NULL,
 score TEXT NOT NULL, weighted_score TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('complete','partial','missing','not_applicable')),
 threshold_passed INTEGER NOT NULL, hard_gates_json TEXT NOT NULL DEFAULT '[]',
 evidence_json TEXT NOT NULL DEFAULT '{}', checked_at TEXT NOT NULL,
 PRIMARY KEY(company_id,category_key))"""),
    ("idx_factory_category_scores_status", """CREATE INDEX idx_factory_category_scores_status
 ON factory_category_scores(category_key,status,threshold_passed)"""),
)


class ReadinessMigrationError(ValueError):
    """Preflight rejected an incompatible database; nothing was migrated."""


def _canonical_sql(sql: str) -> str:
    # Ignore formatting outside string literals, retaining CHECK/default values.
    tokens = re.findall(r"'(?:''|[^'])*'|[A-Za-z_][A-Za-z_0-9]*|\S", sql)
    tokens = [token if token.startswith("'") else token.lower() for token in tokens]
    return " ".join(tokens).replace(" if not exists ", " ").rstrip(" ;")


def _feature_objects(conn: sqlite3.Connection) -> dict[str, tuple]:
    return {row[0]: tuple(row[1:]) for row in conn.execute(
        "SELECT name,type,tbl_name,sql FROM sqlite_master WHERE name IN (?,?,?)",
        tuple(name for name, _ in DDL))}


def _expected_objects() -> dict[str, tuple]:
    with sqlite3.connect(":memory:") as expected:
        for _, statement in DDL:
            expected.execute(statement)
        return _feature_objects(expected)


def _validate_objects(conn: sqlite3.Connection, *, require_all: bool) -> dict:
    actual, expected = _feature_objects(conn), _expected_objects()
    if require_all and set(actual) != set(expected):
        raise ReadinessMigrationError("canonical readiness feature is incomplete")
    for name, (kind, table, sql) in actual.items():
        ekind, etable, esql = expected[name]
        if (kind, table) != (ekind, etable) or not sql or _canonical_sql(sql) != _canonical_sql(esql):
            raise ReadinessMigrationError(f"incompatible canonical object: {name}")
    # Reject unexpected indexes/triggers that could mutate rows or alter uniqueness.
    for row in conn.execute("SELECT name,type FROM sqlite_master WHERE tbl_name IN (?,?)",
                            tuple(name for name, _ in DDL[:2])):
        if row[0] not in expected and not row[0].startswith("sqlite_autoindex_"):
            raise ReadinessMigrationError(f"unexpected canonical object: {row[0]}")
    return actual


def migrate_readiness_feature(conn: sqlite3.Connection, *,
                              after_ddl: Callable[[str], None] | None = None) -> dict:
    """Apply two tables and one index atomically; reject malformed existing DDL.

    ``after_ddl`` is a local fault-injection seam, called after every newly
    executed statement. Exceptions roll back the entire transaction. Caller
    transactions are rejected to avoid committing unrelated pending changes.
    """
    if conn.in_transaction:
        raise ReadinessMigrationError("caller transaction must be committed or rolled back first")
    if conn.execute("PRAGMA query_only").fetchone()[0]:
        raise ReadinessMigrationError("read-only connection cannot migrate")
    conn.execute("BEGIN IMMEDIATE")
    try:
        version = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        if version != BASE_SCHEMA_VERSION:
            raise ReadinessMigrationError(f"expected base schema 23, found {version!r}")
        company_columns = {row[1]: row for row in conn.execute("PRAGMA table_info(companies)")}
        if "company_id" not in company_columns or company_columns["company_id"][5] != 1:
            raise ReadinessMigrationError("companies.company_id primary key is required")
        before = _validate_objects(conn, require_all=False)
        created = []
        for name, statement in DDL:
            if name not in before:
                conn.execute(statement)
                created.append(name)
                if after_ddl:
                    after_ddl(name)
        actual = _validate_objects(conn, require_all=True)
        fingerprint = hashlib.sha256("\n".join(
            name + ":" + _canonical_sql(actual[name][2]) for name, _ in DDL
        ).encode()).hexdigest()
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    return {"feature_revision": FEATURE_REVISION, "base_schema_version": version,
            "revision_strategy": "schema23-compatible-exact-feature-DDL-fingerprint",
            "ddl_sha256": fingerprint, "created_objects": created,
            "status": "applied" if created else "already_present"}
