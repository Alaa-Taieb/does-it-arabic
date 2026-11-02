import json

import pytest

from doesitarabic import site
from doesitarabic.matrix import apply_reviews
from doesitarabic.paths import RESULTS


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist")
    site.build_site(RESULTS, out, skill_dir=None)
    return out, site.load_matrix(RESULTS)


def test_every_page_and_agent_file_is_generated(built):
    out, m = built
    for name in ("index.html", "fixtures.html", "method.html", "style.css", "matrix.json", "llms.txt", "skill/SKILL.md"):
        assert (out / name).exists(), name
    for r in m["rows"]:
        assert (out / "lib" / f"{r['id']}.html").exists()


def test_headline_numbers_come_from_the_matrix(built):
    out, m = built
    s = site.stats(m)
    index = (out / "index.html").read_text(encoding="utf-8")
    assert f"Same Arabic invoice line, {s['invoice_judged']} library configurations, {s['invoice_broken']} broke it." in index
    broken = [r for r in m["rows"] if r["cells"]["invoice-line"]["verdict"] in ("fail", "partial", "mismatch")]
    assert s["invoice_broken"] == len(broken)


def test_site_says_verdicts_are_automatic(built):
    out, _ = built
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "Automatic verdicts." in index
    assert "No cell has been reviewed by a native speaker yet." in index


def test_published_matrix_points_at_existing_images(built):
    out, _ = built
    pm = json.loads((out / "matrix.json").read_text(encoding="utf-8"))
    for r in pm["rows"]:
        for c in r["cells"].values():
            if c.get("shot"):
                assert (out / c["shot"]).exists()
                assert (out / c["shot"].replace("img/", "img/crop/", 1)).exists()
    for p in pm["referenceImages"].values():
        assert (out / p).exists()


def test_library_page_shows_adapter_source(built):
    out, _ = built
    page = (out / "lib" / "fpdf2-shaping.html").read_text(encoding="utf-8")
    assert "set_text_shaping" in page and "Correct (Chromium)" in page


def test_llms_txt_lists_every_row(built):
    out, m = built
    txt = (out / "llms.txt").read_text(encoding="utf-8")
    assert txt.startswith("# Does It Arabic?")
    for r in m["rows"]:
        assert f"[{r['library']}](lib/{r['id']}.html)" in txt


def test_skill_file_has_frontmatter_and_groups(built):
    out, m = built
    skill = (out / "skill" / "SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\nname: does-it-arabic\ndescription: ")
    for r in m["rows"]:
        assert f"**{r['library']}**" in skill
    passing = [r for r in m["rows"] if r["summary"] == "pass"]
    works = skill.split("## Works")[1].split("## Partly")[0]
    assert all(r["library"] in works for r in passing)


def _row(id_, summary, passed, package="p", mode="default", eco="npm", cat="pdf"):
    return {"id": id_, "library": id_, "package": package, "mode": mode, "ecosystem": eco, "category": cat,
            "summary": summary, "passed": passed, "judged": 8, "version": "1", "cells": {}}


def test_alternatives_prefer_same_ecosystem_and_category():
    m = {"rows": [_row("a", "fail", 0), _row("b", "pass", 8, eco="pypi"), _row("c", "pass", 8, cat="og-image"),
                  _row("d", "pass", 8)]}
    assert [r["id"] for r in site.alternatives(m, m["rows"][0])] == ["d", "c"]


def test_worse_workaround_is_reported():
    m = {"rows": [_row("lib", "partial", 4, package="x"), _row("lib+fix", "fail", 0, package="x", mode="workaround")]}
    assert site.worse_workarounds(m) == [
        "lib+fix passes 0/8 fixtures, plain lib passes 4/8: the workaround makes it worse."]
    m["rows"][1]["passed"] = 6
    assert site.worse_workarounds(m) == []


def test_html_is_escaped():
    assert site.e('<script>"x"</script>') == "&lt;script&gt;&quot;x&quot;&lt;/script&gt;"


def test_reviewed_cells_are_marked():
    m = {"rows": [{"id": "a", "cells": {"x": {"verdict": "mismatch"}}}]}
    apply_reviews(m, [{"row": "a", "fixture": "x", "verdict": "pass", "reviewer": "R", "date": "2026-11-02", "note": "ok"}])
    html = site.badge(m["rows"][0]["cells"]["x"])
    assert "✓*" in html and "Human review" in html and "machine said mismatch" in html
