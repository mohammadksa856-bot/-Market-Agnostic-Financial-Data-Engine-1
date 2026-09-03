from __future__ import annotations

import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .query import FinancialQueryService


HELP = """الأوامر المتاحة:
/company SA 2222
/profile SA 2222
/metric SA 2222 revenue
/snapshot SA 2222 2025-12-31
/coverage SA 2222
/health"""


def _shown(value, unit: str, currency: str) -> str:
    try: number=float(value)
    except (TypeError,ValueError): return str(value)
    if unit == "ratio": return f"{number*100:,.2f}%"
    if unit == "percent": return f"{number:,.2f}%"
    if unit in {"SAR","USD"}: return f"{number:,.0f} {currency}"
    return f"{number:,.3f} {unit}".strip()


def answer_command(db_path: str, text: str) -> str:
    parts=text.strip().split(); command=parts[0].split("@",1)[0].lower() if parts else "/help"
    query=FinancialQueryService(db_path)
    try:
        if command in {"/start","/help"}: return HELP
        if command == "/health":
            health=query.health(); return "✅ القاعدة تعمل\n" + "\n".join(
                f"{key}: {value}" for key,value in health.items())
        if command == "/company" and len(parts)==3:
            item=query.company_overview(parts[1],parts[2])
            counts="، ".join(f"{key}: {value}" for key,value in item["fact_counts"].items()) or "لا توجد بيانات"
            return f"{item['name']} ({item['market']}:{item['symbol']})\nالعملة: {item['currency']}\nآخر تقرير: {item['latest_filing']}\nالحقائق: {counts}"
        if command == "/profile" and len(parts)==3:
            dossier=query.company_dossier(parts[1],parts[2]); overview=dossier["overview"]
            attributes=dossier["attributes"]
            def attribute(key, default="غير متوفر"):
                return attributes.get(key,{}).get("value",default)
            def metric(key):
                rows=query.metric_history(parts[1],parts[2],key,1)
                return _shown(rows[0]["value"],rows[0]["unit"],rows[0]["currency"]) if rows else "غير متوفر"
            return (
                f"{attribute('company_name_ar',overview['name'])} ({overview['market']}:{overview['symbol']})\n"
                f"النشاط: {attribute('business_description_ar',attribute('business_description'))}\n"
                f"الرئيس التنفيذي: {attribute('ceo_name')}\n"
                f"الرئيس: {attribute('chairman_name')}\n"
                f"الموظفون: {attribute('employees')}\n"
                f"الإيرادات: {metric('revenue')}\nصافي الدخل: {metric('net_income')}\n"
                f"التدفق التشغيلي: {metric('operating_cash_flow')}\nالأصول: {metric('total_assets')}\n"
                f"الإنتاج: {metric('total_hydrocarbon_production')}\n"
                f"الملكية المسجلة: {len(dossier['ownership'])}، الإفصاحات: {len(dossier['disclosures'])}، "
                f"الحقائق: {sum(overview['fact_counts'].values())}"
            )
        if command == "/metric" and len(parts) in {4,5}:
            limit=int(parts[4]) if len(parts)==5 else 8
            rows=query.metric_history(parts[1],parts[2],parts[3],limit)
            if not rows: return "لا توجد نتائج لهذا المقياس."
            lines=[f"{row['period_end']} ({row['period_kind']}): {_shown(row['value'],row['unit'],row['currency'])}" for row in rows]
            return f"{parts[3]} — {parts[1].upper()}:{parts[2].upper()}\n" + "\n".join(lines)
        if command == "/snapshot" and len(parts) in {3,4}:
            result=query.snapshot(parts[1],parts[2],parts[3] if len(parts)==4 else None)
            lines=[]
            for metric,rows in list(result["metrics"].items())[:30]:
                row=rows[0]; lines.append(f"{metric}: {_shown(row['value'],row['unit'],row['currency'])}")
            return f"لقطة {result['market']}:{result['symbol']} — {result['period_end']}\n" + "\n".join(lines)
        if command == "/coverage" and len(parts)==3:
            rows=query.coverage(parts[1],parts[2],20)
            if not rows: return "لا توجد نتائج تغطية."
            return "\n".join(f"{row['period_end']} {row['period_kind']}: {row['status']} ({row['available_count']}/{row['expected_count']})" for row in rows)
        return HELP
    except (KeyError,ValueError) as error:
        return f"تعذر تنفيذ الطلب: {error}\n\n{HELP}"
    finally:
        query.close()


class TelegramBot:
    """Minimal long-polling adapter; all financial access stays read-only."""
    def __init__(self, db_path: str, token: str, opener=urlopen):
        if not token or ":" not in token: raise ValueError("a valid Telegram bot token is required")
        self.db_path=db_path; self.base=f"https://api.telegram.org/bot{token}"; self.opener=opener

    def _call(self, method: str, payload: dict):
        data=urlencode(payload).encode("utf-8")
        with self.opener(Request(f"{self.base}/{method}",data=data),timeout=70) as response:
            result=json.loads(response.read())
        if not result.get("ok"): raise RuntimeError(f"Telegram API error: {result.get('description','unknown')}")
        return result["result"]

    def serve(self, poll_seconds: int = 2):
        offset=0
        while True:
            updates=self._call("getUpdates",{"offset":offset,"timeout":60,"allowed_updates":json.dumps(["message"])})
            for update in updates:
                offset=max(offset,int(update["update_id"])+1)
                message=update.get("message") or {}; text=message.get("text")
                if not text: continue
                reply=answer_command(self.db_path,text)[:4000]
                self._call("sendMessage",{"chat_id":message["chat"]["id"],"text":reply})
            if not updates: time.sleep(max(0,min(poll_seconds,5)))
