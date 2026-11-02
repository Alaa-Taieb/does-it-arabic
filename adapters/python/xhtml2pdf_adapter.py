"""xhtml2pdf: HTML/CSS to PDF with @font-face, dir="rtl" and text-align: right."""

import html
from pathlib import Path

from xhtml2pdf import pisa

from _lib import geometry, pkg_version, read_config, run_fixtures

config = read_config()
font_url = Path(config["fontPath"]).resolve().as_posix()


def render(fixture, stem):
    g = geometry(config, fixture)
    width = f"width: {config['wrapWidth']}pt; margin-left: {g['width'] - 2 * g['pad'] - config['wrapWidth']}pt;" if fixture.get("wrap") else ""
    doc = f"""<html lang="{fixture['lang']}" dir="{fixture['dir']}"><head><meta charset="utf-8"><style>
      @font-face {{ font-family: DejaVu; src: url("{font_url}"); }}
      @page {{ size: {g['width']}pt {g['height']}pt; margin: {g['pad']}pt; }}
      body {{ font-family: DejaVu; font-size: {config['fontSize']}pt; }}
      p {{ text-align: right; margin: 0; {width} }}
    </style></head><body><p dir="{fixture['dir']}">{html.escape(fixture['text'])}</p></body></html>"""
    path = stem.with_suffix(".pdf")
    with open(path, "wb") as out:
        result = pisa.CreatePDF(doc, dest=out, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"xhtml2pdf reported {result.err} error(s)")
    return "pdf"


run_fixtures(config, pkg_version("xhtml2pdf"), render)
