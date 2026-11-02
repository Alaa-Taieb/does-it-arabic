"""Synthetic renderings of a fixture: the correct one and the known ways libraries break it.

Every variant is rendered by Chromium (HarfBuzz + full Unicode Bidi Algorithm), so the only
difference between ``ok`` and a failure variant is the failure itself, not the rasteriser.
A library output is then classified by which variant it looks most like.
"""

from __future__ import annotations

from dataclasses import dataclass

ZWNJ = "‌"

# Arabic-script letters that take part in cursive joining (incl. Persian/Urdu extensions).
_LETTER_RANGES = [
    (0x0620, 0x064A),
    (0x066E, 0x066F),
    (0x0671, 0x06D3),
    (0x06D5, 0x06D5),
    (0x06EE, 0x06EF),
    (0x06FA, 0x06FF),
    (0x0750, 0x077F),
]
# Combining marks (harakat etc.) that attach to the preceding letter.
_MARK_RANGES = [(0x0610, 0x061A), (0x064B, 0x065F), (0x0670, 0x0670), (0x06D6, 0x06ED)]


def _in(ranges, ch: str) -> bool:
    o = ord(ch)
    return any(lo <= o <= hi for lo, hi in ranges)


def is_arabic_letter(ch: str) -> bool:
    return _in(_LETTER_RANGES, ch)


def is_arabic_mark(ch: str) -> bool:
    return _in(_MARK_RANGES, ch)


def has_arabic(text: str) -> bool:
    return any(is_arabic_letter(c) for c in text)


def break_joining(text: str) -> str:
    """Insert ZWNJ between consecutive Arabic letters so every letter takes its isolated form.

    Marks stay attached to their base letter: the ZWNJ goes after the marks, before the next letter.
    This reproduces what a renderer without Arabic shaping draws (nominal, unjoined glyphs).
    """
    out: list[str] = []
    prev_letter = False
    for ch in text:
        if is_arabic_letter(ch):
            if prev_letter:
                out.append(ZWNJ)
            prev_letter = True
        elif not is_arabic_mark(ch):
            prev_letter = False
        out.append(ch)
    return "".join(out)


@dataclass(frozen=True)
class Variant:
    id: str
    verdict: str  # pass | partial | fail
    label: str  # human description of what the output looks like
    advice: str  # what usually fixes it


VARIANTS: dict[str, Variant] = {
    v.id: v
    for v in [
        Variant("ok", "pass", "Correct: shaped and in Unicode Bidi order", ""),
        Variant(
            "ltr-base",
            "partial",
            "Shaped and bidi-ordered, but with a left-to-right base direction",
            "Set the paragraph/base direction to RTL (or start the line with an RLM).",
        ),
        Variant(
            "unshaped",
            "fail",
            "Letters disconnected (no Arabic shaping), order correct",
            "The library does not shape Arabic: use a library with HarfBuzz shaping, or pre-shape the text.",
        ),
        Variant(
            "no-bidi",
            "fail",
            "Letters joined but drawn left-to-right in typing order (no bidi reordering)",
            "Apply the Unicode Bidi Algorithm (e.g. bidi-js / python-bidi get_display) or set RTL direction.",
        ),
        Variant(
            "naive",
            "fail",
            "Disconnected letters drawn left-to-right in typing order (no shaping, no bidi)",
            "The library draws code points one by one: use a library with HarfBuzz shaping and bidi.",
        ),
        Variant(
            "reversed",
            "fail",
            "Whole line reversed: Arabic looks right but Latin text and numbers are mirrored",
            "Do not reverse the whole string; run a real bidi algorithm that keeps LTR runs intact.",
        ),
        Variant(
            "unshaped-reversed",
            "fail",
            "Disconnected letters and the whole line reversed (numbers and Latin mirrored)",
            "Shape the text and run a real bidi algorithm instead of reversing the string.",
        ),
    ]
}


def variant_jobs(fixture: dict) -> list[dict]:
    """Chromium render jobs for one fixture: name, text, dir, css, wrap.

    Variants that cannot differ from ``ok`` for this fixture (e.g. ``unshaped`` on Hebrew)
    are still rendered; the classifier drops variants that look identical to ``ok``.
    """
    text = fixture["text"]
    base = fixture.get("dir", "rtl")
    wrap = bool(fixture.get("wrap"))
    unjoined = break_joining(text)
    override_ltr = "unicode-bidi: bidi-override; direction: ltr;"
    override_rtl = "unicode-bidi: bidi-override; direction: rtl;"
    specs = {
        "ok": (text, base, ""),
        "ltr-base": (text, "ltr", ""),
        "unshaped": (unjoined, base, ""),
        "no-bidi": (text, "ltr", override_ltr),
        "naive": (unjoined, "ltr", override_ltr),
        "reversed": (text, "rtl", override_rtl),
        "unshaped-reversed": (unjoined, "rtl", override_rtl),
    }
    if base == "ltr":
        specs.pop("ltr-base")
    return [
        {"name": f"{fixture['id']}__{vid}", "variant": vid, "text": t, "dir": d, "css": css, "wrap": wrap}
        for vid, (t, d, css) in specs.items()
    ]
