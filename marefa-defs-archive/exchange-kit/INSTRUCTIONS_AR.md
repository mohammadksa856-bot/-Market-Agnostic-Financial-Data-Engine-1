# حزمة تبادل Snapshot العقود

**الخطوات:**
1. **فحص البنية:** `python3 tools/snapshot_tool.py validate codex-coverage-snapshot.json`. رمز الخروج 2 يعني ملفًا غير صالح، مع قائمة بكل خطأ.
2. **المقارنة مع حزمتنا:** `python3 tools/snapshot_tool.py compare OURS.json codex-coverage-snapshot.json --out compare.json`.
3. **التكامل على نسخة ثالثة:** `integration/integration_run.sh <نسخة المحرك الأصلي> codex-coverage-snapshot.json OURS.json <مجلد فارغ> [ملفات استيراد Codex]`.
   - يستنسخ المحرك الأصلي ويطبق حزمة التصحيحات ويعيد البناء ويصدر Snapshot للنسخة.
   - لا يكتب في المحرك الأصلي.
4. **التغطية المجمعة:** في `4-summary.json`. كل مفتاح يُحتسب مرة واحدة لكل خانة.
5. **التعارضات غير القابلة للحسم الآلي:** في `5-escalations.json`، في قسمين:
   - `needs_review`: تعارض القيم والوحدات وبدايات الفترات والتعريفات والأوزان. تُرفع لمراجع.
   - `coverage_differences`: فترات لدى طرف دون الآخر، للعلم.

   لا يُحسم شيء آليًا.

**أقل Snapshot مقبول:** المفاتيح كأسماء فقط مع `record_default: "missing"`. انظر `examples/example-snapshot-minimal.json`.

**الحزمة لا تحتوي بيانات شركات.** الأمثلة اصطناعية.
