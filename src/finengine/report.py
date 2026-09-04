from __future__ import annotations

import csv
import html
import json
import sqlite3
from datetime import datetime
from pathlib import Path


AR_METRICS = {
    "revenue": "الإيرادات",
    "other_income_related_to_sales": "دخل آخر مرتبط بالمبيعات",
    "revenue_and_other_income_related_to_sales": "الإيرادات والدخل الآخر المرتبط بالمبيعات",
    "operating_costs": "التكاليف التشغيلية",
    "operating_income": "الدخل التشغيلي",
    "income_before_income_taxes_and_zakat": "الدخل قبل الضرائب والزكاة",
    "income_taxes_and_zakat": "ضرائب الدخل والزكاة",
    "net_income": "صافي الربح",
    "adjusted_net_income": "صافي الربح المعدل",
    "net_income_parent": "صافي الربح العائد لمساهمي الشركة",
    "operating_cash_flow": "التدفق النقدي التشغيلي",
    "capex": "النفقات الرأسمالية",
    "free_cash_flow": "التدفق النقدي الحر",
    "dividends_paid": "التوزيعات المدفوعة",
    "base_dividends_paid": "التوزيعات الأساسية المدفوعة",
    "performance_linked_dividends_paid": "التوزيعات المرتبطة بالأداء",
    "dividends_per_share": "التوزيعات لكل سهم",
    "eps_diluted": "ربحية السهم الأساسية والمخفضة",
    "net_margin": "هامش صافي الربح",
    "roace": "العائد على متوسط رأس المال المستخدم",
    "gearing": "نسبة المديونية (Gearing)",
    "total_assets": "إجمالي الأصول",
    "total_liabilities": "إجمالي الالتزامات",
    "total_equity": "حقوق الملكية",
    "cash": "النقد وما في حكمه",
    "liabilities_to_equity": "الالتزامات إلى حقوق الملكية",
    "average_realized_crude_oil_price": "متوسط سعر النفط الخام المحقق",
    "total_hydrocarbon_production": "إجمالي إنتاج الهيدروكربونات",
    "total_liquids_production": "إجمالي إنتاج السوائل",
    "total_gas_production": "إجمالي إنتاج الغاز",
    "total_hydrocarbon_reserves": "إجمالي احتياطيات الهيدروكربونات",
    "maximum_sustainable_capacity": "الطاقة الإنتاجية القصوى المستدامة",
    "net_refining_capacity": "صافي طاقة التكرير",
    "net_chemicals_production_capacity": "صافي الطاقة الإنتاجية للكيماويات",
    "supply_reliability": "موثوقية الإمداد",
}

AR_UNITS = {
    "mmboed": "مليون برميل مكافئ نفطي/يوم",
    "mmbpd": "مليون برميل/يوم",
    "bscfd": "مليار قدم مكعبة قياسية/يوم",
    "billion_boe": "مليار برميل مكافئ نفطي",
    "million_tonnes_per_year": "مليون طن/سنة",
}


def _display_value(value: float, currency: str, unit: str) -> str:
    if unit in {"SAR", "USD"}:
        amount = f"{value / 1_000_000_000:,.2f} مليار" if abs(value) >= 1_000_000_000 else f"{value:,.2f}"
        return f"{amount} {currency}"
    if unit == "ratio":
        return f"{value * 100:,.2f}%"
    if unit == "percent":
        return f"{value:,.2f}%"
    if unit == "USD/bbl":
        return f"${value:,.2f}/برميل"
    if unit == "SAR/share":
        return f"{value:,.4f} ريال/سهم"
    return f"{value:,.3f} {AR_UNITS.get(unit, unit)}".strip()


def export_readable_report(db_path: str, html_path: str, csv_path: str) -> None:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT c.company_id,c.name,c.market,c.symbol,d.fiscal_year,NULLIF(d.fiscal_quarter,0) AS fiscal_quarter,
        d.period_end,d.period_kind,d.metric_key AS metric,d.value_decimal AS value,d.currency,d.unit,d.scope,
        d.dimensions_json,d.source_url,
        m.category
        FROM data_points d JOIN companies c USING(company_id) JOIN metric_definitions m USING(metric_key)
        WHERE d.is_current=1 AND d.value_decimal IS NOT NULL
        ORDER BY c.market,c.symbol,d.period_end DESC,d.metric_key"""
    ).fetchall()
    audit = {
        "المصادر المحفوظة": conn.execute("SELECT count(*) FROM source_documents").fetchone()[0],
        "الملفات الخام المؤرشفة": conn.execute("SELECT count(*) FROM source_artifacts").fetchone()[0],
        "حقائق الاستخراج": conn.execute("SELECT count(*) FROM extracted_facts").fetchone()[0],
        "Mapping معتمد": conn.execute("SELECT count(*) FROM mapped_facts WHERE status='accepted'").fetchone()[0],
        "بانتظار المراجعة": conn.execute("SELECT count(*) FROM mapped_facts WHERE status='review'").fetchone()[0],
        "حقائق منشورة": conn.execute("SELECT count(*) FROM data_points WHERE is_current=1").fetchone()[0],
        "حقول الكتالوج": conn.execute("SELECT count(*) FROM data_catalog_fields WHERE enabled=1").fetchone()[0],
        "قياسات الاكتمال": conn.execute("SELECT count(*) FROM company_completeness").fetchone()[0],
        "إدراجات نشطة": conn.execute("SELECT count(*) FROM listings WHERE active=1").fetchone()[0],
        "فترات مقاسة التغطية": conn.execute("SELECT count(*) FROM coverage_status").fetchone()[0],
        "عناصر الباكلوق المفتوحة": conn.execute("SELECT count(*) FROM backlog_items WHERE status IN ('open','ready','in_progress','blocked')").fetchone()[0],
        "استثناءات مفتوحة": conn.execute("SELECT count(*) FROM exceptions WHERE status='open'").fetchone()[0],
    }
    completeness = {row["company_id"]: (row["populated"], row["expected"]) for row in conn.execute(
        """SELECT company_id,sum(populated_fields) populated,sum(expected_fields) expected
        FROM company_completeness GROUP BY company_id""").fetchall()}
    conn.close()

    csv_target = Path(csv_path)
    csv_target.parent.mkdir(parents=True, exist_ok=True)
    with csv_target.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["الشركة", "السوق", "الرمز", "السنة", "الربع", "نهاية الفترة", "نوع الفترة", "التصنيف", "المقياس", "النطاق", "الأبعاد", "القيمة", "العملة", "الوحدة", "المصدر"])
        for row in rows:
            writer.writerow([row["name"], row["market"], row["symbol"], row["fiscal_year"], row["fiscal_quarter"] or "", row["period_end"], row["period_kind"], row["category"], AR_METRICS.get(row["metric"], row["metric"]), row["scope"], row["dimensions_json"], row["value"], row["currency"], row["unit"], row["source_url"]])

    groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        groups.setdefault(f'{row["name"]} ({row["symbol"]})', []).append(row)
    sections = []
    company_options=[]
    company_cards=[]
    for company, company_rows in groups.items():
        symbol=company_rows[0]["symbol"]
        company_options.append(f'<option value="{html.escape(symbol)}">{html.escape(company)}</option>')
        latest=max(row["period_end"] for row in company_rows)
        company_id = next(row["company_id"] for row in company_rows)
        populated, expected = completeness.get(company_id, (0, 0))
        score = (100 * populated / expected) if expected else 0
        company_cards.append(f'<div class="company-card"><strong>{html.escape(company)}</strong><span>{len(company_rows):,} حقيقة حالية</span><span>اكتمال الكتالوج: {score:.1f}% ({populated:,}/{expected:,})</span><span>أحدث فترة: {html.escape(latest)}</span></div>')
        body = []
        for row in company_rows:
            value = float(row["value"])
            shown = _display_value(value, row["currency"], row["unit"])
            period = {"fy": "سنوي", "quarter": "ربع", "ytd": "من بداية السنة", "instant": "رصيد"}.get(row["period_kind"], row["period_kind"])
            dimensions = json.loads(row["dimensions_json"])
            dimension_text = "، ".join(f"{key}: {value}" for key, value in dimensions.items()) or row["scope"]
            search_text=f'{AR_METRICS.get(row["metric"], row["metric"])} {row["metric"]} {dimension_text}'.lower()
            body.append(f'<tr data-company="{html.escape(row["symbol"])}" data-kind="{html.escape(row["period_kind"])}" data-category="{html.escape(row["category"])}" data-search="{html.escape(search_text)}"><td>{html.escape(row["period_end"])}</td><td>{html.escape(period)}</td><td>{html.escape(row["category"])}</td><td>{html.escape(AR_METRICS.get(row["metric"], row["metric"]))}<small>{html.escape(row["metric"])}</small></td><td>{html.escape(dimension_text)}</td><td class="value">{html.escape(shown)}</td><td><a target="_blank" rel="noopener" href="{html.escape(row["source_url"],quote=True)}">فتح المصدر</a></td></tr>')
        sections.append(f'<section class="company-section" data-company-section="{html.escape(symbol)}"><h2>{html.escape(company)}</h2><div class="table"><table><thead><tr><th>الفترة</th><th>النوع</th><th>التصنيف</th><th>البيان</th><th>الأبعاد</th><th>القيمة</th><th>التوثيق</th></tr></thead><tbody>{"".join(body)}</tbody></table></div></section>')
    cards=''.join(f'<div class="card"><b>{value:,}</b><span>{html.escape(label)}</span></div>' for label,value in audit.items())
    refreshed=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    page = f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>بيانات الشركات المالية</title><style>:root{{--green:#0b5d50;--ink:#17212b;--muted:#60707c}}*{{box-sizing:border-box}}body{{font-family:Tahoma,Arial,sans-serif;background:#f3f6f8;color:var(--ink);margin:0;line-height:1.6}}main{{max-width:1280px;margin:auto;padding:28px}}h1{{margin:0 0 6px}}h2{{margin-top:0}}.note{{color:var(--muted);margin:0 0 6px}}.refreshed{{color:#087f5b;font-weight:bold;margin:0 0 20px}}.cards,.company-cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:16px 0}}.card,.company-card{{border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:4px}}.card{{background:#163c35;color:white}}.card b{{font-size:24px}}.card span{{color:#cce4dc}}.company-card{{background:white;border:1px solid #dce6e3}}.company-card span{{font-size:13px;color:var(--muted)}}.controls{{position:sticky;top:0;z-index:5;display:grid;grid-template-columns:2fr repeat(3,1fr);gap:10px;background:#f3f6f8ee;backdrop-filter:blur(8px);padding:12px 0}}input,select{{width:100%;padding:11px;border:1px solid #cdd9d5;border-radius:10px;background:white;font:inherit}}#result-count{{color:var(--muted);margin:5px 0}}section{{background:white;border-radius:14px;padding:20px;margin:18px 0;box-shadow:0 3px 14px #0001}}.table{{overflow:auto;max-height:680px}}table{{width:100%;border-collapse:collapse;white-space:nowrap}}th,td{{padding:11px;border-bottom:1px solid #e7ecef;text-align:right}}th{{position:sticky;top:0;background:#edf5f2;z-index:2}}td small{{display:block;color:#7a8790;font-family:Consolas,monospace;font-size:11px}}td.value{{direction:ltr;text-align:right;font-variant-numeric:tabular-nums}}a{{color:#087f5b;font-weight:bold;text-decoration:none}}tr:hover{{background:#f7fbfa}}.hidden{{display:none!important}}@media(max-width:760px){{main{{padding:12px}}section{{padding:12px}}.controls{{grid-template-columns:1fr 1fr}}.controls input{{grid-column:1/-1}}}}</style></head><body><main><h1>مصنع البيانات المالية</h1><p class="note">قاعدة موحّدة للسوق السعودي والأمريكي. كل قيمة منشورة اجتازت الاستخراج والتطبيع والتحقق ومرتبطة بمصدرها الرسمي.</p><p class="refreshed">آخر بناء وفحص: {html.escape(refreshed)}</p><div class="cards">{cards}</div><div class="company-cards">{''.join(company_cards)}</div><div class="controls"><input id="search" type="search" placeholder="ابحث باسم المقياس: الإيرادات، صافي الربح..."><select id="company"><option value="">كل الشركات</option>{''.join(company_options)}</select><select id="kind"><option value="">كل الفترات</option><option value="fy">سنوي</option><option value="quarter">ربع</option><option value="ytd">تراكمي</option><option value="instant">رصيد</option><option value="ttm">TTM</option></select><select id="category"><option value="">كل التصنيفات</option><option value="financial">مالي</option><option value="operational">تشغيلي</option><option value="ratio">نسب</option><option value="calculated">محسوب</option></select></div><p id="result-count"></p>{''.join(sections)}</main><script>(()=>{{const controls=['search','company','kind','category'].map(id=>document.getElementById(id));const rows=[...document.querySelectorAll('tbody tr')];const sections=[...document.querySelectorAll('.company-section')];function apply(){{const search=controls[0].value.trim().toLowerCase(),company=controls[1].value,kind=controls[2].value,category=controls[3].value;let shown=0;rows.forEach(row=>{{const match=(!search||row.dataset.search.includes(search))&&(!company||row.dataset.company===company)&&(!kind||row.dataset.kind===kind)&&(!category||row.dataset.category===category);row.classList.toggle('hidden',!match);if(match)shown++;}});sections.forEach(section=>section.classList.toggle('hidden',![...section.querySelectorAll('tbody tr')].some(row=>!row.classList.contains('hidden'))));document.getElementById('result-count').textContent=`عرض ${{shown.toLocaleString('ar-SA')}} من ${{rows.length.toLocaleString('ar-SA')}} سجل`}}controls.forEach(control=>control.addEventListener(control.tagName==='INPUT'?'input':'change',apply));apply();}})();</script></body></html>'''
    html_target = Path(html_path)
    html_target.parent.mkdir(parents=True, exist_ok=True)
    html_target.write_text(page, encoding="utf-8")
