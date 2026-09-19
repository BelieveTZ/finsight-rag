"""CPU-only rendering for whitelisted local reports, independent of inference."""

import io
import threading
from functools import lru_cache

import pypdfium2 as pdfium

from scripts.corpus import pdf_path

# PDFium is not thread-safe, including operations on separate documents.
_render_lock = threading.Lock()


@lru_cache(maxsize=12)
def render_page(document_id: str, page_number: int) -> bytes:
    path = pdf_path(document_id)
    with _render_lock, pdfium.PdfDocument(path) as pdf:
        if not 1 <= page_number <= len(pdf):
            raise ValueError("PDF page out of range")
        page = pdf[page_number - 1]
        try:
            width, height = page.get_size()
            bitmap = page.render(scale=1600 / max(width, height))
            try:
                with bitmap.to_pil() as image, io.BytesIO() as output:
                    image.save(output, format="PNG")
                    return output.getvalue()
            finally:
                bitmap.close()
        finally:
            page.close()
