# Corpus and Annotation Record

Prepared 2026-09-19 before portfolio model evaluation. See the pre-experiment
[selection policy](DELIVERY_CHECKLIST.md) and runtime registry in `data/corpus.json`.

| Document | Split | PDF pages | Indexed chunks | Empty text pages |
| --- | --- | --- | --- | --- |
| 3M 2018 10-K | Development | 160 | 431 | None |
| PepsiCo 2022 10-K | Development | 503 | 916 | None |
| AMD 2022 10-K | Final | 121 | 294 | None |
| CVS Health 2022 10-K | Final | 213 | 604 | 206 |

Total: 997 PDF pages and 2,245 chunks. Each complete PDF, including any attached
exhibits, was ingested. CVS PDF page 206 was rendered and inspected: it is visually
blank apart from a horizontal rule. It was not silently removed from the page
audit. No OCR is implemented. Embeddings use CPUExecutionProvider only.

## Sources and Rights

PDFs are retrieved from the [official FinanceBench repository](https://github.com/patronus-ai/financebench)
at commit `cc39aeb4afdf33909ee1412188bf89035950c2eb`, with SHA-256 checksums and original
publisher links in the registry. The upstream README describes its 150 public
examples and zero-based evidence-page convention; this project displays one-based
PDF positions. These differ from printed page numbers.

No blanket PDF redistribution license is assumed. Full PDFs, extracted text, model
weights and private prompt traces stay in ignored local directories. Publish source
links, checksums, independently authored question labels and short evidence excerpts
needed to inspect results, not the upstream annotated dataset or whole reports.
The original two 3M FinanceBench questions remain attributed. The portfolio dataset
is mostly authored: do **not** call its score a FinanceBench benchmark score.

## Frozen Questions and Verification

`evaluation/portfolio_v1.json` has 24 numeric questions (12 development and 12 final)
and six unanswerable checks (three per split). Documents do not cross splits.
Original 3M questions remain exposed development examples. The final source tables
were inspected to annotate labels, not to tune on model outputs. This is a small,
single-author annotation effort, not independent multi-rater ground truth.

The numeric categories on new reports are revenue, parent-attributable net income
(AMD uses net income), total assets, net PP&E, capital expenditure and operating
cash flow. Inapplicable original extraction questions about qualitative businesses
or litigation are not scored by this numeric prototype; new numeric questions are
explicitly authored instead. Nothing was selected according to model success.

Source pages rendered and visually inspected, including year columns and units:

- PepsiCo: PDF pages 62, 64, 66 (printed pages 60, 62, 64).
- AMD: PDF pages 54, 56, 58 (printed pages 51, 53, 55).
- CVS Health: PDF pages 108, 110, 111 (printed pages 106, 108, 109).
- 3M: prior development inspections of PDF pages 56, 58 and 60 are retained.

Numeric labels preserve cash-outflow magnitude when explicitly asked for spending.
PepsiCo net income attributable to the parent is 8,910, not consolidated 8,978;
CVS Health parent net income is 4,149, not consolidated 4,165. All amounts are USD
millions except the original 3M PPNE question, which requests billions.

Unanswerable cases distinguish future reporting periods, wrong companies, and
in-scope customer-level figures that are not separately disclosed. All extracted
PepsiCo pages were searched for Microsoft and all AMD pages for OpenAI, with zero
mentions; the statement layouts were also inspected. The reason is insufficient
disclosure, not an inference that the companies had zero business together.

Model and retrieval configurations must be frozen before running the final split.
After observing final results, any tuning makes that result exploratory. Do not
drop failures, broaden labels silently or reuse an exposed final set as held out.

## Reproduce Without GPU

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_retrieval
.\.venv\Scripts\python.exe -m scripts.prepare_corpus --download
.\.venv\Scripts\python.exe -m pytest -q
```

Per-document extraction/index audits are in `artifacts/corpus/`. The runtime
registry has no questions, expected values or gold evidence pages. The portfolio
application uses that registry rather than loading evaluation labels.
