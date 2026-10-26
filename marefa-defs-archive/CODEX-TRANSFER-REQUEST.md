# طلب نقل واحد من Codex — التكامل الأول

**ما يحدث الآن:** الملفان غير موجودين في حاوية Claude. بحثت في الحاوية، وفي مجلدات الرفع، وفي كل الفروع والتاريخ الكامل للمستودعات الثلاثة المتاحة على GitHub. الالتزام `65447bd55e565181e5c608dd47bd39c88127624d` غير موجود فيها، ومسارات Windows لا تصل إلى الحاوية.

**الطريقة (واحدة):** أرفق الملفات الأربعة أدناه برسالة في هذه المحادثة نفسها داخل تطبيق Claude، كملفات أو كملف zip واحد. لا رفع إلى أي مستودع عام.

## الملفات المطلوبة
| # | الملف | لماذا |
|---|---|---|
| 1 | `codex-coverage-snapshot.json` | للفحص والمقارنة وإعادة إنتاج النسب |
| 2 | `codex-special-source-evidence.json` | لفحص أدلة `spare_capacity` و`refinery_utilization` وغيرها |
| 3 | `codex-engine.bundle` | **ضروري لإعادة البناء:** الـ Snapshot مقارنة فقط ولا يكفي لإعادة بناء المحرك. هذه الحزمة تحمل ملفات الاستيراد (`data/imports/*.json`) والإعدادات (`config/`) وشيفرة Codex عند `65447bd` |
| 4 | `SHA256SUMS.txt` | بصمات الملفات الثلاثة |

**الحجم المتوقع:** حزمة git فوق `b70254e` صغيرة؛ 83 التزامًا مماثلًا كانت 212 كيلوبايت.

## أوامر Codex (في نسخة المحرك على جهازه)
```powershell
git cat-file -e 65447bd55e565181e5c608dd47bd39c88127624d
git merge-base --is-ancestor b70254e463c18e893fd042a82ecdad78209384d6 65447bd55e565181e5c608dd47bd39c88127624d; echo $LASTEXITCODE
# 0 = based on b70254e (small bundle):
git bundle create codex-engine.bundle b70254e463c18e893fd042a82ecdad78209384d6..65447bd55e565181e5c608dd47bd39c88127624d
# otherwise (full history):
git bundle create codex-engine.bundle 65447bd55e565181e5c608dd47bd39c88127624d
git bundle verify codex-engine.bundle
Get-FileHash -Algorithm SHA256 codex-coverage-snapshot.json, codex-special-source-evidence.json, codex-engine.bundle |
  ForEach-Object { "{0}  {1}" -f $_.Hash.ToLower(), (Split-Path $_.Path -Leaf) } | Set-Content -Encoding ascii SHA256SUMS.txt
```

## شرطان لإعادة إنتاج النسب بدقة
1. **علامة المحافظ في كل سجل:** إن كانت نسبة 534/685 و75.920313% محسوبة من سجلات، يحتاج كل سجل مغلق حقلًا صريحًا، مثل `"conservative": true|false`. بدونه أعيد إنتاج الإجمالي فقط، وأعلن أن المحافظ غير قابل لإعادة الإنتاج، ولا أخمنه.
2. **مصدر الأرقام المعلنة:** الـ Snapshot صادر عن الالتزام `65447bd` نفسه، بالإعدادات نفسها (`config/factory/field-availability`).

## ما سيحدث عند الاستلام (أمر واحد، `codex_intake.sh`)
0. فحص البصمات.
1. `contract-validate`.
2. إعادة إنتاج 535/685 و76.112621%، و534 و75.920313% إن وُجدت العلامة.
3. المقارنة مع حزمتي.
4. فحص الأدلة الخاصة مقابل قراراتي السابقة.
5. نسخة تكامل ثالثة عند `65447bd`.
6. بناء «قبل»:
   - بتقييمات Codex: لإعادة الإنتاج فقط.
   - **بلا تقييمات غير موقعة:** الرسمي.
7. دمج حزمة التصحيحات، والتزام محلي يكون هو SHA التكامل، ثم الاختبارات. **التعارض يوقف التشغيل، ولا يُحل آليًا.**
8. بناء «بعد» وقياس الأثر قبل وبعد.
9. القياس من سجلات النسخة الموحدة، والتصعيد.

**لا اعتماد مالي.** المحرك الأصلي يُقرأ فقط.
