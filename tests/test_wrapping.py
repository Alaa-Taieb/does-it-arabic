import numpy as np

from conftest import DATA
from doesitarabic.classify import classify
from doesitarabic.compare import Ink, distance, load_ink, restack_lines, text_lines
from doesitarabic.variants import VARIANTS


def _two_lines(gap):
    a = np.zeros((20 + gap + 20, 100), dtype=np.float32)
    a[0:20, 10:100] = 1
    a[20 + gap :, 40:100] = 1  # shorter, right-aligned second line
    return Ink(a)


def test_text_lines_finds_lines_and_ignores_small_gaps():
    a = np.zeros((60, 50), dtype=np.float32)
    a[0:3] = 1  # a dot above the line
    a[5:20] = 1  # the line body (gap of 2 rows < 0.35 * 15)
    a[40:55] = 1  # second line
    assert text_lines(Ink(a)) == [(0, 20), (40, 55)]


def test_restack_removes_leading_differences_but_keeps_alignment():
    tight, loose = restack_lines(_two_lines(5)), restack_lines(_two_lines(40))
    assert tight.data.shape == loose.data.shape
    assert np.array_equal(tight.data, loose.data)
    # a left-aligned second line is still different
    left = _two_lines(5).data.copy()
    left[25:, :] = 0
    left[25:, 0:60] = 1
    assert distance(restack_lines(Ink(left)), tight) > 0.1


def test_single_line_is_unchanged():
    ink = load_ink(DATA / "ref" / "invoice-line__ok.png")
    assert restack_lines(ink) is ink


def _wrap_refs():
    return {v: load_ink(DATA / "ref" / f"wrapping__{v}.png", multiline=True) for v in VARIANTS
            if (DATA / "ref" / f"wrapping__{v}.png").exists()}


def test_correct_wrap_with_bigger_line_spacing_passes():
    # xhtml2pdf wraps correctly but with a larger leading than Chromium
    out = load_ink(DATA / "out" / "xhtml2pdf-wrapping.png", multiline=True)
    assert len(text_lines(load_ink(DATA / "out" / "xhtml2pdf-wrapping.png"))) == 2
    assert classify(out, _wrap_refs()).verdict == "pass"


def test_lines_in_wrong_order_do_not_pass():
    # reshape + get_display before wrapping puts the second sentence on line one
    out = load_ink(DATA / "out" / "reportlab-reshaper-wrapping.png", multiline=True)
    assert classify(out, _wrap_refs()).verdict != "pass"


def test_dropped_harakat_do_not_pass():
    # arabic_reshaper deletes harakat by default
    refs = {v: load_ink(DATA / "ref" / f"harakat__{v}.png") for v in VARIANTS
            if (DATA / "ref" / f"harakat__{v}.png").exists()}
    out = load_ink(DATA / "out" / "reportlab-reshaper-harakat.png")
    assert classify(out, refs).verdict == "mismatch"
