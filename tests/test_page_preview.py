import io

import pytest
from PIL import Image
from pypdf import PdfWriter

from scripts import page_preview


@pytest.fixture
def pdf(monkeypatch, tmp_path):
    path = tmp_path / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(path)
    monkeypatch.setattr(page_preview, "pdf_path", lambda doc_id: path)
    page_preview.render_page.cache_clear()
    yield
    page_preview.render_page.cache_clear()


def test_cpu_renderer_returns_bounded_png(pdf):
    data = page_preview.render_page("example", 1)
    with Image.open(io.BytesIO(data)) as image:
        assert image.format == "PNG"
        assert max(image.size) == 1600
    assert page_preview.render_page("example", 1) == data


@pytest.mark.parametrize("page", [0, -1, 2])
def test_invalid_page_rejected(pdf, page):
    with pytest.raises(ValueError, match="out of range"):
        page_preview.render_page("example", page)
