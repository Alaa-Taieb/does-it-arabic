"""Judge one rendering of one fixture against the reference and failure variants."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .compare import Ink, distance
from .variants import VARIANTS

# Same text from two different correct renderers lands at ~0.00-0.03; the closest genuinely
# different variants (e.g. only the digits mirrored) sit at ~0.15. See DECISIONS.md.
MATCH_THRESHOLD = 0.08
# Two variants closer than this look the same for this fixture (e.g. "unshaped" Hebrew),
# so they cannot tell failures apart and are dropped.
SAME_THRESHOLD = 0.03

VERDICT_ORDER = ["pass", "partial", "fail", "mismatch", "error", "n/a"]


@dataclass
class Judgement:
    verdict: str  # pass | partial | fail | mismatch
    variant: str | None  # matched variant id, "blank", or None for mismatch
    distance: float | None
    label: str
    advice: str = ""
    nearest: str | None = None
    distances: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["distance"] = None if self.distance is None else round(self.distance, 4)
        d["distances"] = {k: round(v, 4) for k, v in self.distances.items()}
        return d


def discriminating_variants(refs: dict[str, Ink | None]) -> list[str]:
    """Variants that look different from ``ok`` and from every earlier kept variant."""
    kept = ["ok"]
    for vid in VARIANTS:
        if vid == "ok" or vid not in refs:
            continue
        if all(distance(refs[vid], refs[k]) > SAME_THRESHOLD for k in kept):
            kept.append(vid)
    return kept


def classify(output: Ink | None, refs: dict[str, Ink | None], usable: list[str] | None = None) -> Judgement:
    """Classify a cropped rendering.

    ``refs`` maps variant id -> reference ink (must contain ``ok``).
    ``usable`` is the result of :func:`discriminating_variants`; computed when omitted.
    """
    if "ok" not in refs:
        raise ValueError("references must include the 'ok' variant")
    if output is None:
        return Judgement("fail", "blank", None, "Nothing visible was drawn (missing glyphs or empty output)",
                         "Check that the font is embedded and the library supports this script.")
    usable = usable or discriminating_variants(refs)
    dists = {vid: distance(output, refs[vid]) for vid in usable}
    nearest = min(dists, key=lambda v: (dists[v], usable.index(v)))
    d = dists[nearest]
    if d > MATCH_THRESHOLD:
        return Judgement("mismatch", None, None,
                         "Differs from the correct rendering and from every known failure pattern; needs human review",
                         "", nearest, dists)
    v = VARIANTS[nearest]
    return Judgement(v.verdict, nearest, d, v.label, v.advice, nearest, dists)


def summarize(verdicts: list[str]) -> str:
    """Row-level verdict: pass only if every judged fixture passes."""
    judged = [v for v in verdicts if v != "n/a"]
    if not judged:
        return "n/a"
    if all(v == "pass" for v in judged):
        return "pass"
    if any(v == "pass" or v == "partial" for v in judged):
        return "partial"
    return "fail"
