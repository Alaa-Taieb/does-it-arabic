---
name: does-it-arabic
description: Use when generating PDFs, invoices, receipts, certificates, OG/social images or charts that contain Arabic, Persian, Urdu or Hebrew text, or when choosing a library for that. Gives tested library verdicts so the output does not ship with disconnected letters, reversed words or misplaced numbers.
---

# Does It Arabic? — RTL output rules

Tested 2026-11-02 by rendering the same RTL fixtures with each library and comparing the screenshots with a Chromium/HarfBuzz reference. Verdicts are automatic; see matrix.json for every cell.

## Before you write code

1. Pick a library configuration from **Works** below. Do not default to one from **Avoid**.
2. Embed a font that covers every script in the text (Arabic *and* Latin digits/letters), e.g. DejaVu Sans or Noto Sans Arabic + a Latin font with fallback. Many Arabic fonts contain no Latin glyphs.
3. Set the paragraph/base direction to RTL where the API allows it (`dir="rtl"`, `direction: 'rtl'`, `ctx.direction = 'rtl'`, `set_text_shaping(True, direction="rtl")`).
4. Do not reverse strings yourself, and do not pre-shape text for a library that already shapes it.
5. Keep harakat: `arabic_reshaper` removes them by default.
6. Measured here: jsPDF + reshaper + bidi-js passes 0/8 fixtures, plain jsPDF passes 4/8: the workaround makes it worse.

## Works (passes every fixture)

- **Headless Chrome page.pdf()** (npm, pdf, Chrome 156.0.8078.74): 8/8 pass
- **@napi-rs/canvas** (npm, og-image, 1.1.0): 7/7 pass
- **Pillow ImageDraw** (pypi, og-image, 12.0.0 (raqm layout)): 7/7 pass

## Partly works

- **jsPDF** (npm, pdf, 4.2.1): 4/8 pass; broken: Harakat (vowel marks), Mixed bidi invoice line, Hebrew with numbers, Line wrapping
- **pdf-lib** (npm, pdf, 1.17.1): 2/8 pass; broken: Harakat (vowel marks), Mixed bidi invoice line, Arabic-Indic and Persian digits, Persian letters (ی ک پ گ, ZWNJ), Hebrew with numbers, Line wrapping
- **@react-pdf/renderer** (npm, pdf, 4.9.0): 4/8 pass; broken: Harakat (vowel marks), Mixed bidi invoice line, Hebrew with numbers, Line wrapping
- **satori (@vercel/og engine) + resvg** (npm, og-image, 0.63.2): 7/8 pass; broken: Harakat (vowel marks)
- **Chart.js on @napi-rs/canvas** (npm, chart, 4.6.1): 5/7 pass; broken: Mixed bidi invoice line, Hebrew with numbers
- **ReportLab + arabic_reshaper + python-bidi** (pypi, pdf, 5.1.0 + arabic-reshaper 3.1.0 + python-bidi 0.6.12): 6/8 pass; broken: Harakat (vowel marks), Line wrapping
- **fpdf2 with set_text_shaping()** (pypi, pdf, 2.9.0): 7/8 pass; broken: Harakat (vowel marks)
- **xhtml2pdf** (pypi, pdf, 0.2.28): 7/8 pass; broken: Harakat (vowel marks)

## Avoid for RTL text

- **jsPDF + reshaper + bidi-js** (npm, pdf, 4.2.1 + arabic-persian-reshaper 1.0.1 + bidi-js 1.1.0): 0/8 pass; broken: Connected letterforms, Lam-alef ligature, Harakat (vowel marks), Mixed bidi invoice line, Arabic-Indic and Persian digits, Persian letters (ی ک پ گ, ZWNJ), Hebrew with numbers, Line wrapping
- **PDFKit** (npm, pdf, 0.20.2): 0/8 pass; broken: Connected letterforms, Lam-alef ligature, Harakat (vowel marks), Mixed bidi invoice line, Arabic-Indic and Persian digits, Persian letters (ی ک پ گ, ZWNJ), Hebrew with numbers, Line wrapping
- **pdfmake** (npm, pdf, 0.3.13): 0/8 pass; broken: Connected letterforms, Lam-alef ligature, Harakat (vowel marks), Mixed bidi invoice line, Arabic-Indic and Persian digits, Persian letters (ی ک پ گ, ZWNJ), Hebrew with numbers, Line wrapping
- **ReportLab** (pypi, pdf, 5.1.0): 0/8 pass; broken: Connected letterforms, Lam-alef ligature, Harakat (vowel marks), Mixed bidi invoice line, Arabic-Indic and Persian digits, Persian letters (ی ک پ گ, ZWNJ), Hebrew with numbers, Line wrapping
- **fpdf2** (pypi, pdf, 2.9.0): 0/8 pass; broken: Connected letterforms, Lam-alef ligature, Harakat (vowel marks), Mixed bidi invoice line, Arabic-Indic and Persian digits, Persian letters (ی ک پ گ, ZWNJ), Hebrew with numbers, Line wrapping
- **matplotlib** (pypi, chart, 3.10.7): 0/8 pass; broken: Connected letterforms, Lam-alef ligature, Harakat (vowel marks), Mixed bidi invoice line, Arabic-Indic and Persian digits, Persian letters (ی ک پ گ, ZWNJ), Hebrew with numbers, Line wrapping

## Check your output

Render the fixture text with your code, then judge the PDF or PNG:

```
python -m doesitarabic check invoice.pdf --fixture invoice-line
```

Exit code 0 means it matches the correct rendering. Fixture texts are in `packages/arabic-fixtures/fixtures.json` (the invoice line is `Order #1234 للعميل محمد – 250 TND`).
