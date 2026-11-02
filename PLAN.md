# Does It Arabic? — MVP plan

## Scope (the wedge)

The **invoice grid**: the same Arabic/Persian/Hebrew invoice fixtures rendered by ~15 real PDF, OG-image
and chart library configurations, each output screenshotted and judged automatically against a Chromium
(HarfBuzz + Unicode Bidi) reference. The matrix is published three ways from one `matrix.json`:

1. a static site (grid + per-library pages with the screenshots and the exact adapter code),
2. agent-facing files: `matrix.json`, `llms.txt` and a Claude Code / Codex / Cursor skill file,
3. a `check` command (and a GitHub Action wrapping it) that judges *your* PDF/PNG output against the fixtures.

Plus the `arabic-fixtures` package (fixtures JSON with a JS and a Python loader).

Out of scope for v1 (listed in README): the coding-agent benchmark runs, weekly CI history, native-speaker
review of every cell, Urdu/Nastaliq, publishing to npm/PyPI/Marketplace.

## Stack

- **Python 3.11+** core (`doesitarabic/`): variants, image comparison (numpy + Pillow), PDF rasterising
  (pypdfium2), classification, matrix runner, site/agent-file generator, `check` CLI. Tests: pytest.
- **Node 20+** adapters for JS libraries and the Chromium reference renderer (playwright-core driving the
  locally installed Chrome; no browser download).
- One font for every library: **DejaVu Sans 2.37** (covers Arabic, Persian, Hebrew, Latin and digits in one
  file), so differences come from layout engines, not font fallback.
- Static site: plain generated HTML + CSS, no framework. Served with Python's `http.server`.

## How judging works

For each fixture Chromium renders the correct output **and** the known failure modes (unshaped letters,
no bidi, naive code-point drawing, whole-string reversal, LTR base direction). Each library screenshot is
cropped, normalised and compared with every variant; the nearest variant under a threshold gives the verdict
and the diagnosis. Nothing near anything → "mismatch, needs review". Every verdict is labelled as machine
judged until a human review is recorded.

## Milestones

1. **Foundation** — fixtures package, reference + failure-variant renderer, comparison + classifier, tests.
2. **Matrix** — adapters for ~15 library configurations, `npm run matrix` → `results/` with screenshots and
   `matrix.json`.
3. **Publish** — static site, `llms.txt`, skill file; `npm start` builds and serves it.
4. **Check + Action** — `check` CLI for any PDF/PNG (or a URL that returns one), `action.yml` wrapping it.
5. **Docs** — README, DECISIONS, final verification.

Each milestone ends with tests + build + a run of the app, and one local commit.
