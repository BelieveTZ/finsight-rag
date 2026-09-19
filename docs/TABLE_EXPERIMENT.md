# Statement Header Chunking Experiment

Date: 2026-09-16. Development-only follow-up on the same exposed six questions.
**Decision: keep the baseline default; table-v1 is opt-in.** Page retrieval improves,
but a newly retrieved page can still lack the needed row in the returned chunk.

## Controlled Change

Query mode stayed `baseline`, not the previous `financial-v1` experiment. The PDF,
question manifest, labels, embedding model, CPU runtime, BM25 settings, candidate
counts and fusion settings stayed fixed. Only the chunk representation pipeline
changed. It bundles layout extraction, line-boundary packing and repeated headers;
the experiment does not isolate their individual contributions.

The detector looks for a consolidated statement/balance-sheet title in the first ten
nonempty layout lines and exactly one spaced multi-year header within the first twenty.
It has no question, answer, gold page or hard-coded document/page input. Pages with
ambiguous/multiple year headers, overlong headers or overlong rows fall back to the
original token-window splitting. This is a deliberately narrow heuristic, not a
general table parser or an OCR solution.

For eligible pages, pypdf layout extraction preserves physical lines. Each chunk
contains the original header and consecutive complete lines, up to 384 tokens
including special tokens. Body lines do not overlap. Remaining pages retain the
old 384-token windows with 64-token overlap. Wrapped logical rows, nested headers
and multi-page tables are not solved by preserving physical lines.

## Coverage and Provenance

- All 160 pages were processed; there were no empty extracted pages.
- Detected pages: 56, 57, 58 and 60. They produced six new chunks.
- All chunks outside these four pages were verified unchanged against the original.
- Total corpus size remains 431 chunks; maximum size across both chunk types is
  387 tokens including special tokens, below the model's 512-token limit.
- Every new chunk's header and body were reconstructed from source spans and checked
  against normalized layout text. Body spans collectively cover every body line on
  the four pages without omission. Repeated headers do not introduce invented text.

For a table chunk, `header_start_char`/`header_end_char` and
`start_char`/`end_char` address two separate spans in `normalize(layout_text)`.
The latter pair describes the body, not the entire composite chunk. `extraction_mode`
is `layout`. Its `text` preserves line breaks. Legacy chunks retain their original
single-span semantics and original extraction method.

The composite text must **not** be presented as a single contiguous PDF quotation.
A future citation validator must verify the two spans separately. Repeating a year
header preserves context but does not formally map each cell to a year or unit.

## Results

Strict designated-page metrics; before/after use the same six development questions:

| Method | Page Recall@5 | Page Recall@10 | Label-and-number chunk hit@10 | MRR@10 |
| --- | --- | --- | --- | --- |
| BM25 | 0/6 to 0/6 | 1/6 to 2/6 | 1/6 to 2/6 | 0.0185 to 0.0370 |
| Dense BGE | 1/6 to 2/6 | 1/6 to 2/6 | 1/6 to 1/6 | 0.1667 to 0.2222 |
| Hybrid RRF | 0/6 to 0/6 | 2/6 to 4/6 | 2/6 to 3/6 | 0.0516 to 0.0933 |

The label/number measure requires both markers in one chunk on the designated page.
It is only a proxy for evidence sufficiency, not answer accuracy or semantic support.
The difference between hybrid's 4/6 page hits and 3/6 marker hits is substantive:

- Capital expenditures: dense rank 3 and hybrid rank 8 retrieve `p60:row30`, the
  financing section and investing subtotal. The requested PP&E purchases and 1,577
  amount are in `p60:row5`, which neither method returns in its top ten. This is a
  page-level success **without** the designated supporting row. The earlier valid
  alternative-page observations remain separate; labels were not broadened.
- Dividends: BM25 rank 9 and hybrid rank 8 now retrieve `p60:row30`, including the
  dividends row, 3,193 amount and 2018/2017/2016 header. Previously page 60 was absent.
  Valid alternative evidence on page 48 already existed in the baseline.
- Net income: designated page 56 remains BM25 rank 9 / hybrid rank 6.
- Total assets: designated page 58 remains dense rank 1 / hybrid rank 7.
- Revenue and net PPNE: all methods still miss their designated pages in the top ten.

For the two original FinanceBench cases, dense/hybrid page Recall@10 is now 1/2,
but same-chunk marker hits remain 0/2. For the four authored cases, page and marker
hits are BM25 2/4, dense 1/4, hybrid 3/4. These exposed subsets are not held-out tests.

First setup took 90.71 seconds, including 33.11 seconds creating embeddings. The
layout path currently extracts every page a second time before deciding whether to
fall back; it is more expensive than the original setup. Retrieval P50 was 1.09 ms
BM25, 7.33 ms dense and 7.61 ms hybrid, excluding setup. Six timing samples per method
do not support production performance claims. No GPU inference or paid service was used.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m scripts.retrieval_check --chunk-mode baseline --query-mode baseline
.\.venv\Scripts\python.exe -m scripts.retrieval_check --chunk-mode table-v1 --query-mode baseline
.\.venv\Scripts\python.exe -m pytest -q
```

- [Table experiment raw results](../artifacts/retrieval/20260916T065128208829Z.json)
- [Baseline rerun](../artifacts/retrieval/20260916T065218586060Z.json)
- [Table chunking implementation](../scripts/table_chunks.py)
- [Chunking tests](../tests/test_table_chunks.py)

The baseline rerun reproduced historical rankings, scores and metrics exactly.
Both runs use the same manifest hash and raw queries. Table mode has a separate cache
key incorporating its implementation hash and chunk contents, so it cannot reuse
the old corpus's vectors accidentally. Full text and vectors remain in the ignored
local cache; public reports contain provenance and ranking metadata.

All 36 unit tests and Ruff checks pass. Tests cover source-span reconstruction,
complete body coverage, header repetition, token budget, uncertain-header fallback,
overlong-row fallback and preserving numeric signs. Source-span checks were also run
on all six actual table chunks, not only synthetic fixtures.

Next bounded step: compare the combination of query processing and table chunks
against the three existing configurations before selecting a candidate. Do not assume
their gains add together. Keep page hits separate from actual supporting chunks;
unseen-document validation is still needed before any broad quality claim.
