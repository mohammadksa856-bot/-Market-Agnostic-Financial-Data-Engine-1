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
CREATE TABLE IF NOT EXISTS extracted_facts(
 id INTEGER PRIMARY KEY, source_key TEXT NOT NULL REFERENCES source_documents(source_key), company_id TEXT NOT NULL REFERENCES companies(company_id),
 raw_label TEXT NOT NULL, raw_value TEXT NOT NULL, raw_currency TEXT NOT NULL, raw_unit TEXT NOT NULL, scale TEXT NOT NULL,
 period_start TEXT, period_end TEXT NOT NULL, period_kind TEXT NOT NULL, fiscal_year INTEGER NOT NULL, fiscal_quarter INTEGER,
 accession TEXT, form TEXT, page INTEGER, table_ref TEXT, location_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS mapped_facts(
 id INTEGER PRIMARY KEY, extracted_fact_id INTEGER NOT NULL REFERENCES extracted_facts(id), canonical_metric TEXT,
 confidence TEXT NOT NULL, mapping_method TEXT NOT NULL, reason TEXT, status TEXT NOT NULL CHECK(status IN ('accepted','review')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS normalized_facts(
 id INTEGER PRIMARY KEY, mapped_fact_id INTEGER NOT NULL REFERENCES mapped_facts(id), normalized_value TEXT NOT NULL,
 currency TEXT NOT NULL, unit TEXT NOT NULL, period_start TEXT, period_end TEXT NOT NULL, period_kind TEXT NOT NULL,
 fiscal_year INTEGER NOT NULL, fiscal_quarter INTEGER, status TEXT NOT NULL DEFAULT 'staged' CHECK(status IN ('staged','validated','rejected','published')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS validation_results(
 id INTEGER PRIMARY KEY, source_key TEXT NOT NULL REFERENCES source_documents(source_key), company_id TEXT NOT NULL,
 rule_code TEXT NOT NULL, severity TEXT NOT NULL, passed INTEGER NOT NULL, message TEXT NOT NULL, payload_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS publication_batches(
 id INTEGER PRIMARY KEY, source_key TEXT NOT NULL REFERENCES source_documents(source_key), company_id TEXT NOT NULL,
 status TEXT NOT NULL, staged_count INTEGER NOT NULL, published_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
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
    def has_staging(self, key: str) -> bool:
        return self.conn.execute("SELECT 1 FROM extracted_facts WHERE source_key=? LIMIT 1",(key,)).fetchone() is not None
    def save_source(self, d: SourceDocument, content_hash: str, local_path: str | None):
        self.conn.execute("INSERT OR IGNORE INTO source_documents(source_key,company_id,source_url,filing_type,filed_at,content_hash,local_path,metadata_json) VALUES(?,?,?,?,?,?,?,?)", (d.source_key,d.company_id,d.source_url,d.filing_type,d.filed_at,content_hash,local_path,json.dumps(d.metadata))); self.conn.commit()
    def set_source_status(self, source_key: str, status: str):
        self.conn.execute("UPDATE source_documents SET status=? WHERE source_key=?",(status,source_key)); self.conn.commit()
    def save_extracted(self, facts):
        ids=[]
        for f in facts:
            cur=self.conn.execute("""INSERT INTO extracted_facts(source_key,company_id,raw_label,raw_value,raw_currency,raw_unit,scale,period_start,period_end,period_kind,fiscal_year,fiscal_quarter,accession,form,page,table_ref,location_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(f.source_key,f.company_id,f.raw_label,str(f.raw_value),f.raw_currency,f.raw_unit,str(f.scale),f.period_start,f.period_end,f.period_kind.value,f.fiscal_year,f.fiscal_quarter,f.accession,f.form,f.page,f.table_ref,json.dumps(f.location)))
            ids.append(cur.lastrowid)
        self.conn.commit(); return ids
    def save_mapped(self, facts, extracted_ids, threshold=0.95):
        ids=[]
        for f,extracted_id in zip(facts,extracted_ids):
            status="accepted" if f.metric and float(f.confidence)>=threshold else "review"
            cur=self.conn.execute("INSERT INTO mapped_facts(extracted_fact_id,canonical_metric,confidence,mapping_method,reason,status) VALUES(?,?,?,?,?,?)",(extracted_id,f.metric,str(f.confidence),f.mapping_method,f.reason,status)); ids.append(cur.lastrowid)
        self.conn.commit(); return ids
    def save_normalized(self, facts, mapped_ids, accepted_indexes):
        ids=[]
        for f,index in zip(facts,accepted_indexes):
            cur=self.conn.execute("""INSERT INTO normalized_facts(mapped_fact_id,normalized_value,currency,unit,period_start,period_end,period_kind,fiscal_year,fiscal_quarter) VALUES(?,?,?,?,?,?,?,?,?)""",(mapped_ids[index],str(f.value),f.currency,f.unit,f.period_start,f.period_end,f.period_kind.value,f.fiscal_year,f.fiscal_quarter)); ids.append(cur.lastrowid)
        self.conn.commit(); return ids
    def save_validation(self, source_key: str, company_id: str, errors: list[dict]):
        if errors:
            for error in errors:
                self.conn.execute("INSERT INTO validation_results(source_key,company_id,rule_code,severity,passed,message,payload_json) VALUES(?,?,?,?,?,?,?)",(source_key,company_id,error["code"],error.get("severity","error"),0,error.get("message",error["code"]),json.dumps(error)))
        else:
            self.conn.execute("INSERT INTO validation_results(source_key,company_id,rule_code,severity,passed,message) VALUES(?,?,?,?,?,?)",(source_key,company_id,"publication_gate","info",1,"All validation rules passed"))
        self.conn.commit()
    def set_normalized_status(self, ids: list[int], status: str):
        if ids: self.conn.executemany("UPDATE normalized_facts SET status=? WHERE id=?",[(status,i) for i in ids]); self.conn.commit()
    def publication_batch(self, source_key: str, company_id: str, status: str, staged: int, published: int=0):
        self.conn.execute("INSERT INTO publication_batches(source_key,company_id,status,staged_count,published_count) VALUES(?,?,?,?,?)",(source_key,company_id,status,staged,published)); self.conn.commit()
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
