"""Page-preserving full-PDF retrieval. This module never reads evaluation labels."""

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from pypdf import PdfReader
from rank_bm25 import BM25Okapi

MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
CHUNK_TOKENS = 384
OVERLAP = 64
CANDIDATES = 20
RRF_K = 60


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(text):
    return " ".join(text.split())


def lexical_tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    pdf_page: int
    start_char: int
    end_char: int
    text: str


def split_page(text, document_id, pdf_page, tokenizer, size=CHUNK_TOKENS, overlap=OVERLAP):
    if not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < chunk size")
    if pdf_page < 1:
        raise ValueError("PDF pages are one-based")
    text = normalize(text)
    offsets = tokenizer.encode(text, add_special_tokens=False).offsets
    chunks = []
    for start in range(0, len(offsets), size - overlap):
        end = min(start + size, len(offsets))
        left, right = offsets[start][0], offsets[end - 1][1]
        chunks.append(
            Chunk(
                f"{document_id}:p{pdf_page}:t{start}",
                document_id,
                pdf_page,
                left,
                right,
                text[left:right],
            )
        )
        if end == len(offsets):
            break
    return chunks


def extract_pdf(path, document_id, tokenizer, chunk_mode="baseline"):
    if chunk_mode not in {"baseline", "table-v1"}:
        raise ValueError("Unknown chunk mode")
    reader = PdfReader(path)
    chunks, pages = [], []
    for number, page in enumerate(reader.pages, 1):
        text = normalize(page.extract_text() or "")
        current = split_page(text, document_id, number, tokenizer)
        strategy = "baseline"
        if chunk_mode == "table-v1":
            from scripts.table_chunks import split_statement

            replacement = split_statement(
                page.extract_text(extraction_mode="layout") or "", document_id, number, tokenizer
            )
            if replacement is not None:
                current = replacement
                strategy = "table-v1"
        chunks.extend(current)
        pages.append({"pdf_page": number, "characters": len(text), "chunks": len(current)})
        if chunk_mode != "baseline":
            pages[-1]["strategy"] = strategy
    if not chunks:
        raise ValueError("PDF has no extractable text; OCR is not supported")
    return chunks, pages


def top_indices(scores, count, positive_only=False):
    return [
        int(i)
        for i in np.argsort(-np.asarray(scores), kind="stable")
        if not positive_only or scores[i] > 0
    ][:count]


def reciprocal_rank_fusion(rankings, k=RRF_K):
    scores = {}
    for ranking in rankings:
        for rank, index in enumerate(dict.fromkeys(ranking), 1):
            scores[index] = scores.get(index, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda index: (-scores[index], index)), scores


class Retriever:
    def __init__(self, chunks, vectors, embedder):
        if not chunks or vectors.shape[0] != len(chunks):
            raise ValueError("Chunk/vector count mismatch or empty corpus")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if not np.isfinite(vectors).all() or np.any(norms == 0):
            raise ValueError("Invalid embedding vectors")
        self.chunks = chunks
        self.vectors = vectors / norms
        self.embedder = embedder
        self.bm25 = BM25Okapi([lexical_tokens(c.text) for c in chunks], k1=1.5, b=0.75)

    def search(self, question, method="hybrid", limit=10):
        if method not in {"bm25", "dense", "hybrid"}:
            raise ValueError("Unknown retrieval method")
        if not question.strip() or limit < 1:
            raise ValueError("Question and positive result limit required")
        if method in {"bm25", "hybrid"}:
            lexical = self.bm25.get_scores(lexical_tokens(question))
            lexical_rank = top_indices(lexical, CANDIDATES, positive_only=True)
        if method in {"dense", "hybrid"}:
            query = next(iter(self.embedder.embed([QUERY_PREFIX + question])))
            norm = np.linalg.norm(query)
            if not np.isfinite(query).all() or norm == 0:
                raise ValueError("Invalid query vector")
            dense = self.vectors @ (query / norm)
            dense_rank = top_indices(dense, CANDIDATES)
        if method == "hybrid":
            ranking, scores = reciprocal_rank_fusion([lexical_rank, dense_rank])
        elif method == "bm25":
            ranking, scores = lexical_rank, lexical
        else:
            ranking, scores = dense_rank, dense
        dense_positions = (
            {index: rank for rank, index in enumerate(dense_rank, 1)}
            if method in {"dense", "hybrid"}
            else {}
        )
        lexical_positions = (
            {index: rank for rank, index in enumerate(lexical_rank, 1)}
            if method in {"bm25", "hybrid"}
            else {}
        )
        return [
            {
                **asdict(self.chunks[i]),
                "score": float(scores[i]),
                "dense_rank": dense_positions.get(i),
                "lexical_rank": lexical_positions.get(i),
            }
            for i in ranking[:limit]
        ]


def page_metrics(hits, document_id, gold_pages):
    gold = {(document_id, page) for page in gold_pages}
    if not gold:
        raise ValueError("Evidence-page metrics require nonempty gold pages")
    keys = [(h["document_id"], h["pdf_page"]) for h in hits]
    return {
        **{f"recall_at_{k}": len(set(keys[:k]) & gold) / len(gold) for k in (5, 10)},
        "mrr_at_10": next((1 / rank for rank, key in enumerate(keys[:10], 1) if key in gold), 0.0),
    }
