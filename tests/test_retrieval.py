import numpy as np
import pytest
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

from scripts.retrieval import (
    QUERY_PREFIX,
    Chunk,
    Retriever,
    normalize,
    page_metrics,
    reciprocal_rank_fusion,
    split_page,
    top_indices,
)


@pytest.fixture
def tokenizer():
    value = Tokenizer(WordLevel({"[UNK]": 0}, unk_token="[UNK]"))
    value.pre_tokenizer = Whitespace()
    return value


def test_chunk_offsets_overlap_and_page_provenance(tokenizer):
    text = "one  two\nthree four five six seven eight nine"
    chunks = split_page(text, "report", 7, tokenizer, size=4, overlap=1)
    assert len(chunks) == 3
    assert len({c.id for c in chunks}) == 3
    assert all(c.pdf_page == 7 and c.document_id == "report" for c in chunks)
    assert all(c.text == normalize(text)[c.start_char : c.end_char] for c in chunks)
    assert chunks[0].text.split()[-1] == chunks[1].text.split()[0]
    assert chunks[0].start_char == 0
    assert chunks[-1].end_char == len(normalize(text))


def test_empty_page_stays_empty(tokenizer):
    assert split_page(" \n", "report", 1, tokenizer) == []


def test_extraction_visits_all_pages_and_records_empty_pages(tokenizer, monkeypatch):
    from types import SimpleNamespace

    from scripts import retrieval

    pages = [SimpleNamespace(extract_text=lambda text=t: text) for t in ("revenue", "", "assets")]
    monkeypatch.setattr(retrieval, "PdfReader", lambda _: SimpleNamespace(pages=pages))
    chunks, audit = retrieval.extract_pdf("unused.pdf", "report", tokenizer)
    assert [p["pdf_page"] for p in audit] == [1, 2, 3]
    assert audit[1]["characters"] == 0
    assert [c.pdf_page for c in chunks] == [1, 3]


def test_invalid_split_rejected(tokenizer):
    with pytest.raises(ValueError):
        split_page("text", "report", 0, tokenizer)
    with pytest.raises(ValueError):
        split_page("text", "report", 1, tokenizer, size=4, overlap=4)


def test_duplicate_pages_do_not_inflate_recall_or_shift_chunk_rank():
    hits = [{"document_id": "a", "pdf_page": p} for p in (2, 2, 7, 7, 7, 8)]
    assert page_metrics(hits, "a", [7, 8]) == {
        "recall_at_5": 0.5,
        "recall_at_10": 1.0,
        "mrr_at_10": 1 / 3,
    }
    assert page_metrics(hits, "different", [7])["mrr_at_10"] == 0


def test_rank_eleven_is_not_in_top_ten():
    hits = [{"document_id": "a", "pdf_page": p} for p in range(1, 12)]
    assert page_metrics(hits, "a", [11])["recall_at_10"] == 0
    assert page_metrics(hits, "a", [11])["mrr_at_10"] == 0


def test_rrf_uses_ranks_and_deduplicates_each_branch():
    ranking, scores = reciprocal_rank_fusion([[0, 0, 1], [1, 2]])
    assert ranking == [1, 0, 2]
    assert scores[1] == pytest.approx(1 / 62 + 1 / 61)


def test_stable_score_ties():
    assert top_indices([2, 2, 0], 3) == [0, 1, 2]
    assert top_indices([2, 2, 0], 3, positive_only=True) == [0, 1]


class Embedder:
    def __init__(self):
        self.inputs = []

    def embed(self, texts):
        self.inputs.extend(texts)
        yield np.array([0.0, 1.0])


def test_real_bm25_and_dense_retrieval_do_not_need_gold_labels():
    chunks = [
        Chunk("a", "report", 1, 0, 7, "revenue"),
        Chunk("b", "report", 2, 0, 6, "assets"),
        Chunk("c", "report", 3, 0, 4, "risk"),
    ]
    embedder = Embedder()
    index = Retriever(chunks, np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]), embedder)
    assert index.search("revenue", "bm25")[0]["id"] == "a"
    assert index.search("unmatchedword", "bm25") == []
    assert index.search("capital", "dense")[0]["id"] == "b"
    assert embedder.inputs == [QUERY_PREFIX + "capital"]
    assert index.search("assets", "hybrid")[0]["id"] == "b"
    hybrid = {h["id"]: h for h in index.search("revenue", "hybrid")}
    assert hybrid["a"]["lexical_rank"] == 1
    assert hybrid["b"]["dense_rank"] == 1
    assert hybrid["b"]["lexical_rank"] is None
    assert index.search("revenue", "bm25")[0]["dense_rank"] is None


def test_invalid_index_and_query_rejected():
    with pytest.raises(ValueError):
        Retriever([], np.zeros((0, 2)), Embedder())
    chunk = Chunk("a", "r", 1, 0, 4, "text")
    with pytest.raises(ValueError):
        Retriever([chunk], np.zeros((1, 2)), Embedder())
    index = Retriever([chunk], np.ones((1, 2)), Embedder())
    with pytest.raises(ValueError):
        index.search(" ")
    with pytest.raises(ValueError):
        index.search("text", "unknown")
