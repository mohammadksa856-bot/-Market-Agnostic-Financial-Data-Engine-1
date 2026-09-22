from __future__ import annotations

import json
from html import escape


def company_viewer_html(page: dict) -> str:
    company = page.get("company", {})
    sections = page.get("sections", {})
    profile = sections.get("profile", {})
    financials = sections.get("financials", {})
    market = sections.get("market", {})
    completeness = company.get("completeness") or page.get("data_quality", {}).get("completeness", {})

    def text(value) -> str:
        if isinstance(value, dict) and "value" in value:
            value = value["value"]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        return escape("—" if value in (None, "") else str(value))

    def number(value, unit="") -> str:
        try:
            amount = float(value)
            if unit == "SAR" and abs(amount) >= 1_000_000_000:
                return f"{amount / 1_000_000_000:,.2f} مليار ر.س"
            if unit == "SAR" and abs(amount) >= 1_000_000:
                return f"{amount / 1_000_000:,.2f} مليون ر.س"
            return f"{amount:,.2f} {escape(unit)}".strip()
        except (TypeError, ValueError):
            return text(value)

    annual_data = financials.get("annual", {})
    if isinstance(annual_data, list):
        annual = next((item for item in annual_data if item.get("status") == "available"), {})
    else:
        annual = annual_data
    metrics = annual.get("metrics", {})
    metric_cards = []
    for key, label in (
        ("revenue", "الإيرادات"), ("gross_profit", "إجمالي الربح"),
        ("operating_income", "الربح التشغيلي"), ("net_income", "صافي الربح"),
        ("operating_cash_flow", "التدفق التشغيلي"), ("free_cash_flow", "التدفق الحر"),
        ("total_assets", "إجمالي الأصول"), ("total_equity", "حقوق الملكية"),
    ):
        item = metrics.get(key)
        if isinstance(item, list):
            item = item[0] if item else None
        if item:
            metric_cards.append(f'<div class="card"><small>{label}</small><strong>{number(item.get("value"), item.get("unit", ""))}</strong></div>')

    profile_rows = []
    for key, label in (
        ("business_description", "نبذة"), ("business_model", "نموذج العمل"),
        ("products_services", "المنتجات والخدمات"), ("geographic_presence", "الانتشار الجغرافي"),
        ("headquarters_address", "المقر"), ("founding_date", "التأسيس"),
        ("auditor", "المراجع الخارجي"), ("website", "الموقع الرسمي"),
    ):
        if key in profile:
            profile_rows.append(f"<dt>{label}</dt><dd>{text(profile[key])}</dd>")

    category_rows = "".join(
        f'<tr><td>{text(item.get("category"))}</td><td>{text(item.get("populated_fields"))}/{text(item.get("expected_fields"))}</td><td>{float(item.get("completeness_score", 0))*100:.0f}%</td></tr>'
        for item in completeness.get("categories", [])
    )
    score = float(completeness.get("completeness_score", 0)) * 100
    counts = company.get("fact_counts", {})
    latest = market.get("latest") or {}
    links = (("2222", "أرامكو"), ("2010", "سابك"), ("7010", "stc"),
             ("7020", "موبايلي"), ("7030", "زين"), ("7040", "قو"))
    nav = "".join(f'<a href="/view/SA/{symbol}">{label}</a>' for symbol, label in links)
    css = """
*{box-sizing:border-box}body{margin:0;background:#07111f;color:#e8eef7;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.7}.wrap{max-width:1100px;margin:auto;padding:18px}nav{display:flex;gap:8px;overflow:auto;padding:8px 0 18px}nav a{white-space:nowrap;color:#a7f3d0;background:#11243a;padding:8px 13px;border-radius:20px;text-decoration:none}.hero,.panel{background:#0d1b2d;border:1px solid #20364f;border-radius:18px;padding:20px;margin-bottom:16px}h1{margin:0;font-size:clamp(26px,6vw,48px)}h2{margin:0 0 14px;color:#7dd3fc}.muted,small{color:#9fb0c5}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px}.card{background:#11243a;border-radius:14px;padding:14px;min-height:95px}.card strong{display:block;font-size:19px;margin-top:7px;color:#fff}.score{font-size:44px;color:#34d399;font-weight:800}dl{margin:0}dt{color:#7dd3fc;font-weight:700;margin-top:13px}dd{margin:2px 0;white-space:pre-wrap;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:9px;border-bottom:1px solid #20364f;text-align:right}.scroll{max-height:430px;overflow:auto}footer{color:#7890aa;text-align:center;padding:20px}@media(max-width:550px){.wrap{padding:10px}.hero,.panel{padding:15px;border-radius:14px}}
"""
    title = text(profile.get("company_name_ar", company.get("name")))
    return f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | معرفة استثمار</title><style>{css}</style></head><body><main class="wrap"><nav>{nav}</nav>
<section class="hero"><span class="muted">{text(company.get("exchange"))} · {text(company.get("symbol"))}</span><h1>{title}</h1><div class="muted">{text(company.get("name"))} · {text(company.get("sector"))} · {text(company.get("industry"))}</div></section>
<section class="grid"><div class="card"><small>اكتمال قاعدة البيانات</small><div class="score">{score:.1f}%</div></div><div class="card"><small>حقائق مالية</small><strong>{text(counts.get("financial", 0))}</strong></div><div class="card"><small>مؤشرات محسوبة</small><strong>{text(counts.get("calculated", 0))}</strong></div><div class="card"><small>آخر إقفال</small><strong>{number(latest.get("close"), latest.get("currency", "SAR"))}</strong><small>{text(latest.get("observed_at"))}</small></div></section>
<section class="panel"><h2>أحدث سنة مالية · {text(annual.get("period_end"))}</h2><div class="grid">{''.join(metric_cards) or '<span class="muted">لا توجد بيانات سنوية منشورة.</span>'}</div></section>
<section class="panel"><h2>عن الشركة</h2><dl>{''.join(profile_rows) or '<dd>لا توجد معلومات وصفية منشورة.</dd>'}</dl></section>
<section class="panel"><h2>تغطية فئات البيانات</h2><div class="scroll"><table><thead><tr><th>الفئة</th><th>الحقول</th><th>النسبة</th></tr></thead><tbody>{category_rows}</tbody></table></div></section>
<footer>عرض تجريبي مباشر من قاعدة البيانات · للقراءة فقط</footer></main></body></html>'''
