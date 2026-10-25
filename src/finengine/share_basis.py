"""Per-share comparisons that straddle a share-basis event.

A reported per-share value (or weighted share count) is restated for every bonus issue, split or
rights issue effective before its report is filed. Two values taken from reports filed on either
side of such an event therefore sit on different share bases, and a growth rate, CAGR or quarterly
change between them compares unlike quantities. The audit never rewrites stored data: it names the
affected current rows so completeness and acceptance views can withhold them.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

SHARE_BASIS_ACTIONS = ("bonus_shares", "stock_split", "reverse_split", "rights_issue")

# output metric -> (per-share input metric, comparison, fiscal-year lag)
COMPARISONS = {
    "eps_growth": ("eps_diluted", "fy", 1),
    "dividend_per_share_growth": ("dividends_per_share", "fy", 1),
    "eps_cagr_3y": ("eps_diluted", "fy", 3),
    "eps_cagr_5y": ("eps_diluted", "fy", 5),
    "dividend_cagr_3y": ("dividends_per_share", "fy", 3),
    "dividend_cagr_5y": ("dividends_per_share", "fy", 5),
    "eps_cagr_10y": ("eps_diluted", "fy", 10),
    "dividend_cagr_10y": ("dividends_per_share", "fy", 10),
    "eps_qoq": ("eps_diluted", "quarter", 0),
    "revenue_per_share_growth": ("weighted_average_shares", "fy", 1),
    "free_cash_flow_per_share_growth": ("weighted_average_shares", "fy", 1),
}
SHARE_COUNT_BASES = ("weighted_average_shares_diluted", "weighted_average_shares_basic")


def share_basis_events(conn: sqlite3.Connection, company_id: str) -> list[str]:
    placeholders = ",".join("?" for _ in SHARE_BASIS_ACTIONS)
    return sorted(row[0] for row in conn.execute(
        f"""SELECT DISTINCT effective_date FROM corporate_actions WHERE company_id=? AND is_current=1
        AND action_type IN ({placeholders}) AND effective_date IS NOT NULL AND effective_date<>''""",
        (company_id, *SHARE_BASIS_ACTIONS)))


def _consolidated(conn, company_id, metric, where, args):
    return conn.execute(
        f"""SELECT * FROM data_points WHERE company_id=? AND metric_key=? AND is_current=1
        AND scope='consolidated' AND dimensions_json IN ('{{}}','') AND {where}
        ORDER BY filed_at DESC LIMIT 1""", (company_id, metric, *args)).fetchone()


def _input_metric(row, metric):
    if metric != "weighted_average_shares":
        return metric
    formula = row["calculation"] or ""
    return next((base for base in SHARE_COUNT_BASES if base in formula), SHARE_COUNT_BASES[0])


def _inputs(conn, row, metric, kind, lag):
    company_id = row["company_id"]
    metric = _input_metric(row, metric)
    if kind == "fy":
        now = _consolidated(conn, company_id, metric, "period_kind='fy' AND fiscal_year=?", (row["fiscal_year"],))
        prior = _consolidated(conn, company_id, metric, "period_kind='fy' AND fiscal_year=?",
                              (row["fiscal_year"] - lag,))
    else:
        now = _consolidated(conn, company_id, metric, "period_kind='quarter' AND period_end=?", (row["period_end"],))
        prior = None
        if now is not None and now["period_start"]:
            previous_end = (date.fromisoformat(now["period_start"]) - timedelta(days=1)).isoformat()
            prior = _consolidated(conn, company_id, metric, "period_kind='quarter' AND period_end=?", (previous_end,))
    return now, prior


def audit_share_basis(conn: sqlite3.Connection, company_id: str) -> list[dict]:
    """Current calculated per-share comparisons that cannot be shown on one share basis."""
    if conn.row_factory is None:
        conn.row_factory = sqlite3.Row
    events = share_basis_events(conn, company_id)
    if not events:
        return []
    placeholders = ",".join("?" for _ in COMPARISONS)
    findings = []
    for row in conn.execute(
            f"""SELECT * FROM data_points WHERE company_id=? AND is_current=1 AND is_calculated=1
            AND metric_key IN ({placeholders}) ORDER BY metric_key, period_end""",
            (company_id, *COMPARISONS)).fetchall():
        metric, kind, lag = COMPARISONS[row["metric_key"]]
        now, prior = _inputs(conn, row, metric, kind, lag)
        base = {"id": row["id"], "company_id": company_id, "metric_key": row["metric_key"],
                "period_end": row["period_end"], "period_kind": row["period_kind"]}
        if now is None or prior is None or not now["filed_at"] or not prior["filed_at"]:
            findings.append({**base, "reason": "inputs_not_resolved", "events": events})
            continue
        low, high = sorted((now["filed_at"][:10], prior["filed_at"][:10]))
        straddled = [event for event in events if low < event[:10] <= high]
        if straddled:
            findings.append({**base, "reason": "share_basis_event_between_sources", "events": straddled,
                             "inputs": [(item["metric_key"], item["period_end"], item["filed_at"][:10])
                                        for item in (prior, now)]})
    return findings


def withheld_metric_keys(conn: sqlite3.Connection, company_id: str) -> set[str]:
    """Per-share comparison keys whose every current row is withheld by the audit."""
    withheld_ids = {finding["id"] for finding in audit_share_basis(conn, company_id)}
    if not withheld_ids:
        return set()
    current = {}
    placeholders = ",".join("?" for _ in COMPARISONS)
    for row_id, metric_key in conn.execute(
            f"""SELECT id, metric_key FROM data_points WHERE company_id=? AND is_current=1
            AND metric_key IN ({placeholders})""", (company_id, *COMPARISONS)):
        current.setdefault(metric_key, set()).add(row_id)
    return {metric for metric, ids in current.items() if ids <= withheld_ids}
