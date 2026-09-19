"""Download/verify the fixed corpus and build CPU-only indexes without answer labels."""

import argparse
import json
import urllib.request
from datetime import UTC, datetime

from scripts.corpus import ROOT, documents, pdf_path
from scripts.retrieval import sha256
from scripts.retrieval_check import build_index


def prepare(download=False):
    reports = []
    for doc in documents():
        path = pdf_path(doc["document_id"])
        if not path.exists() and download:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".download")
            try:
                with urllib.request.urlopen(doc["pdf_url"], timeout=120) as response:
                    with temporary.open("wb") as output:
                        total = 0
                        while block := response.read(1024 * 1024):
                            total += len(block)
                            if total > 100 * 1024 * 1024:
                                raise ValueError("PDF exceeds 100 MiB limit")
                            output.write(block)
                if sha256(temporary) != doc["pdf_sha256"]:
                    raise ValueError("Downloaded PDF checksum differs from fixed corpus")
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        if not path.exists() or sha256(path) != doc["pdf_sha256"]:
            raise ValueError(f"Missing or changed PDF: {doc['document_id']}; use --download")
        print(f"Indexing {doc['document_id']} on CPU", flush=True)
        _, _, report = build_index("table-v1", doc["document_id"])
        reports.append(report)
        target = ROOT / "artifacts/corpus"
        target.mkdir(parents=True, exist_ok=True)
        (target / (doc["document_id"] + ".json")).write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(
            f"{doc['document_id']}: {report['chunk_count']} chunks, "
            f"empty pages: {report['empty_pages']}",
            flush=True,
        )
    return {"at_utc": datetime.now(UTC).isoformat(), "documents": len(reports)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    print(prepare(parser.parse_args().download))
