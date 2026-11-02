from doesitarabic.variants import VARIANTS, ZWNJ, break_joining, has_arabic, variant_jobs


def test_break_joining_separates_every_arabic_letter():
    assert break_joining("محمد") == ZWNJ.join("محمد")


def test_break_joining_keeps_marks_on_their_letter():
    # shadda + damma stay on waw; the ZWNJ goes after the marks, before qaf
    out = break_joining("وُّق")
    assert out == "وُّ" + ZWNJ + "ق"


def test_break_joining_leaves_latin_digits_and_hebrew_alone():
    text = "Order #1234 חשבונית 250"
    assert break_joining(text) == text


def test_break_joining_does_not_join_across_spaces():
    assert break_joining("لا لا") == "ل" + ZWNJ + "ا ل" + ZWNJ + "ا"


def test_has_arabic():
    assert has_arabic("Order محمد")
    assert not has_arabic("חשבונית 1234")


def test_variant_jobs_cover_all_variants_for_rtl_fixture():
    jobs = variant_jobs({"id": "x", "text": "مرحبا", "dir": "rtl"})
    assert [j["variant"] for j in jobs] == list(VARIANTS)
    by = {j["variant"]: j for j in jobs}
    assert by["ok"]["dir"] == "rtl" and by["ok"]["css"] == ""
    assert by["ltr-base"]["dir"] == "ltr"
    assert "bidi-override" in by["no-bidi"]["css"] and "direction: ltr" in by["no-bidi"]["css"]
    assert ZWNJ in by["naive"]["text"] and "direction: ltr" in by["naive"]["css"]
    assert "direction: rtl" in by["reversed"]["css"]
    assert all(j["name"] == f"x__{j['variant']}" for j in jobs)


def test_ltr_fixture_has_no_ltr_base_variant():
    jobs = variant_jobs({"id": "x", "text": "abc", "dir": "ltr"})
    assert "ltr-base" not in [j["variant"] for j in jobs]


def test_every_failure_variant_has_advice():
    for v in VARIANTS.values():
        assert v.verdict in ("pass", "partial", "fail")
        assert v.advice or v.id == "ok"
