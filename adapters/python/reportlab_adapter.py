"""ReportLab: register the TTF, canvas.drawRightString for one line, a right-aligned Paragraph for
wrapping. Pass --reshaper for the widely copied fix: arabic_reshaper.reshape() + bidi get_display()."""

import sys

from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from _lib import geometry, pkg_version, read_config, run_fixtures

config = read_config()
reshaper = "--reshaper" in sys.argv
pdfmetrics.registerFont(TTFont("DejaVu", config["fontPath"]))

if reshaper:
    import arabic_reshaper
    from bidi import get_display


def prepare(text, base_dir):
    if not reshaper:
        return text
    return get_display(arabic_reshaper.reshape(text), base_dir="R" if base_dir == "rtl" else "L")


def render(fixture, stem):
    g = geometry(config, fixture)
    path = str(stem.with_suffix(".pdf"))
    c = canvas.Canvas(path, pagesize=(g["width"], g["height"]))
    size = config["fontSize"]
    text = prepare(fixture["text"], fixture["dir"])
    if fixture.get("wrap"):
        style = ParagraphStyle("p", fontName="DejaVu", fontSize=size, leading=size * 1.2, alignment=TA_RIGHT)
        para = Paragraph(text, style)
        w, h = para.wrap(config["wrapWidth"], g["height"])
        para.drawOn(c, g["width"] - g["pad"] - config["wrapWidth"], g["height"] - g["pad"] - h)
    else:
        c.setFont("DejaVu", size)
        c.drawRightString(g["width"] - g["pad"], g["height"] - g["pad"] - size, text)
    c.save()
    return "pdf"


version = pkg_version("reportlab")
if reshaper:
    version += f" + arabic-reshaper {pkg_version('arabic-reshaper')} + python-bidi {pkg_version('python-bidi')}"
run_fixtures(config, version, render)
