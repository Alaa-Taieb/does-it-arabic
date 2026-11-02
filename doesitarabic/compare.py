"""Renderer-independent comparison of two text renderings.

Different libraries rasterise at different sizes and positions, with different anti-aliasing.
We therefore compare *shapes*, not pixels:

1. convert to an ink map (0 = paper, 1 = full ink), flattening any alpha onto white;
2. crop to the ink bounding box;
3. resample both crops onto one common grid (same pixel budget, shared aspect ratio);
4. blur slightly so a one-pixel offset or a bolder stroke does not matter;
5. distance = (1 - cosine similarity of the blurred maps) + a penalty for different aspect ratios.

Disconnected letters change glyph shapes and line width; missing bidi reordering moves whole
words; both move the distance far more than font hinting or rasteriser differences do.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

INK_THRESHOLD = 0.25
PIXEL_BUDGET = 60_000
BLUR_SIGMA = 1.5
ASPECT_WEIGHT = 0.5


@dataclass
class Ink:
    """Cropped ink map of a rendering."""

    data: np.ndarray  # float32, 0..1

    @property
    def height(self) -> int:
        return self.data.shape[0]

    @property
    def width(self) -> int:
        return self.data.shape[1]

    @property
    def aspect(self) -> float:
        return self.width / self.height


def ink_from_image(img: Image.Image) -> np.ndarray:
    """Ink map of an image: dark-on-light text becomes values near 1."""
    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, rgba)
    gray = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    return 1.0 - gray


def crop_ink(ink: np.ndarray, threshold: float = INK_THRESHOLD) -> Ink | None:
    """Crop to the bounding box of ink; None when there is no visible ink at all."""
    mask = ink > threshold
    if not mask.any():
        return None
    rows = np.flatnonzero(mask.any(axis=1))
    cols = np.flatnonzero(mask.any(axis=0))
    return Ink(ink[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1].astype(np.float32))


LINE_MERGE_GAP = 0.35  # gaps smaller than this x line height are dots/harakat, not a line break
LINE_GAP = 0.25  # normalised gap between re-stacked lines, x median line height


def text_lines(ink: Ink, threshold: float = INK_THRESHOLD) -> list[tuple[int, int]]:
    """Row ranges [start, end) of the text lines in a cropped ink map."""
    rows = (ink.data > threshold).any(axis=1)
    runs: list[list[int]] = []
    start = None
    for i, on in enumerate(rows):
        if on and start is None:
            start = i
        elif not on and start is not None:
            runs.append([start, i])
            start = None
    if start is not None:
        runs.append([start, len(rows)])
    if not runs:
        return []
    tallest = max(e - s for s, e in runs)
    merged = [runs[0]]
    for s, e in runs[1:]:
        if s - merged[-1][1] < LINE_MERGE_GAP * tallest:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def restack_lines(ink: Ink) -> Ink:
    """Re-stack the lines of a paragraph with a fixed gap, so line spacing (leading) does not count.

    Each line keeps its horizontal position, so alignment and line order still matter.
    """
    lines = text_lines(ink)
    if len(lines) < 2:
        return ink
    heights = sorted(e - s for s, e in lines)
    gap = max(1, int(round(LINE_GAP * heights[len(heights) // 2])))
    parts = []
    for i, (s, e) in enumerate(lines):
        if i:
            parts.append(np.zeros((gap, ink.width), dtype=np.float32))
        parts.append(ink.data[s:e])
    return Ink(np.vstack(parts))


def load_ink(path: str | Path, multiline: bool = False) -> Ink | None:
    with Image.open(path) as img:
        ink = crop_ink(ink_from_image(img))
    return restack_lines(ink) if multiline and ink is not None else ink


def _resample(ink: Ink, width: int, height: int) -> np.ndarray:
    img = Image.fromarray(ink.data, mode="F")
    return np.asarray(img.resize((width, height), Image.Resampling.BILINEAR), dtype=np.float32)


def _gaussian_kernel(sigma: float) -> np.ndarray:
    radius = max(1, int(math.ceil(3 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=np.float32)
    k = np.exp(-(x**2) / (2 * sigma**2))
    return k / k.sum()


def blur(a: np.ndarray, sigma: float = BLUR_SIGMA) -> np.ndarray:
    k = _gaussian_kernel(sigma)
    pad = len(k) // 2
    p = np.pad(a, pad, mode="constant")
    # separable convolution: rows then columns
    rows = np.apply_along_axis(lambda r: np.convolve(r, k, mode="valid"), 1, p)
    return np.apply_along_axis(lambda c: np.convolve(c, k, mode="valid"), 0, rows)


def common_grid(a: Ink, b: Ink, budget: int = PIXEL_BUDGET) -> tuple[int, int]:
    """Grid size (width, height) shared by both images: geometric-mean aspect, fixed pixel budget."""
    aspect = math.sqrt(a.aspect * b.aspect)
    height = max(8, int(round(math.sqrt(budget / aspect))))
    width = max(8, int(round(height * aspect)))
    return width, height


def distance(a: Ink | None, b: Ink | None) -> float:
    """0 for identical shapes; ~0.05-0.15 for the same text from different renderers; larger otherwise."""
    if a is None and b is None:
        return 0.0
    if a is None or b is None:
        return 2.0
    width, height = common_grid(a, b)
    ra = blur(_resample(a, width, height))
    rb = blur(_resample(b, width, height))
    denom = float(np.sqrt((ra * ra).sum() * (rb * rb).sum()))
    cosine = float((ra * rb).sum()) / denom if denom > 0 else 0.0
    aspect_penalty = abs(math.log(a.aspect / b.aspect))
    return (1.0 - cosine) + ASPECT_WEIGHT * aspect_penalty
