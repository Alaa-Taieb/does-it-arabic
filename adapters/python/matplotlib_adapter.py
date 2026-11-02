"""matplotlib: fig.text() with the TTF as FontProperties, right-aligned; wrap=True for wrapping.
Chart titles, labels and annotations all go through this same text engine."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402

from _lib import geometry, pkg_version, read_config, run_fixtures  # noqa: E402

config = read_config()
font = FontProperties(fname=config["fontPath"])
DPI = 72 * config["scale"]


def render(fixture, stem):
    g = geometry(config, fixture)
    fig = plt.figure(figsize=(g["width"] / 72, g["height"] / 72), dpi=DPI)
    fig.patch.set_facecolor("white")
    x = 1 - g["pad"] / g["width"]
    y = 1 - g["pad"] / g["height"]
    fig.text(x, y, fixture["text"], ha="right", va="top", fontproperties=font, fontsize=config["fontSize"],
             wrap=bool(fixture.get("wrap")))
    fig.savefig(stem.with_suffix(".png"), dpi=DPI, facecolor="white")
    plt.close(fig)
    return "png"


run_fixtures(config, pkg_version("matplotlib"), render)
