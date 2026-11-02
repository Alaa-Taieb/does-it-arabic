# Decisions and assumptions

Each entry gives the choice and the reason for it. The brief came from an AI idea engine, so its market claims
were treated as leads to check. What this build did and did not check is listed at the end.

## Scope

- **Wedge = the invoice grid.** I built the screenshot matrix and its outputs (site, matrix.json, llms.txt,
  skill, fixtures, check + Action). I did not build the coding-agent benchmark: it needs agent accounts and
  produces non-deterministic runs, and the matrix is useful without it. It is listed as not built in the
  README.
- **17 configurations instead of "about 15 libraries".** Workarounds and built-in options get their own rows,
  for example fpdf2 with and without `set_text_shaping`, and ReportLab with and without arabic_reshaper. The
  brief asks that every failing cell come with *tested* workaround code. A tested configuration is that code,
  and its adapter source is shown on the page.
- **Libraries left out:** WeasyPrint needs GTK/Pango, which is painful on Windows. node-canvas needs Cairo, so
  @napi-rs/canvas (Skia) stands in. borb and ECharts SSR were left out for time. Puppeteer is covered by the
  headless Chrome row, which uses playwright-core.

## Stack

- **Python core plus Node adapters.** Image work (numpy, Pillow) and PDF rasterising (pypdfium2) are simplest
  in Python. JS libraries have to run in Node anyway. Each adapter is a small standalone script that prints
  one JSON line, so adding a library touches one file and one registry entry.
- **System Chrome via playwright-core.** This avoids downloading a browser, and it is the same engine
  (HarfBuzz plus full UBA) the brief names as the reference.
- **PDFium for PDF rasterising.** It is Chrome's PDF engine, it installs with pip on every OS, and it draws
  the glyphs the library placed without re-shaping them. poppler's `pdftoppm` was only available here through
  MiKTeX.
- **Plain generated HTML for the site.** There is no framework and no client JavaScript. `npm start` builds
  and serves it with Python's `http.server`.
- **Python 3.12+**, because the site generator uses nested f-string quotes.

## Fixtures

- **One font for everything: DejaVu Sans 2.37.** A single redistributable file covers Arabic, Persian,
  Hebrew, Latin and both digit sets, with GSUB/GPOS. Differences between rows then come from layout engines,
  not from font fallback. Noto Sans Arabic was rejected because it has no Latin glyphs, so the mixed invoice
  line would have tested fallback instead of RTL.
- **Urdu dropped from v1.** DejaVu Sans lacks `ے`, and proper Urdu needs Nastaliq, which is a separate
  problem. The brief's own list of eight fixtures has no Urdu fixture.
- **The invoice line is judged with an RTL base direction**, because it sits on an Arabic invoice. Correctly
  shaped output laid out with an LTR base is **partial**, not fail: Unicode handles it correctly, but it reads
  wrong on an Arabic invoice, and the fix is one setting.
- **Wrapping text and width (470) were picked by simulation** so that the line break lands in the same place
  even if a library measures widths 15% differently. Otherwise every library that measures text slightly
  differently would "fail" wrapping for reasons unrelated to RTL.
- **Fixture texts:** I wrote the Arabic in Modern Standard Arabic. The Persian and Hebrew texts are simple
  invoice phrases that still need a native speaker to confirm them.

## Judging

- **Classify against rendered failure patterns, not against the correct image alone.** Chromium renders the
  correct output plus each known bug: ZWNJ between letters for unshaped text, `bidi-override` for missing or
  reversed bidi, and `dir=ltr` for the wrong base direction. A library screenshot gets the verdict of the
  nearest of these. This produces a diagnosis ("letters disconnected"), and the failure renders come from the
  same engine as the correct one.
- **Distance metric:** crop to ink, resample both images onto a common grid, blur, then take 1 − cosine
  similarity plus an aspect-ratio penalty. In the calibration run, correct renders from different libraries
  scored 0.002 to 0.035. The closest genuinely different variants (only the digits mirrored) scored about
  0.15. **The match threshold is 0.08.** Variants within 0.03 of the correct render are ignored for that
  fixture.
- **"mismatch" is its own verdict.** An output that matches neither the correct render nor any known bug
  (scrambled words, dropped or misplaced harakat) is not passed. It is labelled "needs human review" rather
  than given a made-up diagnosis.
- **Line spacing does not count.** For wrapped text, detected lines are re-stacked with a fixed gap before
  comparing. The first run flagged xhtml2pdf, which wraps correctly but uses larger leading. Line order and
  alignment still count.
- **Adapter fairness rule:** each adapter uses the library's documented basic text API plus that library's own
  RTL or direction option when it has one: `dir`, `ctx.direction`, `textAlign: 'right'`, and fpdf2's
  `direction=`. Third-party fixes are separate "workaround" rows.
- **Human reviews override machine verdicts** through `results/reviews.json`. The site shows both the review
  and the original machine verdict, and the headline says that no cell has been reviewed yet.
- **`check` renders references in the user's font** (`--font`). Without that, a different typeface is a
  mismatch, as one of the tests shows.

## Process

- **Results are committed** (`results/`, about 3.5 MB of PNGs). `npm start` works without re-running anything,
  and the dated record is part of the repository. Raw PDFs are not kept because each embeds the full font.
- **Northstar tracks the project.** Tasks were started provisionally because the vision has not been approved
  yet. The approval is yours to give.
- **The fixtures package is not published**, and the Python loader has no `pyproject.toml`. I removed an
  untested packaging file rather than ship one I had not verified.

## Brief claims: what this run checked

- *"Enough popular libraries still visibly break Arabic" (the riskiest assumption):* **supported for
  libraries.** Six default configurations break basic fixtures without workarounds: PDFKit, pdfmake, pdf-lib,
  ReportLab, fpdf2 and matplotlib. That clears the brief's kill line of "fewer than 4". The agent half of the
  kill test was not run.
- *"The 2019 arabic_reshaper fix often breaks mixed Latin and numbers":* **not reproduced** with ReportLab +
  arabic-reshaper 3.1.0 + python-bidi 0.6.12, where the invoice line passed. What it did break: harakat are
  deleted (`delete_harakat: True` is arabic_reshaper's default), and wrapped lines come out in the wrong order.
  In JS, adding a reshaper and bidi-js to jsPDF 4.2.1 made every fixture fail, because jsPDF already shapes
  Arabic itself.
- *jsPDF issue #3467 "closed as stale", agents "default to jsPDF or satori", ZATCA/ETA market size, revenue
  figures:* **not checked.** No web research was done in this build.
