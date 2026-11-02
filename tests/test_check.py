import io
import json
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from PIL import Image, ImageDraw, ImageFont, features

from conftest import DATA
from doesitarabic import check
from doesitarabic.cli import main
from doesitarabic.paths import FONT, REFERENCE_DIR

needs_raqm = pytest.mark.skipif(not features.check("raqm"), reason="Pillow without raqm cannot render correct Arabic")
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="custom-font references are rendered by Chrome")


def render_png(text, font_path=FONT, direction="rtl", basic=False):
    """A small, real renderer standing in for a user's pipeline."""
    engine = ImageFont.Layout.BASIC if basic else ImageFont.Layout.RAQM
    font = ImageFont.truetype(str(font_path), 64, layout_engine=engine)
    img = Image.new("RGB", (1600, 160), "white")
    kwargs = {} if basic else {"direction": direction}
    ImageDraw.Draw(img).text((1560, 30), text, font=font, fill="black", anchor="ra", **kwargs)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def test_sniff_detects_formats():
    assert check.sniff(b"%PDF-1.7 ...") == "pdf"
    assert check.sniff(b"\x89PNG\r\n\x1a\n....") == "png"
    with pytest.raises(ValueError):
        check.sniff(b"<html>")


def test_parse_spec():
    pairs = check.parse_spec("# comment\ninvoice-line out/a.pdf\n\nhebrew  out/b c.png\n")
    assert pairs == [("invoice-line", "out/a.pdf"), ("hebrew", "out/b c.png")]
    with pytest.raises(ValueError):
        check.parse_spec("nope a.pdf")
    with pytest.raises(ValueError):
        check.parse_spec("invoice-line")
    with pytest.raises(ValueError):
        check.parse_spec("\n# nothing\n")


def test_default_font_uses_committed_references():
    assert check.reference_dir_for(None) == REFERENCE_DIR


def test_cli_exit_codes(capsys):
    assert main(["check", str(DATA / "out" / "pillow-invoice-line.png"), "--fixture", "invoice-line"]) == 0
    assert main(["check", str(DATA / "out" / "fpdf2-invoice-line.pdf"), "--fixture", "invoice-line"]) == 1
    assert main(["check", str(DATA / "out" / "jspdf-invoice-line.png"), "--fixture", "invoice-line"]) == 1
    assert main(["check", str(DATA / "out" / "jspdf-invoice-line.png"), "--fixture", "invoice-line",
                 "--allow-partial"]) == 0
    assert main(["check", "missing.pdf", "--fixture", "invoice-line"]) == 2
    assert main(["check"]) == 2
    out = capsys.readouterr().out
    assert "FAIL" in out and "fix:" in out


def test_cli_json_and_markdown_summary(tmp_path, capsys):
    spec = f"invoice-line {DATA / 'out' / 'pillow-invoice-line.png'}\ninvoice-line {DATA / 'out' / 'fpdf2-invoice-line.pdf'}\n"
    summary = tmp_path / "summary.md"
    assert main(["check", "--spec", spec, "--json", "--summary", str(summary)]) == 1
    data = json.loads(capsys.readouterr().out)
    assert [d["verdict"] for d in data] == ["pass", "fail"]
    md = summary.read_text(encoding="utf-8")
    assert "**1/2 passed.**" in md and "Usual fixes:" in md


@needs_raqm
@needs_node
def test_custom_font_gets_its_own_references(tmp_path, monkeypatch):
    monkeypatch.setattr(check, "CACHE", tmp_path)
    noto = DATA / "fonts" / "NotoSansArabic.ttf"
    out = tmp_path / "connected.png"
    out.write_bytes(render_png("فاتورة ضريبية للعميل", noto))
    with_font = check.judge_file(out, "connected", check.reference_dir_for(noto))
    assert with_font.verdict == "pass"
    # judged against DejaVu references, a different typeface is not a pass
    assert check.judge_file(out, "connected", REFERENCE_DIR).verdict != "pass"


class _Renderer(BaseHTTPRequestHandler):
    broken = False

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
        png = render_png(body["text"], direction=body["dir"], basic=self.broken)
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.end_headers()
        self.wfile.write(png)

    def do_GET(self):
        self.send_response(500)
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture
def endpoint():
    servers = []

    def start(broken):
        handler = type("H", (_Renderer,), {"broken": broken})
        srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        return f"http://127.0.0.1:{srv.server_address[1]}/render"

    yield start
    for s in servers:
        s.shutdown()


@needs_raqm
def test_endpoint_that_renders_correctly_passes(endpoint):
    results = check.check_endpoint(endpoint(False), ["connected", "invoice-line", "hebrew"], REFERENCE_DIR)
    assert [r.verdict for r in results] == ["pass", "pass", "pass"]


@needs_raqm
def test_endpoint_without_shaping_fails(endpoint):
    results = check.check_endpoint(endpoint(True), ["connected", "invoice-line"], REFERENCE_DIR)
    assert all(r.verdict == "fail" for r in results)
    assert results[1].variant == "naive"


def test_endpoint_errors_are_reported_not_raised(endpoint):
    results = check.check_endpoint(endpoint(False), ["connected"], REFERENCE_DIR, method="GET")
    assert results[0].verdict == "error" and "endpoint failed" in results[0].label
