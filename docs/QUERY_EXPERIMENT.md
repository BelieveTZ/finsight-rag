# Query Normalization Experiment

Date: 2026-09-16. Development-only experiment, informed by previously observed
failures. This is not held-out accuracy or evidence of generalization.

## Change and Controls

Added opt-in `financial-v1` query processing. It removes narrowly recognized analyst
role/instruction phrases while retaining statement constraints; normalizes `FY2022`
to `2022`; expands PPNE/PP&E; and adds retrieval aliases for capex and revenue.
Company names, years, units, negation and scope qualifiers are not deliberately removed.
The rules receive only the question, never a document, gold page, answer or case ID.
Aliases are search hints, not universal accounting equivalences or answer-generation rules.

All six development questions, designated pages, 160 PDF pages, 431 chunks, embedding
model, vectors, candidate counts, fusion and scoring stayed fixed. The identical
manifest hash and corpus cache key were verified across both runs. The new baseline
run reproduced historical rankings, scores and metrics exactly. Original/effective
queries and the query-processing source hash are stored in each new report.

The factor varied was query processing as a bundle. This experiment does not isolate
the contribution of each cleanup or expansion rule. Table splitting was not changed.

## Results

Strict designated-page metrics on the same six development questions:

| Method | Recall@5 before / after | Recall@10 before / after | MRR@10 before / after |
| --- | --- | --- | --- |
| BM25 | 0/6 / 0/6 | 1/6 / 0/6 | 0.0185 / 0.0000 |
| Dense BGE | 1/6 / 3/6 | 1/6 / 3/6 | 0.1667 / 0.2417 |
| Hybrid RRF | 0/6 / 1/6 | 2/6 / 3/6 | 0.0516 / 0.0960 |

The same-chunk label/number proxy matched these Recall@5/@10 counts. It remains a
proxy, not an answer correctness score. Alternative valid pages remain separate
from strict designated-page scoring, as explained in [the baseline report](RETRIEVAL_CHECK.md).

- Capital expenditure: dense now retrieves `p60:t0` at rank 4, hybrid at rank 3.
- Net PPNE: dense now retrieves `p58:t0` at rank 5, hybrid at rank 10.
- Both gained chunks were inspected: they contain the year headers, units and
  target rows/numbers, not merely unrelated content on the correct page.
- Total assets stays at dense rank 1 / hybrid rank 7.
- Revenue and dividends still miss their designated pages in the top 10.
- Net income regresses: BM25 rank 9 and hybrid rank 6 previously reached page 56;
  neither reaches it in the new top 10. The only effective-query change for this
  question is `FY2018` to `2018`. That change alters relevance scores; it does not
  establish whether alternative evidence is absent from the results.

The two original FinanceBench cases improve from 0/2 to 2/2 for dense and hybrid,
but they were already examined during development. On the four authored cases,
dense stays at 1/4; hybrid falls from 2/4 to 1/4; BM25 falls from 1/4 to 0/4.
Reporting only the newly successful cases would hide these regressions.

Retrieval P50 before/after (six timings per method): BM25 1.05/1.31 ms,
dense 6.73/6.12 ms, hybrid 7.63/7.15 ms. These exclude setup, query normalization
and indexing; differences this small are not a demonstrated speed improvement.
No GPU inference, paid API, new model download or background process was needed.

## Decision and Reproduction

Keep `baseline` as the default. `financial-v1` is an explicit experimental option:
the dense result is promising, but the regression and tiny exposed dataset do not
justify replacing the default or claiming reliable RAG performance.

```powershell
.\.venv\Scripts\python.exe -m scripts.retrieval_check --query-mode baseline
.\.venv\Scripts\python.exe -m scripts.retrieval_check --query-mode financial-v1
.\.venv\Scripts\python.exe -m scripts.retrieval_check --query-mode financial-v1 --method dense --question "What is 3M's FY2018 net PPNE?"
.\.venv\Scripts\python.exe -m pytest -q
```

- [Baseline rerun](../artifacts/retrieval/20260916T063346702177Z.json)
- [Query-processing run](../artifacts/retrieval/20260916T063326991993Z.json)
- [Rules](../scripts/query_processing.py) and [regression tests](../tests/test_query_processing.py)

Validation: all 30 unit tests pass, including preservation of baseline text, years,
company names, units, negation, statement constraints and unrelated words. Ruff passes.
No evaluation labels or earlier result files were overwritten.

Next bounded experiment: preserve table headers/year context during splitting,
holding the query mode fixed and retaining this baseline. Rule-by-rule ablation and
unseen-document evaluation are still required before promoting query processing.
