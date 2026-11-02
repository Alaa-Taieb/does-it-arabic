"""fpdf2: documented usage, add_font + cell/multi_cell, right-aligned. Pass --shaping to call
set_text_shaping(True, direction=...), fpdf2's own documented switch for HarfBuzz shaping
and bidi with the fixture's base direction."""

import sys

from fpdf import FPDF

from _lib import geometry, pkg_version, read_config, run_fixtures

config = read_config()
shaping = "--shaping" in sys.argv


def render(fixture, stem):
    g = geometry(config, fixture)
    pdf = FPDF(unit="pt", format=(g["width"], g["height"]))
    pdf.set_margin(g["pad"])
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.add_font("DejaVu", fname=config["fontPath"])
    pdf.set_font("DejaVu", size=config["fontSize"])
    if shaping:
        pdf.set_text_shaping(True, direction=fixture["dir"])
    if fixture.get("wrap"):
        pdf.set_x(g["width"] - g["pad"] - config["wrapWidth"])
        pdf.multi_cell(config["wrapWidth"], config["fontSize"] * 1.2, fixture["text"], align="R")
    else:
        pdf.cell(g["width"] - 2 * g["pad"], config["fontSize"] * 1.2, fixture["text"], align="R")
    pdf.output(str(stem.with_suffix(".pdf")))
    return "pdf"


run_fixtures(config, pkg_version("fpdf2"), render)
