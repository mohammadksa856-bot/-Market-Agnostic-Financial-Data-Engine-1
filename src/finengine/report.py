from __future__ import annotations

import csv
import html
import sqlite3
from datetime import datetime
from pathlib import Path


AR_METRICS = {
    "revenue": "الإيرادات",
    "net_income": "صافي الربح",
    "operating_cash_flow": "التدفق النقدي التشغيلي",
    "capex": "النفقات الرأسمالية",
    "free_cash_flow": "التدفق النقدي الحر",
    "net_margin": "هامش صافي الربح",
    "total_assets": "إجمالي الأصول",
    "total_liabilities": "إجمالي الالتزامات",
    "total_equity": "حقوق الملكية",
}


def export_readable_report(db_path: str, html_path: str, csv_path: str) -> None:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT c.name,c.market,c.symbol,d.fiscal_year,NULLIF(d.fiscal_quarter,0) AS fiscal_quarter,
        d.period_end,d.period_kind,d.metric_key AS metric,d.value_decimal AS value,d.currency,d.source_url
        FROM data_points d JOIN companies c USING(company_id)
        WHERE d.is_current=1 AND d.scope='consolidated' AND d.dimensions_json='{}'
        ORDER BY c.market,c.symbol,d.period_end DESC,d.metric_key"""
    ).fetchall()
    audit = {
        "المصادر المحفوظة": conn.execute("SELECT count(*) FROM source_documents").fetchone()[0],
        "حقائق الاستخراج": conn.execute("SELECT count(*) FROM extracted_facts").fetchone()[0],
        "Mapping معتمد": conn.execute("SELECT count(*) FROM mapped_facts WHERE status='accepted'").fetchone()[0],
        "بانتظار المراجعة": conn.execute("SELECT count(*) FROM mapped_facts WHERE status='review'").fetchone()[0],
        "حقائق منشورة": conn.execute("SELECT count(*) FROM data_points WHERE is_current=1").fetchone()[0],
        "إدراجات نشطة": conn.execute("SELECT count(*) FROM listings WHERE active=1").fetchone()[0],
        "فترات مقاسة التغطية": conn.execute("SELECT count(*) FROM coverage_status").fetchone()[0],
        "استثناءات مفتوحة": conn.execute("SELECT count(*) FROM exceptions WHERE status='open'").fetchone()[0],
    }
    conn.close()

    csv_target = Path(csv_path)
    csv_target.parent.mkdir(parents=True, exist_ok=True)
    with csv_target.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["الشركة", "السوق", "الرمز", "السنة", "الربع", "نهاية الفترة", "نوع الفترة", "المقياس", "القيمة", "العملة", "المصدر"])
        for row in rows:
            writer.writerow([row["name"], row["market"], row["symbol"], row["fiscal_year"], row["fiscal_quarter"] or "", row["period_end"], row["period_kind"], AR_METRICS.get(row["metric"], row["metric"]), row["value"], row["currency"], row["source_url"]])

    groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        groups.setdefault(f'{row["name"]} ({row["symbol"]})', []).append(row)
    sections = []
    for company, company_rows in groups.items():
        body = []
        for row in company_rows:
            value = float(row["value"])
            shown = f"{value / 1_000_000_000:,.2f} مليار" if row["currency"] in {"SAR", "USD"} and abs(value) >= 1_000_000_000 else f"{value:,.2f}"
            period = {"fy": "سنوي", "quarter": "ربع", "ytd": "من بداية السنة", "instant": "رصيد"}.get(row["period_kind"], row["period_kind"])
            body.append(f'<tr><td>{html.escape(row["period_end"])}</td><td>{html.escape(period)}</td><td>{html.escape(AR_METRICS.get(row["metric"], row["metric"]))}</td><td>{shown} {html.escape(row["currency"])}</td><td><a href="{html.escape(row["source_url"])}">المصدر</a></td></tr>')
        sections.append(f'<section><h2>{html.escape(company)}</h2><div class="table"><table><thead><tr><th>الفترة</th><th>النوع</th><th>البيان</th><th>القيمة</th><th>التوثيق</th></tr></thead><tbody>{"".join(body)}</tbody></table></div></section>')
    cards=''.join(f'<div class="card"><b>{value:,}</b><span>{html.escape(label)}</span></div>' for label,value in audit.items())
    refreshed=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    page = f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>بيانات الشركات المالية</title><style>body{{font-family:Tahoma,Arial;background:#f4f7f9;color:#17212b;margin:0}}main{{max-width:1180px;margin:auto;padding:28px}}h1{{margin-bottom:8px}}.note{{color:#52606d;margin-bottom:8px}}.refreshed{{color:#087f5b;font-weight:bold;margin:0 0 20px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}.card{{background:#163c35;color:white;border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:6px}}.card b{{font-size:24px}}.card span{{color:#cce4dc}}section{{background:white;border-radius:14px;padding:20px;margin:18px 0;box-shadow:0 3px 14px #0001}}.table{{overflow:auto}}table{{width:100%;border-collapse:collapse;white-space:nowrap}}th,td{{padding:11px;border-bottom:1px solid #e7ecef;text-align:right}}th{{background:#edf5f2}}a{{color:#087f5b}}@media(max-width:600px){{main{{padding:12px}}section{{padding:12px}}}}</style></head><body><main><h1>مصنع البيانات المالية</h1><p class="note">Source → Extraction → Mapping → Normalization → Validation → Production. القيم الكبيرة معروضة بالمليار، وكل سطر مرتبط بمصدره الرسمي.</p><p class="refreshed">آخر فحص وتحديث: {html.escape(refreshed)}</p><div class="cards">{cards}</div>{''.join(sections)}</main></body></html>'''
    html_target = Path(html_path)
    html_target.parent.mkdir(parents=True, exist_ok=True)
    html_target.write_text(page, encoding="utf-8")
