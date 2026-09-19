"""Runtime document registry; contains no evaluation questions or answers."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/corpus.json"


def documents():
    registry = json.loads(CATALOG.read_text(encoding="utf-8"))
    result = []
    for record in registry["documents"]:
        item = dict(record)
        item["pdf_url"] = (
            "https://raw.githubusercontent.com/patronus-ai/financebench/"
            + registry["source_revision"]
            + "/pdfs/"
            + item["document_id"]
            + ".pdf"
        )
        result.append(item)
    return result


def document(document_id):
    for item in documents():
        if item["document_id"] == document_id:
            return item
    raise ValueError("Unknown document; choose one from the fixed corpus")


def pdf_path(document_id):
    document(document_id)
    return ROOT / ".cache" / (document_id + ".pdf")
