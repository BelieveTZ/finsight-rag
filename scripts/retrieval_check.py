"""Evaluate a frozen development set; also allow label-free interactive retrieval."""

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from tokenizers import Tokenizer

from scripts.corpus import CATALOG, document, pdf_path
from scripts.query_processing import prepare_query
from scripts.retrieval import (
    CANDIDATES,
    CHUNK_TOKENS,
    MODEL,
    OVERLAP,
    QUERY_PREFIX,
    RRF_K,
    Retriever,
    extract_pdf,
    normalize,
    page_metrics,
    sha256,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL_REPOSITORY = "qdrant/bge-small-en-v1.5-onnx-q"
MODEL_REVISION = "52398278842ec682c6f32300af41344b1c0b0bb2"


def build_index(chunk_mode="baseline", document_id=None):
    if document_id is None:
        manifest_path = ROOT / "evaluation/retrieval_dev_v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        pdf = ROOT / ".cache/3M_2018_10K.pdf"
    else:
        manifest_path = CATALOG
        manifest = document(document_id)
        pdf = pdf_path(document_id)
    if sha256(pdf) != manifest["pdf_sha256"]:
        raise ValueError("PDF checksum mismatch; do not evaluate a different edition")
    started = time.perf_counter()
    pinned_model = (
        ROOT
        / ".models/fastembed/models--qdrant--bge-small-en-v1.5-onnx-q/snapshots"
        / MODEL_REVISION
    )
    if not (pinned_model / "model_optimized.onnx").is_file():
        raise FileNotFoundError("Pinned embedding model missing; see docs/RETRIEVAL_CHECK.md")
    embedder = TextEmbedding(
        MODEL,
        cache_dir=str(ROOT / ".models/fastembed"),
        threads=4,
        providers=["CPUExecutionProvider"],
        local_files_only=True,
        specific_model_path=str(pinned_model),
    )
    # Version-pinned FastEmbed exposes these on its ONNX implementation.
    model_dir = Path(embedder.model._model_dir)
    model_hashes = {p.name: sha256(p) for p in sorted(model_dir.iterdir()) if p.is_file()}
    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    chunks, pages = extract_pdf(pdf, manifest["document_id"], tokenizer, chunk_mode)
    if len(pages) != manifest["pdf_pages"]:
        raise ValueError("Unexpected PDF page count")
    lengths = [len(tokenizer.encode(c.text).ids) for c in chunks]
    if max(lengths) > 512:
        raise ValueError("A chunk exceeds the embedding context limit")
    config = {
        "model": MODEL,
        "model_repository": MODEL_REPOSITORY,
        "model_revision": MODEL_REVISION,
        "model_hashes": model_hashes,
        "pdf_sha256": sha256(pdf),
        "chunk_tokens": CHUNK_TOKENS,
        "overlap": OVERLAP,
        "pypdf": version("pypdf"),
        "fastembed": version("fastembed"),
        "tokenizers": version("tokenizers"),
        "query_prefix": QUERY_PREFIX,
    }
    if chunk_mode != "baseline":
        config["chunk_mode"] = chunk_mode
        config["table_chunks_sha256"] = sha256(ROOT / "scripts/table_chunks.py")
    content = json.dumps([asdict(c) for c in chunks], ensure_ascii=False)
    cache_key = hashlib.sha256((json.dumps(config, sort_keys=True) + content).encode()).hexdigest()
    cache = ROOT / ".cache/retrieval" / cache_key
    cache.mkdir(parents=True, exist_ok=True)
    vector_path = cache / "vectors.npy"
    cache_hit = vector_path.exists()
    index_start = time.perf_counter()
    if cache_hit:
        vectors = np.load(vector_path, allow_pickle=False)
    else:
        vectors = np.asarray(list(embedder.embed([c.text for c in chunks], batch_size=16)))
        np.save(vector_path, vectors, allow_pickle=False)
    vector_seconds = time.perf_counter() - index_start
    (cache / "chunks.json").write_text(content, encoding="utf-8")
    retriever = Retriever(chunks, vectors, embedder)
    setup_seconds = time.perf_counter() - started
    report = {
        "at_utc": datetime.now(UTC).isoformat(),
        "scope": "development retrieval only",
        "document_id": manifest["document_id"],
        "chunk_mode": chunk_mode,
        "query_processing_sha256": sha256(ROOT / "scripts/query_processing.py"),
        "manifest_sha256": sha256(manifest_path),
        "config": config,
        "packages": {p: version(p) for p in ("numpy", "onnxruntime", "rank-bm25")},
        "providers": embedder.model.model.get_providers(),
        "chunk_count": len(chunks),
        "max_chunk_tokens_with_special": max(lengths),
        "pages": pages,
        "empty_pages": [p["pdf_page"] for p in pages if not p["characters"]],
        "cache_key": cache_key,
        "vector_cache_hit": cache_hit,
        "vector_seconds": vector_seconds,
        "setup_seconds": setup_seconds,
        "bm25": {"k1": 1.5, "b": 0.75, "tokens": "lowercase [a-z0-9]+, no stemming"},
        "rrf_k": RRF_K,
        "candidates_per_branch": CANDIDATES,
        "results": [],
    }
    return retriever, tokenizer, report


def main(args):
    retriever, tokenizer, report = build_index(args.chunk_mode)
    report["query_mode"] = args.query_mode
    if args.question:
        effective_query = prepare_query(args.question, args.query_mode)
        if len(tokenizer.encode(QUERY_PREFIX + effective_query).ids) > 512:
            raise ValueError("Question exceeds embedding context limit")
        print(
            json.dumps(retriever.search(effective_query, args.method), indent=2, ensure_ascii=True)
        )
        return
    manifest = json.loads((ROOT / "evaluation/retrieval_dev_v1.json").read_text(encoding="utf-8"))
    # Gold pages/markers are read only after each label-free search has returned.
    for case in manifest["cases"]:
        effective_query = prepare_query(case["question"], args.query_mode)
        if len(tokenizer.encode(QUERY_PREFIX + effective_query).ids) > 512:
            raise ValueError("Evaluation question would be truncated")
        for method in ("bm25", "dense", "hybrid"):
            begin = time.perf_counter()
            hits = retriever.search(effective_query, method)
            elapsed = time.perf_counter() - begin
            metrics = page_metrics(hits, manifest["document_id"], case["evidence_pages"])
            for k in (5, 10):
                metrics[f"marker_hit_at_{k}"] = any(
                    h["pdf_page"] in case["evidence_pages"]
                    and all(
                        normalize(m).lower() in normalize(h["text"]).lower()
                        for m in case["markers"]
                    )
                    for h in hits[:k]
                )
            record = {
                "case_id": case["id"],
                "original_query": case["question"],
                "effective_query": effective_query,
                "source": case["source"],
                "method": method,
                "seconds": elapsed,
                "metrics": metrics,
                "hits": [{k: v for k, v in h.items() if k != "text"} for h in hits],
            }
            report["results"].append(record)
            print(case["id"], method, metrics, flush=True)
    report["summary"] = {}
    for method in ("bm25", "dense", "hybrid"):
        records = [r for r in report["results"] if r["method"] == method]
        report["summary"][method] = {
            "questions": len(records),
            **{
                name: float(np.mean([r["metrics"][name] for r in records]))
                for name in records[0]["metrics"]
            },
            "p50_seconds": float(np.percentile([r["seconds"] for r in records], 50)),
            "p95_seconds": float(np.percentile([r["seconds"] for r in records], 95)),
        }
    output = ROOT / "artifacts/retrieval"
    output.mkdir(parents=True, exist_ok=True)
    path = output / (datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Report: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question")
    parser.add_argument("--chunk-mode", choices=("baseline", "table-v1"), default="baseline")
    parser.add_argument("--query-mode", choices=("baseline", "financial-v1"), default="baseline")
    parser.add_argument("--method", choices=("bm25", "dense", "hybrid"), default="hybrid")
    main(parser.parse_args())
