# Does It Arabic? — Specification

See PLAN.md for stack and milestones. Fixtures live in packages/arabic-fixtures/fixtures.json. Adapters (adapters/node, adapters/python) render each fixture to PDF/PNG with one library. doesitarabic/ (Python) renders Chromium reference + failure variants, rasterises outputs, classifies each cell (pass / partial / fail / mismatch / error / n/a) and writes results/matrix.json. The site generator writes dist/ with index.html, per-library pages, matrix.json, llms.txt and the skill file. `check` judges any user PDF/PNG for a fixture; action/action.yml wraps it.
