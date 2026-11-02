import pytest

from conftest import DATA
from doesitarabic.classify import MATCH_THRESHOLD, classify, discriminating_variants, summarize
from doesitarabic.compare import load_ink
from doesitarabic.raster import rasterize
from doesitarabic.variants import VARIANTS


def refs(fixture_id):
    out = {}
    for vid in VARIANTS:
        p = DATA / "ref" / f"{fixture_id}__{vid}.png"
        if p.exists():
            out[vid] = load_ink(p)
    return out


def judge(fixture_id, out_name):
    return classify(load_ink(DATA / "out" / out_name), refs(fixture_id))


def test_each_reference_variant_classifies_as_itself():
    r = refs("invoice-line")
    usable = discriminating_variants(r)
    for vid in usable:
        j = classify(r[vid], r, usable)
        assert j.variant == vid and j.verdict == VARIANTS[vid].verdict


def test_hebrew_drops_variants_that_cannot_differ():
    usable = discriminating_variants(refs("hebrew"))
    # Hebrew has no joining: "unshaped" looks exactly like "ok"
    assert "unshaped" not in usable and "ok" in usable


def test_real_pillow_raqm_output_passes():
    j = judge("invoice-line", "pillow-invoice-line.png")
    assert j.verdict == "pass" and j.distance < MATCH_THRESHOLD


def test_real_fpdf2_default_output_is_naive_fail():
    j = judge("invoice-line", "fpdf2-invoice-line.png")
    assert j.verdict == "fail" and j.variant == "naive"
    assert "Disconnected" in j.label and j.advice


def test_real_jspdf_output_is_ltr_base_partial():
    j = judge("invoice-line", "jspdf-invoice-line.png")
    assert j.verdict == "partial" and j.variant == "ltr-base"


def test_real_satori_connected_passes():
    assert judge("connected", "satori-connected.png").verdict == "pass"


def test_real_pdfkit_scrambled_words_is_a_mismatch_not_a_pass():
    j = judge("connected", "pdfkit-connected.png")
    assert j.verdict == "mismatch" and j.variant is None and j.nearest


def test_real_fpdf2_hebrew_without_bidi_fails():
    j = judge("hebrew", "fpdf2-hebrew.png")
    assert j.verdict == "fail" and j.variant == "no-bidi"


def test_rasterized_pdf_gives_same_verdict(tmp_path):
    png = rasterize(DATA / "out" / "fpdf2-invoice-line.pdf", tmp_path / "x.png")
    j = classify(load_ink(png), refs("invoice-line"))
    assert j.variant == "naive"


def test_blank_output_fails():
    j = classify(None, refs("connected"))
    assert j.verdict == "fail" and j.variant == "blank"


def test_classify_requires_ok_reference():
    with pytest.raises(ValueError):
        classify(None, {})


def test_to_dict_is_json_friendly():
    d = judge("invoice-line", "pillow-invoice-line.png").to_dict()
    assert d["verdict"] == "pass" and isinstance(d["distances"]["ok"], float)


@pytest.mark.parametrize(
    "verdicts,expected",
    [
        (["pass", "pass", "n/a"], "pass"),
        (["pass", "fail"], "partial"),
        (["partial", "fail"], "partial"),
        (["fail", "mismatch", "error"], "fail"),
        (["n/a"], "n/a"),
    ],
)
def test_summarize(verdicts, expected):
    assert summarize(verdicts) == expected
