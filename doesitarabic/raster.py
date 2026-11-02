"""Turn adapter output (PDF or image) into a PNG screenshot.

PDFs are rasterised with PDFium (Chrome's PDF engine, via pypdfium2). PDFium only draws the
glyphs the library put into the PDF; it does not re-shape text, so library bugs stay visible.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

PDF_SCALE = 2.0  # 144 dpi, matching the 2x device scale of the reference renders


def rasterize(src: str | Path, dest: str | Path, scale: float = PDF_SCALE) -> Path:
    src, dest = Path(src), Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".pdf":
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(src))
        try:
            page = pdf[0]
            image = page.render(scale=scale, fill_color=(255, 255, 255, 255)).to_pil()
            page.close()
        finally:
            pdf.close()
        image.convert("RGB").save(dest)
    else:
        with Image.open(src) as img:
            if img.mode in ("RGBA", "LA", "P"):
                rgba = img.convert("RGBA")
                bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                Image.alpha_composite(bg, rgba).convert("RGB").save(dest)
            else:
                img.convert("RGB").save(dest)
    return dest
