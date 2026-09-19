# Combined Retrieval Experiment

Date: 2026-09-16. Development-only comparison on six previously exposed questions.
Decision: use `financial-v1` queries with `table-v1` chunks as an explicit candidate
for the next end-to-end smoke test. Keep CLI defaults unchanged. This is not a
validated general-purpose configuration or an answer-accuracy result.

## Controls

Completed the fourth cell of the query-processing / chunking comparison using the
existing implementation, without new rules, model downloads or label changes.
All four reports have the same frozen manifest hash. The two baseline-chunk runs
share one corpus cache key; the two table-chunk runs share another. Queries do not
affect document vectors. The corpus remains all 160 pages and 431 chunks of the
3M 2018 annual report. Model, candidate counts, fusion and metric definitions stay
fixed. The three earlier runs are reused, not rerun for this comparison.

## Four-Way Results

Each count is out of six questions. Page metrics require the designated evidence
page. Marker metrics additionally require the field label and number in the same
retrieved chunk on that page. Neither establishes semantic support or answer accuracy.

| Query / chunks | Method | Page@5 | Page@10 | Marker@10 | MRR@10 |
| --- | --- | --- | --- | --- | --- |
| baseline / baseline | BM25 | 0 | 1 | 1 | 0.0185 |
| baseline / baseline | Dense | 1 | 1 | 1 | 0.1667 |
| baseline / baseline | Hybrid | 0 | 2 | 2 | 0.0516 |
| financial-v1 / baseline | BM25 | 0 | 0 | 0 | 0.0000 |
| financial-v1 / baseline | Dense | 3 | 3 | 3 | 0.2417 |
| financial-v1 / baseline | Hybrid | 1 | 3 | 3 | 0.0960 |
| baseline / table-v1 | BM25 | 0 | 2 | 2 | 0.0370 |
| baseline / table-v1 | Dense | 2 | 2 | 1 | 0.2222 |
| baseline / table-v1 | Hybrid | 0 | 4 | 3 | 0.0933 |
| financial-v1 / table-v1 | BM25 | 0 | 1 | 1 | 0.0208 |
| financial-v1 / table-v1 | Dense | 2 | 3 | 3 | 0.2278 |
| financial-v1 / table-v1 | Hybrid | 1 | 4 | 4 | 0.1060 |

The combination improves hybrid marker hits over either single change, but does
not dominate every measure: dense Page@5 drops from 3 to 2 versus query-only.
Hybrid Marker@5 remains only 1/6. A future generator receiving only five chunks
would discard several designated supporting chunks; top-ten results cannot be
reported as evidence of a top-five pipeline's quality.

## Case-Level Hybrid Inspection

| Question | Baseline marker rank | Query only | Table only | Combined |
| --- | --- | --- | --- | --- |
| Capital expenditure | absent | 3 | absent | 4, p60:row5 |
| Net PPNE | absent | 10 | absent | 10, p58:row6 |
| Revenue | absent | absent | absent | absent |
| Dividends | absent | absent | 8 | 7, p60:row30 |
| Net income | 6 | absent | 6 | absent |
| Total assets | 7 | 7 | 7 | 7, p58:row6 |

Capital expenditure now reaches the chunk with PP&E purchases and 1,577, rather
than merely a different cash-flow chunk on page 60. Net PPNE and total assets
share a balance-sheet chunk containing 8,738 and 36,500 respectively; dividends
uses the financing chunk containing 3,193. These are retrieval marker checks,
not proof that a generator selects the right year, sign or unit conversion.

The original FinanceBench subset reaches 2/2 hybrid marker hits; the four authored
questions reach 2/4. Both subsets remain development data. Revenue still misses
its designated page. The query-processing net-income regression is not repaired
by table chunks. Alternative-page evidence is not counted or relabeled: for
example, the combined net-income results still return page 16 at rank 1.

## Runtime and Reproduction

The new run used CPUExecutionProvider and existing local vectors (cache hit).
Setup still took 47.14 seconds because PDF extraction and chunking precede cache
lookup. Retrieval P50 was 0.91 ms BM25, 4.12 ms dense and 4.85 ms hybrid, excluding
setup and query processing. Six samples and nonsimultaneous runs do not establish
a speed improvement. No GPU inference, paid API or additional background service
was used.

```powershell
.\.venv\Scripts\python.exe -m scripts.retrieval_check --query-mode baseline --chunk-mode baseline
.\.venv\Scripts\python.exe -m scripts.retrieval_check --query-mode financial-v1 --chunk-mode baseline
.\.venv\Scripts\python.exe -m scripts.retrieval_check --query-mode baseline --chunk-mode table-v1
.\.venv\Scripts\python.exe -m scripts.retrieval_check --query-mode financial-v1 --chunk-mode table-v1
.\.venv\Scripts\python.exe -m pytest -q
```

Raw reports in table order:

- [Baseline](../artifacts/retrieval/20260916T065218586060Z.json)
- [Query only](../artifacts/retrieval/20260916T063326991993Z.json)
- [Table only](../artifacts/retrieval/20260916T065128208829Z.json)
- [Combined](../artifacts/retrieval/20260916T070308019253Z.json)

The older query-only report predates the `chunk_mode` report field; its baseline
corpus cache key verifies its chunk configuration. Existing 36 unit tests pass.
No implementation or default configuration was changed for this experiment.

## Next Bounded Step

Connect the candidate's actual retrieved evidence to local Qwen generation for a
small end-to-end test with page citations and insufficient-evidence refusals.
Use retrieved chunks, not gold excerpts, and record the context actually supplied.
Validate repeated-header/body source spans separately. Retain failure cases and
distinguish retrieval failures, unsupported answers and citation failures. Do not
tune repeatedly on these six questions to claim benchmark performance; independent
questions/documents remain necessary for final acceptance.
