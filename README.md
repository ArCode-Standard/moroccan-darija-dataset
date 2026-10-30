# معجم الدارجة المغربية — Moroccan Darija Lexicon

مجموعة معطيات معجمية للدارجة المغربية، موجّهة لتدريب نماذج الذكاء الاصطناعي ولبحوث المعالجة الآلية للغة.

A lexical dataset of Moroccan Arabic (Darija) intended for AI training and natural language processing research.

## المحتوى / Contents

| العنصر | العدد |
|---|---|
| المدخلات المعجمية | 887 |
| الفئات | 38 |
| الملف | `data/moroccan-darija.json` |

كل مدخل يحتوي على الكلمة بالخط العربي، ونسخة لاتينية بأسلوب فرنسي/عربيزي، ومقابلها بالفصحى، وترجمتها بالفرنسية.

## بنية الملف / File structure

```json
{
  "meta": {},
  "categories": [{ "category": "تحيات", "count": 17 }],
  "entries": [
    {
      "id": 1,
      "category": "تحيات",
      "darija_ar": "السلام عليكم",
      "darija_latin": "salam 3likoum",
      "fusha_ar": "السلام عليكم",
      "fr": "Bonjour / paix sur vous"
    }
  ]
}
```

### الحقول / Fields

| الحقل | الوصف |
|---|---|
| `id` | معرّف تسلسلي فريد |
| `category` | الفئة الدلالية بالعربية |
| `darija_ar` | الكلمة أو العبارة بالخط العربي |
| `darija_latin` | الكتابة اللاتينية الاستعمالية (عربيزي/فرنسية) |
| `fusha_ar` | المقابل بالفصحى |
| `fr` | الترجمة الفرنسية |

## الكتابة اللاتينية / Transliteration

الكتابة اللاتينية استنساخ مبسّط للاستعمال الشائع في الرسائل والشبكات الاجتماعية، وليست نظاما معياريا.

| الرمز | الحرف |
|---|---|
| `3` | ع / ء |
| `4` | غ |
| `7` | ح |
| `9` | ق |
| `kh` | خ |
| `gh` | غ (بديل عن `4`) |
| `ch` | ش |
| `ou` | و |
| `y` | ي |

## الاستعمال / Usage

```bash
# عرض عدد المدخلات
jq '.entries | length' data/moroccan-darija.json

# تصفية فئة
jq '.entries[] | select(.category == "الوقت")' data/moroccan-darija.json
```

```python
import json

with open("data/moroccan-darija.json", encoding="utf-8") as f:
    data = json.load(f)

for entry in data["entries"]:
    print(entry["darija_ar"], "→", entry["fr"])
```

## المنهجية / Methodology

- جمع وتحرير يدوي للمفردات والعبارات اليومية، مع مقابل فصيح وترجمة فرنسية.
- مراجعة آلية للبنية: صحة JSON، تسلسل المعرّفات، عدم تكرار المدخلات، سلامة الترميز.
- التحقق من الكتابة والاستعمال الجزئي عبر مصادر معجمية مفتوحة (Wiktionary) دون إعادة نشر محتواها.
- الترجمة الفرنسية تحريرية وليست اقتباسا من مصادر محمية.

## حدود المعطيات / Limitations

- المجموعة موسّعة لكنها **غير شاملة** لكل مفردات الدارجة.
- التغطية الجهوية (الشمال، الصحراء، الريف، البوادي) قيد التوسيع.
- الكتابة اللاتينية غير موحّدة، وقد تختلف بين مدخلات ذات نطق متقارب.
- الترجمة الفرنسية قد تحمل أكثر من مقابل واحد حسب السياق.

## الترخيص / License

هذا المستودع مرخّص بموجب **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

يمكنك النسخ والتوزيع والتعديل للاستخدام غير التجاري بشرط الإسناد:

> ArCode Standard — Moroccan Darija Lexicon — https://github.com/ArCode-Standard/moroccan-darija-dataset

النص الكامل للترخيص في ملف [LICENSE](LICENSE).

## المساهمة / Contributing

- افتح Issue لاقتراح تصحيح أو إضافة.
- أرفق لكل اقتراح: الكلمة بالعربية، الكتابة اللاتينية، المقابل بالفصحى، الترجمة الفرنسية، والمنطقة إن وُجدت.
- لا تُقبل الإضافات التي تكرر مدخلا موجودا أو تفتقد حقلا من الحقول الأربعة.
