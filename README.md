# Does It Arabic?

A screenshot-backed test matrix of which PDF, OG-image and chart libraries render Arabic, Persian and Hebrew
correctly. Every cell is a real screenshot of a library's output, judged automatically against a
Chromium/HarfBuzz reference. The same results are published as a static site, as files a coding agent can read
(`matrix.json`, `llms.txt`, a skill file), as a fixtures package, and as a `check` command plus a GitHub Action
you can point at your own PDFs.

**First run (2026-11-02, Windows, DejaVu Sans 2.37):** the same Arabic invoice line,
`Order #1234 للعميل محمد – 250 TND`, went through 17 library configurations and **10 broke it**.
3 of the 17 pass all eight fixtures. These verdicts are automatic, and no native speaker has reviewed them yet.

| Configuration | Invoice line | Fixtures passed |
|---|---|---|
| Headless Chrome `page.pdf()` | pass | 8/8 |
| @napi-rs/canvas (`ctx.direction = 'rtl'`) | pass | 7/7 (no wrapping API) |
| Pillow ImageDraw (raqm layout) | pass | 7/7 (no wrapping API) |
| fpdf2 with `set_text_shaping(direction="rtl")` | pass | 7/8 (harakat) |
| xhtml2pdf | pass | 7/8 (harakat dropped) |
| satori + resvg | pass | 7/8 (harakat misplaced) |
| ReportLab + arabic_reshaper + python-bidi | pass | 6/8 (harakat dropped, wrapped lines swapped) |
| Chart.js on @napi-rs/canvas | partial (LTR base) | 5/7 |
| jsPDF 4.2.1 | partial (LTR base) | 4/8 |
| @react-pdf/renderer | partial (LTR base) | 4/8 |
| pdf-lib | fail (letters disconnected, reversed) | 2/8 |
| PDFKit, pdfmake | mismatch (words scrambled) | 0/8 |
| jsPDF + arabic-persian-reshaper + bidi-js | mismatch | 0/8 (the workaround breaks jsPDF's own Arabic support) |
| ReportLab, fpdf2, matplotlib (defaults) | fail (unshaped, no bidi) | 0/8 |

## Setup

You need Node 20+, Python 3.12+ and an installed Google Chrome or Chromium. Chrome is only needed to re-run the
matrix or to check output in a custom font. Viewing the site works without it. Set `CHROME_PATH` if Chrome is
not in a standard location. No browser is downloaded.

```bash
npm install
pip install -r requirements.txt               # core: numpy, Pillow, pypdfium2, pytest, PyYAML
pip install -r requirements-adapters.txt      # only to re-run the Python library adapters
```

## Usage

```bash
npm start        # builds the site from results/ and serves it at http://127.0.0.1:8000/
npm test         # 79 tests (unit tests plus real end-to-end runs through Chrome and live adapters)
npm run matrix   # re-render references, run all 17 adapters (~30 s), rewrite results/
npm run build    # only generate dist/ (site, matrix.json, llms.txt, skill/SKILL.md)
```

### Check your own output

Render a fixture's text with your own code. The file must contain only that text, as black text on white. Then:

```bash
python -m doesitarabic check invoice.pdf --fixture invoice-line          # exit 0 = matches the correct rendering
python -m doesitarabic check out.png --fixture connected --font MyFont.ttf  # references rendered in your font
python -m doesitarabic check --spec-file checks.txt --json                # lines of "<fixture-id> <path>"
python -m doesitarabic check --endpoint http://localhost:3000/render      # POST {id,text,dir,lang} -> PDF/PNG
```

Exit codes: 0 means every check passed, 1 means at least one failed, 2 means a usage error.
`--allow-partial` accepts output that is correctly shaped but laid out with a left-to-right base direction.

### GitHub Action

`action.yml` is a composite action that wraps `check` and writes a Markdown table to the job summary:

```yaml
- uses: <owner>/does-it-arabic@<ref>   # not published: copy this repo or use a local path
  with:
    checks: |
      invoice-line build/fixtures/invoice-line.pdf
      hebrew       build/fixtures/hebrew.png
    font: assets/fonts/MyFont.ttf
```

Or use `endpoint: http://localhost:3000/render` to have the action call your renderer once per fixture.

### For coding agents

- `skill/does-it-arabic/SKILL.md` is a Claude Code / Codex / Cursor skill generated from the matrix. Copy the
  folder into `~/.claude/skills/` (or `.agents/skills/`, or Cursor rules) so an agent reads it before it
  picks a PDF or image library for RTL text.
- `dist/llms.txt` and `dist/matrix.json` are written by `npm run build`.

### Fixtures package

`packages/arabic-fixtures` holds the eight fixtures (`fixtures.json`, CC0) with a JS loader (`index.js`) and a
Python loader (`arabic_fixtures.py`). The fixtures are connected letterforms, lam-alef, harakat, the mixed
invoice line, Arabic-Indic and Persian digits, Persian letters with ZWNJ, Hebrew with numbers, and line wrapping.

## How it works

1. Each adapter (`adapters/node/*.mjs`, `adapters/python/*_adapter.py`, listed in `adapters/registry.json`)
   renders every fixture with one library, using the same font and size.
2. Chromium renders the correct output and six known failure patterns: unshaped, no bidi, naive, whole line
   reversed, unshaped and reversed, and LTR base direction (`reference/render-chromium.mjs`,
   `doesitarabic/variants.py`).
3. PDFs are rasterised with PDFium. Each screenshot is compared with every variant
   (`doesitarabic/compare.py`, `classify.py`). The nearest variant within a threshold decides the verdict:
   pass, partial, fail, or **mismatch** when the output matches nothing known and needs a human look.
4. `results/matrix.json`, `results/shots/` and `results/history.jsonl` (one dated line per adapter run) are
   committed. `results/reviews.json` holds human overrides, which the site marks with `*`.

The site's *How it is judged* page explains the method and its limits.

## What is not built yet

- **The coding-agent benchmark**, the brief's second launch artefact. It would ask Claude Code, Codex, Cursor,
  Copilot and v0 for an Arabic invoice PDF and show what they produce. Nothing here runs coding agents.
- **Native-speaker review.** The review mechanism exists, but `reviews.json` is empty. The Persian and Hebrew
  fixture texts were written without a native speaker and should be checked.
- **Weekly scheduled runs.** `history.jsonl` records each run, but nothing schedules one.
- **More libraries.** Not covered: WeasyPrint (needs GTK/Pango on Windows), borb, node-canvas (Cairo), ECharts
  SSR, @vercel/og itself (satori is covered), Puppeteer as a separate row, and Java/.NET/PHP/Go libraries.
- **Urdu / Nastaliq.** DejaVu Sans has no `ے`, and Nastaliq needs its own font and fixtures.
- **Font fallback.** Everything uses one font that covers every script, so "an Arabic font with no Latin
  glyphs" bugs are out of scope.
- **Region selection in `check`.** Your file has to contain only the fixture text. You can't point it at one
  line of a full invoice yet.
- **Publishing.** Nothing is deployed or published: the site, npm/PyPI packages, the Action on the Marketplace,
  and the issues for library maintainers. The Python fixtures loader has no packaging metadata yet.
- **Only tested on Windows 11.** Linux runners should work (`find-chrome.mjs` knows the usual paths) but have not
  been tried, and the Action has never run on GitHub.
- Paid audits, sponsorship and a hosted service are not built.

## Accounts, payments, API keys

None are used. No mocks were needed. The endpoint tests start a real renderer on `127.0.0.1` inside the tests.

## Licences

Code: MIT. Fixtures: CC0. DejaVu Sans: Bitstream Vera licence (`fonts/DejaVu-LICENSE.txt`). Noto Sans Arabic
(test data only): SIL OFL 1.1 (`tests/data/fonts/NotoSansArabic-OFL.txt`).
