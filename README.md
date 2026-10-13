# product-card-generator

Builds **product titles and descriptions in Ukrainian and Russian** from a CSV of attributes, using templates you control, and checks the result: length, duplicate titles, missing attributes and risky claims. Python standard library only, no AI, no internet.

## What it does
- One CSV row per product (any columns). A JSON config holds, per language, a **title template** and a list of **description sentences**. `{placeholders}` are filled from the row.
- **Nothing is invented.** A part in `[square brackets]` disappears when its attribute is empty (`"[ {color}]"`), and a sentence whose attribute is missing is left out, so there are no dangling words, empty fields or "None".
- A sentence can have several **variants**; the variant is chosen deterministically from the SKU, so the same product always gets the same text and different products do not all read identically.
- **Checks** (written to the `issues` column): title and description length limits, a title that repeats another row, attributes you marked `required` that are missing, and risky claim words (for example "best", "100%", "we guarantee", "cures") that marketplaces often reject.
- Output `cards.csv`: `sku, title_uk, desc_uk, title_ru, desc_ru, issues`. Values that start with `=`, `+`, `-`, `@` get a leading `'`.

## Use
```bash
PYTHONPATH=src python3 -m card_gen examples/products.csv --config examples/config.json --out cards.csv
```
Edit `examples/config.json` for your shop: templates, `limits`, `required`, and the languages you need. Tests: `python3 -m unittest discover -s tests`.

## Limits (read this)
- It **assembles** texts from your templates and your data. It does not write marketing copy and it does not translate: the Russian values (`type_ru`, `color_ru`) must be in your CSV.
- Generated descriptions are formulaic. Read a sample before importing; for a few key products write the text by hand.
- Grammar is only as good as your templates (cases and genders are not handled), so keep sentences neutral.
- The risky-word list is short and only a hint; check the rules of your marketplace.

MIT license.

---

# product-card-generator (українською)

Складає **назви й описи товарів українською та російською** з атрибутів у CSV за вашими шаблонами та перевіряє результат: довжину, дублікати назв, відсутні атрибути й ризиковані обіцянки. Лише стандартна бібліотека Python.

**Запуск:** `PYTHONPATH=src python3 -m card_gen products.csv --config config.json --out cards.csv`. Нічого не вигадується: якщо атрибута немає, відповідна частина тексту пропускається.

**Важливо:** це збирання тексту за шаблоном, а не копірайтинг і не переклад; російські значення мають бути у вашому CSV. Описи шаблонні — перегляньте вибірку перед імпортом.
