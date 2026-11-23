# معجم الدارجة المغربية | Moroccan Darija Lexicon

**ArCode Standard** · مورد معجمي منظم لتوثيق الدارجة المغربية ودعم البحث في تقنيات اللغة.

A structured lexical resource for Moroccan Darija (ary), maintained by ArCode Standard.

[العربية](#نظرة-عامة) · [English](#overview) · [البيانات](#محتوى-المعجم) · [الاستخدام](#البدء-السريع) · [المساهمة](#المساهمة)

---

## نظرة عامة

يهدف المشروع إلى توثيق مفردات وعبارات الدارجة المغربية، وصيغ كتابتها بالخطين العربي واللاتيني، ومقابلاتها التقريبية بالفصحى والفرنسية. كما يسجل معلومات عن مصدر كل مدخل وحالة مراجعته.

> **الإصدار المعلن:** 1.11.0 — **1,090 مدخلاً** موزعة على **38 فئة**، إضافة إلى **146 مثالاً سياقياً**.

هذا المستودع **معجم (Lexicon)**، وليس مجموعة محادثات (Corpus)، أو مجموعة تعليمات (Instruction Dataset)، أو معيار تقييم (Benchmark). ولا توجد نتائج منشورة تثبت أن محتواه وحده كافٍ لتدريب نموذج لغوي عام أو تقييمه.

## نظرة سريعة

| الخاصية | القيمة |
|---|---|
| اللغة | الدارجة المغربية — ary |
| إصدار البيانات | 1.11.0 |
| عدد المدخلات | 1,090 |
| عدد الفئات | 38 |
| الأمثلة السياقية | 146 |
| حالة المراجعة البشرية | جميع المدخلات pending وفق سجل المشروع |
| الترخيص المعلن | [CC BY-NC 4.0](LICENSE) |

## محتوى المعجم

يتضمن السجل المعجمي الحقول الأساسية التالية:

| الحقل | الوصف |
|---|---|
| id | معرّف المدخل |
| category | الفئة الدلالية |
| darija_ar | الكلمة أو العبارة بالخط العربي |
| darija_latin | تمثيل لاتيني كما يرد في الاستعمال |
| fusha_ar | مقابل أو صياغة تقريبية بالفصحى |
| fr | مقابل أو ترجمة تحريرية بالفرنسية |
| register | تصنيف تحريري: darija أو shared أو fusha |
| provenance | بيانات المصدر والحقوق |
| review | حالة المراجعة وملاحظاتها |

توزيع حقل register في الإصدار 1.11.0:

| التصنيف | عدد المدخلات |
|---|---:|
| shared | 603 |
| darija | 471 |
| fusha | 16 |
| **المجموع** | **1,090** |

هذه التصنيفات تحريرية، ولا تعني أن كل مدخل خضع لمراجعة لغوية مستقلة.

### الكتابة اللاتينية وعربيزي

الكتابة اللاتينية للدارجة المغربية غير موحّدة؛ وقد يكتب المتحدثون الصوت نفسه بطرق مختلفة. يحتفظ المشروع بالتمثيل المسجل ولا يفرض تطبيعاً واحداً قد يفقد معلومات مفيدة.

| الصوت/الحرف | تمثيلات مستعملة |
|---|---|
| غ | gh أو 4 |
| ش | ch أو x |
| ح | 7 |
| خ | kh |
| ع | 3 |
| ق | 9 |

هذه أمثلة وصفية وليست معيار تحويل شاملاً. لا ينبغي دمج مدخلين أو الحكم على صحة كلمة اعتماداً على التشابه اللاتيني وحده.

للتفاصيل: [دليل الكتابة اللاتينية](docs/TRANSLITERATION_STANDARD.md).

## البدء السريع

### 1. استنساخ المستودع وتثبيت المتطلبات

\`\`\`bash
git clone https://github.com/ArCode-Standard/moroccan-darija-dataset.git
cd moroccan-darija-dataset
python -m pip install -r requirements.txt
\`\`\`

### 2. التحقق من البيانات والاختبارات

\`\`\`bash
python scripts/validate_dataset.py
python -m unittest discover -s tests -v
\`\`\`

### 3. استكشاف البيانات باستخدام jq

عدد المدخلات:

\`\`\`bash
jq '.entries | length' data/moroccan-darija.json
\`\`\`

عرض مدخلات فئة محددة:

\`\`\`bash
jq '.entries[] | select(.category == "الوقت")' data/moroccan-darija.json
\`\`\`

### 4. قراءة البيانات باستخدام Python

\`\`\`python
import json

with open("data/moroccan-darija.json", encoding="utf-8") as file:
    dataset = json.load(file)

for entry in dataset["entries"]:
    print(entry["darija_ar"], "→", entry["fr"])
\`\`\`

## بنية المستودع

| المسار | الغرض |
|---|---|
| data/moroccan-darija.json | البيانات المعجمية |
| data/schema.json | JSON Schema للمدخلات |
| data/context-examples.json | أمثلة سياقية مرتبطة بالمدخلات |
| data/context-schema.json | مخطط الأمثلة السياقية |
| data/manifest.template.yaml | قالب بيانات الإصدار والمصادر والحقوق |
| data/sources/registry.json | فهرس مركزي لعائلات المصادر والحقوق المعلنة |
| data/regions/north.json | مساهمة إقليمية أولية؛ 122 مدخلاً pending |
| data/schemas/regional-lexicon.schema.json | مخطط الموارد المعجمية الإقليمية |
| docs/DATA_STRUCTURE.md | بنية البيانات والتوافق والترحيل |
| docs/DATA_COLLECTION.md | سياسة الجمع والموافقة والخصوصية |
| docs/REGIONAL_VARIATION.md | منهجية توثيق التنوع الجهوي |
| scripts/validate_dataset.py | مدقق بنية البيانات والاتساق |\n| scripts/audit_provenance.py | تقرير آلي لفجوات المصدر والحقوق والأدلة |\n| .github/workflows/quality.yml | بوابات جودة تلقائية عبر GitHub Actions |
| tests/ | اختبارات المدقق |
| docs/TRANSLITERATION_STANDARD.md | دليل الكتابة اللاتينية |
| docs/REVIEW_WORKFLOW.md | سير عمل المراجعة |
| docs/DATA_PROVENANCE_AND_RIGHTS.md | سياسة توثيق المصادر والحقوق |
| DATASET_CARD.md | بطاقة وصف مجموعة البيانات |
| CONTRIBUTING.md | دليل المساهمة |

## المصادر ومنشأ البيانات

راجع [سجل المصادر المركزي](data/sources/registry.json)؛ وهو فهرس تجميعي لا يمثل تدقيقاً قانونياً مستقلاً. وللتفاصيل حول بنية الموارد وجمعها وتوثيق الاختلافات الجهوية، راجع [بنية البيانات](docs/DATA_STRUCTURE.md)، و[سياسة الجمع](docs/DATA_COLLECTION.md)، و[التوثيق الجهوي](docs/REGIONAL_VARIATION.md).

وفق سجل الإصدار 1.11.0، يتوزع أصل المدخلات كما يلي:

| نوع المصدر المسجل | العدد | ملاحظة |
|---|---:|---|
| original | 656 | تصنيف المستودع؛ يتضمن 71 مدخلاً أُعيدت صياغتها تحريرياً من مصادر ويب وفق جرد الحقوق |
| dictionary | 271 | من DODa |
| corpus | 126 | مفردات مستخرجة من مواد Wattpad؛ لا تُدرج نصوص القصص في هذا المستودع |
| other | 37 | مفردات من مسرد كتاب Peace Corps Morocco (2011) |
| web | 0 | لا توجد مدخلات مصنفة حالياً بهذا النوع |
| **المجموع** | **1,090** | |

مصادر ومراجع:
- [DODa — Darija Open Dataset](https://github.com/darija-open-dataset/dataset)
- [Peace Corps Morocco — Moroccan Arabic Textbook (2011)](https://www.livelingua.com/course/peace_corps/moroccan_arabic_textbook)

تُسجل معلومات المصدر والحقوق على مستوى المدخل عبر provenance. لكن وجود هذه البيانات الوصفية أو قيمة إذن داخل ملف البيانات لا يشكل، بمفرده، تدقيقاً قانونياً مستقلاً أو دليلاً على امتلاك المشروع حقوق جميع مكونات المدخل.

## الجودة وحدود الاستخدام

يرجى أخذ القيود التالية في الاعتبار:

1. **المراجعة البشرية:** حالة جميع المدخلات pending وفق السجل الحالي؛ ولا يدّعي المشروع اكتمال مراجعة بشرية مستقلة لكل كلمة.
2. **التغطية:** لا توجد دراسة كمية تثبت تمثيلاً متوازناً لجميع مناطق المغرب أو الفئات الاجتماعية أو أنماط الكلام.
3. **المعاني والترجمات:** المقابلات بالفصحى والفرنسية تقريبية وتحريرية، وقد يختلف المعنى بحسب السياق.
4. **الكتابة اللاتينية:** متعددة الأشكال ولا تخضع لتهجئة معيارية واحدة.
5. **الأمثلة السياقية:** توجد 146 عينة في ملف منفصل؛ ولا ينبغي اعتبارها corpus واسعاً أو ممثلاً للمحادثات الطبيعية.
6. **التقييم:** لا يتضمن المستودع benchmark مستقلاً أو نتائج تقييم بشرية منشورة.
7. **الحقوق:** يلزم فحص مصدر كل مكوّن ونطاق الإذن المرتبط به قبل إعادة استخدامه، خصوصاً في المنتجات التجارية.

### ماذا يثبت التحقق الآلي؟

يشغّل المدقق فحوص JSON Schema وفحوصاً بنيوية مخصصة، مثل تفرد المعرّفات واتساق بعض الحقول ومراجع الأمثلة السياقية. نجاح هذه الفحوص لا يثبت صحة المعنى أو شيوع الكلمة أو ملاءمتها ثقافياً أو قانونية إعادة استخدامها.

للاطلاع على آلية المراجعة: [Review Workflow](docs/REVIEW_WORKFLOW.md).  
لتفاصيل المصادر: [Data Provenance & Rights](docs/DATA_PROVENANCE_AND_RIGHTS.md).  
لتقرير التدقيق: [Quality Audit](docs/QUALITY_AUDIT_2026-10.md).

## الترخيص والحقوق

يعلن المستودع عن ترخيص **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**؛ راجع [LICENSE](LICENSE).

- يتطلب الترخيص الإسناد ويقيد الاستخدامات التجارية وفق شروطه.
- لا يمنح هذا الترخيص إذناً بالاستخدام التجاري.
- قد تخضع بعض المواد أو المكونات المأخوذة من مصادر خارجية لحقوق أو شروط إضافية.
- لا تعني إتاحة البيانات على GitHub أن جميع عناصرها خالية من القيود أو أن كل إذن مسجل قد خضع لتحقق قانوني مستقل.
- قبل دمج البيانات في نموذج أو منتج، افحص سجل المصدر والترخيص والإذن لكل عنصر، واستشر مختصاً قانونياً عند الحاجة.

صيغة إسناد مقترحة:

> ArCode Standard, Moroccan Darija Lexicon, https://github.com/ArCode-Standard/moroccan-darija-dataset

هذا القسم وصف للمعلومات المعلنة في المستودع، وليس استشارة قانونية أو ضماناً لحقوق أطراف ثالثة.

## المساهمة

نرحب بالمساهمات التي تحسن دقة المعجم وتوثيقه. عند اقتراح كلمة أو تصحيح، يرجى إضافة ما يتوفر من المعلومات التالية:

- الصيغة بالخط العربي.
- الكتابة اللاتينية والبدائل الشائعة، إن وجدت.
- المعنى والاستعمال وجملة سياقية طبيعية.
- المنطقة أو التنوع المحلي، إذا كان معروفاً ومسنوداً بمعلومة موثوقة.
- مصدر المعلومة وشروط إعادة استخدامها، إن كان المصدر خارجياً.
- توضيح ما إذا كانت المساهمة أصلية أو مأذوناً بمشاركتها.

لا ترسل بيانات شخصية أو معلومات تعريفية عن المتحدثين. ولا تنسخ محتوى من مصادر خارجية دون التحقق من حقوق إعادة استخدامه.

قنوات المساهمة:
- [اقتراح مدخل جديد](https://github.com/ArCode-Standard/moroccan-darija-dataset/issues/new?template=new-entry.yml)
- [الإبلاغ عن تصحيح](https://github.com/ArCode-Standard/moroccan-darija-dataset/issues/new?template=correction.yml)

اقرأ [CONTRIBUTING.md](CONTRIBUTING.md) و[دليل المراجعة](docs/REVIEW_WORKFLOW.md) قبل إرسال مساهمة. لا يصبح المدخل reviewed إلا بعد قرار مراجعة بشرية موثق.

## خارطة الطريق

يعتمد المشروع مبدأ **تحسين الجودة والتوثيق قبل زيادة حجم البيانات**. وتشمل الأولويات:
- استكمال المراجعة اللغوية البشرية وتوثيق قراراتها.
- تحسين أدلة المصدر ومحددات مواضع المصدر وإثباتات الأذونات.
- تطوير المخطط لدعم معلومات السياق ونوع التعبير والتنوع الجهوي عند توفر أدلة.
- نشر تقارير جودة قابلة لإعادة الإنتاج.
- إنشاء موارد مستقلة للمتون النصية، والبيانات المتوازية، والتعليمات، والتقييم، والصوت.

راجع [خطة التطوير 2.0.0](docs/ROADMAP_2.0.md). هذه الخطة تصف أعمالاً مستقبلية ولا تعني أنها أُنجزت.

---

## Overview

The Moroccan Darija Lexicon is a structured lexical resource maintained by **ArCode Standard**. It documents Darija words and expressions, Arabic and Latin-script forms, approximate Modern Standard Arabic equivalents, French glosses, and record-level provenance metadata.

**Published snapshot:** version **1.11.0**, containing **1,090 entries**, **38 categories**, and **146 contextual examples**.

This repository is a **lexicon**, not a conversational corpus, instruction-tuning dataset, or evaluation benchmark. Its current size and review status do not establish that it is sufficient on its own to train or evaluate a general-purpose language model.

### Dataset facts

| Field | Value |
|---|---|
| Language | Moroccan Darija (ary) |
| Published data version | 1.11.0 |
| Entries | 1,090 |
| Categories | 38 |
| Contextual examples | 146 |
| Human review status | All entries marked pending in the current project record |
| Declared license | [CC BY-NC 4.0](LICENSE) |

### Use and limitations

- Latin-script spellings vary; the project does not enforce a single transliteration.
- Arabic and French equivalents are editorial approximations and may be context-dependent.
- Regional and social coverage has not been quantitatively established.
- Automated validation checks structure and consistency, not linguistic correctness or legal permission.
- Record-level provenance is metadata, not independent legal clearance.
- Review the license and provenance of each record before reuse, especially for commercial applications.

### Quick start

\`\`\`bash
git clone https://github.com/ArCode-Standard/moroccan-darija-dataset.git
cd moroccan-darija-dataset
python -m pip install -r requirements.txt
python scripts/validate_dataset.py
python -m unittest discover -s tests -v
\`\`\`

### Contributing

Contributions are welcome. Please include the Darija form, known spelling variants, meaning, a natural context sentence, and source or permission information where relevant. Do not submit personal data or third-party content without appropriate rights.

See [CONTRIBUTING.md](CONTRIBUTING.md), [Review Workflow](docs/REVIEW_WORKFLOW.md), and the [2.0.0 Roadmap](docs/ROADMAP_2.0.md).

---

**ArCode Standard** · [GitHub repository](https://github.com/ArCode-Standard/moroccan-darija-dataset)
