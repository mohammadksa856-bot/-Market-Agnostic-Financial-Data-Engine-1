# حزمة سابك المصغرة من نسخة AWS (نقل مرة واحدة)

المصدر: قاعدة البيانات المستعادة على جهاز Windows (`Marefa-AWS-Recovery`).
المطلوب: ملف واحد `sabic-aws-export.json` (أو نسخة SQLite مصفّاة)، مع بصمة SHA256 الخاصة به.

## المحتوى
| الجدول | التصفية | الأعمدة |
|---|---|---|
| `data_points` | `company_id='sa:2010'`، **كل النسخ** (`is_current` 0 و1) | كل الأعمدة، بما فيها `metric_key` و`period_kind` و`period_start` و`period_end` و`fiscal_year` و`fiscal_quarter` و`value_decimal` و`unit` و`currency` و`scale` و`source_key` و`source_url` و`filed_at` و`version` و`is_calculated` و`calculation` |
| `source_documents` | الصفوف المرتبطة بـ `source_key` أعلاه | `source_key`، و`source_url`، و`filed_at`، و`form`، و`content_hash` |
| `market_prices` | قائمة سابك | كل الأعمدة |
| `ownership_positions` و`corporate_actions` و`disclosures` و`company_attributes` | `company_id='sa:2010'` | كل الأعمدة |
| قائمة الاختلافات الـ12 | كما ظهرت في تدقيق Codex | المفتاح، والفترة، وقيمة AWS، والقيمة المحلية |

## الشروط
- لا تُدرج كلمات مرور أو مفاتيح أو متغيرات بيئة.
- يُرفق الملف هنا في المحادثة، أو يوضع في مستودع خاص لا عام.

## ما سأفعله عند وصوله
1. أطابق كل هوية/فترة مع ما أنتجته من المصادر الأصلية، أي تقارير sabic.com والتقرير السنوي 2025.
2. لا أستورد إلا ما له مصدر موثق (`source_url` و`content_hash`) لا يتعارض مع المصدر الأصلي.
3. أعرض الاختلافات الـ12 بالقيمتين وبالصفحة في المصدر، ولا أختار قيمة دون دليل.
