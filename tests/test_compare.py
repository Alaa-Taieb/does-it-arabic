import numpy as np
from PIL import Image, ImageDraw

from conftest import DATA
from doesitarabic.compare import Ink, crop_ink, distance, ink_from_image, load_ink


def _canvas(w=400, h=100):
    return Image.new("RGB", (w, h), "white")


def test_blank_image_has_no_ink():
    assert crop_ink(ink_from_image(_canvas())) is None


def test_crop_finds_ink_bounding_box():
    img = _canvas()
    ImageDraw.Draw(img).rectangle([50, 20, 149, 39], fill="black")
    ink = crop_ink(ink_from_image(img))
    assert (ink.width, ink.height) == (100, 20)


def test_transparent_png_is_flattened_onto_white():
    img = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    ImageDraw.Draw(img).rectangle([10, 10, 19, 19], fill=(0, 0, 0, 255))
    ink = crop_ink(ink_from_image(img))
    assert (ink.width, ink.height) == (10, 10)


def test_identical_images_have_zero_distance():
    a = load_ink(DATA / "ref" / "invoice-line__ok.png")
    assert distance(a, a) < 1e-6


def test_distance_ignores_scale_and_position():
    src = Image.open(DATA / "ref" / "invoice-line__ok.png").convert("RGB")
    big = _canvas(src.width * 2 + 300, src.height * 2 + 120)
    big.paste(src.resize((src.width * 2, src.height * 2)), (250, 60))
    assert distance(load_ink(DATA / "ref" / "invoice-line__ok.png"), crop_ink(ink_from_image(big))) < 0.03


def test_distance_separates_correct_and_broken_rendering():
    ok = load_ink(DATA / "ref" / "invoice-line__ok.png")
    for broken in ("naive", "no-bidi", "unshaped", "reversed", "ltr-base"):
        assert distance(ok, load_ink(DATA / "ref" / f"invoice-line__{broken}.png")) > 0.15, broken


def test_distance_with_missing_image():
    a = Ink(np.ones((10, 40), dtype=np.float32))
    assert distance(a, None) == 2.0
    assert distance(None, None) == 0.0
