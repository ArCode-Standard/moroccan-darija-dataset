# أداة استقبال المرشحات المعجمية

## المتطلبات
`python -m pip install -r requirements-dev.txt`

## 1. جهّز مساهمة JSON
انسخ `data/collection/templates/lexical-candidate.template.json` إلى ملف جديد، ثم عدّل القيم. لا تضف أسماء مستخدمين أو روابط حسابات أو محادثات خاصة أو بيانات شخصية.

- `source_id` يجب أن يكون موجوداً في سجل المصادر.
- `observed_at` تاريخ الملاحظة بصيغة YYYY-MM-DD.
- `privacy_checked` يجب أن يكون true بعد التأكد من خلو المساهمة من البيانات الشخصية.
- `rights_status` و`review_status` يحددهما النظام مبدئياً: unknown وdiscovered.

## 2. معاينة دون حفظ
```bash
python scripts/intake_candidate.py --input path/to/contribution.json --dry-run
```

## 3. إنشاء سجل مرشح
```bash
python scripts/intake_candidate.py --input path/to/contribution.json
```

ينشئ النظام ملفاً في `data/collection/candidates/CAND-XXXXXX.json`. لا يعدّل المعجم الرئيسي ولا يدمج المرشح تلقائياً. راجع الملف ثم افتح Pull Request للمراجعة.

## ملاحظات
- لا يُسمح بإدخال حقول غير معروفة؛ هذا يمنع تمرير بيانات هوية أو حقول غير معتمدة.
- لا يُقبل مصدر غير مسجل.
- لا تُستنتج الحقوق من كون المصدر عاماً أو قابلاً للقراءة.
- يحتفظ المرشح بصيغته الأصلية؛ لا يجري تطبيع Arabizi أو دمج المتغيرات آلياً.
- الأداة محلية ولا تتصل بالمنصات ولا تجمع محتواها.
