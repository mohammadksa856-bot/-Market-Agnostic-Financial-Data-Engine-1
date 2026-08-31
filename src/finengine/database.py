from __future__ import annotations
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from .models import Company, Fact, SourceDocument

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS companies(company_id TEXT PRIMARY KEY, market TEXT NOT NULL, symbol TEXT NOT NULL, name TEXT NOT NULL, currency TEXT NOT NULL, cik TEXT, isin TEXT, fiscal_year_end TEXT NOT NULL, UNIQUE(market,symbol));
CREATE TABLE IF NOT EXISTS source_documents(source_key TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id), source_url TEXT NOT NULL, filing_type TEXT NOT NULL, filed_at TEXT NOT NULL, content_hash TEXT NOT NULL, local_path TEXT, status TEXT NOT NULL DEFAULT 'fetched', metadata_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(company_id), metric TEXT NOT NULL, value TEXT NOT NULL, currency TEXT NOT NULL, unit TEXT NOT NULL, period_start TEXT, period_end TEXT NOT NULL, period_kind TEXT NOT NULL, fiscal_year INTEGER NOT NULL, fiscal_quarter INTEGER, source_key TEXT NOT NULL REFERENCES source_documents(source_key), source_url TEXT NOT NULL, filed_at TEXT NOT NULL, accession TEXT, form TEXT, is_calculated INTEGER NOT NULL DEFAULT 0, calculation TEXT, version INTEGER NOT NULL, is_current INTEGER NOT NULL DEFAULT 1, published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(company_id,metric,period_end,period_kind,fiscal_year,fiscal_quarter,currency,unit,version));
CREATE INDEX IF NOT EXISTS idx_observation_query ON observations(company_id,metric,is_current,period_end);
CREATE TABLE IF NOT EXISTS exceptions(id INTEGER PRIMARY KEY, company_id TEXT, source_key TEXT, stage TEXT NOT NULL, code TEXT NOT NULL, message TEXT NOT NULL, payload_json TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pipeline_runs(run_id TEXT PRIMARY KEY, company_id TEXT NOT NULL, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, finished_at TEXT, status TEXT NOT NULL, stats_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS monitor_state(company_id TEXT NOT NULL, connector TEXT NOT NULL, cursor TEXT, last_checked_at TEXT, PRIMARY KEY(company_id,connector));
"""

class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
    def close(self): self.conn.close()
    def register_company(self, c: Company):
        self.conn.execute("INSERT INTO companies VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(company_id) DO UPDATE SET name=excluded.name,currency=excluded.currency", (c.company_id,c.market.value,c.symbol,c.name,c.currency,c.cik,c.isin,c.fiscal_year_end)); self.conn.commit()
    def has_source(self, key: str) -> bool:
        return self.conn.execute("SELECT 1 FROM source_documents WHERE source_key=?", (key,)).fetchone() is not None
    def save_source(self, d: SourceDocument, content_hash: str, local_path: str | None):
        self.conn.execute("INSERT OR IGNORE INTO source_documents(source_key,company_id,source_url,filing_type,filed_at,content_hash,local_path,metadata_json) VALUES(?,?,?,?,?,?,?,?)", (d.source_key,d.company_id,d.source_url,d.filing_type,d.filed_at,content_hash,local_path,json.dumps(d.metadata))); self.conn.commit()
    def publish(self, f: Fact) -> str:
        where = "company_id=? AND metric=? AND period_end=? AND period_kind=? AND fiscal_year=? AND fiscal_quarter IS ? AND currency=? AND unit=? AND is_current=1"
        args = f.natural_key
        old = self.conn.execute("SELECT id,value,version,source_key FROM observations WHERE "+where, args).fetchone()
        if old and old["value"] == str(f.value) and old["source_key"] == f.source_key: return "duplicate"
        version = 1
        if old:
            version = old["version"] + 1
            self.conn.execute("UPDATE observations SET is_current=0 WHERE id=?", (old["id"],))
        self.conn.execute("""INSERT INTO observations(company_id,metric,value,currency,unit,period_start,period_end,period_kind,fiscal_year,fiscal_quarter,source_key,source_url,filed_at,accession,form,is_calculated,calculation,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (f.company_id,f.metric,str(f.value),f.currency,f.unit,f.period_start,f.period_end,f.period_kind.value,f.fiscal_year,f.fiscal_quarter,f.source_key,f.source_url,f.filed_at,f.accession,f.form,int(f.is_calculated),f.calculation,version)); self.conn.commit()
        return "restated" if old else "inserted"
    def exception(self, company_id: str, source_key: str, stage: str, code: str, message: str, payload: dict | None=None):
        self.conn.execute("INSERT INTO exceptions(company_id,source_key,stage,code,message,payload_json) VALUES(?,?,?,?,?,?)",(company_id,source_key,stage,code,message,json.dumps(payload or {}))); self.conn.commit()
