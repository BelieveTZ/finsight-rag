# Full-Report Retrieval Check

Date: 2026-09-16. **Conclusion: retrieval works for some questions, but this baseline
does not yet reliably locate the designated evidence. Do not claim RAG acceptance.**
No paid API, Qwen generation, GPU embedding, background watcher, or game automation
was used. These commands consume CPU/RAM while running and release them on exit.

## Scope and Frozen Inputs

The entire 160-page `3M_2018_10K` PDF was parsed, including notes and exhibits:
431 page-local chunks, zero empty extracted pages. No gold evidence text or answer
was indexed. The document was already exposed during the generation smoke test,
so it belongs exclusively to development/demo data, never a held-out test split.

[Frozen manifest](../evaluation/retrieval_dev_v1.json): all two public FinanceBench
questions for this document, plus four authored numerical questions. These six cases
and designated pages were recorded before the first retrieval run. Authored labels
were checked visually against PDF pages 56, 58 and 60. They are not FinanceBench
annotations. No question or parameter was changed after viewing retrieval results.

The PDF SHA-256 is `faf10c53fc6f1a8aa346ec3db79145e3ae6fbb3753c8064924e174d0a973934d`.
PDF display pages are one-based; the two original zero-based evidence labels, 59
and 57, map to display pages 60 and 58. Printed numbers also match on reviewed pages.

## Configuration

| Component | Fixed setting |
| --- | --- |
| Parsing | pypdf 6.18.1, all pages, whitespace normalization only |
| Chunking | 384 BGE tokens, 64-token overlap; never crosses a page |
| Measured maximum chunk size | 387 tokens after re-tokenization and special tokens; below 512 |
| Sparse search | rank-bm25 0.2.2, BM25Okapi k1=1.5, b=0.75 |
| Sparse tokenization | Lowercase `[a-z0-9]+`; no stopword removal, stemming or query cleanup |
| Dense search | BAAI/bge-small-en-v1.5, Qdrant quantized ONNX distribution, 384 dimensions |
| Embedding runtime | FastEmbed 0.7.4, ONNX Runtime 1.30.0, CPUExecutionProvider only, 4 threads |
| Dense ranking | L2-normalized vectors, cosine similarity; exact search over all chunks |
| Query prefix | `Represent this sentence for searching relevant passages: ` |
| Document prefix | None |
| Hybrid | Equal-weight reciprocal-rank fusion, k=60, top 20 candidates per branch |
| Evaluation | Top 10 chunks, same corpus and chunking for every method; no reranker |

Embedding repository: `qdrant/bge-small-en-v1.5-onnx-q`, revision
`52398278842ec682c6f32300af41344b1c0b0bb2`. ONNX SHA-256:
`51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431`.
This is a quantized ONNX baseline, not a measurement of the full-precision
Sentence Transformers implementation proposed earlier. Model metadata lists MIT.
All downloaded model/tokenizer hashes and exact dependencies are recorded in results
and `uv.lock`.

## Measured Results

These are **strict designated-page metrics**, not answer accuracy. Two original
FinanceBench cases and four authored cases are combined only as a six-case smoke set.

| Method | Page Recall@5 | Page Recall@10 | First-page MRR@10 | Retrieval P50 / P95 |
| --- | --- | --- | --- | --- |
| BM25 | 0/6 | 1/6 (16.7%) | 0.0185 | 1.13 / 2.55 ms |
| Dense BGE | 1/6 (16.7%) | 1/6 (16.7%) | 0.1667 | 6.77 / 11.54 ms |
| Hybrid RRF | 0/6 | 2/6 (33.3%) | 0.0516 | 7.71 / 13.53 ms |

Both original FinanceBench designated pages were missed in the top 10 by all methods.
For the four authored cases, Recall@10 was BM25 1/4, dense 1/4, hybrid 2/4.
The additional proxy requiring the metric label and target numeric string in the
same retrieved chunk on the designated page had the same @5/@10 counts in this run.
That proxy is not a semantic citation-support or year/unit correctness score.

Recall deduplicates `(document_id, pdf_page)` within the first K **chunks**, without
refilling to K unique pages. MRR uses the first matching chunk's rank. All cases here
have one designated page. Unit tests also cover multi-page labels and duplicate pages.

Timing includes query embedding for dense/hybrid but excludes process startup, model
loading, PDF parsing, indexing and disk reads. Six measurements per method are too
few for a robust P95 claim. Initial setup was 47.02 seconds, including 30.96 seconds
embedding the corpus. A separate cache-reuse run took 16.21 seconds setup and 0.006
seconds loading vectors: the CLI still reparses the PDF at startup. It is **not** a
7-millisecond end-to-end application. A resident application has not been built.

## Manual Evidence Review

Gold-page misses do not always mean that no correct evidence was retrieved. The
following supplementary review inspected actual retrieved chunks and rendered PDF
pages. It does not change the frozen labels or the strict scores above.

| Question | Observed retrieved evidence and limitation |
| --- | --- |
| FY2018 capital expenditures | BM25 rank 3 / hybrid rank 7: page 49, chunk `p49:t320`, cash-flow recap contains the 2018 PP&E purchase amount 1,577 million. This supports the amount but is not the designated consolidated cash-flow statement page 60. Dense retrieved a geographic capital-spending table, not the requested statement. |
| FY2018 net PPNE | All methods missed page 58 and failed to surface its 8,738 million figure in the top 10. BM25's first result discusses pension-plan equities; dense's discusses derivatives. This is a genuine baseline failure. |
| FY2018 revenue | BM25 rank 9: page 14, chunk `p14:t0`, selected financial data contains 2018 net sales of 32,765 million. The designated page 56 was missed, and even this alternative would be lost with a top-5 evidence budget. |
| FY2018 dividends | BM25/hybrid rank 1 and dense rank 2: page 48, chunk `p48:t640`, explicitly states 3.193 billion for 2018. Correct alternative support, despite missing designated page 60. Dense rank 1 was a trailing chunk that lacked the 2018 total: top-1 alone would be insufficient. |
| FY2018 net income attributable to 3M | BM25/hybrid rank 1: page 16, chunk `p16:t0`, distinguishes full-year net income of 5.349 billion from quarterly and adjusted figures. Designated page 56 appeared only at ranks 9 and 6 respectively. |
| FY2018 total assets | Dense rank 1: page 58, chunk `p58:t0`, contains the 2018 value 36,500 million. Hybrid moves that page down to rank 7, although its rank 4 page-14 summary also supports the amount. Mixing rankings can worsen the rank of a good dense hit. |

Likely improvement targets, not yet validated explanations: question boilerplate and
financial abbreviations distract retrieval; table headings/year context are fragile
under fixed token windows; naive equal-weight fusion can promote generic passages.
These need controlled follow-up experiments rather than per-question patches.

The earlier generation test's revenue refusal was correct for **only page 60**.
It must not become a no-answer label for the full report, which does disclose revenue.
Do not reuse that excerpt-based refusal set as a full-document refusal benchmark.

## Reproduction on Windows

From the repository root, using the local environment prepared previously:

```powershell
.\.tools\bootstrap\Scripts\uv.exe sync --locked --cache-dir .cache/uv
.\.venv\Scripts\python.exe -m scripts.prepare_retrieval
.\.venv\Scripts\python.exe -m scripts.retrieval_check
.\.venv\Scripts\python.exe -m pytest -q
```

Preparation downloads the exact PDF and a pinned ~67 MB quantized embedding model
only when missing. It checks the PDF hash. Once cached, evaluation loads models
locally with `local_files_only=True`, without Ollama or any paid endpoint.
On a fresh machine first follow the Python portion of [Windows setup](LOCAL_SETUP.md);
Ollama is unnecessary for this retrieval-only check. Windows symlink-cache warnings
do not require administrator access; regular file copies work.

Try an arbitrary question, independently of evaluation labels:

```powershell
.\.venv\Scripts\python.exe -m scripts.retrieval_check --method dense --question "What were 3M's total assets at December 31, 2017?"
```

This additional manual query returned page 58 at rank 1, including the 2017 column
value 37,987 million. It is an exploratory demonstration, not another held-out test.
The command returns evidence, not a generated financial answer. Scores are ranking
signals, not confidence probabilities; no score-based refusal threshold is defined.
Open the cached PDF in a viewer at the returned `pdf_page` to inspect the source.

## Saved Evidence and Boundaries

- [First raw run](../artifacts/retrieval/20260916T061331960250Z.json)
- [Cache-reuse reproduction](../artifacts/retrieval/20260916T061512515547Z.json)
- [Core retrieval module](../scripts/retrieval.py): parsing, page-preserving chunks, BM25/dense/fusion; no evaluation-label input.
- [Runner](../scripts/retrieval_check.py): setup, interactive questions, post-search scoring and reports.
- [Tests](../tests/test_retrieval.py): offsets/overlap, page identity, ranking, metric boundaries and label-free search.

All 18 method/question rankings, numeric scores and metrics reproduced exactly in
the second run. All 21 unit tests and Ruff checks passed; preparation also succeeded
using existing local inputs without downloading again. The cache key includes PDF hash, model/tokenizer hashes, parser/runtime
versions, chunk settings and exact chunk content. Full chunks and vectors remain in
`.cache/retrieval/<cache_key>/`; reports contain IDs, offsets, pages and scores, not
full third-party text. Use a reported chunk ID to inspect `chunks.json` locally.

Source access: [FinanceBench repository](https://github.com/patronus-ai/financebench)
provides the public questions and PDFs; the manifest retains its PDF URL and the
issuer URL. Attribution: Islam et al., *FinanceBench: A New Benchmark for Financial
Question Answering* (2023). No blanket PDF redistribution permission was established:
PDFs, rendered pages, full extracted text, embeddings and downloaded models are
ignored, not committed. Public availability is not treated as permission to relicense
issuer reports or redistribute the complete dataset.

Technical references: [FastEmbed supported models](https://qdrant.github.io/fastembed/examples/Supported_Models/),
[rank-bm25](https://github.com/dorianbrown/rank_bm25),
[pypdf extraction limitations](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).

Still missing: multi-document development/held-out evaluation, validated query cleanup,
table-aware chunking, reranking, generated answers from retrieved evidence, and a UI.
The next useful unit is one controlled retrieval improvement, keeping this baseline
and all failures, before connecting generation or expanding portfolio claims.
