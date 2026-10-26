# استعادة AWS لمعرفة استثمار: دليل التنفيذ

كل الأوامر تعمل من **AWS CloudShell** بجلسة دخولك الحالية، بلا مفاتيح جديدة. أي خطوة تنشئ موردًا مدفوعًا لا تعمل إلا مع `--confirm`.

## ما يُحمى دائمًا
- **الخادم الأصلي:** لا يُشغَّل أبدًا. أمر `snapshot` يرفض العمل إن لم يكن الخادم متوقفًا.
- **القرص الأصلي والـ Snapshot:** لا يوجد في الأداة أي أمر يحذفهما. أمر `cleanup` يحذف فقط الخادم المؤقت ونسخة القرص المستعادة.
- **القرص المستعاد:**
  - يُضبط للقراءة فقط على مستوى الجهاز (`blockdev --setro`).
  - يُركَّب دون إعادة تشغيل سجل نظام الملفات (`ro,noload` لـ ext4، و`ro,norecovery` لـ XFS).
  - يتوقف السكربت إن لم يكن التركيب للقراءة فقط.
- **PostgreSQL:** يعمل على طبقة overlay، فتُكتب تعديلاته على قرص خادم الفحص فقط، ثم يُصدَّر بـ `pg_dump`.
- **خادم الفحص:** بلا أي قاعدة دخول (0 inbound rules)، والتحكم عبر SSM فقط.
- **الأسرار:**
  - تُنقل إلى حزمة منفصلة مشفرة بـ AES256، ولا تدخل الأرشيف الرئيسي.
  - كلمة فتح الحزمة تُحفظ في SSM Parameter Store، ولا تظهر في أي تقرير.
  - الأسرار المقصودة: `.env`، ومفاتيح SSH والشهادات، وسجلات الأوامر، وGit config التي تحمل رمزًا في رابطها، وإعدادات حاويات Docker، وأدوار PostgreSQL.

## الخطوات
### 1. افتح CloudShell وارفع الحزمة (مرة واحدة)
1. ادخل إلى console.aws.amazon.com، واختر المنطقة **Europe (Stockholm) eu-north-1**.
2. اضغط أيقونة CloudShell (`>_`) أعلى الصفحة.
3. من **Actions → Upload file** اختر `marefa-cloudshell.zip`.
4. نفّذ:
```bash
unzip -o marefa-cloudshell.zip -d ~/marefa && cd ~/marefa
python3 -c "import boto3" || pip3 install --user boto3
```

### 2. الفحص (مجاني، للقراءة فقط)
```bash
python3 marefa_recovery.py inspect
```
**ما يعرضه:**
- الحساب والخادم وحالته وسبب توقفه.
- القرص: المعرف والحجم والتشفير ومفتاح KMS وإعداد DeleteOnTermination.
- الـ Snapshots السابقة.
- اختبار الصلاحيات بـ DryRun.
- الأسعار الفعلية من AWS Pricing API، والتكلفة حسب المساحة المستخدمة.

**أرسل لي** محتوى الملف `~/marefa-recovery/01-inspect.json`، أو صورة من الناتج. لا يحتوي أي بيانات اعتماد.

### 3. الـ Snapshot (بعد موافقتك)
```bash
python3 marefa_recovery.py snapshot --confirm
```
- ينتظر حتى يكتمل.
- يقيس الحجم الفعلي المكتوب على القرص، ويعرض التكلفة الدقيقة للخطوة التالية.
- إن أُغلق CloudShell في أثناء الانتظار، أعد الأمر نفسه: يكمل متابعة الـ Snapshot نفسه ولا ينشئ آخر.

### 4. القرص المؤقت وخادم الفحص (بعد موافقتك على التكلفة)
```bash
python3 marefa_recovery.py launch --confirm
```
**ينشئ:**
- حاوية S3 خاصة: الوصول العام محجوب، والتشفير مفعّل، وHTTPS فقط.
- دورًا مؤقتًا لخادم الفحص، صلاحياته محصورة في هذه الحاوية وفي SSM.
- مجموعة أمان بلا أي قاعدة دخول.
- خادم `t3.medium`، وقرصًا جديدًا من الـ Snapshot مربوطًا به.

### 5. الاستخراج والجرد
```bash
python3 marefa_recovery.py extract
```
- قد يستغرق ساعة أو أكثر حسب الحجم.
- إن انقطع CloudShell، أعد الأمر نفسه: يتابع العملية الجارية على الخادم ولا يبدأها من جديد.

**النتيجة في S3:**

| المسار | المحتوى |
|---|---|
| `filesystems/*.tar.gz` | نظام الملفات كاملًا بالبنية والصلاحيات، ما عدا الأسرار |
| `databases/sqlite-consistent.tar.gz` | نسخ SQLite متسقة، عبر `.backup` |
| `databases/postgres-N/*.dump` و`*-schema.sql` | قواعد PostgreSQL، بعد تشغيل نسخة منها على overlay |
| `secrets/secrets.tar.gz.gpg` | الأسرار، مشفرة |
| `inventory/` و`inventory.json` و`manifest.json` | الجرد، وقائمة الملفات بالحجم وبصمة SHA256 |

**أرسل لي** الملف `~/marefa-recovery/inventory.json`: من **Actions → Download file** حمّله إلى جهازك، ثم أرفقه في المحادثة. هو الذي أبني عليه الجرد والمقارنة بمحركنا.

### 6. النقل إلى Windows
1. في CloudShell:
   ```bash
   python3 marefa_recovery.py presign
   ```
2. من **Actions → Download file** حمّل `~/marefa-recovery/download-list.tsv`. فيه روابط مؤقتة، **فلا تشاركه مع أحد**.
3. على جهازك، افتح PowerShell في مجلد سكربت `Receive-MarefaRecovery.ps1` ونفّذ:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\Receive-MarefaRecovery.ps1 -ListFile "$HOME\Downloads\download-list.tsv"
   ```

**ما يفعله السكربت:**
- يتحقق من المساحة المتاحة قبل التنزيل.
- ينزّل عبر HTTPS، ويستأنف الملف إن انقطع.
- يطابق بصمة SHA256 لكل ملف، ويعزل أي ملف لا يطابق.
- يكتب `SHA256SUMS.txt`.
- يفك قواعد البيانات، ويختبر فتحها: SQLite بـ `quick_check`، وPostgreSQL بـ `pg_restore --list` إن كان مثبتًا، وإلا بفحص ترويسة الملف.
- يقرأ الأرشيفات من أولها إلى آخرها.
- المكان: `C:\Users\Mohammed856\Documents\Marefa-AWS-Recovery\`.

**إن انتهت صلاحية الروابط:** أعد `presign` وشغّل السكربت مرة أخرى، فيتخطى ما تحقق منه.

**أرسل لي** الملف `verify-report.json`. لا يحتوي روابط ولا أسرارًا. لن أعتبر الاستعادة ناجحة قبل أن أراه.

**فك نظام الملفات كاملًا على Windows** اختياري، بـ `-ExtractFilesystems`. روابط Linux الرمزية قد لا تُنشأ على Windows، والأرشيف نفسه هو النسخة المرجعية الكاملة. لفكه بدقة كاملة استخدم WSL.

### 7. بعد التحقق المحلي
```bash
python3 marefa_recovery.py cleanup --confirm
```
- **يحذف:** خادم الفحص، ونسخة القرص المستعادة، ومجموعة الأمان.
- **يبقى:** الخادم الأصلي وقرصه والـ Snapshot وحاوية S3.
- احذف حاوية S3 بنفسك متى شئت، بعد أن تتأكد من النسخة المحلية.

**فتح حزمة الأسرار عند الحاجة فقط:**
1. من CloudShell، اقرأ كلمة فتح الحزمة: `aws ssm get-parameter --name /marefa-recovery/secrets-passphrase --with-decryption --query Parameter.Value --output text`
2. على جهازك: `gpg -d secrets.tar.gz.gpg > secrets.tar.gz`
3. لا تضع الكلمة في المحادثة.

## IAM Role بصلاحيات مؤقتة لبيئتي (البند 7)
- **الإمكانية:** بيئتي لا تملك هوية AWS يمكن ربطها بدور مباشرة (لا يوجد OIDC). البديل الوحيد: تُصدر أنت من CloudShell بيانات اعتماد مؤقتة (`aws sts assume-role`، أقصاها 12 ساعة)، وتضعها في متغيرات البيئة، ثم تفتح جلسة جديدة.
- **التوصية:** لا حاجة لذلك. مسار CloudShell أعلاه يغطي التنفيذ كله، والمخرجات التي أحتاجها (`01-inspect.json` و`inventory.json` و`verify-report.json`) لا تحمل أسرارًا، وتصلني مرفقة في المحادثة.

## التكلفة
- **مصدرها:** يعرضها `inspect` من AWS Pricing API، ثم `snapshot` بالحجم الفعلي.
- **أسعار التخطيط (قائمة، تقريبية):**
  - Snapshot: نحو $0.05 لكل GB شهريًا، على المساحة المكتوبة فقط.
  - قرص gp3 المؤقت: نحو $0.084 لكل GB شهريًا، ويُحسب بالساعات.
  - خادم `t3.medium`: نحو $0.045 للساعة.
  - النقل إلى الإنترنت: 100 GB شهريًا مجانية للحساب، ثم نحو $0.09 لكل GB.
  - تخزين S3: نحو $0.023 لكل GB شهريًا.
- **مثال لقرص مستخدم بـ 42 GiB:** نحو $2.1 شهريًا للـ Snapshot، ونحو $6 مرة واحدة كحد أعلى دون احتساب النقل المجاني.
