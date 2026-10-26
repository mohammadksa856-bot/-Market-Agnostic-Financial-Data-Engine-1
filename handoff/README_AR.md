# حزمة تسليم عمل معرفة (2026-10-26)

هذا الفرع (`handoff/marefa-work-20261026`) هو `prod/sabic-production` كما هو، ومعه مجلد `handoff/`. لم يُدمج شيء في `main`.

## الفروع المرفوعة
| الفرع | المحتوى |
|---|---|
| `prod/sabic-production` | آخر عمل سابك: الدفعات 1 إلى 4. Implementation `745c814`، والتغطية الموزونة 74.8603 |
| `prod/aramco-production` | فرع أرامكو. يملكه Codex، ولم يُعدَّل في دفعات سابك |
| `fixes/correctness-pack`، `defs/independent-validation`، `sprint/contract-derivations` | الفروع التي بُني عليها العمل |
| `handoff/marefa-work-20261026` | هذا الفرع |

## محتويات `handoff/`
| المجلد | المحتوى |
|---|---|
| `reports/` | تقارير الدفعات 1 إلى 4 بالعربية، ومواصفة حزمة AWS |
| `sabic-builders/` | سكربتات بناء ملفات `data/imports/sabic-*.json` من ملفات PDF الرسمية. كل رقم فيها يُطابق مع صفحته |
| `tools/` | الأدوات (انظر التفاصيل بعد الجدول) |
| `field-availability/conclusive-candidates/` | الدليل المستخدم في البناء الافتراضي |
| `field-availability/draft-unsigned/` | مسودات N/A غير موقعة، **لا تُستخدم في القياس** |
| `results/` | نتيجة الجاهزية وأثر الدفعة الرابعة على الشركات |
| `sources/` | فهارس المصادر: فهرس تقارير سابك مع الروابط وsha256، وقائمة التقارير العربية، وسجل GLEIF |

**الأدوات في `tools/`:**
- `run_build.sh`: البناء الكامل.
- `missing.py`: مقارنة الجاهزية بين بناءين.
- `stale.py`: تشخيص القيم المشتقة القديمة.
- `q.py`: استعلام سريع على قاعدة البيانات.
- `fetch_pdf_browser.js`: تنزيل ملفات PDF من موقع سابك. الموقع يحجب curl، فالتنزيل يمر عبر Chromium.

ملفات PDF المصدرية (نحو 323MB) غير موجودة في git. روابطها وبصماتها في `sources/`.

## التشغيل محليًا (WSL أو Linux)
```bash
git clone -b handoff/marefa-work-20261026 https://github.com/mohammadksa856-bot/-market-agnostic-financial-data-engine-1 marefa-engine
cd marefa-engine
PYTHONPATH=src python3 -m unittest discover -s tests      # 612 اختبارًا
bash handoff/tools/run_build.sh local1                     # يجب أن يعطي 74.8603 لسابك
python3 handoff/tools/missing.py handoff/results/ready-sabic-batch4.json runs/local1/ready-2010.json
```

**ولمتابعة العمل مع Claude:**
- **من جهازك:** شغّل `claude` داخل المجلد.
- **عن بُعد:** شغّل `claude remote-control` من المجلد نفسه، فتظهر الجلسة في تطبيق Claude Code. هذا يسمح أيضًا بقراءة أرشيف AWS المحلي في مكانه، مثل `/mnt/c/Users/Mohammed856/Documents/Marefa-AWS-Recovery/`.
- **من جلسة سحابية:** اختر المستودع وهذا الفرع.

## قيود العمل السارية
- لا تغيير على العقد أو أوزانه أو مقاماته.
- الحجب 7/22/142/0 ثابت.
- لا merge ولا deploy ولا اعتماد مالي ذاتي.
- لا قيم مختلقة.
- مسودات N/A لا تُطبق قبل التوقيع.
- أرامكو مسؤولية Codex.
