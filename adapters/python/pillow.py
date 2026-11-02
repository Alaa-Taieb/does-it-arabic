"""Pillow ImageDraw.text with direction='rtl' (needs the raqm layout engine for shaping and bidi)."""

from PIL import Image, ImageDraw, ImageFont, features

from _lib import Skip, geometry, pkg_version, read_config, run_fixtures

config = read_config()
s = config["scale"]
engine = "raqm" if features.check("raqm") else "basic"


def render(fixture, stem):
    if fixture.get("wrap"):
        raise Skip("ImageDraw has no line-wrapping API")
    g = geometry(config, fixture)
    img = Image.new("RGB", (g["width"] * s, g["height"] * s), "white")
    font = ImageFont.truetype(config["fontPath"], config["fontSize"] * s)
    draw = ImageDraw.Draw(img)
    kwargs = {"direction": fixture["dir"]} if engine == "raqm" else {}
    draw.text(((g["width"] - g["pad"]) * s, g["pad"] * s), fixture["text"], font=font, fill="black", anchor="ra", **kwargs)
    img.save(stem.with_suffix(".png"))
    return "png"


run_fixtures(config, f"{pkg_version('Pillow')} ({engine} layout)", render)
