"""Fetch pinned public inputs. No inference API or credentials are required."""

import json
import os
import urllib.request
from pathlib import Path

from scripts.retrieval import sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HOME"] = str(ROOT / ".cache/huggingface")
    from huggingface_hub import snapshot_download

    from scripts.retrieval_check import MODEL_REPOSITORY, MODEL_REVISION

    manifest = json.loads((ROOT / "evaluation/retrieval_dev_v1.json").read_text(encoding="utf-8"))
    target = ROOT / ".cache/3M_2018_10K.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or sha256(target) != manifest["pdf_sha256"]:
        temporary = target.with_suffix(".download")
        try:
            with urllib.request.urlopen(manifest["pdf_url"], timeout=60) as response:
                with temporary.open("wb") as output:
                    total = 0
                    while block := response.read(1024 * 1024):
                        total += len(block)
                        if total > 20 * 1024 * 1024:
                            raise ValueError("PDF download exceeds expected size bound")
                        output.write(block)
            if sha256(temporary) != manifest["pdf_sha256"]:
                raise ValueError("Downloaded PDF differs from the frozen development corpus")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    files = [
        "config.json",
        "model_optimized.onnx",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
    ]
    cache = str(ROOT / ".models/fastembed")
    arguments = {
        "repo_id": MODEL_REPOSITORY,
        "revision": MODEL_REVISION,
        "cache_dir": cache,
        "allow_patterns": files,
        "token": False,
    }
    path = ROOT / ".models/fastembed/models--qdrant--bge-small-en-v1.5-onnx-q/snapshots"
    path /= MODEL_REVISION
    if not all((path / name).is_file() for name in files):
        path = Path(snapshot_download(**arguments))
    print(f"Verified PDF: {target}")
    print(f"Pinned embedding snapshot: {path}")


if __name__ == "__main__":
    main()
