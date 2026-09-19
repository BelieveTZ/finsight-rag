import hashlib
import io
import json

import pytest

from scripts import prepare_retrieval
from scripts.retrieval_check import MODEL_REVISION


def setup_root(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare_retrieval, "ROOT", tmp_path)
    (tmp_path / "evaluation").mkdir()
    (tmp_path / ".cache").mkdir()
    (tmp_path / "evaluation/retrieval_dev_v1.json").write_text(
        json.dumps(
            {
                "pdf_url": "https://example.invalid/report.pdf",
                "pdf_sha256": hashlib.sha256(b"expected pdf").hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    return tmp_path / ".cache/3M_2018_10K.pdf"


def test_bad_download_does_not_replace_existing_pdf(tmp_path, monkeypatch):
    pdf = setup_root(tmp_path, monkeypatch)
    pdf.write_bytes(b"existing invalid edition")
    monkeypatch.setattr(
        prepare_retrieval.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"wrong download")
    )
    with pytest.raises(ValueError, match="differs"):
        prepare_retrieval.main()
    assert pdf.read_bytes() == b"existing invalid edition"
    assert not pdf.with_suffix(".download").exists()


def test_prepared_inputs_need_no_network(tmp_path, monkeypatch):
    import huggingface_hub

    pdf = setup_root(tmp_path, monkeypatch)
    pdf.write_bytes(b"expected pdf")
    model = (
        tmp_path
        / ".models/fastembed/models--qdrant--bge-small-en-v1.5-onnx-q"
        / "snapshots"
        / MODEL_REVISION
    )
    model.mkdir(parents=True)
    for name in (
        "config.json",
        "model_optimized.onnx",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
    ):
        (model / name).write_bytes(b"fixture")

    def unexpected_network(*args, **kwargs):
        raise AssertionError("Unexpected network request")

    monkeypatch.setattr(prepare_retrieval.urllib.request, "urlopen", unexpected_network)
    monkeypatch.setattr(huggingface_hub, "snapshot_download", unexpected_network)
    prepare_retrieval.main()
